import operator
import numpy as np
import numba
from numba import njit
from numba.core import types
from numba.experimental import structref
from numba.core.extending import overload_method, overload_attribute, overload

from pyreason.scripts.interval.interval import Interval



@structref.register
class IntervalType(numba.types.StructRef):
    def preprocess_fields(self, fields):
        return tuple((name, types.unliteral(typ)) for name, typ in fields)

interval_fields = [
    ('l', types.float64),
    ('u', types.float64),
    ('s', types.boolean),
    ('prev_l', types.float64),
    ('prev_u', types.float64)
]

interval_type = IntervalType(interval_fields)
structref.define_proxy(Interval, IntervalType, ["l", "u", 's', 'prev_l', 'prev_u'])


@overload_attribute(IntervalType, "lower")
def get_lower(interval):
    def getter(interval):
        return interval.l
    return getter

@overload_attribute(IntervalType, "upper")
def get_upper(interval):
    def getter(interval):
        return interval.u
    return getter

@overload_attribute(IntervalType, "prev_lower")
def prev_lower(interval):
    def getter(interval):
        return interval.prev_l
    return getter

@overload_attribute(IntervalType, "prev_upper")
def prev_upper(interval):
    def getter(interval):
        return interval.prev_u
    return getter


@overload_method(IntervalType, "intersection")
def intersection(self, interval):
    def impl(self, interval):
        lower = max(self.lower, interval.lower)
        upper = min(self.upper, interval.upper)
        if lower > upper:
            lower = np.float32(0)
            upper = np.float32(1)
        return Interval(lower, upper, False, self.prev_lower, self.prev_upper)

    return impl

@overload_method(IntervalType, 'set_lower_upper')
def set_lower_upper(interval, l, u):
    def impl(interval, l, u):
        interval.l = np.float64(l)
        interval.u = np.float64(u)
    return impl

@overload_method(IntervalType, 'reset')
def reset(interval):
    def impl(interval):
        # Set previous bounds
        interval.prev_l = interval.l
        interval.prev_u = interval.u
        # Then set new bounds
        interval.l = np.float64(0)
        interval.u = np.float64(1)
    return impl

@overload_method(IntervalType, 'set_static')
def set_static(interval, s):
    def impl(interval, s):
        interval.s = s
    return impl

@overload_method(IntervalType, 'is_static')
def is_static(interval):
    def impl(interval):
        return interval.s
    return impl

@overload_method(IntervalType, 'has_changed')
def has_changed(interval):
    def impl(interval):
        if interval.lower==interval.prev_lower and interval.upper==interval.prev_upper:
            return False
        else:
            return True
    return impl

@overload_method(IntervalType, 'copy')
def copy(interval):
    def impl(interval):
        return Interval(interval.lower, interval.upper, interval.s, interval.prev_l, interval.prev_u)
    return impl


@overload(operator.eq)
def interval_eq(interval_1, interval_2):
    if isinstance(interval_1, IntervalType) and isinstance(interval_2, IntervalType):
        def impl(interval_1, interval_2):
            if interval_1.lower == interval_2.lower and interval_1.upper == interval_2.upper:
                return True
            else:
                return False 
        return impl

@overload(operator.ne)
def interval_ne(interval_1, interval_2):
    if isinstance(interval_1, IntervalType) and isinstance(interval_2, IntervalType):
        def impl(interval_1, interval_2):
            if interval_1.lower != interval_2.lower or interval_1.upper != interval_2.upper:
                return True
            else:
                return False 
        return impl

@overload(operator.contains)
def interval_contains(interval_1, interval_2):
    def impl(interval_1, interval_2):
        if interval_1.lower <= interval_2.lower and interval_1.upper >= interval_2.upper:
            return True
        else:
            return False
    return impl


@njit
def closed(lower, upper, static=False):
    return Interval(np.float64(lower), np.float64(upper), static, np.float64(lower), np.float64(upper))
