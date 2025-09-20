#!/usr/bin/env python3
"""
Debug the edge rule application condition logic
"""

import pyreason as pr
import networkx as nx

def debug_edge_condition():
    print("=== DEBUGGING EDGE RULE APPLICATION CONDITION ===")

    # Reset and setup
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = False  # Reduce noise

    # Create simple graph
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Add rule and facts
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    # Reason for one timestep to get initial state
    interpretation = pr.reason(timesteps=1)

    print(f"After reasoning:")
    print(f"Available timesteps: {list(interpretation.interpretations_edge.keys())}")

    # Check what edges exist at T=0
    t = 0
    print(f"\nT={t} edge interpretations:")
    for edge in interpretation.interpretations_edge[t].keys():
        print(f"  Edge {edge}: {interpretation.interpretations_edge[t][edge].world}")

    # Check if the target edge (A, C) exists
    target_edge = ('A', 'C')
    print(f"\nTarget edge check:")
    print(f"  Target edge {target_edge} exists: {target_edge in interpretation.interpretations_edge[t]}")

    # This is likely the issue: the rule wants to infer connected(A, C) but edge (A, C) doesn't exist in the graph
    # The condition checking logic tries to access interpretations_edge[t][(A, C)] which doesn't exist

    print(f"\nRoot cause analysis:")
    print(f"  1. Rule should infer: connected(A, C)")
    print(f"  2. But edge (A, C) doesn't exist in initial graph")
    print(f"  3. Condition logic tries to access interpretations_edge[t][(A, C)].world")
    print(f"  4. This causes the rule to not be applied (silent failure)")

    print(f"\nExpected behavior:")
    print(f"  - Edge (A, C) should be created with connected predicate")
    print(f"  - Or condition should handle non-existent edges properly")

if __name__ == "__main__":
    debug_edge_condition()