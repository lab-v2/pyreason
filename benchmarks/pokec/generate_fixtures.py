#!/usr/bin/env python3
"""Deterministic Pokec fixture generator for the paper §4.2-shaped CI bench.

Reconstructs an id-prefix induced subgraph from SNAP soc-Pokec files.
Every output byte is a pure function of the SNAP inputs and the constants
below — no randomness, no set-iteration-order dependence.

Usage (from repo root)::

  python benchmarks/pokec/generate_fixtures.py \\
    --data-dir benchmarks/pokec/data --size 2k --write

  python benchmarks/pokec/generate_fixtures.py \\
    --data-dir benchmarks/pokec/data --size 10k --write
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

SIZE_N = {
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

# Convert a user's free-text pets field into sorted, normalized pet tokens.
def _pets_from_text(text: str) -> list[str]:
    if not text or text.lower() == "null":
        return []
    lowered = text.lower()
    found: set[str] = set()
    for stem, token in PET_STEMS:
        if stem in lowered:
            found.add(token)
    return sorted(found)

 # Calculate the proportion of customers used in the original Pokec experiment.
def _pick_customers(owners: list[int], n_users: int) -> list[int]:
    proportion = CUSTOMER_NUMER / CUSTOMER_DENOM
    # Calculate how many customers this fixture should have based on its number of users.
    # Always select at least 5 customers.
    target = max(5, round(proportion * n_users))
    # We can never select more customers than the number of available pet owners.
    target = min(target, len(owners))
    # If there are no available pet owners, there are no customers to select.
    if target == 0:
        return []
    # Calculate how far apart customer selections should be in the sorted owners list.
    step = len(owners) / target
    # Select 'target' customers evenly across the owners list.
    return [owners[int(i * step)] for i in range(target)]

# Open a text file normally or through gzip depending on its extension.
def _open_maybe_gzip(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def load_profiles(
    profiles_path: Path,
    max_id: int | None = None
) -> tuple[list[int], dict[int, list[str]], int]:
    # Store every valid Pokec user ID found in the profiles file.
    user_ids: list[int] = []
    # Map users with recognized pets to their normalized pet categories.
    # Example: {412: ["cat", "dog"], 789: ["fish"]}
    pets_by_id: dict[int, list[str]] = {}
    # Count every line read so we can later verify that the full SNAP file was used.
    line_count = 0
    # Open the SNAP profiles file, supporting either .txt or .txt.gz.
    with _open_maybe_gzip(profiles_path) as fh:
        # Process one Pokec user profile at a time.
        for line in fh:
            # Count the raw profile line for SNAP dataset integrity verification.
            line_count += 1
            # Remove the newline and split the tab-separated profile into columns.
            parts = line.rstrip("\n").split("\t")
            # Skip malformed rows that do not contain a user ID.
            if not parts or not parts[0]:
                continue
            try:
                # Column 0 of the SNAP profile contains the user's numeric ID.
                uid = int(parts[0])
            except ValueError:
                # Skip the row if its user ID cannot be converted to an integer.
                continue
            # Optionally ignore users whose IDs are above the requested maximum.
            if max_id is not None and uid > max_id:
                continue
            # Save this valid user ID as part of the available Pokec population.
            user_ids.append(uid)
            # Column 13 contains the user's free-text pets information.
            # Use an empty string if the row does not contain that column.
            pets_text = parts[13] if len(parts) > 13 else ""
            # Convert the raw pets text into normalized categories such as
            # "dog", "cat", "fish", etc.
            pets = _pets_from_text(pets_text)
            # Only users with at least one recognized pet are stored as pet owners.
            if pets:
                pets_by_id[uid] = pets
    # Return:
    # 1. every valid user ID,
    # 2. pet ownership information for users with recognized pets,
    # 3. total number of raw profile lines read.
    return user_ids, pets_by_id, line_count

def load_friend_edges(
    rel_path: Path,
    kept: set[int]
) -> tuple[list[tuple[int, int]], int]:
    """Read Pokec relationships and keep only edges between selected fixture users."""
    # Store the friendship edges where both users belong to our selected fixture.
    # Example: [(1, 412), (412, 789)]
    edges: list[tuple[int, int]] = []
    # Count every raw line in the SNAP relationships file for integrity verification.
    lines = 0
    # Open the SNAP relationships file, supporting either .txt or .txt.gz.
    with _open_maybe_gzip(rel_path) as fh:
        # Process each relationship line in the original SNAP dataset.
        for raw in fh:
            # Count every raw line so we can verify the complete SNAP file was read.
            lines += 1
            # Ignore comment/header lines because they do not represent relationships.
            if raw.startswith("#"):
                continue
            # Split the line into its whitespace-separated values.
            # The first two values represent the source and destination user IDs.
            parts = raw.split()
            # Skip malformed lines that do not contain both user IDs.
            if len(parts) < 2:
                continue
            # Convert the source and destination user IDs from strings to integers.
            src, dst = int(parts[0]), int(parts[1])
            # Only keep the friendship if BOTH users are part of our selected
            # 2k or 10k fixture.
            if src in kept and dst in kept:
                edges.append((src, dst))
    # Return:
    # 1. all friendship edges contained within our selected fixture,
    # 2. the total number of raw relationship lines read.
    return edges, lines


def build_size(
    profiles_path: Path,
    relationships_path: Path,
    n: int,
    verify_snap_counts: bool = True,
) -> dict:
    """Build one deterministic Pokec benchmark fixture containing n users."""
    # Read the entire SNAP profiles file once.
    # Returns all user IDs, pet information for users with recognized pets,
    # and the total number of profile lines read.
    print(f"  reading profiles: {profiles_path}", file=sys.stderr)
    all_ids, pets_all, profile_lines = load_profiles(
        profiles_path,
        max_id=None
    )
    # If SNAP verification is enabled, make sure we read the expected
    # number of rows from the original profiles dataset.
    if verify_snap_counts and profile_lines != EXPECTED_PROFILE_LINES:
        raise SystemExit(
            f"profiles line count {profile_lines} != expected {EXPECTED_PROFILE_LINES}"
        )
    # Remove duplicate user IDs and sort them in ascending order.
    # Sorting makes the user selection deterministic.
    all_ids_sorted = sorted(set(all_ids))
    # Make sure the SNAP dataset contains enough unique users
    # to construct the requested fixture size.
    if len(all_ids_sorted) < n:
        raise SystemExit(f"only {len(all_ids_sorted)} unique users; need {n}")
    # Select the N smallest user IDs for this fixture.
    # Example: n=10_000 selects the first 10,000 sorted Pokec user IDs.
    kept_ids = all_ids_sorted[:n]
    # Convert the selected IDs to a set for fast membership checks.
    # This is used when filtering profiles and friendship edges.
    kept = set(kept_ids)
    # Store the largest selected user ID.
    # This is currently used for the progress/debug message below.
    max_kept = kept_ids[-1]
    # Keep pet information only for users included in this fixture.
    # Example: if user 50,000 is not in a 2k fixture, discard their pet data.
    pets_by_id = {
        uid: pets
        for uid, pets in pets_all.items()
        if uid in kept
    }
    # Get the selected users who have at least one recognized pet.
    # Sorting keeps customer selection and GraphML generation deterministic.
    owners = sorted(pets_by_id.keys())
    # Choose the initial customer/relevance seed users from the pet owners.
    # The number of customers is based on the original paper's proportion.
    customers = _pick_customers(owners, n)
    # Collect every unique pet category that appears in this fixture.
    # These will later become pet nodes in the GraphML graph.
    pet_tokens: set[str] = set()
    # Add each user's normalized pets to the set of pet categories.
    for pets in pets_by_id.values():
        pet_tokens.update(pets)
    # Sort the pet categories so their output order is deterministic.
    # Example: ["bird", "cat", "dog", "fish", ...]
    pet_tokens_sorted = sorted(pet_tokens)
    # Read the original SNAP relationships file and keep only friendships
    # where both users belong to this fixture.
    print(
        f"  reading relationships (kept ≤ id {max_kept}): {relationships_path}",
        file=sys.stderr
    )
    friend_edges, rel_lines = load_friend_edges(
        relationships_path,
        kept
    )
    # If SNAP verification is enabled, make sure the complete original
    # relationships dataset contained the expected number of lines.
    if verify_snap_counts and rel_lines != EXPECTED_RELATIONSHIP_LINES:
        raise SystemExit(
            f"relationships line count {rel_lines} != expected {EXPECTED_RELATIONSHIP_LINES}"
        )
    # Store the graph edges connecting users to the pets they own.
    # Example: (412, "dog") represents u412 --hasPet--> dog.
    haspet_edges: list[tuple[int, str]] = []
    # Process pet owners in ascending user-ID order.
    for uid in owners:
        # Each user's pet list is already sorted.
        for token in pets_by_id[uid]:
            # Create one hasPet edge for this user/pet combination.
            haspet_edges.append((uid, token))
    # Return all information needed to write and validate the fixture.
    return {
        # Requested fixture population size.
        "n": n,
        # The actual user IDs included in the fixture.
        "kept_ids": kept_ids,
        # Friendship relationships between selected users.
        "friend_edges": friend_edges,
        # User-to-pet relationships.
        "haspet_edges": haspet_edges,
        # Unique pet categories that need to exist as graph nodes.
        "pet_tokens": pet_tokens_sorted,
        # Users that begin as the customer/relevance seeds.
        "customers": customers,
        # Summary statistics used to validate that fixture generation
        # still matches the banked benchmark specification.
        "counts": {
            "users": len(kept_ids),
            "friend_edges": len(friend_edges),
            "haspet_edges": len(haspet_edges),
            "customers": len(customers),
            "pet_tokens": len(pet_tokens_sorted),
        },
    }


def write_graphml(path: Path, fixture: dict) -> None:
    """Write the generated Pokec fixture to a deterministic GraphML file."""
    # Make sure the directory where the GraphML file will be saved exists.
    # parents=True creates any missing parent directories.
    # exist_ok=True prevents an error if the directory already exists.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create a short alias for the XML escaping function.
    # This makes strings safe to place inside XML.
    # Example: "cats & dogs" becomes "cats &amp; dogs".
    esc = saxutils.escape
    # Open the output GraphML file for writing as UTF-8 text.
    # newline="\n" ensures consistent line endings across operating systems.
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        # Write the standard XML declaration at the top of the file.
        fh.write("<?xml version='1.0' encoding='utf-8'?>\n")
        # Start the GraphML document and declare the standard GraphML XML namespaces.
        fh.write(
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
            'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n'
        )
        # Define "friend" as an edge attribute.
        # PyReason will later recognize edges carrying this attribute as friend relations.
        fh.write(
            '  <key id="friend" for="edge" '
            'attr.name="friend" attr.type="long" />\n'
        )
        # Define "hasPet" as another edge attribute.
        # These edges connect users to their normalized pet-category nodes.
        fh.write(
            '  <key id="hasPet" for="edge" '
            'attr.name="hasPet" attr.type="long" />\n'
        )
        # Start the actual graph.
        # edgedefault="directed" means every edge has a source and a target direction.
        fh.write('  <graph edgedefault="directed">\n')
        # Write one graph node for every selected Pokec user.
        # User IDs are prefixed with "u" to distinguish users from pet nodes.
        # Example: user 412 becomes <node id="u412" />.
        for uid in fixture["kept_ids"]:
            fh.write(f'    <node id="u{uid}" />\n')
        # Write one graph node for every unique pet category in the fixture.
        # Example: "dog" becomes <node id="dog" />.
        # esc() protects the token in case it contains XML-special characters.
        for token in fixture["pet_tokens"]:
            fh.write(f'    <node id="{esc(token)}" />\n')
        # Write every friendship relationship between selected Pokec users.
        for src, dst in fixture["friend_edges"]:
            # Create the directed edge from the source user to the destination user.
            # Example: (12, 50) becomes u12 -> u50.
            fh.write(
                f'    <edge source="u{src}" target="u{dst}">\n'
            )
            # Mark this edge as a "friend" relationship with value 1.
            fh.write('      <data key="friend">1</data>\n')
            # Close this friendship edge.
            fh.write("    </edge>\n")
        # Write every relationship between a user and a pet category they own.
        for uid, token in fixture["haspet_edges"]:
            # Create a directed edge from the user to the pet node.
            # Example: (412, "dog") becomes u412 -> dog.
            fh.write(
                f'    <edge source="u{uid}" target="{esc(token)}">\n'
            )
            # Mark this edge as a "hasPet" relationship with value 1.
            fh.write('      <data key="hasPet">1</data>\n')
            # Close this hasPet edge.
            fh.write("    </edge>\n")
        # Close the graph itself.
        fh.write("  </graph>\n")
        # Close the GraphML document.
        fh.write("</graphml>\n")

#Just writes the array of the customers to a JSON file.
def write_customers(path: Path, customers: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(customers, indent=2) + "\n", encoding="utf-8")


def assert_counts(size_name: str, counts: dict) -> None:
    """Verify that the generated fixture counts match the banked expected counts."""
    # Get the expected counts for this fixture size from EXPECTED_COUNTS.
    # Example: size_name="10k" gets the expected users, friendships,
    # hasPet edges, and customer count for the 10k fixture.
    expected = EXPECTED_COUNTS.get(size_name)
    # If there are no expected counts stored for this size,
    # there is nothing to validate, so exit the function.
    if expected is None:
        return
    # Check each important property of the generated fixture.
    for key in ("users", "friend_edges", "haspet_edges", "customers"):
        # Get the previously verified/banked expected value for this property.
        # Example: for 10k and "friend_edges", banked = 121_716.
        banked = expected.get(key)
        # If this particular property does not have a banked expected value,
        # skip its validation.
        if banked is None:
            continue
        # Compare the newly generated count against the verified expected count.
        if counts[key] != banked:
            # Stop fixture generation immediately if the counts differ.
            # A mismatch means the generated benchmark is no longer identical
            # to the benchmark specification we previously verified.
            raise SystemExit(
                f"{size_name} {key}={counts[key]} != banked {banked} — "
                "fixture generation diverged from the verified spec"
            )


def _parse_args():
    """Define and parse the command-line options for the fixture generator."""
    # Create the command-line argument parser.
    # description=__doc__ uses the file's top-level docstring as the
    # description shown when running the script with --help.
    p = argparse.ArgumentParser(description=__doc__)
    # Define where the original downloaded SNAP Pokec data is located.
    # The value is converted into a Path object automatically.
    # If --data-dir is not provided, use benchmarks/pokec/data.
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path("benchmarks/pokec/data"),
        help="Directory with soc-pokec-*.txt.gz",
    )
    # Define where the generated benchmark fixture files should be saved.
    # This directory will contain the GraphML graph and customers JSON.
    # If --out-dir is not provided, use benchmarks/pokec/fixtures.
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("benchmarks/pokec/fixtures"),
        help="Where to write GraphML + customers JSON",
    )
    # Define which fixture size or sizes should be generated.
    # nargs="+" allows the user to provide one or more sizes.
    # choices restricts the values to the sizes defined in SIZE_N.
    # If no --size is provided, generate only the 2k fixture.
    p.add_argument(
        "--size",
        nargs="+",
        choices=sorted(SIZE_N.keys()),
        default=["2k"],
        help="Which fixture size(s) to build (2k, 10k)",
    )
    # Add an optional --write flag.
    # If --write is present, save the generated GraphML and customers JSON.
    # If it is absent, build/validate the fixture without writing those files.
    p.add_argument(
        "--write",
        action="store_true",
        help="Write GraphML + customers JSON (otherwise only print counts)",
    )
    # Add an optional debugging flag that disables the exact SNAP
    # source-file line-count verification.
    # By default, SNAP verification remains enabled.
    p.add_argument(
        "--skip-snap-verify",
        action="store_true",
        help="Skip exact SNAP line-count checks (debug only)",
    )
    # Read the arguments supplied in the terminal and return them
    # as an argparse Namespace object.
    return p.parse_args()


def main() -> int:
    """Run the complete Pokec fixture generation and validation process."""
    # Read the command-line arguments provided by the user.
    # This gives us the data directory, output directory, requested sizes,
    # whether to write files, and whether SNAP verification should be skipped.
    args = _parse_args()
    # Build the expected path to the compressed SNAP profiles file.
    profiles = args.data_dir / "soc-pokec-profiles.txt.gz"
    # Build the expected path to the compressed SNAP relationships file.
    relationships = args.data_dir / "soc-pokec-relationships.txt.gz"
    # If the compressed profiles file does not exist,
    # try using the uncompressed .txt version instead.
    if not profiles.exists():
        profiles = args.data_dir / "soc-pokec-profiles.txt"
    # If the compressed relationships file does not exist,
    # try using the uncompressed .txt version instead.
    if not relationships.exists():
        relationships = args.data_dir / "soc-pokec-relationships.txt"
    # After checking both compressed and uncompressed versions,
    # stop if either required SNAP source file still cannot be found.
    if not profiles.exists() or not relationships.exists():
        raise SystemExit(
            f"SNAP files not found under {args.data_dir}. "
            "Download soc-pokec-profiles.txt.gz and "
            "soc-pokec-relationships.txt.gz from SNAP."
        )
    # Build each fixture size requested through --size.
    # Example: --size 2k 10k causes this loop to run twice.
    for size_name in args.size:
        # Convert the size name into its actual number of users.
        # Example: "2k" -> 2,000 and "10k" -> 10,000.
        n = SIZE_N[size_name]
        # Print which fixture is currently being generated.
        print(f"=== building {size_name} (N={n}) ===", file=sys.stderr)
        # Build the complete fixture in memory from the SNAP profiles
        # and relationships files.
        fixture = build_size(
            profiles,
            relationships,
            n,
            # SNAP integrity verification is enabled by default.
            # It is disabled only if --skip-snap-verify was provided.
            verify_snap_counts=not args.skip_snap_verify,
        )
        # Extract the summary counts produced by build_size().
        # These include users, friendship edges, hasPet edges,
        # customers, and pet tokens.
        counts = fixture["counts"]
        # Print the generated fixture counts in readable JSON format.
        print(json.dumps({"size": size_name, **counts}, indent=2))
        # Compare the newly generated counts against the previously
        # verified values stored in EXPECTED_COUNTS.
        assert_counts(size_name, counts)
        # Get the banked expected counts for this fixture size.
        # If the size has no entry yet, use an empty dictionary.
        banked = EXPECTED_COUNTS.get(size_name, {})
        # Check whether any important expected count has not yet been banked.
        # This is useful when generating a new fixture size for the first time.
        if any(
            banked.get(k) is None
            for k in ("friend_edges", "haspet_edges", "customers")
        ):
            # Print the newly generated values so they can be manually
            # reviewed and added to EXPECTED_COUNTS as reference values.
            print(
                f"NOTE: bank these into EXPECTED_COUNTS[{size_name!r}]: "
                f"friend_edges={counts['friend_edges']}, "
                f"haspet_edges={counts['haspet_edges']}, "
                f"customers={counts['customers']}",
                file=sys.stderr,
            )
        # Only create the actual fixture files if --write was provided.
        if args.write:
            # Build the output path for the GraphML graph.
            # Example: benchmarks/pokec/fixtures/pokec-10k.graphml
            graphml = args.out_dir / f"pokec-{size_name}.graphml"
            # Build the output path for the customer seed JSON.
            # Example: benchmarks/pokec/fixtures/pokec-10k-customers.json
            customers_path = (
                args.out_dir / f"pokec-{size_name}-customers.json"
            )
            # Write the users, pets, friendship edges, and hasPet edges
            # from the fixture into the GraphML file.
            write_graphml(graphml, fixture)
            # Write the selected customer/relevance seed IDs
            # into their separate JSON file.
            write_customers(
                customers_path,
                fixture["customers"]
            )
            # Confirm which files were successfully written.
            print(
                f"wrote {graphml} and {customers_path}",
                file=sys.stderr
            )
    # Return 0 to indicate that fixture generation completed successfully.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
