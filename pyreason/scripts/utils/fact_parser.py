import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import re


def parse_fact(fact_text):
    # Validate input is not empty or whitespace only
    if not fact_text or not fact_text.strip():
        raise ValueError("Fact text cannot be empty or whitespace only")

    f = fact_text.replace(' ', '')

    # Validate no empty string after whitespace removal
    if not f:
        raise ValueError("Fact text cannot be empty after removing whitespace")

    # Check for multiple colons
    colon_count = f.count(':')
    if colon_count > 1:
        raise ValueError(f"Fact text contains multiple colons ({colon_count}), expected at most 1")

    # Check for double negation
    if f.startswith('~~'):
        raise ValueError("Double negation is not allowed")

    # Separate into predicate-component and bound. If there is no bound it means it's true
    if ':' in f:
        parts = f.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid fact format: expected at most one colon separator")
        pred_comp, bound = parts

        # Check for negation with explicit bound (ambiguous)
        if pred_comp.startswith('~'):
            raise ValueError("Cannot use negation (~) with explicit bound - ambiguous syntax")
    else:
        pred_comp = f
        if pred_comp.startswith('~'):
            bound = 'False'
            pred_comp = pred_comp[1:]
        else:
            bound = 'True'

    # Validate predicate-component is not empty
    if not pred_comp:
        raise ValueError("Predicate-component cannot be empty")

    # Validate parentheses exist and are properly formed
    if '(' not in pred_comp:
        raise ValueError("Missing opening parenthesis in fact")
    if ')' not in pred_comp:
        raise ValueError("Missing closing parenthesis in fact")

    # Check for nested or multiple parentheses
    open_count = pred_comp.count('(')
    close_count = pred_comp.count(')')
    if open_count != 1 or close_count != 1:
        raise ValueError(f"Invalid parentheses: found {open_count} '(' and {close_count} ')', expected exactly 1 of each")

    # Check parentheses are in correct order
    open_idx = pred_comp.find('(')
    close_idx = pred_comp.find(')')
    if open_idx >= close_idx:
        raise ValueError("Invalid parentheses order: '(' must come before ')'")

    # Check closing parenthesis is at the end
    if close_idx != len(pred_comp) - 1:
        raise ValueError("Closing parenthesis must be at the end of predicate-component")

    # Split the predicate and component
    idx = pred_comp.find('(')
    pred = pred_comp[:idx]
    component = pred_comp[idx + 1:-1]

    # Validate predicate is not empty
    if not pred:
        raise ValueError("Predicate cannot be empty")

    # Validate predicate contains only valid characters (alphanumeric and underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', pred):
        raise ValueError(f"Predicate '{pred}' contains invalid characters. Only alphanumeric and underscore allowed")

    # Validate component is not empty
    if not component:
        raise ValueError("Component cannot be empty")

    # Check for invalid characters in component
    if '(' in component or ')' in component:
        raise ValueError("Component cannot contain parentheses")
    if ':' in component:
        raise ValueError("Component cannot contain colons")

    # Check if it is a node or edge fact
    if ',' in component:
        fact_type = 'edge'
        components = component.split(',')

        # Validate exactly 2 components for edges
        if len(components) != 2:
            raise ValueError(f"Edge facts must have exactly 2 components, found {len(components)}")

        # Validate no empty components
        for i, comp in enumerate(components):
            if not comp:
                raise ValueError(f"Component {i+1} in edge fact cannot be empty")

        component = tuple(components)
    else:
        fact_type = 'node'

    # Check if bound is a boolean or a list of floats
    bound_lower = bound.lower()
    if bound_lower == 'true':
        bound = interval.closed(1, 1)
    elif bound_lower == 'false':
        bound = interval.closed(0, 0)
    else:
        # Validate interval format
        if not bound.startswith('['):
            raise ValueError(f"Invalid bound format: expected '[' at start of interval, got '{bound[0] if bound else 'empty'}'")
        if not bound.endswith(']'):
            raise ValueError(f"Invalid bound format: expected ']' at end of interval, got '{bound[-1] if bound else 'empty'}'")

        # Extract values between brackets
        interval_content = bound[1:-1]
        if not interval_content:
            raise ValueError("Interval cannot be empty")

        # Parse float values
        parts = interval_content.split(',')
        if len(parts) != 2:
            raise ValueError(f"Interval must have exactly 2 values, found {len(parts)}")

        try:
            bound_values = [float(b) for b in parts]
        except ValueError as e:
            raise ValueError(f"Invalid interval values: {e}")

        lower, upper = bound_values

        # Validate bounds are in valid range [0, 1]
        if lower < 0 or lower > 1:
            raise ValueError(f"Interval lower bound {lower} is out of valid range [0, 1]")
        if upper < 0 or upper > 1:
            raise ValueError(f"Interval upper bound {upper} is out of valid range [0, 1]")

        # Validate lower <= upper
        if lower > upper:
            raise ValueError(f"Interval lower bound {lower} cannot be greater than upper bound {upper}")

        bound = interval.closed(*bound_values)

    return pred, component, bound, fact_type
