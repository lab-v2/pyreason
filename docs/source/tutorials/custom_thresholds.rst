PyReason Custom Threshold Example
=================================

In this tutorial, we will look at how to run PyReason with Custom Thresholds. 
Custom Thresholds are parameters in the :ref:`Rule Class <pyreason_rules>`. 

The following graph represents a network of People and a Text Message in their group chat.
.. image:: ../media/group_chat_graph.png


Graph
------------

First, we load in the GraphML. This graph has friends and text messages.

.. code:: python

   
    import networkx as nx

    # Create an empty graph
    G = nx.Graph()

    # Add nodes
    nodes = ["TextMessage", "Zach", "Justin", "Michelle", "Amy"]
    G.add_nodes_from(nodes)

    # Add edges with attribute 'HaveAccess'
    edges = [
        ("Zach", "TextMessage", {"HaveAccess": 1}),
        ("Justin", "TextMessage", {"HaveAccess": 1}),
        ("Michelle", "TextMessage", {"HaveAccess": 1}),
        ("Amy", "TextMessage", {"HaveAccess": 1})
    ]
    G.add_edges_from(edges)

Rules and Custom Thresholds
---------------------------
Considering that we only want a text message to be considered viewed by all if it has been viewed by everyone that can view it, we define the rule as follows:

..code :: text
    ViewedByAll(x) <- HaveAccess(x,y), Viewed(y)

The ``head`` of the rule is ``ViewedByAll(x)`` and the body is ``HaveAccess(x,y), Viewed(y)``. The head and body are separated by an arrow which means the rule will start evaluating from
timestep 0.

We then initialize and load the graph using the following code:

.. code:: python

    import pyreason as pr
    from pyreason import Threshold

    def test_custom_thresholds():
        # Reset PyReason
        pr.reset()
        pr.reset_rules()

        # Modify the paths based on where you've stored the files we made above
        graph_path = "group_chat_graph.graphml"

        # Modify pyreason settings to make verbose
        pr.reset_settings()
        pr.settings.verbose = True  # Print info to screen

        # Load all the files into pyreason
        pr.load_graphml(graph_path)

Add in the custom thresholds. In this graph, the custom_thresholds ensure that in order for the rules to be fired, specific criteria must be met. 

    - The first threshold means that a rule is only fired if the number of views is greater than or equal to 1.
    - The second threshold requires that the percentage of views is greater than or equal to 100%.

.. code:: python

    # add custom thresholds
    user_defined_thresholds = [
        Threshold("greater_equal", ("number", "total"), 1),
        Threshold("greater_equal", ("percent", "total"), 100),
    ]

Next, add the Rules and Facts. The custom_thresholods are passed as parameters to the new Rule. The Facts indicate at what timestep each user will view the message. 

.. code:: python

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

Run the program:

.. code:: python

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

After the first 2 timesteps TextMessage has been ViewedByAll bounds [1,1]. Before, not every member of the group chat has viewd the message and therefore, due to the custom thresholds, the rule will not fire. 
The intended output is:

.. code:: text

    Timestep: 0
    Timestep: 1
    Timestep: 2
    Timestep: 3

    Converged at time: 3
    Fixed Point iterations: 6
    TIMESTEP - 0
    Empty DataFrame
    Columns: [component, ViewedByAll]
    Index: []

    TIMESTEP - 1
    Empty DataFrame
    Columns: [component, ViewedByAll]
    Index: []

    TIMESTEP - 2
        component ViewedByAll
    0  TextMessage  [1.0, 1.0]

    TIMESTEP - 3
        component ViewedByAll
    0  TextMessage  [1.0, 1.0]
