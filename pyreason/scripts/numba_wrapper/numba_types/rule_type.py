import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.rules.rule import Rule

from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_method
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box

# WARNING: problem with constructing inside jit function (not needed for now)
# Create new numba type
class RuleType(types.Type):
    def __init__(self):
        super(RuleType, self).__init__(name='Rule')

rule_type = RuleType()


# Type ann_fnerence
@typeof_impl.register(Rule)
def typeof_rule(val, c):
    return rule_type


# Construct object from Numba functions
@type_callable(Rule)
def type_rule(context):
    def typer(target, tc, delta, neigh_criteria, ann_fn, bnd, thresholds, subset, l, weights):
        if isinstance(target, label.LabelType) and isinstance(tc, (types.NoneType, types.ListType)) and isinstance(delta, types.Integer) and isinstance(neigh_criteria, (types.NoneType, types.ListType)) and isinstance(ann_fn, types.UnicodeType) and isinstance(bnd, interval.IntervalType) and isinstance(thresholds, types.ListType) and isinstance(subset, types.Tuple) and isinstance(l, label.LabelType) and isinstance(weights, types.Array):
            return rule_type
    return typer


# Define native representation: datamodel
@register_model(RuleType)
class RuleModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('target', label.label_type),
            ('target_criteria', types.ListType(types.Tuple((label.label_type, interval.interval_type)))),
            ('delta', types.int8),
            ('neigh_criteria', types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), label.label_type, interval.interval_type)))),
            ('ann_fn', types.string),
            ('bnd', interval.interval_type),
            ('thresholds', types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64)))),
            ('subset', types.UniTuple(types.string, 2)),
            ('l', label.label_type),
            ('weights', types.float64[::1])
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(RuleType, 'target', 'target')
make_attribute_wrapper(RuleType, 'target_criteria', 'target_criteria')
make_attribute_wrapper(RuleType, 'delta', 'delta')
make_attribute_wrapper(RuleType, 'neigh_criteria', 'neigh_criteria')
make_attribute_wrapper(RuleType, 'ann_fn', 'ann_fn')
make_attribute_wrapper(RuleType, 'bnd', 'bnd')
make_attribute_wrapper(RuleType, 'thresholds', 'thresholds')
make_attribute_wrapper(RuleType, 'subset', 'subset')
make_attribute_wrapper(RuleType, 'l', 'l')
make_attribute_wrapper(RuleType, 'weights', 'weights')

# Implement constructor
@lower_builtin(Rule, label.label_type, types.ListType(types.Tuple((label.label_type, interval.interval_type))), types.int8, types.ListType(types.Tuple((types.string, label.label_type, interval.interval_type))), types.string, interval.interval_type, types.ListType(types.ListType(types.Tuple((types.string, types.string, types.float64)))), types.UniTuple(types.string, 2), label.label_type, types.float64[::1])
def impl_rule(context, builder, sig, args):
    typ = sig.return_type
    target, target_criteria, delta, neigh_criteria, ann_fn, bnd, thresholds, subset, l, weights = args
    context.nrt.incref(builder, types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), label.label_type, interval.interval_type))), neigh_criteria)
    context.nrt.incref(builder, types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), thresholds)
    rule = cgutils.create_struct_proxy(typ)(context, builder)
    rule.target = target
    rule.target_criteria = target_criteria
    rule.delta = delta
    rule.neigh_criteria = neigh_criteria
    rule.ann_fn = ann_fn
    rule.bnd = bnd
    rule.thresholds = thresholds
    rule.subset = subset
    rule.l = l
    rule.weights = weights
    return rule._getvalue()

# Expose properties
@overload_method(RuleType, "get_target")
def get_target(rule):
    def getter(rule):
        return rule.target
    return getter

@overload_method(RuleType, "get_target_criteria")
def get_target_criteria(rule):
    def getter(rule):
        return rule.target_criteria
    return getter

@overload_method(RuleType, "get_delta")
def get_delta(rule):
    def getter(rule):
        return rule.delta
    return getter

@overload_method(RuleType, "get_neigh_criteria")
def get_neigh_criteria(rule):
    def getter(rule):
        return rule.neigh_criteria
    return getter

@overload_method(RuleType, "get_annotation_function")
def get_annotation_function(rule):
    def impl(rule):
        return rule.ann_fn
    return impl

@overload_method(RuleType, "get_bnd")
def get_bnd(rule):
    def impl(rule):
        return rule.bnd
    return impl

@overload_method(RuleType, "get_thresholds")
def get_thresholds(rule):
    def impl(rule):
        return rule.thresholds
    return impl

@overload_method(RuleType, "get_subset")
def get_subset(rule):
    def impl(rule):
        return rule.subset
    return impl

@overload_method(RuleType, "get_label")
def get_label(rule):
    def impl(rule):
        return rule.l
    return impl



# Tell numba how to make native
@unbox(RuleType)
def unbox_rule(typ, obj, c):
    target_obj = c.pyapi.object_getattr_string(obj, "_target")
    tc_obj = c.pyapi.object_getattr_string(obj, "_target_criteria")
    delta_obj = c.pyapi.object_getattr_string(obj, "_delta")
    neigh_criteria_obj = c.pyapi.object_getattr_string(obj, "_neigh_criteria")
    ann_fn_obj = c.pyapi.object_getattr_string(obj, "_ann_fn")
    bnd_obj = c.pyapi.object_getattr_string(obj, "_bnd")
    thresholds_obj = c.pyapi.object_getattr_string(obj, "_thresholds")
    subset_obj = c.pyapi.object_getattr_string(obj, "_subset")
    label_obj = c.pyapi.object_getattr_string(obj, "_label")
    weights_obj = c.pyapi.object_getattr_string(obj, "_weights")
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    rule.target = c.unbox(label.label_type, target_obj).value
    rule.target_criteria = c.unbox(types.ListType(types.Tuple((label.label_type, interval.interval_type))), tc_obj).value
    rule.delta = c.unbox(types.int8, delta_obj).value
    rule.neigh_criteria = c.unbox(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), label.label_type, interval.interval_type))), neigh_criteria_obj).value
    rule.ann_fn = c.unbox(types.string, ann_fn_obj).value
    rule.bnd = c.unbox(interval.interval_type, bnd_obj).value
    rule.thresholds = c.unbox(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), thresholds_obj).value
    rule.subset = c.unbox(types.UniTuple(types.string, 2), subset_obj).value
    rule.l = c.unbox(label.label_type, label_obj).value
    rule.weights = c.unbox(types.float64[::1], weights_obj).value
    c.pyapi.decref(target_obj)
    c.pyapi.decref(tc_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(neigh_criteria_obj)
    c.pyapi.decref(ann_fn_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(thresholds_obj)
    c.pyapi.decref(subset_obj)
    c.pyapi.decref(label_obj)
    c.pyapi.decref(weights_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rule._getvalue(), is_error=is_error)



@box(RuleType)
def box_rule(typ, val, c):
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Rule))
    target_obj = c.box(label.label_type, rule.target)
    tc_obj = c.box(types.ListType(types.Tuple((label.label_type, interval.interval_type))), rule.tc_node)
    delta_obj = c.box(types.int8, rule.delta)
    neigh_criteria_obj = c.box(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), label.label_type, interval.interval_type))), rule.neigh_criteria)
    ann_fn_obj = c.box(types.string, rule.ann_fn)
    bnd_obj = c.box(interval.interval_type, rule.bnd)
    thresholds_obj = c.box(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), rule.thresholds)
    subset_obj = c.box(types.UniTuple(types.string, 2), rule.subset)
    label_obj = c.box(label.label_type, rule.l)
    weights_obj = c.box(types.float64[::1], rule.weights)
    res = c.pyapi.call_function_objargs(class_obj, (target_obj, tc_obj, delta_obj, neigh_criteria_obj, ann_fn_obj, bnd_obj, thresholds_obj, subset_obj, label_obj, weights_obj))
    c.pyapi.decref(target_obj)
    c.pyapi.decref(tc_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(neigh_criteria_obj)
    c.pyapi.decref(ann_fn_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(thresholds_obj)
    c.pyapi.decref(subset_obj)
    c.pyapi.decref(label_obj)
    c.pyapi.decref(weights_obj)
    c.pyapi.decref(class_obj)
    return res
