import numba
import pyreason.scripts.interpretation.interpretation as interpretation
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def test_satisfies_threshold_consistency():
    """_satisfies_threshold should match between JIT and pure Python."""
    thresh = ('greater_equal', ('number', 'total'), 4)
    jit_res = interpretation._satisfies_threshold(10, 5, thresh)
    py_res = interpretation._satisfies_threshold.py_func(10, 5, thresh)
    assert jit_res == py_res


def test_get_rule_node_clause_grounding_consistency():
    """get_rule_node_clause_grounding outputs should match between JIT and Python."""
    node_type = numba.types.string
    nodes = numba.typed.List(['n1', 'n2', 'n3'])
    groundings = numba.typed.Dict.empty(key_type=node_type, value_type=interpretation.list_of_nodes)
    predicate_map = numba.typed.Dict.empty(key_type=label.label_type, value_type=interpretation.list_of_nodes)
    l = label.Label('L')
    predicate_map[l] = numba.typed.List(['n1', 'n2'])

    jit_res = interpretation.get_rule_node_clause_grounding('X', groundings, predicate_map, l, nodes)
    py_res = interpretation.get_rule_node_clause_grounding.py_func('X', groundings, predicate_map, l, nodes)
    assert list(jit_res) == list(py_res)


def test_get_rule_edge_clause_grounding_consistency():
    """get_rule_edge_clause_grounding outputs should match between JIT and Python."""
    node_type = numba.types.string
    edge_type = numba.types.UniTuple(numba.types.string, 2)
    nodes = numba.typed.List(['n1', 'n2'])
    edges = numba.typed.List([('n1', 'n2'), ('n2', 'n1')])

    neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=interpretation.list_of_nodes)
    neighbors['n1'] = numba.typed.List(['n2'])
    neighbors['n2'] = numba.typed.List(['n1'])
    reverse_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=interpretation.list_of_nodes)
    reverse_neighbors['n1'] = numba.typed.List(['n2'])
    reverse_neighbors['n2'] = numba.typed.List(['n1'])

    groundings = numba.typed.Dict.empty(key_type=node_type, value_type=interpretation.list_of_nodes)
    groundings_edges = numba.typed.Dict.empty(key_type=edge_type, value_type=interpretation.list_of_edges)
    predicate_map = numba.typed.Dict.empty(key_type=label.label_type, value_type=interpretation.list_of_edges)
    l = label.Label('L')

    jit_res = interpretation.get_rule_edge_clause_grounding('X', 'Y', groundings, groundings_edges,
                                                            neighbors, reverse_neighbors, predicate_map, l, edges)
    py_res = interpretation.get_rule_edge_clause_grounding.py_func('X', 'Y', groundings, groundings_edges,
                                                                    neighbors, reverse_neighbors, predicate_map, l, edges)
    assert list(jit_res) == list(py_res)
