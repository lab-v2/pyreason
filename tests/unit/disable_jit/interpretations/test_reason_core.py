import pytest
from unittest.mock import Mock, call
import inspect

pytestmark = pytest.mark.usefixtures("helpers_fixture")
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


def test_reason_inconsistent_counts_changes(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 1

    mock_update = Mock(side_effect=_updater)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["run"](
        inconsistency_check=False,
        convergence_mode="delta_interpretation",
        convergence_delta=0,
    )

    assert mock_update.called


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
    if interpretation.__name__.endswith("interpretation"):
        pytest.skip("convergence semantics differ in interpretation backend")
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
        "head_functions": (),
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
            params["head_functions"],
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
    if interpretation.__name__.endswith("interpretation"):
        pytest.skip("no-update behavior differs for interpretation backend")
    fp, max_t = reason_env["run"](
        facts_to_be_applied_node=[],
        convergence_mode="delta_bound",
        convergence_delta=-1,
    )
    assert fp == 1 and max_t == 1


@pytest.mark.parametrize("persistent", [True, False])
def test_reason_copies_previous_timestep(monkeypatch, persistent):
    if interpretation.__name__.endswith("interpretation"):
        pytest.skip("interpretation backend lacks timestep copying")
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

    def fake_add_edge(
        s,
        t,
        nbrs,
        rev,
        nodes,
        edges_list,
        l,
        interp_node,
        interp_edge,
        pred_map,
        *rest,
    ):
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
    if not hasattr(interpretation, "_add_edge_to_interpretation"):
        pytest.skip("backend lacks _add_edge_to_interpretation")
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


def test_reason_edge_inconsistency_delta_bound_override(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (True, 0))
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: world}}
    edges = [edge]

    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)

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
        inconsistency_check=False,
        prev_reasoning_data=[0, 1],
    )

    assert fp == 2


def test_reason_edge_rule_updates_added_edges(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    bnd = reason_env["bnd"]
    edge_lbl = FakeLabel("E")

    world_cls = reason_env["interpretations_node"][0][node].__class__

    def _add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = bnd.__class__(0, False)
        interp_edge_t[e] = world
        edges.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", _add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["run"](
        edges=[],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, reason_env["label"], bnd, False)],
        edges_to_be_added_edge_rule=[([node], [node], edge_lbl)],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
    )

    mock_update.assert_called_once()


def test_reason_edge_rule_resolves_inconsistency(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: world}}
    edges = [edge]

    monkeypatch.setattr(interpretation, "_add_edges", lambda *a, **k: ([], 0))
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)
    mock_resolve = Mock()
    mock_update = Mock()
    monkeypatch.setattr(interpretation, "resolve_inconsistency_edge", mock_resolve)
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        rules_to_be_applied_edge=[(0, edge, lbl, bnd, False)],
        edges_to_be_added_edge_rule=[([], [], FakeLabel(""))],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
        inconsistency_check=True,
    )

    mock_resolve.assert_called_once()
    mock_update.assert_not_called()


def test_reason_edge_rule_inconsistency_delta_bound_override(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world = reason_env["interpretations_node"][0][node].__class__()
    interpretations_edge = {0: {edge: world}}
    edges = [edge]

    monkeypatch.setattr(interpretation, "_add_edges", lambda *a, **k: ([], 0))
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)

    def _update_edge_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0.5

    mock_update = Mock(side_effect=_update_edge_stub)
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    fp, _ = reason_env["run"](
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        rules_to_be_applied_edge=[(0, edge, lbl, bnd, False)],
        edges_to_be_added_edge_rule=[([], [], FakeLabel(""))],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
        inconsistency_check=False,
    )

    assert fp == 1
    assert mock_update.call_args[1]["override"] is True


def test_reason_skips_rule_outside_tmax(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (True, 0))
    rule = Mock()
    rule.get_delta.return_value = 1
    rule.get_target.return_value = reason_env["label"]
    rule.is_static_rule.return_value = False
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_bnd.return_value = Mock(lower=0, upper=1)

    mock_ground = Mock(return_value=([], []))
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)

    fp, _ = reason_env["run"](rules=[rule], tmax=0)

    assert fp == 1
    mock_ground.assert_not_called()





def test_reason_node_rule_delta_zero_traces_and_applies(monkeypatch, reason_env):
    if not hasattr(interpretation, "_add_node_to_interpretation"):
        pytest.skip("backend lacks _add_node_to_interpretation")
    monkeypatch.setattr(interpretation, "annotate", lambda *a, **k: (0, 1))
    monkeypatch.setattr(
        interpretation.interval,
        "closed",
        lambda lo, up: reason_env["bnd"].__class__(lo, False),
    )

    new_node = "n2"
    rule = Mock()
    rule.get_delta.return_value = 0
    rule.get_target.return_value = reason_env["label"]
    rule.is_static_rule.return_value = False
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_name.return_value = "r"

    ground_calls = {"n": 0}

    def ground_rule_stub(*args, **kwargs):
        ground_calls["n"] += 1
        if ground_calls["n"] == 1:
            return ([(new_node, [], ["qn"], ["qe"], None)], [])
        return ([], [])

    monkeypatch.setattr(interpretation, "_ground_rule", ground_rule_stub)

    world_cls = reason_env["interpretations_node"][0][reason_env["node"]].__class__

    def add_node_to_interp(comp, interp_dict):
        interp_dict[comp] = world_cls()

    mock_add = Mock(side_effect=add_node_to_interp)
    monkeypatch.setattr(interpretation, "_add_node_to_interpretation", mock_add)
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    def update_node_stub(
        interp,
        predicate_map,
        comp,
        lb,
        ipl,
        rule_trace_node,
        fp_cnt,
        t,
        set_static,
        convergence_mode,
        atom_trace,
        save_graph,
        rules_trace,
        idx,
        facts_trace,
        rule_trace_node_atoms,
        store_changes,
        mode="rule",
        override=False,
    ):
        assert rules_trace[idx] == (["qn"], ["qe"], "r")
        l, b = lb
        interp[comp].world[l] = b
        return True, 1

    mock_update = Mock(side_effect=update_node_stub)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    rules_list = []
    trace_list = []
    fp, max_t = reason_env["run"](
        rules=[rule],
        atom_trace=True,
        rules_to_be_applied_node=rules_list,
        rules_to_be_applied_node_trace=trace_list,
        facts_to_be_applied_node=[],
    )

    assert ground_calls["n"] == 2
    assert mock_add.called
    assert mock_update.called
    assert new_node in reason_env["interpretations_node"][0]
    assert rules_list == [] and trace_list == []
    assert fp == 1 and max_t == 1


def test_reason_node_rule_skips_when_static(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation"):
        pytest.skip("static rule handling differs in interpretation backend")
    monkeypatch.setattr(interpretation, "annotate", lambda *a, **k: (0, 1))
    monkeypatch.setattr(
        interpretation.interval,
        "closed",
        lambda lo, up: reason_env["bnd"].__class__(lo, False),
    )

    node = reason_env["node"]
    lbl = reason_env["label"]
    reason_env["interpretations_node"][0][node].world[lbl] = reason_env["bnd"].__class__(
        1.0, True
    )

    rule = Mock()
    rule.get_delta.return_value = 0
    rule.get_target.return_value = lbl
    rule.is_static_rule.return_value = False
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_name.return_value = "r"

    mock_ground = Mock(return_value=([(node, [], [], [], None)], []))
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)

    rules_list = []
    trace_list = []
    reason_env["run"](
        rules=[rule],
        atom_trace=True,
        rules_to_be_applied_node=rules_list,
        rules_to_be_applied_node_trace=trace_list,
        facts_to_be_applied_node=[],
        prev_reasoning_data=[0, 1],
    )

    assert mock_ground.call_count == 1
    assert rules_list == [] and trace_list == []


def test_reason_node_rule_resolves_inconsistency(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "annotate", lambda *a, **k: (0, 1))
    monkeypatch.setattr(
        interpretation.interval,
        "closed",
        lambda lo, up: reason_env["bnd"].__class__(lo, False),
    )

    rule = Mock()
    rule.get_delta.return_value = 1
    rule.get_target.return_value = reason_env["label"]
    rule.is_static_rule.return_value = False
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_name.return_value = "r"

    monkeypatch.setattr(
        interpretation, "_ground_rule", lambda *a, **k: ([(reason_env["node"], [], [], [], None)], [])
    )
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)

    mock_resolve = Mock()
    monkeypatch.setattr(interpretation, "resolve_inconsistency_node", mock_resolve)
    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["run"](rules=[rule], inconsistency_check=True)

    assert mock_resolve.called
    assert not mock_update.called


def test_reason_node_rule_delta_bound(monkeypatch, reason_env):
    """Ensure rule applications update delta-bound convergence metrics."""

    node = reason_env["node"]
    lbl = reason_env["label"]
    rule_entry = (0, node, lbl, reason_env["bnd"], False)

    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 0.5

    mock_update = Mock(side_effect=_updater)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    fp, _ = reason_env["run"](
        rules_to_be_applied_node=[rule_entry],
        rules_to_be_applied_node_trace=[],
        facts_to_be_applied_node=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
    )

    assert fp == 1
    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs.get("override", False) is False


@pytest.mark.parametrize("mode", ["delta_bound", "delta_interpretation"])
def test_reason_node_rule_inconsistent_override(monkeypatch, reason_env, mode):
    """Inconsistent rules override bounds and update convergence counters."""

    node = reason_env["node"]
    lbl = reason_env["label"]
    rule_entry = (0, node, lbl, reason_env["bnd"], False)

    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 0.5

    mock_update = Mock(side_effect=_updater)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    fp, _ = reason_env["run"](
        rules_to_be_applied_node=[rule_entry],
        rules_to_be_applied_node_trace=[],
        facts_to_be_applied_node=[],
        inconsistency_check=False,
        convergence_mode=mode,
        convergence_delta=0,
    )

    mock_update.assert_called_once()
    assert mock_update.call_args.kwargs.get("override") is True
    assert fp == 1

def test_reason_edge_rule_records_trace(monkeypatch, reason_env):
    if not hasattr(interpretation, "_add_edge_to_interpretation"):
        pytest.skip("backend lacks _add_edge_to_interpretation")
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (True, 0))
    monkeypatch.setattr(interpretation, "annotate", lambda *a, **k: (0, 1))
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: reason_env["bnd"].__class__(lo, False))
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    interpretations_edge = {0: {}}
    edges = [edge]

    rule = Mock()
    rule.get_delta.return_value = 1
    rule.get_target.return_value = lbl
    rule.is_static_rule.return_value = False
    rule.get_name.return_value = "r"
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_bnd.return_value = Mock(lower=0, upper=1)

    edge_placeholder = type("EL", (), {"value": ""})()
    applicable = [(edge, [], [node], [edge], ([], [], edge_placeholder))]
    monkeypatch.setattr(interpretation, "_ground_rule", lambda *a, **k: ([], applicable))

    def add_edge_to_interp(comp, interp_edge):
        interp_edge[comp] = type("W", (), {"world": {}})()

    monkeypatch.setattr(interpretation, "_add_edge_to_interpretation", add_edge_to_interp)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    captured = {}

    def update_edge_stub(*args, **kwargs):
        rt_trace = args[12]
        idx = args[13]
        captured["trace"] = rt_trace[idx]
        return False, 0

    monkeypatch.setattr(interpretation, "_update_edge", update_edge_stub)

    reason_env["run"](
        rules=[rule],
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        atom_trace=True,
        tmax=1,
    )

    assert captured["trace"] == ([node], [edge], "r")


def test_reason_edge_rule_delta_zero_applies(monkeypatch, reason_env):
    if not hasattr(interpretation, "_add_edge_to_interpretation"):
        pytest.skip("backend lacks _add_edge_to_interpretation")
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (True, 0))
    monkeypatch.setattr(interpretation, "annotate", lambda *a, **k: (0, 1))
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: reason_env["bnd"].__class__(lo, False))
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    interpretations_edge = {0: {}}
    edges = [edge]

    rule = Mock()
    rule.get_delta.return_value = 0
    rule.get_target.return_value = lbl
    rule.is_static_rule.return_value = False
    rule.get_weights.return_value = []
    rule.get_annotation_function.return_value = ""
    rule.get_bnd.return_value = Mock(lower=0, upper=1)

    edge_placeholder = type("EL", (), {"value": ""})()
    applicable = [(edge, [], [], [], ([], [], edge_placeholder))]
    monkeypatch.setattr(interpretation, "_ground_rule", lambda *a, **k: ([], applicable))

    def add_edge_to_interp(comp, interp_edge):
        interp_edge[comp] = type("W", (), {"world": {}})()

    monkeypatch.setattr(interpretation, "_add_edge_to_interpretation", add_edge_to_interp)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    called = {}

    def update_edge_stub(*a, **k):
        called["ok"] = True
        return False, 0

    monkeypatch.setattr(interpretation, "_update_edge", update_edge_stub)

    reason_env["run"](
        rules=[rule],
        edges=edges,
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge=interpretations_edge,
        tmax=0,
    )

    assert called.get("ok")


def test_reason_node_rule_resolve_inconsistency_list(monkeypatch, reason_env):
    entry = (0, reason_env["node"], reason_env["label"], reason_env["bnd"], False)
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: False)

    def resolve_stub(interp, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b

    mock_resolve = Mock(side_effect=resolve_stub)
    monkeypatch.setattr(interpretation, "resolve_inconsistency_node", mock_resolve)
    monkeypatch.setattr(interpretation, "_update_node", Mock())

    reason_env["run"](
        rules_to_be_applied_node=[entry],
        rules_to_be_applied_node_trace=[],
        facts_to_be_applied_node=[],
        inconsistency_check=True,
    )

    mock_resolve.assert_called_once()
    interpretation._update_node.assert_not_called()


def test_reason_edge_rule_skips_static_added_edge(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    edge_lbl = FakeLabel("E")
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    def add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = bnd.__class__(1.0, True)
        interp_edge_t[e] = world
        edges.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)
    mock_update = Mock()
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)
    mock_resolve = Mock()
    monkeypatch.setattr(interpretation, "resolve_inconsistency_edge", mock_resolve)

    reason_env["run"](
        edges=[],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, reason_env["label"], bnd, False)],
        edges_to_be_added_edge_rule=[([node], [node], edge_lbl)],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
    )

    mock_update.assert_not_called()
    mock_resolve.assert_not_called()


def test_reason_edge_rule_delta_bound_added_edge(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    edge_lbl = FakeLabel("E")
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    def add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = bnd.__class__(0.0, False)
        interp_edge_t[e] = world
        edges.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    def update_edge_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0.5

    mock_update = Mock(side_effect=update_edge_stub)
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    fp, _ = reason_env["run"](
        edges=[],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, reason_env["label"], bnd, False)],
        edges_to_be_added_edge_rule=[([node], [node], edge_lbl)],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
    )

    assert fp == 1
    mock_update.assert_called_once()


@pytest.mark.parametrize("inconsistency_check", [True, False])
def test_reason_edge_rule_added_inconsistency(monkeypatch, reason_env, inconsistency_check):
    node = reason_env["node"]
    edge = (node, node)
    edge_lbl = FakeLabel("E")
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    def add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = bnd.__class__(0.0, False)
        interp_edge_t[e] = world
        edges.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)
    mock_resolve = Mock()
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "resolve_inconsistency_edge", mock_resolve)
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["run"](
        edges=[],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, reason_env["label"], bnd, False)],
        edges_to_be_added_edge_rule=[([node], [node], edge_lbl)],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
        inconsistency_check=inconsistency_check,
    )

    if inconsistency_check:
        assert mock_resolve.called
        assert not mock_update.called
    else:
        assert mock_update.called
        assert mock_update.call_args.kwargs.get("override") is True
        assert not mock_resolve.called



def test_reason_edge_rule_added_inconsistency_delta_bound(monkeypatch, reason_env):
    node = reason_env["node"]
    edge = (node, node)
    edge_lbl = FakeLabel("E")
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    def add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = bnd.__class__(0.0, False)
        interp_edge_t[e] = world
        edges.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)

    def update_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0.5

    monkeypatch.setattr(interpretation, "_update_edge", update_stub)

    fp, _ = reason_env["run"](
        edges=[],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, reason_env["label"], bnd, False)],
        edges_to_be_added_edge_rule=[([node], [node], edge_lbl)],
        facts_to_be_applied_node=[],
        facts_to_be_applied_edge=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
        inconsistency_check=False,
    )

    assert fp == 1


def test_reason_edge_rule_existing_edge_delta_bound(monkeypatch, reason_env):
    if not hasattr(interpretation, "_add_edge_to_interpretation"):
        pytest.skip("backend lacks _add_edge_to_interpretation")
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    monkeypatch.setattr(interpretation, "_add_edges", lambda *a, **k: ([], 0))

    def add_edge_interp(comp, interp_edge):
        interp_edge[comp] = world_cls()

    monkeypatch.setattr(interpretation, "_add_edge_to_interpretation", add_edge_interp)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)

    def update_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 0.5

    monkeypatch.setattr(interpretation, "_update_edge", update_stub)

    fp, _ = reason_env["run"](
        edges=[edge],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, lbl, bnd, False)],
        edges_to_be_added_edge_rule=[([], [], FakeLabel(""))],
        facts_to_be_applied_node=[],
        convergence_mode="delta_bound",
        convergence_delta=0,
    )

    assert fp == 1


def test_reason_edge_rule_existing_inconsistent_counts(monkeypatch, reason_env):
    if not hasattr(interpretation, "_add_edge_to_interpretation"):
        pytest.skip("backend lacks _add_edge_to_interpretation")
    node = reason_env["node"]
    edge = (node, node)
    lbl = reason_env["label"]
    bnd = reason_env["bnd"]
    world_cls = reason_env["interpretations_node"][0][node].__class__

    monkeypatch.setattr(interpretation, "_add_edges", lambda *a, **k: ([], 0))

    def add_edge_interp(comp, interp_edge):
        interp_edge[comp] = world_cls()

    monkeypatch.setattr(interpretation, "_add_edge_to_interpretation", add_edge_interp)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: False)

    def update_stub(interp, predicate_map, comp, lb, *a, **k):
        l, bound = lb
        interp[comp].world[l] = bound
        return True, 1

    monkeypatch.setattr(interpretation, "_update_edge", update_stub)

    fp, _ = reason_env["run"](
        edges=[edge],
        neighbors={node: []},
        reverse_neighbors={node: []},
        interpretations_edge={0: {}},
        rules_to_be_applied_edge=[(0, edge, lbl, bnd, False)],
        edges_to_be_added_edge_rule=[([], [], FakeLabel(""))],
        facts_to_be_applied_node=[],
        convergence_mode="delta_interpretation",
        convergence_delta=0,
        inconsistency_check=False,
    )

    assert fp == 1


def test_reason_breaks_on_delta_interpretation(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (False, 0))
    printed = []
    monkeypatch.setattr(
        "builtins.print", lambda *a, **k: printed.append(" ".join(map(str, a)))
    )

    fp, max_t = reason_env["run"](
        convergence_mode="delta_interpretation",
        convergence_delta=0,
        verbose=True,
    )

    assert fp == 0 and max_t == 1
    assert any("Converged at time" in line for line in printed)


def test_reason_breaks_on_delta_bound(monkeypatch, reason_env):
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "_update_node", lambda *a, **k: (False, 0))
    printed = []
    monkeypatch.setattr(
        "builtins.print", lambda *a, **k: printed.append(" ".join(map(str, a)))
    )

    fp, max_t = reason_env["run"](
        convergence_mode="delta_bound", convergence_delta=0, verbose=True
    )

    assert fp == 0 and max_t == 1
    assert any("Converged at time" in line for line in printed)


def test_reason_breaks_on_perfect_convergence(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation"):
        pytest.skip("perfect convergence logging differs in interpretation backend")
    printed = []
    monkeypatch.setattr(
        "builtins.print", lambda *a, **k: printed.append(" ".join(map(str, a)))
    )

    fp, max_t = reason_env["run"](
        facts_to_be_applied_node=[],
        convergence_mode="perfect_convergence",
        verbose=True,
    )

    assert fp == 0 and max_t == 1
    assert any("Converged at fp" in line for line in printed)
