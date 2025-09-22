#!/usr/bin/env python3
"""
Deep comparison between regular and FP interpretation engines
Focus on understanding:
1. Why regular can do transitive reasoning despite same Case 1 bug
2. Why facts disappear in regular version with transitive rules
3. Whether FP version has the same fact disappearance issue
"""

import pyreason as pr
import networkx as nx

def test_fact_persistence_regular():
    """Test if facts persist in regular version with transitive rules"""
    print("=== REGULAR VERSION - FACT PERSISTENCE TEST ===")

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

    # Add transitive rule and facts
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation = pr.reason(timesteps=2)

    print("\nQuerying with return_bool=False to see bounds:")
    print(f"  connected(A, B) bounds: {interpretation.query(pr.Query('connected(A, B)'), return_bool=False)}")
    print(f"  connected(B, C) bounds: {interpretation.query(pr.Query('connected(B, C)'), return_bool=False)}")
    print(f"  connected(A, C) bounds: {interpretation.query(pr.Query('connected(A, C)'), return_bool=False)}")

    # Check at different timesteps with bounds
    print("\nBounds at different timesteps:")
    for t in range(3):
        try:
            ab_bounds = interpretation.query(pr.Query('connected(A, B)'), t, return_bool=False)
            bc_bounds = interpretation.query(pr.Query('connected(B, C)'), t, return_bool=False)
            ac_bounds = interpretation.query(pr.Query('connected(A, C)'), t, return_bool=False)
            print(f"  t={t}: A-B={ab_bounds}, B-C={bc_bounds}, A-C={ac_bounds}")
        except Exception as e:
            print(f"  t={t}: Error - {e}")

def test_fact_persistence_fp():
    """Test if facts persist in FP version with transitive rules"""
    print("\n=== FP VERSION - FACT PERSISTENCE TEST ===")

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = False  # Less verbose for comparison

    # Create simple graph
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    # Add transitive rule and facts
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation = pr.reason(timesteps=2)

    print("\nQuerying with return_bool=False to see bounds:")
    print(f"  connected(A, B) bounds: {interpretation.query(pr.Query('connected(A, B)'), return_bool=False)}")
    print(f"  connected(B, C) bounds: {interpretation.query(pr.Query('connected(B, C)'), return_bool=False)}")
    print(f"  connected(A, C) bounds: {interpretation.query(pr.Query('connected(A, C)'), return_bool=False)}")

    # Check at different timesteps with bounds
    print("\nBounds at different timesteps:")
    for t in range(3):
        try:
            ab_bounds = interpretation.query(pr.Query('connected(A, B)'), t, return_bool=False)
            bc_bounds = interpretation.query(pr.Query('connected(B, C)'), t, return_bool=False)
            ac_bounds = interpretation.query(pr.Query('connected(A, C)'), t, return_bool=False)
            print(f"  t={t}: A-B={ab_bounds}, B-C={bc_bounds}, A-C={ac_bounds}")
        except Exception as e:
            print(f"  t={t}: Error - {e}")

def test_transitive_with_more_edges():
    """Test both versions with more edges to trigger Case 1 over-grounding"""
    print("\n=== TESTING WITH MORE EDGES TO TRIGGER CASE 1 BUG ===")

    # Create a graph with multiple connected edges to trigger over-grounding
    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "D")
    graph.add_edge("D", "E")

    # Test Regular Version
    print("\nREGULAR VERSION with multiple edges:")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = True

    pr.load_graph(graph)
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))
    pr.add_fact(pr.Fact('connected(C, D)', 'fact3'))
    pr.add_fact(pr.Fact('connected(D, E)', 'fact4'))

    interpretation_reg = pr.reason(timesteps=3)

    print("Regular results with multiple edges:")
    print(f"  connected(A, B): {interpretation_reg.query(pr.Query('connected(A, B)'))}")
    print(f"  connected(B, C): {interpretation_reg.query(pr.Query('connected(B, C)'))}")
    print(f"  connected(C, D): {interpretation_reg.query(pr.Query('connected(C, D)'))}")
    print(f"  connected(A, D): {interpretation_reg.query(pr.Query('connected(A, D)'))}")

    # Test FP Version
    print("\nFP VERSION with multiple edges:")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = False

    pr.load_graph(graph)
    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))
    pr.add_fact(pr.Fact('connected(C, D)', 'fact3'))
    pr.add_fact(pr.Fact('connected(D, E)', 'fact4'))

    interpretation_fp = pr.reason(timesteps=3)

    print("FP results with multiple edges:")
    print(f"  connected(A, B): {interpretation_fp.query(pr.Query('connected(A, B)'))}")
    print(f"  connected(B, C): {interpretation_fp.query(pr.Query('connected(B, C)'))}")
    print(f"  connected(C, D): {interpretation_fp.query(pr.Query('connected(C, D)'))}")
    print(f"  connected(A, D): {interpretation_fp.query(pr.Query('connected(A, D)'))}")

def compare_case_1_behavior():
    """Compare how Case 1 logic behaves in both versions"""
    print("\n=== COMPARING CASE 1 BEHAVIOR ===")

    # We can't directly call the case 1 function, but we can look at the debug output
    # when both variables are new (which triggers Case 1)

    print("\nRegular version Case 1 behavior:")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = True

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("X", "Y")  # Extra edge to create multiple options
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))
    pr.add_fact(pr.Fact('connected(X, Y)', 'fact3'))  # This should trigger over-grounding if bug exists

    print("Running regular version...")
    interpretation_reg = pr.reason(timesteps=2)

    print(f"\nRegular results:")
    print(f"  connected(A, C): {interpretation_reg.query(pr.Query('connected(A, C)'))}")
    print(f"  connected(X, Y): {interpretation_reg.query(pr.Query('connected(X, Y)'))}")


    print("\FP version Case 1 behavior:")
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = True

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("X", "Y")  # Extra edge to create multiple options
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule', infer_edges=True))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))
    pr.add_fact(pr.Fact('connected(X, Y)', 'fact3'))  # This should trigger over-grounding if bug exists

    print("Running regular version...")
    interpretation_reg = pr.reason(timesteps=2)

    print(f"\nRegular results:")
    print(f"  connected(A, C): {interpretation_reg.query(pr.Query('connected(A, C)'))}")
    print(f"  connected(X, Y): {interpretation_reg.query(pr.Query('connected(X, Y)'))}")

if __name__ == "__main__":
    print("DEEP COMPARISON: REGULAR vs FP INTERPRETATION ENGINES")
    print("=" * 70)

    # Test 1: Fact persistence in both versions
    test_fact_persistence_regular()
    test_fact_persistence_fp()

    # Test 2: More complex scenarios to trigger Case 1 bug
    test_transitive_with_more_edges()

    # Test 3: Compare Case 1 behavior
    compare_case_1_behavior()

    print("\n" + "=" * 70)
    print("INVESTIGATION COMPLETE")
    print("=" * 70)