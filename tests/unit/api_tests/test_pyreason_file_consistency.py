"""
Tests to validate consistency between related files in the PyReason codebase.
"""

import os
from pathlib import Path


def test_interpretation_parallel_consistency():
    """
    Test that interpretation_parallel.py is identical to interpretation.py
    except for the parallel flag in the @numba.njit decorator on line 226.

    interpretation.py line 226 should have: @numba.njit(cache=True, parallel=False)
    interpretation_parallel.py line 226 should have: @numba.njit(cache=True, parallel=True)
    """
    # Get the path to the interpretation files
    scripts_dir = Path(__file__).parent.parent.parent.parent / "pyreason" / "scripts" / "interpretation"
    interpretation_file = scripts_dir / "interpretation.py"
    interpretation_parallel_file = scripts_dir / "interpretation_parallel.py"

    # Verify both files exist
    assert interpretation_file.exists(), f"File not found: {interpretation_file}"
    assert interpretation_parallel_file.exists(), f"File not found: {interpretation_parallel_file}"

    # Read both files
    with open(interpretation_file, 'r', encoding='utf-8') as f:
        interpretation_lines = f.readlines()

    with open(interpretation_parallel_file, 'r', encoding='utf-8') as f:
        interpretation_parallel_lines = f.readlines()

    # Check that both files have the same number of lines
    assert len(interpretation_lines) == len(interpretation_parallel_lines), \
        f"Files have different number of lines: {len(interpretation_lines)} vs {len(interpretation_parallel_lines)}"

    # Expected difference on line 226 (index 225)
    expected_line_226_interpretation = "\t@numba.njit(cache=True, parallel=False)\n"
    expected_line_226_interpretation_parallel = "\t@numba.njit(cache=True, parallel=True)\n"

    # Track differences
    differences = []

    # Compare line by line
    for line_num, (line1, line2) in enumerate(zip(interpretation_lines, interpretation_parallel_lines), start=1):
        if line1 != line2:
            # Line 226 should be the only difference
            if line_num == 226:
                # Verify the expected difference
                if line1 != expected_line_226_interpretation:
                    differences.append(
                        f"Line {line_num} in interpretation.py is not as expected.\n"
                        f"  Expected: {expected_line_226_interpretation.strip()}\n"
                        f"  Got: {line1.strip()}"
                    )
                if line2 != expected_line_226_interpretation_parallel:
                    differences.append(
                        f"Line {line_num} in interpretation_parallel.py is not as expected.\n"
                        f"  Expected: {expected_line_226_interpretation_parallel.strip()}\n"
                        f"  Got: {line2.strip()}"
                    )
            else:
                # Any other difference is unexpected
                differences.append(
                    f"Unexpected difference at line {line_num}:\n"
                    f"  interpretation.py: {line1.strip()}\n"
                    f"  interpretation_parallel.py: {line2.strip()}"
                )

    # Assert no unexpected differences
    assert len(differences) == 0, \
        f"Found {len(differences)} unexpected difference(s) between the files:\n" + "\n\n".join(differences)

    # Verify the expected difference exists on line 226
    assert interpretation_lines[225] == expected_line_226_interpretation, \
        f"Line 226 in interpretation.py is not as expected"
    assert interpretation_parallel_lines[225] == expected_line_226_interpretation_parallel, \
        f"Line 226 in interpretation_parallel.py is not as expected"
