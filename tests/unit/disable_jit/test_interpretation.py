# tests/unit/test_interpretation.py
import pytest
import math
from unittest.mock import Mock, call

# Single, consistent import style: import the module once
import pyreason.scripts.interpretation.interpretation_fp as interpretation
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

# Bind pure-Python callables (works even if Numba compiled elsewhere)
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


class FakeWorld:
    """Minimal stand-in for World."""
    def __init__(self, truth_by_label=None, name=""):
        self.truth_by_label = truth_by_label or {}
        self.name = name

    def is_satisfied(self, label, interval):
        # interval content isn't important to the edge function; we key by label.
        return self.truth_by_label.get(label, False)


@pytest.fixture
def interpretations():
    # Mirrors your printed mapping
    return {
        ('Justin', 'Cat'):  FakeWorld({'owns': False}, "owns,[0.0,0.0]"),
        ('Justin', 'Dog'):  FakeWorld({'owns': True},  "owns,[1.0,1.0]"),
    }


# ---- is_satisfied_node  and is_satisfied_edge tests ----

def test_satisfied_path_true(interpretations):
    comp = ('Justin', 'Dog')
    na = ('owns', [1.0, 1.0])
    assert _is_sat_node(interpretations, comp, na) is True
    assert is_satisfied_edge(interpretations, comp, na) is True

def test_satisfied_path_false(interpretations):
    comp = ('Justin', 'Cat')
    na = ('owns', [1.0, 1.0])
    assert is_satisfied_edge(interpretations, comp, na) is False

def test_missing_comp_key_false():
    # name kept from your original file; behavior is True when na has None
    interpretations = {}
    comp = ('Nobody', 'Home')
    na = ('owns', None)
    assert _is_sat_node(interpretations, comp, na) is True
    assert is_satisfied_edge(interpretations, comp, na) is True
    
def test_is_satisfied_edge_returns_false_when_comp_missing():
    # Empty dict so interpretations[comp] raises inside the try-block
    interpretations = {}
    comp = ("ghost", "edge")
    na = ("owns", [1.0, 1.0])  # both non-None => enter try/except
    assert _is_sat_node(interpretations, comp, na) is False
    assert is_satisfied_edge(interpretations, comp, na) is False


# ---- get_qualified_edge_groundings and get_qualified_node_groundings tests ----

def test_get_qualified_edge_and_node_groundings_filters_true_edges(interpretations, monkeypatch):
    # Use a plain list instead of a typed list for easy assertions
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    # Separate mocks so each gets exactly 3 calls
    mock_is_sat_edge = Mock(side_effect=[False, True, True])  # F, T, T
    mock_is_sat_node = Mock(side_effect=[False, True, True])  # F, T, T

    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mock_is_sat_node)

    grounding = [
        ('Justin', 'Cat'),   # False
        ('Justin', 'Dog'),   # True
        ('Nobody', 'Home'),  # True
    ]
    clause_l, clause_bnd = 'owns', [1.0, 1.0]

    result_edge = get_qualified_edge_groundings(interpretations, grounding, clause_l, clause_bnd)
    result_node = get_qualified_node_groundings(interpretations, grounding, clause_l, clause_bnd)

    assert result_edge == [grounding[1], grounding[2]]
    assert result_node == [grounding[1], grounding[2]]

    # Each mock is called 3 times with the same argument sequence
    assert mock_is_sat_edge.call_count == 3
    assert mock_is_sat_node.call_count == 3

    from unittest.mock import call
    expected_calls = [
        call(interpretations, grounding[0], (clause_l, clause_bnd)),
        call(interpretations, grounding[1], (clause_l, clause_bnd)),
        call(interpretations, grounding[2], (clause_l, clause_bnd)),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mock_is_sat_node.assert_has_calls(expected_calls)


def test_get_qualified_edge_and_node_groundings_none_qualify(interpretations, monkeypatch):
    # Return a plain list instead of a numba typed list for easy assertions
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    # Separate mocks so each gets exactly len(grounding) calls
    mock_is_sat_edge = Mock(return_value=False)
    mock_is_sat_node = Mock(return_value=False)
    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mock_is_sat_node)

    grounding = [('Justin', 'Dog'), ('Justin', 'Cat')]

    result_edge = get_qualified_edge_groundings(interpretations, grounding, 'owns', [1.0, 1.0])
    result_node = get_qualified_node_groundings(interpretations, grounding, 'owns', [1.0, 1.0])

    assert result_edge == []
    assert result_node == []
    assert mock_is_sat_edge.call_count == 2
    assert mock_is_sat_node.call_count == 2

    expected_calls = [
        call(interpretations, grounding[0], ('owns', [1.0, 1.0])),
        call(interpretations, grounding[1], ('owns', [1.0, 1.0])),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mock_is_sat_node.assert_has_calls(expected_calls)


def test_get_qualified_edge_and_node_groundings_all_qualify(interpretations, monkeypatch):
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    mock_is_sat_edge = Mock(return_value=True)
    mock_is_sat_node = Mock(return_value=True)
    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mock_is_sat_node)

    grounding = [('A', 'B'), ('C', 'D')]

    result_edge = get_qualified_edge_groundings(interpretations, grounding, 'owns', [1.0, 1.0])
    result_node = get_qualified_node_groundings(interpretations, grounding, 'owns', [1.0, 1.0])

    assert result_edge == grounding
    assert result_node == grounding
    assert mock_is_sat_edge.call_count == 2
    assert mock_is_sat_node.call_count == 2

    expected_calls = [
        call(interpretations, grounding[0], ('owns', [1.0, 1.0])),
        call(interpretations, grounding[1], ('owns', [1.0, 1.0])),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mock_is_sat_node.assert_has_calls(expected_calls)

# ---- get_rule_node_clause_grounding tests ----

def test_rule_node_clause_grounding_uses_predicate_map_when_label_present_and_no_prior():
    clause_var_1 = "X"
    groundings = {}  # no prior grounding
    predicate_map = {"owns": ["u", "v"]}
    l = "owns"
    nodes = ["a", "b", "c"]

    result = get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes)

    # Returns predicate_map[l]
    assert result == ["u", "v"]
    assert result is predicate_map["owns"]  # same object


def test_rule_node_clause_grounding_prefers_prior_when_exists_even_if_label_present():
    clause_var_1 = "X"
    prior = ["p1", "p2"]
    groundings = {"X": prior}  # prior grounding exists
    predicate_map = {"owns": ["u", "v"]}
    l = "owns"
    nodes = ["a", "b", "c"]

    result = get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes)

    # Returns groundings[clause_var_1]
    assert result == prior
    assert result is prior  # same object


def test_rule_node_clause_grounding_uses_all_nodes_when_label_absent_and_no_prior():
    clause_var_1 = "X"
    groundings = {}  # no prior
    predicate_map = {"likes": ["x", "y"]}  # label 'owns' absent
    l = "owns"
    nodes = ["a", "b", "c"]

    result = get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes)

    # Falls back to all nodes
    assert result == nodes
    assert result is nodes  # same object


def test_rule_node_clause_grounding_prefers_prior_when_label_absent_but_prior_exists():
    clause_var_1 = "X"
    prior = ["p1", "p2"]
    groundings = {"X": prior}
    predicate_map = {"likes": ["x", "y"]}  # label 'owns' absent
    l = "owns"
    nodes = ["a", "b", "c"]

    result = get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes)

    # Uses prior grounding again
    assert result == prior
    assert result is prior  # same object

# ---- get_rule_edge_clause_grounding tests ----

def _patch_typed_list_to_plain_list(monkeypatch):
    # Make interpretation.numba.typed.List(...) return a plain list,
    # and .empty_list(...) return [] so extend() etc. work.
    class _ListShim:
        def __call__(self, iterable):
            return list(iterable)
        def empty_list(self, *a, **k):
            return []
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())

def test_rule_edge_clause_case1_uses_predicate_map_when_label_present(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    groundings = {}
    groundings_edges = {}
    neighbors, reverse_neighbors = {}, {}
    edges = [('a','x'), ('b','y')]  # unused in this branch
    pm_edges = [('u','v'), ('w','z')]
    predicate_map = {"owns": pm_edges}
    l = "owns"

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    # Returns predicate_map[l] directly
    assert result == pm_edges
    assert result is pm_edges  # same object

def test_rule_edge_clause_case1_falls_back_to_edges_when_label_absent(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    groundings = {}
    groundings_edges = {}
    neighbors, reverse_neighbors = {}, {}
    edges = [('a','x'), ('b','y')]
    predicate_map = {}  # l not present
    l = "owns"

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    # Returns 'edges' directly
    assert result == edges
    assert result is edges

def test_rule_edge_clause_case2_sources_of_Z(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    # Z seen, Y not seen
    groundings = {"Z": ["t1", "t2"]}
    groundings_edges = {}
    neighbors = {}
    reverse_neighbors = {
        "t1": ["s1", "s2"],
        "t2": ["s3"],
    }
    predicate_map, l = {}, "owns"
    edges = []

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    # For each n in groundings[Z], add (src, n) for each src in reverse_neighbors[n]
    assert result == [("s1","t1"), ("s2","t1"), ("s3","t2")]

def test_rule_edge_clause_case3_neighbors_of_Y(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    # Y seen, Z not seen
    groundings = {"Y": ["s1", "s2"]}
    groundings_edges = {}
    neighbors = {
        "s1": ["t1", "t2"],
        "s2": ["t3"],
    }
    reverse_neighbors = {}
    predicate_map, l = {}, "owns"
    edges = []

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    # For each n in groundings[Y], add (n, nn) for nn in neighbors[n]
    assert result == [("s1","t1"), ("s1","t2"), ("s2","t3")]

def test_rule_edge_clause_case4_returns_existing_groundings_edges(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    groundings = {"Y": ["s"], "Z": ["t"]}
    # Pair already exists as an edge grounding
    existing = [("pre","made")]
    groundings_edges = {("Y","Z"): existing}
    neighbors, reverse_neighbors = {}, {}
    predicate_map, l, edges = {}, "owns", []

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    assert result == existing
    assert result is existing  # returned by reference

def test_rule_edge_clause_case4_intersect_neighbors_with_var2_groundings(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)
    clause_var_1, clause_var_2 = "Y", "Z"
    # Both vars seen, but no existing edge grounding for (Y,Z)
    groundings = {"Y": ["a", "b"], "Z": ["b", "c"]}  # set(Z) = {b, c}
    groundings_edges = {}
    neighbors = {
        "a": ["b", "x"],  # only 'b' is in set(Z)
        "b": ["c"],       # 'c' is in set(Z)
    }
    reverse_neighbors = {}
    predicate_map, l, edges = {}, "owns", []

    result = get_rule_edge_clause_grounding(
        clause_var_1, clause_var_2,
        groundings, groundings_edges,
        neighbors, reverse_neighbors,
        predicate_map, l, edges
    )

    # Only neighbors that are also in groundings[Z] are kept
    assert result == [("a","b"), ("b","c")]


# ---- satisfies_threshold tests ----

@pytest.mark.parametrize(
    "op,num_neigh,num_qualified,thr,expected",
    [
        ("greater_equal", 10, 10, 10, True),
        ("greater_equal", 10, 9,  10, False),

        ("greater",       10, 11, 10, True),
        ("greater",       10, 10, 10, False),

        ("less_equal",    10, 10, 10, True),
        ("less_equal",    10, 11, 10, False),

        ("less",          10,  9, 10, True),
        ("less",          10, 10, 10, False),

        ("equal",         10,  7,  7, True),
        ("equal",         10,  7,  8, False),
    ],
)
def test_satisfies_threshold_number_mode(op, num_neigh, num_qualified, thr, expected):
    threshold = (op, ("number",), thr)
    assert satisfies_threshold(num_neigh, num_qualified, threshold) is expected


def test_satisfies_threshold_percent_mode_divide_by_zero_is_false():
    threshold = ("greater_equal", ("percent",), 50)  # 50%
    assert satisfies_threshold(0, 0, threshold) is False


@pytest.mark.parametrize(
    "op,num_neigh,num_qualified,thr_percent,expected",
    [
        # >= and > cases
        ("greater_equal", 5, 3, 60, True),   # 3/5=0.6 >= 0.60
        ("greater_equal", 5, 2, 60, False),  # 0.4 >= 0.60 -> False
        ("greater",       4, 3, 75, False),  # 0.75 > 0.75 -> False
        ("greater",       4, 3, 74, True),   # 0.75 > 0.74 -> True

        # <= and < cases
        ("less_equal",    4, 3, 80, True),   # 0.75 <= 0.80 -> True
        ("less_equal",    4, 3, 70, False),  # 0.75 <= 0.70 -> False
        ("less",          2, 1, 60, True),   # 0.5 < 0.60 -> True
        ("less",          2, 1, 50, False),  # 0.5 < 0.50 -> False (equality)

        # equality case (pick clean ratio to avoid FP fuzz)
        ("equal",         4, 2, 50, True),   # 0.5 == 0.5
        ("equal",         5, 2, 50, False),  # 0.4 != 0.5
    ],
)
def test_satisfies_threshold_percent_mode(op, num_neigh, num_qualified, thr_percent, expected):
    threshold = (op, ("percent",), thr_percent)  # percent stored as whole number (e.g., 75 -> 0.75)
    assert satisfies_threshold(num_neigh, num_qualified, threshold) is expected


# ---- check_*_grounding_threshold_satisfaction (parametrized for node & edge) ----

@pytest.mark.parametrize(
    "label,check_fn,get_q_attr,grounding,qualified,threshold",
    [
        (
            "node",
            check_node_grounding_threshold_satisfaction,
            "get_qualified_node_groundings",
            ["n1", "n2", "n3"],          # grounding
            ["n1", "n2"],               # qualified_grounding
            ("greater_equal", ("number", "total"), 2),
        ),
        (
            "edge",
            check_edge_grounding_threshold_satisfaction,
            "get_qualified_edge_groundings",
            [("a","b"), ("c","d"), ("e","f")],   # grounding
            [("a","b"), ("c","d")],              # qualified_grounding
            ("greater_equal", ("number", "total"), 2),
        ),
    ],
)
def test_check_grounding_threshold_total_uses_len_grounding(
    interpretations, monkeypatch, label, check_fn, get_q_attr, grounding, qualified, threshold
):
    # _satisfies_threshold should be called with len(grounding) and len(qualified)
    mock_sat = Mock(return_value=True)
    monkeypatch.setattr(interpretation, "_satisfies_threshold", mock_sat)

    # Should NOT call the get_qualified_* in 'total' mode
    mock_get_q = Mock()
    monkeypatch.setattr(interpretation, get_q_attr, mock_get_q)

    out = check_fn(interpretations, grounding, qualified, "owns", threshold)

    assert out is True
    mock_sat.assert_called_once_with(len(grounding), len(qualified), threshold)
    mock_get_q.assert_not_called()


@pytest.mark.parametrize(
    "label,check_fn,get_q_attr,grounding,qualified,threshold,available_return",
    [
        (
            "node",
            check_node_grounding_threshold_satisfaction,
            "get_qualified_node_groundings",
            ["x", "y", "z", "w"],
            ["x"],                               # qualified_grounding length = 1
            ("less", ("percent", "available"), 60),
            ["a", "b", "c"],                    # len=3 becomes neigh_len
        ),
        (
            "edge",
            check_edge_grounding_threshold_satisfaction,
            "get_qualified_edge_groundings",
            [("u","v"), ("v","w"), ("w","x"), ("x","y")],
            [("u","v")],                        # qualified_grounding length = 1
            ("less", ("percent", "available"), 60),
            [("p","q"), ("q","r"), ("r","s")], # len=3 becomes neigh_len
        ),
    ],
)
def test_check_grounding_threshold_available_calls_get_qualified(
    interpretations, monkeypatch, label, check_fn, get_q_attr, grounding, qualified, threshold, available_return
):
    # Avoid constructing real Interval; just return a sentinel
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: ("closed", lo, up))
    sentinel_closed = interpretation.interval.closed(0, 1)

    # get_qualified_* returns N "available" neighbors -> neigh_len should be N
    mock_get_q = Mock(return_value=available_return)
    monkeypatch.setattr(interpretation, get_q_attr, mock_get_q)

    # _satisfies_threshold should be called with (len(available_return), len(qualified), threshold)
    mock_sat = Mock(return_value=False)
    monkeypatch.setattr(interpretation, "_satisfies_threshold", mock_sat)

    out = check_fn(interpretations, grounding, qualified, "owns", threshold)

    assert out is False
    mock_get_q.assert_called_once_with(interpretations, grounding, "owns", sentinel_closed)
    mock_sat.assert_called_once_with(len(available_return), len(qualified), threshold)



def test_check_node_grounding_threshold_available_calls_get_qualified(interpretations, monkeypatch):
    # Replace interval.closed to avoid constructing real Interval objects
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: ("closed", lo, up))
    sentinel_closed = interpretation.interval.closed(0, 1)

    # get_qualified_node_groundings returns 3 "available" neighbors
    mock_get_q = Mock(return_value=["a", "b", "c"])  # len = 3
    monkeypatch.setattr(interpretation, "get_qualified_node_groundings", mock_get_q)

    # _satisfies_threshold should be called with neigh_len = 3, qualified_len = 1
    mock_sat = Mock(return_value=False)
    monkeypatch.setattr(interpretation, "_satisfies_threshold", mock_sat)

    grounding = ["x", "y", "z", "w"]        # original neighbors (len doesn't matter in 'available' branch)
    qualified_grounding = ["x"]             # len = 1
    clause_label = "owns"
    threshold = ("less", ("percent", "available"), 60)  # mode 'percent', quantifier 'available'

    out = check_node_grounding_threshold_satisfaction(
        interpretations, grounding, qualified_grounding, clause_label, threshold
    )

    assert out is False
    mock_get_q.assert_called_once_with(interpretations, grounding, clause_label, sentinel_closed)
    mock_sat.assert_called_once_with(3, 1, threshold)


# ---- refine_groundings tests ----

def test_refine_groundings_forward_neighbor_filters_edges_and_updates_nodes(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)

    clause_variables = ["X"]
    groundings = {
        "X": ["a1"],     # refined
        "Y": ["b0"],     # will be rebuilt
    }
    groundings_edges = {
        ("X", "Y"): [("a1", "b1"), ("a2", "b2"), ("a1", "b2")],
    }
    neighbors = {"X": ["Y"]}
    reverse_neighbors = {}

    refine_groundings(clause_variables, groundings, groundings_edges, neighbors, reverse_neighbors)

    # Only edges whose source is in groundings["X"] survive
    assert groundings_edges[("X", "Y")] == [("a1", "b1"), ("a1", "b2")]
    # Y's node groundings rebuilt from surviving targets, deduped
    assert groundings["Y"] == ["b1", "b2"]
    # X unchanged
    assert groundings["X"] == ["a1"]


def test_refine_groundings_reverse_neighbor_filters_edges_and_updates_nodes(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)

    clause_variables = ["X"]
    groundings = {
        "X": ["a1"],     # refined
        "Z": ["z0"],     # will be rebuilt from sources of surviving edges into X
    }
    groundings_edges = {
        ("Z", "X"): [("z1", "a1"), ("z2", "a2")],
    }
    neighbors = {}
    reverse_neighbors = {"X": ["Z"]}

    refine_groundings(clause_variables, groundings, groundings_edges, neighbors, reverse_neighbors)

    # Only edges whose target is in groundings["X"] survive
    assert groundings_edges[("Z", "X")] == [("z1", "a1")]
    # Z's node groundings rebuilt from surviving sources, deduped
    assert groundings["Z"] == ["z1"]
    # X unchanged
    assert groundings["X"] == ["a1"]


def test_refine_groundings_propagates_across_two_hops(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)

    # X refined -> affects Y via (X,Y), which then affects Z via (Y,Z)
    clause_variables = ["X"]
    groundings = {
        "X": ["a1"],   # refined frontier
        "Y": ["b0"],   # will be rebuilt from (X,Y)
        "Z": ["c0"],   # will be rebuilt from (Y,Z) in the second wave
    }
    groundings_edges = {
        ("X", "Y"): [("a1", "b1"), ("a2", "b2")],
        ("Y", "Z"): [("b1", "c1"), ("b2", "c2")],
    }
    neighbors = {
        "X": ["Y"],
        "Y": ["Z"],
    }
    reverse_neighbors = {
        "Y": ["X"],
        "Z": ["Y"],
    }

    refine_groundings(clause_variables, groundings, groundings_edges, neighbors, reverse_neighbors)

    # After wave 1: (X,Y) filtered by X=["a1"] -> keep only ("a1","b1"); Y=["b1"]
    assert groundings_edges[("X", "Y")] == [("a1", "b1")]
    assert groundings["Y"] == ["b1"]

    # After wave 2: (Y,Z) filtered by Y=["b1"] -> keep only ("b1","c1"); Z=["c1"]
    assert groundings_edges[("Y", "Z")] == [("b1", "c1")]
    assert groundings["Z"] == ["c1"]


def test_refine_groundings_deduplicates_neighbor_nodes(monkeypatch):
    _patch_typed_list_to_plain_list(monkeypatch)

    clause_variables = ["X"]
    groundings = {
        "X": ["a1"],
        "Y": ["old"],  # will be rebuilt
    }
    # Duplicate edges to the same target should yield unique nodes in Y
    groundings_edges = {
        ("X", "Y"): [("a1", "b1"), ("a1", "b1"), ("a1", "b2")],
    }
    neighbors = {"X": ["Y"]}
    reverse_neighbors = {}

    refine_groundings(clause_variables, groundings, groundings_edges, neighbors, reverse_neighbors)

    # Edges keep duplicates (filtering doesn’t dedup edges), but node list is deduped by the set
    assert groundings_edges[("X", "Y")] == [("a1", "b1"), ("a1", "b1"), ("a1", "b2")]
    assert groundings["Y"] == ["b1", "b2"]

# ---- check_all_clause_satisfaction tests ----

def test_check_all_clause_satisfaction_calls_both_helpers_and_ands_results(interpretations, monkeypatch):
    # Node helper returns False; Edge helper returns True
    mock_node = Mock(return_value=False)
    mock_edge = Mock(return_value=True)
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", mock_node)
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", mock_edge)

    # Groundings/edges expected by the function
    groundings = {"X": ["n1", "n2"]}
    groundings_edges = {("X", "Y"): [("n1", "m1"), ("n2", "m2")]}

    clauses = [
        ("node", "owns", ("X",)),        # uses groundings["X"]
        ("edge", "likes", ("X", "Y")),   # uses groundings_edges[("X","Y")]
    ]
    thresholds = [
        ("greater_equal", ("number", "total"), 1),
        ("greater_equal", ("number", "total"), 1),
    ]

    out = check_all_clause_satisfaction(
        interpretations, interpretations, clauses, thresholds, groundings, groundings_edges
    )

    # Overall AND -> False and no short-circuit: both helpers were called
    assert out is False
    mock_node.assert_called_once_with(
        interpretations, groundings["X"], groundings["X"], "owns", thresholds[0]
    )
    mock_edge.assert_called_once_with(
        interpretations, groundings_edges[("X", "Y")], groundings_edges[("X", "Y")], "likes", thresholds[1]
    )


def test_check_all_clause_satisfaction_all_true_returns_true(interpretations, monkeypatch):
    mock_node = Mock(return_value=True)
    mock_edge = Mock(return_value=True)
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", mock_node)
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", mock_edge)

    groundings = {"X": ["n1"]}
    groundings_edges = {("X", "Y"): [("n1", "m1")]}

    clauses = [
        ("node", "owns", ("X",)),
        ("edge", "likes", ("X", "Y")),
    ]
    thresholds = [
        ("greater_equal", ("number", "total"), 1),
        ("greater_equal", ("number", "total"), 1),
    ]

    out = check_all_clause_satisfaction(
        interpretations, interpretations, clauses, thresholds, groundings, groundings_edges
    )

    assert out is True
    assert mock_node.call_count == 1
    assert mock_edge.call_count == 1


def test_check_all_clause_satisfaction_empty_clauses_returns_true(interpretations):
    # No clauses: initialized satisfaction=True should be returned
    out = check_all_clause_satisfaction(
        interpretations, interpretations, [], [], {}, {}
    )
    assert out is True


def test_check_all_clause_satisfaction_multiple_clauses_no_short_circuit(interpretations, monkeypatch):
    # First two fail, last succeeds — we still call all of them once
    seq_node = [False, False, True]  # we'll use node helper for 3 node clauses
    mock_node = Mock(side_effect=seq_node)
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", mock_node)

    # No edge clauses in this test; keep the symbol in place
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", Mock())

    groundings = {"A": ["a"], "B": ["b"], "C": ["c"]}
    groundings_edges = {}

    clauses = [
        ("node", "L1", ("A",)),
        ("node", "L2", ("B",)),
        ("node", "L3", ("C",)),
    ]
    thresholds = [
        ("greater_equal", ("number", "total"), 1),
        ("greater_equal", ("number", "total"), 1),
        ("greater_equal", ("number", "total"), 1),
    ]

    out = check_all_clause_satisfaction(
        interpretations, interpretations, clauses, thresholds, groundings, groundings_edges
    )

    assert out is False                          # False AND False AND True -> False
    assert mock_node.call_count == 3             # all evaluated; no short-circuit
    # Verify the calls used the right arguments each time
    expected_calls = [
        call(interpretations, groundings["A"], groundings["A"], "L1", thresholds[0]),
        call(interpretations, groundings["B"], groundings["B"], "L2", thresholds[1]),
        call(interpretations, groundings["C"], groundings["C"], "L3", thresholds[2]),
    ]
    mock_node.assert_has_calls(expected_calls)


def test_add_node_minimal(monkeypatch):
    # Make typed empty lists just plain lists, and stub World
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])
    class DummyWorld:
        def __init__(self, labels):
            self.labels = labels
    monkeypatch.setattr(interpretation.world, "World", DummyWorld)

    nodes = []
    neighbors = {}
    reverse_neighbors = {}
    interpretations_node = {}

    add_node("A", neighbors, reverse_neighbors, nodes, interpretations_node)

    # All four statements covered:
    assert nodes == ["A"]
    assert neighbors["A"] == []
    assert reverse_neighbors["A"] == []
    assert isinstance(interpretations_node["A"], DummyWorld)

# ---- _add_edge tests (with _add_node mocked) ----

class FakeLabel:
    def __init__(self, value: str):
        self.value = value
    def __hash__(self):
        return hash(self.value)
    def __eq__(self, other):
        return isinstance(other, FakeLabel) and self.value == other.value
    def __repr__(self):
        return f"FakeLabel({self.value!r})"

def _shim_typed_list(monkeypatch):
    # Make typed.List(...) -> list(iterable) and .empty_list(...) -> []
    class _ListShim:
        def __call__(self, iterable):
            return list(iterable)
        def empty_list(self, *a, **k):
            return []
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())

def _mock_add_node(monkeypatch):
    # Minimal in-place behavior so _add_edge can proceed,
    # but still fully mockable for call assertions.
    def side_effect(node, neighbors, reverse_neighbors, nodes, interpretations_node):
        if node not in nodes:
            nodes.append(node)
            neighbors.setdefault(node, [])
            reverse_neighbors.setdefault(node, [])
            interpretations_node[node] = "NODE"
    m = Mock(side_effect=side_effect)
    monkeypatch.setattr(interpretation, "_add_node", m)
    return m

class DummyWorld:
    def __init__(self, labels):
        # mirror edge-world: a dict keyed by label
        self.world = {lab: "INIT" for lab in list(labels)}

@pytest.mark.parametrize(
    "label, pred_init, expect_pred, expect_world_keys, expect_new, expect_add_calls",
    [
        # 1) new edge, non-empty label, new predicate bucket
        (FakeLabel("owns"), {}, [("A","B")], {"owns"}, True, 2),
        # 2) new edge, non-empty label, existing predicate bucket (append)
        (FakeLabel("owns"), {FakeLabel("owns"): [("X","Y")]}, [("X","Y"), ("A","B")], {"owns"}, True, 2),
        # 3) new edge, empty label (unlabeled)
        (FakeLabel(""), {}, None, set(), True, 2),
    ]
)
def test_add_edge_new_edge_variants(
    monkeypatch, label, pred_init, expect_pred, expect_world_keys, expect_new, expect_add_calls
):
    _shim_typed_list(monkeypatch)
    monkeypatch.setattr(interpretation.world, "World", DummyWorld)
    mock_add = _mock_add_node(monkeypatch)

    neighbors, reverse_neighbors = {}, {}
    nodes, edges = [], []
    interpretations_node, interpretations_edge = {}, {}
    predicate_map = dict(pred_init)  # copy
    t = 0

    edge, new_edge = add_edge(
        "A", "B",
        neighbors, reverse_neighbors, nodes, edges,
        label, interpretations_node, interpretations_edge, predicate_map, t
    )

    assert edge == ("A","B")
    assert new_edge is expect_new
    assert mock_add.call_count == expect_add_calls
    assert neighbors["A"] == ["B"]
    assert reverse_neighbors["B"] == ["A"]

    # world contents
    world_keys = {lbl.value for lbl in interpretations_edge[("A","B")].world.keys()}
    assert world_keys == expect_world_keys

    # predicate_map effects
    if label.value == "":
        assert predicate_map == {}
    else:
        assert predicate_map[label] == expect_pred

@pytest.mark.parametrize(
    "initial_world_labels, pred_init, expect_pred, expect_new, label_value",
    [
        # 4) existing edge gains a new (missing) label -> create predicate bucket
        ([], {}, [("A","B")], True, "owns"),
        # 5) existing edge gains a new label -> append to existing predicate bucket
        ([], {FakeLabel("owns"): [("X","Y")]}, [("X","Y"), ("A","B")], True, "owns"),
        # 6) existing edge called again with same label -> no-op
        ([FakeLabel("owns")], {FakeLabel("owns"): [("A","B")]}, [("A","B")], False, "owns"),
    ]
)
def test_add_edge_existing_edge_variants(
    monkeypatch, initial_world_labels, pred_init, expect_pred, expect_new, label_value
):
    _shim_typed_list(monkeypatch)
    monkeypatch.setattr(interpretation.world, "World", DummyWorld)
    # interval only matters when adding a new label in this branch
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: ("closed", lo, up))
    mock_add = _mock_add_node(monkeypatch)  # should NOT be called; nodes pre-exist

    # pre-existing graph
    neighbors = {"A": ["B"]}
    reverse_neighbors = {"B": ["A"]}
    nodes = ["A","B"]
    edges = [("A","B")]
    interpretations_node = {"A":"NODE","B":"NODE"}
    interpretations_edge = {("A","B"): DummyWorld(initial_world_labels)}
    predicate_map = dict(pred_init)
    t = 0
    l = FakeLabel(label_value)

    edge, new_edge = add_edge(
        "A", "B",
        neighbors, reverse_neighbors, nodes, edges,
        l, interpretations_node, interpretations_edge, predicate_map, t
    )

    assert edge == ("A","B")
    assert new_edge is expect_new
    mock_add.assert_not_called()  # nodes already present
    assert neighbors["A"] == ["B"] and reverse_neighbors["B"] == ["A"]

    # world & predicate_map outcomes
    if expect_new:  # new label added → interval set
        assert interpretations_edge[("A","B")].world[l] == ("closed", 0, 1)
    assert predicate_map[l] == expect_pred

# ---- _ground_rule tests (with _add_node mocked) ----

class DummyRule:
    def __init__(self, rtype, head_vars, clauses, thresholds, ann_fn, rule_edges):
        self._rtype = rtype
        self._head_vars = head_vars
        self._clauses = clauses
        self._thresholds = thresholds
        self._ann_fn = ann_fn
        self._rule_edges = rule_edges
    def get_type(self): return self._rtype
    def get_head_variables(self): return self._head_vars
    def get_clauses(self): return self._clauses
    def get_thresholds(self): return self._thresholds
    def get_annotation_function(self): return self._ann_fn
    def get_edges(self): return self._rule_edges

def _shim_typed_list(monkeypatch):
    class _ListShim:
        def __call__(self, iterable): return list(iterable)
        def empty_list(self, *a, **k): return []
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())

def test_ground_rule_node_early_fail_breaks_and_returns_empty(monkeypatch):
    _shim_typed_list(monkeypatch)

    # Mocks for node clause processing
    monkeypatch.setattr(interpretation, "get_rule_node_clause_grounding", lambda *a, **k: ["n1", "n2"])
    monkeypatch.setattr(interpretation, "get_qualified_node_groundings", lambda *a, **k: ["n1"])
    mock_check = Mock(return_value=False)  # threshold fails
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", mock_check)

    mock_refine = Mock()  # should NOT be called
    monkeypatch.setattr(interpretation, "refine_groundings", mock_refine)

    rule = DummyRule(
        rtype="node",
        head_vars=("H",),
        clauses=[("node", "L", ("X",), ("bnd",), "op")],
        thresholds=[("ge", ("number","total"), 1)],
        ann_fn="",
        rule_edges=("","","HEAD")  # unused for node head except [-1]
    )

    # bare graph/structures
    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node, interpretations_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=False, allow_ground_rules=False, t=0
    )

    assert apps_node == []
    assert apps_edge == []
    mock_refine.assert_not_called()
    mock_check.assert_called_once()

def test_ground_rule_node_success_adds_head_node_and_collects_trace_ann(monkeypatch):
    _shim_typed_list(monkeypatch)

    # Variable-aware grounding: X -> ["x1"]
    def mock_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, clause_label, nodes):
        assert clause_var_1 == "X"
        return ["x1"]
    monkeypatch.setattr(interpretation, "get_rule_node_clause_grounding", mock_rule_node_clause_grounding)

    # Pass-through qualification: keep whatever grounding we provide
    monkeypatch.setattr(
        interpretation,
        "get_qualified_node_groundings",
        lambda interpretations_node, grounding, clause_label, clause_bnd: list(grounding),
    )

    # Thresholds ok; refine is a no-op; final re-check ok
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    # We want _add_node called for head 'H' (not in nodes and not pre-grounded)
    mock_add_node = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)

    class DummyNW:
        def __init__(self, d): self.world = d

    # Ensure x1 has L1 for annotation
    interpretations_node = {
        "x1": DummyNW({"L1": "ANN_x1"}),
    }

    rule = DummyRule(
        rtype="node",
        head_vars=("H",),
        # Only a node clause on X (≠ head) so groundings doesn't get a key for "H"
        clauses=[
            ("node", "L1", ("X",), ("b",), "op"),
        ],
        thresholds=[("ge",("number","total"),1)],
        ann_fn="some_fn",
        rule_edges=("","","HEAD_LBL"),
    )

    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_edge = {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=False, t=0
    )

    # One applicable rule instance for node head
    assert len(apps_node) == 1 and apps_edge == []
    head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_add = apps_node[0]

    assert head_grounding == "H"
    # _add_node called to materialize head node (ground rule)
    mock_add_node.assert_called_once()

    # Trace/ann collections exist for 1 clause
    assert len(annotations) == 1
    assert len(qualified_nodes) == 1
    assert len(qualified_edges) == 1

    # For the non-head clause, annotation should include x1’s value
    assert annotations[0] == ["ANN_x1"]  # order/shape from the code path
    # edges_to_add’s label (3rd element) equals rule_edges[-1]
    assert edges_to_add[2] == "HEAD_LBL"


def test_ground_rule_edge_infer_adds_nodes_and_unlabeled_edge(monkeypatch):
    _shim_typed_list(monkeypatch)

    # No body clauses -> satisfaction stays True
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    # Add head nodes and unlabeled edge via mocks
    mock_add_node = Mock()
    mock_add_edge = Mock(return_value=(("S","T"), True))
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    rule = DummyRule(
        rtype="edge",
        head_vars=("S","T"),
        clauses=[],                # no clauses
        thresholds=[],
        ann_fn="",                 # no annotations
        rule_edges=("src","tgt","HEAD_LBL"),  # non-empty src/tgt => infer_edges=True
    )

    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node, interpretations_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=False, allow_ground_rules=False, t=0
    )

    # One applicable edge instance
    assert apps_node == []
    assert len(apps_edge) == 1
    (e, annotations, qn, qe, edges_to_add) = apps_edge[0]
    assert e == ("S","T")

    # infer_edges → edges_to_add lists get S and T
    assert edges_to_add[0] == ["S"]
    assert edges_to_add[1] == ["T"]
    assert edges_to_add[2] == "HEAD_LBL"

    # Head nodes added; unlabeled edge added once
    assert mock_add_node.call_count == 2
    mock_add_edge.assert_called_once()

def test_ground_rule_edge_existing_edge_with_body_clause_trace_and_ann(monkeypatch):
    _shim_typed_list(monkeypatch)

    # Body: edge clause on variables (X,Y) → returns qualified edge (A,B)
    monkeypatch.setattr(
        interpretation, "get_rule_edge_clause_grounding",
        lambda *a, **k: [("A","B")]
    )
    monkeypatch.setattr(
        interpretation, "get_qualified_edge_groundings",
        lambda *a, **k: [("A","B")]
    )
    monkeypatch.setattr(
        interpretation, "check_edge_grounding_threshold_satisfaction",
        lambda *a, **k: True
    )
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    # Edge interpretations for annotations
    class DummyEW:
        def __init__(self, d): self.world = d
    interpretations_edge = {("A","B"): DummyEW({"L": "EANN"})}

    rule = DummyRule(
        rtype="edge",
        head_vars=("X","Y"),           # variables
        clauses=[("edge","L",("X","Y"),("b",),"op")],
        thresholds=[("ge",("number","total"),1)],
        ann_fn="fn",                   # collect annotations
        rule_edges=("", "", "HEADLBL") # empty src/tgt => infer_edges=False
    )

    # Graph already has the concrete edge; head vars will be grounded by the body
    nodes = ["A","B"]
    edges = [("A","B")]
    neighbors, reverse_neighbors = {"A": ["B"]}, {"B": ["A"]}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node = {}

    # Add/edge shouldn’t be called in this path
    monkeypatch.setattr(interpretation, "_add_node", Mock())
    monkeypatch.setattr(interpretation, "_add_edge", Mock())

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=True,   # head vars in nodes? (they’re variables, but allow won’t force anything here)
        t=0
    )

    # One applicable instance using existing edge
    assert apps_node == []
    assert len(apps_edge) == 1
    (e, annotations, qn, qe, edges_to_add) = apps_edge[0]

    # The head grounding should be the concrete edge
    assert e == ("A","B")

    # Because infer_edges=False, edges_to_add stays empty lists
    assert edges_to_add[0] == []
    assert edges_to_add[1] == []
    assert edges_to_add[2] == "HEADLBL"

    # With atom_trace=True and both vars equal to head vars, we trace the single edge
    assert len(qn) == 1 and len(qe) == 1
    assert qe[0] == [("A","B")]  # traced edges for the clause

    # Annotation pulled from interpretations_edge[(A,B)].world["L"]
    assert len(annotations) == 1
    assert annotations[0] == ["EANN"]

def test_ground_rule_node_edge_clause_trace_and_ann_three_cases(monkeypatch):
    _shim_typed_list(monkeypatch)

    # Three edge lists: (1) cv1==head, (2) cv2==head, (3) none==head
    c1_edges = [("H", "z1"), ("H", "z2"), ("X", "Y")]   # for (H, Z) -> filter e[0] == "H"
    c2_edges = [("x1", "H"), ("x2", "H")]               # for (Z, H) -> filter e[1] == "H"
    c3_edges = [("a1", "b1"), ("a2", "b2")]             # for (A, B) -> keep all

    # Variable-aware grounding for edge clauses
    def mock_rule_edge_clause_grounding(cv1, cv2, groundings, groundings_edges,
                                        neighbors, reverse_neighbors,
                                        predicate_map_edge, l, edges):
        if (cv1, cv2) == ("H", "Z"):
            return list(c1_edges)
        if (cv1, cv2) == ("Z", "H"):
            return list(c2_edges)
        if (cv1, cv2) == ("A", "B"):
            return list(c3_edges)
        return []

    # Qualification is pass-through; thresholds always satisfied
    monkeypatch.setattr(interpretation, "get_rule_edge_clause_grounding", mock_rule_edge_clause_grounding)
    monkeypatch.setattr(interpretation, "get_qualified_edge_groundings",
                        lambda interpretations_edge, grounding, clause_label, clause_bnd: list(grounding))
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    # Edge interpretations for annotations; each edge only knows its clause label
    class DummyEW:
        def __init__(self, d): self.world = d

    interpretations_edge = {}
    for e in c1_edges:
        interpretations_edge[e] = DummyEW({"L1": f"ANN_{e}_L1"})
    for e in c2_edges:
        interpretations_edge[e] = DummyEW({"L2": f"ANN_{e}_L2"})
    for e in c3_edges:
        interpretations_edge[e] = DummyEW({"L3": f"ANN_{e}_L3"})

    # No node annotations needed for this test
    interpretations_node = {}

    # Node-head rule; 3 EDGE clauses:
    #  - (H,Z) → cv1 == head_var_1  → filter by source == head_grounding
    #  - (Z,H) → cv2 == head_var_1  → filter by target == head_grounding
    #  - (A,B) → none equal         → keep all
    rule = DummyRule(
        rtype="node",
        head_vars=("H",),
        clauses=[
            ("edge", "L1", ("H", "Z"), ("b",), "op"),
            ("edge", "L2", ("Z", "H"), ("b",), "op"),
            ("edge", "L3", ("A", "B"), ("b",), "op"),
        ],
        thresholds=[
            ("ge", ("number", "total"), 1),
            ("ge", ("number", "total"), 1),
            ("ge", ("number", "total"), 1),
        ],
        ann_fn="do_ann",
        rule_edges=("","","HEADLBL"),
    )

    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=False, t=0
    )

    # Node-head: expect exactly one applicable rule instance
    assert len(apps_node) == 1 and apps_edge == []
    head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_add = apps_node[0]
    assert head_grounding == "H"

    # We have 3 edge clauses → 3 entries added for both trace and annotations
    assert len(qualified_nodes) == 3
    assert len(qualified_edges) == 3
    assert len(annotations) == 3

    # --- Clause 1: (H, Z) → filter edges with source == "H"
    assert qualified_nodes[0] == []  # edge clause adds empty node list
    assert qualified_edges[0] == [("H","z1"), ("H","z2")]  # ("X","Y") filtered out
    assert annotations[0] == [
        interpretations_edge[("H","z1")].world["L1"],
        interpretations_edge[("H","z2")].world["L1"],
    ]

    # --- Clause 2: (Z, H) → filter edges with target == "H"
    assert qualified_nodes[1] == []
    assert qualified_edges[1] == [("x1","H"), ("x2","H")]
    assert annotations[1] == [
        interpretations_edge[("x1","H")].world["L2"],
        interpretations_edge[("x2","H")].world["L2"],
    ]

    # --- Clause 3: (A, B) → none equal → include all edges
    assert qualified_nodes[2] == []
    assert qualified_edges[2] == [("a1","b1"), ("a2","b2")]
    assert annotations[2] == [
        interpretations_edge[("a1","b1")].world["L3"],
        interpretations_edge[("a2","b2")].world["L3"],
    ]

    # Node-head: edges_to_add just carries the head label
    assert edges_to_add[2] == "HEADLBL"
def test_ground_rule_edge_head_edge_clause_all_matching_cases(monkeypatch):
    _shim_typed_list(monkeypatch)

    hv1, hv2 = "H1", "H2"

    # Patch graph mutations to avoid real label/interval/world internals
    mock_add_node = Mock()
    mock_add_edge = Mock(return_value=((hv1, hv2), True))
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    # Constrain pools so groundings[H1]==["H1"], groundings[H2]==["H2"]
    c_both_eq       = [(hv1, hv2)]
    c_both_swapped  = [(hv2, hv1)]
    c_cv1_hv1       = [(hv1, "Z1"), (hv1, "Z2")]
    c_cv1_hv2       = [(hv2, "Z9")]
    c_cv2_hv1       = [("Z0", hv1)]
    c_cv2_hv2       = [("P", hv2)]
    c_none_equal    = [("a","b"), ("c","d")]

    def mock_rule_edge_clause_grounding(cv1, cv2, *_):
        key = (cv1, cv2)
        return {
            (hv1, hv2): c_both_eq,
            (hv2, hv1): c_both_swapped,
            (hv1, "Z"): c_cv1_hv1,
            (hv2, "Z"): c_cv1_hv2,
            ("Z", hv1): c_cv2_hv1,
            ("Z", hv2): c_cv2_hv2,
            ("A", "B"): c_none_equal,
        }.get(key, [])

    monkeypatch.setattr(interpretation, "get_rule_edge_clause_grounding", mock_rule_edge_clause_grounding)
    monkeypatch.setattr(interpretation, "get_qualified_edge_groundings", lambda *_: list(_[1]))
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    class DummyEW:
        def __init__(self, d): self.world = d

    interpretations_edge = {}
    def add_label(edges, lbl):
        for e in edges:
            interpretations_edge[e] = DummyEW({lbl: f"ANN_{e}_{lbl}"})

    add_label(c_both_eq, "LA")
    add_label(c_both_swapped, "LB")
    add_label(c_cv1_hv1, "LC")
    add_label(c_cv1_hv2, "LD")
    add_label(c_cv2_hv1, "LE")
    add_label(c_cv2_hv2, "LF")
    add_label(c_none_equal, "LG")

    interpretations_node = {}

    rule = DummyRule(
        rtype="edge",
        head_vars=(hv1, hv2),
        clauses=[
            ("edge", "LA", (hv1, hv2), ("b",), "op"),
            ("edge", "LB", (hv2, hv1), ("b",), "op"),
            ("edge", "LC", (hv1, "Z"), ("b",), "op"),
            ("edge", "LD", (hv2, "Z"), ("b",), "op"),
            ("edge", "LE", ("Z", hv1), ("b",), "op"),
            ("edge", "LF", ("Z", hv2), ("b",), "op"),
            ("edge", "LG", ("A", "B"), ("b",), "op"),
        ],
        thresholds=[("ge", ("number","total"), 1)] * 7,
        ann_fn="collect_annotations",
        rule_edges=("src","tgt","HEADLBL"),  # infer=True
    )

    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=False, t=0
    )

    # Exactly one head pair (H1,H2) → one applicable edge
    assert apps_node == []
    assert len(apps_edge) == 1
    (e, annotations, qn, qe, edges_to_add) = apps_edge[0]
    assert e == (hv1, hv2)

    # 7 clauses → 7 entries
    assert len(qn) == len(qe) == len(annotations) == 7
    assert all(q == [] for q in qn)

    # 1) both equal
    assert qe[0] == [(hv1, hv2)]
    assert annotations[0] == [interpretations_edge[(hv1, hv2)].world["LA"]]
    # 2) both swapped
    assert qe[1] == [(hv2, hv1)]
    assert annotations[1] == [interpretations_edge[(hv2, hv1)].world["LB"]]
    # 3) cv1 == hv1
    assert qe[2] == [(hv1, "Z1"), (hv1, "Z2")]
    assert annotations[2] == [
        interpretations_edge[(hv1, "Z1")].world["LC"],
        interpretations_edge[(hv1, "Z2")].world["LC"],
    ]
    # 4) cv1 == hv2
    assert qe[3] == [(hv2, "Z9")]
    assert annotations[3] == [interpretations_edge[(hv2, "Z9")].world["LD"]]
    # 5) cv2 == hv1
    assert qe[4] == [("Z0", hv1)]
    assert annotations[4] == [interpretations_edge[("Z0", hv1)].world["LE"]]
    # 6) cv2 == hv2
    assert qe[5] == [("P", hv2)]
    assert annotations[5] == [interpretations_edge[("P", hv2)].world["LF"]]
    # 7) none equal
    assert qe[6] == [("a","b"), ("c","d")]
    assert annotations[6] == [
        interpretations_edge[("a","b")].world["LG"],
        interpretations_edge[("c","d")].world["LG"],
    ]

    # infer mode → head pair queued for addition
    assert edges_to_add[0] == [hv1]
    assert edges_to_add[1] == [hv2]
    assert edges_to_add[2] == "HEADLBL"

    # No requirement on _add_node here (groundings already had H1/H2 due to body clauses)
    mock_add_edge.assert_called_once()


def test_ground_rule_node_clause_ground_atom_allow_ground_rules(monkeypatch):
    _shim_typed_list(monkeypatch)

    mock_rule_node = Mock()
    monkeypatch.setattr(interpretation, "get_rule_node_clause_grounding", mock_rule_node)
    monkeypatch.setattr(interpretation, "get_qualified_node_groundings", lambda *a, **k: ["A"])
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    mock_add_node = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)

    class DummyNW:
        def __init__(self, d):
            self.world = d

    interpretations_node = {"A": DummyNW({"L": "ANN_A"})}
    interpretations_edge = {}

    rule = DummyRule(
        rtype="node",
        head_vars=("A",),
        clauses=[("node", "L", ("A",), ("b",), "op")],
        thresholds=[("ge", ("number", "total"), 1)],
        ann_fn="fn",
        rule_edges=("", "", "HEADLBL"),
    )

    nodes = ["A"]
    edges = []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=True, t=0,
    )

    assert apps_edge == []
    assert len(apps_node) == 1
    head_grounding, annotations, qn, qe, edges_to_add = apps_node[0]
    assert head_grounding == "A"
    assert qn[0] == ["A"]
    assert annotations[0] == ["ANN_A"]
    mock_rule_node.assert_not_called()
    mock_add_node.assert_not_called()


def test_ground_rule_edge_clause_ground_atom_allow_ground_rules(monkeypatch):
    _shim_typed_list(monkeypatch)

    mock_rule_edge = Mock()
    monkeypatch.setattr(interpretation, "get_rule_edge_clause_grounding", mock_rule_edge)
    monkeypatch.setattr(interpretation, "get_qualified_edge_groundings", lambda *a, **k: [("A", "B")])
    monkeypatch.setattr(interpretation, "check_edge_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    mock_add_node = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)

    rule = DummyRule(
        rtype="node",
        head_vars=("H",),
        clauses=[("edge", "L", ("A", "B"), ("b",), "op")],
        thresholds=[("ge", ("number", "total"), 1)],
        ann_fn="",
        rule_edges=("", "", "HEADLBL"),
    )

    nodes = ["A", "B"]
    edges = [("A", "B")]
    neighbors = {"A": ["B"]}
    reverse_neighbors = {"B": ["A"]}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node, interpretations_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=False, allow_ground_rules=True, t=0,
    )

    assert len(apps_node) == 1 and apps_edge == []
    mock_rule_edge.assert_not_called()
    mock_add_node.assert_called_once()


def test_ground_rule_edge_head_vars_use_existing_nodes_when_allowed(monkeypatch):
    _shim_typed_list(monkeypatch)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    mock_add_node = Mock()
    mock_add_edge = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    rule = DummyRule(
        rtype="edge",
        head_vars=("A", "B"),
        clauses=[],
        thresholds=[],
        ann_fn="",
        rule_edges=("", "", "HEADLBL"),
    )

    nodes = ["A", "B"]
    edges = [("A", "B")]
    neighbors = {"A": ["B"]}
    reverse_neighbors = {"B": ["A"]}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node, interpretations_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule,
        interpretations_node,
        interpretations_edge,
        predicate_map_node,
        predicate_map_edge,
        nodes,
        edges,
        neighbors,
        reverse_neighbors,
        atom_trace=False,
        allow_ground_rules=True,
        t=0,
    )

    assert apps_node == []
    assert len(apps_edge) == 1
    e, annotations, qn, qe, edges_to_add = apps_edge[0]
    assert e == ("A", "B")
    assert annotations == []
    assert qn == []
    assert qe == []
    assert edges_to_add == ([], [], "HEADLBL")
    mock_add_node.assert_not_called()
    mock_add_edge.assert_not_called()


def test_ground_rule_node_clause_filters_edge_groundings(monkeypatch):
    _shim_typed_list(monkeypatch)
    mock_add_node = _mock_add_node(monkeypatch)

    edges_xy = [("n1", "nY"), ("n2", "nY")]
    edges_zx = [("nZ", "n1"), ("nZ", "n3")]

    def mock_rule_edge_clause_grounding(cv1, cv2, *args):
        if (cv1, cv2) == ("X", "Y"):
            return list(edges_xy)
        if (cv1, cv2) == ("Z", "X"):
            return list(edges_zx)
        return []

    monkeypatch.setattr(
        interpretation,
        "get_rule_edge_clause_grounding",
        mock_rule_edge_clause_grounding,
    )
    monkeypatch.setattr(
        interpretation,
        "get_qualified_edge_groundings",
        lambda *a, **k: list(a[1]),
    )
    monkeypatch.setattr(
        interpretation,
        "check_edge_grounding_threshold_satisfaction",
        lambda *a, **k: True,
    )

    monkeypatch.setattr(
        interpretation,
        "get_rule_node_clause_grounding",
        lambda *a, **k: ["n1", "n2", "n3"],
    )
    monkeypatch.setattr(
        interpretation,
        "get_qualified_node_groundings",
        lambda *a, **k: ["n1"],
    )
    monkeypatch.setattr(
        interpretation,
        "check_node_grounding_threshold_satisfaction",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)

    def assert_filtered_edges(*args):
        groundings_edges = args[5]
        assert groundings_edges[("X", "Y")] == [("n1", "nY")]
        assert groundings_edges[("Z", "X")] == [("nZ", "n1")]
        return True

    monkeypatch.setattr(
        interpretation,
        "check_all_clause_satisfaction",
        assert_filtered_edges,
    )

    rule = DummyRule(
        rtype="node",
        head_vars=("X",),
        clauses=[
            ("edge", "L1", ("X", "Y"), ("b",), "op"),
            ("edge", "L2", ("Z", "X"), ("b",), "op"),
            ("node", "L3", ("X",), ("b",), "op"),
        ],
        thresholds=[("ge", ("number", "total"), 1)] * 3,
        ann_fn="",
        rule_edges=("", "", "HEADLBL"),
    )

    nodes = ["n1", "n2", "n3", "nY", "nZ"]
    edges = []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}
    interpretations_node, interpretations_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule,
        interpretations_node,
        interpretations_edge,
        predicate_map_node,
        predicate_map_edge,
        nodes,
        edges,
        neighbors,
        reverse_neighbors,
        atom_trace=False,
        allow_ground_rules=False,
        t=0,
    )

    assert len(apps_node) == 1 and apps_edge == []
    mock_add_node.assert_not_called()


def test_ground_rule_edge_with_node_clauses_tracing(monkeypatch):
    _shim_typed_list(monkeypatch)

    hv1, hv2 = "H1", "H2"

    def mock_rule_node_clause_grounding(cv1, *args):
        return {"H1": ["a1"], "H2": ["b1"], "Z": ["z1"]}[cv1]

    monkeypatch.setattr(interpretation, "get_rule_node_clause_grounding", mock_rule_node_clause_grounding)
    monkeypatch.setattr(interpretation, "get_qualified_node_groundings", lambda *a, **k: list(a[1]))
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    mock_add_node = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)

    class DummyNW:
        def __init__(self, d):
            self.world = d

    interpretations_node = {
        "a1": DummyNW({"L1": "ANN_a1"}),
        "b1": DummyNW({"L2": "ANN_b1"}),
        "z1": DummyNW({"L3": "ANN_z1"}),
    }
    interpretations_edge = {}

    rule = DummyRule(
        rtype="edge",
        head_vars=(hv1, hv2),
        clauses=[
            ("node", "L1", (hv1,), ("b",), "op"),
            ("node", "L2", (hv2,), ("b",), "op"),
            ("node", "L3", ("Z",), ("b",), "op"),
        ],
        thresholds=[("ge", ("number", "total"), 1)] * 3,
        ann_fn="fn",
        rule_edges=("", "", "HEADLBL"),
    )

    nodes = ["a1", "b1", "z1"]
    edges = [("a1", "b1")]
    neighbors = {"a1": ["b1"]}
    reverse_neighbors = {"b1": ["a1"]}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=True, allow_ground_rules=False, t=0,
    )

    assert apps_node == []
    assert len(apps_edge) == 1
    (e, annotations, qn, qe, edges_to_add) = apps_edge[0]
    assert e == ("a1", "b1")
    assert qn[0] == ["a1"]
    assert qn[1] == ["b1"]
    assert qn[2] == ["z1"]
    assert annotations[0] == ["ANN_a1"]
    assert annotations[1] == ["ANN_b1"]
    assert annotations[2] == ["ANN_z1"]
    mock_add_node.assert_not_called()


def test_ground_rule_edge_infer_self_loop_prevents_output(monkeypatch):
    _shim_typed_list(monkeypatch)

    hv1, hv2 = "X", "Y"

    monkeypatch.setattr(interpretation, "get_rule_node_clause_grounding", lambda *a, **k: ["A"])
    monkeypatch.setattr(interpretation, "get_qualified_node_groundings", lambda *a, **k: ["A"])
    monkeypatch.setattr(interpretation, "check_node_grounding_threshold_satisfaction", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "refine_groundings", lambda *a, **k: None)
    monkeypatch.setattr(interpretation, "check_all_clause_satisfaction", lambda *a, **k: True)

    mock_add_node = Mock()
    mock_add_edge = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    class DummyNW:
        def __init__(self, d):
            self.world = d

    interpretations_node = {"A": DummyNW({"L": "ann"})}
    interpretations_edge = {}

    rule = DummyRule(
        rtype="edge",
        head_vars=(hv1, hv2),
        clauses=[
            ("node", "L", (hv1,), ("b",), "op"),
            ("node", "L", (hv2,), ("b",), "op"),
        ],
        thresholds=[("ge", ("number", "total"), 1)] * 2,
        ann_fn="",
        rule_edges=("src", "tgt", "HEADLBL"),
    )

    nodes = ["A"]
    edges = []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule, interpretations_node, interpretations_edge,
        predicate_map_node, predicate_map_edge,
        nodes, edges, neighbors, reverse_neighbors,
        atom_trace=False, allow_ground_rules=False, t=0,
    )

    assert apps_node == []
    assert apps_edge == []
    mock_add_edge.assert_not_called()
    mock_add_node.assert_not_called()


def test_ground_rule_node_recheck_failure_skips_body(monkeypatch):
    _shim_typed_list(monkeypatch)

    monkeypatch.setattr(
        interpretation,
        "get_rule_node_clause_grounding",
        lambda *a, **k: ["x1"],
    )
    monkeypatch.setattr(
        interpretation,
        "get_qualified_node_groundings",
        lambda *a, **k: ["x1"],
    )
    monkeypatch.setattr(
        interpretation,
        "check_node_grounding_threshold_satisfaction",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        interpretation,
        "refine_groundings",
        lambda *a, **k: None,
    )

    mock_check_all = Mock(return_value=False)
    monkeypatch.setattr(
        interpretation,
        "check_all_clause_satisfaction",
        mock_check_all,
    )

    mock_add_node = Mock()
    mock_add_edge = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    rule = DummyRule(
        rtype="node",
        head_vars=("X",),
        clauses=[("node", "L1", ("X",), ("b",), "op")],
        thresholds=[("ge", ("number", "total"), 1)],
        ann_fn="ann_fn",
        rule_edges=("", "", "HEADLBL"),
    )

    interpretations_node, interpretations_edge = {}, {}
    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule,
        interpretations_node,
        interpretations_edge,
        predicate_map_node,
        predicate_map_edge,
        nodes,
        edges,
        neighbors,
        reverse_neighbors,
        atom_trace=True,
        allow_ground_rules=False,
        t=0,
    )

    assert apps_node == []
    assert apps_edge == []
    mock_check_all.assert_called_once()
    mock_add_node.assert_not_called()
    mock_add_edge.assert_not_called()


# ---- reason function tests ----


@pytest.fixture
def reason_env(monkeypatch):
    """Minimal environment to exercise Interpretation.reason."""

    # Provide lightweight stand-ins for numba typed containers
    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    class _DictShim:
        def empty(self, *args, **kwargs):
            return {}

    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.typed, "Dict", _DictShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    # Simple world/interval representations
    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class SimpleInterval:
        def __init__(self, val=1.0, static=False):
            self.val = val
            self._static = static

        def copy(self):
            return SimpleInterval(self.val, self._static)

        def is_static(self):
            return self._static

    node = "n1"
    lbl = label.Label("L")
    bnd = SimpleInterval()

    env = {
        "interpretations_node": {0: {node: SimpleWorld()}},
        "interpretations_edge": {0: {}},
        "predicate_map_node": {},
        "predicate_map_edge": {},
        "tmax": 0,
        "prev_reasoning_data": [0, 0],
        "rules": [],
        "nodes": [node],
        "edges": [],
        "neighbors": {node: []},
        "reverse_neighbors": {node: []},
        "rules_to_be_applied_node": [],
        "rules_to_be_applied_edge": [],
        "edges_to_be_added_node_rule": [],
        "edges_to_be_added_edge_rule": [],
        "rules_to_be_applied_node_trace": [],
        "rules_to_be_applied_edge_trace": [],
        "facts_to_be_applied_node": [(0, node, lbl, bnd, False, False)],
        "facts_to_be_applied_edge": [],
        "facts_to_be_applied_node_trace": [],
        "facts_to_be_applied_edge_trace": [],
        "ipl": [],
        "rule_trace_node": [],
        "rule_trace_edge": [],
        "rule_trace_node_atoms": [],
        "rule_trace_edge_atoms": [],
        "reverse_graph": {},
        "atom_trace": False,
        "save_graph_attributes_to_rule_trace": False,
        "persistent": False,
        "inconsistency_check": False,
        "store_interpretation_changes": False,
        "update_mode": "",
        "allow_ground_rules": True,
        "max_facts_time": 0,
        "annotation_functions": {},
        "convergence_mode": "perfect_convergence",
        "convergence_delta": 0,
        "verbose": False,
        "again": False,
    }

    def run(**overrides):
        params = env.copy()
        params.update(overrides)
        return reason(
            params["interpretations_node"],
            params["interpretations_edge"],
            params["predicate_map_node"],
            params["predicate_map_edge"],
            params["tmax"],
            params["prev_reasoning_data"],
            params["rules"],
            params["nodes"],
            params["edges"],
            params["neighbors"],
            params["reverse_neighbors"],
            params["rules_to_be_applied_node"],
            params["rules_to_be_applied_edge"],
            params["edges_to_be_added_node_rule"],
            params["edges_to_be_added_edge_rule"],
            params["rules_to_be_applied_node_trace"],
            params["rules_to_be_applied_edge_trace"],
            params["facts_to_be_applied_node"],
            params["facts_to_be_applied_edge"],
            params["facts_to_be_applied_node_trace"],
            params["facts_to_be_applied_edge_trace"],
            params["ipl"],
            params["rule_trace_node"],
            params["rule_trace_edge"],
            params["rule_trace_node_atoms"],
            params["rule_trace_edge_atoms"],
            params["reverse_graph"],
            params["atom_trace"],
            params["save_graph_attributes_to_rule_trace"],
            params["persistent"],
            params["inconsistency_check"],
            params["store_interpretation_changes"],
            params["update_mode"],
            params["allow_ground_rules"],
            params["max_facts_time"],
            params["annotation_functions"],
            params["convergence_mode"],
            params["convergence_delta"],
            params["verbose"],
            params["again"],
        )

    env["run"] = run
    env["node"] = node
    env["label"] = lbl
    env["bnd"] = bnd
    return env


def test_reason_applies_node_fact(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 1

    mock_update = Mock(side_effect=_updater)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    fp, max_t = reason_env["run"]()

    assert fp == 1 and max_t == 1
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs.get("override", False) is False
    assert reason_env["interpretations_node"][0][reason_env["node"]].world[reason_env["label"]] is reason_env["bnd"]


def test_reason_resolves_inconsistency(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)
    mock_resolve = Mock()
    monkeypatch.setattr(interpretation, "resolve_inconsistency_node", mock_resolve)
    monkeypatch.setattr(interpretation, "_update_node", Mock(return_value=(True, 1)))

    reason_env["run"](inconsistency_check=True)

    mock_resolve.assert_called_once()
    interpretation._update_node.assert_not_called()


def test_reason_overrides_without_inconsistency(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["run"](inconsistency_check=False)

    assert mock_update.call_args.kwargs.get("override") is True


@pytest.mark.parametrize(
    "mode,delta,change,expected_fp",
    [
        ("delta_interpretation", 1, 1, 0),
        ("delta_interpretation", 0, 1, 1),
        ("delta_bound", 0.5, 0.5, 0),
        ("delta_bound", 0, 0.5, 1),
    ],
)
def test_reason_convergence_modes(monkeypatch, reason_env, mode, delta, change, expected_fp):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, change

    monkeypatch.setattr(interpretation, "_update_node", _updater)

    fp, max_t = reason_env["run"](convergence_mode=mode, convergence_delta=delta)

    assert fp == expected_fp and max_t == 1


def make_copy_env(monkeypatch, persistent):
    """Build a minimal environment starting from t=1 to test persistence copying."""

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *a, **k):
            return []

    class _DictShim:
        def empty(self, *a, **k):
            return {}

    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.typed, "Dict", _DictShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    class SimpleWorld:
        def __init__(self, *a, **k):
            self.world = {}

    monkeypatch.setattr(interpretation.world, "World", SimpleWorld)

    class SimpleInterval:
        def __init__(self, static=False):
            self._static = static

        def copy(self):
            return SimpleInterval(self._static)

        def is_static(self):
            return self._static

    n1, n2 = "n1", "n2"
    edge = (n1, n2)
    dyn_lbl = label.Label("dyn")
    stat_lbl = label.Label("stat")

    node_w0 = SimpleWorld()
    node_w0.world[dyn_lbl] = SimpleInterval()
    node_w0.world[stat_lbl] = SimpleInterval(static=True)

    edge_w0 = SimpleWorld()
    edge_w0.world[dyn_lbl] = SimpleInterval()
    edge_w0.world[stat_lbl] = SimpleInterval(static=True)

    env = {
        "interpretations_node": {0: {n1: node_w0}},
        "interpretations_edge": {0: {edge: edge_w0}},
        "predicate_map_node": {},
        "predicate_map_edge": {},
        "tmax": 1,
        "prev_reasoning_data": [1, 0],
        "rules": [],
        "nodes": [n1, n2],
        "edges": [edge],
        "neighbors": {n1: [n2], n2: []},
        "reverse_neighbors": {n1: [], n2: [n1]},
        "rules_to_be_applied_node": [],
        "rules_to_be_applied_edge": [],
        "edges_to_be_added_node_rule": [],
        "edges_to_be_added_edge_rule": [],
        "rules_to_be_applied_node_trace": [],
        "rules_to_be_applied_edge_trace": [],
        "facts_to_be_applied_node": [],
        "facts_to_be_applied_edge": [],
        "facts_to_be_applied_node_trace": [],
        "facts_to_be_applied_edge_trace": [],
        "ipl": [],
        "rule_trace_node": [],
        "rule_trace_edge": [],
        "rule_trace_node_atoms": [],
        "rule_trace_edge_atoms": [],
        "reverse_graph": {},
        "atom_trace": False,
        "save_graph_attributes_to_rule_trace": False,
        "persistent": persistent,
        "inconsistency_check": False,
        "store_interpretation_changes": False,
        "update_mode": "",
        "allow_ground_rules": True,
        "max_facts_time": 0,
        "annotation_functions": {},
        "convergence_mode": "perfect_convergence",
        "convergence_delta": 0,
        "verbose": False,
        "again": False,
    }

    def run(**overrides):
        params = env.copy()
        params.update(overrides)
        return reason(
            params["interpretations_node"],
            params["interpretations_edge"],
            params["predicate_map_node"],
            params["predicate_map_edge"],
            params["tmax"],
            params["prev_reasoning_data"],
            params["rules"],
            params["nodes"],
            params["edges"],
            params["neighbors"],
            params["reverse_neighbors"],
            params["rules_to_be_applied_node"],
            params["rules_to_be_applied_edge"],
            params["edges_to_be_added_node_rule"],
            params["edges_to_be_added_edge_rule"],
            params["rules_to_be_applied_node_trace"],
            params["rules_to_be_applied_edge_trace"],
            params["facts_to_be_applied_node"],
            params["facts_to_be_applied_edge"],
            params["facts_to_be_applied_node_trace"],
            params["facts_to_be_applied_edge_trace"],
            params["ipl"],
            params["rule_trace_node"],
            params["rule_trace_edge"],
            params["rule_trace_node_atoms"],
            params["rule_trace_edge_atoms"],
            params["reverse_graph"],
            params["atom_trace"],
            params["save_graph_attributes_to_rule_trace"],
            params["persistent"],
            params["inconsistency_check"],
            params["store_interpretation_changes"],
            params["update_mode"],
            params["allow_ground_rules"],
            params["max_facts_time"],
            params["annotation_functions"],
            params["convergence_mode"],
            params["convergence_delta"],
            params["verbose"],
            params["again"],
        )

    env["run"] = run
    env["node"] = n1
    env["edge"] = edge
    env["dyn_label"] = dyn_lbl
    env["stat_label"] = stat_lbl
    return env


def test_reason_breaks_when_no_update(monkeypatch, reason_env):
    fp, max_t = reason_env["run"](
        facts_to_be_applied_node=[],
        convergence_mode="delta_bound",
        convergence_delta=-1,
    )
    assert fp == 1 and max_t == 1


@pytest.mark.parametrize("persistent", [True, False])
def test_reason_copies_previous_timestep(monkeypatch, persistent):
    env = make_copy_env(monkeypatch, persistent)
    env["run"]()

    expected = {env["stat_label"]} | ({env["dyn_label"]} if persistent else set())

    node_world = env["interpretations_node"][1][env["node"]].world
    edge_world = env["interpretations_edge"][1][env["edge"]].world

    assert set(node_world.keys()) == expected
    assert set(edge_world.keys()) == expected


def test_reason_adds_missing_node(monkeypatch, reason_env):
    new_node = "n2"

    def stub_add_node(node, neighbors, reverse_neighbors, nodes, interp):
        nodes.append(node)
        neighbors[node] = []
        reverse_neighbors[node] = []
        interp[node] = reason_env["interpretations_node"][0][reason_env["node"]].__class__()

    monkeypatch.setattr(interpretation, "_add_node", stub_add_node)
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (False, 0))

    nodes = [reason_env["node"]]
    neighbors = {reason_env["node"]: []}
    reverse = {reason_env["node"]: []}
    interp = {0: {reason_env["node"]: reason_env["interpretations_node"][0][reason_env["node"]]}}
    facts = [(0, new_node, reason_env["label"], reason_env["bnd"], False, False)]

    reason_env["run"](
        nodes=nodes,
        neighbors=neighbors,
        reverse_neighbors=reverse,
        interpretations_node=interp,
        facts_to_be_applied_node=facts,
    )

    assert new_node in nodes and new_node in interp[0] and neighbors[new_node] == []


def test_reason_logs_static_fact(monkeypatch, reason_env):
    node = reason_env["node"]
    label_ = reason_env["label"]
    static_bnd = reason_env["bnd"].__class__(1.0, True)
    reason_env["interpretations_node"][0][node].world[label_] = static_bnd
    new_bnd = reason_env["bnd"].__class__(0.5, False)
    facts = [(0, node, label_, new_bnd, False, False)]
    rule_trace = []

    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    reason_env["run"](
        facts_to_be_applied_node=facts,
        store_interpretation_changes=True,
        rule_trace_node=rule_trace,
        prev_reasoning_data=[0, 1],
    )

    assert rule_trace == [(0, 1, node, label_, new_bnd)]
    assert reason_env["interpretations_node"][0][node].world[label_] is static_bnd


def test_reason_static_fact_traces_and_requeues(reason_env):
    node = reason_env["node"]
    lbl = reason_env["label"]
    other = label.Label("other")
    static_bnd = reason_env["bnd"].__class__(1.0, True)
    other_bnd = reason_env["bnd"].__class__(0.7, False)
    reason_env["interpretations_node"][0][node].world[lbl] = static_bnd
    reason_env["interpretations_node"][0][node].world[other] = other_bnd
    new_bnd = reason_env["bnd"].__class__(0.2, False)
    facts = [(0, node, lbl, new_bnd, True, False)]
    trace = [["x"]]
    rule_trace = []
    rule_trace_atoms = []
    ipl = [(lbl, other)]

    reason_env["run"](
        facts_to_be_applied_node=facts,
        facts_to_be_applied_node_trace=trace,
        rule_trace_node=rule_trace,
        rule_trace_node_atoms=rule_trace_atoms,
        atom_trace=True,
        store_interpretation_changes=True,
        ipl=ipl,
        prev_reasoning_data=[0, 1],
    )

    assert facts == [(1, node, lbl, new_bnd, True, False)]
    assert trace == [["x"]]
    assert rule_trace == [(0, 1, node, lbl, new_bnd), (0, 1, node, other, other_bnd)]
    assert len(rule_trace_atoms) == 2
    assert reason_env["interpretations_node"][0][node].world[lbl] is static_bnd


def test_reason_static_fact_traces_complement_second(reason_env):
    node = reason_env["node"]
    lbl = reason_env["label"]
    other = label.Label("other")
    static_bnd = reason_env["bnd"].__class__(1.0, True)
    other_bnd = reason_env["bnd"].__class__(0.3, False)
    reason_env["interpretations_node"][0][node].world[lbl] = static_bnd
    reason_env["interpretations_node"][0][node].world[other] = other_bnd
    new_bnd = reason_env["bnd"].__class__(0.4, False)
    facts = [(0, node, lbl, new_bnd, True, False)]
    trace = [["z"]]
    rule_trace = []
    rule_trace_atoms = []
    ipl = [(other, lbl)]

    reason_env["run"](
        facts_to_be_applied_node=facts,
        facts_to_be_applied_node_trace=trace,
        rule_trace_node=rule_trace,
        rule_trace_node_atoms=rule_trace_atoms,
        atom_trace=True,
        store_interpretation_changes=True,
        ipl=ipl,
        prev_reasoning_data=[0, 1],
    )

    assert facts == [(1, node, lbl, new_bnd, True, False)]
    assert trace == [["z"]]
    assert rule_trace == [(0, 1, node, lbl, new_bnd), (0, 1, node, other, other_bnd)]
    assert len(rule_trace_atoms) == 2
    assert reason_env["interpretations_node"][0][node].world[lbl] is static_bnd


def test_reason_delta_bound_inconsistent(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 0.5

    monkeypatch.setattr(interpretation, "_update_node", _updater)

    fp, _ = reason_env["run"](
        convergence_mode="delta_bound",
        convergence_delta=0,
    )

    assert fp == 1


def test_reason_defers_future_fact_and_traces(reason_env):
    future_fact = [(1, reason_env["node"], reason_env["label"], reason_env["bnd"], False, False)]
    future_trace = [["t"]]

    reason_env["run"](
        facts_to_be_applied_node=future_fact,
        facts_to_be_applied_node_trace=future_trace,
        atom_trace=True,
    )

    assert future_fact == [(1, reason_env["node"], reason_env["label"], reason_env["bnd"], False, False)]
    assert future_trace == [["t"]]


def test_reason_defers_future_edge_fact_and_traces(reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    edge_world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: edge_world}}
    edges = [edge]
    future_fact = [(1, edge, lbl, bnd, False, False)]
    future_trace = ["edge"]

    reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=future_fact,
        facts_to_be_applied_edge_trace=future_trace,
        facts_to_be_applied_node=[],
        atom_trace=True,
        prev_reasoning_data=[0, 1],
    )

    assert future_fact == [(1, edge, lbl, bnd, False, False)]
    assert future_trace == ["edge"]


def test_reason_applies_edge_fact(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    edge_world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: edge_world}}
    edges = [edge]
    neighbors = {node: []}
    reverse = {node: []}
    facts = [(0, edge, lbl, bnd, False, False)]

    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    called = {}

    def _update_edge_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        called["ok"] = True
        return True, 0

    monkeypatch.setattr(interpretation, "_update_edge", _update_edge_stub)

    reason_env["run"](
        edges=edges,
        neighbors=neighbors,
        reverse_neighbors=reverse,
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=facts,
        facts_to_be_applied_node=[],
        predicate_map_edge={},
        prev_reasoning_data=[0, 1],
    )

    assert called.get("ok")
    assert edge_world.world[lbl] is bnd


def test_reason_adds_missing_edge(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    edges = []
    neighbors = {node: []}
    reverse = {node: []}
    interpretations_edge = {0: {}}
    called = {}

    def fake_add_edge(s, t, nbrs, rev, nodes, edges_list, l, interp_node, interp_edge, pred_map, t_val):
        interp_edge[(s, t)] = reason_env["interpretations_node"][0][node].__class__()
        edges_list.append((s, t))
        called["ok"] = True
        return (s, t), True

    monkeypatch.setattr(interpretation, "_add_edge", fake_add_edge)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    def updater(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0

    monkeypatch.setattr(interpretation, "_update_edge", updater)

    reason_env["run"](
        edges=edges,
        neighbors=neighbors,
        reverse_neighbors=reverse,
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=[(0, edge, lbl, bnd, False, False)],
        facts_to_be_applied_node=[],
        prev_reasoning_data=[0, 1],
    )

    assert called.get("ok")
    assert edge in edges
    assert edge in interpretations_edge[0]


def test_reason_adds_edge_to_interpretation(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    edges = [edge]
    neighbors = {node: []}
    reverse = {node: []}
    interpretations_edge = {0: {}}
    called = {}

    def fake_add_edge_to_interp(edge_comp, interp_edge):
        interp_edge[edge_comp] = reason_env["interpretations_node"][0][node].__class__()
        called["ok"] = True

    monkeypatch.setattr(interpretation, "_add_edge_to_interpretation", fake_add_edge_to_interp)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    def updater(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0

    monkeypatch.setattr(interpretation, "_update_edge", updater)

    reason_env["run"](
        edges=edges,
        neighbors=neighbors,
        reverse_neighbors=reverse,
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=[(0, edge, lbl, bnd, False, False)],
        facts_to_be_applied_node=[],
        prev_reasoning_data=[0, 1],
    )

    assert called.get("ok")
    assert edge in interpretations_edge[0]


@pytest.mark.parametrize(
    "save_attrs, graph_attr, store_changes, expect_trace",
    [
        (True, True, True, True),
        (False, True, True, False),
        (True, True, False, False),
        (False, False, True, True),
    ],
)
def test_reason_static_edge_rule_trace_branches(
    reason_env, save_attrs, graph_attr, store_changes, expect_trace
):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    other = label.Label("other")
    static_bnd = reason_env["bnd"].__class__(1.0, True)
    other_bnd = reason_env["bnd"].__class__(0.5, False)
    world = reason_env["interpretations_node"][0][node].__class__()
    world.world = {lbl: static_bnd, other: other_bnd}
    interpretations_edge = {0: {edge: world}}
    edges = [edge]
    facts = [(0, edge, lbl, reason_env["bnd"], True, graph_attr)]
    rule_trace = []

    reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=facts,
        facts_to_be_applied_node=[],
        rule_trace_edge=rule_trace,
        store_interpretation_changes=store_changes,
        save_graph_attributes_to_rule_trace=save_attrs,
        ipl=[(lbl, other)],
        prev_reasoning_data=[0, 1],
    )

    if expect_trace:
        assert rule_trace == [
            (0, 1, edge, lbl, static_bnd),
            (0, 1, edge, other, other_bnd),
        ]
    else:
        assert rule_trace == []
    assert facts == [(1, edge, lbl, reason_env["bnd"], True, graph_attr)]


def test_reason_static_edge_atom_trace_complements(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    other1 = label.Label("o1")
    other2 = label.Label("o2")
    static_bnd = reason_env["bnd"].__class__(1.0, True)
    o1_bnd = reason_env["bnd"].__class__(0.5, False)
    o2_bnd = reason_env["bnd"].__class__(0.6, False)
    world = reason_env["interpretations_node"][0][node].__class__()
    world.world = {lbl: static_bnd, other1: o1_bnd, other2: o2_bnd}
    interpretations_edge = {0: {edge: world}}
    edges = [edge]
    facts = [(0, edge, lbl, reason_env["bnd"], True, False)]
    facts_trace = ["t"]
    rule_trace = []
    rule_trace_atoms = []
    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_rule_trace", mock_update)

    reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=facts,
        facts_to_be_applied_edge_trace=facts_trace,
        facts_to_be_applied_node=[],
        rule_trace_edge=rule_trace,
        rule_trace_edge_atoms=rule_trace_atoms,
        store_interpretation_changes=True,
        atom_trace=True,
        ipl=[(lbl, other1), (other2, lbl)],
        prev_reasoning_data=[0, 1],
    )

    assert rule_trace == [
        (0, 1, edge, lbl, static_bnd),
        (0, 1, edge, other1, o1_bnd),
        (0, 1, edge, other2, o2_bnd),
    ]
    assert facts == [(1, edge, lbl, reason_env["bnd"], True, False)]
    assert facts_trace == ["t"]
    assert mock_update.call_count == 3
    calls = [
        call(rule_trace_atoms, [], [], reason_env["bnd"], "t"),
        call(rule_trace_atoms, [], [], o1_bnd, "t"),
        call(rule_trace_atoms, [], [], o2_bnd, "t"),
    ]
    mock_update.assert_has_calls(calls)


def test_reason_edge_delta_bound(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: world}}
    edges = [edge]

    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    def _update_edge_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0.5

    monkeypatch.setattr(interpretation, "_update_edge", _update_edge_stub)

    fp, _ = reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=[(0, edge, lbl, bnd, False, False)],
        facts_to_be_applied_node=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
        prev_reasoning_data=[0, 1],
    )

    assert fp == 2


@pytest.mark.parametrize("inconsistency_check", [True, False])
def test_reason_edge_inconsistency_branches(monkeypatch, reason_env, inconsistency_check):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: world}}
    edges = [edge]

    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)
    mock_resolve = Mock()
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "resolve_inconsistency_edge", mock_resolve)
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        facts_to_be_applied_edge=[(0, edge, lbl, bnd, False, False)],
        facts_to_be_applied_node=[],
        inconsistency_check=inconsistency_check,
        prev_reasoning_data=[0, 1],
    )

    if inconsistency_check:
        assert mock_resolve.called
        assert not mock_update.called
    else:
        assert mock_update.called
        assert mock_update.call_args[1]["override"] is True
        assert not mock_resolve.called


# ---- check_consistent_node / check_consistent_edge tests ----

class _Interval:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.static = False
    def copy(self):
        return _Interval(self.lower, self.upper)
    def set_lower_upper(self, lo, up):
        self.lower, self.upper = lo, up
    def set_static(self, val):
        self.static = val

class _World:
    def __init__(self, mapping=None):
        self.world = mapping or {}
    def is_satisfied(self, label, bnd):
        w = self.world[label]
        return not (bnd.lower > w.upper or w.lower > bnd.upper)

@pytest.mark.parametrize("check_fn", [check_consistent_node, check_consistent_edge])
def test_check_consistent_functions(monkeypatch, check_fn):
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: _Interval(lo, up))
    interp = {"c": _World({"p": _Interval(0, 0.5)})}
    assert check_fn(interp, "c", ("p", _Interval(0.4, 0.6))) is True
    assert check_fn(interp, "c", ("p", _Interval(0.6, 0.8))) is False
    interp2 = {"c": _World({})}
    assert check_fn(interp2, "c", ("p", _Interval(0.6, 0.8))) is True


# ---- resolve_inconsistency_node / resolve_inconsistency_edge tests ----

@pytest.mark.parametrize(
    "resolver,comp_key",
    [
        (resolve_inconsistency_node, "n"),
        (resolve_inconsistency_edge, ("s", "t")),
    ],
)
def test_resolve_inconsistency_updates_world_and_trace(monkeypatch, resolver, comp_key):
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: _Interval(lo, up))
    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a: calls.append(a))
    world = _World({"p": _Interval(0, 0.5), "q": _Interval(0, 0.5), "r": _Interval(0, 0.5)})
    interpretations = {comp_key: world}
    ipl = [("p", "q"), ("r", "p")]
    rule_trace = []
    rule_trace_atoms = []
    facts = ["fact"]
    resolver(
        interpretations,
        comp_key,
        ("p", _Interval(0.9, 1.0)),
        ipl,
        1,
        2,
        0,
        True,
        rule_trace,
        rule_trace_atoms,
        [],
        facts,
        True,
        "fact",
    )
    assert world.world["p"].lower == 0 and world.world["p"].upper == 1 and world.world["p"].static
    assert world.world["q"].lower == 0 and world.world["q"].upper == 1 and world.world["q"].static
    assert world.world["r"].lower == 0 and world.world["r"].upper == 1 and world.world["r"].static
    assert len(rule_trace) == 3
    assert len(calls) == 3


# ---- _add_node_to_interpretation / _add_edge_to_interpretation tests ----

def test_add_node_and_edge_to_interpretation(monkeypatch):
    class DummyWorld:
        def __init__(self, labels):
            self.labels = labels
    monkeypatch.setattr(interpretation.world, "World", DummyWorld)
    nodes = {}
    add_node_to_interpretation("A", nodes)
    assert isinstance(nodes["A"], DummyWorld)
    edges = {}
    add_edge_to_interpretation(("A", "B"), edges)
    assert isinstance(edges[("A", "B")], DummyWorld)


# ---- _add_edges tests ----

def test_add_edges_counts_new_edges(monkeypatch):
    def fake_add_edge(src, tgt, neighbors, reverse_neighbors, nodes, edges, l, interp_node, interp_edge, pred, t):
        edge = (src, tgt)
        new_edge = edge not in edges
        if new_edge:
            edges.append(edge)
        return edge, new_edge
    monkeypatch.setattr(interpretation, "_add_edge", fake_add_edge)
    edges = [("A", "B")]
    added, changes = add_edges(["A"], ["B", "C"], {}, {}, [], edges, FakeLabel("L"), {}, {}, {}, 0)
    assert added == [("A", "B"), ("A", "C")]
    assert changes == 1


# ---- _delete_edge / _delete_node tests ----

def test_delete_edge_removes_all_references():
    lbl = FakeLabel("L")
    neighbors = {"A": ["B"], "C": []}
    reverse_neighbors = {"B": ["A"], "C": []}
    edges = [("A", "B")]
    interp_edge = {("A", "B"): "W"}
    predicate_map = {lbl: [("A", "B"), ("C", "D")]}
    delete_edge(("A", "B"), neighbors, reverse_neighbors, edges, interp_edge, predicate_map)
    assert edges == []
    assert interp_edge == {}
    assert neighbors["A"] == [] and reverse_neighbors["B"] == []
    assert predicate_map[lbl] == [("C", "D")]


def test_delete_node_removes_all_references():
    lbl = FakeLabel("L")
    neighbors = {"A": ["B"], "B": [], "C": ["A"]}
    reverse_neighbors = {"A": ["C"], "B": ["A"], "C": []}
    nodes = ["A", "B", "C"]
    interp_node = {"A": "wA", "B": "wB", "C": "wC"}
    predicate_map = {lbl: ["A", "B"]}
    delete_node("A", neighbors, reverse_neighbors, nodes, interp_node, predicate_map)
    assert nodes == ["B", "C"]
    assert "A" not in neighbors and "A" not in reverse_neighbors
    assert interp_node == {"B": "wB", "C": "wC"}
    assert predicate_map[lbl] == ["B"]


# ---- are_satisfied_node / are_satisfied_edge tests ----

@pytest.mark.parametrize(
    "are_fn,sat_name",
    [
        (are_satisfied_node, "is_satisfied_node"),
        (are_satisfied_edge, "is_satisfied_edge"),
    ],
)
def test_are_satisfied_helpers_call_each(monkeypatch, are_fn, sat_name):
    mock = Mock(side_effect=[True, False])
    monkeypatch.setattr(interpretation, sat_name, mock)
    nas = [("l1", _Interval(0, 1)), ("l2", _Interval(0, 1))]
    out = are_fn({}, "c", nas)
    assert out is False
    expected = [call({}, "c", nas[0]), call({}, "c", nas[1])]
    mock.assert_has_calls(expected)


# ---- is_satisfied_*_comparison tests ----

@pytest.mark.parametrize(
    "cmp_fn,interp_key",
    [
        (is_satisfied_node_comparison, "n"),
        (is_satisfied_edge_comparison, ("s", "t")),
    ],
)
def test_is_satisfied_comparison(monkeypatch, cmp_fn, interp_key):
    monkeypatch.setattr(interpretation, "str_to_float", lambda s: float(s))
    w = _World({FakeLabel("p.5"): _Interval(0, 1)})
    interpretations = {interp_key: w}
    res, num = cmp_fn(interpretations, interp_key, (FakeLabel("p"), _Interval(0, 1)))
    assert res is True and num == 5.0
    res, num = cmp_fn(interpretations, interp_key, (FakeLabel("q"), _Interval(0, 1)))
    assert res is False and num == 0


# ---- _update_rule_trace tests ----

def test_update_rule_trace_makes_copy():
    rt = []
    bnd = _Interval(0.1, 0.2)
    update_rule_trace(rt, [["n1"]], [[("a", "b")]], bnd, "name")
    assert rt[0][0] == [["n1"]]
    assert rt[0][1] == [[("a", "b")]]
    assert rt[0][2] is not bnd and rt[0][2].lower == bnd.lower
    assert rt[0][3] == "name"


# ---- annotate tests ----

class AnnRule:
    def __init__(self, fn, bnd):
        self._fn = fn
        self._bnd = bnd
    def get_annotation_function(self): return self._fn
    def get_bnd(self): return self._bnd


def test_annotate_returns_bounds_when_no_function():
    bnd = _Interval(0.2, 0.3)
    rule = AnnRule("", bnd)
    lo, up = annotate([], rule, [], [])
    assert (lo, up) == (0.2, 0.3)


def test_annotate_calls_named_function():
    bnd = _Interval(0, 1)
    rule = AnnRule("foo", bnd)
    def foo(ann, wts):
        return (len(ann), len(wts))
    out = annotate([foo], rule, [1, 2], [3])
    assert out == (2, 1)


# ---- float/str conversion helper tests ----

def test_float_to_str_and_str_to_int():
    assert float_to_str(12.345) == "12.345"
    assert float_to_str(3.0) == "3.0"
    assert str_to_int("123") == 123
    assert str_to_int("-45") == -45


@pytest.mark.parametrize(
    "s,expected",
    [("3.14", 3.14), ("42", 42.0), ("-2.5", -2.5)],
)
def test_str_to_float_variants(s, expected):
    assert math.isclose(str_to_float(s), expected)


def test_ground_rule_edge_recheck_failure_skips_body(monkeypatch):
    _shim_typed_list(monkeypatch)

    monkeypatch.setattr(
        interpretation,
        "get_rule_node_clause_grounding",
        lambda var, *a: ["x1"] if var == "X" else ["y1"],
    )
    monkeypatch.setattr(
        interpretation,
        "get_qualified_node_groundings",
        lambda interp, grounding, *a: grounding,
    )
    monkeypatch.setattr(
        interpretation,
        "check_node_grounding_threshold_satisfaction",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        interpretation,
        "refine_groundings",
        lambda *a, **k: None,
    )

    mock_check_all = Mock(return_value=False)
    monkeypatch.setattr(
        interpretation,
        "check_all_clause_satisfaction",
        mock_check_all,
    )

    mock_add_node = Mock()
    mock_add_edge = Mock()
    monkeypatch.setattr(interpretation, "_add_node", mock_add_node)
    monkeypatch.setattr(interpretation, "_add_edge", mock_add_edge)

    rule = DummyRule(
        rtype="edge",
        head_vars=("X", "Y"),
        clauses=[
            ("node", "L", ("X",), ("b",), "op"),
            ("node", "L", ("Y",), ("b",), "op"),
        ],
        thresholds=[("ge", ("number", "total"), 1)] * 2,
        ann_fn="",
        rule_edges=("src", "tgt", "HEADLBL"),
    )

    interpretations_node, interpretations_edge = {}, {}
    nodes, edges = [], []
    neighbors, reverse_neighbors = {}, {}
    predicate_map_node, predicate_map_edge = {}, {}

    apps_node, apps_edge = ground_rule(
        rule,
        interpretations_node,
        interpretations_edge,
        predicate_map_node,
        predicate_map_edge,
        nodes,
        edges,
        neighbors,
        reverse_neighbors,
        atom_trace=False,
        allow_ground_rules=False,
        t=0,
    )

    assert apps_node == []
    assert apps_edge == []
    mock_check_all.assert_called_once()
    mock_add_node.assert_not_called()
    mock_add_edge.assert_not_called()
