import numba
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def reorder_clauses(rule):
    # Go through all clauses in the rule and re-order them if necessary
    # It is faster for grounding to have node clauses first and then edge clauses
    # Move all the node clauses to the front of the list
    reordered_clauses = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, label.label_type, numba.types.ListType(numba.types.string), interval.interval_type, numba.types.string)))
    reordered_thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64)))
    node_clauses = []
    edge_clauses = []
    reordered_clauses_map = {}

    for index, clause in enumerate(rule.get_clauses()):
        if clause[0] == 'node':
            node_clauses.append((index, clause))
        else:
            edge_clauses.append((index, clause))

    thresholds = rule.get_thresholds()
    for new_index, (original_index, clause) in enumerate(node_clauses + edge_clauses):
        reordered_clauses.append(clause)
        reordered_thresholds.append(thresholds[original_index])
        reordered_clauses_map[new_index] = original_index

    rule.set_clauses(reordered_clauses)
    rule.set_thresholds(reordered_thresholds)
    return rule, reordered_clauses_map
