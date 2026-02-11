from typing import List, Any

import torch
import torch.nn.functional as F

from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.classification.logic_integration_base import LogicIntegrationBase
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class HuggingFaceLogicIntegratedClassifier(LogicIntegrationBase):
    """
    Integrates a HuggingFace image classification model with PyReason.
    Extends LogicIntegrationBase by implementing _infer, _postprocess, and _pred_to_facts.
    """

    def __init__(
        self,
        model,
        class_names: List[str],
        identifier: str = 'hf_classifier',
        interface_options: ModelInterfaceOptions = None,
        limit_classes: bool = False
    ):
        """
        :param model: A HuggingFace model (e.g. AutoModelForImageClassification).
        :param class_names: List of class names for the model output.
        :param identifier: Identifier for the model, used as the constant in the facts.
        :param interface_options: Options for the model interface, including threshold and snapping behavior.
        :param limit_classes: If True, filter output probabilities to only the classes in class_names
            using the model's id2label config, renormalize, and reorder class_names by probability.
        """
        super().__init__(model, class_names, interface_options, identifier)
        self.limit_classes = limit_classes

    def _infer(self, x: Any) -> Any:
        return self.model(**x).logits

    def _postprocess(self, raw_output: Any) -> Any:
        probabilities = F.softmax(raw_output, dim=1).squeeze()

        if self.limit_classes:
            probabilities, self._filtered_labels = self._filter_to_allowed_classes(probabilities)
        else:
            self._filtered_labels = None

        return probabilities

    def _filter_to_allowed_classes(self, probabilities: torch.Tensor):
        """Filter probabilities to only the allowed class_names using model.config.id2label.
        Returns (top_probs, top_labels) without mutating self.class_names."""
        id2label = self.model.config.id2label

        allowed_indices = [
            i for i, label in id2label.items()
            if label.split(",")[0].strip().lower() in [name.lower() for name in self.class_names]
        ]

        filtered_probs = torch.zeros_like(probabilities)
        filtered_probs[allowed_indices] = probabilities[allowed_indices]
        filtered_probs = filtered_probs / filtered_probs.sum()

        top_labels = []
        top_probs, top_indices = filtered_probs.topk(len(self.class_names))
        for idx in top_indices:
            label = id2label[idx.item()].split(",")[0]
            top_labels.append(label)

        return top_probs, top_labels

    def _pred_to_facts(
        self,
        raw_output: Any,
        probabilities: Any,
        t1: int = 0,
        t2: int = 0
    ) -> List[Fact]:
        opts = self.interface_options

        threshold = torch.tensor(opts.threshold, dtype=probabilities.dtype, device=probabilities.device)
        condition = probabilities > threshold

        if opts.snap_value is not None:
            snap_value = torch.tensor(opts.snap_value, dtype=probabilities.dtype, device=probabilities.device)
            lower_val = snap_value if opts.set_lower_bound else torch.tensor(0.0, dtype=probabilities.dtype, device=probabilities.device)
            upper_val = snap_value if opts.set_upper_bound else torch.tensor(1.0, dtype=probabilities.dtype, device=probabilities.device)
        else:
            lower_val = probabilities if opts.set_lower_bound else torch.zeros_like(probabilities)
            upper_val = probabilities if opts.set_upper_bound else torch.ones_like(probabilities)

        lower_bounds = torch.where(condition, lower_val, torch.zeros_like(probabilities))
        upper_bounds = torch.where(condition, upper_val, torch.ones_like(probabilities))

        labels = self._filtered_labels if self._filtered_labels is not None else self.class_names

        facts = []
        for i in range(len(labels)):
            lower = lower_bounds[i].item()
            upper = upper_bounds[i].item()
            fact_str = f'{labels[i]}({self.identifier}) : [{lower:.3f}, {upper:.3f}]'
            fact = Fact(fact_str, name=f'{self.identifier}-{labels[i]}-fact', start_time=t1, end_time=t2)
            facts.append(fact)

        return facts
