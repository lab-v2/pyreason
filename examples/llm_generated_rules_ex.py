"""
LLM-Generated PyReason Rules Example
====================================
Demonstrates using Claude to generate a specific PyReason rule for a student-major-department knowledge graph,
then validates and runs inference

SETUP (Mac/Linux):
    export ANTHROPIC_API_KEY=your_key_here

SETUP (Windows PowerShell):
    $env:ANTHROPIC_API_KEY="your_key_here"
"""

import os
import sys
import anthropic
import pyreason as pr
import networkx as nx


# ================================ CREATE GRAPH ================================
g = nx.DiGraph()

# A simple Student-Major-Department KG
g.add_edge('alice', 'math', major_in=1)
g.add_edge('bob',   'math', major_in=1)
g.add_edge('mary',  'cs',   major_in=1)

# Major -> Department
g.add_edge('math', 'math_dept', in_department=1)
g.add_edge('cs',   'cs_dept',   in_department=1)


# ================================ PROMPT ======================================
PROMPT = """\
You are generating a rule for a PyReason knowledge graph.

### Task
Write a single PyReason rule that derives which department a student belongs to,
given that a student is enrolled in a major and that major belongs to a department.

### Available predicates
- major_in(Student, Major) - student in enrolled in a major
- in_department(Major, Department) - major belongs to a department

### PyReason rule syntax
head_predicate(X,Y) <-N body_predicate_1(X,Z),body_predicates_2(Z,Y)

- N is the delta: use 0 for immediate firing
- Variables are single uppercase letters (X,Y,Z)
- Head predicate name must be: student_in_dept

### Output format
Output the rule on a single line. No explanation, no markdown, no punctuation.

### Example (Different predicates, shows syntax only)
grandparent(X,Y)<-0 parent(X,Z),parent(Z,Y)
"""


# ================================ CALL CLAUDE ================================
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("Error: set ANTHROPIC_API_KEY before running.")

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": PROMPT}],
)

rule_str = response.content[0].text.strip()
print(f"Generated rule: {rule_str}")


# ================================ VALIDATE ====================================
try: 
    pr.Rule(rule_str)
    print(f"[VALID] {rule_str}")
except Exception as e:
    sys.exit(f"[INVALID] {rule_str}\nError: {e}")

# ================================ LOAD + REASON ==============================
pr.settings.verbose = False
pr.load_graph(g)
pr.add_rule(pr.Rule(rule_str, name="student_in_dept_rule",infer_edges=True))

interpretation = pr.reason(timesteps=2)


# ================================ VIEW RESULTS ===============================
print("\nInferred student-department relationships: ")
for df in pr.filter_and_sort_edges(interpretation, ["student_in_dept"]):
    if not df.empty:
        print(df.to_string())