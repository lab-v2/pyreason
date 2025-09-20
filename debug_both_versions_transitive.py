#!/usr/bin/env python3
"""
Demonstrates that transitive reasoning fails in BOTH regular and FP versions
This proves the issue is not FP-specific but affects PyReason fundamentally
"""

import pyreason as pr
import networkx as nx

def test_both_versions_transitive():
    print("=== TESTING TRANSITIVE REASONING: BOTH VERSIONS ===")
    print("This script demonstrates that both regular and FP versions fail")
    print("the same transitive reasoning test, proving it's not FP-specific.\n")

    # Test setup
    rule_str = 'connected(x, z) <-1 connected(x, y), connected(y, z)'

    print("Setup:")
    print("  Graph: A -> B -> C")
    print("  Facts: connected(A, B), connected(B, C)")
    print(f"  Rule: {rule_str}")
    print("  Expected: Should infer connected(A, C) via transitivity")
    print("=" * 60)

    # Test Regular Version
    print("\n1. TESTING REGULAR VERSION (fp_version = False)")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False  # Regular version
    pr.settings.verbose = False

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    pr.add_rule(pr.Rule(rule_str, 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation_regular = pr.reason(timesteps=2)

    # Query results
    result_ab_regular = interpretation_regular.query(pr.Query('connected(A, B)'))
    result_bc_regular = interpretation_regular.query(pr.Query('connected(B, C)'))
    result_ac_regular = interpretation_regular.query(pr.Query('connected(A, C)'))

    print(f"Regular version results:")
    print(f"  connected(A, B): {result_ab_regular}")
    print(f"  connected(B, C): {result_bc_regular}")
    print(f"  connected(A, C): {result_ac_regular} ← Should be True but isn't!")

    # Test FP Version
    print("\n2. TESTING FP VERSION (fp_version = True)")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True  # FP version
    pr.settings.verbose = False

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    pr.add_rule(pr.Rule(rule_str, 'transitive_rule'))
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    interpretation_fp = pr.reason(timesteps=2)

    # Query results
    result_ab_fp = interpretation_fp.query(pr.Query('connected(A, B)'))
    result_bc_fp = interpretation_fp.query(pr.Query('connected(B, C)'))
    result_ac_fp = interpretation_fp.query(pr.Query('connected(A, C)'))

    print(f"FP version results:")
    print(f"  connected(A, B): {result_ab_fp}")
    print(f"  connected(B, C): {result_bc_fp}")
    print(f"  connected(A, C): {result_ac_fp} ← Should be True but isn't!")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY COMPARISON")
    print("=" * 60)
    print(f"{'Query':<20} {'Regular':<10} {'FP':<10} {'Expected':<10}")
    print("-" * 50)
    print(f"{'connected(A, B)':<20} {str(result_ab_regular):<10} {str(result_ab_fp):<10} {'True':<10}")
    print(f"{'connected(B, C)':<20} {str(result_bc_regular):<10} {str(result_bc_fp):<10} {'True':<10}")
    print(f"{'connected(A, C)':<20} {str(result_ac_regular):<10} {str(result_ac_fp):<10} {'True':<10}")

    both_fail = not result_ac_regular and not result_ac_fp
    if both_fail:
        print("\n🔴 CONCLUSION: Both versions FAIL transitive reasoning!")
        print("   This proves the issue is NOT FP-specific.")
        print("   It's a fundamental limitation in PyReason's architecture.")
    else:
        print(f"\n🟡 Mixed results: Regular={result_ac_regular}, FP={result_ac_fp}")

    return {
        'regular': {'A_B': result_ab_regular, 'B_C': result_bc_regular, 'A_C': result_ac_regular},
        'fp': {'A_B': result_ab_fp, 'B_C': result_bc_fp, 'A_C': result_ac_fp}
    }

if __name__ == "__main__":
    results = test_both_versions_transitive()
    print(f"\nScript completed. Return value: {results}")