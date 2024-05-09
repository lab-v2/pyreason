from pyreason.scripts.threshold.threshold import Threshold
from numba import types  
from numba.extending import models, register_model, make_attribute_wrapper  
from numba.extending import lower_builtin  
from numba.core import cgutils  
from numba.extending import unbox, NativeValue, box  
from numba.extending import typeof_impl

# Define the Numba type for Threshold  
class ThresholdType(types.Type):  
    def __init__(self):  
        super(ThresholdType, self).__init__(name='Threshold')  
  
threshold_type = ThresholdType()  
  
# Register the type with Numba  
@typeof_impl.register(Threshold)  
def typeof_threshold(val, c):  
    return threshold_type  
  
# Define the data model for the type  
@register_model(ThresholdType)  
class ThresholdModel(models.StructModel):  
    def __init__(self, dmm, fe_type):  
        members = [  
            ('quantifier', types.unicode_type),  
            ('quantifier_type', types.UniTuple(types.unicode_type, 2)),  
            ('thresh', types.int64)  
        ]  
        models.StructModel.__init__(self, dmm, fe_type, members)  
  
# Make attributes accessible  
make_attribute_wrapper(ThresholdType, 'quantifier', 'quantifier')  
make_attribute_wrapper(ThresholdType, 'quantifier_type', 'quantifier_type')  
make_attribute_wrapper(ThresholdType, 'thresh', 'thresh')  
  
# Implement the constructor for the type  
@lower_builtin(Threshold, types.unicode_type, types.UniTuple(types.unicode_type, 2), types.int64)  
def impl_threshold(context, builder, sig, args):  
    typ = sig.return_type  
    quantifier, quantifier_type, thresh = args  
    threshold = cgutils.create_struct_proxy(typ)(context, builder)  
    threshold.quantifier = quantifier  
    threshold.quantifier_type = quantifier_type  
    threshold.thresh = thresh  
    return threshold._getvalue()  
  
# Tell Numba how to unbox and box the type  
@unbox(ThresholdType)  
def unbox_threshold(typ, obj, c):  
    quantifier_obj = c.pyapi.object_getattr_string(obj, 'quantifier')  
    quantifier_type_obj = c.pyapi.object_getattr_string(obj, 'quantifier_type')  
    thresh_obj = c.pyapi.object_getattr_string(obj, 'thresh')  
  
    threshold = cgutils.create_struct_proxy(typ)(c.context, c.builder)  
    threshold.quantifier = c.unbox(types.unicode_type, quantifier_obj).value  
    threshold.quantifier_type = c.unbox(types.UniTuple(types.unicode_type, 2), quantifier_type_obj).value  
    threshold.thresh = c.unbox(types.int64, thresh_obj).value  
  
    c.pyapi.decref(quantifier_obj)  
    c.pyapi.decref(quantifier_type_obj)  
    c.pyapi.decref(thresh_obj)  
      
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())  
    return NativeValue(threshold._getvalue(), is_error=is_error)  
  
@box(ThresholdType)
def box_threshold(typ, val, c):
    threshold = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    threshold_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Threshold))

    quantifier_obj = c.box(types.unicode_type, threshold.quantifier)
    quantifier_type_obj = c.box(types.UniTuple(types.unicode_type, 2), threshold.quantifier_type)
    thresh_obj = c.box(types.int64, threshold.thresh)

    # Create the Threshold object using its constructor
    threshold_instance = c.pyapi.call_function_objargs(
        threshold_obj,
        (quantifier_obj, quantifier_type_obj, thresh_obj)
    )

    # Decrease the reference count of the boxed objects
    c.pyapi.decref(quantifier_obj)
    c.pyapi.decref(quantifier_type_obj)
    c.pyapi.decref(thresh_obj)
    c.pyapi.decref(threshold_obj)

    # Return the boxed Threshold object
    return threshold_instance