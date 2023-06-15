import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

from typing import Tuple
from typing import List
from typing import Union


class Fact:
    def __init__(self, name: str, component: Union[str, Tuple[str, str]], attribute: str, bound: Union[interval.Interval, List[float]], start_time: int, end_time: int, static: bool = False):
        self.name = name
        self.t_upper = end_time
        self.t_lower = start_time
        self.component = component
        self.label = attribute
        self.interval = bound
        self.static = static

        # Check if it is a node fact or edge fact
        if isinstance(self.component, str):
            self.type = 'node'
        else:
            self.type = 'edge'

        # Set label to correct type
        self.label = label.Label(attribute)

        # Set bound to correct type
        if isinstance(bound, list):
            self.interval = interval.closed(*bound)
