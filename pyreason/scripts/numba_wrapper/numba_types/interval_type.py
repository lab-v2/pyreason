# Changed: used to register Interval as a Numba structref + @njit closed().
# Plain re-export now — Interval/closed live in scripts.interval.interval.
from pyreason.scripts.interval.interval import Interval, closed

interval_type = Interval
IntervalType = Interval
