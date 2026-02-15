"""
Example: Atom Trace with Inconsistencies
=========================================
This example demonstrates how PyReason detects and resolves inconsistencies
using the Inconsistent Predicate List (IPL) and how atom_trace provides
full explainability of what happened.

Scenario:
  - We have a small health network: Alice, Bob, and Carol.
  - "sick" and "healthy" are declared as inconsistent node predicates.
  - "close_contact" and "no_contact" are declared as inconsistent edge predicates.
  - Node inconsistencies:
      1. sick(Alice) vs healthy(Alice) — IPL-based conflict
      2. tired(Bob) with non-overlapping bounds — same-predicate conflict
  - Edge inconsistencies (triggered by rules firing):
      3. quarantine_rule infers no_contact(Alice,Bob) which conflicts with
         the close_contact(Alice,Bob) fact via the IPL
      4. distrust_rule infers trust(Bob,Carol):[0.0,0.2] which conflicts with
         the trust(Bob,Carol):[0.9,1.0] fact — same-predicate non-overlapping bounds
  - All inconsistencies are resolved to [0, 1] (complete uncertainty).
  - A rule propagates sickness through edges, showing normal (non-conflicting)
    reasoning alongside the inconsistency resolution.
"""

import pyreason as pr
import networkx as nx

# Reset PyReason to a clean state
pr.reset()
pr.reset_rules()
pr.reset_settings()

# ================================ CREATE GRAPH ================================
g = nx.DiGraph()

# People in our health network
g.add_nodes_from(['Alice', 'Bob', 'Carol', 'Dave'])

# Contact edges (who has been in contact with whom)
g.add_edge('Alice', 'Bob', contact=1)
g.add_edge('Bob', 'Carol', contact=1)
g.add_edge('Bob', 'Dave', contact=1)

# ================================ CONFIGURE ===================================
pr.settings.verbose = True
pr.settings.atom_trace = True  # Enable atom trace for full explainability
pr.settings.inconsistency_check = True  # Enable inconsistency detection (default)

# ================================ LOAD GRAPH ==================================
pr.load_graph(g)

# Declare sick and healthy as inconsistent predicates
# When one is set, PyReason automatically gives the other the negated bound
pr.add_inconsistent_predicate('sick', 'healthy')

# Declare close_contact and no_contact as inconsistent edge predicates
pr.add_inconsistent_predicate('close_contact', 'no_contact')

# ================================ ADD RULES ===================================
# If someone is sick and in contact with another person, that person may get sick
pr.add_rule(pr.Rule('sick(y):[0.5,0.7] <- sick(x):[0.5,1.0], contact(x,y)', 'spread_rule'))

# Rule that infers no_contact on an edge when both people are sick — will conflict
# with the close_contact fact on (Alice, Bob) via the IPL
pr.add_rule(pr.Rule('no_contact(x,y):[0.8,1.0] <- sick(x):[0.5,1.0], sick(y):[0.5,1.0], contact(x,y)', 'quarantine_rule'))

# Rule that infers low trust on an edge when someone is sick — will conflict
# with the high trust fact on (Bob, Carol) via same-predicate conflicting bounds
pr.add_rule(pr.Rule('trust(x,y):[0.0,0.2] <- sick(x):[0.5,1.0], contact(x,y)', 'distrust_rule'))

# Rule that infers risk on an edge (no conflict — clean edge rule for comparison)
pr.add_rule(pr.Rule('risk(x,y):[0.6,0.8] <- sick(x):[0.5,1.0], contact(x,y)', 'risk_rule'))

# ================================ ADD FACTS ===================================
# Fact 1: Alice is sick with high confidence
pr.add_fact(pr.Fact('sick(Alice):[0.8,1.0]', 'alice_sick_fact', 0, 0))

# Fact 2: Alice is also healthy with high confidence — this CONTRADICTS Fact 1
# Since sick and healthy are in the IPL, this creates an inconsistency
pr.add_fact(pr.Fact('healthy(Alice):[0.9,1.0]', 'alice_healthy_fact', 0, 0))

# Fact 3: Bob is sick (no contradiction here, normal reasoning)
pr.add_fact(pr.Fact('sick(Bob):[0.6,0.8]', 'bob_sick_fact', 0, 0))
# Fact 3.5 : Carol is Healthy (will trigger contradiction later)
pr.add_fact(pr.Fact('healthy(Carol):[0.9,1.0]', 'alice_healthy_fact', 0, 0))

# Fact 4 & 5: Bob is tired with two conflicting, non-overlapping bounds
# Since "tired" is NOT in the IPL, this triggers a same-predicate inconsistency
pr.add_fact(pr.Fact('tired(Bob):[0.8,1.0]', 'bob_tired_fact_1', 0, 0))
pr.add_fact(pr.Fact('tired(Bob):[0.0,0.1]', 'bob_tired_fact_2', 0, 0))

# Dave has no conflicting predicates — spread_rule will cleanly set sick(Dave)
# This provides a normal node rule trace entry for comparison

# ---- Edge inconsistencies (set up initial state for rule-triggered conflicts) ----
# Fact 6: Set close_contact on (Alice, Bob) — quarantine_rule will later infer
# no_contact on the same edge, triggering an IPL-based edge inconsistency
pr.add_fact(pr.Fact('close_contact(Alice,Bob):[0.8,1.0]', 'alice_bob_close_fact', 0, 0))

# Fact 7: Set high trust on (Bob, Carol) — distrust_rule will later infer
# trust:[0.0,0.2] on the same edge, triggering a same-predicate edge inconsistency
pr.add_fact(pr.Fact('trust(Bob,Carol):[0.9,1.0]', 'bob_carol_trust_high', 0, 0))

# ================================ REASON ======================================
print('=' * 60)
print('Running PyReason with inconsistency detection...')
print('=' * 60)
interpretation = pr.reason(timesteps=2)

# ================================ VIEW RESULTS ================================
print('\n' + '=' * 60)
print('Node Interpretation Changes (sick)')
print('=' * 60)
dataframes = pr.filter_and_sort_nodes(interpretation, ['sick'])
for t, df in enumerate(dataframes):
    print(f'\nTIMESTEP {t}:')
    print(df)

print('\n' + '=' * 60)
print('Node Interpretation Changes (healthy)')
print('=' * 60)
dataframes = pr.filter_and_sort_nodes(interpretation, ['healthy'])
for t, df in enumerate(dataframes):
    print(f'\nTIMESTEP {t}:')
    print(df)

# ================================ VIEW TRACE ==================================
print('\n' + '=' * 60)
print('Rule Trace (shows inconsistency resolution details)')
print('=' * 60)
node_trace, edge_trace = pr.get_rule_trace(interpretation)
print('\nNode trace:')
print(node_trace.to_string())

if not edge_trace.empty:
    print('\nEdge trace:')
    print(edge_trace.to_string())

# Save the rule trace to a file for further inspection
pr.save_rule_trace(interpretation)
print('\nRule trace saved to current directory.')
