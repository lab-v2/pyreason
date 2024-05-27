# Test if the simple program works with thresholds defined
import pyreason as pr
from pyreason import Threshold


def test_custom_thresholds():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()

    # Modify the paths based on where you've stored the files we made above
    graph_path = "./tests/group_chat_graph.graphml"

    # Modify pyreason settings to make verbose and to save the rule trace to a file
    pr.settings.verbose = True  # Print info to screen

    # Load all the files into pyreason
    pr.load_graphml(graph_path)

    # add custom thresholds
    user_defined_thresholds = [
        Threshold("greater_equal", ("number", "total"), 1),
        Threshold("greater_equal", ("percent", "total"), 100),
    ]

    pr.add_rule(
        pr.Rule(
            "ViewedByAll(x) <- HaveAccess(x,y), Viewed(y)",
            "viewed_by_all_rule",
            custom_thresholds=user_defined_thresholds,
        )
    )

    pr.add_fact(pr.Fact("seen-fact-zach", "Zach", "Viewed", [1, 1], 0, 3))
    pr.add_fact(pr.Fact("seen-fact-justin", "Justin", "Viewed", [1, 1], 0, 3))
    pr.add_fact(pr.Fact("seen-fact-michelle", "Michelle", "Viewed", [1, 1], 1, 3))
    pr.add_fact(pr.Fact("seen-fact-amy", "Amy", "Viewed", [1, 1], 2, 3))

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
