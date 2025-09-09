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
