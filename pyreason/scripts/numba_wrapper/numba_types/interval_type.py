from pyreason.scripts.interval.interval import Interval

import operator
import numpy as np
from numba import types, typed
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method, overload_attribute, overload
from numba.extending import lower_builtin
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
    def typer(left, low, up, right, static):
        if isinstance(low, types.Float) and isinstance(up, types.Float) and isinstance(left, types.UnicodeType) and isinstance(right, types.UnicodeType) and isinstance(static, types.ListType):
            return interval_type
    return typer


# Define native representation: datamodel
@register_model(IntervalType)
class IntervalModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('low', types.float32),
            ('up', types.float32),
            ('left', types.string),
            ('right', types.string),
            ('static', types.ListType(types.boolean))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(IntervalType, 'low', 'low')
make_attribute_wrapper(IntervalType, 'up', 'up')
make_attribute_wrapper(IntervalType, 'left', 'left')
make_attribute_wrapper(IntervalType, 'right', 'right')
make_attribute_wrapper(IntervalType, 'static', 'static')


# Implement constructor
@lower_builtin(Interval, types.string, types.float32, types.float32, types.string, types.ListType(types.boolean))
def impl_interval(context, builder, sig, args):
    typ = sig.return_type
    left, low, up, right, static = args
    context.nrt.incref(builder, types.ListType(types.boolean), static)
    interval = cgutils.create_struct_proxy(typ)(context, builder)
    interval.low = low
    interval.up = up
    interval.left = left
    interval.right = right
    interval.static = static
    return interval._getvalue()

# Expose properties
@overload_attribute(IntervalType, "lower")
def get_lower(interval):
    def getter(interval):
        return round(interval.low, 7)
    return getter

@overload_attribute(IntervalType, "upper")
def get_upper(interval):
    def getter(interval):
        return round(interval.up, 7)
    return getter

@overload_method(IntervalType, 'intersection')
def intersection(interval_1, interval_2):
    def impl(interval_1, interval_2):
        lower = max(interval_1.lower, interval_2.lower)
        upper = min(interval_1.upper, interval_2.upper)
        if lower > upper:
            lower = np.float32(0)
            upper = np.float32(1)
        return Interval('[', lower, upper, ']', typed.List([False]))
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
        return hash((interval.left, interval.low, interval.up, interval.right))
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
    lower_obj = c.pyapi.object_getattr_string(obj, "_lower")
    upper_obj = c.pyapi.object_getattr_string(obj, "_upper")
    right_obj = c.pyapi.object_getattr_string(obj, "_right")
    static_obj = c.pyapi.object_getattr_string(obj, "_static")
    interval = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    interval.left = c.unbox(types.string, left_obj).value
    interval.low = c.unbox(types.float32, lower_obj).value
    interval.up = c.unbox(types.float32, upper_obj).value
    interval.right = c.unbox(types.string, right_obj).value
    interval.static = c.unbox(types.ListType(types.boolean), static_obj).value
    c.pyapi.decref(left_obj)
    c.pyapi.decref(lower_obj)
    c.pyapi.decref(upper_obj)
    c.pyapi.decref(right_obj)
    c.pyapi.decref(static_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(interval._getvalue(), is_error=is_error)



@box(IntervalType)
def box_interval(typ, val, c):
    interval = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Interval))
    left_obj = c.box(types.string, interval.left)
    lower_obj = c.box(types.float32, interval.low)
    upper_obj = c.box(types.float32, interval.up)
    right_obj = c.box(types.string, interval.right)
    static_obj = c.box(types.ListType(types.boolean), interval.static)
    res = c.pyapi.call_function_objargs(class_obj, (left_obj, lower_obj, upper_obj, right_obj, static_obj))
    c.pyapi.decref(left_obj)
    c.pyapi.decref(lower_obj)
    c.pyapi.decref(upper_obj)
    c.pyapi.decref(right_obj)
    c.pyapi.decref(static_obj)
    c.pyapi.decref(class_obj)
    return res


from numba import njit
import numpy as np

@njit
def closed(lower, upper, static=False):
    return Interval('[', np.float32(lower), np.float32(upper), ']', typed.List([static]))
