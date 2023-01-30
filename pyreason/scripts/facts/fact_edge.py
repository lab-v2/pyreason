class Fact:
    
    def __init__(self, name, component, label, interval, t_lower, t_upper, static=False):
        self._name = name
        self._t_upper = t_upper
        self._t_lower = t_lower
        self._component = component
        self._label = label
        self._interval = interval
        self._static = static

    def get_name(self):
        return self._name

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
        net_diff_dict = {}
        net_diff_dict["component"] = str(self._component)
        net_diff_dict["label"] = str(self._label)
        net_diff_dict["confidence"] = self._interval.to_str()
        net_diff_dict["time"] = '[' + str(self._t_lower) + ',' + str(self._t_upper) + ']'
        return str(net_diff_dict)