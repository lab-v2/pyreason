import pytest
import torch
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.learning.classification.classifier import LogicIntegratedClassifier
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

class DummyModel(torch.nn.Module):
    def forward(self, x):
        return torch.tensor([[2.0, 1.0, 0.1]])

@pytest.fixture
def setup_classifier():
    model = DummyModel()
    class_names = ["class1", "class2", "class3"]
    interface_options = ModelInterfaceOptions(
        threshold=0.5,
        snap_value=1.0,
        set_lower_bound=True,
        set_upper_bound=True
    )
    classifier = LogicIntegratedClassifier(model, class_names, "test_classifier", interface_options)
    return classifier

def test_get_class_facts(setup_classifier):
    classifier = setup_classifier
    facts = classifier.get_class_facts(0, 10)
    assert len(facts) == 3
    assert facts[0].name == "test_classifier-class1-fact"
    assert facts[1].name == "test_classifier-class2-fact"
    assert facts[2].name == "test_classifier-class3-fact"

def test_forward_pass(setup_classifier):
    classifier = setup_classifier
    x = torch.tensor([[0.5, 0.5]])
    output, probabilities, facts = classifier(x, t1=0, t2=10)

    assert output.shape == torch.Size([1, 3])
    print("Fact 0 : ", facts[0])
    print("Pred: ", type(facts[0].bound))

    assert len(probabilities) == 3
    assert len(facts) == 3
    assert facts[0].name == "test_classifier-class1-fact"
    interval.closed(0,1)== facts[0].bound
    assert facts[0].start_time == 0
    assert facts[0].end_time == 10

@pytest.mark.parametrize("set_lower_bound, set_upper_bound, set_snap_val, expected_bounds", [
    (True, True, 0.75, [(0.75, 0.75), (0.0, 1.0)]),
    (True, False, 0.55, [(0.55, 1.0), (0.0, 1.0)]),
    (False, True, 0.5348, [(0.0, 0.5348), (0.0, 1.0)]),
    (False, False, 0.31415, [(0.0, 1.0), (0.0, 1.0)])
])
def test_bounds_with_different_interface_options(set_lower_bound, set_upper_bound, set_snap_val, expected_bounds):
    model = DummyModel()
    class_names = ["class1", "class2", "class3"]
    interface_options = ModelInterfaceOptions(
        threshold=0.5,
        snap_value=set_snap_val,
        set_lower_bound=set_lower_bound,
        set_upper_bound=set_upper_bound
    )
    classifier = LogicIntegratedClassifier(model, class_names, "test_classifier", interface_options)

    probabilities = torch.tensor([0.6, 0.4])  # Example probabilities
    lower_bounds, upper_bounds = classifier.calculate_bounds(probabilities)

    for i, (expected_lower, expected_upper) in enumerate(expected_bounds):
        # Note: Floating point inprecision found on these upper and lower bound tenors
        assert pytest.approx(lower_bounds[i].item(), rel=1e-6) == expected_lower
        #assert lower_bounds[i].item() == expected_lower
        assert pytest.approx(upper_bounds[i].item(), rel=1e-6) == expected_upper


@pytest.mark.parametrize("set_lower_bound, set_upper_bound, expected_bounds", [
    (True, True, [(0.6, 0.6), (0.0, 1.0)]),
    (False, False, [(0.0, 1.0), (0.0, 1.0)]),
])
def test_bounds_with_different_interface_options_no_snap_val(set_lower_bound, set_upper_bound, expected_bounds):
    model = DummyModel()
    class_names = ["class1", "class2", "class3"]
    interface_options = ModelInterfaceOptions(
        threshold=0.5,
        snap_value=None,
        set_lower_bound=set_lower_bound,
        set_upper_bound=set_upper_bound
    )
    classifier = LogicIntegratedClassifier(model, class_names, "test_classifier", interface_options)

    probabilities = torch.tensor([0.6, 0.4])  # Example probabilities
    lower_bounds, upper_bounds = classifier.calculate_bounds(probabilities)

    for i, (expected_lower, expected_upper) in enumerate(expected_bounds):
        # Note: Floating point inprecision found on these upper and lower bound tenors
        assert pytest.approx(lower_bounds[i].item(), rel=1e-6) == expected_lower
        assert pytest.approx(upper_bounds[i].item(), rel=1e-6) == expected_upper