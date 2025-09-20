#!/usr/bin/env python3
"""
Debug script for test_reason_again_fp failure
This script implements the debugging steps from the error report
"""

import pyreason as pr
import faulthandler

def debug_reason_again_fp():
    print("=== DEBUGGING test_reason_again_fp FAILURE ===")

    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    pr.settings.fp_version = True  # Use the FP version of the reasoner
    pr.settings.atom_trace = True  # Save atom trace

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    # Run the program for initial timestep
    faulthandler.enable()
    print("\n=== PHASE 1: Initial reasoning ===")
    interpretation1 = pr.reason(timesteps=1)

    print(f"Phase 1 - Interpretation type: {type(interpretation1)}")
    print(f"Phase 1 - Time attribute: {getattr(interpretation1, 'time', 'NOT FOUND')}")
    print(f"Phase 1 - Available attributes: {[attr for attr in dir(interpretation1) if not attr.startswith('_')]}")

    # Check if interpretation has timestep data
    if hasattr(interpretation1, 'interpretations_node'):
        print(f"Phase 1 - interpretations_node keys: {list(interpretation1.interpretations_node.keys()) if hasattr(interpretation1.interpretations_node, 'keys') else 'NOT DICT-LIKE'}")

    # Now reason again
    print("\n=== PHASE 2: Adding new fact and reasoning again ===")
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)
    interpretation2 = pr.reason(timesteps=3, again=True, restart=False)

    print(f"Phase 2 - Interpretation type: {type(interpretation2)}")
    print(f"Phase 2 - Time attribute: {getattr(interpretation2, 'time', 'NOT FOUND')}")
    print(f"Phase 2 - Same object as Phase 1: {interpretation1 is interpretation2}")

    # Check if interpretation has timestep data
    if hasattr(interpretation2, 'interpretations_node'):
        print(f"Phase 2 - interpretations_node keys: {list(interpretation2.interpretations_node.keys()) if hasattr(interpretation2.interpretations_node, 'keys') else 'NOT DICT-LIKE'}")

    # Try to get dataframes and see what happens
    print("\n=== PHASE 3: Analyzing dataframes ===")
    try:
        dataframes = pr.filter_and_sort_nodes(interpretation2, ['popular'])
        print(f"Dataframes generated successfully")
        print(f"Number of dataframes: {len(dataframes)}")
        print(f"Available indices: {list(range(len(dataframes)))}")

        # Show what's in each dataframe
        for t, df in enumerate(dataframes):
            print(f'TIMESTEP - {t}: {len(df)} rows')
            if len(df) > 0:
                print(f'  Columns: {list(df.columns)}')
                print(f'  Data preview: {df.head()}')
            print()

    except Exception as e:
        print(f"ERROR generating dataframes: {e}")
        import traceback
        traceback.print_exc()

    # Test the specific assertions that are failing
    print("\n=== PHASE 4: Testing specific assertions ===")
    try:
        if 'dataframes' in locals():
            # These are the lines that are failing
            print(f"Trying to access dataframes[2]...")
            if len(dataframes) > 2:
                print(f"dataframes[2] length: {len(dataframes[2])}")
            else:
                print(f"ERROR: dataframes only has {len(dataframes)} elements, cannot access index 2")

            print(f"Trying to access dataframes[3]...")
            if len(dataframes) > 3:
                print(f"dataframes[3] length: {len(dataframes[3])}")
            else:
                print(f"ERROR: dataframes only has {len(dataframes)} elements, cannot access index 3")

            print(f"Trying to access dataframes[4]...")
            if len(dataframes) > 4:
                print(f"dataframes[4] length: {len(dataframes[4])}")
            else:
                print(f"ERROR: dataframes only has {len(dataframes)} elements, cannot access index 4")

    except Exception as e:
        print(f"ERROR in assertion testing: {e}")
        import traceback
        traceback.print_exc()

def debug_regular_version():
    print("\n\n=== COMPARING WITH REGULAR VERSION ===")

    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    pr.settings.fp_version = False  # Use the REGULAR version of the reasoner
    pr.settings.atom_trace = True  # Save atom trace

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    # Run the program for initial timestep
    faulthandler.enable()
    print("\n=== REGULAR - PHASE 1: Initial reasoning ===")
    interpretation1 = pr.reason(timesteps=1)

    print(f"Regular Phase 1 - Interpretation type: {type(interpretation1)}")
    print(f"Regular Phase 1 - Time attribute: {getattr(interpretation1, 'time', 'NOT FOUND')}")

    # Now reason again
    print("\n=== REGULAR - PHASE 2: Adding new fact and reasoning again ===")
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)
    interpretation2 = pr.reason(timesteps=3, again=True, restart=False)

    print(f"Regular Phase 2 - Interpretation type: {type(interpretation2)}")
    print(f"Regular Phase 2 - Time attribute: {getattr(interpretation2, 'time', 'NOT FOUND')}")

    # Try to get dataframes and see what happens
    print("\n=== REGULAR - PHASE 3: Analyzing dataframes ===")
    try:
        dataframes = pr.filter_and_sort_nodes(interpretation2, ['popular'])
        print(f"Regular - Dataframes generated successfully")
        print(f"Regular - Number of dataframes: {len(dataframes)}")
        print(f"Regular - Available indices: {list(range(len(dataframes)))}")

        # Show what's in each dataframe
        for t, df in enumerate(dataframes):
            print(f'Regular TIMESTEP - {t}: {len(df)} rows')
            print()

    except Exception as e:
        print(f"Regular - ERROR generating dataframes: {e}")

if __name__ == "__main__":
    debug_reason_again_fp()
    debug_regular_version()