"""Debug script for test_custom_thresholds parallel mode issue."""
import pyreason as pr
from pyreason import Threshold


def main():
    # Setup parallel mode
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = False  # Disable verbose to speed up
    pr.settings.parallel_computing = True
    pr.settings.atom_trace = True

    print("=" * 80)
    print("CUSTOM THRESHOLDS PARALLEL MODE DEBUG")
    print("=" * 80)
    print(f"Settings:")
    print(f"  parallel_computing: {pr.settings.parallel_computing}")
    print(f"  atom_trace: {pr.settings.atom_trace}")

    # Load graph
    graph_path = "./tests/functional/group_chat_graph.graphml"
    print(f"\nLoading graph from: {graph_path}")
    pr.load_graphml(graph_path)

    # Add custom thresholds
    user_defined_thresholds = [
        Threshold("greater_equal", ("number", "total"), 1),
        Threshold("greater_equal", ("percent", "total"), 100),
    ]
    print(f"\nCustom thresholds: {user_defined_thresholds}")

    # Add rule
    pr.add_rule(
        pr.Rule(
            "ViewedByAll(y) <- HaveAccess(x,y), Viewed(x)",
            "viewed_by_all_rule",
            custom_thresholds=user_defined_thresholds,
        )
    )
    print("Rule added: ViewedByAll(y) <- HaveAccess(x,y), Viewed(x)")

    # Add facts
    pr.add_fact(pr.Fact("Viewed(Zach)", "seen-fact-zach", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Justin)", "seen-fact-justin", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Michelle)", "seen-fact-michelle", 1, 3))
    pr.add_fact(pr.Fact("Viewed(Amy)", "seen-fact-amy", 2, 3))
    print("\nFacts added:")
    print("  Viewed(Zach) at t=0")
    print("  Viewed(Justin) at t=0")
    print("  Viewed(Michelle) at t=1")
    print("  Viewed(Amy) at t=2")

    # Run reasoning
    print("\n" + "=" * 80)
    print("Running reasoning for 3 timesteps...")
    print("=" * 80)
    interpretation = pr.reason(timesteps=3)
    print("Reasoning completed!")

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS - ViewedByAll at each timestep")
    print("=" * 80)

    dataframes = pr.filter_and_sort_nodes(interpretation, ["ViewedByAll"])
    for t, df in enumerate(dataframes):
        print(f"\nTIMESTEP {t}:")
        print(f"  Number of nodes with ViewedByAll: {len(df)}")
        if len(df) > 0:
            print(df)
        else:
            print("  (no nodes with ViewedByAll)")

    # Check specific assertions
    print("\n" + "=" * 80)
    print("ASSERTION CHECKS")
    print("=" * 80)

    t0_check = len(dataframes[0]) == 0
    print(f"✓ t=0: ViewedByAll count = {len(dataframes[0])} (expected: 0) - {'PASS' if t0_check else 'FAIL'}")

    t2_check = len(dataframes[2]) == 1
    print(f"✓ t=2: ViewedByAll count = {len(dataframes[2])} (expected: 1) - {'PASS' if t2_check else 'FAIL'}")

    if len(dataframes[2]) > 0:
        has_textmsg = "TextMessage" in dataframes[2]["component"].values
        if has_textmsg:
            bounds = dataframes[2].iloc[0].ViewedByAll
            bounds_check = bounds == [1, 1]
            print(f"✓ t=2: TextMessage bounds = {bounds} (expected: [1, 1]) - {'PASS' if bounds_check else 'FAIL'}")
        else:
            print(f"✗ t=2: TextMessage not found in ViewedByAll nodes")
            print(f"     Available nodes: {dataframes[2]['component'].values}")
    else:
        print("✗ t=2: No ViewedByAll nodes found (expected TextMessage)")

    # Additional debugging: show all Viewed facts at each timestep
    print("\n" + "=" * 80)
    print("DEBUG - Viewed nodes at each timestep")
    print("=" * 80)
    viewed_dataframes = pr.filter_and_sort_nodes(interpretation, ["Viewed"])
    for t, df in enumerate(viewed_dataframes):
        print(f"\nTIMESTEP {t}:")
        if len(df) > 0:
            print(df)
        else:
            print("  (no Viewed nodes)")

    # Show HaveAccess edges if possible
    print("\n" + "=" * 80)
    print("DEBUG - HaveAccess edges")
    print("=" * 80)
    try:
        access_dataframes = pr.filter_and_sort_edges(interpretation, ["HaveAccess"])
        print(f"Number of HaveAccess edges at t=0: {len(access_dataframes[0]) if access_dataframes else 'N/A'}")
        if access_dataframes and len(access_dataframes[0]) > 0:
            print("\nSample HaveAccess edges:")
            print(access_dataframes[0].head(10))
    except Exception as e:
        print(f"Could not retrieve HaveAccess edges: {e}")


if __name__ == "__main__":
    main()