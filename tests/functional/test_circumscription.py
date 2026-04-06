"""Functional tests for minimized predicates (circumscription).

End-to-end tests using the full PyReason API with networkx graphs,
parametrized across regular, fp, and parallel reasoning modes.
"""
import pyreason as pr
import networkx as nx
import pytest


def setup_mode(mode):
    """Configure PyReason settings for the specified mode."""
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = True

    if mode == "fp":
        pr.settings.fp_version = True
    elif mode == "parallel":
        pr.settings.parallel_computing = True


def _build_two_node_graph():
    """Build a simple A -> B graph with a stepFrom edge."""
    g = nx.DiGraph()
    g.add_nodes_from(['A', 'B'])
    g.add_edge('A', 'B', stepFrom=1)
    return g

@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_known_bounds_bypass_minimization(mode):
    """Known [1,1] bounds on a minimized predicate should NOT be coerced to [0,0].
    A ~minimized_pred(Y) clause must therefore not fire when Y has known [1,1]."""
    setup_mode(mode)

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')

    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B)', 'hc_b_known'))  # defaults to [1,1]

    # ~hackerControl(Y) requires [0,0]. B has known [1,1] -> minimization bypassed -> rule MUST NOT fire.
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'block_rule'))

    interpretation = pr.reason(timesteps=1)

    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    for df in blocked_dfs:
        if len(df) > 0:
            assert 'B' not in df['component'].values, \
                'blocked(B) should NOT fire: known [1,1] hackerControl(B) bypasses minimization'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_vs_non_minimized_satisfaction(mode):
    """A minimized predicate with [0,1] bounds satisfies a ~pred (negated [0,0])
    clause because [0,1] is treated as [0,0]. An equivalent non-minimized predicate
    with the same [0,1] bounds does NOT satisfy the same clause."""
    setup_mode(mode)

    g = nx.DiGraph()
    g.add_nodes_from(['A', 'B'])
    g.add_edge('A', 'B', stepFrom=1)
    pr.load_graph(g)

    # hackerControl is minimized, otherPred is not
    pr.add_minimized_predicate('hackerControl')

    # Both predicates start with unknown [0,1] on B
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_fact(pr.Fact('otherPred(A)', 'op_a'))
    pr.add_fact(pr.Fact('otherPred(B):[0,1]', 'op_b_unknown'))

    # Rule using negation: ~pred requires [0,0] bounds
    # minimized hackerControl [0,1] -> [0,0] -> satisfies ~hackerControl
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'minimized_rule'))
    # Non-minimized otherPred [0,1] stays [0,1] -> does NOT satisfy ~otherPred ([0,0])
    pr.add_rule(pr.Rule('notBlocked(Y) <-1 stepFrom(X,Y), otherPred(X), ~otherPred(Y)',
                        'non_minimized_rule'))

    interpretation = pr.reason(timesteps=1)

    # Minimized: hackerControl(B) [0,1] -> [0,0] satisfies ~hackerControl -> blocked(B) fires
    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    found_blocked = False
    for df in blocked_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found_blocked = True
            break
    assert found_blocked, \
        'blocked(B) should fire: minimized hackerControl(B) [0,1] -> [0,0] satisfies ~hackerControl'

    # Non-minimized: otherPred(B) stays [0,1], does NOT satisfy ~otherPred ([0,0])
    not_blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['notBlocked'])
    for df in not_blocked_dfs:
        if len(df) > 0:
            assert 'B' not in df['component'].values, \
                'notBlocked(B) should NOT fire: non-minimized otherPred(B) [0,1] does not satisfy ~otherPred'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_predicate_multi_timestep(mode):
    """Minimization must apply at every timestep where a body clause sees an
    unknown [0,1] bound on a minimized predicate. Cascade A -> B -> C: the
    block rule must fire on B at t=1 and on C at t=2, both via minimization."""
    setup_mode(mode)

    g = nx.DiGraph()
    g.add_nodes_from(['A', 'B', 'C'])
    g.add_edge('A', 'B', stepFrom=1)
    g.add_edge('B', 'C', stepFrom=1)
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_fact(pr.Fact('hackerControl(C):[0,1]', 'hc_c_unknown'))

    # block(Y) fires when Y has minimized hackerControl ([0,1] -> [0,0])
    # and X (the source) is "active" — either has known hackerControl or is already blocked.
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'block_rule_initial'))
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), blocked(X), ~hackerControl(Y)',
                        'block_rule_cascade'))

    interpretation = pr.reason(timesteps=2)

    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    found_b = False
    found_c = False
    for df in blocked_dfs:
        if len(df) > 0:
            if 'B' in df['component'].values:
                found_b = True
            if 'C' in df['component'].values:
                found_c = True
    assert found_b, 'blocked(B) should fire at t=1 via minimization of hackerControl(B) [0,1] -> [0,0]'
    assert found_c, 'blocked(C) should fire at t=2 via minimization of hackerControl(C) [0,1] -> [0,0]'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_inconsistency_check(mode):
    """Minimization must drive a rule to fire even with inconsistency_check enabled."""
    setup_mode(mode)
    pr.settings.inconsistency_check = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'block_rule'))

    interpretation = pr.reason(timesteps=1)

    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    found = False
    for df in blocked_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found = True
            break
    assert found, 'blocked(B) should fire via minimization with inconsistency_check enabled'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_persistent_mode(mode):
    """Minimization must drive a rule to fire even with persistent bounds enabled."""
    setup_mode(mode)
    pr.settings.persistent = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'block_rule'))

    interpretation = pr.reason(timesteps=2)

    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    found = False
    for df in blocked_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found = True
            break
    assert found, 'blocked(B) should fire via minimization with persistent mode enabled'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_atom_trace(mode):
    """Minimization must drive a rule to fire and the atom trace must be available."""
    setup_mode(mode)
    pr.settings.atom_trace = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_rule(pr.Rule('blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'block_rule'))

    interpretation = pr.reason(timesteps=1)

    blocked_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked'])
    found = False
    for df in blocked_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found = True
            break
    assert found, 'blocked(B) should fire via minimization with atom_trace enabled'

    # Rule trace should be available without errors
    rule_trace_node, rule_trace_edge = pr.get_rule_trace(interpretation)
    assert rule_trace_node is not None


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_circumscription_example_scenario(mode):
    """End-to-end scenario adapted from the circumscription example: a rule
    that fires only because hackerControl(cb_2) is minimized from [0,1] to [0,0]."""
    setup_mode(mode)
    pr.settings.atom_trace = True
    pr.settings.inconsistency_check = True

    g = nx.DiGraph()
    g.add_nodes_from(['cb_1', 'cb_2', 'l1', 'l2'])
    g.add_edge('cb_1', 'cb_2', stepFrom=1)
    g.add_edge('cb_1', 'l1', hasLabel=1)
    g.add_edge('cb_2', 'l2', hasLabel=1)
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('stepFrom(cb_1, cb_2)', 'step_from_fact', 0, 1))
    pr.add_fact(pr.Fact('hackerControl(cb_1)', 'hacker_control_initial_fact'))
    pr.add_fact(pr.Fact('hackerControl(cb_2):[0,1]', 'hc_cb2_unknown'))

    # safe(Y) fires only if Y has minimized hackerControl ([0,1] -> [0,0]).
    pr.add_rule(pr.Rule('safe(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'safe_rule'))

    interpretation = pr.reason(timesteps=2)

    # safe(cb_2) should fire because hackerControl(cb_2) [0,1] is minimized to [0,0]
    safe_dfs = pr.filter_and_sort_nodes(interpretation, ['safe'])
    found_cb2 = False
    for df in safe_dfs:
        if len(df) > 0 and 'cb_2' in df['component'].values:
            found_cb2 = True
            break
    assert found_cb2, 'safe(cb_2) should fire via minimization of hackerControl(cb_2) [0,1] -> [0,0]'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_two_minimized_predicates_explicit_and_missing(mode):
    """Two minimized predicates exercise both branches of the minimization check:
      - hackerControl(B) is set explicitly to [0,1] via a fact (in-world branch).
      - compromised(B) has no fact at all (missing-from-world branch).
    Two rules each negate one of these predicates; both must fire on B."""
    setup_mode(mode)

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_minimized_predicate('compromised')

    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    # Explicit [0,1] -> exercises the in-world [0,1] -> [0,0] branch
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    # No fact for compromised(B) -> exercises the missing-from-world branch

    pr.add_rule(pr.Rule('blocked_hc(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
                        'blocked_hc_rule'))
    pr.add_rule(pr.Rule('blocked_comp(Y) <-1 stepFrom(X,Y), hackerControl(X), ~compromised(Y)',
                        'blocked_comp_rule'))

    interpretation = pr.reason(timesteps=1)

    blocked_hc_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked_hc'])
    found_hc = False
    for df in blocked_hc_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found_hc = True
            break
    assert found_hc, \
        'blocked_hc(B) should fire: minimized hackerControl(B) [0,1] -> [0,0] satisfies ~hackerControl'

    blocked_comp_dfs = pr.filter_and_sort_nodes(interpretation, ['blocked_comp'])
    found_comp = False
    for df in blocked_comp_dfs:
        if len(df) > 0 and 'B' in df['component'].values:
            found_comp = True
            break
    assert found_comp, \
        'blocked_comp(B) should fire: missing compromised(B) treated as [0,0] satisfies ~compromised'
