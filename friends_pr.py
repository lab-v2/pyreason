# Test if the simple hello world program works
import pyreason as pr
import faulthandler


def hello_world():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = 'tests/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    pr.settings.use_gpu = True
    # pr.settings.optimize_rules = False  # Disable rule optimization for debugging

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    # pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_rule(pr.Rule('owns(y,x) <-1 popular(y), Friends(x,y)', 'popular_rule', infer_edges=True))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    faulthandler.enable()
    interpretation = pr.reason(timesteps=2)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
        dataframes = pr.filter_and_sort_edges(interpretation, ['owns'])
        for t, df in enumerate(dataframes):
            print(f'TIMESTEP - {t}')
            print(df)
            print()

hello_world()
