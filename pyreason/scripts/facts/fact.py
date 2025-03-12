import pyreason.scripts.utils.fact_parser as fact_parser
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


class Fact:
    def __init__(self, fact_text: str, name: str = None, start_time: int = 0, end_time: int = 0, static: bool = False):
        """Define a PyReason fact that can be loaded into the program using `pr.add_fact()`

        :param fact_text: The fact in text format. Example: `'pred(x,y) : [0.2, 1]'` or `'pred(x,y) : True'`
        :type fact_text: str
        :param name: The name of the fact. This will appear in the trace so that you know when it was applied
        :type name: str
        :param start_time: The timestep at which this fact becomes active
        :type start_time: int
        :param end_time: The last timestep this fact is active
        :type end_time: int
        :param static: If the fact should be active for the entire program. In which case `start_time` and `end_time` will be ignored
        :type static: bool
        """
        pred, component, bound, fact_type = fact_parser.parse_fact(fact_text)
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.static = static
        self.pred = label.Label(pred)
        self.component = component
        self.bound = bound
        self.type = fact_type

    def __str__(self):
        s = f'{self.pred}({self.component}) : {self.bound}'
        if self.static:
            s += ' | static'
        else:
            s += f' | start: {self.start_time} -> end: {self.end_time}'
        return s
