import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.rules.rule_internal import Rule

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


# Type ann_fn
@typeof_impl.register(Rule)
def typeof_rule(val, c):
    return rule_type


# Construct object from Numba functions (Doesn't work. We don't need this currently)
@type_callable(Rule)
def type_rule(context):
    def typer(rule_name, type, target, delta, clauses, bnd, thresholds, ann_fn, weights, edges, static, immediate_rule):
        if isinstance(rule_name, types.UnicodeType) and isinstance(type, types.UnicodeType) and isinstance(target, label.LabelType) and isinstance(delta, types.Integer) and isinstance(clauses, (types.NoneType, types.ListType)) and isinstance(bnd, interval.IntervalType) and isinstance(thresholds, types.ListType) and isinstance(ann_fn, types.UnicodeType) and isinstance(weights, types.Array) and isinstance(edges, types.Tuple) and isinstance(static, types.Boolean) and isinstance(immediate_rule, types.Boolean):
            return rule_type
    return typer


# Define native representation: data-model
@register_model(RuleType)
class RuleModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('rule_name', types.string),
            ('type', types.string),
            ('target', label.label_type),
            ('delta', types.uint16),
            ('clauses', types.ListType(types.Tuple((types.string, label.label_type, types.ListType(types.string), interval.interval_type, types.string)))),
            ('bnd', interval.interval_type),
            ('thresholds', types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64)))),
            ('ann_fn', types.string),
            ('weights', types.float64[::1]),
            ('edges', types.Tuple((types.string, types.string, label.label_type))),
            ('static', types.boolean),
            ('immediate_rule', types.boolean)
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose data-model attributes
make_attribute_wrapper(RuleType, 'rule_name', 'rule_name')
make_attribute_wrapper(RuleType, 'type', 'type')
make_attribute_wrapper(RuleType, 'target', 'target')
make_attribute_wrapper(RuleType, 'delta', 'delta')
make_attribute_wrapper(RuleType, 'clauses', 'clauses')
make_attribute_wrapper(RuleType, 'bnd', 'bnd')
make_attribute_wrapper(RuleType, 'thresholds', 'thresholds')
make_attribute_wrapper(RuleType, 'ann_fn', 'ann_fn')
make_attribute_wrapper(RuleType, 'weights', 'weights')
make_attribute_wrapper(RuleType, 'edges', 'edges')
make_attribute_wrapper(RuleType, 'static', 'static')
make_attribute_wrapper(RuleType, 'immediate_rule', 'immediate_rule')


# Implement constructor
@lower_builtin(Rule, types.string, types.string, label.label_type, types.uint16, types.ListType(types.Tuple((types.string, label.label_type, types.ListType(types.string), interval.interval_type, types.string))), interval.interval_type, types.ListType(types.ListType(types.Tuple((types.string, types.string, types.float64)))), types.string, types.float64[::1], types.Tuple((types.string, types.string, label.label_type)), types.boolean, types.boolean)
def impl_rule(context, builder, sig, args):
    typ = sig.return_type
    rule_name, type, target, delta, clauses, bnd, thresholds, ann_fn, weights, edges, static, immediate_rule = args
    context.nrt.incref(builder, types.ListType(types.Tuple((types.string, label.label_type, types.ListType(types.string), interval.interval_type, types.string))), clauses)
    context.nrt.incref(builder, types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), thresholds)
    rule = cgutils.create_struct_proxy(typ)(context, builder)
    rule.rule_name = rule_name
    rule.type = type
    rule.target = target
    rule.delta = delta
    rule.clauses = clauses
    rule.bnd = bnd
    rule.thresholds = thresholds
    rule.ann_fn = ann_fn
    rule.weights = weights
    rule.edges = edges
    rule.static = static
    rule.immediate_rule = immediate_rule
    return rule._getvalue()


# Expose properties
@overload_method(RuleType, "get_name")
def get_name(rule):
    def getter(rule):
        return rule.rule_name
    return getter


@overload_method(RuleType, "get_type")
def get_type(rule):
    def getter(rule):
        return rule.type
    return getter


@overload_method(RuleType, "get_target")
def get_target(rule):
    def getter(rule):
        return rule.target
    return getter


@overload_method(RuleType, "get_delta")
def get_delta(rule):
    def getter(rule):
        return rule.delta
    return getter


@overload_method(RuleType, "get_clauses")
def get_clauses(rule):
    def getter(rule):
        return rule.clauses
    return getter


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


@overload_method(RuleType, "get_annotation_function")
def get_annotation_function(rule):
    def impl(rule):
        return rule.ann_fn
    return impl


@overload_method(RuleType, "get_weights")
def get_weights(rule):
    def impl(rule):
        return rule.weights
    return impl


@overload_method(RuleType, "get_edges")
def get_edges(rule):
    def impl(rule):
        return rule.edges
    return impl


@overload_method(RuleType, "is_static_rule")
def is_static_rule(rule):
    def impl(rule):
        return rule.static
    return impl


@overload_method(RuleType, "is_immediate_rule")
def is_immediate_rule(rule):
    def impl(rule):
        return rule.immediate_rule
    return impl


# Tell numba how to make native
@unbox(RuleType)
def unbox_rule(typ, obj, c):
    name_obj = c.pyapi.object_getattr_string(obj, "_rule_name")
    type_obj = c.pyapi.object_getattr_string(obj, "_type")
    target_obj = c.pyapi.object_getattr_string(obj, "_target")
    delta_obj = c.pyapi.object_getattr_string(obj, "_delta")
    clauses_obj = c.pyapi.object_getattr_string(obj, "_clauses")
    bnd_obj = c.pyapi.object_getattr_string(obj, "_bnd")
    thresholds_obj = c.pyapi.object_getattr_string(obj, "_thresholds")
    ann_fn_obj = c.pyapi.object_getattr_string(obj, "_ann_fn")
    weights_obj = c.pyapi.object_getattr_string(obj, "_weights")
    edges_obj = c.pyapi.object_getattr_string(obj, "_edges")
    static_obj = c.pyapi.object_getattr_string(obj, "_static")
    immediate_rule_obj = c.pyapi.object_getattr_string(obj, "_immediate_rule")
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    rule.rule_name = c.unbox(types.string, name_obj).value
    rule.type = c.unbox(types.string, type_obj).value
    rule.target = c.unbox(label.label_type, target_obj).value
    rule.delta = c.unbox(types.uint16, delta_obj).value
    rule.clauses = c.unbox(types.ListType(types.Tuple((types.string, label.label_type, types.ListType(types.string), interval.interval_type, types.string))), clauses_obj).value
    rule.bnd = c.unbox(interval.interval_type, bnd_obj).value
    rule.thresholds = c.unbox(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), thresholds_obj).value
    rule.ann_fn = c.unbox(types.string, ann_fn_obj).value
    rule.weights = c.unbox(types.float64[::1], weights_obj).value
    rule.edges = c.unbox(types.Tuple((types.string, types.string, label.label_type)), edges_obj).value
    rule.static = c.unbox(types.boolean, static_obj).value
    rule.immediate_rule = c.unbox(types.boolean, immediate_rule_obj).value
    c.pyapi.decref(name_obj)
    c.pyapi.decref(type_obj)
    c.pyapi.decref(target_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(clauses_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(thresholds_obj)
    c.pyapi.decref(ann_fn_obj)
    c.pyapi.decref(weights_obj)
    c.pyapi.decref(edges_obj)
    c.pyapi.decref(static_obj)
    c.pyapi.decref(immediate_rule_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rule._getvalue(), is_error=is_error)


@box(RuleType)
def box_rule(typ, val, c):
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Rule))
    name_obj = c.box(types.string, rule.rule_name)
    type_obj = c.box(types.string, rule.type)
    target_obj = c.box(label.label_type, rule.target)
    delta_obj = c.box(types.uint16, rule.delta)
    clauses_obj = c.box(types.ListType(types.Tuple((types.string, label.label_type, types.ListType(types.string), interval.interval_type, types.string))), rule.clauses)
    bnd_obj = c.box(interval.interval_type, rule.bnd)
    thresholds_obj = c.box(types.ListType(types.Tuple((types.string, types.UniTuple(types.string, 2), types.float64))), rule.thresholds)
    ann_fn_obj = c.box(types.string, rule.ann_fn)
    weights_obj = c.box(types.float64[::1], rule.weights)
    edges_obj = c.box(types.Tuple((types.string, types.string, label.label_type)), rule.edges)
    static_obj = c.box(types.boolean, rule.static)
    immediate_rule_obj = c.box(types.boolean, rule.immediate_rule)
    res = c.pyapi.call_function_objargs(class_obj, (name_obj, type_obj, target_obj, delta_obj, clauses_obj, bnd_obj, thresholds_obj, ann_fn_obj, weights_obj, edges_obj, static_obj, immediate_rule_obj))
    c.pyapi.decref(name_obj)
    c.pyapi.decref(type_obj)
    c.pyapi.decref(target_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(clauses_obj)
    c.pyapi.decref(ann_fn_obj)
    c.pyapi.decref(bnd_obj)
    c.pyapi.decref(thresholds_obj)
    c.pyapi.decref(weights_obj)
    c.pyapi.decref(edges_obj)
    c.pyapi.decref(static_obj)
    c.pyapi.decref(immediate_rule_obj)
    c.pyapi.decref(class_obj)
    return res
