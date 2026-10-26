import importlib

import numba
import pytest


@pytest.mark.parametrize("engine", ["interpretation", "interpretation_parallel", "interpretation_fp"])
@pytest.mark.parametrize("atom_trace", [False, True])
@pytest.mark.parametrize(
    "removed_indices, expected_indices",
    [({-1}, [0, 1, 2]), ({1}, [0, 2]), ({0, 1, 2}, [])],
    ids=["retain-all", "remove-middle", "remove-all"],
)
def test_filter_pending_node_rules_with_no_edges(engine, atom_trace, removed_indices, expected_indices):
    """Retain delayed node rules and their traces without requiring edge entries."""
    module = importlib.import_module(f"pyreason.scripts.interpretation.{engine}")
    rules = numba.typed.List.empty_list(module.rules_to_be_applied_node_type)
    edges = numba.typed.List.empty_list(module.edges_to_be_added_type)
    traces = numba.typed.List.empty_list(module.rules_to_be_applied_trace_type)

    for index in range(3):
        node = f"node_{index}"
        rules.append((numba.uint16(index + 1), node, module.label.Label("result"),
                      module.interval.closed(1, 1), False))
        if atom_trace:
            qualified_nodes = numba.typed.List.empty_list(module.list_of_nodes)
            qualified_nodes.append(numba.typed.List([node]))
            qualified_edges = numba.typed.List.empty_list(module.list_of_edges)
            traces.append((qualified_nodes, qualified_edges, f"rule_{index}"))

    module._filter_pending_node_rules(rules, edges, traces, removed_indices, atom_trace)

    assert [rule[1] for rule in rules] == [f"node_{index}" for index in expected_indices]
    assert len(edges) == 0
    if atom_trace:
        assert [trace[2] for trace in traces] == [f"rule_{index}" for index in expected_indices]
        assert [list(trace[0][0]) for trace in traces] == [
            [f"node_{index}"] for index in expected_indices
        ]
    else:
        assert len(traces) == 0
