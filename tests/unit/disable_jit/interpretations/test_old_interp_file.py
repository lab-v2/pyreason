import pytest
from unittest.mock import Mock

pytestmark = pytest.mark.usefixtures("helpers_fixture")

# These tests are desinged to test branches and functions defined in interpretation.py that do not exist in interpretation_fp.py.
def test_reason_resets_non_persistent(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    class ResetInterval:
        def __init__(self):
            self.reset_called = False

        def copy(self):
            return ResetInterval()

        def is_static(self):
            return False

        def reset(self):
            self.reset_called = True

    bnd = ResetInterval()
    reason_env["interpretations_node"][0][reason_env["node"]].world[reason_env["label"]] = bnd

    reason_env["run"](prev_reasoning_data=[1, 0], tmax=1)

    assert bnd.reset_called


def test_reason_counts_node_rule_changes(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    def _updater(interp, predicate_map, comp, lb, *a, **k):
        l, b = lb
        interp[comp].world[l] = b
        return True, 1

    mock_update = Mock(side_effect=_updater)
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["rules_to_be_applied_node"].append((0, reason_env["node"], reason_env["label"], reason_env["bnd"], False))

    fp, _ = reason_env["run"](convergence_mode="delta_interpretation", convergence_delta=0)

    assert fp == 1
    mock_update.assert_called_once()


@pytest.mark.parametrize("consistent", [True, False])
def test_reason_edge_rule_consistency(monkeypatch, reason_env, consistent):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    edge = (reason_env["node"], "n2")
    reason_env["edges"].append(edge)
    reason_env["interpretations_edge"][0][edge] = type(reason_env["interpretations_node"][0][reason_env["node"]])()
    reason_env["nodes"].append("n2")
    reason_env["neighbors"].setdefault("n2", [])
    reason_env["reverse_neighbors"].setdefault("n2", [])

    monkeypatch.setattr(interpretation, "_add_edges", Mock(return_value=([], 0)))
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: consistent)
    mock_update = Mock(return_value=(True, 1))
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["rules_to_be_applied_edge"].append((0, edge, reason_env["label"], reason_env["bnd"], False))
    class DummyLabel:
        def __init__(self, value=""):
            self.value = value

    reason_env["edges_to_be_added_edge_rule"].append(([], [], DummyLabel()))

    reason_env["run"](convergence_mode="delta_interpretation", convergence_delta=0)

    assert mock_update.call_count == 1
    if consistent:
        assert mock_update.call_args.kwargs.get("override", False) is False
    else:
        assert mock_update.call_args.kwargs.get("override") is True


def test_reason_resets_edge_non_persistent(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    class ResetInterval:
        def __init__(self):
            self.reset_called = False

        def copy(self):
            return ResetInterval()

        def is_static(self):
            return False

        def reset(self):
            self.reset_called = True

    edge = (reason_env["node"], "n2")
    reason_env["edges"].append(edge)
    world = type(reason_env["interpretations_node"][0][reason_env["node"]])()
    bnd = ResetInterval()
    world.world[reason_env["label"]] = bnd
    reason_env["interpretations_edge"][0][edge] = world

    reason_env["run"](prev_reasoning_data=[1, 0], tmax=1)

    assert bnd.reset_called


def test_reason_delta_bound_convergence(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    edge = (reason_env["node"], "n2")
    reason_env["edges"].append(edge)
    reason_env["interpretations_edge"][0][edge] = type(reason_env["interpretations_node"][0][reason_env["node"]])()
    reason_env["nodes"].append("n2")
    reason_env["neighbors"].setdefault("n2", [])
    reason_env["reverse_neighbors"].setdefault("n2", [])

    monkeypatch.setattr(interpretation, "_add_edges", Mock(return_value=([], 0)))
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)
    mock_update = Mock(return_value=(True, 0.5))
    monkeypatch.setattr(interpretation, "_update_edge", mock_update)

    reason_env["rules_to_be_applied_edge"].append((0, edge, reason_env["label"], reason_env["bnd"], False))

    class DummyLabel:
        def __init__(self, value=""):
            self.value = value

    reason_env["edges_to_be_added_edge_rule"].append(([], [], DummyLabel()))

    fp, t = reason_env["run"](
        convergence_mode="delta_bound", convergence_delta=1, tmax=5
    )

    assert (fp, t) == (1, 1)
    mock_update.assert_called_once()


def test_reason_atom_trace_creates_trace_lists(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    mock_update = Mock(return_value=(True, 1))
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["rules_to_be_applied_node"].append(
        (0, reason_env["node"], reason_env["label"], reason_env["bnd"], False)
    )
    reason_env["rules_to_be_applied_node_trace"].append(([], [], "r"))

    class Rule:
        def get_delta(self):
            return 0

    reason_env["rules"] = [Rule()]
    mock_ground = Mock(return_value=([], []))
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)

    fp, _ = reason_env["run"](
        atom_trace=True,
        convergence_mode="delta_interpretation",
        convergence_delta=0,
    )

    assert fp == 1
    mock_ground.assert_called_once()


def test_reason_skips_rule_grounding_when_out_of_time(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["rules_to_be_applied_node"].append(
        (0, reason_env["node"], reason_env["label"], reason_env["bnd"], False)
    )

    class Rule:
        def get_delta(self):
            return 1

    reason_env["rules"] = [Rule()]
    mock_ground = Mock(return_value=([], []))
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)

    reason_env["run"](tmax=0, convergence_mode="delta_interpretation", convergence_delta=0)

    mock_ground.assert_not_called()


def test_reason_applies_applicable_node_rule_with_trace_and_delta_zero(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    class Rule:
        def get_delta(self):
            return 0

        def get_target(self):
            return reason_env["label"]

        def is_static_rule(self):
            return False

        def get_name(self):
            return "r"

        def get_weights(self):
            return ()

    rule = Rule()
    reason_env["rules"] = [rule]

    applicable_rule = (reason_env["node"], [], [], [], None)
    mock_ground = Mock(side_effect=[([applicable_rule], []), ([], [])])
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)
    monkeypatch.setattr(interpretation, "annotate", Mock(return_value=(0.0, 1.0)))
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u, static=False: reason_env["bnd"].copy())

    fp, _ = reason_env["run"](
        atom_trace=True,
        convergence_mode="delta_interpretation",
        convergence_delta=0,
    )

    assert fp == 2
    assert mock_ground.call_count == 2
    assert mock_update.call_count == 2
    # _ground_rule receives atom_trace flag enabling trace list updates
    assert mock_ground.call_args_list[0].args[9] is True



def test_reason_skips_static_node_rule(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    reason_env["facts_to_be_applied_node"].clear()
    other_label = type(reason_env["label"])("L2")
    reason_env["facts_to_be_applied_node"].append((0, reason_env["node"], other_label, reason_env["bnd"], False, False))
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    static_bnd = reason_env["bnd"].copy()
    static_bnd._static = True
    reason_env["interpretations_node"][0][reason_env["node"]].world[reason_env["label"]] = static_bnd

    class Rule:
        def get_delta(self):
            return 1

        def get_target(self):
            return reason_env["label"]

        def is_static_rule(self):
            return False

        def get_name(self):
            return "r"

        def get_weights(self):
            return ()

    reason_env["rules"] = [Rule()]
    applicable_rule = (reason_env["node"], [], [], [], None)
    monkeypatch.setattr(interpretation, "_ground_rule", Mock(return_value=([applicable_rule], [])))
    mock_annotate = Mock(return_value=(0.0, 1.0))
    monkeypatch.setattr(interpretation, "annotate", mock_annotate)
    mock_update = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_node", mock_update)

    reason_env["run"](convergence_mode="delta_interpretation", convergence_delta=0)

    mock_annotate.assert_not_called()
    assert mock_update.call_count == 1
    assert mock_update.call_args.kwargs["mode"] == "fact"


def test_reason_applies_applicable_edge_rule_with_trace_and_delta_zero(monkeypatch, reason_env):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    node = reason_env["node"]
    other = "n2"
    edge = (node, other)
    reason_env["nodes"].append(other)
    reason_env["edges"].append(edge)
    reason_env["neighbors"].setdefault(other, [])
    reason_env["reverse_neighbors"].setdefault(other, [])

    world_cls = type(reason_env["interpretations_node"][0][node])
    interval_cls = type(reason_env["bnd"])

    def _add_edges_stub(
        sources,
        targets,
        neighbors,
        reverse_neighbors,
        nodes,
        edges_list,
        edge_l,
        interp_node_t,
        interp_edge_t,
        predicate_map_edge,
        *rest,
    ):
        e = (sources[0], targets[0])
        world = world_cls()
        world.world[edge_l] = interval_cls(0, False)
        interp_edge_t[e] = world
        edges_list.append(e)
        return [e], 0

    monkeypatch.setattr(interpretation, "_add_edges", _add_edges_stub)
    monkeypatch.setattr(interpretation, "check_consistent_edge", lambda *a, **k: True)
    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)
    mock_update_edge = Mock(return_value=(True, 0))
    monkeypatch.setattr(interpretation, "_update_edge", mock_update_edge)
    monkeypatch.setattr(interpretation, "_update_node", Mock(return_value=(True, 0)))

    edge_lbl = FakeLabel("E")

    class Rule:
        def __init__(self, delta):
            self._delta = delta

        def get_delta(self):
            return self._delta

        def get_target(self):
            return edge_lbl

        def is_static_rule(self):
            return False

        def get_name(self):
            return "r"

        def get_weights(self):
            return ()

    rule1 = Rule(0)
    rule2 = Rule(1)
    reason_env["rules"] = [rule1, rule2]

    edges_to_add = ([node], [other], edge_lbl)
    applicable_edge_rule = (edge, [], [], [], edges_to_add)
    mock_ground = Mock(
        side_effect=[
            ([], [applicable_edge_rule]),
            ([], []),
            ([], []),
            ([], []),
        ]
    )
    monkeypatch.setattr(interpretation, "_ground_rule", mock_ground)
    monkeypatch.setattr(interpretation, "annotate", Mock(return_value=(0.0, 1.0)))
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u, static=False: reason_env["bnd"].copy())

    fp, _ = reason_env["run"](
        atom_trace=True,
        convergence_mode="delta_interpretation",
        convergence_delta=0,
    )

    assert fp == 2
    assert mock_ground.call_count == 2
    assert mock_ground.call_args_list[0].args[9] is True
    assert mock_update_edge.call_count == 1


def test_reason_verbose_prints_convergence(monkeypatch, reason_env, capsys):
    """Ensure verbose flag triggers convergence message."""
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    monkeypatch.setattr(interpretation, "check_consistent_node", lambda *a, **k: True)

    reason_env["run"](verbose=True)

    assert "Converged at time:" in capsys.readouterr().out


def test_get_num_ground_atoms_trims_trailing_zero():
    """get_num_ground_atoms removes a trailing zero and returns list."""
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    interp_cls = interpretation.Interpretation
    obj = interp_cls.__new__(interp_cls)

    obj.num_ga = [1, 0]
    assert obj.get_num_ground_atoms() == [1]

    obj.num_ga = [1, 2]
    assert obj.get_num_ground_atoms() == [1, 2]


@pytest.mark.parametrize(
    "quantifier, threshold, expected",
    [
        ("total", ("greater_equal", ("number", "total"), 2), False),
        ("available", ("greater_equal", ("number", "available"), 1), True),
    ],
)
def test_check_edge_grounding_threshold_satisfaction_branches(
    monkeypatch, quantifier, threshold, expected
):
    if interpretation.__name__.endswith("interpretation_fp"):
        pytest.skip("interpretation backend only")

    monkeypatch.setattr(
        interpretation.interval, "closed", lambda *a, **k: object()
    )

    class World:
        def __init__(self, sat):
            self._sat = sat

        def is_satisfied(self, _l, _b):
            return self._sat

    edge1 = ("n1", "n2")
    edge2 = ("n1", "n3")
    interpretations_edge = {edge1: World(True), edge2: World(False)}
    grounding = [edge1, edge2]
    qualified_grounding = [edge1]

    l = label.Label("L")

    result = check_edge_grounding_threshold_satisfaction(
        interpretations_edge, grounding, qualified_grounding, l, threshold
    )

    assert result is expected
