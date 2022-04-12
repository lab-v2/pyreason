from abc import ABC,abstractmethod

class AbstractInfluenceFunction:
	
	@abstractmethod
	def influence(self, neigh, qualified_neigh, nas):
		pass