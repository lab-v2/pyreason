from typing import List

import torch.nn
import torch.nn.functional as F

from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.classification.logic_integration_base import LogicIntegrationBase
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class LogicIntegratedClassifier(LogicIntegrationBase):
    """
    Class to integrate a PyTorch model with PyReason. The output of the model is returned to the
    user in the form of PyReason facts. The user can then add these facts to the logic program and reason using them.
    Wraps any torch.nn.Module whose forward(x) returns [N, C] logits (multi-class).
    Implements _infer, _postprocess, and _pred_to_facts to replace the original forward().
    """

    def __init__(
        self,
        model: torch.nn.Module,
        class_names: List[str],
        identifier: str = 'classifier',
        interface_options: ModelInterfaceOptions = None
    ):
        super().__init__(model, class_names, interface_options, identifier)

    def _infer(self, x: torch.Tensor) -> torch.Tensor:
        # Simply run the underlying model to get raw logits [N, C]
        return self.model(x)

    def _postprocess(self, raw_output: torch.Tensor) -> torch.Tensor:
        """
        raw_output: a [N, C] logits tensor.
        Apply softmax over dim=1 to get probabilities [N, C].
        """
        logits = raw_output
        if logits.dim() != 2 or logits.size(1) != len(self.class_names):
            raise ValueError(
                f"Expected logits of shape [N, C] with C={len(self.class_names)}, "
                f"got {tuple(logits.shape)}"
            )
        return F.softmax(logits, dim=1)

    def _pred_to_facts(
        self,
        raw_output: torch.Tensor,
        probabilities: torch.Tensor,
        t1: int,
        t2: int
    ) -> List[Fact]:
        """
        Turn the [N, C] probability tensor into a flat List[Fact],
        using threshold, snap_value, set_lower_bound, set_upper_bound.
        Produces N * C facts.
        """
        opts = self.interface_options
        prob = probabilities  # [N, C]

        # Build a threshold tensor
        threshold = torch.tensor(opts.threshold, dtype=prob.dtype, device=prob.device)
        condition = prob > threshold  # [N, C] boolean

        # Determine lower/upper for “true” entries
        if opts.snap_value is not None:
            snap_val = torch.tensor(opts.snap_value, dtype=prob.dtype, device=prob.device)
            lower_if_true = (
                snap_val if opts.set_lower_bound else torch.tensor(0.0, dtype=prob.dtype, device=prob.device)
            )
            upper_if_true = (
                snap_val if opts.set_upper_bound else torch.tensor(1.0, dtype=prob.dtype, device=prob.device)
            )
        else:
            lower_if_true = prob if opts.set_lower_bound else torch.zeros_like(prob)
            upper_if_true = prob if opts.set_upper_bound else torch.ones_like(prob)

        # Build full [N, C] lower_bounds and upper_bounds
        zeros = torch.zeros_like(prob)
        ones = torch.ones_like(prob)
        lower_bounds = torch.where(condition, lower_if_true, zeros)  # [N, C]
        upper_bounds = torch.where(condition, upper_if_true, ones)   # [N, C]

        N, C = prob.shape
        facts: List[Fact] = []

        for i in range(N):
            for j, class_name in enumerate(self.class_names):
                lower = lower_bounds[i, j].item()
                upper = upper_bounds[i, j].item()
                fact_str = f"{class_name}({self.identifier}) : [{lower:.3f}, {upper:.3f}]"
                fact_name = f"{self.identifier}-{class_name}-fact"
                f = Fact(fact_str, name=fact_name, start_time=t1, end_time=t2)
                facts.append(f)

        return facts
