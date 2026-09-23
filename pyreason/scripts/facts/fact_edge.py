class Fact:

    def __init__(self, name, component, label, interval, t_lower, t_upper, static=False):
        self._name = name
        self._t_upper = t_upper
        self._t_lower = t_lower
        self._component = component
        self._label = label
        self._interval = interval
        self._static = static

    # Numba FactType attribute names used inside the interpretation engines.
    @property
    def name(self):
        return self._name

    @property
    def component(self):
        return self._component

    @property
    def l(self):  # noqa: E743  # short name kept: old FactType field for the label
        return self._label

    @property
    def bnd(self):
        return self._interval

    @property
    def t_lower(self):
        return self._t_lower

    @property
    def t_upper(self):
        return self._t_upper

    @property
    def static(self):
        return self._static

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_component(self):
        return self._component

    def get_label(self):
        return self._label

    def get_bound(self):
        return self._interval

    def get_time_lower(self):
        return self._t_lower

    def get_time_upper(self):
        return self._t_upper

    def __str__(self):
        fact = {
            "type": 'pyreason edge fact',
            "name": self._name,
            "component": self._component,
            "label": self._label,
            "confidence": self._interval,
            "time": '[' + str(self._t_lower) + ',' + str(self._t_upper) + ']'
        }
        return fact
