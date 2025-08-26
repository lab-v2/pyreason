# Test if the simple hello world program works
import pyreason as pr
import faulthandler


def test_reason_again():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    pr.settings.atom_trace = True  # Save atom trace
    # pr.settings.optimize_rules = False  # Disable rule optimization for debugging

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    # Run the program for two timesteps to see the diffusion take place
    faulthandler.enable()
    interpretation = pr.reason(timesteps=1)

    # Now reason again
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)
    interpretation = pr.reason(timesteps=3, again=True, restart=False)

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
    popular_counts = {}
    previous_popular = set()
    
    for t in sorted(interpretation_dict.keys()):
        current_popular = set()
        for component, labels in interpretation_dict[t].items():
            if 'popular' in labels and labels['popular'] == [1, 1]:
                current_popular.add(component)
        
        # Count only newly added popular people
        newly_added = len(current_popular - previous_popular)
        popular_counts[t] = newly_added
        previous_popular = current_popular

    assert popular_counts[2] == 1, 'At t=2 there should be one newly added popular person'
    assert popular_counts[3] == 1, 'At t=3 there should be one newly added popular person'
    assert popular_counts[4] == 1, 'At t=4 there should be one newly added popular person'

    # Mary should be popular in all three timesteps
    for t in [2, 3, 4]:
        if t in interpretation_dict:
            mary_popular = any(component == 'Mary' and labels.get('popular') == [1, 1] 
                              for component, labels in interpretation_dict[t].items())
            assert mary_popular, f'Mary should have popular bounds [1,1] for t={t} timesteps'

    # Justin should be popular in timesteps 3, 4
    for t in [3, 4]:
        if t in interpretation_dict:
            justin_popular = any(component == 'Justin' and labels.get('popular') == [1, 1] 
                                for component, labels in interpretation_dict[t].items())
            assert justin_popular, f'Justin should have popular bounds [1,1] for t={t} timesteps'

    # John should be popular in timestep 4
    if 4 in interpretation_dict:
        john_popular = any(component == 'John' and labels.get('popular') == [1, 1] 
                          for component, labels in interpretation_dict[4].items())
        assert john_popular, 'John should have popular bounds [1,1] for t=4 timesteps'
