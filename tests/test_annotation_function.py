# Test if annotation functions work
import pyreason as pr
import numba
import numpy as np


@numba.njit
def probability_func(annotations, weights):
    prob_A = annotations[0][0].lower
    prob_B = annotations[1][0].lower
    union_prob = prob_A + prob_B
    union_prob = np.round(union_prob, 3)
    return union_prob, 1


def test_annotation_function():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()

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
