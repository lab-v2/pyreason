import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def parse_query(query: str):
    query = query.replace(' ', '')

    if ':' in query:
        pred_comp, bounds = query.split(':')
        bounds = bounds.replace('[', '').replace(']', '')
        lower, upper = bounds.split(',')
        lower, upper = float(lower), float(upper)
    else:
        if query[0] == '~':
            pred_comp = query[1:]
            lower, upper = 0, 0
        else:
            pred_comp = query
            lower, upper = 1, 1

    bnd = interval.closed(lower, upper)

    # Split predicate and component
    idx = pred_comp.find('(')
    pred = label.Label(pred_comp[:idx])
    component = pred_comp[idx + 1:-1]

    if ',' in component:
        component = tuple(component.split(','))
        comp_type = 'edge'
    else:
        comp_type = 'node'

    return pred, component, comp_type, bnd
