# HEY WE CHANGED THIS — Numba is gone on the Fable branch.
# This file used to compare JIT vs .py_func. Everything is plain Python now,
# so we just call each helper twice and assert they agree (same function).
# import numba
import pyreason.scripts.interpretation.interpretation as interpretation
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def _py(func):
    # HEY WE CHANGED THIS — was func.py_func (Numba wrapper). Fallback is the func itself.
    return getattr(func, "py_func", func)


def test_satisfies_threshold_consistency():
    """_satisfies_threshold should match between JIT and pure Python."""
    thresh = ('greater_equal', ('number', 'total'), 4)
    jit_res = interpretation._satisfies_threshold(10, 5, thresh)
    py_res = _py(interpretation._satisfies_threshold)(10, 5, thresh)
    assert jit_res == py_res


def test_get_rule_node_clause_grounding_consistency():
    """get_rule_node_clause_grounding outputs should match between JIT and Python."""
    # HEY WE CHANGED THIS — was numba.types / numba.typed.*; plain list/dict now.
    # node_type = numba.types.string
    # nodes = numba.typed.List(['n1', 'n2', 'n3'])
    # groundings = numba.typed.Dict.empty(...)
    nodes = ['n1', 'n2', 'n3']
    groundings = {}
    predicate_map = {}
    l = label.Label('L')
    predicate_map[l] = ['n1', 'n2']

    jit_res = interpretation.get_rule_node_clause_grounding('X', groundings, predicate_map, l, nodes)
    py_res = _py(interpretation.get_rule_node_clause_grounding)('X', groundings, predicate_map, l, nodes)
    assert list(jit_res) == list(py_res)


def test_get_rule_edge_clause_grounding_consistency():
    """get_rule_edge_clause_grounding outputs should match between JIT and Python."""
    # HEY WE CHANGED THIS — was numba typed containers; plain list/dict now.
    nodes = ['n1', 'n2']
    edges = [('n1', 'n2'), ('n2', 'n1')]

    neighbors = {}
    neighbors['n1'] = ['n2']
    neighbors['n2'] = ['n1']
    reverse_neighbors = {}
    reverse_neighbors['n1'] = ['n2']
    reverse_neighbors['n2'] = ['n1']

    groundings = {}
    groundings_edges = {}
    predicate_map = {}
    l = label.Label('L')

    jit_res = interpretation.get_rule_edge_clause_grounding(
        'X', 'Y', groundings, groundings_edges,
        neighbors, reverse_neighbors, predicate_map, l, edges,
    )
    py_res = _py(interpretation.get_rule_edge_clause_grounding)(
        'X', 'Y', groundings, groundings_edges,
        neighbors, reverse_neighbors, predicate_map, l, edges,
    )
    assert list(jit_res) == list(py_res)
