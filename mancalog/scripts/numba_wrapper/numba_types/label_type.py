class Label:
	
	def __init__(self, value):
		self._value = value

	def get_value(self):
		return self._value

	def __eq__(self, label):
		result = (self._value == label.get_value()) and isinstance(label, type(self))
		return result

	def __str__(self):
		return self._value

	def __hash__(self):
		return hash(str(self))

	def test(self, array):
		return array[0].value


from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box
from numba import njit


# Create new numba type
class LabelType(types.Type):
    def __init__(self):
        super(LabelType, self).__init__(name='Label')

label_type = LabelType()


# Type inference
@typeof_impl.register(Label)
def typeof_label(val, c):
    return label_type


# Construct object from Numba functions
@type_callable(Label)
def type_label(context):
    def typer(value):
        if isinstance(value, types.UnicodeType):
            return label_type
    return typer


# Define native representation: datamodel
@register_model(LabelType)
class LabelModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('value', types.string)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(LabelType, 'value', 'value')


# Implement constructor
@lower_builtin(Label, types.string)
def impl_label(context, builder, sig, args):
    typ = sig.return_type
    value = args[0]
    label = cgutils.create_struct_proxy(typ)(context, builder)
    label.value = value
    return label._getvalue()


# Expose properties
@overload_method(LabelType, "get_value")
def get_value(label):
    def getter(label):
        return label.value
    return getter

@overload_method(LabelType, "__str__")
def __str__(label):
    def getter(label):
        return label.value
    return getter

@overload_method(LabelType, "test")
def test(array):
	def getter(array):
		return array[0].value
	return getter


# Test
from numba import jit, typeof
import numpy as np
@jit(nopython=True)
def f():
	n = Label('abc')
	a = [n]
	return n.test(a)

print(f())