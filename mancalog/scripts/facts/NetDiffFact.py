from NetCompTarget import NetCompTarget

class NetDiffFact(NetCompTarget):
	
	def __init__(self, component, label, interval, t_lower, t_upper):
		super().__init__(component, label, interval)
		self._t_upper = t_upper
		self._t_lower = t_lower

	def getTimeUpper(self):
		return self._t_upper

	def getTimeLower(self):
		return self._t_lower

	def __str__(self):
		net_diff_dict = {}
		net_diff_dict["component"] = str(self._component)
		net_diff_dict["label"] = str(self._label)
		net_diff_dict["confidence"] = str(self._interval)
		net_diff_dict["time"] = '[' + str(self._t_lower) + ',' + str(self._t_upper) + ']'
		return str(net_diff_dict)