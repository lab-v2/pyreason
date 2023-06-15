import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

from typing import Tuple
from typing import List


class Fact:
    def __init__(self, name: str, component: str | Tuple[str, str], attribute: str, bound: interval.Interval | List[float], start_time: int, end_time: int, static: bool = False):
        self.name = name
        self.t_upper = start_time
        self.t_lower = end_time
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
        self._label = label.Label(attribute)

        # Set bound to correct type
        if isinstance(bound, list):
            self.interval = interval.closed(*bound)
