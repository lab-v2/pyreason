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
def test_minimized_predicate_allows_known_propagation(mode):
    """When hackerControl is minimized but B has known [1,1] bounds,
    the rule should still fire normally."""
    setup_mode(mode)

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')

    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B)', 'hc_b_known'))  # defaults to [1,1]

    pr.add_rule(pr.Rule('infected(Y) <-1 stepFrom(X,Y), hackerControl(X), hackerControl(Y)',
                        'infection_rule'))

    interpretation = pr.reason(timesteps=1)

    # Both nodes have known hackerControl [1,1], so infected(B) should fire
    dataframes = pr.filter_and_sort_nodes(interpretation, ['infected'])
    found = False
    for df in dataframes:
        if len(df) > 0 and 'B' in df['component'].values:
            row = df[df['component'] == 'B'].iloc[0]
            assert row['infected'] == [1.0, 1.0], \
                f'infected(B) should have bounds [1,1], got {row["infected"]}'
            found = True
            break
    assert found, 'infected(B) should fire when both nodes have known hackerControl'


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
    """A minimized predicate propagated by a rule should set known bounds
    at a later timestep."""
    setup_mode(mode)

    g = nx.DiGraph()
    g.add_nodes_from(['A', 'B'])
    g.add_edge('A', 'B', stepFrom=1)
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')

    # A has control from the start
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    # Simple propagation rule: control spreads via stepFrom (only needs source)
    pr.add_rule(pr.Rule('hackerControl(Y) <-1 stepFrom(X,Y), hackerControl(X)',
                        'propagation_rule'))

    interpretation = pr.reason(timesteps=2)

    # B should eventually get hackerControl from propagation
    dataframes = pr.filter_and_sort_nodes(interpretation, ['hackerControl'])
    found_b = False
    for df in dataframes:
        if len(df) > 0 and 'B' in df['component'].values:
            found_b = True
            break
    assert found_b, 'hackerControl should propagate from A to B via the rule'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_inconsistency_check(mode):
    """Verify that reasoning with minimized predicates works correctly
    when inconsistency_check is enabled."""
    setup_mode(mode)
    pr.settings.inconsistency_check = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_rule(pr.Rule('infected(Y) <-1 stepFrom(X,Y), hackerControl(X), hackerControl(Y)',
                        'infection_rule'))

    # Should complete without error
    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_nodes(interpretation, ['infected'])
    for df in dataframes:
        if len(df) > 0:
            assert 'B' not in df['component'].values


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_persistent_mode(mode):
    """Verify minimized predicates work correctly with persistent bounds."""
    setup_mode(mode)
    pr.settings.persistent = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))
    pr.add_rule(pr.Rule('infected(Y) <-1 stepFrom(X,Y), hackerControl(X), hackerControl(Y)',
                        'infection_rule'))

    interpretation = pr.reason(timesteps=2)

    # With persistent mode, B's unknown [0,1] should still be minimized to [0,0]
    dataframes = pr.filter_and_sort_nodes(interpretation, ['infected'])
    for df in dataframes:
        if len(df) > 0:
            assert 'B' not in df['component'].values, \
                'Minimization should still block propagation in persistent mode'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_minimized_with_atom_trace(mode):
    """Verify atom tracing works correctly with minimized predicates."""
    setup_mode(mode)
    pr.settings.atom_trace = True

    g = _build_two_node_graph()
    pr.load_graph(g)

    pr.add_minimized_predicate('hackerControl')
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_rule(pr.Rule('hackerControl(Y) <-1 stepFrom(X,Y), hackerControl(X)',
                        'propagation_rule'))

    interpretation = pr.reason(timesteps=1)

    # Rule trace should be available without errors
    rule_trace_node, rule_trace_edge = pr.get_rule_trace(interpretation)
    assert rule_trace_node is not None


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_circumscription_example_scenario(mode):
    """Test the scenario from the circumscription example file."""
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
    pr.add_rule(pr.Rule('future(Y) <-1 stepFrom(X,Y), hackerControl(X)'))

    interpretation = pr.reason(timesteps=2)

    # cb_2 should have future because cb_1 has known hackerControl
    dataframes = pr.filter_and_sort_nodes(interpretation, ['future'])
    found_cb2 = False
    for df in dataframes:
        if len(df) > 0 and 'cb_2' in df['component'].values:
            found_cb2 = True
            break
    assert found_cb2, 'future(cb_2) should fire since hackerControl(cb_1) is known'

    # cb_1 should have hackerControl in the results
    hc_dataframes = pr.filter_and_sort_nodes(interpretation, ['hackerControl'])
    found_cb1 = False
    for df in hc_dataframes:
        if len(df) > 0 and 'cb_1' in df['component'].values:
            found_cb1 = True
            break
    assert found_cb1, 'cb_1 should appear in hackerControl filter results'
