#!/usr/bin/env python3
"""
Test if regular version actually works with transitive reasoning
"""

import pyreason as pr
import networkx as nx

def test_regular_transitive():
    print("=== TESTING REGULAR VERSION TRANSITIVE REASONING ===")

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False  # Regular version
    pr.settings.verbose = True

    # Same setup as failing FP test
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation = pr.reason(timesteps=2)

    # Test the query
    result = interpretation.query(pr.Query('connected(A, C)'))
    print(f"Regular version result: connected(A, C) = {result}")

    return result

if __name__ == "__main__":
    test_regular_transitive()