from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_attribute
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box
from numba import njit
# from numba import cuda


class Node:
    available_labels = []
    
    def __init__(self, id):
        self._id = id
    
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

	# def __eq__(self, node):
	# 	result = False
	# 	if isinstance(self, type(node)):
	# 		result = self is node

	# 		result = result or (self._id == node.get_id())

	# 	return result


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
def type_interval(context):
    def typer(_id):
        if isinstance(_id, types.string):
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
def impl_interval(context, builder, sig, args):
    typ = sig.return_type
    _id = args[0]
    node = cgutils.create_struct_proxy(typ)(context, builder)
    node.id = _id
    return node._getvalue()

# Expose properties
@overload_attribute(NodeType, "get_id")
def get_id(node):
    def getter(node):
        return node.id
    return getter



# Tell numba how to make native


# Return class values from numba functions
@unbox(NodeType)
def unbox_interval(typ, obj, c):
    """
    Convert a Interval object to a native interval structure.
    """
    id_obj = c.pyapi.object_getattr_string(obj, "id")
    node = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    node.id = c.pyapi.string_as_string(id_obj)
    c.pyapi.decref(id_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(node._getvalue(), is_error=is_error)

@box(NodeType)
def box_interval(typ, val, c):
    """
    Convert a native interval structure to an Interval object.
    """
    node = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    id_obj = c.pyapi.string_from_string(node.id)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Node))
    res = c.pyapi.call_function_objargs(class_obj, (id_obj))
    c.pyapi.decref(id_obj)
    c.pyapi.decref(class_obj)
    return res


from numba import jit

@jit(nopython=True)
def f():
    return Node("abc").id

print(f())