from abc import ABC, abstractmethod


class AbstractInfluenceFunction(ABC):

	@abstractmethod
	def influence(self, neigh, qualified_neigh):
		pass