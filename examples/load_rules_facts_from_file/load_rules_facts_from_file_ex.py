"""
...
Scenario:
    - A simple student-major-department knowledge graph
    - Students (alice, bob, mary) enroll in majors (math, cs) via graph edges
    - in_department and scholarship facts are loaded from external files
      to demonstrate separation of graph structure from logical knowledge
    - Rule 1: if X enrolls in Z, and Z is in department Y, then X is under department Y
    - Rule 2: if X is under department Y, and Y has scholarship, then X is eligible

Both CSV and JSON loading produce identical results — the four functions are interchangeable.
"""

import networkx as nx
import pyreason as pr

# A simple Student/Major/Department Knowledge Graph
# Graph structure: nodes and enrollment edges only

# in_department and scholarship relationships are intentionally omitted here
# we loaded them as facts from CSV/JSON files instead

g = nx.DiGraph()
g.add_nodes_from(['alice', 'bob', 'mary'])   # students
g.add_nodes_from(['math', 'cs'])             # majors
g.add_nodes_from(['math_dept', 'cs_dept'])   # departments

g.add_edge('alice', 'math', enroll=1)
g.add_edge('bob', 'math', enroll=1)
g.add_edge('mary', 'cs', enroll=1)

# There are different ways that you could load rules and facts from files, and here are 2 examples:
# Both methods below produce identical results.
# Method 1 uses CSV files, Method 2 uses JSON files.

# Method 1: load rules from csv + facts from csv
print("=" * 50)
print("Method 1: Loading rules and facts from CSV")
print("=" * 50)

pr.reset()
pr.load_graph(g)
pr.add_rule_from_csv('examples/load_rules_facts_from_file/inputs/rules.csv')
pr.add_fact_from_csv('examples/load_rules_facts_from_file/inputs/facts.csv')

interpretation = pr.reason(timesteps=2)

dataframes = pr.filter_and_sort_nodes(interpretation, ['eligible'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()


# Method 2: load rules from json + facts from json
print("=" * 50)
print("Method 2: Loading rules and facts from JSON")
print("=" * 50)

pr.reset()
pr.load_graph(g)
pr.add_rule_from_json('examples/load_rules_facts_from_file/inputs/rules.json')
pr.add_fact_from_json('examples/load_rules_facts_from_file/inputs/facts.json')

interpretation = pr.reason(timesteps=2)

dataframes = pr.filter_and_sort_nodes(interpretation, ['eligible'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()