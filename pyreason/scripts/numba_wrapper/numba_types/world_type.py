import numba
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
from pyreason.scripts.components.world import World

import operator
from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method, overload
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box
from numba.core.typing import signature


# Create new numba type
class WorldType(types.Type):
    def __init__(self):
        super(WorldType, self).__init__(name='World')

world_type = WorldType()


# Type inference
@typeof_impl.register(World)
def typeof_world(val, c):
    return world_type


# Construct object from Numba functions
# Constructor for internal use only
@type_callable(World)
def type_world(context):
    def typer(labels, world):
        if isinstance(labels, types.ListType) and isinstance(world, types.DictType):
            return world_type
    return typer

@type_callable(World)
def type_world(context):
    def typer(labels):
        if isinstance(labels, types.ListType):
            return world_type
    return typer


# Define native representation: datamodel
@register_model(WorldType)
class WorldModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('labels', types.ListType(label.label_type)),
            ('world', types.DictType(label.label_type, interval.interval_type))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(WorldType, 'labels', 'labels')
make_attribute_wrapper(WorldType, 'world', 'world')

# Implement constructor
# Constructor for internal use only
@lower_builtin(World, types.ListType(label.label_type), types.DictType(label.label_type, interval.interval_type))
def impl_world(context, builder, sig, args):
    # context.build_map(builder, )
    typ = sig.return_type
    l, wo = args
    context.nrt.incref(builder, types.DictType(label.label_type, interval.interval_type), wo)
    context.nrt.incref(builder, types.ListType(label.label_type), l)
    w = cgutils.create_struct_proxy(typ)(context, builder)
    w.labels = l
    w.world = wo
    return w._getvalue()

@lower_builtin(World, types.ListType(label.label_type))
def impl_world(context, builder, sig, args):
    def make_world(l):
        d = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
        for lab in l:
            d[lab] = interval.closed(0.0, 1.0)
        w = World(l, d)
        return w

    w = context.compile_internal(builder, make_world, sig, args)
    return w


# Expose properties
@overload_method(WorldType, 'is_satisfied')
def is_satisfied(world, label, interval):
    def impl(world, label, interval):
        result = False
        bnd = world.world[label]
        result = bnd in interval

        return result
    return impl

@overload_method(WorldType, 'update')
def update(w, label, interval):
    def impl(w, label, interval):       
        current_bnd = w.world[label]
        new_bnd = current_bnd.intersection(interval)
        w.world[label] = new_bnd
    return impl

@overload_method(WorldType, 'get_bound')
def get_bound(world, label):
    def impl(world, label):
        result = None
        result = world.world[label] 
        return result
    return impl


# Tell numba how to make native
@unbox(WorldType)
def unbox_world(typ, obj, c):
    labels_obj = c.pyapi.object_getattr_string(obj, "_labels")
    world_obj = c.pyapi.object_getattr_string(obj, "_world")
    world = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    world.labels = c.unbox(types.ListType(label.label_type), labels_obj).value
    world.world = c.unbox(types.DictType(label.label_type, interval.interval_type), world_obj).value
    c.pyapi.decref(labels_obj)
    c.pyapi.decref(world_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(world._getvalue(), is_error=is_error)



@box(WorldType)
def box_world(typ, val, c):
    w = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(World.make_world))
    labels_obj = c.box(types.ListType(label.label_type), w.labels)
    world_obj = c.box(types.DictType(label.label_type, interval.interval_type), w.world)
    res = c.pyapi.call_function_objargs(class_obj, (labels_obj, world_obj))
    c.pyapi.decref(labels_obj)
    c.pyapi.decref(world_obj)
    c.pyapi.decref(class_obj)
    return res
