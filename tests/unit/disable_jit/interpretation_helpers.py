import pyreason.scripts.interpretation.interpretation_fp as interpretation
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

# Bind pure-Python callables for Numba-compiled functions
_is_sat_edge = interpretation.is_satisfied_edge
is_satisfied_edge = getattr(_is_sat_edge, "py_func", _is_sat_edge)

_is_sat_node = interpretation.is_satisfied_node
is_satisfied_node = getattr(_is_sat_node, "py_func", _is_sat_node)

_get_q_edge_groundings = interpretation.get_qualified_edge_groundings
get_qualified_edge_groundings = getattr(_get_q_edge_groundings, "py_func", _get_q_edge_groundings)

_get_q_node_groundings = interpretation.get_qualified_node_groundings
get_qualified_node_groundings = getattr(_get_q_node_groundings, "py_func", _get_q_node_groundings)

_get_rule_node_clause_grounding = interpretation.get_rule_node_clause_grounding
get_rule_node_clause_grounding = getattr(_get_rule_node_clause_grounding, "py_func", _get_rule_node_clause_grounding)

_get_rule_edge_clause_grounding = interpretation.get_rule_edge_clause_grounding
get_rule_edge_clause_grounding = getattr(_get_rule_edge_clause_grounding, "py_func", _get_rule_edge_clause_grounding)

_satisfies_threshold = interpretation._satisfies_threshold
satisfies_threshold = getattr(_satisfies_threshold, "py_func", _satisfies_threshold)

_check_node_thresh = interpretation.check_node_grounding_threshold_satisfaction
check_node_grounding_threshold_satisfaction = getattr(_check_node_thresh, "py_func", _check_node_thresh)

_check_edge_thresh = interpretation.check_edge_grounding_threshold_satisfaction
check_edge_grounding_threshold_satisfaction = getattr(_check_edge_thresh, "py_func", _check_edge_thresh)

_refine_groundings = interpretation.refine_groundings
refine_groundings = getattr(_refine_groundings, "py_func", _refine_groundings)

_check_all = interpretation.check_all_clause_satisfaction
check_all_clause_satisfaction = getattr(_check_all, "py_func", _check_all)

_add_node = interpretation._add_node
add_node = getattr(_add_node, "py_func", _add_node)

_add_edge = interpretation._add_edge
add_edge = getattr(_add_edge, "py_func", _add_edge)

_ground_rule = interpretation._ground_rule
ground_rule = getattr(_ground_rule, "py_func", _ground_rule)

_update_rule_trace = interpretation._update_rule_trace
update_rule_trace = getattr(_update_rule_trace, "py_func", _update_rule_trace)

_are_sat_node = interpretation.are_satisfied_node
are_satisfied_node = getattr(_are_sat_node, "py_func", _are_sat_node)

_are_sat_edge = interpretation.are_satisfied_edge
are_satisfied_edge = getattr(_are_sat_edge, "py_func", _are_sat_edge)

_is_sat_node_cmp = interpretation.is_satisfied_node_comparison
is_satisfied_node_comparison = getattr(_is_sat_node_cmp, "py_func", _is_sat_node_cmp)

_is_sat_edge_cmp = interpretation.is_satisfied_edge_comparison
is_satisfied_edge_comparison = getattr(_is_sat_edge_cmp, "py_func", _is_sat_edge_cmp)

_check_cons_node = interpretation.check_consistent_node
check_consistent_node = getattr(_check_cons_node, "py_func", _check_cons_node)

_check_cons_edge = interpretation.check_consistent_edge
check_consistent_edge = getattr(_check_cons_edge, "py_func", _check_cons_edge)

_resolve_incons_node = interpretation.resolve_inconsistency_node
resolve_inconsistency_node = getattr(_resolve_incons_node, "py_func", _resolve_incons_node)

_resolve_incons_edge = interpretation.resolve_inconsistency_edge
resolve_inconsistency_edge = getattr(_resolve_incons_edge, "py_func", _resolve_incons_edge)

_add_node_interp = interpretation._add_node_to_interpretation
add_node_to_interpretation = getattr(_add_node_interp, "py_func", _add_node_interp)

_add_edge_interp = interpretation._add_edge_to_interpretation
add_edge_to_interpretation = getattr(_add_edge_interp, "py_func", _add_edge_interp)

_add_edges_fn = interpretation._add_edges
add_edges = getattr(_add_edges_fn, "py_func", _add_edges_fn)

_delete_edge_fn = interpretation._delete_edge
delete_edge = getattr(_delete_edge_fn, "py_func", _delete_edge_fn)

_delete_node_fn = interpretation._delete_node
delete_node = getattr(_delete_node_fn, "py_func", _delete_node_fn)

_float_to_str = interpretation.float_to_str
float_to_str = getattr(_float_to_str, "py_func", _float_to_str)

_str_to_float = interpretation.str_to_float
str_to_float = getattr(_str_to_float, "py_func", _str_to_float)

_str_to_int = interpretation.str_to_int
str_to_int = getattr(_str_to_int, "py_func", _str_to_int)

_annotate = interpretation.annotate
annotate = getattr(_annotate, "py_func", _annotate)

_reason = interpretation.Interpretation.reason
reason = getattr(_reason, "py_func", _reason)

class FakeLabel:
    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, FakeLabel) and self.value == other.value

    def __repr__(self):
        return f"FakeLabel({self.value!r})"
