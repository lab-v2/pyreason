from abc import ABC
class Label(ABC):

	def __init__(self, value):
		self._value = value

	def getValue(self):
		return self._value

	def __eq__(self, label):
		result = (self._value == label.getValue()) and isinstance(label, type(self))
		return result

	def __str__(self):
		return self._value