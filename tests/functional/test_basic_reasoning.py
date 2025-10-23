# Basic reasoning tests for PyReason
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


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_hello_world(mode):
    """Test basic hello world program with different reasoning modes."""
    setup_mode(mode)

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.atom_trace = True  # Print atom trace

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
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

@pytest.mark.parametrize("mode", ["regular", "fp"])
def test_reorder_clauses(mode):
    """Test clause reordering functionality."""
    setup_mode(mode)

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
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
    rule_trace_node, _ = pr.get_rule_trace(interpretation)

    if mode == "fp":
        # FP version: Find the first Justin rule entry (more robust than relying on row index)
        justin_rule_rows = rule_trace_node[(rule_trace_node['Node'] == 'Justin') & (rule_trace_node['Occurred Due To'] == 'popular_rule')]
        assert len(justin_rule_rows) > 0, 'Should have at least one Justin rule entry'
        first_justin_rule = justin_rule_rows.iloc[0]
        assert first_justin_rule['Clause-1'][0] == ('Justin', 'Mary')
    else:
        # Regular version: The second row, clause 1 should be the edge grounding ('Justin', 'Mary')
        assert rule_trace_node.iloc[2]['Clause-1'][0] == ('Justin', 'Mary')


@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_filter_and_sort_nodes_sorting_verification(mode):
    """Test that filter_and_sort_nodes actually sorts nodes correctly by different criteria."""
    setup_mode(mode)
    pr.settings.store_interpretation_changes = True

    import networkx as nx

    # Create a simple graph with multiple nodes
    graph = nx.DiGraph()
    graph.add_node('A')
    graph.add_node('B')
    graph.add_node('C')
    graph.add_node('D')

    pr.load_graph(graph)

    # Add facts with different interval bounds to create varied data for sorting
    # Node A: [0.7, 0.9] - high lower, high upper
    pr.add_fact(pr.Fact('score(A) : [0.7, 0.9]', 'fact_a', 0, 1))
    # Node B: [0.1, 0.2] - low lower, low upper
    pr.add_fact(pr.Fact('score(B) : [0.1, 0.2]', 'fact_b', 0, 1))
    # Node C: [0.4, 0.6] - medium lower, medium upper
    pr.add_fact(pr.Fact('score(C) : [0.4, 0.6]', 'fact_c', 0, 1))
    # Node D: [0.2, 0.8] - low lower, high upper
    pr.add_fact(pr.Fact('score(D) : [0.2, 0.8]', 'fact_d', 0, 1))

    # Add a simple rule to ensure reasoning happens
    pr.add_rule(pr.Rule('result(x) <- score(x)', 'test_rule'))

    # Run reasoning
    interpretation = pr.reason(timesteps=1)

    # Test 1: Sort by lower bound, descending (default)
    # Expected order: A(0.7), C(0.4), D(0.2), B(0.1)
    result = pr.filter_and_sort_nodes(interpretation, ['score'], sort_by='lower', descending=True)
    df = result[0]  # Get timestep 0
    assert len(df) == 4, 'Should have 4 nodes'

    # Extract lower bounds for each row
    lower_bounds = [df.iloc[i]['score'][0] for i in range(len(df))]
    # Verify descending order
    for i in range(len(lower_bounds) - 1):
        assert lower_bounds[i] >= lower_bounds[i+1], f'Lower bounds should be descending: {lower_bounds}'

    # Test 2: Sort by lower bound, ascending
    # Expected order: B(0.1), D(0.2), C(0.4), A(0.7)
    result = pr.filter_and_sort_nodes(interpretation, ['score'], sort_by='lower', descending=False)
    df = result[0]
    lower_bounds = [df.iloc[i]['score'][0] for i in range(len(df))]
    # Verify ascending order
    for i in range(len(lower_bounds) - 1):
        assert lower_bounds[i] <= lower_bounds[i+1], f'Lower bounds should be ascending: {lower_bounds}'

    # Test 3: Sort by upper bound, descending
    # Expected order: A(0.9), D(0.8), C(0.6), B(0.2)
    result = pr.filter_and_sort_nodes(interpretation, ['score'], sort_by='upper', descending=True)
    df = result[0]
    upper_bounds = [df.iloc[i]['score'][1] for i in range(len(df))]
    # Verify descending order
    for i in range(len(upper_bounds) - 1):
        assert upper_bounds[i] >= upper_bounds[i+1], f'Upper bounds should be descending: {upper_bounds}'

    # Test 4: Sort by upper bound, ascending
    # Expected order: B(0.2), C(0.6), D(0.8), A(0.9)
    result = pr.filter_and_sort_nodes(interpretation, ['score'], sort_by='upper', descending=False)
    df = result[0]
    upper_bounds = [df.iloc[i]['score'][1] for i in range(len(df))]
    # Verify ascending order
    for i in range(len(upper_bounds) - 1):
        assert upper_bounds[i] <= upper_bounds[i+1], f'Upper bounds should be ascending: {upper_bounds}'


@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_filter_and_sort_edges_sorting_verification(mode):
    """Test that filter_and_sort_edges actually sorts edges correctly by different criteria."""
    setup_mode(mode)
    pr.settings.store_interpretation_changes = True

    import networkx as nx

    # Create a simple graph with multiple edges
    graph = nx.DiGraph()
    graph.add_edge('A', 'B')
    graph.add_edge('B', 'C')
    graph.add_edge('C', 'D')
    graph.add_edge('D', 'E')

    pr.load_graph(graph)

    # Add facts with different interval bounds to create varied data for sorting
    # Edge A->B: [0.7, 0.9] - high lower, high upper
    pr.add_fact(pr.Fact('weight(A, B) : [0.7, 0.9]', 'fact_ab', 0, 1))
    # Edge B->C: [0.1, 0.2] - low lower, low upper
    pr.add_fact(pr.Fact('weight(B, C) : [0.1, 0.2]', 'fact_bc', 0, 1))
    # Edge C->D: [0.4, 0.6] - medium lower, medium upper
    pr.add_fact(pr.Fact('weight(C, D) : [0.4, 0.6]', 'fact_cd', 0, 1))
    # Edge D->E: [0.2, 0.8] - low lower, high upper
    pr.add_fact(pr.Fact('weight(D, E) : [0.2, 0.8]', 'fact_de', 0, 1))

    # Add a simple rule to ensure reasoning happens
    pr.add_rule(pr.Rule('result(x, y) <- weight(x, y)', 'test_rule'))

    # Run reasoning
    interpretation = pr.reason(timesteps=1)

    # Test 1: Sort by lower bound, descending (default)
    # Expected order: A->B(0.7), C->D(0.4), D->E(0.2), B->C(0.1)
    result = pr.filter_and_sort_edges(interpretation, ['weight'], sort_by='lower', descending=True)
    df = result[0]  # Get timestep 0
    assert len(df) == 4, 'Should have 4 edges'

    # Extract lower bounds for each row
    lower_bounds = [df.iloc[i]['weight'][0] for i in range(len(df))]
    # Verify descending order
    for i in range(len(lower_bounds) - 1):
        assert lower_bounds[i] >= lower_bounds[i+1], f'Lower bounds should be descending: {lower_bounds}'

    # Test 2: Sort by lower bound, ascending
    # Expected order: B->C(0.1), D->E(0.2), C->D(0.4), A->B(0.7)
    result = pr.filter_and_sort_edges(interpretation, ['weight'], sort_by='lower', descending=False)
    df = result[0]
    lower_bounds = [df.iloc[i]['weight'][0] for i in range(len(df))]
    # Verify ascending order
    for i in range(len(lower_bounds) - 1):
        assert lower_bounds[i] <= lower_bounds[i+1], f'Lower bounds should be ascending: {lower_bounds}'

    # Test 3: Sort by upper bound, descending
    # Expected order: A->B(0.9), D->E(0.8), C->D(0.6), B->C(0.2)
    result = pr.filter_and_sort_edges(interpretation, ['weight'], sort_by='upper', descending=True)
    df = result[0]
    upper_bounds = [df.iloc[i]['weight'][1] for i in range(len(df))]
    # Verify descending order
    for i in range(len(upper_bounds) - 1):
        assert upper_bounds[i] >= upper_bounds[i+1], f'Upper bounds should be descending: {upper_bounds}'

    # Test 4: Sort by upper bound, ascending
    # Expected order: B->C(0.2), C->D(0.6), D->E(0.8), A->B(0.9)
    result = pr.filter_and_sort_edges(interpretation, ['weight'], sort_by='upper', descending=False)
    df = result[0]
    upper_bounds = [df.iloc[i]['weight'][1] for i in range(len(df))]
    # Verify ascending order
    for i in range(len(upper_bounds) - 1):
        assert upper_bounds[i] <= upper_bounds[i+1], f'Upper bounds should be ascending: {upper_bounds}'
