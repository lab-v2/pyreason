from abc import ABC, abstractmethod
from mancalog.scripts.components.world import World

class GraphComponent(ABC):
	_labels = []

	@abstractmethod
	def get_labels(self):
		pass

	def equals(self, element):
		return isinstance(element, type(self)) and self._id == element.getId()

	def getInitialWorld(self):
		return World(self.get_labels())