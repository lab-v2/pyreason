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


# Create new numba type
class RuleType(types.Type):
    def __init__(self):
        super(RuleType, self).__init__(name='Rule')

rule_type = RuleType()


# Type inference
@typeof_impl.register(Rule)
def typeof_rule(val, c):
    return rule_type


# Construct object from Numba functions
@type_callable(Rule)
def type_rule(context):
    def typer(target, tc, delta, neigh_nodes, neigh_edges, inf, thresholds):
        if isinstance(target, label.LabelType) and isinstance(tc, (types.NoneType, types.ListType)) and isinstance(delta, types.Integer) and isinstance(neigh_nodes, (types.NoneType, types.ListType)) and isinstance(neigh_edges, (types.NoneType, types.ListType)) and isinstance(inf, types.UnicodeType) and isinstance(thresholds, types.ListType):
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
            ('neigh_nodes', types.ListType(types.Tuple((label.label_type, interval.interval_type)))),
            ('neigh_edges', types.ListType(types.Tuple((label.label_type, interval.interval_type)))),
            ('inf', types.string),
            ('thresholds', types.ListType(types.Tuple((types.string, types.string, types.float64))))
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)


# Expose datamodel attributes
make_attribute_wrapper(RuleType, 'target', 'target')
make_attribute_wrapper(RuleType, 'target_criteria', 'target_criteria')
make_attribute_wrapper(RuleType, 'delta', 'delta')
make_attribute_wrapper(RuleType, 'neigh_nodes', 'neigh_nodes')
make_attribute_wrapper(RuleType, 'neigh_edges', 'neigh_edges')
make_attribute_wrapper(RuleType, 'inf', 'inf')
make_attribute_wrapper(RuleType, 'thresholds', 'thresholds')

# Implement constructor
@lower_builtin(Rule, label.label_type, types.ListType(types.Tuple((label.label_type, interval.interval_type))), types.int8, types.ListType(types.Tuple((label.label_type, interval.interval_type))), types.ListType(types.Tuple((label.label_type, interval.interval_type))), types.string, types.ListType(types.Tuple((types.string, types.string, types.float64))))
def impl_rule(context, builder, sig, args):
    typ = sig.return_type
    target, target_criteria, delta, neigh_nodes, neigh_edges, inf, thresholds = args
    context.nrt.incref(builder, types.ListType(types.Tuple((label.label_type, interval.interval_type))), neigh_nodes)
    context.nrt.incref(builder, types.ListType(types.Tuple((label.label_type, interval.interval_type))), neigh_edges)
    rule = cgutils.create_struct_proxy(typ)(context, builder)
    rule.target = target
    rule.target_criteria = target_criteria
    rule.delta = delta
    rule.neigh_nodes = neigh_nodes
    rule.neig_edges = neigh_edges
    rule.inf = inf
    rule.thresholds = thresholds
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

@overload_method(RuleType, "get_neigh_nodes")
def get_neigh_nodes(rule):
    def getter(rule):
        return rule.neigh_nodes
    return getter

@overload_method(RuleType, "get_neigh_edges")
def get_neigh_edges(rule):
    def getter(rule):
        return rule.neigh_edges
    return getter

@overload_method(RuleType, "get_influence")
def get_influence(rule):
    def impl(rule):
        return rule.inf
    return impl

@overload_method(RuleType, "get_thresholds")
def get_thresholds(rule):
    def impl(rule):
        return rule.thresholds
    return impl




# Tell numba how to make native
@unbox(RuleType)
def unbox_rule(typ, obj, c):
    target_obj = c.pyapi.object_getattr_string(obj, "_target")
    tc_obj = c.pyapi.object_getattr_string(obj, "_target_criteria")
    delta_obj = c.pyapi.object_getattr_string(obj, "_delta")
    neigh_nodes_obj = c.pyapi.object_getattr_string(obj, "_neigh_nodes")
    neigh_edges_obj = c.pyapi.object_getattr_string(obj, "_neigh_edges")
    inf_obj = c.pyapi.object_getattr_string(obj, "_inf")
    thresholds_obj = c.pyapi.object_getattr_string(obj, "_thresholds")
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    rule.target = c.unbox(label.label_type, target_obj).value
    rule.target_criteria = c.unbox(types.ListType(types.Tuple((label.label_type, interval.interval_type))), tc_obj).value
    rule.delta = c.unbox(types.int8, delta_obj).value
    rule.neigh_nodes = c.unbox(types.ListType(types.Tuple((label.label_type, interval.interval_type))), neigh_nodes_obj).value
    rule.neigh_edges = c.unbox(types.ListType(types.Tuple((label.label_type, interval.interval_type))), neigh_edges_obj).value
    rule.inf = c.unbox(types.string, inf_obj).value
    rule.thresholds = c.unbox(types.ListType(types.Tuple((types.string, types.string, types.float64))), thresholds_obj).value
    c.pyapi.decref(target_obj)
    c.pyapi.decref(tc_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(neigh_nodes_obj)
    c.pyapi.decref(neigh_edges_obj)
    c.pyapi.decref(inf_obj)
    c.pyapi.decref(thresholds_obj)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(rule._getvalue(), is_error=is_error)



@box(RuleType)
def box_rule(typ, val, c):
    rule = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Rule))
    target_obj = c.box(label.label_type, rule.target)
    tc_obj = c.box(types.ListType(types.Tuple((label.label_type, interval.interval_type))), rule.tc_node)
    delta_obj = c.box(types.int8, rule.delta)
    neigh_nodes_obj = c.box(types.ListType(types.Tuple((label.label_type, interval.interval_type))), rule.neigh_nodes)
    neigh_edges_obj = c.box(types.ListType(types.Tuple((label.label_type, interval.interval_type))), rule.neigh_edges)
    inf_obj = c.box(types.string, rule.inf)
    thresholds_obj = c.box(types.ListType(types.Tuple((types.string, types.string, types.float64))), rule.thresholds)
    res = c.pyapi.call_function_objargs(class_obj, (target_obj, tc_obj, delta_obj, neigh_nodes_obj, neigh_edges_obj, inf_obj, thresholds_obj))
    c.pyapi.decref(target_obj)
    c.pyapi.decref(tc_obj)
    c.pyapi.decref(delta_obj)
    c.pyapi.decref(neigh_nodes_obj)
    c.pyapi.decref(neigh_edges_obj)
    c.pyapi.decref(inf_obj)
    c.pyapi.decref(thresholds_obj)
    c.pyapi.decref(class_obj)
    return res
