import portion

class NetDiffWorld:

	def __init__(self, labels):
		self._world = []
		for label in labels:
			self._world.append((label, portion.closed(0,1)))

	def isSatisfied(self, label, interval):
		result = False
		for (l, bnd) in self._world:
			if (l == label):
				result = bnd in interval
				break

		return result

	def update(self, label, interval):
		lwanted = None
		bwanted = None 
		for (l, bnd) in self._world:
			if l == label:
				lwanted = l
				bwanted = bnd
				break
		bnd = bwanted & interval
		self._world.remove((lwanted, bwanted))
		self._world.append((lwanted, bnd))

	def getBound(self, label):
		result = None
		for (l, bnd) in self._world:
			if l == label:
				result = bnd
				break
		return result


	def __str__(self):
		result = ''
		for (label, bnd) in self._world:
			result = result + label.getValue() + ',' + str(bnd) + '\n'

		return result

