import numba

import label_type as label
import interval_type as interval


class World:
	
	def __init__(self, labels):
		self.labels = labels
		self._world = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
		for l in labels:
			self._world[l] = interval.closed(0.0, 1.0)

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
        if isinstance(labels, types.ListType):
            return world_type
    return typer


# Define native representation: datamodel
@register_model(WorldType)
class WorldModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('world', types.DictType(label.label_type, interval.interval_type)),
			('labels', types.List(types.string))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(WorldType, 'world', 'world')
make_attribute_wrapper(WorldType, 'labels', 'labels')

# Implement constructor
@lower_builtin(World, types.ListType(types.string))
def impl_world(context, builder, sig, args):
    typ = sig.return_type
    node = cgutils.create_struct_proxy(typ)(context, builder)
    labels = args[0]
    for l in numba.typed.List(labels):
        node.world[l] = interval.closed(0.0, 1.0)
        
    return node._getvalue()

# Expose properties
# TODO

# @overload(operator.eq)
# def world_eq(world_1, world_2):
# 	if isinstance(world_1, WorldType) and isinstance(world_2, WorldType):
# 		def impl(world_1, world_2):
# 			if node_1.id == node_2.id:
# 				return True
# 			else:
# 				return False 
# 		return impl

# @overload(hash)
# def node_hash(node):
# 	def impl(node):
# 		return hash(node.id)
# 	return impl


# Tell numba how to make native
@unbox(WorldType)
def unbox_world(typ, obj, c):
    world_obj = c.pyapi.object_getattr_string(obj, "world")
    world = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    world.world = c.unbox(types.string, world_obj).value
    c.pyapi.decref(world_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(world._getvalue(), is_error=is_error)



@box(WorldType)
def box_world(typ, val, c):
    world = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(World))
    labels_obj = c.box(types.List(types.string), world.labels)
    res = c.pyapi.call_function_objargs(class_obj, (labels_obj,))
    c.pyapi.decref(labels_obj)
    c.pyapi.decref(class_obj)
    return res

import numba
@numba.njit
def f():
    l = numba.typed.List()
    l.append('a')
    a = World(l)
    return a

print(f())