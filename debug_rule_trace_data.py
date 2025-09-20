#!/usr/bin/env python3
"""
Debug script to compare rule trace data between regular and FP versions
Focus on understanding why clause data is None in FP version
"""

import pyreason as pr

def debug_rule_trace_data():
    print("=== RULE TRACE DATA COMPARISON ===")
    print("Comparing rule trace clause data between regular and FP versions")
    print("=" * 70)

    graph_path = './tests/functional/friends_graph.graphml'

    # Test Regular Version
    print("\n1. REGULAR VERSION RULE TRACE DATA")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = False
    pr.settings.verbose = False
    pr.settings.atom_trace = True

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    interpretation_regular = pr.reason(timesteps=2)
    rule_trace_regular = pr.get_rule_trace(interpretation_regular)
    rule_trace_node_regular, _ = rule_trace_regular

    print(f"Regular version rule trace:")
    print(f"  Shape: {rule_trace_node_regular.shape}")
    print(f"  Columns: {list(rule_trace_node_regular.columns)}")

    print(f"\nRegular version - Row by row analysis:")
    for i in range(len(rule_trace_node_regular)):
        row = rule_trace_node_regular.iloc[i]
        print(f"  Row {i}: Time={row['Time']}, Node={row['Node']}, Label={row['Label']}")
        print(f"    Occurred Due To: {row['Occurred Due To']}")
        print(f"    Clause-1: {row['Clause-1']} (type: {type(row['Clause-1'])})")
        if row['Clause-1'] is not None:
            print(f"    Clause-1 length: {len(row['Clause-1']) if hasattr(row['Clause-1'], '__len__') else 'N/A'}")
            if hasattr(row['Clause-1'], '__getitem__') and len(row['Clause-1']) > 0:
                print(f"    Clause-1[0]: {row['Clause-1'][0]} (type: {type(row['Clause-1'][0])})")
        print()

    # Test FP Version
    print("\n2. FP VERSION RULE TRACE DATA")
    print("-" * 50)

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.fp_version = True
    pr.settings.verbose = False
    pr.settings.atom_trace = True

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 Friends(x,y), popular(y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    interpretation_fp = pr.reason(timesteps=2)
    rule_trace_fp = pr.get_rule_trace(interpretation_fp)
    rule_trace_node_fp, _ = rule_trace_fp

    print(f"FP version rule trace:")
    print(f"  Shape: {rule_trace_node_fp.shape}")
    print(f"  Columns: {list(rule_trace_node_fp.columns)}")

    print(f"\nFP version - Row by row analysis:")
    for i in range(len(rule_trace_node_fp)):
        row = rule_trace_node_fp.iloc[i]
        print(f"  Row {i}: Time={row['Time']}, Node={row['Node']}, Label={row['Label']}")
        print(f"    Occurred Due To: {row['Occurred Due To']}")
        print(f"    Clause-1: {row['Clause-1']} (type: {type(row['Clause-1'])})")
        if row['Clause-1'] is not None:
            print(f"    Clause-1 length: {len(row['Clause-1']) if hasattr(row['Clause-1'], '__len__') else 'N/A'}")
            if hasattr(row['Clause-1'], '__getitem__') and len(row['Clause-1']) > 0:
                print(f"    Clause-1[0]: {row['Clause-1'][0]} (type: {type(row['Clause-1'][0])})")
        print()

    # Direct comparison of raw data
    print("\n3. RAW RULE TRACE DATA COMPARISON")
    print("-" * 50)

    print(f"Regular interpretation.rule_trace_node_atoms length: {len(interpretation_regular.rule_trace_node_atoms)}")
    for i, atom_data in enumerate(interpretation_regular.rule_trace_node_atoms):
        print(f"  Regular atom {i}: {atom_data}")

    print(f"\nFP interpretation.rule_trace_node_atoms length: {len(interpretation_fp.rule_trace_node_atoms)}")
    for i, atom_data in enumerate(interpretation_fp.rule_trace_node_atoms):
        print(f"  FP atom {i}: {atom_data}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Find problematic row (should be row 2)
    problem_row_regular = rule_trace_node_regular.iloc[2] if len(rule_trace_node_regular) > 2 else None
    problem_row_fp = rule_trace_node_fp.iloc[2] if len(rule_trace_node_fp) > 2 else None

    if problem_row_regular and problem_row_fp:
        print(f"Row 2 comparison:")
        print(f"  Regular Clause-1: {problem_row_regular['Clause-1']}")
        print(f"  FP Clause-1: {problem_row_fp['Clause-1']}")

        if problem_row_regular['Clause-1'] is not None and problem_row_fp['Clause-1'] is None:
            print(f"🔴 ISSUE CONFIRMED: FP version has None where regular has data")
            print(f"  Regular would pass test: {problem_row_regular['Clause-1'][0] if len(problem_row_regular['Clause-1']) > 0 else 'NO DATA'}")
            print(f"  FP would fail with TypeError when accessing [0]")

    return {
        'regular_clause_1': problem_row_regular['Clause-1'] if problem_row_regular else None,
        'fp_clause_1': problem_row_fp['Clause-1'] if problem_row_fp else None
    }

if __name__ == "__main__":
    results = debug_rule_trace_data()
    print(f"\nScript completed. Results: {results}")