"""Unit tests for closed_world predicates (circumscription) in is_satisfied_node/edge.

Tests verify that when a predicate is in the closed_world_predicates list:
- Unknown bounds [0,1] are treated as [0,0]
- Missing labels are treated as [0,0]
- Known bounds (not [0,1]) are unaffected
"""
import pytest
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


class _Interval:
    """Interval with lower/upper attributes."""
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __eq__(self, other):
        return (isinstance(other, _Interval)
                and self.lower == other.lower
                and self.upper == other.upper)

    def __repr__(self):
        return f"_Interval({self.lower}, {self.upper})"


class _Bound:
    """Clause bound supporting interval containment via ``in``."""
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.l = lower
        self.u = upper

    def __contains__(self, iv):
        return self.lower <= iv.lower and iv.upper <= self.upper

    def __repr__(self):
        return f"_Bound({self.lower}, {self.upper})"


class _World:
    """Minimal world with a .world dict mapping labels to intervals."""
    def __init__(self, mapping=None):
        self.world = mapping or {}

    def is_satisfied(self, label, bnd):
        w = self.world[label]
        return not (bnd.lower > w.upper or w.lower > bnd.upper)


@pytest.fixture(autouse=True)
def patch_interval(monkeypatch):
    monkeypatch.setattr(interpretation.interval, "closed",
                        lambda lo, up: _Interval(lo, up))


# ---- is_satisfied_node tests ----

class Testclosed_worldIsStatisfiedNode:
    def test_unknown_bounds_treated_as_false(self):
        """[0,1] bounds on a closed_world predicate should be treated as [0,0],
        so a clause requiring [1,1] should NOT be satisfied."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is False

    def test_missing_label_treated_as_false(self):
        """A closed_world predicate not in the world should be treated as [0,0]."""
        world = _World({})  # pred not present
        interpretations = {"node_a": world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is False

    def test_known_bounds_unaffected(self):
        """A closed_world predicate with known bounds [1,1] should still satisfy [1,1]."""
        world = _World({"pred": _Interval(1.0, 1.0)})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is True

    def test_zero_zero_clause_with_unknown(self):
        """A clause requiring [0,0] should be satisfied when closed_world [0,1] -> [0,0]."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(0.0, 0.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is True

    def test_zero_zero_clause_with_missing(self):
        """A clause requiring [0,0] should be satisfied when closed_world pred is missing."""
        world = _World({})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(0.0, 0.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is True

    def test_non_closed_world_predicate_unchanged(self):
        """Without minimization, [0,1] bounds use standard satisfaction."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(1.0, 1.0))
        # Standard: [0,1] overlaps [1,1] at the boundary -> not (1 > 1 or 0 > 1) -> True
        assert is_satisfied_node(interpretations, "node_a", na, []) is True

    def test_partial_bounds_not_closed_world(self):
        """Bounds like [0.5, 0.8] should NOT be treated as unknown even if closed_world."""
        world = _World({"pred": _Interval(0.5, 0.8)})
        interpretations = {"node_a": world}
        na = ("pred", _Bound(0.0, 1.0))
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is True

    def test_multiple_closed_world_predicates(self):
        """Multiple predicates can be closed_world; each checked independently."""
        world = _World({
            "pred_a": _Interval(0.0, 1.0),  # unknown -> [0,0]
            "pred_b": _Interval(1.0, 1.0),  # known -> unaffected
        })
        interpretations = {"node_a": world}
        closed_world = ["pred_a", "pred_b"]
        # pred_a [0,1] -> [0,0], clause [1,1] -> False
        assert is_satisfied_node(interpretations, "node_a",
                                 ("pred_a", _Bound(1.0, 1.0)), closed_world) is False
        # pred_b [1,1] -> still [1,1], clause [1,1] -> True
        assert is_satisfied_node(interpretations, "node_a",
                                 ("pred_b", _Bound(1.0, 1.0)), closed_world) is True

    def test_none_na_returns_true(self):
        """na with None components should still return True regardless of closed_world."""
        interpretations = {}
        na = (None, None)
        assert is_satisfied_node(interpretations, "node_a", na, ["pred"]) is True


# ---- is_satisfied_edge tests ----

class Testclosed_worldIsSatisfiedEdge:
    def test_unknown_bounds_treated_as_false(self):
        """[0,1] bounds on a closed_world predicate should be treated as [0,0]."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {("a", "b"): world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_edge(interpretations, ("a", "b"), na, ["pred"]) is False

    def test_missing_label_treated_as_false(self):
        """A closed_world predicate not in the world should be treated as [0,0]."""
        world = _World({})
        interpretations = {("a", "b"): world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_edge(interpretations, ("a", "b"), na, ["pred"]) is False

    def test_known_bounds_unaffected(self):
        """Known bounds [1,1] should still satisfy [1,1] even when closed_world."""
        world = _World({"pred": _Interval(1.0, 1.0)})
        interpretations = {("a", "b"): world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_edge(interpretations, ("a", "b"), na, ["pred"]) is True

    def test_zero_zero_clause_with_unknown(self):
        """Clause [0,0] satisfied when closed_world [0,1] -> [0,0]."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {("a", "b"): world}
        na = ("pred", _Bound(0.0, 0.0))
        assert is_satisfied_edge(interpretations, ("a", "b"), na, ["pred"]) is True

    def test_non_closed_world_unchanged(self):
        """Without minimization, [0,1] uses standard satisfaction."""
        world = _World({"pred": _Interval(0.0, 1.0)})
        interpretations = {("a", "b"): world}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_edge(interpretations, ("a", "b"), na, []) is True

    def test_multiple_closed_world_predicates(self):
        """Multiple closed_world predicates checked independently on edges."""
        world = _World({
            "pred_a": _Interval(0.0, 1.0),
            "pred_b": _Interval(1.0, 1.0),
        })
        interpretations = {("a", "b"): world}
        closed_world = ["pred_a", "pred_b"]
        assert is_satisfied_edge(interpretations, ("a", "b"),
                                 ("pred_a", _Bound(1.0, 1.0)), closed_world) is False
        assert is_satisfied_edge(interpretations, ("a", "b"),
                                 ("pred_b", _Bound(1.0, 1.0)), closed_world) is True

    def test_comp_missing_returns_false(self):
        """Edge not in interpretations should return False (exception path)."""
        interpretations = {}
        na = ("pred", _Bound(1.0, 1.0))
        assert is_satisfied_edge(interpretations, ("ghost", "edge"), na, ["pred"]) is False
