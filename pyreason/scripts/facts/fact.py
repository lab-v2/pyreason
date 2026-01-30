import pyreason.scripts.utils.fact_parser as fact_parser
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


class Fact:
    def __init__(self, fact_text: str, name: str = None, start_time: int = 0, end_time: int = 0, static: bool = False):
        """Define a PyReason fact that can be loaded into the program using `pr.add_fact()`

        :param fact_text: The fact in text format. Must follow these formatting rules:

            **Format:** `predicate(component)` or `predicate(component):bound`

            **Predicate rules:**
            - Must start with a letter (a-z, A-Z) or underscore (_)
            - Can contain letters, digits (0-9), and underscores
            - Cannot start with a digit
            - Examples: `viewed`, `has_access`, `_internal`, `pred123`

            **Component rules:**
            - Node fact: Single component `predicate(node1)`
            - Edge fact: Two components separated by comma `predicate(node1,node2)`
            - Cannot contain parentheses, colons, or nested structures

            **Bound rules:**
            - If omitted, defaults to True (1.0)
            - Boolean: `True` or `False` (case-insensitive)
            - Interval: `[lower,upper]` where both values are in range [0, 1]
            - Negation: `~predicate(component)` (equivalent to False, cannot be combined with explicit bound)

            **Valid examples:**
            - `'viewed(Zach)'` - defaults to True
            - `'viewed(Zach):True'` - explicit True
            - `'viewed(Zach):False'` - explicit False
            - `'~viewed(Zach)'` - negation (False)
            - `'viewed(Zach):[0.5,0.8]'` - interval bound
            - `'connected(Alice,Bob)'` - edge fact
            - `'connected(Alice,Bob):[0.7,0.9]'` - edge fact with interval
            - `'~pred(node):[0.2,0.8]'` - negation with explicit bound
            NOTE: Negating an explicit bound will round the upper and lower bounds to 10 decimal places before taking the negation
            This is needed to avoid floating point precision errors.

            **Invalid examples:**
            - `'123pred(node)'` - predicate starts with digit
            - `'pred@name(node)'` - invalid characters in predicate
            - `'pred(node1,node2,node3)'` - more than 2 components
            - `'pred(node):[1.5,2.0]'` - values out of range [0,1]

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
