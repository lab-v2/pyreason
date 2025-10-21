import pytest
from unittest.mock import Mock, call
import inspect

pytestmark = pytest.mark.usefixtures("helpers_fixture")
def test_update_node_tracks_changes(monkeypatch):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def is_static(self):
            return self._static

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    interpretations = {"n1": SimpleWorld()}
    predicate_map = {}
    num_ga = [0]

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)

    def call(lower, upper):
        kwargs = dict(
            interpretations=interpretations,
            predicate_map=predicate_map,
            comp="n1",
            na=(l, interpretation.interval.closed(lower, upper)),
            ipl=[],
            rule_trace=[],
            fp_cnt=0,
            t_cnt=0,
            static=False,
            convergence_mode="perfect_convergence",
            atom_trace=False,
            save_graph_attributes_to_rule_trace=False,
            rules_to_be_applied_trace=[],
            idx=0,
            facts_to_be_applied_trace=[],
            rule_trace_atoms=[],
            store_interpretation_changes=False,
            mode="fact",
            override=False,
        )
        if "num_ga" in sig.parameters:
            kwargs["num_ga"] = num_ga
        return update_node(**kwargs)

    assert call(0.2, 0.4) == (True, 1)
    assert call(0.2, 0.4) == (False, 0)
    w_bnd = interpretations["n1"].world[l]
    assert (w_bnd.lower, w_bnd.upper) == (0.2, 0.4)
    assert list(predicate_map[l]) == ["n1"]
    if "num_ga" in sig.parameters:
        assert num_ga[0] == 1


def test_update_edge_tracks_changes(monkeypatch):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def is_static(self):
            return self._static

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {}
    num_ga = [0]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)

    def call(lower, upper):
        kwargs = dict(
            interpretations=interpretations,
            predicate_map=predicate_map,
            comp="e1",
            na=(l, interpretation.interval.closed(lower, upper)),
            ipl=[],
            rule_trace=[],
            fp_cnt=0,
            t_cnt=0,
            static=True,
            convergence_mode="perfect_convergence",
            atom_trace=False,
            save_graph_attributes_to_rule_trace=False,
            rules_to_be_applied_trace=[],
            idx=0,
            facts_to_be_applied_trace=[],
            rule_trace_atoms=[],
            store_interpretation_changes=False,
            mode="rule",
            override=False,
        )
        if "num_ga" in sig.parameters:
            kwargs["num_ga"] = num_ga
        return update_edge(**kwargs)

    assert call(0.3, 0.6) == (True, 1)
    assert call(0.3, 0.6) == (False, 0)
    w_bnd = interpretations["e1"].world[l]
    assert (w_bnd.lower, w_bnd.upper) == (0.3, 0.6)
    assert w_bnd.is_static() is True
    assert list(predicate_map[l]) == ["e1"]
    if "num_ga" in sig.parameters:
        assert num_ga[0] == 1


def test_update_node_override_sets_bounds(monkeypatch):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def is_static(self):
            return self._static

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class NoUpdateWorld:
        def __init__(self):
            self.world = {}

        def update(self, *a, **k):  # pragma: no cover - should not be called
            raise AssertionError("update should not be used when override=True")

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    world = NoUpdateWorld()
    world.world[l] = SimpleInterval()
    interpretations = {"n1": world}
    predicate_map = {}
    rule_trace = []
    rule_trace_atoms = []
    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.3, 0.7)),
        ipl=[],
        rule_trace=rule_trace,
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=rule_trace_atoms,
        store_interpretation_changes=False,
        mode="fact",
        override=True,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    update_node(**kwargs)
    bnd = interpretations["n1"].world[l]
    assert (bnd.lower, bnd.upper) == (0.3, 0.7)


def test_update_node_skips_graph_attr_trace(monkeypatch):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def is_static(self):
            return self._static

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    interpretations = {"n1": SimpleWorld()}
    predicate_map = {}
    rule_trace = []
    rule_trace_atoms = []
    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=[],
        rule_trace=rule_trace,
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=["fa"],
        rule_trace_atoms=rule_trace_atoms,
        store_interpretation_changes=True,
        mode="graph-attribute-fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    update_node(**kwargs)
    assert rule_trace == []
    assert rule_trace_atoms == []


@pytest.mark.parametrize(
    "mode,save_attr,trace_key,trace_val,expected_name",
    [
        ("fact", False, "facts_to_be_applied_trace", ["f"], "f"),
        ("graph-attribute-fact", True, "facts_to_be_applied_trace", ["g"], "g"),
        ("rule", False, "rules_to_be_applied_trace", [([], [], "r")], "r"),
    ],
)
def test_update_node_records_rule_trace(monkeypatch, mode, save_attr, trace_key, trace_val, expected_name):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def is_static(self):
            return self._static

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    interpretations = {"n1": SimpleWorld()}
    predicate_map = {}
    rule_trace = []
    rule_trace_atoms = []
    kwargs_trace = {trace_key: trace_val}
    calls = []

    def fake_update_rule_trace(rt_atoms, qn, qe, prev_bnd, name):
        calls.append((qn, qe, name))

    monkeypatch.setattr(interpretation, "_update_rule_trace", fake_update_rule_trace)

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=[],
        rule_trace=rule_trace,
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=save_attr,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=rule_trace_atoms,
        store_interpretation_changes=True,
        mode=mode,
        override=False,
    )
    kwargs.update(kwargs_trace)
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    update_node(**kwargs)
    assert len(rule_trace) == 1
    assert calls and calls[0][2] == expected_name


def test_update_node_handles_ipl_and_predicate_map(monkeypatch):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p2 = label.Label("L2")
    p3 = label.Label("L3")
    interpretations = {"n1": SimpleWorld()}
    predicate_map = {l: ["c0"], p2: ["x"]}
    ipl = [(l, p2), (l, p3)]

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_node(**kwargs)
    assert updated is True
    assert predicate_map[l] == ["c0", "n1"]
    assert predicate_map[p2] == ["x", "n1"]
    assert predicate_map[p3] == ["n1"]
    assert p2 in interpretations["n1"].world and p3 in interpretations["n1"].world
    assert len(calls) == 2


def test_update_node_complement_records_traces(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p2 = label.Label("L2")
    p3 = label.Label("L3")
    interpretations = {"n1": SimpleWorld()}
    predicate_map = {}
    ipl = [(l, p2), (p3, l)]

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.1, 0.2)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=["f"],
        rule_trace_atoms=[],
        store_interpretation_changes=True,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_node(**kwargs)
    assert updated is True
    world = interpretations["n1"].world
    assert p2 in world and p3 in world
    assert {entry[3] for entry in kwargs["rule_trace"]} == {l, p2, p3}
    assert len(calls) == 3


def test_update_node_complement_existing_predicate(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p3 = label.Label("L3")
    world = SimpleWorld()
    world.world[p3] = interpretation.interval.closed(0, 1)
    interpretations = {"n1": world}
    predicate_map = {p3: ["n1"]}

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.3, 0.6)),
        ipl=[(p3, l)],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_node(**kwargs)
    assert updated is True
    assert kwargs["rule_trace"] == []
    assert not calls


def test_update_node_predicate_map_appends_and_delta(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    p3 = label.Label("L3")
    world = SimpleWorld()
    interpretations = {"n1": world}
    predicate_map = {p3: ["other"]}

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="n1",
        na=(l, interpretation.interval.closed(0.1, 0.2)),
        ipl=[(p3, l)],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="delta_bound",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, change = update_node(**kwargs)
    assert updated is True
    assert predicate_map[p3][-1] == "n1"
    assert change == pytest.approx(0.8)


def test_update_edge_handles_ipl_and_predicate_map(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p2 = label.Label("L2")
    p3 = label.Label("L3")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {p3: ["x"]}
    ipl = [(l, p2), (p3, l)]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=["f"],
        rule_trace_atoms=[],
        store_interpretation_changes=True,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_edge(**kwargs)
    assert updated is True
    assert predicate_map[l] == ["e1"]
    assert predicate_map[p2] == ["e1"]
    assert predicate_map[p3] == ["x", "e1"]
    world = interpretations["e1"].world
    assert p2 in world and p3 in world
    assert {entry[3] for entry in kwargs["rule_trace"]} == {l, p2, p3}
    assert len(calls) == 3
    if "num_ga" in sig.parameters:
        assert kwargs["num_ga"][0] == 1


def test_update_edge_predicate_map_append_override(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {l: ["x"]}

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=[],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=True,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_edge(**kwargs)
    assert updated is True
    assert predicate_map[l] == ["x", "e1"]
    world_bnd = interpretations["e1"].world[l]
    assert (world_bnd.lower, world_bnd.upper) == (0.2, 0.4)


def test_update_edge_rule_atom_trace(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {}
    qn = [["n1"]]
    qe = [["e"]]
    rules_to_be_applied_trace = [(qn, qe, "r1")]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.3, 0.5)),
        ipl=[],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=rules_to_be_applied_trace,
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=True,
        mode="rule",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_edge(**kwargs)
    assert updated is True
    assert calls and calls[0][1] is qn and calls[0][2] is qe and calls[0][4] == "r1"


def test_update_node_missing_world(monkeypatch, helpers_fixture):
    """_update_node returns (False, 0) when interpretations lacks the component."""

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)

    l = label.Label("L")
    kwargs = dict(
        interpretations={},
        predicate_map={},
        comp="n1",
        na=(l, None),
        ipl=[],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    if interpretation.__name__.endswith("interpretation_fp"):
        with pytest.raises(KeyError):
            update_node(**kwargs)
    else:
        assert update_node(**kwargs) == (False, 0)


def test_update_edge_complement_delta_bound(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p2 = label.Label("L2")
    p3 = label.Label("L3")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {}
    ipl = [(l, p2), (p3, l)]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.2, 0.4)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="delta_bound",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, change = update_edge(**kwargs)
    assert updated is True
    assert predicate_map[p2] == ["e1"]
    assert predicate_map[p3] == ["e1"]
    world = interpretations["e1"].world
    assert p2 in world and p3 in world
    assert kwargs["rule_trace"] == []
    assert calls == []
    assert change == pytest.approx(0.6)


def test_update_edge_complement_records_traces(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

        def __eq__(self, other):
            return self.lower == other.lower and self.upper == other.upper

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    calls = []
    monkeypatch.setattr(interpretation, "_update_rule_trace", lambda *a, **k: calls.append(a))

    l = label.Label("L")
    p2 = label.Label("L2")
    p3 = label.Label("L3")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {}
    ipl = [(l, p2), (p3, l)]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.1, 0.2)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=True,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=["f"],
        rule_trace_atoms=[],
        store_interpretation_changes=True,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_edge(**kwargs)
    assert updated is True
    assert predicate_map[l] == ["e1"]
    assert predicate_map[p2] == ["e1"]
    assert predicate_map[p3] == ["e1"]
    world = interpretations["e1"].world
    assert p2 in world and p3 in world
    assert {entry[3] for entry in kwargs["rule_trace"]} == {l, p2, p3}
    assert len(calls) == 3
    if "num_ga" in sig.parameters:
        assert kwargs["num_ga"][0] == 1


def test_update_edge_complement_existing_predicate(monkeypatch, helpers_fixture):
    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

    class SimpleWorld:
        def __init__(self):
            self.world = {}

        def update(self, label, bnd):
            if label in self.world:
                w = self.world[label]
                lower = max(w.lower, bnd.lower)
                upper = min(w.upper, bnd.upper)
                w.set_lower_upper(lower, upper)
            else:
                self.world[label] = bnd.copy()

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    l = label.Label("L")
    p2 = label.Label("L2")
    interpretations = {"e1": SimpleWorld()}
    predicate_map = {p2: ["x"]}
    ipl = [(l, p2)]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="e1",
        na=(l, interpretation.interval.closed(0.4, 0.6)),
        ipl=ipl,
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    updated, _ = update_edge(**kwargs)
    assert updated is True
    assert predicate_map[p2] == ["x", "e1"]
    assert p2 in interpretations["e1"].world


def test_update_edge_missing_world(monkeypatch, helpers_fixture):
    interpretation = helpers_fixture.interpretation
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation_fp lacks error handling branch")

    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0, static=False):
            self.lower = lower
            self.upper = upper
            self.prev_lower = lower
            self.prev_upper = upper
            self._static = static

        def copy(self):
            return SimpleInterval(self.lower, self.upper, self._static)

        def set_lower_upper(self, l, u):
            self.prev_lower = self.lower
            self.prev_upper = self.upper
            self.lower = l
            self.upper = u

        def set_static(self, s):
            self._static = s

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)
    kwargs = dict(
        interpretations={},
        predicate_map={},
        comp="missing",
        na=(label.Label("L"), interpretation.interval.closed(0, 1)),
        ipl=[],
        rule_trace=[],
        fp_cnt=0,
        t_cnt=0,
        static=False,
        convergence_mode="perfect_convergence",
        atom_trace=False,
        save_graph_attributes_to_rule_trace=False,
        rules_to_be_applied_trace=[],
        idx=0,
        facts_to_be_applied_trace=[],
        rule_trace_atoms=[],
        store_interpretation_changes=False,
        mode="fact",
        override=False,
    )
    if "num_ga" in sig.parameters:
        kwargs["num_ga"] = [0]

    assert update_edge(**kwargs) == (False, 0)


def test_add_edge_existing_predicate_map_append(monkeypatch, helpers_fixture):
    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label

    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0):
            self.lower = lower
            self.upper = upper

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())

    l = label.Label("L")
    l.value = l.get_value()
    source, target = "s", "t"
    edge = (source, target)
    neighbors = {source: [target], target: []}
    reverse_neighbors = {source: [], target: [source]}
    nodes = [source, target]
    edges = [edge]
    interpretations_node = {}

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    interpretations_edge = {edge: SimpleWorld()}
    predicate_map = {l: [("x", "y")]}

    returned_edge, new_edge = helpers_fixture.add_edge(
        source,
        target,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        l,
        interpretations_node,
        interpretations_edge,
        predicate_map,
        0,
    )

    assert returned_edge == edge
    assert new_edge is True
    assert l in interpretations_edge[edge].world
    assert predicate_map[l][0] == ("x", "y")
    assert predicate_map[l][1] == edge


def test_add_edge_existing_creates_predicate_map_entry(monkeypatch, helpers_fixture):
    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label

    class SimpleInterval:
        def __init__(self, lower=0.0, upper=1.0):
            self.lower = lower
            self.upper = upper

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())

    l = label.Label("L")
    l.value = l.get_value()
    source, target = "s", "t"
    edge = (source, target)
    neighbors = {source: [target], target: []}
    reverse_neighbors = {source: [], target: [source]}
    nodes = [source, target]
    edges = [edge]
    interpretations_node = {}

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    interpretations_edge = {edge: SimpleWorld()}
    predicate_map = {}

    returned_edge, new_edge = helpers_fixture.add_edge(
        source,
        target,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        l,
        interpretations_node,
        interpretations_edge,
        predicate_map,
        0,
    )

    assert returned_edge == edge
    assert new_edge is True
    assert l in interpretations_edge[edge].world
    assert predicate_map[l] == [edge]
