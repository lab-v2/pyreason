import pytest
from unittest.mock import Mock

pytestmark = pytest.mark.usefixtures("helpers_fixture")


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
