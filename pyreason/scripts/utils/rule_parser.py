import numba
import numpy as np

import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def parse_rule(rule_text: str, name: str, custom_thresholds: list, infer_edges: bool = False, set_static: bool = False, immediate_rule: bool = False) -> rule.Rule:
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

    # Raw parsing steps
    # 1. Remove whitespaces
    # 2. replace ) by )) and ] by ]] so that we can split without damaging the string
    # 3. Split with ), and then for each element of list, split with ], and add to new list
    # 4. Then replace ]] with ] and )) with ) in for loop
    # 5. Add :[1,1] to the end of each element if a bound is not specified
    # 6. Then split each element with :
    # 7. Transform bound strings into pr.intervals

    # 2
    body = body.replace(')', '))')
    body = body.replace(']', ']]')

    # 3
    body = body.split('),')
    split_body = []
    for b in body:
        split_body.extend(b.split('],'))

    # 4
    for i in range(len(split_body)):
        split_body[i] = split_body[i].replace('))', ')')
        split_body[i] = split_body[i].replace(']]', ']')

    # 5
    for i in range(len(split_body)):
        if split_body[i][-1] != ']':
            split_body[i] += ':[1,1]'

    # 6
    body_clauses = []
    body_bounds = []
    for b in split_body:
        clause, bound = b.split(':')
        body_clauses.append(clause)
        body_bounds.append(bound)

    # 7
    for i in range(len(body_bounds)):
        bound = body_bounds[i]
        l, u = _str_bound_to_bound(bound)
        body_bounds[i] = [l, u]

    # Find the target predicate and bounds and annotation function if any.
    # Possible heads:
    # pred(x) : [x,y]
    # pred(x) : f
    # pred(x)

    # This means there is no bound or annotation function specified
    if head[-1] == ')':
        head += ':[1,1]'

    head, head_bound = head.split(':')
    # Check if we have a bound or annotation function
    if _is_bound(head_bound):
        target_bound = list(_str_bound_to_bound(head_bound))
        target_bound = interval.closed(*target_bound)
        ann_fn = ''
    else:
        target_bound = interval.closed(0, 1)
        ann_fn = head_bound

    idx = head.find('(')
    target = head[:idx]
    target = label.Label(target)

    # Variable(s) in the head of the rule
    end_idx = head.find(')')
    head_variables = head[idx + 1:end_idx].split(',')

    # Assign type of rule
    rule_type = 'node' if len(head_variables) == 1 else 'edge'

    # Get the variables in the body
    # If there's an operator in the body then discard anything that comes after the operator, but keep the variables
    body_predicates = []
    body_variables = []
    for clause in body_clauses:
        start_idx = clause.find('(')
        end_idx = clause.find(')')
        body_predicates.append(clause[:start_idx])

        # Add body variables depending on whether there's an operator or not
        variables = clause[start_idx+1:end_idx].split(',')
        start_idx = clause.find('(', start_idx+1)
        end_idx = clause.find(')', end_idx+1)
        if start_idx != -1 and end_idx != -1:
            variables += clause[start_idx+1:end_idx].split(',')
        body_variables.append(variables)

    # Change infer edge parameter if it's a node rule
    if rule_type == 'node':
        infer_edges = False

    # Start setting up clauses
    # clauses = [c1, c2, c3, c4]
    # thresholds = [t1, t2, t3, t4]

    # Array of thresholds to keep track of for each neighbor criterion. Form [(comparison, (number/percent, total/available), thresh)]
    thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64)))

    # Array to store clauses for nodes: node/edge, [subset]/[subset1, subset2], label, interval, operator
    clauses = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, label.label_type, numba.types.ListType(numba.types.string), interval.interval_type, numba.types.string)))

    # gather count of clauses for threshold validation
    num_clauses = len(body_clauses)

    if custom_thresholds and (len(custom_thresholds) != num_clauses):
        raise Exception('The length of custom thresholds {} is not equal to number of clauses {}'
                        .format(len(custom_thresholds), num_clauses))

    # If no custom thresholds provided, use defaults
    # otherwise loop through user-defined thresholds and convert to numba compatible format
    if not custom_thresholds:
        for _ in range(num_clauses):
            thresholds.append(('greater_equal', ('number', 'total'), 1.0))
    else:
        for threshold in custom_thresholds:
            thresholds.append(threshold.to_tuple())

    # # Loop though clauses
    for body_clause, predicate, variables, bounds in zip(body_clauses, body_predicates, body_variables, body_bounds):
        # Neigh criteria
        clause_type = 'node' if len(variables) == 1 else 'edge'
        op = _get_operator_from_clause(body_clause)
        if op:
            clause_type = 'comparison'

        subset = numba.typed.List(variables)
        l = label.Label(predicate)
        bnd = interval.closed(bounds[0], bounds[1])
        clauses.append((clause_type, l, subset, bnd, op))

    # Assert that there are two variables in the head of the rule if we infer edges
    # Add edges between head variables if necessary
    if infer_edges:
        # var = '__target' if head_variables[0] == head_variables[1] else head_variables[1]
        # edges = ('__target', var, target)
        edges = (head_variables[0], head_variables[1], target)
    else:
        edges = ('', '', label.Label(''))

    weights = np.ones(len(body_predicates), dtype=np.float64)
    weights = np.append(weights, 0)

    head_variables = numba.typed.List(head_variables)

    r = rule.Rule(name, rule_type, target, head_variables, numba.types.uint16(t), clauses, target_bound, thresholds, ann_fn, weights, edges, set_static, immediate_rule)
    return r


def _str_bound_to_bound(str_bound):
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    l, u = str_bound.split(',')
    return float(l), float(u)


def _is_bound(str_bound):
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    try:
        l, u = str_bound.split(',')
        l = l.replace('.', '')
        u = u.replace('.', '')
        if l.isdigit() and u.isdigit():
            result = True
        else:
            result = False
    except:
        result = False

    return result


def _get_operator_from_clause(clause):
    operators = ['<=', '>=', '<', '>', '==', '!=']
    for op in operators:
        if op in clause:
            return op

    # No operator found in clause
    return ''
