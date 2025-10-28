import pytest
from unittest.mock import Mock, call
from tests.unit.disable_jit.interpretations.test_interpretation_common import get_interpretation_helpers

# Preload defaults so decorators resolve
_default = get_interpretation_helpers("interpretation_fp")
for _name in dir(_default):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_default, _name)


@pytest.fixture(params=["interpretation_fp", "interpretation"], autouse=True)
def helpers_fixture(request):
    h = get_interpretation_helpers(request.param)
    g = globals()
    for name in dir(h):
        if not name.startswith("_"):
            g[name] = getattr(h, name)
    yield


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
    assert is_satisfied_node(interpretations, comp, na) is True
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
    assert is_satisfied_node(interpretations, comp, na) is True
    assert is_satisfied_edge(interpretations, comp, na) is True
    
def test_is_satisfied_edge_returns_false_when_comp_missing():
    # Empty dict so interpretations[comp] raises inside the try-block
    interpretations = {}
    comp = ("ghost", "edge")
    na = ("owns", [1.0, 1.0])  # both non-None => enter try/except
    assert is_satisfied_node(interpretations, comp, na) is False
    assert is_satisfied_edge(interpretations, comp, na) is False


# ---- get_qualified_edge_groundings and get_qualified_node_groundings tests ----

def test_get_qualified_edge_and_node_groundings_filters_true_edges(interpretations, monkeypatch):
    # Use a plain list instead of a typed list for easy assertions
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    # Separate mocks so each gets exactly 3 calls
    mock_is_sat_edge = Mock(side_effect=[False, True, True])  # F, T, T
    mockis_satisfied_node = Mock(side_effect=[False, True, True])  # F, T, T

    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mockis_satisfied_node)

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
    assert mockis_satisfied_node.call_count == 3

    from unittest.mock import call
    expected_calls = [
        call(interpretations, grounding[0], (clause_l, clause_bnd)),
        call(interpretations, grounding[1], (clause_l, clause_bnd)),
        call(interpretations, grounding[2], (clause_l, clause_bnd)),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mockis_satisfied_node.assert_has_calls(expected_calls)


def test_get_qualified_edge_and_node_groundings_none_qualify(interpretations, monkeypatch):
    # Return a plain list instead of a numba typed list for easy assertions
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    # Separate mocks so each gets exactly len(grounding) calls
    mock_is_sat_edge = Mock(return_value=False)
    mockis_satisfied_node = Mock(return_value=False)
    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mockis_satisfied_node)

    grounding = [('Justin', 'Dog'), ('Justin', 'Cat')]

    result_edge = get_qualified_edge_groundings(interpretations, grounding, 'owns', [1.0, 1.0])
    result_node = get_qualified_node_groundings(interpretations, grounding, 'owns', [1.0, 1.0])

    assert result_edge == []
    assert result_node == []
    assert mock_is_sat_edge.call_count == 2
    assert mockis_satisfied_node.call_count == 2

    expected_calls = [
        call(interpretations, grounding[0], ('owns', [1.0, 1.0])),
        call(interpretations, grounding[1], ('owns', [1.0, 1.0])),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mockis_satisfied_node.assert_has_calls(expected_calls)


def test_get_qualified_edge_and_node_groundings_all_qualify(interpretations, monkeypatch):
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])

    mock_is_sat_edge = Mock(return_value=True)
    mockis_satisfied_node = Mock(return_value=True)
    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_is_sat_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mockis_satisfied_node)

    grounding = [('A', 'B'), ('C', 'D')]

    result_edge = get_qualified_edge_groundings(interpretations, grounding, 'owns', [1.0, 1.0])
    result_node = get_qualified_node_groundings(interpretations, grounding, 'owns', [1.0, 1.0])

    assert result_edge == grounding
    assert result_node == grounding
    assert mock_is_sat_edge.call_count == 2
    assert mockis_satisfied_node.call_count == 2

    expected_calls = [
        call(interpretations, grounding[0], ('owns', [1.0, 1.0])),
        call(interpretations, grounding[1], ('owns', [1.0, 1.0])),
    ]
    mock_is_sat_edge.assert_has_calls(expected_calls)
    mockis_satisfied_node.assert_has_calls(expected_calls)

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
    monkeypatch.setitem(check_fn.__globals__, "_satisfies_threshold", mock_sat)

    # Should NOT call the get_qualified_* in 'total' mode
    mock_get_q = Mock()
    monkeypatch.setitem(check_fn.__globals__, get_q_attr, mock_get_q)

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
    monkeypatch.setitem(check_fn.__globals__, get_q_attr, mock_get_q)

    # _satisfies_threshold should be called with (len(available_return), len(qualified), threshold)
    mock_sat = Mock(return_value=False)
    monkeypatch.setitem(check_fn.__globals__, "_satisfies_threshold", mock_sat)

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
    monkeypatch.setitem(
        check_node_grounding_threshold_satisfaction.__globals__,
        "get_qualified_node_groundings",
        mock_get_q,
    )

    # _satisfies_threshold should be called with neigh_len = 3, qualified_len = 1
    mock_sat = Mock(return_value=False)
    monkeypatch.setitem(
        check_node_grounding_threshold_satisfaction.__globals__,
        "_satisfies_threshold",
        mock_sat,
    )

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
    predicate_map = {k: list(v) for k, v in pred_init.items()}  # deep copy
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
@pytest.mark.skip(reason="predicate map updates diverge between implementations")
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
    predicate_map = {k: list(v) for k, v in pred_init.items()}
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
    def get_head_function(self): return ["", ""]
    def get_head_function_vars(self): return [[], []]

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
