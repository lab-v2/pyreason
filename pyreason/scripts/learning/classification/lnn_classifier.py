from typing import List, Dict, Tuple, Optional, Any

from lnn import Model, Predicate
from pyreason.scripts.facts.fact import Fact


class LNNInterfaceOptions:
    """Configuration for the LNN-PyReason bridge."""

    def __init__(
        self,
        convergence_threshold: float = 0.001,
        max_feedback_rounds: int = 5,
        bound_tightening_only: bool = True,
    ):
        self.convergence_threshold = convergence_threshold
        self.max_feedback_rounds = max_feedback_rounds
        self.bound_tightening_only = bound_tightening_only


class LNNClassifier:
    """
    Integrates an IBM LNN Model with PyReason.

    Unlike LogicIntegratedClassifier (which wraps torch.nn.Module),
    this wraps an LNN Model whose inference naturally produces
    bounded truth values [lower, upper] for logical predicates.

    Supports bidirectional operation:
      - Forward: LNN inference -> PyReason Facts
      - Feedback: PyReason interpretation bounds -> LNN evidence

    Follows the same interface contract as LogicIntegrationBase.forward():
      forward(data, t1, t2) -> (raw_output, postproc, List[Fact])
    """

    def __init__(
        self,
        lnn_model: Model,
        predicate_map: Dict[str, Predicate],
        target_predicates: List[str],
        identifier: str = "lnn",
        interface_options: LNNInterfaceOptions = None,
        node_groundings: Optional[Dict[str, str]] = None,
    ):
        """
        :param lnn_model: A configured IBM LNN Model with predicates, rules, and knowledge.
        :param predicate_map: Mapping from predicate name (str) to LNN Predicate object.
        :param target_predicates: Predicate names whose bounds are exported as PyReason Facts.
        :param identifier: Identifier injected into each Fact name.
        :param interface_options: Configuration for the feedback loop.
        :param node_groundings: Mapping from LNN grounding names to PyReason node names.
                                If None, names are used as-is.
        """
        self.lnn_model = lnn_model
        self.predicate_map = predicate_map
        self.target_predicates = target_predicates
        self.identifier = identifier
        self.options = interface_options or LNNInterfaceOptions()
        self.node_groundings = node_groundings or {}
        self._reverse_groundings = {v: k for k, v in self.node_groundings.items()}

    def forward(
        self,
        data: Optional[Dict[str, Dict[str, Any]]] = None,
        t1: int = 0,
        t2: int = 0,
    ) -> Tuple[Dict[str, Dict], Dict[str, Dict], List[Fact]]:
        """
        Run LNN inference and produce PyReason Facts.

        :param data: Optional data keyed by predicate name string.
                     Values are dicts mapping grounding -> (lower, upper) or LNNFact.
        :param t1: Start time for PyReason facts.
        :param t2: End time for PyReason facts.
        :return: (raw_bounds, target_bounds, facts)
        """
        raw_output = self._infer(data)
        postproc = self._postprocess(raw_output)
        facts = self._pred_to_facts(postproc, t1, t2)
        return raw_output, postproc, facts

    def _infer(self, data: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Tuple[float, float]]]:
        if data:
            formatted = {}
            for pred_name, groundings in data.items():
                if pred_name in self.predicate_map:
                    formatted[self.predicate_map[pred_name]] = groundings
            self.lnn_model.add_data(formatted)

        self.lnn_model.infer()

        all_bounds = {}
        for pred_name, pred in self.predicate_map.items():
            bounds = {}
            for grounding in pred.groundings:
                # get_data returns tensor of shape [1, 2]
                tensor = pred.get_data(grounding)
                lower = tensor[0, 0].item()
                upper = tensor[0, 1].item()
                # groundings are always tuples, extract string for arity-1
                key = grounding[0] if isinstance(grounding, tuple) and len(grounding) == 1 else grounding
                bounds[key] = (lower, upper)
            all_bounds[pred_name] = bounds

        return all_bounds

    def _postprocess(self, raw_output: Dict[str, Dict]) -> Dict[str, Dict[str, Tuple[float, float]]]:
        return {
            name: raw_output[name]
            for name in self.target_predicates
            if name in raw_output
        }

    def _pred_to_facts(
        self,
        postproc: Dict[str, Dict[str, Tuple[float, float]]],
        t1: int,
        t2: int,
    ) -> List[Fact]:
        facts = []
        for pred_name, groundings in postproc.items():
            for grounding, (lower, upper) in groundings.items():
                pyreason_node = self.node_groundings.get(grounding, grounding)
                fact_str = f"{pred_name}({pyreason_node}) : [{lower:.4f}, {upper:.4f}]"
                fact_name = f"{self.identifier}-{pred_name}-{pyreason_node}-fact"
                facts.append(Fact(fact_str, name=fact_name, start_time=t1, end_time=t2))
        return facts

    def receive_feedback(
        self,
        feedback_bounds: Dict[str, Dict[str, Tuple[float, float]]],
    ) -> None:
        """
        Feed PyReason's refined bounds back into the LNN model as evidence.

        :param feedback_bounds: Dict mapping predicate_name -> {node_name: (lower, upper)}.
                                Node names are PyReason names (reverse-mapped to LNN groundings).
        """
        data_to_add = {}
        for pred_name, groundings in feedback_bounds.items():
            if pred_name not in self.predicate_map:
                continue
            pred = self.predicate_map[pred_name]
            grounding_data = {}
            for node_name, (lower, upper) in groundings.items():
                lnn_grounding = self._reverse_groundings.get(node_name, node_name)

                if self.options.bound_tightening_only:
                    try:
                        current = pred.get_data(lnn_grounding)
                        curr_l = current[0, 0].item()
                        curr_u = current[0, 1].item()
                        lower = max(lower, curr_l)
                        upper = min(upper, curr_u)
                        if lower > upper:
                            continue
                    except Exception:
                        pass

                grounding_data[lnn_grounding] = (lower, upper)

            if grounding_data:
                data_to_add[pred] = grounding_data

        if data_to_add:
            self.lnn_model.add_data(data_to_add)
