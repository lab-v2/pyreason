# List of annotation functions will come here. All functions to be numba decorated and compatible
# Each function has access to the interpretations at a particular timestep, and the qualified nodes and qualified edges that made the rule fire
import numba

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

@numba.njit
def average(inode, iedge, target_label, qn, qe):
    """
    Take average of lower bounds to make new lower bound, take average of upper bounds to make new upper bound
    """
    avg_lower = 0
    avg_upper = 0
    for i in qn:
        avg_lower += inode[i].world[target_label].lower
        avg_upper += inode[i].world[target_label].upper

    for i in qe:
        avg_lower += iedge[i].world[target_label].lower
        avg_upper += iedge[i].world[target_label].upper

    avg_lower /= len(qn)+len(qe)
    avg_upper /= len(qn)+len(qe)

    return interval.closed(avg_lower, avg_upper)


@numba.njit
def maximum(inode, iedge, target_label, qn, qe):
    """
    Take max of lower bounds to make new lower bound, take max of upper bounds to make new upper bound
    """
    max_lower = 0
    max_upper = 0
    for i in qn:
        max_lower = inode[i].world[target_label].lower if inode[i].world[target_label].lower > max_lower else max_lower
        max_upper = inode[i].world[target_label].upper if inode[i].world[target_label].upper > max_upper else max_upper


    for i in qe:
        max_lower = iedge[i].world[target_label].lower if iedge[i].world[target_label].lower > max_lower else max_lower
        max_upper = iedge[i].world[target_label].upper if iedge[i].world[target_label].upper > max_upper else max_upper

    return interval.closed(max_lower, max_upper)


@numba.njit
def minimum(inode, iedge, target_label, qn, qe):
    """
    Take min of lower bounds to make new lower bound, take min of upper bounds to make new upper bound
    """
    min_lower = 0
    min_upper = 0
    for i in qn:
        min_lower = inode[i].world[target_label].lower if inode[i].world[target_label].lower < min_lower else min_lower
        min_upper = inode[i].world[target_label].upper if inode[i].world[target_label].upper < min_upper else min_upper


    for i in qe:
        min_lower = iedge[i].world[target_label].lower if iedge[i].world[target_label].lower < min_lower else min_lower
        min_upper = iedge[i].world[target_label].upper if iedge[i].world[target_label].upper < min_upper else min_upper

    return interval.closed(min_lower, min_upper)


