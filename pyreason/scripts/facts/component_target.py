class ComponentTarget:
	
	def __init__(self, component, label = None, interval = None):
		self._component = component
		self._label = label
		self._interval = interval

	def get_bound(self):
		return self._interval

	def get_label(self):
		return self._label

	def get_component(self):
		return self._component

	def __str__(self):
		return str(self._component) + '\n' + str(self._label) + '\n' + self._interval.to_str()
