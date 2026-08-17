#!/usr/bin/env python3
"""Pokec relevance-diffusion performance runner (paper §4.2 shape).

Standalone: stdlib + pyreason only. Fresh child process per measurement;
thresholds apply to ``reason_s`` only. Semantic tripwire via ``relevance_rows``.

Parent mode (default)::

  python benchmarks/pokec/run_bench.py \\
    --fixture benchmarks/pokec/fixtures/pokec-2k.graphml \\
    --customers benchmarks/pokec/fixtures/pokec-2k-customers.json \\
    --repeats 3 --band pokec-2k --out pokec-2k-report.json

Child mode is internal (``--child``); do not invoke directly from CI.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_BASELINES = HERE / "baselines.json"


def _parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--customers", type=Path, required=True)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--band", choices=("pokec-2k", "pokec-10k"), required=True)
    p.add_argument("--out", type=Path, default=Path("pokec-report.json"))
    p.add_argument("--baselines", type=Path, default=DEFAULT_BASELINES)
    p.add_argument(
        "--child",
        action="store_true",
        help="Run one measurement in this process and print JSON to stdout",
    )
    p.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip the untimed warmup child (debug only)",
    )
    return p.parse_args(argv)


def _run_program(fixture: Path, customers_path: Path) -> dict:
    """Execute the paper program once; return timed windows + relevance_rows."""
    customers = json.loads(customers_path.read_text(encoding="utf-8"))

    t_import0 = time.perf_counter()
    import pyreason as pr  # noqa: WPS433 — timed deliberately

    import_s = time.perf_counter() - t_import0

    t_setup0 = time.perf_counter()
    pr.settings.verbose = False
    # filter_and_sort_nodes needs store_interpretation_changes (default True).
    pr.load_graphml(str(fixture))
    pr.add_rule(
        pr.Rule(
            "relevance(x) : [0.6,1] <-1 relevance(y):[1,1], friend(x,y):[1,1]",
            "relevance_friend_rule",
        )
    )
    pr.add_rule(
        pr.Rule(
            "relevance(x) : [1,1] <-1 relevance(y):[1,1], friend(x,y):[1,1], "
            "hasPet(x,p):[1,1], hasPet(y,p):[1,1]",
            "relevance_same_pet_rule",
        )
    )
    for i, uid in enumerate(customers):
        pr.add_fact(pr.Fact(f"relevance(u{uid})", f"customer_{i}", 0, 8))
    setup_s = time.perf_counter() - t_setup0

    t_reason0 = time.perf_counter()
    interpretation = pr.reason(timesteps=8)
    reason_s = time.perf_counter() - t_reason0

    df_list = pr.filter_and_sort_nodes(interpretation, ["relevance"])
    final_df = df_list[-1] if df_list else None
    relevance_rows = 0 if final_df is None else int(len(final_df))

    try:
        import pyreason as _pr_mod

        pyreason_version = getattr(_pr_mod, "__version__", "unknown")
    except Exception:  # noqa: BLE001
        pyreason_version = "unknown"

    return {
        "import_s": import_s,
        "setup_s": setup_s,
        "reason_s": reason_s,
        "relevance_rows": relevance_rows,
        "python": sys.version.split()[0],
        "pyreason": pyreason_version,
    }


def _spawn_child(args, warmup: bool = False) -> dict:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--fixture",
        str(args.fixture),
        "--customers",
        str(args.customers),
        "--band",
        args.band,
        "--repeats",
        "1",
        "--out",
        os.devnull,
    ]
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    # Ensure repo root is importable when running from a checkout.
    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    label = "warmup" if warmup else "timed"
    print(f"  spawning {label} child …", flush=True)
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        sys.stderr.write(proc.stdout or "")
        raise SystemExit(f"child failed with exit {proc.returncode}")
    # Child prints a single JSON object on stdout (may have trailing noise).
    line = proc.stdout.strip().splitlines()[-1]
    return json.loads(line)


def _median(xs):
    return float(statistics.median(xs)) if xs else None


def _load_baselines(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"baselines file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluate(band: str, report: dict, baselines: dict) -> list[str]:
    """Return list of failure messages (empty ⇒ pass)."""
    failures: list[str] = []
    bank = baselines.get(band) or {}
    expected_rows = bank.get("relevance_rows")
    observed_rows = report["medians"]["relevance_rows"]
    if expected_rows is None:
        report.setdefault("notes", []).append(
            f"{band}: relevance_rows not banked yet (observed {observed_rows}); "
            "commit that value to baselines.json after a deliberate measurement run"
        )
    elif observed_rows != expected_rows:
        failures.append(
            f"{band}: relevance_rows mismatch — expected {expected_rows}, "
            f"got {observed_rows} (semantics change; hard fail)"
        )

    reason_max = bank.get("reason_s_max")
    observed_reason = report["medians"]["reason_s"]
    if reason_max is None:
        # Timing threshold not banked yet — do not fail the job on speed.
        report.setdefault("notes", []).append(
            f"{band}: reason_s_max not banked; median reason_s={observed_reason:.4f}s "
            "(record after 3× workflow_dispatch, threshold = 2× worst median)"
        )
    elif observed_reason > reason_max:
        failures.append(
            f"{band}: reason_s {observed_reason:.4f}s exceeds threshold "
            f"{reason_max:.4f}s — may be a real regression or runner noise; "
            "re-run once before investigating"
        )
    return failures


def _parent_main(args) -> int:
    baselines = _load_baselines(args.baselines)
    if not args.fixture.exists():
        raise SystemExit(f"fixture not found: {args.fixture}")
    if not args.customers.exists():
        raise SystemExit(f"customers not found: {args.customers}")

    if not args.skip_warmup:
        _spawn_child(args, warmup=True)

    runs = []
    for i in range(args.repeats):
        print(f"  timed run {i + 1}/{args.repeats}", flush=True)
        runs.append(_spawn_child(args, warmup=False))

    report = {
        "band": args.band,
        "fixture": str(args.fixture),
        "customers": str(args.customers),
        "repeats": args.repeats,
        "runs": runs,
        "medians": {
            "import_s": _median([r["import_s"] for r in runs]),
            "setup_s": _median([r["setup_s"] for r in runs]),
            "reason_s": _median([r["reason_s"] for r in runs]),
            "relevance_rows": int(statistics.median([r["relevance_rows"] for r in runs])),
        },
        "python": runs[0]["python"] if runs else sys.version.split()[0],
        "pyreason": runs[0].get("pyreason", "unknown") if runs else "unknown",
        "notes": [],
    }

    # All repeats must agree on relevance_rows (determinism).
    row_set = {r["relevance_rows"] for r in runs}
    if len(row_set) != 1:
        report["notes"].append(f"relevance_rows disagreed across runs: {sorted(row_set)}")

    failures = _evaluate(args.band, report, baselines)
    # Also fail if repeats disagreed on rows.
    if len(row_set) != 1:
        failures.append(f"non-deterministic relevance_rows across repeats: {sorted(row_set)}")

    report["pass"] = len(failures) == 0
    report["failures"] = failures

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    med = report["medians"]
    status = "PASS" if report["pass"] else "FAIL"
    print(
        f"{status} {args.band}: reason_s_med={med['reason_s']:.4f}s "
        f"setup_s_med={med['setup_s']:.4f}s import_s_med={med['import_s']:.4f}s "
        f"relevance_rows={med['relevance_rows']} → {args.out}"
    )
    for msg in report.get("notes", []):
        print(f"NOTE: {msg}")
    for msg in failures:
        print(f"FAIL: {msg}", file=sys.stderr)
    return 0 if report["pass"] else 1


def main(argv=None) -> int:
    args = _parse_args(argv)
    if args.child:
        payload = _run_program(args.fixture, args.customers)
        # Single JSON line for the parent to parse.
        print(json.dumps(payload), flush=True)
        return 0
    return _parent_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
