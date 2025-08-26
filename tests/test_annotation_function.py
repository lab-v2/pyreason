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

    # Display the changes in the interpretation for each timestep using get_dict()
    interpretation_dict = interpretation.get_dict()
    for t, timestep_data in interpretation_dict.items():
        print(f'TIMESTEP - {t}')
        union_probability_edges = []
        for component, labels in timestep_data.items():
            if 'union_probability' in labels:
                union_probability_edges.append((component, labels['union_probability']))
        print(f"union_probability edges: {union_probability_edges}")
        print()

    assert interpretation.query(pr.Query('union_probability(A, B) : [0.21, 1]')), 'Union probability should be 0.21'
