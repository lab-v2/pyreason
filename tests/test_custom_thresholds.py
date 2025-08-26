# Test if the simple program works with thresholds defined
import pyreason as pr
from pyreason import Threshold


def test_custom_thresholds():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()

    # Modify the paths based on where you've stored the files we made above
    graph_path = "./tests/group_chat_graph.graphml"

    # Modify pyreason settings to make verbose
    pr.reset_settings()
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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f"TIMESTEP - {t}")
        viewed_by_all_nodes = []
        for component, labels in timestep_data.items():
            if 'ViewedByAll' in labels:
                viewed_by_all_nodes.append((component, labels['ViewedByAll']))
        print(f"ViewedByAll nodes: {viewed_by_all_nodes}")
        print()

    # Check the number of NEWLY ADDED ViewedByAll nodes at each timestep
    viewed_by_all_counts = {}
    
    for t in sorted(interpretation_dict.keys()):
        current_viewed_by_all = set()
        for component, labels in interpretation_dict[t].items():
            if 'ViewedByAll' in labels and labels['ViewedByAll'] == [1, 1]:
                current_viewed_by_all.add(component)
        
        if t == min(interpretation_dict.keys()):
            # At the first timestep, all ViewedByAll nodes are newly added (initial facts)
            newly_added = len(current_viewed_by_all)
        else:
            # For subsequent timesteps, compare with previous timestep
            previous_viewed_by_all = set()
            for component, labels in interpretation_dict[t-1].items():
                if 'ViewedByAll' in labels and labels['ViewedByAll'] == [1, 1]:
                    previous_viewed_by_all.add(component)
            newly_added = len(current_viewed_by_all - previous_viewed_by_all)
        
        viewed_by_all_counts[t] = newly_added

    assert (
        viewed_by_all_counts[0] == 0
    ), "At t=0 the TextMessage should not have been ViewedByAll"
    assert (
        viewed_by_all_counts[2] == 1
    ), "At t=2 the TextMessage should have been newly added as ViewedByAll"

    # TextMessage should be ViewedByAll in t=2
    if 2 in interpretation_dict:
        textmessage_viewed = any(component == 'TextMessage' and labels.get('ViewedByAll') == [1, 1] 
                                for component, labels in interpretation_dict[2].items())
        assert textmessage_viewed, "TextMessage should have ViewedByAll bounds [1,1] for t=2 timesteps"
