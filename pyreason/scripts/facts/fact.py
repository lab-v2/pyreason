import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

from typing import Tuple
from typing import List
from typing import Union


class Fact:
    def __init__(self, name: str, component: Union[str, Tuple[str, str]], attribute: str, bound: Union[interval.Interval, List[float]], start_time: int, end_time: int, static: bool = False):
        """Define a PyReason fact that can be loaded into the program using `pr.add_fact()`

        :param name: The name of the fact. This will appear in the trace so that you know when it was applied
        :type name: str
        :param component: The node or edge that whose attribute you want to change
        :type component: str | Tuple[str, str]
        :param attribute: The attribute you would like to change for the specified node/edge
        :type attribute: str
        :param bound: The bound to which you'd like to set the attribute corresponding to the specified node/edge
        :type bound: interval.Interval | List[float]
        :param start_time: The timestep at which this fact becomes active
        :type start_time: int
        :param end_time: The last timestep this fact is active
        :type end_time: int
        :param static: If the fact should be active for the entire program. In which case `start_time` and `end_time` will be ignored
        :type static: bool
        """
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
