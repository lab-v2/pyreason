import numba

# import label_type as label
# import interval_type as interval
import mancalog.scripts.numba_wrapper.numba_types.interval_type as interval
import mancalog.scripts.numba_wrapper.numba_types.label_type as label


# NOTE: CANNOT CONSTRUCT WORLD CLASS INSIDE JITTED FUNCTION YET
class World:
    
    def __init__(self, labels):
        self.labels = labels
        self._world = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
        for l in labels:
            self._world[l] = interval.closed(0.0, 1.0)

    def make_world(labels, world):
        w = World(labels)
        w._world = world
        return w

    def is_satisfied(self, label, interval):
        result = False
        
        bnd = self._world[label]
        result = bnd in interval

        return result

    def update(self, label, interval):
        lwanted = None
        bwanted = None 
        
        current_bnd = self._world[label]
        new_bnd = current_bnd.intersection(interval)
        self._world[label] = new_bnd

    def get_bound(self, label):
        result = None

        result = self._world[label] 
        return result

    def get_world(self):
        world = []
        for label in self._world.keys():
            bnd = self._world[label]
            world.append((label.get_value(), interval.closed(bnd.lower, bnd.upper)))
        return world


    def __str__(self):
        result = ''
        for label in self._world.keys():
            result = result + label.get_value() + ',' + self._world[label].to_str() + '\n'

        return result

# a=World([label.Label('a'), label.Label('b')])
# print(numba.typeof(a._world))
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
@type_callable(World)
def type_world(context):
    def typer(labels):
        if isinstance(labels, types.List):
            return world_type
    return typer


# Define native representation: datamodel
@register_model(WorldType)
class WorldModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('world', types.DictType(label.label_type, interval.interval_type)),
            ('labels', types.List(label.label_type))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(WorldType, 'world', 'world')
make_attribute_wrapper(WorldType, 'labels', 'labels')

# Implement constructor
@lower_builtin(World, types.List(label.label_type))
def impl_world(context, builder, sig, args):
    def make_world(labels, world):
        # world = World(labels)
        # w = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
        for l in labels:
            world[l] = interval.closed(0.0, 1.0)
        return world

    typ = sig.return_type
    world = cgutils.create_struct_proxy(typ)(context, builder)
    labels = args[0]
    # print(numba.typeof(labels))
    world.labels = labels
    # make_world(world)
    # world.make_world()
    # print(numba.typeof(labels))

    context.compile_internal(builder, make_world, sig, (labels, world.world))
        
    return world._getvalue()

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
    labels_obj = c.pyapi.object_getattr_string(obj, "labels")
    world_obj = c.pyapi.object_getattr_string(obj, "_world")
    world = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    world.labels = c.unbox(types.List(label.label_type), labels_obj).value
    world.world = c.unbox(types.DictType(label.label_type, interval.interval_type), world_obj).value
    c.pyapi.decref(labels_obj)
    c.pyapi.decref(world_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(world._getvalue(), is_error=is_error)



@box(WorldType)
def box_world(typ, val, c):
    world = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(World.make_world))
    labels_obj = c.box(types.List(label.label_type), world.labels)
    world_obj = c.box(types.DictType(label.label_type, interval.interval_type), world.world)
    res = c.pyapi.call_function_objargs(class_obj, (labels_obj,world_obj))
    c.pyapi.decref(labels_obj)
    c.pyapi.decref(world_obj)
    c.pyapi.decref(class_obj)
    return res

# import numba
# @numba.njit
# def f(a):
#     w = World([label.Label('a')])
#     # i = interval.closed(0.2, 0.8)
#     # l = label.Label('a')
#     # a.update(l,i)
#     return a
#     # return a.world

# l = numba.typed.List()
# l = []
# l.append(label.Label('a'))
# a = World(l)
# b = World([label.Label('b')])
# b._world[label.Label('b')] = interval.closed(3.0,4.0)
# # a = World([label.Label('a')])
# b = f(a)
# print(b)
# # d = numba.typed.Dict.empty(key_type=label.label_type, value_type=world_type)
# # d[label.Label('a')] = a
# # d[label.Label('a')] = b
# # print(d)