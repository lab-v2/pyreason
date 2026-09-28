"""
Tests to validate consistency between related files in the PyReason codebase.
"""

from pathlib import Path


def test_interpretation_parallel_consistency():
    """
    HEY WE CHANGED THIS — Numba is gone, so there is no @numba.njit(parallel=...)
    flip anymore. parallel is just a copy of the main engine (banner comment may differ).

    Old expectation (COMMENTED OUT on purpose):
    - interpretation.py should have: @numba.njit(cache=True, parallel=False)
    - interpretation_parallel.py should have: @numba.njit(cache=True, parallel=True)
    """
    scripts_dir = Path(__file__).parent.parent.parent.parent / "pyreason" / "scripts" / "interpretation"
    interpretation_file = scripts_dir / "interpretation.py"
    interpretation_parallel_file = scripts_dir / "interpretation_parallel.py"

    assert interpretation_file.exists(), f"File not found: {interpretation_file}"
    assert interpretation_parallel_file.exists(), f"File not found: {interpretation_parallel_file}"

    with open(interpretation_file, 'r', encoding='utf-8') as f:
        interpretation_lines = f.readlines()

    with open(interpretation_parallel_file, 'r', encoding='utf-8') as f:
        interpretation_parallel_lines = f.readlines()

    # HEY WE CHANGED THIS — allow a short banner-comment difference at the top;
    # ignore leading comment-only lines when comparing body identity.
    def strip_leading_changed_banners(lines):
        i = 0
        while i < len(lines) and lines[i].lstrip().startswith("#"):
            i += 1
        # keep one blank after banners if present
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        return lines[i:]

    body1 = strip_leading_changed_banners(interpretation_lines)
    body2 = strip_leading_changed_banners(interpretation_parallel_lines)

    assert body1 == body2, (
        "HEY WE CHANGED THIS — with Numba gone, interpretation_parallel.py must "
        "match interpretation.py (aside from the top banner comments).\n"
        f"len body1={len(body1)} body2={len(body2)}"
    )

    # HEY WE CHANGED THIS — old njit-decorator diff check kept for history:
    # numba_decorator_difference_found = False
    # for line_num, (line1, line2) in enumerate(...):
    #     if line1_stripped == "@numba.njit(cache=True, parallel=False)" and
    #        line2_stripped == "@numba.njit(cache=True, parallel=True)":
    #         ...
