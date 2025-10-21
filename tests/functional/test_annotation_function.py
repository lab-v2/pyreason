# Test if annotation functions work
import pyreason as pr
import numba
import numpy as np
import pytest
from pyreason.scripts.numba_wrapper.numba_types.interval_type import closed


@numba.njit
def probability_func(annotations, weights):
    prob_A = annotations[0][0].lower
    prob_B = annotations[1][0].lower
    union_prob = prob_A + prob_B
    union_prob = np.round(union_prob, 3)
    return union_prob, 1


def test_probability_func_consistency():
    """Ensure annotation function behaves the same with and without JIT."""
    annotations = numba.typed.List()
    annotations.append(numba.typed.List([closed(0.01, 1.0)]))
    annotations.append(numba.typed.List([closed(0.2, 1.0)]))
    weights = numba.typed.List([1.0, 1.0])
    jit_res = probability_func(annotations, weights)
    py_res = probability_func.py_func(annotations, weights)
    assert jit_res == py_res


@pytest.mark.slow
def test_annotation_function():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    print("fp version", pr.settings.fp_version)

    pr.settings.allow_ground_rules = True

    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
    pr.add_annotation_function(probability_func)
    pr.add_rule(pr.Rule('union_probability(A, B):probability_func <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_edges(interpretation, ['union_probability'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert interpretation.query(pr.Query('union_probability(A, B) : [0.21, 1]')), 'Union probability should be 0.21'


@pytest.mark.fp
@pytest.mark.slow
def test_annotation_function_fp():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Set FP version
    pr.settings.fp_version = True
    print("fp version", pr.settings.fp_version)

    pr.settings.allow_ground_rules = True

    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
    pr.add_annotation_function(probability_func)
    pr.add_rule(pr.Rule('union_probability(A, B):probability_func <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_edges(interpretation, ['union_probability'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert interpretation.query(pr.Query('union_probability(A, B) : [0.21, 1]')), 'Union probability should be 0.21'
