"""
Example: Loading Fact and Rules from File
=========================================
This example demonstrates four PyReason functions for loading facts and rules from external files:
    - add_rule_from_csv
    - add_rule_from_json
    - add_fact_from_csv
    - add_fact_from_json

Scenario: 
    - A simple student-major-department knowledge graph
    - Student(alice, bob, mary) enroll in major(math, cs)
    - Majors belong to departments (math_dept, cs_dept)
    - Rule 1: if X enrolls in Z, and Z is in department of Y, then X is under department Y
    - Rule 2: if X is under department Y, and Y has scholarship, then X is eligible
    - Fact: scholarship(math_dept) - loaded from file

Both CSV and JSON loading produce identical results, the four functions are interchangeable.
"""

import networkx as nx
import pyreason as pr

# A Simple Student/Major/Department Knowledge Graph

g = nx.DiGraph()
student_names = ['alice', 'bob', 'mary']
g.add_nodes_from(student_names)

majors = ['math', 'cs']
g.add_nodes_from(majors)

departments = ['math_dept', 'cs_dept']
g.add_nodes_from(departments)

g.add_edge('alice', 'math', enroll=1)
g.add_edge('bob', 'math', enroll=1)
g.add_edge('mary', 'cs', enroll=1)

g.add_edge('math', 'math_dept', in_department=1)
g.add_edge('cs', 'cs_dept', in_department=1)

# There are different ways that you could load rules and facts from files, and here are 2 examples:

# Method 1: load rules from csv + facts from csv
print("=" * 50)
print("Method 1: Loading rules and facts from CSV")
print("=" * 50)

pr.reset()
pr.load_graph(g)
pr.add_rule_from_csv('examples/rules.csv')
pr.add_fact_from_csv('examples/facts.csv')

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
pr.add_rule_from_json('examples/rules.json')
pr.add_fact_from_json('examples/facts.json')

interpretation = pr.reason(timesteps=2)

dataframes = pr.filter_and_sort_nodes(interpretation, ['eligible'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()