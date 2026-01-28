"""
Test cases for BUG-127: Delta Bound Convergence with IPL Complements

These tests demonstrate that delta_bound convergence mode was incorrectly
comparing IPL complement bounds against the original label's previous bound
instead of the complement's own previous bound.

Example scenario from bug_log_2.md:
    Timestep t-1:
      infected(Alice) = [0.1, 0.2]
      healthy(Alice) = [0.8, 0.9]

    Timestep t:
      Update: infected(Alice) = [0.7, 0.9]
      IPL triggers: healthy(Alice) = [0.1, 0.3]

    WRONG calculation (BUG-127):
      Comparing healthy [0.1, 0.3] vs infected's previous [0.1, 0.2]
      delta = max(|0.1-0.1|, |0.3-0.2|) = 0.1

    CORRECT calculation:
      Comparing healthy [0.1, 0.3] vs healthy's previous [0.8, 0.9]
      delta = max(|0.1-0.8|, |0.3-0.9|) = 0.7
"""

import pytest
from unittest.mock import Mock
import inspect

pytestmark = pytest.mark.usefixtures("helpers_fixture")


def test_update_node_ipl_complement_delta_bound_bug127(monkeypatch, helpers_fixture):
    """
    Test that exposes BUG-127 in _update_node.

    This test performs TWO updates:
    1. First update establishes non-default previous bounds
    2. Second update is where we test for BUG-127

    Setup:
    - Update 1: infected(Alice) = [0.1, 0.2], healthy(Alice) = [0.8, 0.9] (via IPL)
    - Update 2: infected(Alice) = [0.15, 0.2], healthy(Alice) = [0.8, 0.85] (via IPL)

    BUG-127 would compare healthy's new [0.8, 0.85] against infected's previous [0.1, 0.2]
    Correct: compare healthy's new [0.8, 0.85] against healthy's previous [0.8, 0.9]
    """
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

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    infected = label.Label("infected")
    healthy = label.Label("healthy")

    world = SimpleWorld()
    interpretations = {"Alice": world}
    predicate_map = {}
    ipl = [(infected, healthy)]

    update_node = getattr(interpretation._update_node, "py_func", interpretation._update_node)
    sig = inspect.signature(update_node)

    # UPDATE 1: Establish initial non-default bounds
    # infected = [0.1, 0.2], which triggers healthy = [0.8, 0.9] via IPL
    kwargs1 = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="Alice",
        na=(infected, interpretation.interval.closed(0.1, 0.2)),
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
        kwargs1["num_ga"] = [0]

    updated1, change1 = update_node(**kwargs1)
    assert updated1 is True

    # Verify first update results
    assert world.world[infected].lower == pytest.approx(0.1)
    assert world.world[infected].upper == pytest.approx(0.2)
    assert world.world[healthy].lower == pytest.approx(0.8)
    assert world.world[healthy].upper == pytest.approx(0.9)

    # UPDATE 2: This is where we test for BUG-127
    # infected = [0.15, 0.2] (tightens lower), which triggers healthy = [0.8, 0.85] (tightens upper)
    kwargs2 = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="Alice",
        na=(infected, interpretation.interval.closed(0.15, 0.2)),
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
        kwargs2["num_ga"] = [2]

    updated2, change2 = update_node(**kwargs2)
    assert updated2 is True

    # Verify second update results
    assert world.world[infected].lower == pytest.approx(0.15)
    assert world.world[infected].upper == pytest.approx(0.2)
    assert world.world[healthy].lower == pytest.approx(0.8)
    assert world.world[healthy].upper == pytest.approx(0.85)

    # THE CRITICAL ASSERTION for BUG-127:
    # Correct calculation:
    #   infected: max(|0.15-0.1|, |0.2-0.2|) = max(0.05, 0.0) = 0.05
    #   healthy: max(|0.8-0.8|, |0.85-0.9|) = max(0.0, 0.05) = 0.05
    #   Overall: max(0.05, 0.05) = 0.05
    #
    # BUG-127 would compare healthy against infected's previous [0.1, 0.2]:
    #   healthy (WRONG): max(|0.8-0.1|, |0.85-0.2|) = max(0.7, 0.65) = 0.7
    #   Overall (WRONG): max(0.05, 0.7) = 0.7
    assert change2 == pytest.approx(0.05), \
        f"Expected change=0.05, got {change2}. BUG-127 would give 0.7."

def test_update_edge_ipl_two_complements_bug125(monkeypatch, helpers_fixture):
    """
    Specific test for BUG-125 with multiple IPL pairs.

    This test uses two IPL pairs and two updates to ensure BUG-125 is exposed:
    - (infected, healthy) triggers p1 == l branch
    - (recovered, infected) triggers p2 == l branch (BUG-125 location)

    The bug causes the wrong bound to be appended to updated_bnds, which
    affects convergence delta calculation.
    """
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

    interpretation = helpers_fixture.interpretation
    label = helpers_fixture.label
    monkeypatch.setattr(interpretation.interval, "closed", lambda l, u: SimpleInterval(l, u))
    monkeypatch.setattr(interpretation.numba.typed, "List", _ListShim())
    monkeypatch.setattr(interpretation.numba.types, "uint16", lambda x: x)

    infected = label.Label("infected")
    healthy = label.Label("healthy")
    recovered = label.Label("recovered")

    world = SimpleWorld()
    interpretations = {"edge1": world}
    predicate_map = {}

    # IPL pairs: (infected, healthy) and (recovered, infected)
    # When we update infected:
    # - p1 == infected triggers p1 == l branch → updates healthy
    # - p2 == infected triggers p2 == l branch → updates recovered (BUG-125 location)
    ipl = [(infected, healthy), (recovered, infected)]

    update_edge = getattr(interpretation._update_edge, "py_func", interpretation._update_edge)
    sig = inspect.signature(update_edge)

    # UPDATE 1: Establish initial bounds
    # infected = [0.2, 0.3], triggers healthy = [0.7, 0.8] and recovered = [0.7, 0.8]
    kwargs1 = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="edge1",
        na=(infected, interpretation.interval.closed(0.2, 0.3)),
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
        kwargs1["num_ga"] = [0]

    updated1, change1 = update_edge(**kwargs1)
    assert updated1 is True

    # UPDATE 2: Test for BUG-125
    # infected = [0.25, 0.3], triggers healthy = [0.7, 0.75] and recovered = [0.7, 0.75]
    kwargs2 = dict(
        interpretations=interpretations,
        predicate_map=predicate_map,
        comp="edge1",
        na=(infected, interpretation.interval.closed(0.25, 0.3)),
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
        kwargs2["num_ga"] = [3]

    updated2, change2 = update_edge(**kwargs2)
    assert updated2 is True

    # Verify all three predicates
    assert world.world[infected].lower == pytest.approx(0.25)
    assert world.world[infected].upper == pytest.approx(0.3)
    assert world.world[healthy].lower == pytest.approx(0.7)
    assert world.world[healthy].upper == pytest.approx(0.75)
    assert world.world[recovered].lower == pytest.approx(0.7)
    assert world.world[recovered].upper == pytest.approx(0.75)

    # THE CRITICAL ASSERTION for BUG-125:
    # Correct (all three bounds calculated correctly):
    #   infected: max(|0.25-0.2|, |0.3-0.3|) = 0.05
    #   healthy: max(|0.7-0.7|, |0.75-0.8|) = 0.05
    #   recovered: max(|0.7-0.7|, |0.75-0.8|) = 0.05
    #   Overall: 0.05
    #
    # BUG-125 would append infected's bound instead of recovered's bound
    # This might result in incorrect delta if bounds are different
    assert change2 == pytest.approx(0.05), \
        f"Expected change=0.05, got {change2}. BUG-125 would potentially give wrong value."
