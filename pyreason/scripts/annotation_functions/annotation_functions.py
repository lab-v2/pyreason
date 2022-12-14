# List of annotation functions will come here. All functions to be numba decorated and compatible
# Each function has access to the interpretations at a particular timestep, and the qualified nodes and qualified edges that made the rule fire
import numba

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

@numba.njit
def average(annotations):
    """
    Take average of lower bounds to make new lower bound, take average of upper bounds to make new upper bound
    """
    avg_lower = 0
    avg_upper = 0
    for i in annotations:
        avg_lower += i.lower
        avg_upper += i.upper

    if len(annotations)!=0:
        avg_lower /= len(annotations)
        avg_upper /= len(annotations)
    else:
        avg_lower = 0
        avg_upper = 1

    return interval.closed(avg_lower, avg_upper)

@numba.njit
def average_lower(annotations):
    """
    Take average of lower bounds to make new lower bound, take max of upper bounds to make new upper bound
    """
    avg_lower = 0
    max_upper = 0
    for i in annotations:
        avg_lower += i.lower
        max_upper = i.upper if i.upper > max_upper else max_upper

    if len(annotations)!=0:
        avg_lower /= len(annotations)
    else:
        avg_lower = 0

    return interval.closed(avg_lower, max_upper)

@numba.njit
def maximum(annotations):
    """
    Take max of lower bounds to make new lower bound, take max of upper bounds to make new upper bound
    """
    max_lower = 0
    max_upper = 0
    for i in annotations:
        max_lower = i.lower if i.lower > max_lower else max_lower
        max_upper = i.upper if i.upper > max_upper else max_upper

    return interval.closed(max_lower, max_upper)


@numba.njit
def minimum(annotations):
    """
    Take min of lower bounds to make new lower bound, take min of upper bounds to make new upper bound
    """
    min_lower = 0
    min_upper = 0
    for i in annotations:
        min_lower = i.lower if i.lower < min_lower else min_lower
        min_upper = i.upper if i.upper < min_upper else min_upper

    return interval.closed(min_lower, min_upper)


