import pytest
from unittest.mock import Mock, call
import inspect

pytestmark = pytest.mark.usefixtures("helpers_fixture")
def test_is_satisfied_node_comparison_missing_world():
    l = label.Label("L")
    l.value = l.get_value()
    result, number = interpretation.is_satisfied_node_comparison({}, "missing", (l, object()))
    assert (result, number) == (False, 0)


def test_is_satisfied_edge_comparison_missing_world():
    l = label.Label("L")
    l.value = l.get_value()
    result, number = interpretation.is_satisfied_edge_comparison({}, ("a", "b"), (l, object()))
    assert (result, number) == (False, 0)


def test_is_satisfied_edge_comparison_missing_bounds():
    l = label.Label("L")
    l.value = l.get_value()
    result, number = interpretation.is_satisfied_edge_comparison({}, ("a", "b"), (l, None))
    assert (result, number) == (True, 0)


def test_resolve_inconsistency_node_rule_trace(monkeypatch):
    class SimpleInterval:
        def __init__(self):
            self.lower = self.upper = None
            self.static = False

        def set_lower_upper(self, l, u):
            self.lower, self.upper = l, u

        def set_static(self, s):
            self.static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval())
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    world = SimpleWorld()
    world.world[l] = SimpleInterval()
    interpretations = {"n1": world}
    rule_trace = []
    rule_trace_atoms = []
    rules_to_be_applied_trace = [([], [], "r")]
    facts_to_be_applied_trace = ["f"]

    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_rule_trace", mock_update)

    interpretation.resolve_inconsistency_node(
        interpretations,
        "n1",
        (l, interpretation.interval.closed(0, 1)),
        [],
        0,
        0,
        0,
        True,
        rule_trace,
        rule_trace_atoms,
        rules_to_be_applied_trace,
        facts_to_be_applied_trace,
        True,
        "rule",
    )

    assert mock_update.call_args[0][-1].endswith("r")
    assert len(rule_trace) == 1


def test_resolve_inconsistency_node_rule_trace_no_atom_trace(monkeypatch):
    class SimpleInterval:
        def __init__(self):
            self.lower = self.upper = None
            self.static = False

        def set_lower_upper(self, l, u):
            self.lower, self.upper = l, u

        def set_static(self, s):
            self.static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval())
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    world = SimpleWorld()
    world.world[l] = SimpleInterval()
    interpretations = {"n1": world}
    rule_trace = []
    rules_to_be_applied_trace = [([], [], "r")]

    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_rule_trace", mock_update)

    interpretation.resolve_inconsistency_node(
        interpretations,
        "n1",
        (l, interpretation.interval.closed(0, 1)),
        [],
        0,
        0,
        0,
        False,
        rule_trace,
        [],
        rules_to_be_applied_trace,
        ["f"],
        True,
        "rule",
    )

    mock_update.assert_not_called()
    assert len(rule_trace) == 1


def test_resolve_inconsistency_edge_rule_trace(monkeypatch):
    class SimpleInterval:
        def __init__(self):
            self.lower = self.upper = None
            self.static = False

        def set_lower_upper(self, l, u):
            self.lower, self.upper = l, u

        def set_static(self, s):
            self.static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval())
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    world = SimpleWorld()
    world.world[l] = SimpleInterval()
    interpretations = {("a", "b"): world}
    rule_trace = []
    rule_trace_atoms = []
    rules_to_be_applied_trace = [([], [], "r")]
    facts_to_be_applied_trace = ["f"]

    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_rule_trace", mock_update)

    interpretation.resolve_inconsistency_edge(
        interpretations,
        ("a", "b"),
        (l, interpretation.interval.closed(0, 1)),
        [],
        0,
        0,
        0,
        True,
        rule_trace,
        rule_trace_atoms,
        rules_to_be_applied_trace,
        facts_to_be_applied_trace,
        True,
        "rule",
    )

    assert mock_update.call_args[0][-1].endswith("r")
    assert len(rule_trace) == 1


def test_resolve_inconsistency_edge_rule_trace_no_atom_trace(monkeypatch):
    class SimpleInterval:
        def __init__(self):
            self.lower = self.upper = None
            self.static = False

        def set_lower_upper(self, l, u):
            self.lower, self.upper = l, u

        def set_static(self, s):
            self.static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval())
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    world = SimpleWorld()
    world.world[l] = SimpleInterval()
    interpretations = {("a", "b"): world}
    rule_trace = []
    rules_to_be_applied_trace = [([], [], "r")]

    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_rule_trace", mock_update)

    interpretation.resolve_inconsistency_edge(
        interpretations,
        ("a", "b"),
        (l, interpretation.interval.closed(0, 1)),
        [],
        0,
        0,
        0,
        False,
        rule_trace,
        [],
        rules_to_be_applied_trace,
        ["f"],
        True,
        "rule",
    )

    mock_update.assert_not_called()
    assert len(rule_trace) == 1
