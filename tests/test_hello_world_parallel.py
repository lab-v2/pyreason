# Test if the simple hello world program works
import pyreason as pr


def test_hello_world_parallel():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.reset_settings()
    pr.settings.verbose = True     # Print info to screen

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=2)

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        popular_nodes = []
        for component, labels in timestep_data.items():
            if 'popular' in labels:
                popular_nodes.append((component, labels['popular']))
        print(f"Popular nodes: {popular_nodes}")
        print()

    # Get the number of NEWLY ADDED popular people at each timestep
    popular_counts = []
    
    for t in range(3):  # 0, 1, 2
        if t in interpretation_dict:
            current_popular = set()
            for component, labels in interpretation_dict[t].items():
                if 'popular' in labels:
                    popular_value = labels['popular']
                    # Check if the value represents "true" (popular)
                    # Handle both tuple (1.0, 1.0) and list [1, 1] formats
                    if (isinstance(popular_value, (list, tuple)) and 
                        len(popular_value) == 2 and 
                        popular_value[0] == 1 and popular_value[1] == 1):
                        current_popular.add(component)
            
            if t == 0:
                # At timestep 0, all popular people are newly added (initial facts)
                newly_added = len(current_popular)
            else:
                # For subsequent timesteps, compare with previous timestep
                previous_popular = set()
                for component, labels in interpretation_dict[t-1].items():
                    if 'popular' in labels:
                        popular_value = labels['popular']
                        if (isinstance(popular_value, (list, tuple)) and 
                            len(popular_value) == 2 and 
                            popular_value[0] == 1 and popular_value[1] == 1):
                            previous_popular.add(component)
                
                newly_added = len(current_popular - previous_popular)
            
            popular_counts.append(newly_added)
        else:
            popular_counts.append(0)

    assert popular_counts[0] == 1, 'At t=0 there should be one newly added popular person'
    assert popular_counts[1] == 1, 'At t=1 there should be one newly added popular person'
    assert popular_counts[2] == 1, 'At t=2 there should be one newly added popular person'

    # Mary should be popular in all three timesteps
    for t in range(3):
        if t in interpretation_dict:
            mary_popular = any(component == 'Mary' and 
                              'popular' in labels and 
                              labels['popular'][0] == 1 and labels['popular'][1] == 1
                              for component, labels in interpretation_dict[t].items())
            assert mary_popular, f'Mary should have popular bounds [1,1] for t={t} timesteps'

    # Justin should be popular in timesteps 1, 2
    for t in [1, 2]:
        if t in interpretation_dict:
            justin_popular = any(component == 'Justin' and 
                                'popular' in labels and 
                                labels['popular'][0] == 1 and labels['popular'][1] == 1
                                for component, labels in interpretation_dict[t].items())
            assert justin_popular, f'Justin should have popular bounds [1,1] for t={t} timesteps'

    # John should be popular in timestep 2
    if 2 in interpretation_dict:
        john_popular = any(component == 'John' and 
                          'popular' in labels and 
                          labels['popular'][0] == 1 and labels['popular'][1] == 1
                          for component, labels in interpretation_dict[2].items())
        assert john_popular, 'John should have popular bounds [1,1] for t=2 timesteps'
