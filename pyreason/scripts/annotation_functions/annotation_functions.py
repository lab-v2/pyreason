# List of annotation functions will come here. All functions to be numba decorated and compatible
# Each function has access to the interpretations at a particular timestep, and the qualified nodes and qualified edges that made the rule fire
import numba
import numpy as np

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

@numba.njit
def _get_weighted_sum(annotations, weights, mode='lower'):
    """
    Returns weighted sum plus the total number of annotations
    """
    # List containing the weighted sum for lower bound for each clause
    weighted_sum = np.arange(0, dtype=np.float64)
    annotation_cnt = 0
    for i, clause in enumerate(annotations):
        s = 0
        for annotation in clause:
            annotation_cnt += 1
            if mode=='lower':
                s += annotation.lower * weights[i]
            elif mode=='upper':
                s += annotation.upper * weights[i]
        weighted_sum = np.append(weighted_sum, s)

    return weighted_sum, annotation_cnt

@numba.njit
def _check_bound(lower, upper):
    if lower > upper:
        return (0, 1)
    else:
        l = min(lower, 1)
        u = min(upper, 1)
        return (l, u)


@numba.njit
def average(annotations, weights):
    """
    Take average of lower bounds to make new lower bound, take average of upper bounds to make new upper bound
    """
    weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')
    weighted_sum_upper, n = _get_weighted_sum(annotations, weights, mode='upper')

    # n cannot be zero otherwise rule would not have fired
    avg_lower = np.sum(weighted_sum_lower) / n
    avg_upper = np.sum(weighted_sum_upper) / n

    lower, upper = _check_bound(avg_lower, avg_upper)

    return interval.closed(lower, upper)

@numba.njit
def average_lower(annotations, weights):
    """
    Take average of lower bounds to make new lower bound, take max of upper bounds to make new upper bound
    """
    weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')

    avg_lower = np.sum(weighted_sum_lower) / n

    max_upper = 0
    for clause in annotations:
        for annotation in clause:
            max_upper = annotation.upper if annotation.upper > max_upper else max_upper

    lower, upper = _check_bound(avg_lower, max_upper)

    return interval.closed(lower, upper)

@numba.njit
def maximum(annotations, weights):
    """
    Take max of lower bounds to make new lower bound, take max of upper bounds to make new upper bound
    """
    weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')
    weighted_sum_upper, n = _get_weighted_sum(annotations, weights, mode='upper')

    max_lower = np.max(weighted_sum_lower)
    max_upper = np.max(weighted_sum_upper)

    lower, upper = _check_bound(max_lower, max_upper)

    return interval.closed(lower, upper)


@numba.njit
def minimum(annotations, weights):
    """
    Take min of lower bounds to make new lower bound, take min of upper bounds to make new upper bound
    """
    weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')
    weighted_sum_upper, n = _get_weighted_sum(annotations, weights, mode='upper')

    min_lower = np.min(weighted_sum_lower)
    min_upper = np.min(weighted_sum_upper)

    lower, upper = _check_bound(min_lower, min_upper)

    return interval.closed(lower, upper)


