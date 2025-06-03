import asyncio
import threading
import time
from datetime import timedelta
from datetime import datetime
from typing import List, Tuple, Optional, Union, Callable, Any

import torch.nn
import torch.nn.functional as F

import pyreason as pr
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.classification.logic_integration_base import LogicIntegrationBase
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class TemporalLogicIntegratedClassifier(LogicIntegrationBase):
    """
    Wraps any torch.nn.Module whose forward(x) returns [N, C] logits (multi‐class),
    but additionally polls in the background (either every N timesteps or every N seconds)
    and injects new Facts into a PyReason logic program.
    """
    def __init__(
            self,
            model,
            class_names: List[str],
            identifier: str = 'classifier',
            interface_options: ModelInterfaceOptions = None,
            logic_program=None,
            poll_interval: Optional[Union[int, timedelta]] = None,
            poll_condition: Optional[str] = None,
            input_fn: Optional[Callable[[], Any]] = None,
    ):
        """
        :param model: PyTorch model to be integrated.
        :param class_names: List of class names for the model output.
        :param identifier: Identifier for the model, used as the constant in the facts.
        :param interface_options: Options for the model interface, including threshold and snapping behavior.
        :param logic_program: PyReason logic program
        :param poll_interval: How often to poll the model, either as:
            - an integer number of PyReason timesteps or
            - a `datetime.timedelta` object representing wall-clock time.
            If `None`, polling is disabled.
        :param poll_condition: The name of the predicate attached to the model that must be true to trigger a poll.
            If `None`, the model will be polled every `poll_interval` time steps/seconds.
        :param input_fn: Function to call to get the input to the model. This function should return a tensor.
        """
        super().__init__(model, class_names, interface_options, identifier)
        self.model = model
        self.class_names = class_names
        self.identifier = identifier
        self.interface_options = interface_options
        self.logic_program = logic_program
        self.poll_interval = poll_interval
        self.poll_condition = poll_condition
        self.input_fn = input_fn

        # normalize poll_interval
        if isinstance(poll_interval, int):
            self.poll_interval: Union[int, timedelta, None] = poll_interval
        else:
            self.poll_interval = poll_interval

        # start the async polling task if configured
        if self.poll_interval is not None and self.input_fn is not None:
            # this schedules the background task
            # self._poller_task = asyncio.create_task(self._poll_loop())
            # kick off the background thread
            t = threading.Thread(target=self._poll_loop, daemon=True)
            t.start()

    def _get_current_timestep(self):
        """
        Get the current timestep from the PyReason logic program.
        :return: Current timestep
        """
        if self.logic_program is not None and self.logic_program.interp is not None:
            interp = self.logic_program.interp
            t = interp.time
            return t
        elif pr.get_logic_program() is not None and pr.get_logic_program().interp is not None:
            self.logic_program = pr.get_logic_program()
            interp = self.logic_program.interp
            t = interp.time
            return t
        else:
            # raise ValueError("No PyReason logic program provided.")
            return -1

    def _poll_loop(self) -> None:
        """
        Background async loop that polls every self.poll_interval.
        """
        # if self.logic_program is None:
        #     raise ValueError("No logic program to add facts into.")

        # check if we have a logic program yet or not
        while True:
            current_time = self._get_current_timestep()
            # print("here")
            if current_time != -1:
                print("current time", current_time)
                # determine mode
                if isinstance(self.poll_interval, timedelta):
                    interval_secs = self.poll_interval.total_seconds()
                    while True:
                        print("in loop")
                        time.sleep(interval_secs)
                        current_time = self._get_current_timestep()
                        t1 = current_time + 1
                        t2 = t1

                        if self.poll_condition:
                            print(f"{self.poll_condition}({self.identifier})")
                            print(self.logic_program.interp.query(pr.Query(f"{self.poll_condition}({self.identifier})")))
                            if not self.logic_program.interp.query(pr.Query(f"{self.poll_condition}({self.identifier})")):
                                continue

                        x = self.input_fn()
                        _, _, facts = self.forward(x, t1, t2)
                        for f in facts:
                            print(f)
                            pr.add_fact(f)

                        # run the reasoning
                        pr.reason(again=True, restart=False)
                        print("reasoning done")
                        trace = pr.get_rule_trace(self.logic_program.interp)
                        print(trace[0])

                else:
                    step_interval = self.poll_interval
                    last_step = current_time + 1
                    while True:
                        # wait until enough timesteps have passed
                        while self._get_current_timestep() - last_step < step_interval:
                            time.sleep(0.01)
                        current = self._get_current_timestep()
                        t1, t2 = current, current
                        last_step = current

                        if self.poll_condition:
                            if not self.logic_program.interp.query(pr.Query(f"{self.poll_condition}({self.identifier})")):
                                continue

                        x = self.input_fn()
                        _, _, facts = self.forward(x, t1, t2)
                        for f in facts:
                            pr.add_fact(f)

                        # run the reasoning
                        pr.reason(again=True, restart=False)
                        print("reasoning done")
                        trace = pr.get_rule_trace(self.logic_program.interp)
                        print(trace[0])

                # # run the reasoning
                # pr.reason(again=True, restart=False)
                # print("reasoning done")
                # trace = pr.get_rule_trace(interpretation)
                # print(trace[0])

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

    def _infer(self, x: torch.Tensor) -> torch.Tensor:
        """
        Run the underlying model to get raw logits [N, C].
        """
        return self.model(x)

    def _postprocess(self, raw_output: torch.Tensor) -> torch.Tensor:
        """
        raw_output should be a [N, C] logits tensor.  Assert C == len(class_names),
        then apply softmax over dim=1 → [N, C] probabilities.
        """
        logits = raw_output
        if logits.dim() != 2 or logits.size(1) != len(self.class_names):
            raise ValueError(
                f"Expected logits of shape [N, C] with C={len(self.class_names)}, got {tuple(logits.shape)}"
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
        Given a [N, C] probability tensor, build a flat List[Fact],
        using threshold, snap_value, set_lower_bound, set_upper_bound.
        Returns N * C facts.
        """
        opts = self.interface_options
        prob = probabilities  # [N, C]

        # Build a threshold tensor
        threshold = torch.tensor(opts.threshold, dtype=prob.dtype, device=prob.device)
        condition = prob > threshold  # [N, C] boolean mask

        # Determine lower/upper for “true” entries
        if opts.snap_value is not None:
            snap_val = torch.tensor(opts.snap_value, dtype=prob.dtype, device=prob.device)
            lower_if_true = (snap_val if opts.set_lower_bound
                             else torch.tensor(0.0, dtype=prob.dtype, device=prob.device))
            upper_if_true = (snap_val if opts.set_upper_bound
                             else torch.tensor(1.0, dtype=prob.dtype, device=prob.device))
        else:
            lower_if_true = prob if opts.set_lower_bound else torch.zeros_like(prob)
            upper_if_true = prob if opts.set_upper_bound else torch.ones_like(prob)

        zeros = torch.zeros_like(prob)
        ones = torch.ones_like(prob)
        lower_bounds = torch.where(condition, lower_if_true, zeros)  # [N, C]
        upper_bounds = torch.where(condition, upper_if_true, ones)   # [N, C]

        N, C = prob.shape
        all_facts: List[Fact] = []

        for i in range(N):
            for j, class_name in enumerate(self.class_names):
                lower_val = lower_bounds[i, j].item()
                upper_val = upper_bounds[i, j].item()
                fact_str = f"{class_name}({self.identifier}) : [{lower_val:.3f}, {upper_val:.3f}]"
                fact_name = f"{self.identifier}-{class_name}-fact"
                f = Fact(fact_str, name=fact_name, start_time=t1, end_time=t2)
                all_facts.append(f)

        return all_facts

