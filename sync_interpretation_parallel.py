"""Keep interpretation_parallel.py in sync with interpretation.py.

Changed: used to flip `@numba.njit(... parallel=False)` to `parallel=True`.
Numba is gone on this branch, so parallel is just a copy of the main engine
for API compatibility (`settings.parallel_computing`).
"""

from pathlib import Path


def main():
    src = Path("pyreason/scripts/interpretation/interpretation.py")
    dst = Path("pyreason/scripts/interpretation/interpretation_parallel.py")
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Synced {dst} from {src} (plain-Python, no Numba flip).")


if __name__ == "__main__":
    main()
