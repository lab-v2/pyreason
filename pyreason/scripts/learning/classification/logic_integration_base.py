import torch
from abc import ABC, abstractmethod
from typing import List, Tuple, Any

from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class LogicIntegrationBase(torch.nn.Module, ABC):
    """
    Abstract base class for **any** model (classifier, detector, etc.) whose
    outputs you want to convert into PyReason Facts with lower/upper bounds.

    Subclasses must implement:
      1. _infer(x) → raw_output
      2. _pred_to_facts(raw_output, t1, t2) → List[Fact]

    The base class handles:
      - Calling `self.model(x)`
      - Applying threshold, snap_value, and bound‐construction (for “probabilistic” heads),
        if desired.
      - Packaging everything into a final (raw_output, probs_or_filtered, facts) tuple.
    """

    def __init__(
        self,
        model: torch.nn.Module,
        class_names: List[str],
        interface_options: ModelInterfaceOptions,
        identifier: str = "model"
    ):
        """
        :param model:            Any PyTorch module.  Subclasses will call it in _infer().
        :param class_names:      List of “predicate” names.  For a detector, this is the full label list.
        :param interface_options: Contains threshold, snap_value, set_lower_bound, set_upper_bound, etc.
        :param identifier:       Constant to inject into each Fact (e.g. “image1”, “classifier”, “detector”).
        """
        super().__init__()
        self.model = model
        self.class_names = class_names
        self.interface_options = interface_options
        self.identifier = identifier

        # (Optional) sanity‐check on class_names vs. model (each subclass can override)
        self._validate_init()

    def _validate_init(self):
        """
        Hook for subclasses to check, e.g. that `len(class_names)` matches
        whatever the underlying model expects.
        """
        pass

    def forward(
        self,
        x: Any,
        t1: int = 0,
        t2: int = 0
    ) -> Tuple[Any, Any, List[Fact]]:
        """
        1) Call `_infer(x)` to get the “raw_output.”
        2) Call `_postprocess(raw_output)` to get either “probabilities” or “filtered detections,”
           depending on model‐type.
        3) Call `_pred_to_facts(raw_output, postproc, t1, t2)` to build a List[Fact].

        Returns a 3‐tuple:
          (raw_output, postproc, facts_list)

        - raw_output:   whatever `model(x)` naturally returned
        - postproc:     a tensor of probabilities or a list of filtered boxes, etc.
        - facts_list:   a flat List[Fact]
        """
        # 1) raw predictions
        raw_output = self._infer(x)

        # 2) “postprocess” step (e.g. softmax/sigmoid + threshold for classifiers,
        #    or filtering by confidence for detectors)
        postproc = self._postprocess(raw_output)

        # 3) Turn them into Facts
        facts: List[Fact] = self._pred_to_facts(raw_output, postproc, t1, t2)

        return raw_output, postproc, facts

    @abstractmethod
    def _infer(self, x: Any) -> Any:
        """
        Run the underlying PyTorch model (self.model) on input x, returning
        the “raw” output.  For a classifier, this is a logit‐tensor.  For a YOLO detector,
        this might be a Results object whose `.xyxy[i]` is a [num_det×6] tensor, etc.
        """
        ...

    @abstractmethod
    def _postprocess(self, raw_output: Any) -> Any:
        """
        Convert raw model outputs into a more convenient “postprocessed” form
        that we’ll pass both to the user and into `_pred_to_facts`.

        - For a binary/multiclass classifier, apply sigmoid/softmax + threshold mask.
        - For a multilabel classifier, apply sigmoid + per‐class threshold mask.
        - For a detector, extract a list of (class_idx, confidence) for all detections
          above threshold.
        """
        ...

    @abstractmethod
    def _pred_to_facts(
        self,
        raw_output: Any,
        postproc: Any,
        t1: int,
        t2: int
    ) -> List[Fact]:
        """
        Given raw_output and postproc (see above), build a List of PyReason Fact(...) objects,
        each of the form:
            f"{class_name}({self.identifier}) : [lower, upper]"

        - raw_output:  whatever the model returned
        - postproc:    tensor-of-probs or list‐of‐(class_idx,confidence)
        - t1, t2:      start/end timestamps
        """
        ...
