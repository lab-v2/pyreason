import pyreason as pr


def test_anyBurl_rule_1():
    graph_path = './tests/knowledge_graph_test_subset.graphml'
    pr.reset()
    pr.reset_rules()
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
    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Vnukovo_International_Airport', 'Riga_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Riga_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


def test_anyBurl_rule_2():
    graph_path = './tests/knowledge_graph_test_subset.graphml'
    pr.reset()
    pr.reset_rules()
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
    # Load all the files into pyreason
    pr.load_graphml(graph_path)

    pr.add_rule(pr.Rule('isConnectedTo(Y, A) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_2', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Riga_International_Airport', 'Vnukovo_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Riga_International_Airport, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


def test_anyBurl_rule_3():
    graph_path = './tests/knowledge_graph_test_subset.graphml'
    pr.reset()
    pr.reset_rules()
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
    # Load all the files into pyreason
    pr.load_graphml(graph_path)

    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_3', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Vnukovo_International_Airport', 'Yali') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Yali) should have isConnectedTo bounds [1,1] for t=1 timesteps'


def test_anyBurl_rule_4():
    graph_path = './tests/knowledge_graph_test_subset.graphml'
    pr.reset()
    pr.reset_rules()
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
    # Load all the files into pyreason
    pr.load_graphml(graph_path)

    pr.add_rule(pr.Rule('isConnectedTo(Y, A) <-1  isConnectedTo(B, Y), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_4', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Yali', 'Vnukovo_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Yali, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'
