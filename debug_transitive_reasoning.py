#!/usr/bin/env python3
"""
Debug script to compare transitive reasoning between regular and FP versions
"""

import pyreason as pr
import networkx as nx

def test_regular_version():
    print("=== TESTING REGULAR VERSION ===")

    # Reset and setup
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = True

    # Create simple graph
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Add rule and facts
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    # Reason
    interpretation = pr.reason(timesteps=2)

    print(f"Regular - Interpretation time: {interpretation.time}")

    # Check query
    result = interpretation.query(pr.Query('connected(A, C)'))
    print(f"Regular - connected(A, C) query result: {result}")

    # Check what edges exist
    for t in range(interpretation.time + 1):
        try:
            edges_at_t = interpretation.query(pr.Query('connected(x, y)'), t=t)
            print(f"Regular - T={t} connected edges: {edges_at_t}")
        except Exception as e:
            print(f"Regular - T={t} query error: {e}")

def test_fp_version():
    print("\n=== TESTING FP VERSION ===")

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
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    # Reason
    interpretation = pr.reason(timesteps=2)

    print(f"FP - Interpretation time: {interpretation.time}")

    # Check query
    result = interpretation.query(pr.Query('connected(A, C)'))
    print(f"FP - connected(A, C) query result: {result}")

    # Check what edges exist
    for t in range(interpretation.time + 1):
        try:
            edges_at_t = interpretation.query(pr.Query('connected(x, y)'), t=t)
            print(f"FP - T={t} connected edges: {edges_at_t}")
        except Exception as e:
            print(f"FP - T={t} query error: {e}")

    # Debug: Check interpretation structure
    print(f"FP - Available timesteps: {list(interpretation.interpretations_edge.keys()) if hasattr(interpretation, 'interpretations_edge') else 'No edge interpretations'}")

    # Manual check of edge interpretations
    if hasattr(interpretation, 'interpretations_edge'):
        for t in interpretation.interpretations_edge.keys():
            print(f"FP - T={t} edge interpretations: {list(interpretation.interpretations_edge[t].keys())}")
            for edge in interpretation.interpretations_edge[t].keys():
                print(f"    Edge {edge}: {interpretation.interpretations_edge[t][edge].world}")

if __name__ == "__main__":
    test_regular_version()
    test_fp_version()