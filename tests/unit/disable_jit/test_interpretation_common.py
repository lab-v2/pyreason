import pytest
from unittest.mock import Mock, call
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
