import pyreason as pr


def test_rule_filtering():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
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
