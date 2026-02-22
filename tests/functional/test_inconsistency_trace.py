import pyreason as pr
import networkx as nx
import pytest


def setup_mode(mode):
    """Configure PyReason settings for the specified mode."""
    pr.reset()
    pr.reset_rules()
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

    # Check new columns exist
    assert 'Consistent' in node_trace.columns
    assert 'Triggered By' in node_trace.columns
    assert 'Inconsistency Message' in node_trace.columns

    # Filter to inconsistency rows using the new Consistent column
    incon_rows = node_trace[node_trace['Consistent'] == False]
    assert len(incon_rows) >= 2, f'Expected at least 2 inconsistency trace rows, got {len(incon_rows)}'

    for _, row in incon_rows.iterrows():
        # Occurred Due To should now contain the actual fact/rule name, not the message
        assert not row['Occurred Due To'].startswith('Inconsistency'), \
            f'Occurred Due To should contain fact/rule name, not message: {row["Occurred Due To"]}'

        # Inconsistency Message should contain the descriptive message
        msg = row['Inconsistency Message']
        assert 'Inconsistency occurred.' in msg, f'Expected "Inconsistency occurred." in message: {msg}'
        assert 'Setting bounds to [0,1] and static=True for this timestep.' in msg, f'Expected bounds/static info in message: {msg}'

        # Triggered By should be Fact or IPL (these are fact-triggered inconsistencies)
        assert row['Triggered By'] in ('Fact', 'IPL'), \
            f'Expected Triggered By to be Fact or IPL, got: {row["Triggered By"]}'

    # Also check that consistent rows have the right metadata
    consistent_rows = node_trace[node_trace['Consistent'] == True]
    assert len(consistent_rows) > 0, 'Expected some consistent rows'
    for _, row in consistent_rows.iterrows():
        assert row['Inconsistency Message'] == '', \
            f'Consistent rows should have empty Inconsistency Message, got: {row["Inconsistency Message"]}'
        assert row['Triggered By'] in ('Fact', 'Rule', 'IPL'), \
            f'Expected Triggered By to be Fact/Rule/IPL, got: {row["Triggered By"]}'
