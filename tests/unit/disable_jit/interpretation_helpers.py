"""Utility to expose pure-Python versions of numba-compiled interpretation functions.

The previous implementation bound to ``interpretation_fp`` directly.  This module
now provides :func:`get_interpretation_helpers` which can return helpers for either
``interpretation_fp`` or ``interpretation`` based on the supplied module name.
"""

from types import SimpleNamespace
import importlib
import inspect
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def _py(func):
    """Return the underlying Python callable for numba compiled functions."""
    return getattr(func, "py_func", func)


def get_interpretation_helpers(module_name: str = "interpretation_fp"):
    """Return a namespace with helpers for the given interpretation module.

    Parameters
    ----------
    module_name:
        Either ``"interpretation_fp"`` or ``"interpretation"``.
    """
    interpretation = importlib.import_module(
        f"pyreason.scripts.interpretation.{module_name}"
    )

    ns = SimpleNamespace()
    ns.interpretation = interpretation
    ns.label = label

    ns.is_satisfied_edge = _py(interpretation.is_satisfied_edge)
    ns.is_satisfied_node = _py(interpretation.is_satisfied_node)
    ns.get_qualified_edge_groundings = _py(
        interpretation.get_qualified_edge_groundings
    )
    ns.get_qualified_node_groundings = _py(
        interpretation.get_qualified_node_groundings
    )
    ns.get_rule_node_clause_grounding = _py(
        interpretation.get_rule_node_clause_grounding
    )
    ns.get_rule_edge_clause_grounding = _py(
        interpretation.get_rule_edge_clause_grounding
    )
    ns.satisfies_threshold = _py(interpretation._satisfies_threshold)
    ns.check_node_grounding_threshold_satisfaction = _py(
        interpretation.check_node_grounding_threshold_satisfaction
    )
    ns.check_edge_grounding_threshold_satisfaction = _py(
        interpretation.check_edge_grounding_threshold_satisfaction
    )
    ns.refine_groundings = _py(interpretation.refine_groundings)
    ns.check_all_clause_satisfaction = _py(
        interpretation.check_all_clause_satisfaction
    )
    ns.add_node = _py(interpretation._add_node)

    _add_edge_fn = _py(interpretation._add_edge)
    if "num_ga" in inspect.signature(_add_edge_fn).parameters:
        def add_edge(*args):
            *pre, t = args
            return _add_edge_fn(*pre, [0], t)
    else:
        def add_edge(*args):
            return _add_edge_fn(*args)
    ns.add_edge = add_edge

    _ground_rule_fn = _py(interpretation._ground_rule)
    if "num_ga" in inspect.signature(_ground_rule_fn).parameters:
        def ground_rule(*args, **kwargs):
            return _ground_rule_fn(*args, num_ga=[0], **kwargs)
    else:
        def ground_rule(*args, **kwargs):
            return _ground_rule_fn(*args, **kwargs)
    ns.ground_rule = ground_rule
    ns.update_rule_trace = _py(interpretation._update_rule_trace)
    ns.are_satisfied_node = _py(interpretation.are_satisfied_node)
    ns.are_satisfied_edge = _py(interpretation.are_satisfied_edge)
    ns.is_satisfied_node_comparison = _py(
        interpretation.is_satisfied_node_comparison
    )
    ns.is_satisfied_edge_comparison = _py(
        interpretation.is_satisfied_edge_comparison
    )
    ns.check_consistent_node = _py(interpretation.check_consistent_node)
    ns.check_consistent_edge = _py(interpretation.check_consistent_edge)
    ns.resolve_inconsistency_node = _py(
        interpretation.resolve_inconsistency_node
    )
    ns.resolve_inconsistency_edge = _py(
        interpretation.resolve_inconsistency_edge
    )
    if hasattr(interpretation, "_add_node_to_interpretation"):
        ns.add_node_to_interpretation = _py(
            interpretation._add_node_to_interpretation
        )
    if hasattr(interpretation, "_add_edge_to_interpretation"):
        ns.add_edge_to_interpretation = _py(
            interpretation._add_edge_to_interpretation
        )
    ns.add_edges = _py(interpretation._add_edges)
    ns.delete_edge = _py(interpretation._delete_edge)
    ns.delete_node = _py(interpretation._delete_node)
    ns.float_to_str = _py(interpretation.float_to_str)
    ns.str_to_float = _py(interpretation.str_to_float)
    ns.str_to_int = _py(interpretation.str_to_int)
    ns.annotate = _py(interpretation.annotate)

    # Initialization helpers
    ns.init_reverse_neighbors = _py(
        interpretation.Interpretation._init_reverse_neighbors
    )

    _init_nodes_fn = _py(
        interpretation.Interpretation._init_interpretations_node
    )
    if "num_ga" in inspect.signature(_init_nodes_fn).parameters:
        def init_interpretations_node(nodes, specific_labels):
            return _init_nodes_fn(nodes, specific_labels, [0])
    else:
        def init_interpretations_node(nodes, specific_labels):
            return _init_nodes_fn(nodes, specific_labels)
    ns.init_interpretations_node = init_interpretations_node

    _init_edges_fn = _py(
        interpretation.Interpretation._init_interpretations_edge
    )
    if "num_ga" in inspect.signature(_init_edges_fn).parameters:
        def init_interpretations_edge(edges, specific_labels):
            return _init_edges_fn(edges, specific_labels, [0])
    else:
        def init_interpretations_edge(edges, specific_labels):
            return _init_edges_fn(edges, specific_labels)
    ns.init_interpretations_edge = init_interpretations_edge

    # Additional initialization helpers
    ns.init_convergence = _py(
        interpretation.Interpretation._init_convergence
    )
    ns.init_facts = _py(
        interpretation.Interpretation._init_facts
    )
    ns.start_fp = _py(
        interpretation.Interpretation._start_fp
    )

    _reason_fn = _py(interpretation.Interpretation.reason)
    if "num_ga" in inspect.signature(_reason_fn).parameters:
        def reason(
            interpretations_node,
            interpretations_edge,
            predicate_map_node,
            predicate_map_edge,
            tmax,
            prev_reasoning_data,
            rules,
            nodes,
            edges,
            neighbors,
            reverse_neighbors,
            rules_to_be_applied_node,
            rules_to_be_applied_edge,
            edges_to_be_added_node_rule,
            edges_to_be_added_edge_rule,
            rules_to_be_applied_node_trace,
            rules_to_be_applied_edge_trace,
            facts_to_be_applied_node,
            facts_to_be_applied_edge,
            facts_to_be_applied_node_trace,
            facts_to_be_applied_edge_trace,
            ipl,
            rule_trace_node,
            rule_trace_edge,
            rule_trace_node_atoms,
            rule_trace_edge_atoms,
            reverse_graph,
            atom_trace,
            save_graph_attributes_to_rule_trace,
            persistent,
            inconsistency_check,
            store_interpretation_changes,
            update_mode,
            allow_ground_rules,
            max_facts_time,
            annotation_functions,
            convergence_mode,
            convergence_delta,
            verbose,
            again,
        ):
            return _reason_fn(
                interpretations_node[0],
                interpretations_edge[0],
                predicate_map_node,
                predicate_map_edge,
                tmax,
                prev_reasoning_data,
                rules,
                nodes,
                edges,
                neighbors,
                reverse_neighbors,
                rules_to_be_applied_node,
                rules_to_be_applied_edge,
                edges_to_be_added_node_rule,
                edges_to_be_added_edge_rule,
                rules_to_be_applied_node_trace,
                rules_to_be_applied_edge_trace,
                facts_to_be_applied_node,
                facts_to_be_applied_edge,
                facts_to_be_applied_node_trace,
                facts_to_be_applied_edge_trace,
                ipl,
                rule_trace_node,
                rule_trace_edge,
                rule_trace_node_atoms,
                rule_trace_edge_atoms,
                reverse_graph,
                atom_trace,
                save_graph_attributes_to_rule_trace,
                persistent,
                inconsistency_check,
                store_interpretation_changes,
                update_mode,
                allow_ground_rules,
                max_facts_time,
                annotation_functions,
                convergence_mode,
                convergence_delta,
                [0],
                verbose,
                again,
            )
    else:
        reason = _reason_fn

    ns.reason = reason

    class FakeLabel:
        def __init__(self, value):
            self.value = value

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return isinstance(other, FakeLabel) and self.value == other.value

        def __repr__(self):
            return f"FakeLabel({self.value!r})"

    ns.FakeLabel = FakeLabel
    return ns


# Provide default exports for backward compatibility with existing tests
_default = get_interpretation_helpers("interpretation_fp")
for _name in dir(_default):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_default, _name)
