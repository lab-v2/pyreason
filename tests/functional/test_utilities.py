# Utility function tests for PyReason (ground atoms counting, rule filtering)
import pyreason as pr
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


@pytest.mark.skipif(True, reason="Not implemented for FP version")
@pytest.mark.parametrize("mode", ["regular"])
def test_num_ga(mode):
    """Test ground atom counting functionality."""
    graph_path = './tests/functional/knowledge_graph_test_subset.graphml'
    setup_mode(mode)

    # Modify pyreason settings to make verbose and to save the rule trace to a file
    pr.settings.atom_trace = True
    pr.settings.canonical = True
    pr.settings.inconsistency_check = False
    pr.settings.static_graph_facts = False
    pr.settings.output_to_file = False
    pr.settings.store_interpretation_changes = True
    pr.settings.save_graph_attributes_to_trace = True

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1 isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)

    # Find number of ground atoms from dictionary
    ga_cnt = []
    d = interpretation.get_dict()
    for time, atoms in d.items():
        ga_cnt.append(0)
        for comp, label_bnds in atoms.items():
            ga_cnt[time] += len(label_bnds)

    # Make sure the computed number of ground atoms is correct
    assert ga_cnt == list(interpretation.get_num_ground_atoms()), 'Number of ground atoms should be the same as the computed number of ground atoms'


@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_rule_filtering(mode):
    """Test rule filtering functionality."""
    setup_mode(mode)

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.atom_trace = True  # Print atom trace

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('head1(x) <-1 pred1(x,y), pred2(y,z), pred3(z, w)', 'rule1'))   # Should fire
    pr.add_rule(pr.Rule('head1(x) <-1 pred1(x,y), pred4(y,z), pred3(z, w)', 'rule2'))   # Should fire
    pr.add_rule(pr.Rule('head2(x) <-1 pred1(x,y), pred2(y,z), pred3(z, w)', 'rule3'))   # Should not fire

    # Dependency rules
    pr.add_rule(pr.Rule('pred1(x,y) <-1 pred2(x,y)', 'rule4'))   # Should fire
    pr.add_rule(pr.Rule('pred2(x,y) <-1 pred3(x,y)', 'rule5'))   # Should fire

    # Define the query
    query = pr.Query('head1(x)')

    # Filter the rules
    filtered_rules = pr.ruleset_filter.filter_ruleset([query], pr.get_rules())
    filtered_rule_names = [r.get_rule_name() for r in filtered_rules]
    assert 'rule1' in filtered_rule_names, 'Rule 1 should be in the filtered rules'
    assert 'rule2' in filtered_rule_names, 'Rule 2 should be in the filtered rules'
    assert 'rule4' in filtered_rule_names, 'Rule 4 should be in the filtered rules'
    assert 'rule5' in filtered_rule_names, 'Rule 5 should be in the filtered rules'
    assert 'rule3' not in filtered_rule_names, 'Rule 3 should not be in the filtered rules'
