Custom Threshold Example
============================


.. code:: python

    # Test if the simple program works with thresholds defined
    import pyreason as pr
    from pyreason import Threshold
    import networkx as nx

    # Reset PyReason
    pr.reset()
    pr.reset_rules()


    # Create an empty graph
    G = nx.DiGraph()

    # Add nodes
    nodes = ["TextMessage", "Zach", "Justin", "Michelle", "Amy"]
    G.add_nodes_from(nodes)

    # Add edges with attribute 'HaveAccess'
    G.add_edge("Zach", "TextMessage", HaveAccess=1)
    G.add_edge("Justin", "TextMessage", HaveAccess=1)
    G.add_edge("Michelle", "TextMessage", HaveAccess=1)
    G.add_edge("Amy", "TextMessage", HaveAccess=1)



    # Modify pyreason settings to make verbose
    pr.reset_settings()
    pr.settings.verbose = True  # Print info to screen

    #load the graph
    pr.load_graph(G)

    # add custom thresholds
    user_defined_thresholds = [
        Threshold("greater_equal", ("number", "total"), 1),
        Threshold("greater_equal", ("percent", "total"), 100),

    ]

    pr.add_rule(
        pr.Rule(
            "ViewedByAll(y) <- HaveAccess(x,y), Viewed(x)",
            "viewed_by_all_rule",
            custom_thresholds=user_defined_thresholds,
        )
    )

    pr.add_fact(pr.Fact("Viewed(Zach)", "seen-fact-zach", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Justin)", "seen-fact-justin", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Michelle)", "seen-fact-michelle", 1, 3))
    pr.add_fact(pr.Fact("Viewed(Amy)", "seen-fact-amy", 2, 3))

    # Run the program for three timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=3)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ["ViewedByAll"])
    for t, df in enumerate(dataframes):
        print(f"TIMESTEP - {t}")
        print(df)
        print()

    assert (
        len(dataframes[0]) == 0
    ), "At t=0 the TextMessage should not have been ViewedByAll"
    assert (
        len(dataframes[2]) == 1
    ), "At t=2 the TextMessage should have been ViewedByAll"

    # TextMessage should be ViewedByAll in t=2
    assert "TextMessage" in dataframes[2]["component"].values and dataframes[2].iloc[
        0
    ].ViewedByAll == [
        1,
        1,
    ], "TextMessage should have ViewedByAll bounds [1,1] for t=2 timesteps"
