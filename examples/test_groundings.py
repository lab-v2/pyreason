import pyreason as pr
import numba
import numpy as np
import networkx as nx


# PyReason annotation function definition 
@numba.njit
def ann_fn_1(annotations, weights):
    # For each clause, sum the lower and upper bounds of its grounded atoms
    # (matches the per-clause weighted-sum pattern used by the built-in functions).
    # Then pick the clause whose (lower, upper) has the greatest Euclidean
    # distance from (1, 1) — the "least true" clause taken as a whole.
    print("Running annotation function 1")
    num_clauses = min(len(annotations), 2)
    print("Num Clauses:", num_clauses)
    clause_lowers = np.zeros(num_clauses, dtype=np.float64)
    clause_uppers = np.zeros(num_clauses, dtype=np.float64)

    for i in range(num_clauses):
        clause = annotations[i]
        print("i: ", i)
        print("Clause: ", clause)
        s_lower = 0.0
        s_upper = 0.0
        for atom in clause:
            s_lower = max(s_lower, atom.lower)
            s_upper = max(s_upper, atom.upper)
        clause_lowers[i] = s_lower
        clause_uppers[i] = s_upper

    print("Clause Lowers:", clause_lowers)
    print("Clause Uppers: ", clause_uppers)
    lower = min(np.min(clause_lowers), 1.0)
    upper = min(np.max(clause_uppers), 1.0)
    print("Lower: ", lower)
    print("Upper: ", upper)
    if lower > upper:
        return 0.0, 1.0
    return lower, upper

# 6-arg variant: in addition to (annotations, weights), receives:
#   - qualified_nodes:    per-clause list of node groundings (parallel to annotations)
#   - qualified_edges:    per-clause list of edge groundings as (src, tgt) tuples
#   - clause_labels:      per-clause predicate Label (use .value for the name)
#   - clause_variables:   per-clause list of variable names, e.g. ["CB1", "X"]
# Together these let us recover the per-grounding pairing imposed by conn(X,Y)
# without relying on body position (clause order can be rewritten by the
# reorder_clauses optimization). Identify clauses by predicate name + variable role.
#
# Body of the rule below (positions are NOT guaranteed at runtime):
#   hasLabel(CB1, X)   -> edge clause; qualified_edges[i] is [(CB1, X), ...]
#   hasLabel(CB2, Y)   -> edge clause; qualified_edges[i] is [(CB2, Y), ...]
#   conn(X, Y)         -> edge clause; qualified_edges[i] is [(X, Y), ...]
@numba.njit
def ann_fn_paired(annotations, weights, qualified_nodes, qualified_edges, clause_labels, clause_variables):
    print("---- ann_fn_paired invoked ----")
    # Pretty-print each clause's predicate label, variables, edges, and bounds.
    for i in range(len(clause_labels)):
        print("clause", i, " predicate:", clause_labels[i].value, " variables:", clause_variables[i])
        for k in range(len(qualified_edges[i])):
            print("  edge:", qualified_edges[i][k], " bound:", annotations[i][k])

    # Locate clauses by predicate name + variable role instead of body position.
    # The conn clause is the join driver: its (X, Y) edges are the only valid pairings.
    # The two hasLabel clauses are distinguished by which body variable is the head.
    # Head variable for hackerAt(CB2) is "CB2".
    head_var = "CB2"

    conn_idx = -1
    has_label_cb1_idx = -1  # hasLabel clause whose first var is NOT the head (the X side)
    has_label_cb2_idx = -1  # hasLabel clause whose first var IS the head (the Y side)
    for i in range(len(clause_labels)):
        name = clause_labels[i].value
        if name == "conn":
            conn_idx = i
        elif name == "hasLabel":
            # clause_variables[i] is [arg0, arg1] for hasLabel(arg0, arg1)
            if clause_variables[i][0] == head_var:
                has_label_cb2_idx = i
            else:
                has_label_cb1_idx = i

    if conn_idx < 0 or has_label_cb1_idx < 0 or has_label_cb2_idx < 0:
        return 0.0, 1.0

    best_lower = 0.0
    best_upper = 0.0
    found_any = False

    conn_pairs = qualified_edges[conn_idx]
    for ci in range(len(conn_pairs)):
        x_val = conn_pairs[ci][0]
        y_val = conn_pairs[ci][1]

        # Find hasLabel(CB1, X=x_val) bound by matching the X-position of that clause's edges.
        x_lower = -1.0
        x_upper = -1.0
        for k in range(len(qualified_edges[has_label_cb1_idx])):
            if qualified_edges[has_label_cb1_idx][k][1] == x_val:
                x_lower = annotations[has_label_cb1_idx][k].lower
                x_upper = annotations[has_label_cb1_idx][k].upper
                break
        if x_lower < 0.0:
            continue

        # Find hasLabel(CB2, Y=y_val) bound
        y_lower = -1.0
        y_upper = -1.0
        for k in range(len(qualified_edges[has_label_cb2_idx])):
            if qualified_edges[has_label_cb2_idx][k][1] == y_val:
                y_lower = annotations[has_label_cb2_idx][k].lower
                y_upper = annotations[has_label_cb2_idx][k].upper
                break
        if y_lower < 0.0:
            continue

        pair_lower = min(x_lower, y_lower)
        pair_upper = min(x_upper, y_upper)
        print("Pair X=", x_val, " Y=", y_val, " -> [", pair_lower, ",", pair_upper, "]")

        if not found_any or pair_lower > best_lower:
            best_lower = pair_lower
            best_upper = pair_upper
            found_any = True

    if not found_any:
        return 0.0, 1.0
    lower = min(best_lower, 1.0)
    upper = min(best_upper, 1.0)
    if lower > upper:
        return 0.0, 1.0
    return lower, upper


pr.reset()
pr.reset_rules()


pr.settings.verbose = True
pr.settings.allow_ground_rules = True
pr.settings.atom_trace = True

pr.add_fact(pr.Fact("hasLabel(a, l1):[0.5,1]"))
pr.add_fact(pr.Fact("hasLabel(a, l2):[0.6,1]"))
pr.add_fact(pr.Fact("hasLabel(a, l_unused):[0.8,1]"))
# pr.add_fact(pr.Fact("hasLabel(a, l3):[0.7,1]"))
pr.add_fact(pr.Fact("hasLabel(b, l4):[0.3,1]"))
pr.add_fact(pr.Fact("hasLabel(b, l5):[0.8,1]"))
# pr.add_fact(pr.Fact("hasLabel(a, l6):[0.01,0.1]"))
# pr.add_fact(pr.Fact("hasLabel(b, l7):[0.01,0.05]"))
pr.add_fact(pr.Fact("conn(l1, l4)"))
pr.add_fact(pr.Fact("conn(l2, l4)"))
pr.add_fact(pr.Fact("conn(l1, l5)"))
pr.add_fact(pr.Fact("conn(l1, l6)"))
# pr.add_fact(pr.Fact("hasLabel(a, l6):[0.9,1]"))
# pr.add_fact(pr.Fact("hasLabel(b, l7):[0.95,1]"))
#pr.add_fact(pr.Fact("conn1(l6, l7)"))

# Groundings for isConnected(X,Y): [0.3, 1] for conn(l1, l4 - min of [0.5, 1], [0.3, 1]), [0.3, 1] for conn(l2, l4 - min of [0.6, 0.3]),
#  and [0.5, 1] for conn(l1, l5): min of [0.5, 0.8]
#pr.add_rule(pr.Rule("isConnected(X,Y):ann_fn_1 <- hasLabel(CB1, X):[0.001,1], hasLabel(CB2,Y):[0.001,1], conn(X,Y)"))
# max of [[0.3, 1], [0.3, 1], [0.5,1]]
#pr.add_rule(pr.Rule("hackerAt(CB2):ann_fn_1 <- isConnected(X,Y):[0.001, 1],hasLabel(CB1, X):[0.001,1], hasLabel(CB2,Y):[0.001,1] ")) #add hackerAt(CB1), stepFrom(CB1,CB2)
pr.add_rule(pr.Rule("hackerAt(CB2):ann_fn_paired <- hasLabel(CB1, X):[0.001,1], hasLabel(CB2,Y):[0.001,1], conn(X,Y)"))


# pr.add_fact(pr.Fact("body1(abc1)"))
# pr.add_fact(pr.Fact("body1(abc2)"))
# pr.add_fact(pr.Fact("body2(abc1, rty1)"))
# pr.add_fact(pr.Fact("body2(abc2, rty2)"))
# pr.add_rule(pr.Rule("head(X,Y):[1,1] <-1 body1(X), body2(X,Y)"))
pr.add_annotation_function(ann_fn_1)
pr.add_annotation_function(ann_fn_paired)
# Perform reasoning for 1 timestep
interpretation = pr.reason(timesteps=1)

# Save the rule/atom trace to CSVs in the current directory
#pr.save_rule_trace(interpretation, folder='./examples')

# Filter the results for the computed 'linear_combination_function' edges
dataframes = pr.filter_and_sort_nodes(interpretation, ['hackerAt'])

# Print the resulting dataframes for each timestep
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

