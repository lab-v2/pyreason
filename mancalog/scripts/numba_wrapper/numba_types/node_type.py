import mancalog.scripts.numba_wrapper.numba_types.world_type as world


class Node:
    available_labels = []
    
    def __init__(self, _id):
        self._id = _id
    
    def get_labels(self):
        return Node.available_labels

    def __str__(self):
        return self._id

    def __hash__(self):
        return hash(str(self))

    def get_id(self):
        return self._id

    def get_type(self):
        return 'node'

    def get_initial_world(self):
        return world.World(self.get_labels())

    def __repr__(self):
        return self.get_id()
        
    def __eq__(self, node):
        result = False
        if isinstance(self, type(node)):
            result = self is node

            result = result or (self._id == node.get_id())

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
class NodeType(types.Type):
    def __init__(self):
        super(NodeType, self).__init__(name='Node')

node_type = NodeType()


# Type inference
@typeof_impl.register(Node)
def typeof_node(val, c):
    return node_type


# Construct object from Numba functions
@type_callable(Node)
def type_node(context):
    def typer(_id):
        if isinstance(_id, types.UnicodeType):
            return node_type
    return typer


# Define native representation: datamodel
@register_model(NodeType)
class NodeModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('id', types.string)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(NodeType, 'id', 'id')

# Implement constructor
@lower_builtin(Node, types.string)
def impl_node(context, builder, sig, args):
    typ = sig.return_type
    _id = args[0]
    node = cgutils.create_struct_proxy(typ)(context, builder)
    node.id = _id
    return node._getvalue()

# Expose properties
@overload_method(NodeType, "get_id")
def get_id(node):
    def getter(node):
        return node.id
    return getter

@overload_method(NodeType, "get_initial_world")
def get_initial_world(node, labels):
    def impl(node, labels):
        return world.World(labels)
    return impl


@overload(operator.eq)
def node_eq(node_1, node_2):
    if isinstance(node_1, NodeType) and isinstance(node_2, NodeType):
        def impl(node_1, node_2):
            if node_1.id == node_2.id:
                return True
            else:
                return False 
        return impl

@overload(hash)
def node_hash(node):
    def impl(node):
        return hash(node.id)
    return impl


# Tell numba how to make native
@unbox(NodeType)
def unbox_node(typ, obj, c):
    id_obj = c.pyapi.object_getattr_string(obj, "_id")
    node = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    node.id = c.unbox(types.string, id_obj).value
    c.pyapi.decref(id_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(node._getvalue(), is_error=is_error)



@box(NodeType)
def box_node(typ, val, c):
    node = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Node))
    id_obj = c.box(types.string, node.id)
    res = c.pyapi.call_function_objargs(class_obj, (id_obj,))
    c.pyapi.decref(id_obj)
    c.pyapi.decref(class_obj)
    return res


# TEST
# import numba
# import label_type as label
# import interval_type as interval
# @numba.njit
# def f(n):
#     a = Node('abc')
#     a.get_labels()
#     return n

# f(1)

# # print(f(Node('abc'))._id)
# tuple_type = types.Tuple((label.label_type, interval.interval_type))
# d = numba.typed.Dict.empty(key_type=types.string, value_type=tuple_type)
# i = interval.closed(0.0, 1.0)
# l = label.Label('a')

# d['a'] = (l, i)
# print(d)