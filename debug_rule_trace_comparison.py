#!/usr/bin/env python3
"""
Debug script to compare rule trace functionality between regular and FP versions
This will help identify why FP version returns None for rule traces
"""

import pyreason as pr
import networkx as nx

def debug_rule_trace_comparison():
    print("=== RULE TRACE COMPARISON: REGULAR vs FP ===")
    print("This script compares rule trace functionality between versions")
    print("to identify why FP version returns None.\n")

    # Test setup similar to failing test
    graph_path = './tests/functional/friends_graph.graphml'

    print("Setup:")
    print("  Graph: friends_graph.graphml")
    print("  Rule: popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)")
    print("  Fact: popular(Mary)")
    print("  Settings: atom_trace = True")
    print("=" * 70)

    # Test Regular Version
    print("\n1. TESTING REGULAR VERSION")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False  # Regular version
    pr.settings.verbose = False
    pr.settings.atom_trace = True   # Enable atom trace

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    print(f"Before reasoning - Settings:")
    print(f"  pr.settings.atom_trace: {pr.settings.atom_trace}")
    print(f"  pr.settings.store_interpretation_changes: {pr.settings.store_interpretation_changes}")

    interpretation_regular = pr.reason(timesteps=2)

    print(f"\nAfter reasoning - Interpretation object:")
    print(f"  Type: {type(interpretation_regular)}")
    print(f"  Has atom_trace attr: {hasattr(interpretation_regular, 'atom_trace')}")
    if hasattr(interpretation_regular, 'atom_trace'):
        print(f"  interpretation.atom_trace: {interpretation_regular.atom_trace}")

    print(f"  Has rule_trace_node: {hasattr(interpretation_regular, 'rule_trace_node')}")
    if hasattr(interpretation_regular, 'rule_trace_node'):
        print(f"  rule_trace_node length: {len(interpretation_regular.rule_trace_node)}")

    print(f"  Has rule_trace_node_atoms: {hasattr(interpretation_regular, 'rule_trace_node_atoms')}")
    if hasattr(interpretation_regular, 'rule_trace_node_atoms'):
        print(f"  rule_trace_node_atoms length: {len(interpretation_regular.rule_trace_node_atoms)}")

    # Test get_rule_trace function
    try:
        rule_trace_result_regular = pr.get_rule_trace(interpretation_regular)
        print(f"\nget_rule_trace result:")
        print(f"  Result is None: {rule_trace_result_regular is None}")
        if rule_trace_result_regular is not None:
            rule_trace_node_reg, rule_trace_edge_reg = rule_trace_result_regular
            print(f"  Node trace type: {type(rule_trace_node_reg)}")
            print(f"  Edge trace type: {type(rule_trace_edge_reg)}")
            if rule_trace_node_reg is not None:
                print(f"  Node trace shape: {rule_trace_node_reg.shape}")
                print(f"  Node trace columns: {list(rule_trace_node_reg.columns)}")
                if len(rule_trace_node_reg) > 2:
                    print(f"  Row 2 exists: True")
                    print(f"  Row 2 columns: {list(rule_trace_node_reg.iloc[2].index) if len(rule_trace_node_reg) > 2 else 'N/A'}")
        else:
            print("  get_rule_trace returned None!")
    except Exception as e:
        print(f"  get_rule_trace ERROR: {e}")

    # Test FP Version
    print("\n2. TESTING FP VERSION")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True   # FP version
    pr.settings.verbose = False
    pr.settings.atom_trace = True   # Enable atom trace

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    print(f"Before reasoning - Settings:")
    print(f"  pr.settings.atom_trace: {pr.settings.atom_trace}")
    print(f"  pr.settings.store_interpretation_changes: {pr.settings.store_interpretation_changes}")

    interpretation_fp = pr.reason(timesteps=2)

    print(f"\nAfter reasoning - Interpretation object:")
    print(f"  Type: {type(interpretation_fp)}")
    print(f"  Has atom_trace attr: {hasattr(interpretation_fp, 'atom_trace')}")
    if hasattr(interpretation_fp, 'atom_trace'):
        print(f"  interpretation.atom_trace: {interpretation_fp.atom_trace}")

    print(f"  Has rule_trace_node: {hasattr(interpretation_fp, 'rule_trace_node')}")
    if hasattr(interpretation_fp, 'rule_trace_node'):
        print(f"  rule_trace_node length: {len(interpretation_fp.rule_trace_node)}")

    print(f"  Has rule_trace_node_atoms: {hasattr(interpretation_fp, 'rule_trace_node_atoms')}")
    if hasattr(interpretation_fp, 'rule_trace_node_atoms'):
        print(f"  rule_trace_node_atoms length: {len(interpretation_fp.rule_trace_node_atoms)}")

    # Test get_rule_trace function
    try:
        rule_trace_result_fp = pr.get_rule_trace(interpretation_fp)
        print(f"\nget_rule_trace result:")
        print(f"  Result is None: {rule_trace_result_fp is None}")
        if rule_trace_result_fp is not None:
            rule_trace_node_fp, rule_trace_edge_fp = rule_trace_result_fp
            print(f"  Node trace type: {type(rule_trace_node_fp)}")
            print(f"  Edge trace type: {type(rule_trace_edge_fp)}")
            if rule_trace_node_fp is not None:
                print(f"  Node trace shape: {rule_trace_node_fp.shape}")
                print(f"  Node trace columns: {list(rule_trace_node_fp.columns)}")
                if len(rule_trace_node_fp) > 2:
                    print(f"  Row 2 exists: True")
                    print(f"  Row 2 columns: {list(rule_trace_node_fp.iloc[2].index) if len(rule_trace_node_fp) > 2 else 'N/A'}")
        else:
            print("  get_rule_trace returned None!")
    except Exception as e:
        print(f"  get_rule_trace ERROR: {e}")

    # Summary Comparison
    print("\n" + "=" * 70)
    print("SUMMARY COMPARISON")
    print("=" * 70)

    regular_works = rule_trace_result_regular is not None
    fp_works = rule_trace_result_fp is not None

    print(f"{'Component':<30} {'Regular':<15} {'FP':<15}")
    print("-" * 60)
    print(f"{'get_rule_trace returns data':<30} {str(regular_works):<15} {str(fp_works):<15}")

    if hasattr(interpretation_regular, 'atom_trace') and hasattr(interpretation_fp, 'atom_trace'):
        print(f"{'interpretation.atom_trace':<30} {str(interpretation_regular.atom_trace):<15} {str(interpretation_fp.atom_trace):<15}")

    if hasattr(interpretation_regular, 'rule_trace_node_atoms') and hasattr(interpretation_fp, 'rule_trace_node_atoms'):
        reg_atoms_len = len(interpretation_regular.rule_trace_node_atoms)
        fp_atoms_len = len(interpretation_fp.rule_trace_node_atoms)
        print(f"{'rule_trace_node_atoms len':<30} {str(reg_atoms_len):<15} {str(fp_atoms_len):<15}")

    if not fp_works and regular_works:
        print("\n🔴 CONCLUSION: FP version fails to generate rule traces!")
        print("   The issue is in FP interpretation's rule trace collection.")
        return {'status': 'fp_broken', 'regular_works': True, 'fp_works': False}
    elif fp_works and regular_works:
        print("\n🟢 Both versions work correctly")
        return {'status': 'both_work', 'regular_works': True, 'fp_works': True}
    else:
        print("\n🟡 Unexpected results - both may be broken")
        return {'status': 'unexpected', 'regular_works': regular_works, 'fp_works': fp_works}

if __name__ == "__main__":
    results = debug_rule_trace_comparison()
    print(f"\nScript completed. Results: {results}")