# Test cases for classifier integration with pyreason
import pyreason as pr
import torch
import torch.nn as nn


def test_classifier_integration():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Create a dummy PyTorch model: input size 10, output 3 classes.
    model = nn.Linear(10, 3)

    # Define class names for the output classes.
    class_names = ["cat", "dog", "rabbit"]

    # Create integration options.
    # Only probabilities exceeding 0.6 will be considered.
    # For those, if set_lower_bound is True, lower bound becomes 0.95; if set_upper_bound is False, upper bound is forced to 1.
    interface_options = pr.ModelInterfaceOptions(
        threshold=0.4,
        set_lower_bound=True,
        set_upper_bound=False,
        snap_value=0.95
    )

    # Create an instance of LogicIntegratedClassifier.
    logic_classifier = pr.LogicIntegratedClassifier(model, class_names, model_name="classifier",
                                                    interface_options=interface_options)

    # Create a dummy input tensor with 10 features.
    input_tensor = torch.rand(1, 10)

    # Set time bounds for the facts.
    t1 = 0
    t2 = 0

    # Run the forward pass to get the model output and the corresponding PyReason facts.
    output, probabilities, facts = logic_classifier(input_tensor, t1, t2)

    # Assert that the output is a tensor.
    assert isinstance(output, torch.Tensor), "The model output should be a torch.Tensor"
    # Assert that we have one fact per class.
    assert len(facts) == len(class_names), "Expected one fact per class"

    # Print results for visual inspection.
    print('Logits', output)
    print('Probabilities', probabilities)
    print("\nGenerated PyReason Facts:")
    for fact in facts:
        print(fact)
