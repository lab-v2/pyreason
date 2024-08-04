import pyreason.scripts.facts.fact_node as fact_node
import pyreason.scripts.facts.fact_edge as fact_edge

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def parse_fact(fact_text, name, t_lower, t_upper, static):
    f = fact_text.replace(' ', '')

    # Separate into predicate-component and bound. If there is no bound it means it's true
    if ':' in f:
        pred_comp, bound = f.split(':')
    else:
        pred_comp = f
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

    print(fact_type, component, pred, bound)

    # Create the fact
    if fact_type == 'node':
        fact = fact_node.Fact(name, component, pred, bound, t_lower, t_upper, static)
    else:
        fact = fact_edge.Fact(name, component, pred, bound, t_lower, t_upper, static)

    return fact, fact_type
