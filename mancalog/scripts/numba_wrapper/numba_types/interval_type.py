class Interval:
    """
    No support for open, closedopen, openclosed
    """
    def __init__(self, left, interval, right, static):
        self._lower = round(interval[0], 7)
        self._upper = round(interval[1], 7)
        self._left = left
        self._right = right
        self._interval = interval
        self._static = static

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    def to_str(self):
        interval = f'{self._left}{self._lower},{self._upper}{self._right}'
        return interval

    def intersection(self, interval):
        lower = max(self._lower, interval.lower)
        upper = min(self._upper, interval.upper)
        if lower > upper:
            lower = 0
            upper = 1
        return Interval('[', [lower, upper], ']', [False])

    def __hash__(self):
        return hash(self.to_str())

    def __contains__(self, item):
        if self._lower <= item.lower and self._upper >= item.upper:
            return True
        else:
            return False

    def __eq__(self, interval):
        if self.lower == interval.lower and self.upper == interval.upper:
            return True
        else:
            return False

    def __repr__(self):
        return self.to_str()

    def __lt__(self, other):
        if self.upper < other.lower:
            return True
        else:
            return False

    def __le__(self, other):
        if self.upper <= other.upper:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.lower > other.upper:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.lower >= other.lower:
            return True
        else:
            return False




# def closed(lower, upper):
# 	return Interval('[', lower, upper, ']')


# def open(lower, upper):
# 	return Interval('(', lower, upper, ')')


# def closedopen(lower, upper):
# 	return Interval('[', lower, upper, ')')


# def openclosed(lower, upper):
# 	return Interval('(', lower, upper, ']')


import operator
import numpy as np
from numba import types, typed
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method, overload_attribute, overload
from numba.extending import lower_builtin, lower_setattr
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box

# Create new numba type
class IntervalType(types.Type):
    def __init__(self):
        super(IntervalType, self).__init__(name='Interval')

interval_type = IntervalType()


# Type inference
@typeof_impl.register(Interval)
def typeof_interval(val, c):
    return interval_type


# Construct object from Numba functions
@type_callable(Interval)
def type_interval(context):
    def typer(left, interval, right, static):
        if isinstance(left, types.UnicodeType) and isinstance(right, types.UnicodeType) and isinstance(interval, types.ListType) and isinstance(static, types.ListType):
            return interval_type
    return typer


# Define native representation: datamodel
@register_model(IntervalType)
class IntervalModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('interval', types.ListType(types.float32)),
            ('left', types.string),
            ('right', types.string),
            ('static', types.ListType(types.boolean))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(IntervalType, 'interval', 'interval')
make_attribute_wrapper(IntervalType, 'left', 'left')
make_attribute_wrapper(IntervalType, 'right', 'right')
make_attribute_wrapper(IntervalType, 'static', 'static')


# Implement constructor
@lower_builtin(Interval, types.string, types.ListType(types.float32), types.string, types.ListType(types.boolean))
def impl_interval(context, builder, sig, args):
    typ = sig.return_type
    left, i, right, static = args
    context.nrt.incref(builder, types.ListType(types.float32), i)
    context.nrt.incref(builder, types.ListType(types.boolean), static)
    interval = cgutils.create_struct_proxy(typ)(context, builder)
    interval.interval = i
    interval.left = left
    interval.right = right
    interval.static = static
    return interval._getvalue()

# Expose properties
@overload_attribute(IntervalType, "lower")
def get_lower(interval):
    def getter(interval):
        return round(interval.interval[0], 7)
    return getter

@overload_attribute(IntervalType, "upper")
def get_upper(interval):
    def getter(interval):
        return round(interval.interval[1], 7)
    return getter

@overload_method(IntervalType, 'intersection')
def intersection(interval_1, interval_2):
    def impl(interval_1, interval_2):
        lower = max(interval_1.lower, interval_2.lower)
        upper = min(interval_1.upper, interval_2.upper)
        if lower > upper:
            lower = np.float32(0)
            upper = np.float32(1)
        return Interval('[', typed.List([lower, upper]), ']', typed.List([False]))
    return impl   


@overload_method(IntervalType, 'set_lower')
def set_lower(interval, l):
    def impl(interval, l):
        interval.interval[0] = np.float32(l)
    return impl

@overload_method(IntervalType, 'set_upper')
def set_upper(interval, u):
    def impl(interval, u):
        interval.interval[1] = np.float32(u)
    return impl

@overload_method(IntervalType, 'set_lower_upper')
def set_lower_upper(interval, l, u):
    def impl(interval, l, u):
        interval.interval[0] = np.float32(l)
        interval.interval[1] = np.float32(u)
    return impl

@overload_method(IntervalType, 'set_static')
def set_static(interval, value):
    def impl(interval, value):
        interval.static[0] = value
    return impl

@overload_method(IntervalType, 'is_static')
def is_static(interval):
    def impl(interval):
        return interval.static[0]
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

@overload(hash)
def interval_hash(interval):
    def impl(interval):
        return hash((interval.left, interval.interval[0], interval.interval[1], interval.right))
    return impl

@overload(operator.contains)
def interval_contains(interval_1, interval_2):
    def impl(interval_1, interval_2):
        if interval_1.lower <= interval_2.lower and interval_1.upper >= interval_2.upper:
            return True
        else:
            return False
    return impl


# Tell numba how to make native
@unbox(IntervalType)
def unbox_interval(typ, obj, c):
    left_obj = c.pyapi.object_getattr_string(obj, "_left")
    interval_obj = c.pyapi.object_getattr_string(obj, "_interval")
    right_obj = c.pyapi.object_getattr_string(obj, "_right")
    static_obj = c.pyapi.object_getattr_string(obj, "_static")
    interval = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    interval.left = c.unbox(types.string, left_obj).value
    interval.right = c.unbox(types.string, right_obj).value
    interval.interval = c.unbox(types.ListType(types.float32), interval_obj).value
    interval.static = c.unbox(types.ListType(types.boolean), static_obj).value
    c.pyapi.decref(left_obj)
    c.pyapi.decref(right_obj)
    c.pyapi.decref(interval_obj)
    c.pyapi.decref(static_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(interval._getvalue(), is_error=is_error)



@box(IntervalType)
def box_interval(typ, val, c):
    i = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Interval))
    left_obj = c.box(types.string, i.left)
    right_obj = c.box(types.string, i.right)
    interval_obj = c.box(types.ListType(types.float32), i.interval)
    static_obj = c.box(types.ListType(types.boolean), i.static)
    res = c.pyapi.call_function_objargs(class_obj, (left_obj, interval_obj, right_obj, static_obj))
    c.pyapi.decref(left_obj)
    c.pyapi.decref(right_obj)
    c.pyapi.decref(interval_obj)
    c.pyapi.decref(static_obj)
    c.pyapi.decref(class_obj)
    return res


from numba import njit
import numpy as np


@njit
def closed(lower, upper):
    return Interval('[', typed.List([np.float32(lower), np.float32(upper)]), ']', typed.List([False]))
