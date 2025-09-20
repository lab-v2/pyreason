#!/usr/bin/env python3
"""
Debug script to examine rule grounding in detail
"""

import pyreason as pr
import networkx as nx

def debug_rule_grounding():
    print("=== DEBUGGING RULE GROUNDING IN FP VERSION ===")

    # Reset and setup
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = True

    # Create simple graph
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Add rule and facts
    rule = pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule')
    pr.add_rule(rule)
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    print(f"Rule details:")
    print(f"  Rule object: {rule}")
    print(f"  Available methods: {[method for method in dir(rule) if not method.startswith('_')]}")

    # Try to get rule attributes safely
    try:
        print(f"  Target: {rule.get_target()}")
    except:
        try:
            print(f"  Target: {rule.head}")
        except:
            print(f"  Target: Unable to access")

    try:
        print(f"  Delta: {rule.get_delta()}")
    except:
        try:
            print(f"  Delta: {rule.delta}")
        except:
            print(f"  Delta: Unable to access")

    try:
        print(f"  Is static: {rule.is_static_rule()}")
    except:
        print(f"  Is static: Unable to access")

    # Reason and debug
    interpretation = pr.reason(timesteps=1)  # Only 1 timestep to focus on issue

    print(f"\nAfter reasoning:")
    print(f"Available timesteps: {list(interpretation.interpretations_edge.keys())}")

    # Check T=0 state
    t = 0
    print(f"\nT={t} state:")
    print(f"Edge interpretations: {list(interpretation.interpretations_edge[t].keys())}")

    for edge in interpretation.interpretations_edge[t].keys():
        edge_interp = interpretation.interpretations_edge[t][edge]
        print(f"  Edge {edge}:")
        print(f"    World: {edge_interp.world}")
        if rule.get_target() in edge_interp.world:
            target_pred = edge_interp.world[rule.get_target()]
            print(f"    Target predicate '{rule.get_target()}' exists: {target_pred}")
            print(f"    Is static: {target_pred.is_static()}")
        else:
            print(f"    Target predicate '{rule.get_target()}' does NOT exist")

    # Check what the rule should produce
    print(f"\nExpected inference:")
    print(f"  Rule should infer: connected(A, C)")
    print(f"  Based on: connected(A, B) AND connected(B, C)")

    # Check if (A, C) edge exists
    target_edge = ('A', 'C')
    if target_edge in interpretation.interpretations_edge[t]:
        print(f"  Target edge {target_edge} EXISTS in interpretations")
        target_interp = interpretation.interpretations_edge[t][target_edge]
        print(f"    World: {target_interp.world}")
    else:
        print(f"  Target edge {target_edge} does NOT exist in interpretations")

if __name__ == "__main__":
    debug_rule_grounding()