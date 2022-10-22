import pyreason.scripts.numba_wrapper.numba_types.world_type as world


class Edge:
    available_labels = []
    
    def __init__(self, source, target):
        self._source = source
        self._target = target
        self._id = source + ':' + target
    
    def get_labels(self):
        return Edge.available_labels

    def __str__(self):
        return self._id

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return get_id()

    def get_source(self):
        return self._source

    def get_target(self):
        return self._target

    def get_id(self):
        return self._id

    def get_type(self):
        return 'edge'

    def get_initial_world(self):
        return world.World(self.get_labels())
        
    def __eq__(self, edge):
        result = False
        if isinstance(self, type(edge)):
            result = self is edge

            result = result or (self._source == edge.get_source() and self._target == edge.get_target())

        return result


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
class EdgeType(types.Type):
    def __init__(self):
        super(EdgeType, self).__init__(name='Edge')

edge_type = EdgeType()


# Type inference
@typeof_impl.register(Edge)
def typeof_edge(val, c):
    return edge_type


# Construct object from Numba functions
@type_callable(Edge)
def type_edge(context):
    def typer(source, target):
        if isinstance(source, types.UnicodeType) and isinstance(target, types.UnicodeType):
            return edge_type
    return typer

# Constructor for internal use only
@type_callable(Edge)
def type_edge(context):
    def typer(source, target, Id):
        if isinstance(source, types.UnicodeType) and isinstance(target, types.UnicodeType) and isinstance(Id, types.UnicodeType):
            return edge_type
    return typer


# Define native representation: datamodel
@register_model(EdgeType)
class EdgeModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('source', types.string),
            ('target', types.string),
            ('id', types.string)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(EdgeType, 'source', 'source')
make_attribute_wrapper(EdgeType, 'target', 'target')
make_attribute_wrapper(EdgeType, 'id', 'id')

# Implement constructor
@lower_builtin(Edge, types.string, types.string)
def impl_edge(context, builder, sig, args):
    def make_edge(source, target):
        edge = Edge(source, target, source + ':' + target)
        return edge

    edge = context.compile_internal(builder, make_edge, sig, args)
    return edge

# Constructor for internal use only
@lower_builtin(Edge, types.string, types.string, types.string)
def impl_edge(context, builder, sig, args):
    typ = sig.return_type
    source, target, i = args
    context.nrt.incref(builder, types.string, i)
    edge = cgutils.create_struct_proxy(typ)(context, builder)
    edge.source = source
    edge.target = target
    edge.id = i
    return edge._getvalue()

# Expose properties
@overload_method(EdgeType, "get_id")
def get_id(edge):
    def getter(edge):
        return edge.id
    return getter

@overload_method(EdgeType, "get_initial_world")
def get_initial_world(edge, labels):
    def impl(edge, labels):
        return world.World(labels)
    return impl


@overload(operator.eq)
def edge_eq(edge_1, edge_2):
    if isinstance(edge_1, EdgeType) and isinstance(edge_2, EdgeType):
        def impl(edge_1, edge_2):
            if edge_1.source == edge_2.source and edge_1.target == edge_2.target:
                return True
            else:
                return False 
        return impl

@overload(hash)
def edge_hash(edge):
    def impl(edge):
        return hash(edge.id)
    return impl


# Tell numba how to make native
@unbox(EdgeType)
def unbox_edge(typ, obj, c):
    source_obj = c.pyapi.object_getattr_string(obj, "_source")
    target_obj = c.pyapi.object_getattr_string(obj, "_target")
    id_obj = c.pyapi.object_getattr_string(obj, "_id")
    edge = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    edge.source = c.unbox(types.string, source_obj).value
    edge.target = c.unbox(types.string, target_obj).value
    edge.id = c.unbox(types.string, id_obj).value
    c.pyapi.decref(source_obj)
    c.pyapi.decref(target_obj)
    c.pyapi.decref(id_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(edge._getvalue(), is_error=is_error)



@box(EdgeType)
def box_edge(typ, val, c):
    edge = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Edge))
    source_obj = c.box(types.string, edge.source)
    target_obj = c.box(types.string, edge.target)
    id_obj = c.box(types.string, edge.id)
    res = c.pyapi.call_function_objargs(class_obj, (source_obj, target_obj))
    c.pyapi.decref(source_obj)
    c.pyapi.decref(target_obj)
    c.pyapi.decref(class_obj)
    return res


# TEST
# import numba
# @numba.njit
# def f(n):
#     a = Edge('abc', 'a')
#     print(a.get_id())
#     return a

# print(f(Edge('abc', 'a')))
