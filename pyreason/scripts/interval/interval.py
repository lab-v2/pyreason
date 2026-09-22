# Changed from a Numba structref Interval to a plain Python class.
# Bounds, static flag, and previous bounds stay the same.


class Interval:
    """One [lower, upper] bound pair with a static flag and previous bounds."""

    __slots__ = ("_lower", "_upper", "_static", "_prev_lower", "_prev_upper")

    def __init__(self, lower, upper, static=False, prev_lower=None, prev_upper=None):
        self._lower = float(lower)
        self._upper = float(upper)
        self._static = static
        self._prev_lower = float(lower if prev_lower is None else prev_lower)
        self._prev_upper = float(upper if prev_upper is None else prev_upper)

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    @property
    def prev_lower(self):
        return self._prev_lower

    @property
    def prev_upper(self):
        return self._prev_upper

    # Compat aliases used by older call sites / traces.
    @property
    def l(self):  # noqa: E743  # short name kept: old Interval structref field for lower
        return self._lower

    @property
    def u(self):
        return self._upper

    @property
    def s(self):
        return self._static

    @property
    def prev_l(self):
        return self._prev_lower

    @property
    def prev_u(self):
        return self._prev_upper

    def is_static(self):
        return self._static

    def set_static(self, static):
        self._static = static

    def copy(self):
        return Interval(
            self._lower,
            self._upper,
            self._static,
            self._prev_lower,
            self._prev_upper,
        )

    def set_lower_upper(self, lower, upper):
        self._lower = float(lower)
        self._upper = float(upper)

    def reset(self):
        self._prev_lower = self._lower
        self._prev_upper = self._upper
        self._lower = 0.0
        self._upper = 1.0

    def has_changed(self):
        return not (
            self._lower == self._prev_lower and self._upper == self._prev_upper
        )

    def intersection(self, interval):
        lower = max(self._lower, interval.lower)
        upper = min(self._upper, interval.upper)
        if lower > upper:
            lower, upper = 0.0, 1.0
        # Seed prev from current bounds (Python-proxy arm).
        return Interval(lower, upper, False, self._lower, self._upper)

    def to_str(self):
        return self.__repr__()

    def __eq__(self, interval):
        return interval.lower == self._lower and interval.upper == self._upper

    def __ne__(self, interval):
        return not self.__eq__(interval)

    def __hash__(self):
        return hash((self._lower, self._upper))

    def __contains__(self, item):
        return self._lower <= item.lower and self._upper >= item.upper

    def __repr__(self):
        return f"[{self._lower},{self._upper}]"


def closed(lower, upper, static=False):
    return Interval(lower, upper, static)


def intersect_world_update(current, incoming):
    # Changed from the Numba-jitted intersection arm used by World.update.
    # Previous bounds stay on the live interval so convergence counts stay correct.
    lower = max(current.lower, incoming.lower)
    upper = min(current.upper, incoming.upper)
    if lower > upper:
        lower, upper = 0.0, 1.0
    return Interval(lower, upper, False, current.prev_lower, current.prev_upper)
