# Edge inference rule tests for PyReason
import pyreason as pr
import networkx as nx
import pytest


def setup_mode(mode):
    """Configure PyReason settings for the specified mode."""
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify pyreason settings to make verbose and to save the rule trace to a file
    pr.settings.verbose = True
    pr.settings.atom_trace = True
    pr.settings.memory_profile = False
    pr.settings.canonical = True
    pr.settings.inconsistency_check = False
    pr.settings.static_graph_facts = False
    pr.settings.output_to_file = False
    pr.settings.store_interpretation_changes = True
    pr.settings.save_graph_attributes_to_trace = True
    pr.settings.parallel_computing = False

    if mode == "fp":
        pr.settings.fp_version = True
    elif mode == "parallel":
        pr.settings.parallel_computing = True


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_anyBurl_rule_1(mode):
    """Test anyBurl rule 1: isConnectedTo(A, Y) <- isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)"""
    graph_path = './tests/functional/knowledge_graph_test_subset.graphml'
    setup_mode(mode)

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Vnukovo_International_Airport', 'Riga_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Riga_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_anyBurl_rule_2(mode):
    """Test anyBurl rule 2: isConnectedTo(Y, A) <- isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)"""
    graph_path = './tests/functional/knowledge_graph_test_subset.graphml'
    setup_mode(mode)

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(Y, A) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_2', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Riga_International_Airport', 'Vnukovo_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Riga_International_Airport, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_anyBurl_rule_3(mode):
    """Test anyBurl rule 3: isConnectedTo(A, Y) <- isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)"""
    graph_path = './tests/functional/knowledge_graph_test_subset.graphml'
    setup_mode(mode)

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_3', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Vnukovo_International_Airport', 'Yali') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Yali) should have isConnectedTo bounds [1,1] for t=1 timesteps'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_anyBurl_rule_4(mode):
    """Test anyBurl rule 4: isConnectedTo(Y, A) <- isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)"""
    graph_path = './tests/functional/knowledge_graph_test_subset.graphml'
    setup_mode(mode)

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(Y, A) <-1  isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_4', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Yali', 'Vnukovo_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Yali, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_partial_edge_grounding(mode):
    """Test that ground node names in edge clauses are pre-populated as groundings.

    When a rule has an edge clause like trusts(Alice, y) where Alice is a known
    node but the specific edge pair isn't enumerated, partial grounding ensures
    Alice is recognized and edges from Alice are discovered via neighbor lookups.
    """
    setup_mode(mode)
    pr.settings.allow_ground_rules = True

    # Build a small graph: Alice trusts Bob, Bob trusts Carol
    # Alice has the 'admin' attribute
    graph = nx.DiGraph()
    graph.add_node("Alice", admin=1)
    graph.add_node("Bob", admin=0)
    graph.add_node("Carol", admin=0)
    graph.add_edge("Alice", "Bob", trusts=1)
    graph.add_edge("Bob", "Carol", trusts=1)
    pr.load_graph(graph)

    # Rule: if Alice is admin and Alice trusts someone, infer can_access edge
    # The edge clause trusts(Alice, y) uses a ground node name (Alice) + free variable (y)
    # Partial grounding pre-populates Alice so neighbor lookup finds the edge to Bob
    pr.add_rule(pr.Rule(
        'can_access(Alice, y) <-1 admin(Alice), trusts(Alice, y)',
        'partial_ground_rule',
        infer_edges=True,
    ))

    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_edges(interpretation, ['can_access'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes) == 2, 'Should have 2 timesteps of results'
    assert len(dataframes[1]) == 1, 'At t=1 there should be exactly 1 new can_access edge'
    assert ('Alice', 'Bob') in dataframes[1]['component'].values.tolist(), \
        'can_access(Alice, Bob) should be inferred'
    assert dataframes[1]['can_access'].iloc[0] == [1, 1], \
        'can_access(Alice, Bob) should have bounds [1,1]'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_partial_edge_grounding_reverse(mode):
    """Test partial grounding when the ground node is in the second position of the edge clause.

    Rule: can_reach(y, Carol) <- trusts(y, Carol), admin(Carol)
    Carol is ground in position 2 of the edge clause.
    """
    setup_mode(mode)
    pr.settings.allow_ground_rules = True

    graph = nx.DiGraph()
    graph.add_node("Alice", admin=0)
    graph.add_node("Bob", admin=0)
    graph.add_node("Carol", admin=1)
    graph.add_edge("Alice", "Bob", trusts=1)
    graph.add_edge("Bob", "Carol", trusts=1)
    pr.load_graph(graph)

    pr.add_rule(pr.Rule(
        'can_reach(y, Carol) <-1 admin(Carol), trusts(y, Carol)',
        'partial_ground_reverse_rule',
        infer_edges=True,
    ))

    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_edges(interpretation, ['can_reach'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes) == 2, 'Should have 2 timesteps of results'
    assert len(dataframes[1]) == 1, 'At t=1 there should be exactly 1 new can_reach edge'
    assert ('Bob', 'Carol') in dataframes[1]['component'].values.tolist(), \
        'can_reach(Bob, Carol) should be inferred'
    assert dataframes[1]['can_reach'].iloc[0] == [1, 1], \
        'can_reach(Bob, Carol) should have bounds [1,1]'
