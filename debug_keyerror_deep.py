#!/usr/bin/env python3
"""
Enhanced debug script for precise KeyError location identification
This script adds granular error detection and analysis for the remaining KeyError
"""

import pyreason as pr
import faulthandler
import traceback
import sys

def debug_fp_keyerror_location():
    print("=== ENHANCED DEBUGGING: KeyError Location Detection ===")

    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Setup FP version
    graph_path = './tests/functional/friends_graph.graphml'
    pr.settings.verbose = False  # Reduce noise to focus on KeyError
    pr.settings.fp_version = True
    pr.settings.atom_trace = True

    # Load setup
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    print("\n=== Phase 1: Initial reasoning (should work) ===")
    try:
        interpretation1 = pr.reason(timesteps=1)
        print(f"✅ Phase 1 successful: {type(interpretation1)}, time={interpretation1.time}")
        print(f"   Available timesteps: {list(interpretation1.interpretations_node.keys())}")
    except Exception as e:
        print(f"❌ Phase 1 failed: {e}")
        return

    print("\n=== Phase 2: Setting up reason again ===")
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)

    print("\n=== Phase 3: Attempting reason again with detailed error tracking ===")

    # Wrap the reason call with more granular error detection
    try:
        print("About to call pr.reason(timesteps=3, again=True, restart=False)")
        interpretation2 = pr.reason(timesteps=3, again=True, restart=False)
        print(f"✅ Reason again successful!")

        # If we get here, the KeyError was fixed
        dataframes = pr.filter_and_sort_nodes(interpretation2, ['popular'])
        print(f"Dataframes generated: {len(dataframes)} timesteps")
        print(f"Available indices: {list(range(len(dataframes)))}")

    except KeyError as ke:
        print(f"❌ KeyError caught!")
        print(f"KeyError details: {ke}")
        print(f"KeyError type: {type(ke)}")

        # Get the full traceback
        print("\n=== FULL TRACEBACK ===")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)

        print("\n=== TRACEBACK ANALYSIS ===")
        tb = exc_traceback
        frame_count = 0
        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            function_name = frame.f_code.co_name

            print(f"Frame {frame_count}:")
            print(f"  File: {filename}")
            print(f"  Function: {function_name}")
            print(f"  Line: {line_number}")

            # Look for pyreason-specific frames
            if 'pyreason' in filename and 'interpretation' in filename:
                print(f"  ⭐ PYREASON FRAME - This might be where the issue occurs")

                # Try to get local variables if possible
                if hasattr(frame, 'f_locals'):
                    print(f"  Local vars: {list(frame.f_locals.keys())}")

                    # Look for common variables that might be problematic
                    interesting_vars = ['t', 'interpretations_node', 'interpretations_edge', 'comp', 'l']
                    for var in interesting_vars:
                        if var in frame.f_locals:
                            try:
                                value = frame.f_locals[var]
                                if var == 't':
                                    print(f"    {var} = {value}")
                                elif 'interpretations' in var:
                                    if hasattr(value, 'keys'):
                                        print(f"    {var}.keys() = {list(value.keys())}")
                                    else:
                                        print(f"    {var} = {type(value)}")
                                else:
                                    print(f"    {var} = {value}")
                            except:
                                print(f"    {var} = <cannot access>")

            tb = tb.tb_next
            frame_count += 1

    except Exception as e:
        print(f"❌ Other exception: {type(e).__name__}: {e}")
        traceback.print_exc()

def compare_reasoning_approaches():
    print("\n\n=== COMPARING REGULAR vs FP REASONING APPROACHES ===")

    # Test regular version
    print("\n--- Regular Version Test ---")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    graph_path = './tests/functional/friends_graph.graphml'
    pr.settings.verbose = False
    pr.settings.fp_version = False  # Regular version
    pr.settings.atom_trace = True

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    try:
        interpretation1 = pr.reason(timesteps=1)
        print(f"✅ Regular Phase 1: {type(interpretation1)}, time={interpretation1.time}")

        new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
        pr.add_fact(new_fact)
        interpretation2 = pr.reason(timesteps=3, again=True, restart=False)
        print(f"✅ Regular Phase 2: {type(interpretation2)}, time={interpretation2.time}")

        dataframes = pr.filter_and_sort_nodes(interpretation2, ['popular'])
        print(f"✅ Regular dataframes: {len(dataframes)} timesteps")

        # Check what type of interpretation object we get
        print(f"Regular interpretation class: {interpretation2.__class__.__module__}.{interpretation2.__class__.__name__}")

    except Exception as e:
        print(f"❌ Regular version failed: {e}")

def analyze_interpretation_state():
    print("\n\n=== ANALYZING INTERPRETATION STATE AT FAILURE POINT ===")

    # Create a version that stops just before the KeyError
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    graph_path = './tests/functional/friends_graph.graphml'
    pr.settings.verbose = False
    pr.settings.fp_version = True
    pr.settings.atom_trace = True

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    # Phase 1
    interpretation1 = pr.reason(timesteps=1)
    print(f"\nAfter Phase 1:")
    print(f"  Time: {interpretation1.time}")
    print(f"  Timesteps: {list(interpretation1.interpretations_node.keys())}")
    print(f"  Nodes in each timestep:")
    for t in interpretation1.interpretations_node.keys():
        nodes = list(interpretation1.interpretations_node[t].keys())
        print(f"    t={t}: {nodes}")

    # Add new fact
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)

    print(f"\nBefore Phase 2:")
    print(f"  Previous reasoning data: {interpretation1.prev_reasoning_data}")
    print(f"  Expected to start from timestep: {interpretation1.prev_reasoning_data[0]}")

if __name__ == "__main__":
    debug_fp_keyerror_location()
    compare_reasoning_approaches()
    analyze_interpretation_state()