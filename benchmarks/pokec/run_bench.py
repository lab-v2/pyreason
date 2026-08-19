#!/usr/bin/env python3
"""Pokec relevance-diffusion performance runner (paper §4.2 shape).

Standalone: stdlib + pyreason only. Fresh child process per measurement;
thresholds apply to ``reason_s`` only. Semantic tripwire via ``relevance_rows``.

Parent mode (default)::

  python benchmarks/pokec/run_bench.py \\
    --fixture benchmarks/pokec/fixtures/pokec-2k.graphml \\
    --customers benchmarks/pokec/fixtures/pokec-2k-customers.json \\
    --repeats 3 --type pokec-2k --out pokec-2k-report.json

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
    """Define and parse the command-line options for the Pokec benchmark runner."""
    # Create the command-line argument parser.
    # The script's top-level docstring is used as the --help description.
    p = argparse.ArgumentParser(description=__doc__)
    # Path to the GraphML fixture that PyReason will load and reason over.
    # This argument is required.
    p.add_argument(
        "--fixture",
        type=Path,
        required=True
    )
    # Path to the JSON file containing the initial customer user IDs.
    # These users receive the initial relevance facts.
    # This argument is required.
    p.add_argument(
        "--customers",
        type=Path,
        required=True
    )
    # Number of independent timed benchmark runs to perform.
    # By default, run the benchmark 3 times.
    p.add_argument(
        "--repeats",
        type=int,
        default=3
    )
    # Name of the benchmark size being tested.
    # Only the 2k and 10k Pokec benchmark types are allowed.
    # This determines which baseline values are used later for validation.
    p.add_argument(
        "--type",
        choices=("pokec-2k", "pokec-10k"),
        required=True
    )
    # Path where the final benchmark report JSON should be written.
    # If not specified, write pokec-report.json in the current directory.
    p.add_argument(
        "--out",
        type=Path,
        default=Path("pokec-report.json")
    )
    # Path to the JSON file containing the expected semantic and
    # performance baseline values for each benchmark type.
    # By default, use benchmarks/pokec/baselines.json.
    p.add_argument(
        "--baselines",
        type=Path,
        default=DEFAULT_BASELINES
    )
    # Internal flag used when the parent benchmark process launches
    # a fresh child process to perform one individual measurement.
    # Users/CI normally should not invoke --child directly.
    p.add_argument(
        "--child",
        action="store_true",
        help="Run one measurement in this process and print JSON to stdout",
    )
    # Optional debugging flag that prevents the parent from running
    # the initial untimed warmup process.
    p.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip the untimed warmup child (debug only)",
    )
    # Parse the supplied arguments and return them as an argparse Namespace.
    return p.parse_args(argv)


def _run_program(fixture: Path, customers_path: Path) -> dict:
    """Run one complete Pokec reasoning benchmark and return timing + correctness data."""
    # Read the customer seed IDs from the JSON file.
    # Example: [1, 412, 789, 1168, 1566]
    customers = json.loads(
        customers_path.read_text(encoding="utf-8")
    )
    # Start timing how long importing PyReason takes.
    t_import0 = time.perf_counter()
    # Import PyReason inside the timed section so import cost can be reported separately.
    import pyreason as pr
    # Calculate total PyReason import time.
    import_s = time.perf_counter() - t_import0
    # Start timing benchmark setup:
    # graph loading, rule creation, and initial customer facts.
    t_setup0 = time.perf_counter()
    # Disable verbose PyReason logging so console output does not interfere with the benchmark.
    pr.settings.verbose = False
    # Load the generated Pokec GraphML fixture into PyReason.
    # This contains the selected users, friendship edges, and hasPet edges.
    pr.load_graphml(str(fixture))
    # Add rule 1:
    # If y is fully relevant [1,1] and x is a friend of y,
    # then x becomes partially relevant [0.6,1] one timestep later.
    pr.add_rule(
        pr.Rule(
            "relevance(x) : [0.6,1] <-1 relevance(y):[1,1], friend(x,y):[1,1]",
            "relevance_friend_rule",
        )
    )
    # Add rule 2:
    # If y is fully relevant, x is y's friend, and x and y share a pet,
    # then x becomes fully relevant [1,1] one timestep later.
    pr.add_rule(
        pr.Rule(
            "relevance(x) : [1,1] <-1 relevance(y):[1,1], friend(x,y):[1,1], "
            "hasPet(x,p):[1,1], hasPet(y,p):[1,1]",
            "relevance_same_pet_rule",
        )
    )
    # Add the selected customers as initial relevance facts.
    # Every customer starts fully relevant from timestep 0 through timestep 8.
    for i, uid in enumerate(customers):
        pr.add_fact(
            pr.Fact(
                f"relevance(u{uid})",
                f"customer_{i}",
                0,
                8,
            )
        )
    # Record how long benchmark setup took.
    setup_s = time.perf_counter() - t_setup0
    # Start timing only the reasoning engine.
    # This is the main performance number used for regression detection.
    t_reason0 = time.perf_counter()
    # Run PyReason for 8 timesteps and store the resulting interpretation.
    interpretation = pr.reason(timesteps=8)
    # Record the total reasoning runtime.
    reason_s = time.perf_counter() - t_reason0
    # Extract the relevance results from the interpretation for each timestep.
    df_list = pr.filter_and_sort_nodes(
        interpretation,
        ["relevance"]
    )
    # Take the final timestep's relevance table.
    # If no result tables exist, use None.
    final_df = df_list[-1] if df_list else None
    # Count how many nodes have a relevance result at the final timestep.
    # This is used as a semantic correctness check.
    relevance_rows = (
        0
        if final_df is None
        else int(len(final_df))
    )
    # Try to record the installed PyReason version for the benchmark report.
    try:
        import pyreason as _pr_mod
        pyreason_version = getattr(
            _pr_mod,
            "__version__",
            "unknown",
        )
    # If version detection fails for any reason, continue the benchmark
    # and report the version as unknown instead of failing.
    except Exception:
        pyreason_version = "unknown"
    # Return all measurements and identifying information for this run.
    return {
        "import_s": import_s,
        "setup_s": setup_s,
        "reason_s": reason_s,
        "relevance_rows": relevance_rows,
        "python": sys.version.split()[0],
        "pyreason": pyreason_version,
    }


def _spawn_child(args, warmup: bool = False) -> dict:
    """Launch one fresh benchmark subprocess and return its JSON result."""
    # Build the exact terminal command that the child Python process will run.
    cmd = [
        # Use the same Python executable that is running the parent process.
        sys.executable,
        # Run this same run_bench.py file again.
        str(Path(__file__).resolve()),
        # Tell the new process that it is a child measurement,
        # not the main parent/controller process.
        "--child",
        # Pass the GraphML fixture path to the child.
        "--fixture",
        str(args.fixture),
        # Pass the customer seed JSON path to the child.
        "--customers",
        str(args.customers),
        # Pass which benchmark type/size is being tested.
        "--type",
        args.type,
        # A child performs exactly one measurement.
        "--repeats",
        "1",
        # The child does not need to write a report file.
        # Its result will be returned to the parent through stdout instead.
        "--out",
        os.devnull,
    ]
    # Copy the parent's environment variables so the child starts
    # with the same general execution environment.
    env = os.environ.copy()
    # Fix Python's hash randomization seed so each child process
    # uses the same hash behavior.
    env["PYTHONHASHSEED"] = "0"
    # Find the root directory of the PyReason repository.
    # run_bench.py is under benchmarks/pokec/, so parents[2]
    # moves back up to the repository root.
    repo_root = Path(__file__).resolve().parents[2]
    # Add the repository root to PYTHONPATH so the child process
    # can import the PyReason code from the current checkout.
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    # Label the child as either a warmup run or a timed run
    # for readable console output.
    label = "warmup" if warmup else "timed"
    # Print what kind of child process is about to start.
    # flush=True forces the message to appear immediately.
    print(f"  spawning {label} child …", flush=True)
    # Launch the child process and wait for it to finish.
    proc = subprocess.run(
        cmd,
        # Do not automatically raise an exception on nonzero exit;
        # handle failure manually below so stderr/stdout can be shown.
        check=False,
        # Capture the child's stdout and stderr instead of printing
        # them directly to the parent's terminal.
        capture_output=True,
        # Return stdout/stderr as normal strings instead of bytes.
        text=True,
        # Run the child using the environment configured above.
        env=env,
    )
    # If the child process failed, print its captured output
    # and stop the parent benchmark with an error.
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or "")
        sys.stderr.write(proc.stdout or "")
        raise SystemExit(
            f"child failed with exit {proc.returncode}"
        )
    # The child prints its result as JSON to stdout.
    # Take the final output line in case PyReason printed extra text first.
    line = proc.stdout.strip().splitlines()[-1]
    # Convert the JSON string back into a Python dictionary
    # and return the child's benchmark result to the parent.
    return json.loads(line)

def _median(xs):
    # Return the median value of the list as a float.
    # If the list is empty, return None instead.
    return float(statistics.median(xs)) if xs else None


def _evaluate(type_name: str, report: dict, baselines: dict) -> list[str]:
    """Compare benchmark results against expected baselines and return any failures."""
    # Store any correctness or performance failures found during evaluation.
    # If this list stays empty, the benchmark passes.
    failures: list[str] = []
    # Get the saved baseline values for this benchmark type.
    # Example: "pokec-2k" -> its expected relevance_rows and reason_s_max.
    # If the type does not exist in baselines, use an empty dictionary.
    bank = baselines.get(type_name) or {}
    # Get the expected number of final relevance rows from the baseline.
    expected_rows = bank.get("relevance_rows")
    # Get the median relevance-row count observed in the current benchmark runs.
    observed_rows = report["medians"]["relevance_rows"]
    # If no expected relevance count has been saved yet,
    # do not fail. Add a note saying this value still needs to be banked.
    if expected_rows is None:
        report.setdefault("notes", []).append(
            f"{type_name}: relevance_rows not banked yet (observed {observed_rows}); "
            "commit that value to baselines.json after a deliberate measurement run"
        )
    # If an expected count exists but the new benchmark produced a different
    # number of relevance rows, treat this as a correctness/semantic failure.
    elif observed_rows != expected_rows:
        failures.append(
            f"{type_name}: relevance_rows mismatch — expected {expected_rows}, "
            f"got {observed_rows} (semantics change; hard fail)"
        )
    # Get the maximum allowed reasoning time for this benchmark type.
    reason_max = bank.get("reason_s_max")
    # Get the median reasoning time measured in the current benchmark runs.
    observed_reason = report["medians"]["reason_s"]
    # If no performance threshold has been saved yet,
    # do not fail the benchmark. Add a note saying a threshold must be established.
    if reason_max is None:
        report.setdefault("notes", []).append(
            f"{type_name}: reason_s_max not banked; median reason_s={observed_reason:.4f}s "
            "(record after 3× workflow_dispatch, threshold = 2× worst median)"
        )
    # If the measured median reasoning time exceeds the allowed maximum,
    # record a performance-regression failure.
    elif observed_reason > reason_max:
        failures.append(
            f"{type_name}: reason_s {observed_reason:.4f}s exceeds threshold "
            f"{reason_max:.4f}s — may be a real regression or runner noise; "
            "re-run once before investigating"
        )
    # Return all failures found.
    # Empty list [] means the benchmark passed these checks.
    return failures

def _parent_main(args) -> int:
    """Run the full benchmark workflow in parent mode and return an exit code."""
    # Load the expected correctness and performance baselines
    # from baselines.json.
    baselines = _load_baselines(args.baselines)
    # Stop immediately if the GraphML fixture file does not exist.
    if not args.fixture.exists():
        raise SystemExit(f"fixture not found: {args.fixture}")
    # Stop immediately if the customer seed JSON file does not exist.
    if not args.customers.exists():
        raise SystemExit(f"customers not found: {args.customers}")
    # Run one untimed child process first unless warmup was explicitly skipped.
    # This helps keep first-run compilation/cache effects out of measured runs.
    if not args.skip_warmup:
        _spawn_child(args, warmup=True)
    # Store the result dictionary from each timed child process.
    runs = []
    # Launch the requested number of fresh timed child processes.
    for i in range(args.repeats):
        # Print progress such as "timed run 1/3".
        print(f"  timed run {i + 1}/{args.repeats}", flush=True)
        # Run one benchmark measurement in a fresh child process
        # and save its returned timing/correctness data.
        runs.append(_spawn_child(args, warmup=False))
    # Build the final benchmark report using all measured runs.
    report = {
        # Record which benchmark type was executed.
        "type": args.type,
        # Record which GraphML fixture was used.
        "fixture": str(args.fixture),
        # Record which customer seed file was used.
        "customers": str(args.customers),
        # Record how many timed benchmark runs were performed.
        "repeats": args.repeats,
        # Store the complete raw result from every timed child.
        "runs": runs,
        # Calculate one representative median value for each metric.
        "medians": {
            # Median PyReason import time across all measured runs.
            "import_s": _median([r["import_s"] for r in runs]),
            # Median graph/rule/fact setup time.
            "setup_s": _median([r["setup_s"] for r in runs]),
            # Median actual reasoning time.
            # This is the main performance metric.
            "reason_s": _median([r["reason_s"] for r in runs]),
            # Median final relevance-row count.
            # Normally every run should already have exactly the same count.
            "relevance_rows": int(
                statistics.median(
                    [r["relevance_rows"] for r in runs]
                )
            ),
        },
        # Record the Python version used by the child processes.
        # If no runs somehow exist, fall back to the parent Python version.
        "python": (
            runs[0]["python"]
            if runs
            else sys.version.split()[0]
        ),
        # Record the PyReason version reported by the first child.
        # If unavailable, use "unknown".
        "pyreason": (
            runs[0].get("pyreason", "unknown")
            if runs
            else "unknown"
        ),
        # Start with an empty list for informational notes.
        "notes": [],
    }
    # Collect all distinct relevance-row counts returned by the repeated runs.
    # Example: {1573} means every run agreed.
    row_set = {r["relevance_rows"] for r in runs}
    # If more than one different relevance-row count exists,
    # note that the benchmark was not deterministic.
    if len(row_set) != 1:
        report["notes"].append(
            f"relevance_rows disagreed across runs: {sorted(row_set)}"
        )
    # Compare the median benchmark results against the saved baselines.
    # This checks both correctness and performance.
    failures = _evaluate(
        args.type,
        report,
        baselines
    )
    # Independently fail the benchmark if repeated runs produced
    # different relevance-row counts.
    if len(row_set) != 1:
        failures.append(
            f"non-deterministic relevance_rows across repeats: "
            f"{sorted(row_set)}"
        )
    # The benchmark passes only when there are no failure messages.
    report["pass"] = len(failures) == 0
    # Store all failure messages in the final report.
    report["failures"] = failures
    # Make sure the parent directory for the output report exists.
    args.out.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    # Write the complete benchmark report to JSON.
    args.out.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )
    # Create a short alias to the median metrics for easier printing.
    med = report["medians"]
    # Convert the boolean pass result into a readable status string.
    status = "PASS" if report["pass"] else "FAIL"
    # Print a one-line benchmark summary.
    print(
        f"{status} {args.type}: "
        f"reason_s_med={med['reason_s']:.4f}s "
        f"setup_s_med={med['setup_s']:.4f}s "
        f"import_s_med={med['import_s']:.4f}s "
        f"relevance_rows={med['relevance_rows']} "
        f"→ {args.out}"
    )
    # Print any informational notes.
    for msg in report.get("notes", []):
        print(f"NOTE: {msg}")
    # Print each failure message to stderr.
    for msg in failures:
        print(f"FAIL: {msg}", file=sys.stderr)
    # Return exit code 0 when the benchmark passes.
    # Return exit code 1 when it fails.
    # GitHub Actions uses this exit code to decide whether the job is green or red.
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
