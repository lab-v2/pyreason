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

    def forward(self, x, t1: int = 0, t2: int = 0) -> Tuple[torch.Tensor, torch.Tensor, List[Fact]]:
        """
        Forward pass of the model
        :param x: Input tensor
        :param t1: Start time for the facts
        :param t2: End time for the facts
        :return: Output tensor
        """
        output = self.model(x)

        # Convert logits to probabilities assuming a multi-class classification.
        probabilities = F.softmax(output, dim=1).squeeze()
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

