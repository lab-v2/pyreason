import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.facts.fact_node import Fact

import numba
from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box


# Create new numba type
class FactType(types.Type):
    def __init__(self):
        super(FactType, self).__init__(name='FactNode')

fact_type = FactType()


# Type inference
@typeof_impl.register(Fact)
def typeof_fact(val, c):
    return fact_type


# Construct object from Numba functions
@type_callable(Fact)
def type_fact(context):
    def typer(name, component, l, bnd, t_lower, t_upper, static):
        if isinstance(name, types.UnicodeType) and isinstance(component, types.UnicodeType) and isinstance(l, label.LabelType) and isinstance(bnd, interval.IntervalType) and isinstance(t_lower, numba.types.Integer) and isinstance(t_upper, numba.types.Integer) and isinstance(static, numba.types.Boolean):
            return fact_type
    return typer


# Define native representation: datamodel
@register_model(FactType)
class FactModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('name', numba.types.string),
            ('component', numba.types.string),
            ('l', label.label_type),
            ('bnd', interval.interval_type),
            ('t_lower', numba.types.int8),
            ('t_upper', numba.types.int8),
            ('static', numba.types.boolean)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(FactType, 'name', 'name')
make_attribute_wrapper(FactType, 'component', 'component')
make_attribute_wrapper(FactType, 'l', 'l')
make_attribute_wrapper(FactType, 'bnd', 'bnd')
make_attribute_wrapper(FactType, 't_lower', 't_lower')
make_attribute_wrapper(FactType, 't_upper', 't_upper')
make_attribute_wrapper(FactType, 'static', 'static')


# Implement constructor
@lower_builtin(Fact, numba.types.string, numba.types.string, label.label_type, interval.interval_type, numba.types.int8, numba.types.int8, numba.types.boolean)
def impl_fact(context, builder, sig, args):
    typ = sig.return_type
    name, component, l, bnd, t_lower, t_upper, static = args
    fact = cgutils.create_struct_proxy(typ)(context, builder)
    fact.name = name
    fact.component = component
    fact.l = l
    fact.bnd = bnd
    fact.t_lower = t_lower
    fact.t_upper = t_upper
    fact.static = static
    return fact._getvalue()

# Expose properties
@overload_method(FactType, "get_name")
def get_name(fact):
    def getter(fact):
        return fact.name
    return getter

@overload_method(FactType, "get_component")
def get_component(fact):
    def getter(fact):
        return fact.component
    return getter

@overload_method(FactType, "get_label")
def get_label(fact):
    def getter(fact):
        return fact.l
    return getter

@overload_method(FactType, "get_bound")
def get_bound(fact):
    def getter(fact):
        return fact.bnd
    return getter

@overload_method(FactType, "get_time_lower")
def get_time_lower(fact):
    def getter(fact):
        return fact.t_lower
    return getter

@overload_method(FactType, "get_time_upper")
def get_time_lower(fact):
    def getter(fact):
        return fact.t_upper
    return getter


# Tell numba how to make native
@unbox(FactType)
def unbox_fact(typ, obj, c):
    name_obj = c.pyapi.object_getattr_string(obj, "_name")
    component_obj = c.pyapi.object_getattr_string(obj, "_component")
    l_obj = c.pyapi.object_getattr_string(obj, "_label")
    bnd_obj = c.pyapi.object_getattr_string(obj, "_interval")
    t_lower_obj = c.pyapi.object_getattr_string(obj, "_t_lower")
    t_upper_obj = c.pyapi.object_getattr_string(obj, "_t_upper")
    static_obj = c.pyapi.object_getattr_string(obj, "_static")
    fact = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    fact.name = c.unbox(numba.types.string, name_obj).value
    fact.component = c.unbox(numba.types.string, component_obj).value
    fact.l = c.unbox(label.label_type, l_obj).value
    fact.bnd = c.unbox(interval.interval_type, bnd_obj).value
    fact.t_lower = c.unbox(numba.types.int8, t_lower_obj).value
    fact.t_upper = c.unbox(numba.types.int8, t_upper_obj).value
    fact.static = c.unbox(numba.types.boolean, static_obj).value
    c.pyapi.decref(name_obj)
    c.pyapi.decref(component_obj)
    c.pyapi.decref(l_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(t_lower_obj)
    c.pyapi.decref(t_upper_obj)
    c.pyapi.decref(static_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(fact._getvalue(), is_error=is_error)



@box(FactType)
def box_fact(typ, val, c):
    fact = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Fact))
    name_obj = c.box(numba.types.string, fact.name)
    component_obj = c.box(numba.types.string, fact.component)
    l_obj = c.box(label.label_type, fact.l)
    bnd_obj = c.box(interval.interval_type, fact.bnd)
    t_lower_obj = c.box(numba.types.int8, fact.t_lower)
    t_upper_obj = c.box(numba.types.int8, fact.t_upper)
    static_obj = c.box(numba.types.boolean, fact.static)
    res = c.pyapi.call_function_objargs(class_obj, (name_obj, component_obj, l_obj, bnd_obj, t_lower_obj, t_upper_obj, static_obj))
    c.pyapi.decref(name_obj)
    c.pyapi.decref(component_obj)
    c.pyapi.decref(l_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(t_lower_obj)
    c.pyapi.decref(t_upper_obj)
    c.pyapi.decref(static_obj)
    c.pyapi.decref(class_obj)
    return res
