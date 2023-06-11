import numba
import numpy as np

import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def parse_rule(rule_text: str, name: str, infer_edges: bool = False, immediate_rule: bool = False) -> rule.Rule:
    # First remove all spaces from line
    r = rule_text.replace(' ', '')

    # Separate into head and body
    head, body = r.split('<-')

    # Extract delta_t of rule if it exists else set it to 0
    t = ''
    is_digit = True
    while is_digit:
        if body[0].isdigit():
            t += body[0]
            body = body[1:]
        else:
            is_digit = False

    if t == '':
        t = 0
    else:
        t = int(t)

    # Separate clauses in body
    body = body[:-1].replace(')', '))') + ')'
    body = body.split('),')

    # Find the target predicate
    idx = head.find('(')
    target = head[:idx]
    target = label.Label(target)

    # Variable(s) in the head of the rule
    head_variables = head[idx + 1:-1].split(',')

    # Assign type of rule
    rule_type = 'node' if len(head_variables) == 1 else 'edge'

    # Get the variables in the body
    body_predicates = []
    body_variables = []
    for clause in body:
        idx = clause.find('(')
        body_predicates.append(clause[:idx])
        body_variables.append(clause[idx+1:-1].split(','))

    # Replace the variables in the body with source/target if they match the variables in the head
    # If infer_edges is true, then we consider all rules to be node rules, we infer the 2nd variable of the target predicate from the rule body
    # Else we consider the rule to be an edge rule and replace variables with source/target
    # Node rules with possibility of adding edges
    if infer_edges or len(head_variables) == 1:
        head_source_variable = head_variables[0]
        for i in range(len(body_variables)):
            for j in range(len(body_variables[i])):
                if body_variables[i][j] == head_source_variable:
                    body_variables[i][j] = 'target'
    # Edge rule, no edges to be added
    elif len(head_variables) == 2:
        for i in range(len(body_variables)):
            for j in range(len(body_variables[i])):
                if body_variables[i][j] == head_variables[0]:
                    body_variables[i][j] = 'source'
                elif body_variables[i][j] == head_variables[1]:
                    body_variables[i][j] = 'target'

    # Start setting up clauses
    # clauses = [c1, c2, c3, c4]
    # thresholds = [t1, t2, t3, t4]

    # Array of thresholds to keep track of for each neighbor criterion. Form [(comparison, (number/percent, total/available), thresh)]
    thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64)))

    # Array to store clauses for nodes: node/edge, [subset]/[subset1, subset2], label, interval
    clauses = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, label.label_type, numba.types.UniTuple(numba.types.string, 2), interval.interval_type)))

    # Loop though clauses
    for predicate, variables in zip(body_predicates, body_variables):
        # Neigh criteria
        clause_type = 'node' if len(variables) == 1 else 'edge'
        subset = (variables[0], variables[0]) if clause_type == 'node' else (variables[0], variables[1])
        l = label.Label(predicate)
        bnd = interval.closed(1, 1)
        clauses.append((clause_type, l, subset, bnd))

        # Threshold.
        quantifier = 'greater_equal'
        quantifier_type = ('number', 'total')
        thresh = 1
        thresholds.append((quantifier, quantifier_type, thresh))

    # Assert that there are two variables in the head of the rule if we infer edges
    # Add edges between head variables if necessary
    if infer_edges:
        assert len(head_variables) == 2, 'Cannot infer edges with a node rule. There have to be two variables in the head'
        var = 'target' if head_variables[0] == head_variables[1] else head_variables[1]
        edges = ('target', var, target)
    else:
        edges = ('', '', label.Label(''))

    # Bound to set atom if rule fires
    bnd = interval.closed(1, 1)
    ann_fn = ''
    ann_label = label.Label('')

    weights = np.ones(len(body_predicates), dtype=np.float64)
    weights = np.append(weights, 0)

    r = rule.Rule(name, rule_type, target, numba.types.uint16(t), clauses, bnd, thresholds, ann_fn, ann_label, weights, edges, immediate_rule)
    return r
