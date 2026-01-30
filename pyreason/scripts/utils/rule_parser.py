import numba
import numpy as np
from typing import Union

import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
# import pyreason.scripts.rules.rule_internal as rule
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.threshold.threshold import Threshold


def parse_rule(rule_text: str, name: str, custom_thresholds: Union[None, list, dict], infer_edges: bool = False, set_static: bool = False, weights: Union[None, np.ndarray] = None) -> rule.Rule:
    # --- Group A: Entry-point validation ---
    # V1: rule_text must be a string
    if not isinstance(rule_text, str):
        raise TypeError(f"rule_text must be a string, got {type(rule_text).__name__}")

    # V2: rule_text cannot be empty or whitespace-only
    if not rule_text.strip():
        raise ValueError("rule_text cannot be empty or whitespace only")

    # V3: Must contain exactly one '<-' separator
    arrow_count = rule_text.count('<-')
    if arrow_count != 1:
        raise ValueError(
            f"Rule must contain exactly one '<-' separator, found {arrow_count}. "
            "Use the format: 'head(X) <- body(X)'"
        )

    # First remove all spaces from line
    rule_str = rule_text.replace(' ', '')

    # Separate into head and body
    head, body = rule_str.split('<-')

    # V4: Head and body cannot be empty after split
    if not head:
        raise ValueError("Rule head cannot be empty")
    if not body:
        raise ValueError("Rule body cannot be empty")

    # Extract delta_t of rule if it exists else set it to 0
    delta_t = ''
    is_digit = True
    while is_digit:
        if body[0].isdigit():
            delta_t += body[0]
            body = body[1:]
        else:
            is_digit = False

    if delta_t == '':
        delta_t = 0
    else:
        delta_t = int(delta_t)

    # Split the body into clauses and their bounds
    body_clauses, body_bounds = _split_body_into_clauses(body)

    # Handle forall quantifier in body clauses
    for i, clause_str in enumerate(body_clauses.copy()):
        if 'forall(' in clause_str:
            # V14: Validate forall syntax — must end with ')' (the outer forall paren)
            if not clause_str.endswith(')'):
                raise ValueError(f"Malformed forall expression: '{clause_str}'. Expected 'forall(pred(vars))'")
            if not custom_thresholds:
                custom_thresholds = {}
            custom_thresholds[i] = Threshold("greater_equal", ("percent", "total"), 100)
            body_clauses[i] = clause_str[:-1].replace('forall(', '')

    # Parse the head: target predicate, bound, and annotation function
    head, target_bound, ann_fn = _parse_head(head)

    # V5: Head must contain parentheses
    idx = head.find('(')
    if idx == -1:
        raise ValueError(f"Rule head '{head}' must contain parentheses around variables")

    target = head[:idx]
    target = label.Label(target)

    # Variable(s) in the head of the rule - now supports functions like f(X, Y)
    # Find the last ')' to handle nested function calls
    end_idx = head.rfind(')')
    head_args_str = head[idx + 1:end_idx]

    # Parse head arguments which can be variables or function calls
    head_variables, head_fns, head_fns_vars = _parse_head_arguments(head_args_str)

    # Assign type of rule
    rule_type = 'node' if len(head_variables) == 1 else 'edge'

    # Get the variables in the body
    # If there's an operator in the body then discard anything that comes after the operator, but keep the variables
    body_predicates = []
    body_variables = []
    for clause_str in body_clauses:
        # V8: Body clause must contain parentheses
        start_idx = clause_str.find('(')
        if start_idx == -1:
            raise ValueError(f"Body clause '{clause_str}' must contain parentheses around variables")

        end_idx = clause_str.find(')')
        body_predicates.append(clause_str[:start_idx])

        # Add body variables depending on whether there's an operator or not
        variables = clause_str[start_idx+1:end_idx].split(',')
        start_idx = clause_str.find('(', start_idx+1)
        end_idx = clause_str.find(')', end_idx+1)
        if start_idx != -1 and end_idx != -1:
            variables += clause_str[start_idx+1:end_idx].split(',')
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

    if isinstance(custom_thresholds, list):
        if len(custom_thresholds) != num_clauses:
            raise ValueError(f'The length of custom thresholds {len(custom_thresholds)} is not equal to number of clauses {num_clauses}')
        for threshold in custom_thresholds:
            thresholds.append(threshold.to_tuple())
    elif isinstance(custom_thresholds, dict):
        # V12: Empty dict is not allowed
        if len(custom_thresholds) == 0:
            raise ValueError("custom_thresholds dict cannot be empty. Use None for default thresholds")
        if max(custom_thresholds.keys()) >= num_clauses:
            raise ValueError(f'The max clause index in the custom thresholds map {max(custom_thresholds.keys())} is greater than number of clauses {num_clauses}')
        for i in range(num_clauses):
            if i in custom_thresholds:
                thresholds.append(custom_thresholds[i].to_tuple())
            else:
                thresholds.append(('greater_equal', ('number', 'total'), 1.0))

    # If no custom thresholds provided, use defaults
    # otherwise loop through user-defined thresholds and convert to numba compatible format
    elif not custom_thresholds:
        for _ in range(num_clauses):
            thresholds.append(('greater_equal', ('number', 'total'), 1.0))

    # # Loop though clauses
    for body_clause, predicate, variables, bounds in zip(body_clauses, body_predicates, body_variables, body_bounds):
        # Neigh criteria
        clause_type = 'node' if len(variables) == 1 else 'edge'
        op = _get_operator_from_clause(body_clause)
        if op:
            clause_type = 'comparison'

        subset = numba.typed.List(variables)
        label_obj = label.Label(predicate)
        bnd = interval.closed(bounds[0], bounds[1])
        clauses.append((clause_type, label_obj, subset, bnd, op))

    # Assert that there are two variables in the head of the rule if we infer edges
    # Add edges between head variables if necessary
    if infer_edges:
        # var = '__target' if head_variables[0] == head_variables[1] else head_variables[1]
        # edges = ('__target', var, target)
        edges = (head_variables[0], head_variables[1], target)
    else:
        edges = ('', '', label.Label(''))

    if weights is None:
        weights = np.ones(len(body_predicates), dtype=np.float64)
    elif len(weights) != len(body_predicates):
        raise ValueError(f'Number of weights {len(weights)} is not equal to number of clauses {len(body_predicates)}')

    head_variables = numba.typed.List(head_variables)

    # Convert head functions and their variables to numba types
    head_fns_numba = numba.typed.List(head_fns)
    head_fns_vars_numba = numba.typed.List.empty_list(numba.types.ListType(numba.types.string))
    for vars_list in head_fns_vars:
        typed_vars_list = numba.typed.List.empty_list(numba.types.string)
        for var in vars_list:
            typed_vars_list.append(var)
        head_fns_vars_numba.append(typed_vars_list)

    result = rule.Rule(name, rule_type, target, head_variables, numba.types.uint16(delta_t), clauses, target_bound, thresholds, ann_fn, weights, head_fns_numba, head_fns_vars_numba, edges, set_static)
    return result


def _split_body_into_clauses(body):
    """Split the body string into (body_clauses, body_bounds) lists.

    Uses a double-character trick to split on clause boundaries without
    destroying closing delimiters that are part of the clause content:
      1. Double-up ')' and ']' so that splitting on '),' or '],' always
         leaves one copy of the delimiter inside the clause string.
      2. Split first on '),' then on '],' to handle both unbracketed and
         bracketed clause endings.
      3. Restore the original single characters.
      4. Attach default bounds :[1,1] (or :[0,0] for negated clauses).
      5. Split each clause on ':' to separate predicate from bound.
    """
    # Double-up closing delimiters so splitting on ")," / "]," is safe
    body = body.replace(')', '))')
    body = body.replace(']', ']]')

    # Split on clause boundaries: first '),' then '],'
    body = body.split('),')
    split_body = []
    for part in body:
        split_body.extend(part.split('],'))

    # Restore original single delimiters
    for i in range(len(split_body)):
        split_body[i] = split_body[i].replace('))', ')')
        split_body[i] = split_body[i].replace(']]', ']')

    # V7: Check for empty or malformed clauses (e.g. trailing commas, double commas)
    for i, part in enumerate(split_body):
        stripped = part.lstrip(',')
        if not stripped:
            raise ValueError(f"Body clause {i} is empty. Check for trailing commas or double commas in the rule body")
        # Leading comma indicates consecutive commas in the original rule
        if stripped != part:
            raise ValueError(f"Body clause {i} is empty. Check for trailing commas or double commas in the rule body")

    # Attach default bounds: negated clauses get [0,0], others get [1,1]
    for i in range(len(split_body)):
        if split_body[i][0] == '~':
            split_body[i] = split_body[i][1:] + ':[0,0]'
        elif split_body[i][-1] != ']':
            split_body[i] += ':[1,1]'

    # Separate each clause into predicate and bound string
    body_clauses = []
    body_bounds = []
    for part in split_body:
        # V9: Each clause must split into exactly predicate:bound
        parts = part.split(':')
        if len(parts) != 2:
            raise ValueError(f"Body clause '{part}' has invalid format: expected exactly one ':' separating predicate from bound")
        clause_str, bound_str = parts
        body_clauses.append(clause_str)
        body_bounds.append(bound_str)

    # Convert bound strings to [lower, upper] float pairs
    for i in range(len(body_bounds)):
        bound_str = body_bounds[i]
        lower, upper = _str_bound_to_bound(bound_str)
        body_bounds[i] = [lower, upper]

    return body_clauses, body_bounds


def _parse_head(head):
    """Parse the head string into (head_str, target_bound, ann_fn).

    Possible head formats:
      - pred(x)            → default bound [1,1], no annotation
      - ~pred(x)           → negated bound [0,0]
      - pred(x):[l,u]      → explicit bound
      - pred(x):fn_name    → annotation function with default bound [0,1]
    """
    # V5 (preliminary): head must contain '('
    if '(' not in head:
        raise ValueError(f"Rule head '{head}' must contain parentheses around variables")

    # V6: At most one colon allowed in head
    colon_count = head.count(':')
    if colon_count > 1:
        raise ValueError(f"Rule head contains {colon_count} colons, expected at most 1")

    # If no colon present, attach default bound
    if head[-1] == ')':
        if head[0] == '~':
            head = head[1:] + ':[0,0]'
        else:
            head += ':[1,1]'

    head_str, head_bound_str = head.split(':')

    # Determine if head_bound_str is a numeric bound or an annotation function name
    if _is_bound(head_bound_str):
        target_bound = list(_str_bound_to_bound(head_bound_str))
        target_bound = interval.closed(*target_bound)
        ann_fn = ''
    else:
        # If it looks like a bound (has brackets) but failed _is_bound, it's malformed
        if '[' in head_bound_str and ']' in head_bound_str:
            _str_bound_to_bound(head_bound_str)
        target_bound = interval.closed(0, 1)
        ann_fn = head_bound_str

    return head_str, target_bound, ann_fn


def _parse_head_arguments(head_args_str):
    """
    Parse head arguments which can be either simple variables or function calls.

    Examples:
        "X" -> head_variables=['X'], head_fns=[''], head_fns_vars=[[]]
        "X, Y" -> head_variables=['X', 'Y'], head_fns=['', ''], head_fns_vars=[[], []]
        "f(X, Y)" -> head_variables=['__temp_var_0'], head_fns=['f'], head_fns_vars=[['X', 'Y']]
        "f(X, Y), Z" -> head_variables=['__temp_var_0', 'Z'], head_fns=['f', ''], head_fns_vars=[['X', 'Y'], []]
        "f(X, Y), g(A, B)" -> head_variables=['__temp_var_0', '__temp_var_1'], head_fns=['f', 'g'], head_fns_vars=[['X', 'Y'], ['A', 'B']]
    """
    head_variables = []
    head_fns = []
    head_fns_vars = []

    if not head_args_str:
        return head_variables, head_fns, head_fns_vars

    # Split arguments by comma, being careful about nested parentheses
    args_list = []
    current_arg = ''
    paren_count = 0

    for char in head_args_str:
        if char == '(':
            paren_count += 1
            current_arg += char
        elif char == ')':
            paren_count -= 1
            current_arg += char
        elif char == ',' and paren_count == 0:
            args_list.append(current_arg.strip())
            current_arg = ''
        else:
            current_arg += char

    # Add the last argument
    if current_arg.strip():
        args_list.append(current_arg.strip())

    # Parse each argument
    for arg in args_list:
        arg = arg.strip()

        # Check if it's a function call (contains '(' and ')')
        if '(' in arg and ')' in arg:
            # Extract function name and arguments
            paren_idx = arg.find('(')
            fn_name = arg[:paren_idx]

            # Extract arguments inside the function
            fn_args_str = arg[paren_idx + 1:arg.rfind(')')]
            fn_args = [a.strip() for a in fn_args_str.split(',') if a.strip()]

            # Create a temporary variable name for this function result
            temp_var = f'__temp_var_{len(head_variables)}'

            head_variables.append(temp_var)
            head_fns.append(fn_name)
            head_fns_vars.append(fn_args)
        else:
            # It's a simple variable
            head_variables.append(arg)
            head_fns.append('')
            head_fns_vars.append([])

    return head_variables, head_fns, head_fns_vars


def _str_bound_to_bound(str_bound):
    """Convert a string bound like '[0.5,0.8]' to (float, float).

    Validates that:
      - There are exactly 2 comma-separated values
      - Both values are numeric
      - Both values are in [0, 1]
      - Lower <= upper
    """
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    parts = str_bound.split(',')

    # V10: Must have exactly 2 values
    if len(parts) != 2:
        raise ValueError(f"Bound must contain exactly 2 values, got {len(parts)}: '{str_bound}'")

    lower_str, upper_str = parts

    # V10: Values must be numeric
    try:
        lower = float(lower_str)
    except ValueError:
        raise ValueError(f"Bound lower value must be numeric, got '{lower_str}'")
    try:
        upper = float(upper_str)
    except ValueError:
        raise ValueError(f"Bound upper value must be numeric, got '{upper_str}'")

    # V10: Values must be in [0, 1]
    if lower < 0 or lower > 1:
        raise ValueError(f"Bound lower value {lower} is out of range [0, 1]")
    if upper < 0 or upper > 1:
        raise ValueError(f"Bound upper value {upper} is out of range [0, 1]")

    # V10: Lower must not exceed upper
    if lower > upper:
        raise ValueError(f"Bound lower value {lower} is greater than upper value {upper}")

    return lower, upper


def _is_bound(str_bound):
    """Check whether str_bound looks like a numeric bound (e.g. '[0.5,0.8]')
    rather than an annotation function name.

    Uses float() parsing instead of isdigit() to correctly handle negative
    numbers, scientific notation, etc.
    """
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    try:
        lower, upper = str_bound.split(',')
        # V11: Use float() instead of isdigit() for robust numeric detection
        float(lower)
        float(upper)
        result = True
    except (ValueError, AttributeError):
        result = False

    return result


def _get_operator_from_clause(clause):
    operators = ['<=', '>=', '<', '>', '==', '!=']
    for op in operators:
        if op in clause:
            return op

    # No operator found in clause
    return ''
