from typing import List, Tuple

import torch.nn
import torch.nn.functional as F

from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class LogicIntegratedClassifier(torch.nn.Module):
    """
    Class to integrate a PyTorch model with PyReason. The output of the model is returned to the
    user in the form of PyReason facts. The user can then add these facts to the logic program and reason using them.
    """
    def __init__(self, model, class_names: List[str], identifier: str = 'classifier', interface_options: ModelInterfaceOptions = None):
        """
        :param model: PyTorch model to be integrated.
        :param class_names: List of class names for the model output.
        :param identifier: Identifier for the model, used as the constant in the facts.
        :param interface_options: Options for the model interface, including threshold and snapping behavior.
        """
        super(LogicIntegratedClassifier, self).__init__()
        self.model = model
        self.class_names = class_names
        self.identifier = identifier
        self.interface_options = interface_options

    def get_class_facts(self, t1: int, t2: int) -> List[Fact]:
        """
        Return PyReason facts to create nodes for each class. Each class node will have bounds `[1,1]` with the
         predicate corresponding to the model name.
        :param t1: Start time for the facts
        :param t2: End time for the facts
        :return: List of PyReason facts
        """
        facts = []
        for c in self.class_names:
            fact = Fact(f'{c}({self.identifier})', name=f'{self.identifier}-{c}-fact', start_time=t1, end_time=t2)
            facts.append(fact)
        return facts
    

    # A user may want to restrict the number of classe so that the classifier only returns facts for a subset of classes.  
    # This is useful for large models like CLIP, where the model has 4000 classes. 
    # We will set the new possible classes to be limited to the class names given to the classifier.
    def update_classes_and_probs_for_filter(self, probabilities) -> torch.Tensor:
        # Get the index-to-label mapping from the model config
        id2label = self.model.config.id2label

        # Get the indices of the allowed labels, stripping everything after the comma
        allowed_indices = [
            i for i, label in id2label.items()
            if label.split(",")[0].strip().lower() in [name.lower() for name in self.class_names]
        ]

        # Normalize the probabilities based only on the allowed classes
        filtered_probs = torch.zeros_like(probabilities)
        filtered_probs[allowed_indices] = probabilities[allowed_indices]
        filtered_probs = filtered_probs / filtered_probs.sum()

        # Because we are filtering the probabilities, we need to update the class labels to only include the allowed classes.
        # We also update the class names so they are ordered by the probabilities.
        top_labels = []
        top_probs, top_indices = filtered_probs.topk(len(self.class_names))
        for prob, idx in zip(top_probs, top_indices):
            label = id2label[idx.item()].split(",")[0]
            print(f"{label}: {prob.item():.4f}")
            top_labels.append(label)
        self.class_names = top_labels
        return top_probs

    def forward(self, x, t1: int = 0, t2: int = 0, limit_classification_output_classes = False) -> Tuple[torch.Tensor, torch.Tensor, List[Fact]]:
        """
        Forward pass of the model
        :param x: Input tensor
        :param t1: Start time for the facts
        :param t2: End time for the facts
        :return: Output tensor
        """

        try:
            output = self.model(x)
        except AttributeError as e:
            print(f"Error during model forward pass: {e}")
            try:
                output = self.model(**x).logits
            except Exception as e:
                print(f"Error during model forward pass with kwargs: {e}")

        probabilities = F.softmax(output, dim=1).squeeze()

        if limit_classification_output_classes:
            probabilities = self.update_classes_and_probs_for_filter(probabilities)

        opts = self.interface_options

        # Prepare threshold tensor.
        threshold = torch.tensor(opts.threshold, dtype=probabilities.dtype, device=probabilities.device)
        condition = probabilities > threshold

        if opts.snap_value is not None:
            snap_value = torch.tensor(opts.snap_value, dtype=probabilities.dtype, device=probabilities.device)
            # For values that pass the threshold:
            lower_val = snap_value if opts.set_lower_bound else torch.tensor(0.0, dtype=probabilities.dtype,
                                                                             device=probabilities.device)
            upper_val = snap_value if opts.set_upper_bound else torch.tensor(1.0, dtype=probabilities.dtype,
                                                                             device=probabilities.device)
        else:
            # If no snap_value is provided, keep original probabilities for those passing threshold.
            lower_val = probabilities if opts.set_lower_bound else torch.zeros_like(probabilities)
            upper_val = probabilities if opts.set_upper_bound else torch.ones_like(probabilities)

        # For probabilities that pass the threshold, apply the above; else, bounds are fixed to [0,1].
        lower_bounds = torch.where(condition, lower_val, torch.zeros_like(probabilities))
        upper_bounds = torch.where(condition, upper_val, torch.ones_like(probabilities))

        # Convert bounds to Python floats for fact creation.
        bounds_list = []
        for i in range(len(self.class_names)):
            lower = lower_bounds[i].item()
            upper = upper_bounds[i].item()
            bounds_list.append([lower, upper])

        # Define time bounds for the facts.
        facts = []
        for class_name, bounds in zip(self.class_names, bounds_list):
            lower, upper = bounds
            fact_str = f'{class_name}({self.identifier}) : [{lower:.3f}, {upper:.3f}]'
            fact = Fact(fact_str, name=f'{self.identifier}-{class_name}-fact', start_time=t1, end_time=t2)
            facts.append(fact)
        return output, probabilities, facts



