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


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_inconsistency_trace_message_format(mode):
    """Test that inconsistency trace messages include descriptive grounding info."""
    setup_mode(mode)
    pr.settings.atom_trace = True
    pr.settings.inconsistency_check = True

    g = nx.DiGraph()
    g.add_nodes_from(['Alice', 'Bob'])
    g.add_edge('Alice', 'Bob', contact=1)
    pr.load_graph(g)
    pr.add_inconsistent_predicate('sick', 'healthy')
    pr.add_rule(pr.Rule('sick(y):[0.5,0.7] <- sick(x):[0.5,1.0], contact(x,y)', 'spread_rule'))
    pr.add_fact(pr.Fact('sick(Alice):[0.8,1.0]', 'alice_sick_fact', 0, 0))
    pr.add_fact(pr.Fact('healthy(Alice):[0.9,1.0]', 'alice_healthy_fact', 0, 0))

    interpretation = pr.reason(timesteps=1)
    node_trace, _ = pr.get_rule_trace(interpretation)

    # Filter to inconsistency rows
    incon_rows = node_trace[node_trace['Occurred Due To'].str.startswith('Inconsistency')]
    assert len(incon_rows) >= 2, f'Expected at least 2 inconsistency trace rows, got {len(incon_rows)}'

    for _, row in incon_rows.iterrows():
        msg = row['Occurred Due To']
        assert 'Inconsistency occurred.' in msg, f'Expected "Inconsistency occurred." in message: {msg}'
        assert 'conflicts with grounding' in msg, f'Expected "conflicts with grounding" in message: {msg}'
        assert 'Setting bounds to [0,1] and static=True for this timestep.' in msg, f'Expected bounds/static info in message: {msg}'
        assert 'healthy(Alice)' in msg, f'Expected "healthy(Alice)" in message: {msg}'
        assert 'sick(Alice)' in msg, f'Expected "sick(Alice)" in message: {msg}'
