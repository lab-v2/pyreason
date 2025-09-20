#!/usr/bin/env python3
"""
Debug script that replicates the exact failing test to identify the precise issue
"""

import pyreason as pr

def debug_exact_test_failure():
    print("=== DEBUGGING EXACT TEST FAILURE ===")
    print("Replicating test_reorder_clauses_fp step by step")
    print("=" * 60)

    # Reset PyReason (exactly like the test)
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose (exactly like the test)
    pr.settings.verbose = True     # Print info to screen
    pr.settings.fp_version = True  # Use the FP version of the reasoner
    pr.settings.atom_trace = True  # Print atom trace

    print(f"Settings configured:")
    print(f"  verbose: {pr.settings.verbose}")
    print(f"  fp_version: {pr.settings.fp_version}")
    print(f"  atom_trace: {pr.settings.atom_trace}")
    print(f"  store_interpretation_changes: {pr.settings.store_interpretation_changes}")

    # Load all the files into pyreason (exactly like the test)
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    print(f"\nGraph and rules loaded successfully")

    # Run the program for two timesteps to see the diffusion take place (exactly like the test)
    print(f"\nCalling pr.reason(timesteps=2)...")
    interpretation = pr.reason(timesteps=2)

    print(f"\nAfter reasoning:")
    print(f"  interpretation type: {type(interpretation)}")
    print(f"  interpretation.atom_trace: {getattr(interpretation, 'atom_trace', 'NOT FOUND')}")

    # Display the changes in the interpretation for each timestep (exactly like the test)
    print(f"\nCalling pr.filter_and_sort_nodes...")
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])

    print(f"Dataframes lengths: {[len(df) for df in dataframes]}")

    # Run all the assertions from the test
    try:
        assert len(dataframes[0]) == 1, 'At t=0 there should be one popular person'
        print(f"✅ Assert 1 passed: {len(dataframes[0])} == 1")
    except AssertionError as e:
        print(f"❌ Assert 1 failed: {e}")
        return False

    try:
        assert len(dataframes[1]) == 2, 'At t=1 there should be two popular people'
        print(f"✅ Assert 2 passed: {len(dataframes[1])} == 2")
    except AssertionError as e:
        print(f"❌ Assert 2 failed: {e}")
        return False

    try:
        assert len(dataframes[2]) == 3, 'At t=2 there should be three popular people'
        print(f"✅ Assert 3 passed: {len(dataframes[2])} == 3")
    except AssertionError as e:
        print(f"❌ Assert 3 failed: {e}")
        return False

    # Test the problematic line
    print(f"\n🔍 NOW TESTING THE PROBLEMATIC LINE:")
    print(f"Calling pr.get_rule_trace(interpretation)...")

    try:
        rule_trace_result = pr.get_rule_trace(interpretation)
        print(f"  get_rule_trace returned: {type(rule_trace_result)}")

        if rule_trace_result is None:
            print(f"❌ PROBLEM: get_rule_trace returned None!")
            return False

        rule_trace_node, rule_trace_edge = rule_trace_result
        print(f"  rule_trace_node: {type(rule_trace_node)}")
        print(f"  rule_trace_edge: {type(rule_trace_edge)}")

        if rule_trace_node is None:
            print(f"❌ PROBLEM: rule_trace_node is None!")
            return False

        print(f"  rule_trace_node.shape: {rule_trace_node.shape}")
        print(f"  rule_trace_node.columns: {list(rule_trace_node.columns)}")

        # Check if we have enough rows
        if len(rule_trace_node) <= 2:
            print(f"❌ PROBLEM: rule_trace_node only has {len(rule_trace_node)} rows, need at least 3!")
            return False

        print(f"✅ Row 2 exists (total rows: {len(rule_trace_node)})")

        # Check if 'Clause-1' column exists
        if 'Clause-1' not in rule_trace_node.columns:
            print(f"❌ PROBLEM: 'Clause-1' column not found in: {list(rule_trace_node.columns)}")
            return False

        print(f"✅ 'Clause-1' column exists")

        # Check row 2 specifically
        row_2_data = rule_trace_node.iloc[2]
        print(f"  Row 2 data type: {type(row_2_data)}")
        print(f"  Row 2 'Clause-1': {row_2_data['Clause-1']}")
        print(f"  Row 2 'Clause-1' type: {type(row_2_data['Clause-1'])}")

        if row_2_data['Clause-1'] is None:
            print(f"❌ PROBLEM: Row 2 'Clause-1' is None!")
            return False

        # Final test - access [0] element
        clause_1_data = row_2_data['Clause-1']
        print(f"  Attempting to access clause_1_data[0]...")

        if hasattr(clause_1_data, '__getitem__'):
            try:
                first_element = clause_1_data[0]
                print(f"✅ clause_1_data[0] = {first_element}")
                print(f"  Type: {type(first_element)}")

                # Test the final comparison
                if first_element == ('Justin', 'Mary'):
                    print(f"✅ FINAL TEST PASSED: {first_element} == ('Justin', 'Mary')")
                    return True
                else:
                    print(f"❌ FINAL TEST FAILED: {first_element} != ('Justin', 'Mary')")
                    return False

            except Exception as e:
                print(f"❌ ERROR accessing clause_1_data[0]: {e}")
                return False
        else:
            print(f"❌ PROBLEM: clause_1_data is not subscriptable: {type(clause_1_data)}")
            return False

    except Exception as e:
        print(f"❌ ERROR in get_rule_trace or processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_exact_test_failure()
    print(f"\n{'='*60}")
    if success:
        print("🎉 DEBUG SUCCESS: All steps completed without error!")
    else:
        print("💥 DEBUG FAILED: Found the issue!")
    print(f"{'='*60}")