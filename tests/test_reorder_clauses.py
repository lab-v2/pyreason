# Test if the simple hello world program works
import pyreason as pr


def test_reorder_clauses():
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
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=2)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes[0]) == 1, 'At t=0 there should be one popular person'
    assert len(dataframes[1]) == 2, 'At t=1 there should be two popular people'
    assert len(dataframes[2]) == 3, 'At t=2 there should be three popular people'

    # Mary should be popular in all three timesteps
    assert 'Mary' in dataframes[0]['component'].values and dataframes[0].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
    assert 'Mary' in dataframes[1]['component'].values and dataframes[1].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
    assert 'Mary' in dataframes[2]['component'].values and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

    # Justin should be popular in timesteps 1, 2
    assert 'Justin' in dataframes[1]['component'].values and dataframes[1].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
    assert 'Justin' in dataframes[2]['component'].values and dataframes[2].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

    # John should be popular in timestep 3
    assert 'John' in dataframes[2]['component'].values and dataframes[2].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'

    # Now look at the trace and make sure the order has gone back to the original rule
    # The second row, clause 1 should be the edge grounding ('Justin', 'Mary')
    rule_trace_node, _ = pr.get_rule_trace(interpretation)
    assert rule_trace_node.iloc[2]['Clause-1'][0] == ('Justin', 'Mary')
