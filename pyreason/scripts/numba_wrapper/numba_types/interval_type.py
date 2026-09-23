# Changed: used to register Interval as a Numba structref + @njit closed().
# Plain re-export now — Interval/closed live in scripts.interval.interval.
from pyreason.scripts.interval.interval import Interval, closed

interval_type = Interval
IntervalType = Interval

# Re-exports for `import ...interval_type as interval` then interval.closed(...)
__all__ = ["Interval", "closed", "interval_type", "IntervalType"]
