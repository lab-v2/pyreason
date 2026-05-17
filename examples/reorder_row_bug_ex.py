# Minimal reproducer for the `_reorder_row` IndexError in pyreason/scripts/utils/output.py
#
# Bug: when a rule contains a clause that does NOT append anything to the
# per-row qualified-nodes / qualified-edges lists during the ground-rule pass
# (e.g. a comparison clause: `pred(x) >= 0.5`), the row ends up with fewer
# Clause-N columns than the rule has clauses. `__clause_maps[rule]` is sized to
# the full clause list, so `_reorder_row` walks past the end of the row's
# clause-column array and raises:
#
#   IndexError: index N is out of bounds for axis 0 with size N
#
# Crash site:  pyreason/scripts/utils/output.py:120
#               new_values[target_pos] = original_values[orig_pos]
#
# Trigger here: a 4-clause rule whose 1st clause is a comparison clause.
# The non-comparison clauses produce 3 Clause-N columns, but the clause map
# has key 3 → out of bounds on the size-3 array.

import os
import pyreason as pr
import networkx as nx

pr.reset()
pr.reset_rules()
pr.reset_settings()

# Minimal graph: one edge so an edge-clause can be satisfied.
g = nx.DiGraph()
g.add_nodes_from(['a', 'b'])
g.add_edge('a', 'b', friend=1)

pr.settings.verbose = True
pr.settings.atom_trace = True

pr.load_graph(g)

# Facts on the node-clause predicates so the rule can fire.
pr.add_fact(pr.Fact('p1(a)', 'p1_fact', 0, 5))
pr.add_fact(pr.Fact('p2(a)', 'p2_fact', 0, 5))

# Rule has 4 body clauses:
#   1) comparison clause  -> does NOT append to qn/qe (the trigger)
#   2) node clause        -> appends to qn/qe
#   3) edge clause        -> appends to qn/qe
#   4) node clause        -> appends to qn/qe
#
# Result: len(qn) == len(qe) == 3, max_j == 2, header has 3 Clause-N columns,
# but __clause_maps[<rule>] has keys 0..3 → orig_pos=3 indexes past the end.
pr.add_rule(pr.Rule(
    'result(x) <- score(x) >= 0.5, p1(x), friend(x, y), p2(x)',
    'reorder_row_bug_rule',
))

interpretation = pr.reason(timesteps=2)

# Sanity-check that the rule fired (so there is a trace row to walk over).
dataframes = pr.filter_and_sort_nodes(interpretation, ['result'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

# This is where it blows up — _reorder_row indexes past the end of the row's
# clause-column array because the rule has 4 clauses but only 3 columns exist.
out_dir = os.path.dirname(os.path.abspath(__file__))
pr.save_rule_trace(interpretation, out_dir)
print('save_rule_trace completed without error (bug NOT reproduced).')
