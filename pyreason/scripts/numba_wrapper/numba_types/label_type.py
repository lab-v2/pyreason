from pyreason.scripts.components.label import Label

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
def get_id(label):
    def getter(label):
        return label.value
    return getter

@overload(operator.eq)
def label_eq(label_1, label_2):
    if isinstance(label_1, LabelType) and isinstance(label_2, LabelType):
        def impl(label_1, label_2):
            if label_1.value == label_2.value:
                return True
            else:
                return False 
        return impl

@overload(hash)
def label_hash(label):
    def impl(label):
        return hash(label.value)
    return impl



# Tell numba how to make native
@unbox(LabelType)
def unbox_label(typ, obj, c):
    value_obj = c.pyapi.object_getattr_string(obj, "_value")
    label = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    label.value = c.unbox(types.string, value_obj).value
    c.pyapi.decref(value_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(label._getvalue(), is_error=is_error)



@box(LabelType)
def box_label(typ, val, c):
    label = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Label))
    value_obj = c.box(types.string, label.value)
    res = c.pyapi.call_function_objargs(class_obj, (value_obj,))
    c.pyapi.decref(value_obj)
    c.pyapi.decref(class_obj)
    return res

