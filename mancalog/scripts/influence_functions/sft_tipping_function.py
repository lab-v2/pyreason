import portion
from mancalog.scripts.influence_functions.abstract_influentce_function import AbstractInfluenceFunction


class SftTippingFunction(AbstractInfluenceFunction):
	
	def __init__(self):
		self._threshold = 0.5
		self._bnd_update = portion.closed(0.7,1)

	def influence(self, neigh, qualified_neigh, nas):
		bnd = portion.closed(0,1)
		if len(neigh) != 0:
			if (len(qualified_neigh) / len(neigh)) > self._threshold:
				bnd = self._bnd_update

		return bnd