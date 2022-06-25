from mancalog.scripts.facts.component_target import ComponentTarget


class Fact(ComponentTarget):
	
	def __init__(self, component, label, interval, t_lower, t_upper):
		super().__init__(component, label, interval)
		self._t_upper = t_upper
		self._t_lower = t_lower

	def get_time_upper(self):
		return self._t_upper

	def get_time_lower(self):
		return self._t_lower

	def __str__(self):
		net_diff_dict = {}
		net_diff_dict["component"] = str(self._component)
		net_diff_dict["label"] = str(self._label)
		net_diff_dict["confidence"] = self._interval.to_str()
		net_diff_dict["time"] = '[' + str(self._t_lower) + ',' + str(self._t_upper) + ']'
		return str(net_diff_dict)