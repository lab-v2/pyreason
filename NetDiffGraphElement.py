from abc import ABC, abstractmethod
from NetDiffWorld import NetDiffWorld

class NetDiffGraphElement(ABC):
	_labels = []

	@abstractmethod
	def get_labels(self):
		pass

	def equals(self, element):
		return isinstance(element, type(self)) and self._id == element.getId()

	def getInitialWorld(self):
		return NetDiffWorld(self.get_labels())