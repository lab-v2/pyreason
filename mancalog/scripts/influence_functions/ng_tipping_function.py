import portion
import mancalog.scripts.interval.interval as interval
from mancalog.scripts.influence_functions.abstract_influentce_function import AbstractInfluenceFunction


class NgTippingFunction(AbstractInfluenceFunction):
	
	def __init__(self):
		self._threshold = 1.0
		self._bnd_update = interval.closed(0, 0.2)

	def influence(self, neigh, qualified_neigh):
		bnd = interval.closed(0, 1)
		if len(neigh) != 0:
			if (len(qualified_neigh) / len(neigh)) > self._threshold:
				bnd = self._bnd_update

		return bnd
