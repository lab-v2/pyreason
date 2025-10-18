#!/usr/bin/env python3
"""
Pre-commit hook script to synchronize interpretation_parallel.py from interpretation.py.

This script ensures that interpretation_parallel.py is always an exact copy of
interpretation.py, except for line 226 which should have parallel=True instead of
parallel=False in the @numba.njit decorator.
"""

import sys
from pathlib import Path


def sync_interpretation_files():
    """
    Synchronize interpretation_parallel.py from interpretation.py.

    Returns:
        int: 0 on success, 1 on failure
    """
    # Get the path to the interpretation files
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir
    interpretation_dir = project_root / "pyreason" / "scripts" / "interpretation"

    interpretation_file = interpretation_dir / "interpretation.py"
    interpretation_parallel_file = interpretation_dir / "interpretation_parallel.py"

    # Verify source file exists
    if not interpretation_file.exists():
        print(f"Error: Source file not found: {interpretation_file}", file=sys.stderr)
        return 1

    # Read the source file
    try:
        with open(interpretation_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {interpretation_file}: {e}", file=sys.stderr)
        return 1

    # Verify we have at least 226 lines
    if len(lines) < 226:
        print(f"Error: {interpretation_file} has fewer than 226 lines", file=sys.stderr)
        return 1

    # Expected line 226 (index 225) in source file
    expected_line = "\t@numba.njit(cache=True, parallel=False)\n"

    if lines[225] != expected_line:
        print(f"Warning: Line 226 in {interpretation_file} is not as expected.", file=sys.stderr)
        print(f"  Expected: {expected_line.strip()}", file=sys.stderr)
        print(f"  Got: {lines[225].strip()}", file=sys.stderr)
        print(f"  Proceeding with replacement anyway...", file=sys.stderr)

    # Replace line 226 for parallel version
    modified_lines = lines.copy()
    modified_lines[225] = "\t@numba.njit(cache=True, parallel=True)\n"

    # Write to parallel file
    try:
        with open(interpretation_parallel_file, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
    except Exception as e:
        print(f"Error writing {interpretation_parallel_file}: {e}", file=sys.stderr)
        return 1

    print(f"✓ Successfully synced {interpretation_parallel_file.name} from {interpretation_file.name}")
    print(f"  Modified line 226: parallel=False → parallel=True")

    return 0


def main():
    """Main entry point."""
    result = sync_interpretation_files()
    sys.exit(result)


if __name__ == "__main__":
    main()
