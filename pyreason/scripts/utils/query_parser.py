import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def parse_query(query: str):
    query = query.replace(' ', '')

    if ':' in query:
        pred_comp, bounds = query.split(':')
        bounds = bounds.replace('[', '').replace(']', '')
        l, u = bounds.split(',')
        l, u = float(l), float(u)
    else:
        if query[0] == '~':
            pred_comp = query[1:]
            l, u = 0, 0
        else:
            pred_comp = query
            l, u = 1, 1

    bnd = interval.closed(l, u)

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
