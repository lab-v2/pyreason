import math
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from pyreason.scripts.interpretation.interpretation_dict import InterpretationDict
from tests.unit.disable_jit.interpretation_helpers import get_interpretation_helpers

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
    def __init__(self, truth_by_label=None):
        self.truth_by_label = truth_by_label or {}
    def is_satisfied(self, label, interval):
        return self.truth_by_label.get(label, False)


@pytest.fixture
def interpretations():
    return {
        ('Justin', 'Cat'):  FakeWorld({'owns': False}),
        ('Justin', 'Dog'):  FakeWorld({'owns': True}),
    }


def test_is_satisfied_node_and_edge(interpretations):
    comp = ('Justin', 'Dog')
    na = ('owns', [1.0, 1.0])
    assert is_satisfied_node(interpretations, comp, na) is True
    assert is_satisfied_edge(interpretations, comp, na) is True
    comp = ('Justin', 'Cat')
    assert is_satisfied_edge(interpretations, comp, na) is False


def test_get_qualified_groundings_filters(monkeypatch, interpretations):
    monkeypatch.setattr(interpretation.numba.typed.List, "empty_list", lambda *a, **k: [])
    mock_edge = Mock(side_effect=[False, True, True])
    mock_node = Mock(side_effect=[False, True, True])
    monkeypatch.setattr(interpretation, "is_satisfied_edge", mock_edge)
    monkeypatch.setattr(interpretation, "is_satisfied_node", mock_node)
    grounding = [
        ('Justin', 'Cat'),
        ('Justin', 'Dog'),
        ('Nobody', 'Home'),
    ]
    clause_l, clause_bnd = 'owns', [1.0, 1.0]
    result_edge = get_qualified_edge_groundings(interpretations, grounding, clause_l, clause_bnd)
    result_node = get_qualified_node_groundings(interpretations, grounding, clause_l, clause_bnd)
    assert result_edge == [grounding[1], grounding[2]]
    assert result_node == [grounding[1], grounding[2]]
    expected_calls = [
        call(interpretations, grounding[0], (clause_l, clause_bnd)),
        call(interpretations, grounding[1], (clause_l, clause_bnd)),
        call(interpretations, grounding[2], (clause_l, clause_bnd)),
    ]
    mock_edge.assert_has_calls(expected_calls)
    mock_node.assert_has_calls(expected_calls)


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


@pytest.mark.parametrize("check_fn_name", ["check_consistent_node", "check_consistent_edge"])
def test_check_consistent_functions(monkeypatch, check_fn_name):
    check_fn = globals()[check_fn_name]
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: _Interval(lo, up))
    interp = {"c": _World({"p": _Interval(0, 0.5)})}
    assert check_fn(interp, "c", ("p", _Interval(0.4, 0.6))) is True
    assert check_fn(interp, "c", ("p", _Interval(0.6, 0.8))) is False
    interp2 = {"c": _World({})}
    assert check_fn(interp2, "c", ("p", _Interval(0.6, 0.8))) is True


# ---- resolve_inconsistency_node / resolve_inconsistency_edge tests ----

@pytest.mark.parametrize(
    "resolver_name,comp_key",
    [
        ("resolve_inconsistency_node", "n"),
        ("resolve_inconsistency_edge", ("s", "t")),
    ],
)
def test_resolve_inconsistency_updates_world_and_trace(monkeypatch, resolver_name, comp_key):
    resolver = globals()[resolver_name]
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
    def fake_add_edge(src, tgt, neighbors, reverse_neighbors, nodes, edges, l, interp_node, interp_edge, pred, *rest):
        edge = (src, tgt)
        new_edge = edge not in edges
        if new_edge:
            edges.append(edge)
        return edge, new_edge

    monkeypatch.setattr(interpretation, "_add_edge", fake_add_edge)
    edges = [("A", "B")]
    args = [
        ["A"],
        ["B", "C"],
        {},
        {},
        [],
        edges,
        FakeLabel("L"),
        {},
        {},
        {},
        0,
    ]
    if not interpretation.__name__.endswith("_fp"):
        args.insert(-1, [])
    added, changes = add_edges(*args)
    assert added == [("A", "B"), ("A", "C")]
    assert changes == 1


# ---- _delete_edge / _delete_node tests ----

def test_delete_edge_removes_all_references():
    lbl = FakeLabel("L")
    neighbors = {"A": ["B"], "C": []}
    reverse_neighbors = {"B": ["A"], "C": []}
    edges = [("A", "B")]
    interp_edge = {("A", "B"): SimpleNamespace(world=[])}
    predicate_map = {lbl: [("A", "B"), ("C", "D")]}
    if interpretation.__name__.endswith("_fp"):
        delete_edge(("A", "B"), neighbors, reverse_neighbors, edges, interp_edge, predicate_map)
    else:
        delete_edge(("A", "B"), neighbors, reverse_neighbors, edges, interp_edge, predicate_map, [0])
    assert edges == []
    assert interp_edge == {}
    assert neighbors["A"] == [] and reverse_neighbors["B"] == []
    assert predicate_map[lbl] == [("C", "D")]


def test_delete_node_removes_all_references():
    lbl = FakeLabel("L")
    neighbors = {"A": ["B"], "B": [], "C": ["A"]}
    reverse_neighbors = {"A": ["C"], "B": ["A"], "C": []}
    nodes = ["A", "B", "C"]
    interp_node = {"A": SimpleNamespace(world=[]), "B": SimpleNamespace(world=[]), "C": SimpleNamespace(world=[])}
    predicate_map = {lbl: ["A", "B"]}
    if interpretation.__name__.endswith("_fp"):
        delete_node("A", neighbors, reverse_neighbors, nodes, interp_node, predicate_map)
    else:
        delete_node("A", neighbors, reverse_neighbors, nodes, interp_node, predicate_map, [0])
    assert nodes == ["B", "C"]
    assert "A" not in neighbors and "A" not in reverse_neighbors
    assert set(interp_node.keys()) == {"B", "C"}
    assert predicate_map[lbl] == ["B"]


# ---- are_satisfied_node / are_satisfied_edge tests ----

@pytest.mark.parametrize(
    "are_fn_name,sat_name",
    [
        ("are_satisfied_node", "is_satisfied_node"),
        ("are_satisfied_edge", "is_satisfied_edge"),
    ],
)
def test_are_satisfied_helpers_call_each(monkeypatch, are_fn_name, sat_name):
    mock = Mock(side_effect=[True, False])
    monkeypatch.setattr(interpretation, sat_name, mock)
    nas = [("l1", _Interval(0, 1)), ("l2", _Interval(0, 1))]
    are_fn = globals()[are_fn_name]
    out = are_fn({}, "c", nas)
    assert out is False
    expected = [call({}, "c", nas[0]), call({}, "c", nas[1])]
    mock.assert_has_calls(expected)


# ---- is_satisfied_*_comparison tests ----

@pytest.mark.parametrize(
    "cmp_fn_name,interp_key",
    [
        ("is_satisfied_node_comparison", "n"),
        ("is_satisfied_edge_comparison", ("s", "t")),
    ],
)
def test_is_satisfied_comparison(monkeypatch, cmp_fn_name, interp_key):
    cmp_fn = globals()[cmp_fn_name]
    monkeypatch.setattr(interpretation, "str_to_float", lambda s: float(s))
    w = _World({FakeLabel("p.5"): _Interval(0, 1)})
    interpretations = {interp_key: w}
    res, num = cmp_fn(interpretations, interp_key, (FakeLabel("p"), _Interval(0, 1)))
    assert res is True and math.isclose(num, 5.0)
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

    def get_annotation_function(self):
        return self._fn

    def get_bnd(self):
        return self._bnd


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


# ---- get_dict tests ----

class DummyLabel:
    def __init__(self, value):
        self._value = value


class DummyBound:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __contains__(self, interval):
        return self.lower <= interval.lower and interval.upper <= self.upper


def build_dummy(persistent):
    return SimpleNamespace(
        time=1,
        nodes=["n1"],
        edges=[("n1", "n2")],
        rule_trace_node=[(0, 0, "n1", DummyLabel("L1"), DummyBound(0.1, 0.2))],
        rule_trace_edge=[(0, 0, ("n1", "n2"), DummyLabel("L2"), DummyBound(0.3, 0.4))],
        persistent=persistent,
    )


def build_ga_dummy():
    nw = _World({"L1": _Interval(0.1, 0.2)})
    ew = _World({"L2": _Interval(0.3, 0.4)})
    return SimpleNamespace(
        nodes=["n1"],
        edges=[("n1", "n2")],
        interpretations_node={"n1": nw},
        interpretations_edge={("n1", "n2"): ew},
    )


def build_query_dummy():
    interp = build_ga_dummy()
    if interpretation.__name__.endswith("_fp"):
        interp.interpretations_node = [interp.interpretations_node]
        interp.interpretations_edge = [interp.interpretations_edge]
    return interp


class DummyQuery:
    def __init__(self, comp_type, component, pred, bounds):
        self._ct = comp_type
        self._comp = component
        self._pred = pred
        self._bnd = bounds

    def get_component_type(self):
        return self._ct

    def get_component(self):
        return self._comp

    def get_predicate(self):
        return self._pred

    def get_bounds(self):
        return self._bnd


def test_get_dict_non_persistent():
    module = interpretation
    interp = build_dummy(False)
    result = module.Interpretation.get_dict(interp)

    assert isinstance(result[0]["n1"], InterpretationDict)
    assert result[0]["n1"]["L1"] == (0.1, 0.2)
    assert len(result[1]["n1"]) == 0

    assert result[0][("n1", "n2")]["L2"] == (0.3, 0.4)
    assert len(result[1][("n1", "n2")]) == 0


def test_get_dict_persistent():
    module = interpretation
    interp = build_dummy(True)
    result = module.Interpretation.get_dict(interp)

    assert result[0]["n1"]["L1"] == (0.1, 0.2)
    assert result[1]["n1"]["L1"] == (0.1, 0.2)

    assert result[0][("n1", "n2")]["L2"] == (0.3, 0.4)
    assert result[1][("n1", "n2")]["L2"] == (0.3, 0.4)


# ---- get_final_num_ground_atoms / query tests ----

def test_get_final_num_ground_atoms():
    module = interpretation
    interp = build_ga_dummy()
    assert module.Interpretation.get_final_num_ground_atoms(interp) == 2


@pytest.mark.parametrize(
    "comp_type, component, pred, bound, expected_bool, expected_tuple",
    [
        ("node", "nX", "L1", DummyBound(0, 1), False, (0, 0)),
        ("node", "n1", "missing", DummyBound(0, 1), False, (0, 0)),
        ("node", "n1", "L1", DummyBound(0, 0.05), False, (0, 0)),
        ("node", "n1", "L1", DummyBound(0, 1), True, (0.1, 0.2)),
        ("edge", ("nX", "nY"), "L2", DummyBound(0, 1), False, (0, 0)),
        ("edge", ("n1", "n2"), "missing", DummyBound(0, 1), False, (0, 0)),
        ("edge", ("n1", "n2"), "L2", DummyBound(0, 0.2), False, (0, 0)),
        ("edge", ("n1", "n2"), "L2", DummyBound(0, 1), True, (0.3, 0.4)),
    ],
)
def test_query(comp_type, component, pred, bound, expected_bool, expected_tuple):
    module = interpretation
    interp = build_query_dummy()
    q = DummyQuery(comp_type, component, pred, bound)
    assert module.Interpretation.query(interp, q) is expected_bool
    assert module.Interpretation.query(interp, q, return_bool=False) == expected_tuple
