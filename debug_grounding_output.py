#!/usr/bin/env python3
"""
Debug what _ground_rule actually returns for our transitive rule
"""

import pyreason as pr
import networkx as nx

# Add debugging to see what _ground_rule returns
def debug_ground_rule_output():
    print("=== DEBUGGING _ground_rule OUTPUT ===")

    # Setup
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = False

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    # Trigger the initial reasoning to get to the _ground_rule call
    # We need to patch the function temporarily to see what it returns

    # Import the interpretation module to access _ground_rule
    from pyreason.scripts.interpretation import interpretation_fp

    # Store original function
    original_ground_rule = interpretation_fp._ground_rule

    def debug_ground_rule(*args, **kwargs):
        # Call original function
        result = original_ground_rule(*args, **kwargs)
        applicable_node_rules, applicable_edge_rules = result

        print(f"\n_ground_rule called:")
        print(f"  Node rules: {len(applicable_node_rules)}")
        print(f"  Edge rules: {len(applicable_edge_rules)}")

        for i, edge_rule in enumerate(applicable_edge_rules):
            e, annotations, qualified_nodes, qualified_edges, edges_to_add = edge_rule
            print(f"  Edge rule {i}: edge={e}, annotations={annotations}")
            print(f"    qualified_nodes: {qualified_nodes}")
            print(f"    qualified_edges: {qualified_edges}")
            print(f"    edges_to_add: {edges_to_add}")

        return result

    # Patch the function
    interpretation_fp._ground_rule = debug_ground_rule

    try:
        # Run reasoning
        interpretation = pr.reason(timesteps=1)
        print(f"\nFinal result: reasoning completed")
    except Exception as e:
        print(f"\nError during reasoning: {e}")
    finally:
        # Restore original function
        interpretation_fp._ground_rule = original_ground_rule

if __name__ == "__main__":
    debug_ground_rule_output()