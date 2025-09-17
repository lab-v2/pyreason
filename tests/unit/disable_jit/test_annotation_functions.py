import numpy as np
import pytest
from types import SimpleNamespace

import pyreason.scripts.annotation_functions.annotation_functions as af

af.interval = SimpleNamespace(closed=lambda l, u, static=False: SimpleNamespace(lower=l, upper=u))

def _interval(lower, upper):
    return SimpleNamespace(lower=lower, upper=upper)

def _example_annotations():
    """Return sample annotations and weights used across tests."""
    annotations = [
        [_interval(0.1, 0.2), _interval(0.3, 0.4)],
        [_interval(0.5, 0.6)],
    ]
    weights = [1.0, 2.0]
    return annotations, weights

def test_get_weighted_sum_modes():
    annotations, weights = _example_annotations()
    lower_sum, cnt_l = af._get_weighted_sum(annotations, weights, mode="lower")
    upper_sum, cnt_u = af._get_weighted_sum(annotations, weights, mode="upper")
    invalid_sum, cnt_i = af._get_weighted_sum(annotations, weights, mode="invalid")

    np.testing.assert_allclose(lower_sum, np.array([0.4, 1.0]))
    np.testing.assert_allclose(upper_sum, np.array([0.6, 1.2]))
    np.testing.assert_allclose(invalid_sum, np.array([0.0, 0.0]))
    assert cnt_l == cnt_u == cnt_i == 3

@pytest.mark.parametrize(
    "lower, upper, expected",
    [
        (0.9, 0.8, (0, 1)),
        (1.2, 1.5, (1, 1)),
    ],
)
def test_check_bound(lower, upper, expected):
    assert af._check_bound(lower, upper) == expected

def test_average():
    annotations, weights = _example_annotations()
    result = af.average(annotations, weights)
    assert result.lower == pytest.approx(1.4 / 3)
    assert result.upper == pytest.approx(0.6)

def test_average_lower():
    annotations, weights = _example_annotations()
    result = af.average_lower(annotations, weights)
    assert result.lower == pytest.approx(1.4 / 3)
    assert result.upper == pytest.approx(0.6)

def test_maximum():
    annotations, weights = _example_annotations()
    result = af.maximum(annotations, weights)
    assert result.lower == pytest.approx(1.0)
    assert result.upper == pytest.approx(1.0)

def test_minimum():
    annotations, weights = _example_annotations()
    result = af.minimum(annotations, weights)
    assert result.lower == pytest.approx(0.4)
    assert result.upper == pytest.approx(0.6)
