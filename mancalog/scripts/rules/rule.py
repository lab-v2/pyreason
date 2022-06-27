class Rule:

	def __init__(self, target, tc, delta, neigh_nodes, neigh_edges, inf):
		self._target = target
		self._tc = tc
		self._delta = delta
		self._neigh_nodes = neigh_nodes
		self._neigh_edges = neigh_edges
		self._inf = inf

	def get_target(self):
		return self._target

	def get_target_criteria(self):
		return self._tc

	def get_delta(self):
		return self._delta

	def get_neigh_nodes(self):
		return self._neigh_nodes

	def get_neigh_edges(self):
		return self._neigh_edges

	def get_inf(self):
		return self._inf
	
	def influence(self, neigh, qualified_neigh):
		return self._inf.influence(neigh, qualified_neigh)

