#!/usr/bin/env python3
"""
Debug rule filtering and processing to see why _ground_rule isn't called
"""

import pyreason as pr
import networkx as nx

def debug_rule_processing():
    print("=== DEBUGGING RULE PROCESSING PIPELINE ===")

    # Setup
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = True  # Enable verbose to see filtering messages

    graph = nx.DiGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    pr.load_graph(graph)

    rule = pr.Rule('connected(x, z) <-1 connected(x, y), connected(y, z)', 'transitive_rule')
    pr.add_rule(rule)
    pr.add_fact(pr.Fact('connected(A, B)', 'fact1'))
    pr.add_fact(pr.Fact('connected(B, C)', 'fact2'))

    print(f"\nBefore reasoning:")
    print(f"  Rule: {rule}")

    # Simple approach: see if the rules make it to the reasoner

    # Check if the rule gets filtered out
    from pyreason.scripts.interpretation import interpretation_fp

    # Patch the reason function to see what happens to rules
    original_reason = interpretation_fp.Interpretation.reason

    def debug_reason(self, *args, **kwargs):
        print(f"\nInside Interpretation.reason:")
        print(f"  Rules parameter length: {len(args[6]) if len(args) > 6 else 'No rules arg'}")

        if len(args) > 6:
            rules = args[6]
            print(f"  Rules received: {len(rules)}")
            for i, r in enumerate(rules):
                print(f"    Rule {i}: {r}")

        return original_reason(self, *args, **kwargs)

    interpretation_fp.Interpretation.reason = debug_reason

    try:
        interpretation = pr.reason(timesteps=1)
        print(f"\nReasoning completed successfully")
    except Exception as e:
        print(f"\nError during reasoning: {e}")
        import traceback
        traceback.print_exc()
    finally:
        interpretation_fp.Interpretation.reason = original_reason

if __name__ == "__main__":
    debug_rule_processing()