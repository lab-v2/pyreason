import importlib
import math
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from pyreason.scripts.interpretation.interpretation_dict import InterpretationDict
from tests.unit.disable_jit.interpretation_helpers import *

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



# ---- get_dict tests ----

class DummyLabel:
    def __init__(self, value):
        self._value = value


class DummyBound:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper


def build_dummy(persistent):
    return SimpleNamespace(
        time=1,
        nodes=["n1"],
        edges=[("n1", "n2")],
        rule_trace_node=[(0, 0, "n1", DummyLabel("L1"), DummyBound(0.1, 0.2))],
        rule_trace_edge=[(0, 0, ("n1", "n2"), DummyLabel("L2"), DummyBound(0.3, 0.4))],
        persistent=persistent,
    )


@pytest.mark.parametrize("module_name", ["interpretation_fp", "interpretation"])
def test_get_dict_non_persistent(module_name):
    module = importlib.import_module(f"pyreason.scripts.interpretation.{module_name}")
    interp = build_dummy(False)
    result = module.Interpretation.get_dict(interp)

    assert isinstance(result[0]["n1"], InterpretationDict)
    assert result[0]["n1"]["L1"] == (0.1, 0.2)
    assert len(result[1]["n1"]) == 0

    assert result[0][("n1", "n2")]["L2"] == (0.3, 0.4)
    assert len(result[1][("n1", "n2")]) == 0


@pytest.mark.parametrize("module_name", ["interpretation_fp", "interpretation"])
def test_get_dict_persistent(module_name):
    module = importlib.import_module(f"pyreason.scripts.interpretation.{module_name}")
    interp = build_dummy(True)
    result = module.Interpretation.get_dict(interp)

    assert result[0]["n1"]["L1"] == (0.1, 0.2)
    assert result[1]["n1"]["L1"] == (0.1, 0.2)

    assert result[0][("n1", "n2")]["L2"] == (0.3, 0.4)
    assert result[1][("n1", "n2")]["L2"] == (0.3, 0.4)

