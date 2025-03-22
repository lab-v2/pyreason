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

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes[2]) == 1, 'At t=0 there should be one popular person'
    assert len(dataframes[3]) == 2, 'At t=1 there should be two popular people'
    assert len(dataframes[4]) == 3, 'At t=2 there should be three popular people'

    # Mary should be popular in all three timesteps
    assert 'Mary' in dataframes[2]['component'].values and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
    assert 'Mary' in dataframes[3]['component'].values and dataframes[3].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
    assert 'Mary' in dataframes[4]['component'].values and dataframes[4].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

    # Justin should be popular in timesteps 1, 2
    assert 'Justin' in dataframes[3]['component'].values and dataframes[3].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
    assert 'Justin' in dataframes[4]['component'].values and dataframes[4].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

    # John should be popular in timestep 3
    assert 'John' in dataframes[4]['component'].values and dataframes[4].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'
