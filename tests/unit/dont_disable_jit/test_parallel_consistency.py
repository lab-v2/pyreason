"""
Tests to validate consistency between related files in the PyReason codebase.
"""

from pathlib import Path


def test_interpretation_parallel_consistency():
    """
    Test that interpretation_parallel.py is identical to interpretation.py
    except for the parallel flag in the @numba.njit decorator.

    The only difference should be:
    - interpretation.py should have: @numba.njit(cache=True, parallel=False)
    - interpretation_parallel.py should have: @numba.njit(cache=True, parallel=True)
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

    # Track all differences
    differences = []
    numba_decorator_difference_found = False
    numba_decorator_line_num = None

    # Compare line by line
    for line_num, (line1, line2) in enumerate(zip(interpretation_lines, interpretation_parallel_lines), start=1):
        if line1 != line2:
            # Check if this is the expected numba decorator difference
            # Strip whitespace for comparison
            line1_stripped = line1.strip()
            line2_stripped = line2.strip()

            # Check if this matches the expected decorator pattern
            if (line1_stripped == "@numba.njit(cache=True, parallel=False)" and
                line2_stripped == "@numba.njit(cache=True, parallel=True)"):
                # This is the expected difference
                if numba_decorator_difference_found:
                    differences.append(
                        f"Found multiple @numba.njit decorator differences (line {numba_decorator_line_num} and line {line_num})"
                    )
                numba_decorator_difference_found = True
                numba_decorator_line_num = line_num
            else:
                # This is an unexpected difference
                differences.append(
                    f"Unexpected difference at line {line_num}:\n"
                    f"  interpretation.py: {line1.strip()}\n"
                    f"  interpretation_parallel.py: {line2.strip()}"
                )

    # Check that we found exactly one expected difference
    if not numba_decorator_difference_found:
        differences.append(
            "Expected difference not found: "
            "@numba.njit(cache=True, parallel=False) vs @numba.njit(cache=True, parallel=True)"
        )

    # Assert no unexpected differences
    assert len(differences) == 0, \
        f"Found {len(differences)} issue(s) between the files:\n" + "\n\n".join(differences)
