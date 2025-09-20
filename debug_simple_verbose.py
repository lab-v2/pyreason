#!/usr/bin/env python3
"""
Simple verbose debugging of the transitive rule
"""

import pyreason as pr
import networkx as nx

def debug_simple():
    print("=== SIMPLE VERBOSE DEBUG ===")

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = True

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    rule = pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule')
    pr.add_rule(rule)
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    print(f"\nRule details that we can access:")
    try:
        print(f"  Rule string: {rule.rule}")
    except:
        print(f"  Rule string: Unable to access")

    interpretation = pr.reason(timesteps=1)

    print(f"\nAfter reasoning, query result:")
    result = interpretation.query(pr.Query('connected(A, C)'))
    print(f"  connected(A, C): {result}")

if __name__ == "__main__":
    debug_simple()