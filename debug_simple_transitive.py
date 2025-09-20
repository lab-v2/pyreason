#!/usr/bin/env python3
"""
Test simple transitive reasoning to see if it works at all
"""

import pyreason as pr
import networkx as nx

def test_simple_transitive():
    print("=== TESTING SIMPLE TRANSITIVE REASONING ===")

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = True

    # Create a simple graph: A -> B -> C
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Simple transitive rule
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))

    # Add facts
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    print("Facts added:")
    print("  connected(A, B)")
    print("  connected(B, C)")
    print("Rule: connected(x, z) <-1 connected(x, y), connected(y, z)")
    print("Expected: connected(A, C) should be inferred")

    interpretation = pr.reason(timesteps=3)  # Try more timesteps

    # Check what we have
    print(f"\nAfter reasoning:")
    print(f"  connected(A, B): {interpretation.query(pr.Query('connected(A, B)'))}")
    print(f"  connected(B, C): {interpretation.query(pr.Query('connected(B, C)'))}")
    print(f"  connected(A, C): {interpretation.query(pr.Query('connected(A, C)'))}")

    # Try with different rule syntax
    print("\n=== Trying different rule syntax ===")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = False

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Different rule syntax - explicit timestep
    pr.add_rule(pr.Rule('connected(x, z) <- connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation2 = pr.reason(timesteps=3)
    result2 = interpretation2.query(pr.Query('connected(A, C)'))
    print(f"  With different syntax: connected(A, C) = {result2}")

if __name__ == "__main__":
    test_simple_transitive()