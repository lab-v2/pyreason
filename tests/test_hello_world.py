# Test if the simple hello world program works
import pyreason as pr


def test_hello_world():
    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/friends_graph.graphml'

    # Modify pyreason settings to make verbose and to save the rule trace to a file
    pr.settings.verbose = True     # Print info to screen

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular-fact', 'Mary', 'popular', [1, 1], 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=2)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes[0]) == 1, 'At t=0 there should be one popular person'
    assert len(dataframes[1]) == 2, 'At t=0 there should be two popular people'
    assert len(dataframes[2]) == 3, 'At t=0 there should be three popular people'

    assert dataframes[0].iloc[0].component == 'Mary' and dataframes[0].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
    assert dataframes[1].iloc[0].component == 'Mary' and dataframes[1].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
    assert dataframes[2].iloc[0].component == 'Mary' and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

    assert dataframes[1].iloc[1].component == 'Justin' and dataframes[1].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
    assert dataframes[2].iloc[2].component == 'Justin' and dataframes[2].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

    assert dataframes[2].iloc[1].component == 'John' and dataframes[2].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'
