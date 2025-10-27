# # tests/conftest.py
import os
os.environ["NUMBA_DISABLE_JIT"] = "1"
import numba
numba.config.DISABLE_JIT = True
import sys, types
sys.modules.setdefault("pyreason.pyreason", types.ModuleType("pyreason.pyreason"))
stub = sys.modules["pyreason.pyreason"]
stub.settings = types.SimpleNamespace()
stub.load_graphml = lambda *a, **k: None
stub.add_rule = lambda *a, **k: None
stub.add_fact = lambda *a, **k: None
stub.reason = lambda *a, **k: None
stub.reset = lambda *a, **k: None
stub.reset_rules = lambda *a, **k: None
class Rule:
    def __init__(self, *args, **kwargs):
        pass
class Fact:
    def __init__(self, *args, **kwargs):
        pass
stub.Rule = Rule
stub.Fact = Fact


import pytest
from tests.unit.disable_jit.interpretations.test_interpretation_common import get_interpretation_helpers


@pytest.fixture(params=["interpretation_fp", "interpretation"])
def helpers_fixture(request):
    h = get_interpretation_helpers(request.param)
    m = request.module
    for name in dir(h):
        if not name.startswith("_"):
            setattr(m, name, getattr(h, name))
    yield h


@pytest.fixture
def reason_env(monkeypatch, helpers_fixture):
    """Minimal environment to exercise Interpretation.reason."""

    interp = helpers_fixture.interpretation
    reason_func = helpers_fixture.reason
    lbl_mod = helpers_fixture.label

    class _ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    class _DictShim:
        def empty(self, *args, **kwargs):
            return {}

    monkeypatch.setattr(interp.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interp.numba.typed, "Dict", _DictShim())
    monkeypatch.setattr(interp.numba.types, "uint16", lambda x: x)

    class SimpleWorld:
        def __init__(self):
            self.world = {}

    class SimpleInterval:
        def __init__(self, val=1.0, static=False):
            self.val = val
            self._static = static

        def copy(self):
            return SimpleInterval(self.val, self._static)

        def is_static(self):
            return self._static

    node = "n1"
    lbl = lbl_mod.Label("L")
    bnd = SimpleInterval()

    env = {
        "interpretations_node": {0: {node: SimpleWorld()}},
        "interpretations_edge": {0: {}},
        "predicate_map_node": {},
        "predicate_map_edge": {},
        "tmax": 0,
        "prev_reasoning_data": [0, 0],
        "rules": [],
        "nodes": [node],
        "edges": [],
        "neighbors": {node: []},
        "reverse_neighbors": {node: []},
        "rules_to_be_applied_node": [],
        "rules_to_be_applied_edge": [],
        "edges_to_be_added_node_rule": [],
        "edges_to_be_added_edge_rule": [],
        "rules_to_be_applied_node_trace": [],
        "rules_to_be_applied_edge_trace": [],
        "facts_to_be_applied_node": [(0, node, lbl, bnd, False, False)],
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
        "persistent": False,
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
        return reason_func(
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
    env["node"] = node
    env["label"] = lbl
    env["bnd"] = bnd
    return env
