#!/usr/bin/env python3
"""
Pre-commit hook script to synchronize interpretation_parallel.py from interpretation.py.

This script ensures that interpretation_parallel.py is always an exact copy of
interpretation.py, except for the @numba.njit decorator which should have
parallel=True instead of parallel=False.
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

    # Find the line with the @numba.njit decorator that needs to be changed
    target_line = "@numba.njit(cache=True, parallel=False)"
    replacement_line = "@numba.njit(cache=True, parallel=True)"

    found_indices = []
    for i, line in enumerate(lines):
        if line.strip() == target_line:
            found_indices.append(i)

    # Validate we found exactly one occurrence
    if len(found_indices) == 0:
        print(f"Error: Could not find the expected decorator in {interpretation_file}", file=sys.stderr)
        print(f"  Looking for: {target_line}", file=sys.stderr)
        return 1

    if len(found_indices) > 1:
        print(f"Error: Found multiple occurrences of the decorator in {interpretation_file}", file=sys.stderr)
        print(f"  Found on lines: {[i + 1 for i in found_indices]}", file=sys.stderr)
        print(f"  Expected exactly one occurrence", file=sys.stderr)
        return 1

    # Found exactly one occurrence - replace it
    line_index = found_indices[0]
    line_num = line_index + 1

    # Preserve the original indentation
    original_line = lines[line_index]
    indentation = original_line[:len(original_line) - len(original_line.lstrip())]

    # Create modified lines with the replacement
    modified_lines = lines.copy()
    modified_lines[line_index] = f"{indentation}{replacement_line}\n"

    # Write to parallel file
    try:
        with open(interpretation_parallel_file, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
    except Exception as e:
        print(f"Error writing {interpretation_parallel_file}: {e}", file=sys.stderr)
        return 1

    print(f"✓ Successfully synced {interpretation_parallel_file.name} from {interpretation_file.name}")
    print(f"  Modified line {line_num}: parallel=False → parallel=True")

    return 0


def main():
    """Main entry point."""
    result = sync_interpretation_files()
    sys.exit(result)


if __name__ == "__main__":
    main()
