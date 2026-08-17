#!/usr/bin/env python3
"""Deterministic Pokec fixture generator for the paper §4.2-shaped CI bench.

Reconstructs an id-prefix induced subgraph from SNAP soc-Pokec files.
Every output byte is a pure function of the SNAP inputs and the constants
below — no randomness, no set-iteration-order dependence.

Usage (from repo root)::

  python benchmarks/pokec/generate_fixtures.py \\
    --data-dir benchmarks/pokec/data --rungs 2k --write

  python benchmarks/pokec/generate_fixtures.py \\
    --data-dir benchmarks/pokec/data --rungs 10k --write
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import xml.sax.saxutils as saxutils
from pathlib import Path

# Paper customer proportion (arXiv:2302.13482 §4.2).
CUSTOMER_NUMER = 2308
CUSTOMER_DENOM = 1_632_803

# Exact SNAP integrity checks (gunzip line counts).
EXPECTED_RELATIONSHIP_LINES = 30_622_564
EXPECTED_PROFILE_LINES = 1_632_803

PET_STEMS = (
    ("psa", "dog"),
    ("pes", "dog"),
    ("psik", "dog"),
    ("psy", "dog"),
    ("mack", "cat"),
    ("macic", "cat"),
    ("rybk", "fish"),
    ("rybic", "fish"),
    ("akvari", "fish"),
    ("vtacik", "bird"),
    ("vtaci", "bird"),
    ("kanarik", "bird"),
    ("papagaj", "parrot"),
    ("andulk", "parrot"),
    ("korytnac", "turtle"),
    ("skrecok", "hamster"),
    ("skreck", "hamster"),
    ("hlodav", "rodent"),
    ("mys", "rodent"),
    ("potkan", "rodent"),
    ("morca", "guineapig"),
    ("zajac", "rabbit"),
    ("kralik", "rabbit"),
    ("had", "snake"),
    ("pavuk", "spider"),
    ("jaster", "lizard"),
    ("kon", "horse"),
    ("fretk", "ferret"),
    ("ryb", "fish"),
)

RUNG_N = {
    "2k": 2_000,
    "10k": 10_000,
}

# Banked after first successful generation. 10k counts are externally verified.
# 2k counts are filled by this script on first --write and asserted thereafter.
EXPECTED_COUNTS = {
    "10k": {
        "users": 10_000,
        "friend_edges": 121_716,
        "haspet_edges": 6_204,
        "customers": 14,
    },
    "2k": {
        "users": 2_000,
        "friend_edges": 18_315,
        "haspet_edges": 1_203,
        "customers": 5,
    },
}


def _pets_from_text(text: str) -> list[str]:
    if not text or text.lower() == "null":
        return []
    lowered = text.lower()
    found: set[str] = set()
    for stem, token in PET_STEMS:
        if stem in lowered:
            found.add(token)
    return sorted(found)


def _pick_customers(owners: list[int], n_users: int) -> list[int]:
    proportion = CUSTOMER_NUMER / CUSTOMER_DENOM
    target = max(5, round(proportion * n_users))
    target = min(target, len(owners))
    if target == 0:
        return []
    step = len(owners) / target
    return [owners[int(i * step)] for i in range(target)]


def _open_maybe_gzip(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def load_profiles(profiles_path: Path, max_id: int | None = None) -> tuple[list[int], dict[int, list[str]], int]:
    """Return (sorted user_ids, pets_by_id for kept ids, line_count).

    If max_id is set, only profiles with user_id <= max_id are kept in pets_by_id;
    all ids are still collected for sorting/selection (caller filters by N).
    """
    user_ids: list[int] = []
    pets_by_id: dict[int, list[str]] = {}
    lines = 0
    with _open_maybe_gzip(profiles_path) as fh:
        for raw in fh:
            lines += 1
            # SNAP profiles may start with comment lines.
            if raw.startswith("#"):
                continue
            parts = raw.rstrip("\n").split("\t")
            if not parts or parts[0] == "":
                continue
            uid = int(parts[0])
            user_ids.append(uid)
            pets_text = parts[13] if len(parts) > 13 else ""
            if max_id is None or uid <= max_id:
                pets = _pets_from_text(pets_text)
                if pets:
                    pets_by_id[uid] = pets
    return user_ids, pets_by_id, lines


def load_friend_edges(rel_path: Path, kept: set[int]) -> tuple[list[tuple[int, int]], int]:
    edges: list[tuple[int, int]] = []
    lines = 0
    with _open_maybe_gzip(rel_path) as fh:
        for raw in fh:
            lines += 1
            if raw.startswith("#"):
                continue
            parts = raw.split()
            if len(parts) < 2:
                continue
            src, dst = int(parts[0]), int(parts[1])
            if src in kept and dst in kept:
                edges.append((src, dst))
    return edges, lines


def build_rung(
    profiles_path: Path,
    relationships_path: Path,
    n: int,
    verify_snap_counts: bool = True,
) -> dict:
    # First pass: collect all ids, sort, take N smallest — then we know the
    # id cutoff so a second pet-filter pass is unnecessary if we load pets for
    # all profiles. Profiles is large; we load once and filter.
    print(f"  reading profiles: {profiles_path}", file=sys.stderr)
    all_ids, pets_all, profile_lines = load_profiles(profiles_path, max_id=None)
    if verify_snap_counts and profile_lines != EXPECTED_PROFILE_LINES:
        raise SystemExit(
            f"profiles line count {profile_lines} != expected {EXPECTED_PROFILE_LINES}"
        )

    all_ids_sorted = sorted(set(all_ids))
    if len(all_ids_sorted) < n:
        raise SystemExit(f"only {len(all_ids_sorted)} unique users; need {n}")
    kept_ids = all_ids_sorted[:n]
    kept = set(kept_ids)
    max_kept = kept_ids[-1]

    pets_by_id = {uid: pets for uid, pets in pets_all.items() if uid in kept}
    # Owners: kept users with ≥1 pet, sorted ascending.
    owners = sorted(pets_by_id.keys())
    customers = _pick_customers(owners, n)

    # Pet token universe for this rung.
    pet_tokens: set[str] = set()
    for pets in pets_by_id.values():
        pet_tokens.update(pets)
    pet_tokens_sorted = sorted(pet_tokens)

    print(f"  reading relationships (kept ≤ id {max_kept}): {relationships_path}", file=sys.stderr)
    friend_edges, rel_lines = load_friend_edges(relationships_path, kept)
    if verify_snap_counts and rel_lines != EXPECTED_RELATIONSHIP_LINES:
        raise SystemExit(
            f"relationships line count {rel_lines} != expected {EXPECTED_RELATIONSHIP_LINES}"
        )

    haspet_edges: list[tuple[int, str]] = []
    for uid in owners:  # ascending owner id
        for token in pets_by_id[uid]:  # already sorted
            haspet_edges.append((uid, token))

    return {
        "n": n,
        "kept_ids": kept_ids,
        "friend_edges": friend_edges,
        "haspet_edges": haspet_edges,
        "pet_tokens": pet_tokens_sorted,
        "customers": customers,
        "counts": {
            "users": len(kept_ids),
            "friend_edges": len(friend_edges),
            "haspet_edges": len(haspet_edges),
            "customers": len(customers),
            "pet_tokens": len(pet_tokens_sorted),
        },
    }


def write_graphml(path: Path, rung: dict) -> None:
    """Write deterministic GraphML: users asc, pets sorted; friends SNAP order; hasPet owner asc."""
    path.parent.mkdir(parents=True, exist_ok=True)
    esc = saxutils.escape
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("<?xml version='1.0' encoding='utf-8'?>\n")
        fh.write(
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
            'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n'
        )
        fh.write('  <key id="friend" for="edge" attr.name="friend" attr.type="long" />\n')
        fh.write('  <key id="hasPet" for="edge" attr.name="hasPet" attr.type="long" />\n')
        fh.write('  <graph edgedefault="directed">\n')
        for uid in rung["kept_ids"]:
            fh.write(f'    <node id="u{uid}" />\n')
        for token in rung["pet_tokens"]:
            fh.write(f'    <node id="{esc(token)}" />\n')
        for src, dst in rung["friend_edges"]:
            fh.write(f'    <edge source="u{src}" target="u{dst}">\n')
            fh.write('      <data key="friend">1</data>\n')
            fh.write("    </edge>\n")
        for uid, token in rung["haspet_edges"]:
            fh.write(f'    <edge source="u{uid}" target="{esc(token)}">\n')
            fh.write('      <data key="hasPet">1</data>\n')
            fh.write("    </edge>\n")
        fh.write("  </graph>\n")
        fh.write("</graphml>\n")


def write_customers(path: Path, customers: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(customers, indent=2) + "\n", encoding="utf-8")


def assert_counts(rung_name: str, counts: dict) -> None:
    expected = EXPECTED_COUNTS.get(rung_name)
    if expected is None:
        return
    for key in ("users", "friend_edges", "haspet_edges", "customers"):
        banked = expected.get(key)
        if banked is None:
            continue
        if counts[key] != banked:
            raise SystemExit(
                f"{rung_name} {key}={counts[key]} != banked {banked} — "
                "fixture generation diverged from the verified spec"
            )


def _parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path("benchmarks/pokec/data"),
        help="Directory with soc-pokec-*.txt.gz",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("benchmarks/pokec/fixtures"),
        help="Where to write GraphML + customers JSON",
    )
    p.add_argument(
        "--rungs",
        nargs="+",
        choices=sorted(RUNG_N.keys()),
        default=["2k"],
        help="Which fixture rungs to build",
    )
    p.add_argument(
        "--write",
        action="store_true",
        help="Write GraphML + customers JSON (otherwise only print counts)",
    )
    p.add_argument(
        "--skip-snap-verify",
        action="store_true",
        help="Skip exact SNAP line-count checks (debug only)",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    profiles = args.data_dir / "soc-pokec-profiles.txt.gz"
    relationships = args.data_dir / "soc-pokec-relationships.txt.gz"
    if not profiles.exists():
        # Allow uncompressed fallback.
        profiles = args.data_dir / "soc-pokec-profiles.txt"
    if not relationships.exists():
        relationships = args.data_dir / "soc-pokec-relationships.txt"
    if not profiles.exists() or not relationships.exists():
        raise SystemExit(
            f"SNAP files not found under {args.data_dir}. "
            "Download soc-pokec-profiles.txt.gz and "
            "soc-pokec-relationships.txt.gz from SNAP."
        )

    for rung_name in args.rungs:
        n = RUNG_N[rung_name]
        print(f"=== building {rung_name} (N={n}) ===", file=sys.stderr)
        rung = build_rung(
            profiles,
            relationships,
            n,
            verify_snap_counts=not args.skip_snap_verify,
        )
        counts = rung["counts"]
        print(json.dumps({"rung": rung_name, **counts}, indent=2))
        assert_counts(rung_name, counts)

        # On first 2k generation, print the values to bank into EXPECTED_COUNTS.
        banked = EXPECTED_COUNTS.get(rung_name, {})
        if any(banked.get(k) is None for k in ("friend_edges", "haspet_edges", "customers")):
            print(
                f"NOTE: bank these into EXPECTED_COUNTS[{rung_name!r}]: "
                f"friend_edges={counts['friend_edges']}, "
                f"haspet_edges={counts['haspet_edges']}, "
                f"customers={counts['customers']}",
                file=sys.stderr,
            )

        if args.write:
            graphml = args.out_dir / f"pokec-{rung_name}.graphml"
            customers_path = args.out_dir / f"pokec-{rung_name}-customers.json"
            write_graphml(graphml, rung)
            write_customers(customers_path, rung["customers"])
            print(f"wrote {graphml} and {customers_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
