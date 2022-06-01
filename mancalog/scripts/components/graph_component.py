from abc import ABC, abstractmethod
from mancalog.scripts.components.world import World


class GraphComponent(ABC):
	available_labels = []

	@abstractmethod
	def get_labels(self):
		pass

	def equals(self, element):
		return isinstance(element, type(self)) and self._id == element.get_id()

	def get_initial_world(self):
		return World(self.get_labels())

	@abstractmethod
	def get_type(self):
		pass