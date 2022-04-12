from abc import ABC, abstractmethod

class AbstractAgregationFunction(ABC):

	@abstractmethod
	def aggregate(self, bounds):
		pass