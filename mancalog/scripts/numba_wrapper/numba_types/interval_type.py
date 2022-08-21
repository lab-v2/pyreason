class Interval:
    """
    No support for open, closedopen, openclosed
    """
    def __init__(self, left, lower, upper, right):
        self._lower = lower
        self._upper = upper
        self._left = left
        self._right = right
        # self.name = hash(f'{self._left}{self._lower},{self._upper}{self._right}')

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
        return Interval('[', lower, upper, ']')

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
from numba import types
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
def typeof_node(val, c):
    return interval_type


# Construct object from Numba functions
@type_callable(Interval)
def type_node(context):
    def typer(left, low, up, right):
        if isinstance(low, types.Float) and isinstance(up, types.Float) and isinstance(left, types.UnicodeType) and isinstance(right, types.UnicodeType):
            return interval_type
    return typer


# Define native representation: datamodel
@register_model(IntervalType)
class IntervalModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('low', types.float64),
            ('up', types.float64),
            ('left', types.string),
            ('right', types.string),
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(IntervalType, 'low', 'low')
make_attribute_wrapper(IntervalType, 'up', 'up')
make_attribute_wrapper(IntervalType, 'left', 'left')
make_attribute_wrapper(IntervalType, 'right', 'right')


# Implement constructor
@lower_builtin(Interval, types.UnicodeType, types.Float, types.Float, types.UnicodeType)
def impl_node(context, builder, sig, args):
    typ = sig.return_type
    left, low, up, right = args
    interval = cgutils.create_struct_proxy(typ)(context, builder)
    interval.low = low
    interval.up = up
    interval.left = left
    interval.right = right
    return interval._getvalue()

# Expose properties
@overload_attribute(IntervalType, "lower")
def get_lower(interval):
    def getter(interval):
        return interval.low
    return getter

@overload_attribute(IntervalType, "upper")
def get_upper(interval):
    def getter(interval):
        return interval.up
    return getter

@overload_method(IntervalType, 'intersection')
def intersection(interval_1, interval_2):
    def impl(interval_1, interval_2):
        lower = max(interval_1.lower, interval_2.lower)
        upper = min(interval_1.upper, interval_2.upper)
        return Interval('[', lower, upper, ']')
    return impl

# @overload_method(IntervalType, 'to_str')
# def to_str(interval):
#     def impl(interval):
#         return f'{interval.left}{interval.lower},{interval.upper}{interval.right}'
#     return impl


@overload(operator.eq)
def interval_eq(interval_1, interval_2):
    if isinstance(interval_1, IntervalType) and isinstance(interval_2, IntervalType):
        def impl(interval_1, interval_2):
            if interval_1.lower == interval_2.lower and interval_1.upper == interval_2.upper:
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
    interval = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    interval.left = c.unbox(types.string, left_obj).value
    interval.low = c.unbox(types.float64, lower_obj).value
    interval.up = c.unbox(types.float64, upper_obj).value
    interval.right = c.unbox(types.string, right_obj).value
    c.pyapi.decref(left_obj)
    c.pyapi.decref(lower_obj)
    c.pyapi.decref(upper_obj)
    c.pyapi.decref(right_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(interval._getvalue(), is_error=is_error)



@box(IntervalType)
def box_node(typ, val, c):
    interval = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Interval))
    left_obj = c.box(types.string, interval.left)
    lower_obj = c.box(types.float64, interval.low)
    upper_obj = c.box(types.float64, interval.up)
    right_obj = c.box(types.string, interval.right)
    res = c.pyapi.call_function_objargs(class_obj, (left_obj, lower_obj, upper_obj, right_obj))
    c.pyapi.decref(left_obj)
    c.pyapi.decref(lower_obj)
    c.pyapi.decref(upper_obj)
    c.pyapi.decref(right_obj)
    c.pyapi.decref(class_obj)
    return res


from numba import njit

@njit
def closed(lower, upper):
    return Interval('[', lower, upper, ']')


# @numba.njit
# def f(a):
#     b = closed(1.5, 2.1)
#     return a.intersection(b)

# print(f(closed(1.0,2.0)))
