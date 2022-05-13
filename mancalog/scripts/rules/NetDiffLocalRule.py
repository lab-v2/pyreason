class NetDiffLocalRule:

	def __init__(self, target, tc, delta, neigh_nodes, neigh_edges, inf):
		self._target = target
		self._tc = tc
		self._delta = delta
		self._neigh_nodes = neigh_nodes
		self._neigh_edges = neigh_edges
		self._inf = inf

	def getTarget(self):
		return self._target

	def getTargetCriteria(self):
		return self._tc

	def getDelta(self):
		return self._delta

	def getNeighNodes(self):
		return self._neigh_nodes

	def getNeighEdges(self):
		return self._neigh_edges

	def getInf(self):
		return self._inf
	
	def influence(self, neigh, qualified_neigh, nas):
		return self._inf.influence(neigh, qualified_neigh, nas)

