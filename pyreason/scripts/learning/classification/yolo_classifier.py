from datetime import timedelta
from pathlib import Path
import random
import threading
import time

import cv2
import torch
import pyreason as pr
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.classification.logic_integration_base import LogicIntegrationBase
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions

from typing import List, Tuple, Optional, Union, Callable, Any

class YoloLogicIntegratedTemporalClassifier(LogicIntegrationBase):
    """
    Class to integrate a YOLO model with PyReason. The output of the model is returned to the
    user in the form of PyReason facts. The user can then add these facts to the logic program and reason using them.
    Wraps a YOLO model whose forward(x) returns bounding boxes with class probabilities.
    Implements _infer, _postprocess, and _pred_to_facts to replace the original forward().
    """

    def __init__(
        self,
        model,
        class_names: List[str],
        identifier: str = 'yolo_classifier',
        interface_options: ModelInterfaceOptions = None,
        poll_interval: Optional[Union[int, timedelta]] = None,
        poll_condition: Optional[str] = None,
        input_fn: Optional[Callable[[], Any]] = None
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
        self.poll_interval = poll_interval
        self.poll_condition = poll_condition
        self.input_fn = input_fn
        self.logic_program = None  # Get the current logic program
        print("Class Names: ", self.class_names)

        # normalize poll_interval
        if isinstance(poll_interval, int):
            self.poll_interval: Union[int, timedelta, None] = poll_interval
        else:
            self.poll_interval = poll_interval

        # start the async polling task if configured
        if self.poll_interval is not None and self.input_fn is not None:
            print("Running polling")
            # this schedules the background task
            # self._poller_task = asyncio.create_task(self._poll_loop())
            # kick off the background thread
            t = threading.Thread(target=self._poll_loop, daemon=True)
            t.start()

    def _infer(self, x: Any) -> Any:
        print("Running YOLO model inference...")
        # resized_image = cv2.resize(image, (640, 640))  # Direct resize
        # normalized_image = resized_image / 255.0  # Normalize
        result_predict = self.model.predict(source = x, imgsz=(640), conf=0.5) #the default image size
        #print("Predicted output:", result_predict)
        return result_predict

    def _postprocess(self, raw_output: Any) -> Any:
        """
        Process the raw output from the YOLO model to extract bounding boxes and class probabilities.
        """
        result = raw_output[0]  # Get the first result from the prediction
        box = result.boxes[0]  # Get the first bounding box from the result
        label_id = int(box.cls)
        confidence = float(box.conf)
        label_name = result.names[label_id]  # Get the label name from the names dictionary
        print(f"Predicted label: {label_name}, Confidence: {confidence:.2f}")
        return [label_name, confidence]
    
    def _pred_to_facts(
        self,
        raw_output: Any,
        result: List,
        confidence: float,

        t1: int = None,
        t2: int = None
    ) -> List[Fact]:
        """
        Given a [N, C] probability tensor, build a flat List[Fact],
        using threshold, snap_value, set_lower_bound, set_upper_bound.
        Returns N * C facts.
        """
        opts = self.interface_options
        print("Result: ", result)
        label = result[0]
        confidence = result[1]
        print("Label: ", label)
        print("Confidence: ", confidence)
        print("T1: ", t1, "T2: ", t2)
        # Build a threshold tensor
        threshold = torch.tensor(opts.threshold)
        condition = confidence > threshold  # [N, C] boolean mask

        # Determine lower/upper for “true” entries
        if opts.snap_value is not None:
            snap_val = opts.snap_value
            print("Sanp val: ", snap_val)
            lower_if_true = (snap_val if opts.set_lower_bound
                             else 0)
            upper_if_true = (snap_val if opts.set_upper_bound
                             else 1.0)
        else:
            lower_if_true = confidence if opts.set_lower_bound else 0
            upper_if_true = confidence if opts.set_upper_bound else 1.0

        all_facts: List[Fact] = []

        fact_str = f"_{label}({self.identifier}) : [{lower_if_true:.3f}, {upper_if_true:.3f}]"
        print(f"Creating fact: {fact_str}")
        fact_name = f"{self.identifier}-{label}-fact"
        f = Fact(fact_str, name=fact_name, start_time=0, end_time=0)
        all_facts.append(f)

        return all_facts
    
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
            print("Found")
            self.logic_program = pr.get_logic_program()
            interp = self.logic_program.interp
            t = interp.time
            return t
        else:
            print("Not found")
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
            print("here")
            print("current time", current_time)
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
                                print(f"Condition {self.poll_condition} not met, skipping poll.")
                                continue
                        print("Condition met, polling model...")           
                        x = self.input_fn()
                        _, _, facts = self.forward(x, t1, t2)
                        for f in facts:
                            print(f)
                            pr.add_fact(f)

                        # run the reasoning
                        pr.reason(again=True, restart=True)
                        print("reasoning done")
                        trace = pr.get_rule_trace(self.logic_program.interp)
                        print("Len of trace: ", len(trace))
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

