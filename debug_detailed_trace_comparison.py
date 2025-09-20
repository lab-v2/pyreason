#!/usr/bin/env python3
"""
Generate simple trace comparison showing ordering differences
"""

import pyreason as pr

def generate_trace_comparison():
    graph_path = './tests/functional/friends_graph.graphml'

    # Regular Version
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
    rule_trace_regular = pr.get_rule_trace(interpretation_regular)[0]

    print("REGULAR VERSION TRACE:")
    for i in range(len(rule_trace_regular)):
        row = rule_trace_regular.iloc[i]
        clause_1 = row['Clause-1'] if row['Clause-1'] is not None else None
        clause_preview = f"{clause_1[0] if clause_1 and len(clause_1) > 0 else 'None'}"
        print(f"Row {i}: Time={row['Time']}, Node={row['Node']}, Due To={row['Occurred Due To']}, Clause-1[0]={clause_preview}")

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

    print("\nFP VERSION TRACE:")
    for i in range(len(rule_trace_fp)):
        row = rule_trace_fp.iloc[i]
        clause_1 = row['Clause-1'] if row['Clause-1'] is not None else None
        clause_preview = f"{clause_1[0] if clause_1 and len(clause_1) > 0 else 'None'}"
        print(f"Row {i}: Time={row['Time']}, Node={row['Node']}, Due To={row['Occurred Due To']}, Clause-1[0]={clause_preview}")

    print(f"\nTEST EXPECTS Row 2 to have ('Justin', 'Mary'):")
    print(f"Regular Row 2: {rule_trace_regular.iloc[2]['Clause-1'][0] if rule_trace_regular.iloc[2]['Clause-1'] else 'None'}")
    print(f"FP Row 2: {rule_trace_fp.iloc[2]['Clause-1'][0] if rule_trace_fp.iloc[2]['Clause-1'] else 'None - TypeError!'}")

if __name__ == "__main__":
    generate_trace_comparison()