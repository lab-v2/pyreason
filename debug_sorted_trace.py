#!/usr/bin/env python3
"""
Test what happens when we sort the trace by time
"""

import pyreason as pr

def test_sorted_trace():
    graph_path = './tests/functional/friends_graph.graphml'

    # FP Version
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
    rule_trace_fp = pr.get_rule_trace(interpretation_fp)[0]

    print("ORIGINAL FP TRACE:")
    for i in range(len(rule_trace_fp)):
        row = rule_trace_fp.iloc[i]
        clause_1 = row['Clause-1'] if row['Clause-1'] is not None else None
        clause_preview = f"{clause_1[0] if clause_1 and len(clause_1) > 0 else 'None'}"
        print(f"Row {i}: Time={row['Time']}, Node={row['Node']}, Due To={row['Occurred Due To']}, Clause-1[0]={clause_preview}")

    # Sort by time and node
    rule_trace_sorted = rule_trace_fp.sort_values(['Time', 'Node']).reset_index(drop=True)

    print("\nSORTED FP TRACE:")
    for i in range(len(rule_trace_sorted)):
        row = rule_trace_sorted.iloc[i]
        clause_1 = row['Clause-1'] if row['Clause-1'] is not None else None
        clause_preview = f"{clause_1[0] if clause_1 and len(clause_1) > 0 else 'None'}"
        print(f"Row {i}: Time={row['Time']}, Node={row['Node']}, Due To={row['Occurred Due To']}, Clause-1[0]={clause_preview}")

    print(f"\nTEST WOULD CHECK Row 2:")
    row_2 = rule_trace_sorted.iloc[2]
    print(f"Row 2: Time={row_2['Time']}, Node={row_2['Node']}, Due To={row_2['Occurred Due To']}")
    print(f"Row 2 Clause-1: {row_2['Clause-1']}")

if __name__ == "__main__":
    test_sorted_trace()