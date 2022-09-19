import mancalog.scripts.numba_wrapper.numba_types.interval_type as interval

class SftTippingFunction():
    
    def __init__(self):
        self._threshold = 0.5
        self._bnd_update = interval.closed(0.7, 1.0)

    def influence(self, neigh_len, qualified_neigh_len):
        bnd = interval.closed(0.0, 1.0)
        if neigh_len != 0:
            if (qualified_neigh_len / neigh_len) > self._threshold:
                bnd = self._bnd_update

        return bnd


import numpy as np
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
class SftTippingType(types.Type):
    def __init__(self):
        super(SftTippingType, self).__init__(name='SftTipping')

sft_tipping_type = SftTippingType()


# Type inference
@typeof_impl.register(SftTippingFunction)
def typeof_sft_tipping(val, c):
    return sft_tipping_type


# Construct object from Numba functions
@type_callable(SftTippingFunction)
def type_sft_tipping(context):
    def typer():
        return sft_tipping_type
    return typer


# Define native representation: datamodel
@register_model(SftTippingType)
class SftTippingModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('threshold', types.float32),
            ('bnd_update', interval.interval_type)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(SftTippingType, 'threshold', 'threshold')
make_attribute_wrapper(SftTippingType, 'bnd_update', 'bnd_update')

# Implement constructor
@lower_builtin(SftTippingFunction)
def impl_sft_tipping(context, builder, sig, args):
    typ = sig.return_type
    sft_tipping = cgutils.create_struct_proxy(typ)(context, builder)
    sft_tipping.threshold = np.float32(0.5)
    sft_tipping.bnd_update = interval.closed(0.7, 1.0)
    return sft_tipping._getvalue()

# Expose properties
@overload_method(SftTippingType, "influence")
def influence(sft_tipping, neigh_len, qualified_neigh_len):
    def getter(sft_tipping, neigh_len, qualified_neigh_len):
        bnd = interval.closed(0.0, 1.0)
        if neigh_len != 0:
            if (qualified_neigh_len / neigh_len) >= sft_tipping.threshold:
                bnd = sft_tipping.bnd_update
        return bnd
    return getter




# Tell numba how to make native
@unbox(SftTippingType)
def unbox_sft_tipping(typ, obj, c):
    threshold_obj = c.pyapi.object_getattr_string(obj, "_threshold")
    bnd_update_obj = c.pyapi.object_getattr_string(obj, "_bnd_update")
    sft_tipping = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    sft_tipping.threshold = c.unbox(types.float32, threshold_obj).value
    sft_tipping.bnd_update = c.unbox(interval.interval_type, bnd_update_obj).value
    c.pyapi.decref(threshold_obj)
    c.pyapi.decref(bnd_update_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(sft_tipping._getvalue(), is_error=is_error)



@box(SftTippingType)
def box_sft_tipping(typ, val, c):
    sft_tipping = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(SftTippingFunction))
    res = c.pyapi.call_function_objargs(class_obj, ())
    c.pyapi.decref(class_obj)
    return res
