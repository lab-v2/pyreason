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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        is_connected_to_edges = []
        for component, labels in timestep_data.items():
            if 'isConnectedTo' in labels:
                is_connected_to_edges.append((component, labels['isConnectedTo']))
        print(f"isConnectedTo edges: {is_connected_to_edges}")
        print()
    
    # Check the number of isConnectedTo edges at each timestep
    is_connected_to_counts = {}
    for t in interpretation_dict.keys():
        count = sum(1 for component, labels in interpretation_dict[t].items() 
                   if 'isConnectedTo' in labels and labels['isConnectedTo'] == [1, 1])
        is_connected_to_counts[t] = count
    
    assert len(interpretation_dict) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert is_connected_to_counts[1] == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    
    # Check if the specific edge exists with correct bounds
    edge_found = False
    for t in interpretation_dict.keys():
        for component, labels in interpretation_dict[t].items():
            if (component == ('Vnukovo_International_Airport', 'Riga_International_Airport') and 
                labels.get('isConnectedTo') == [1, 1]):
                edge_found = True
                break
        if edge_found:
            break
    
    assert edge_found, '(Vnukovo_International_Airport, Riga_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        is_connected_to_edges = []
        for component, labels in timestep_data.items():
            if 'isConnectedTo' in labels:
                is_connected_to_edges.append((component, labels['isConnectedTo']))
        print(f"isConnectedTo edges: {is_connected_to_edges}")
        print()
    
    # Check the number of isConnectedTo edges at each timestep
    is_connected_to_counts = {}
    for t in interpretation_dict.keys():
        count = sum(1 for component, labels in interpretation_dict[t].items() 
                   if 'isConnectedTo' in labels and labels['isConnectedTo'] == [1, 1])
        is_connected_to_counts[t] = count
    
    assert len(interpretation_dict) == 2, 'Pyreason should run exactly 2 fixpoint operations'
    assert is_connected_to_counts[1] == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    
    # Check if the specific edge exists with correct bounds
    edge_found = False
    for t in interpretation_dict.keys():
        for component, labels in interpretation_dict[t].items():
            if (component == ('Riga_International_Airport', 'Vnukovo_International_Airport') and 
                labels.get('isConnectedTo') == [1, 1]):
                edge_found = True
                break
        if edge_found:
            break
    
    assert edge_found, '(Riga_International_Airport, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'


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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        is_connected_to_edges = []
        for component, labels in timestep_data.items():
            if 'isConnectedTo' in labels:
                is_connected_to_edges.append((component, labels['isConnectedTo']))
        print(f"isConnectedTo edges: {is_connected_to_edges}")
        print()
    
    # Check the number of isConnectedTo edges at each timestep
    is_connected_to_counts = {}
    for t in interpretation_dict.keys():
        count = sum(1 for component, labels in interpretation_dict[t].items() 
                   if 'isConnectedTo' in labels and labels['isConnectedTo'] == [1, 1])
        is_connected_to_counts[t] = count
    
    assert len(interpretation_dict) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert is_connected_to_counts[1] == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    
    # Check if the specific edge exists with correct bounds
    edge_found = False
    for t in interpretation_dict.keys():
        for component, labels in interpretation_dict[t].items():
            if (component == ('Vnukovo_International_Airport', 'Yali') and 
                labels.get('isConnectedTo') == [1, 1]):
                edge_found = True
                break
        if edge_found:
            break
    
    assert edge_found, '(Vnukovo_International_Airport, Yali) should have isConnectedTo bounds [1,1] for t=1 timesteps'


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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        is_connected_to_edges = []
        for component, labels in timestep_data.items():
            if 'isConnectedTo' in labels:
                is_connected_to_edges.append((component, labels['isConnectedTo']))
        print(f"isConnectedTo edges: {is_connected_to_edges}")
        print()
    
    # Check the number of isConnectedTo edges at each timestep
    is_connected_to_counts = {}
    for t in interpretation_dict.keys():
        count = sum(1 for component, labels in interpretation_dict[t].items() 
                   if 'isConnectedTo' in labels and labels['isConnectedTo'] == [1, 1])
        is_connected_to_counts[t] = count
    
    assert len(interpretation_dict) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert is_connected_to_counts[1] == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    
    # Check if the specific edge exists with correct bounds
    edge_found = False
    for t in interpretation_dict.keys():
        for component, labels in interpretation_dict[t].items():
            if (component == ('Yali', 'Vnukovo_International_Airport') and 
                labels.get('isConnectedTo') == [1, 1]):
                edge_found = True
                break
        if edge_found:
            break
    
    assert edge_found, '(Yali, Vnukovo_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'
