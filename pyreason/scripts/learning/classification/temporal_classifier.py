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
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class TemporalLogicIntegratedClassifier(torch.nn.Module):
    """
    Class to integrate a PyTorch model with PyReason. The output of the model is returned to the
    user in the form of PyReason facts. The user can then add these facts to the logic program and reason using them.
    """
    # from pyreason import Program
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
        super(TemporalLogicIntegratedClassifier, self).__init__()
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

    def update_classes_and_probs_for_filter(self, probabilities) -> torch.Tensor:
        """
        A user may want to restrict the number of classe so that the classifier only returns facts for a subset of classes.  
        This is useful for large models like CLIP, where the model has 4000 classes. 
        We will set the new possible classes to be limited to the class names given to the classifier.
        :param probabilities: The probabilities output by the model.
        """
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
                            print("poll condition", self.poll_condition)
                            print(f"{self.poll_condition}({self.identifier})")
                            print("Eval: ")
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
                print(f"Error during model forward pass after trying to get the output both ways: {e}")

        if limit_classification_output_classes:
            probabilities = self.update_classes_and_probs_for_filter(probabilities)
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

