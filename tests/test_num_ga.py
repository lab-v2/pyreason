# Test if the simple hello world program works
import pyreason as pr


def test_num_ga():
    graph_path = './tests/knowledge_graph_test_subset.graphml'
    pr.reset()
    pr.reset_rules()
    # Modify pyreason settings to make verbose and to save the rule trace to a file
    pr.settings.verbose = True
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
    # pr.add_fact(pr.Fact('dummy(Riga_International_Airport): [0, 1]', 'dummy_fact', 0, 1))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Find number of ground atoms from dictionary
    ga_cnt = []
    d = interpretation.get_dict()
    for time, atoms in d.items():
        ga_cnt.append(0)
        for comp, label_bnds in atoms.items():
            ga_cnt[time] += len(label_bnds)

    # Make sure the computed number of ground atoms is correct
    assert ga_cnt == list(interpretation.get_num_ground_atoms()), 'Number of ground atoms should be the same as the computed number of ground atoms'
