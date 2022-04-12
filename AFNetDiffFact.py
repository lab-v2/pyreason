from abc import ABC
from NetDiffFact import NetDiffFact
import random

class AFNetDiffFact(ABC):

	def __init__(self, components, labels, intervals, times):
		self._labels = labels
		self._intervals = intervals
		self._times = times
		self._random_components = components
		self._index = 0
		random.shuffle(self._random_components)

	def getRandomFact(self):
		c = self._random_components[self._index]
		label = random.choice(self._labels)
		while (not label in c.get_labels()):
			label = random.choice(self._labels)
		bnd = random.choice(self._intervals)
		time = random.choice(self._times)
		if (self._index + 1 < len(self._random_components)):
			self._index = self._index + 1
		else:
			self._index = 0
		return NetDiffFact(c, label, bnd, time[0], time[1])


