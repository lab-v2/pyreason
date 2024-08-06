import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def parse_fact(fact_text):
    f = fact_text.replace(' ', '')

    # Separate into predicate-component and bound. If there is no bound it means it's true
    if ':' in f:
        pred_comp, bound = f.split(':')
    else:
        pred_comp = f
        if pred_comp[0] == '~':
            bound = 'False'
            pred_comp = pred_comp[1:]
        else:
            bound = 'True'

    # Check if bound is a boolean or a list of floats
    bound = bound.lower()
    if bound == 'true':
        bound = interval.closed(1, 1)
    elif bound == 'false':
        bound = interval.closed(0, 0)
    else:
        bound = [float(b) for b in bound[1:-1].split(',')]
        bound = interval.closed(*bound)

    # Split the predicate and component
    idx = pred_comp.find('(')
    pred = pred_comp[:idx]
    component = pred_comp[idx + 1:-1]

    # Check if it is a node or edge fact
    if ',' in component:
        fact_type = 'edge'
        component = tuple(component.split(','))
    else:
        fact_type = 'node'

    return pred, component, bound, fact_type
