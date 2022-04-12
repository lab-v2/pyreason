import portion
from NetDiffWorld import NetDiffWorld
from NetDiffNode import NetDiffNode
from NetDiffEdge import NetDiffEdge

class NetDiffInterpretation:

	def __init__(self, net_diff_graph, tmax = 1):
		self._interpretations = []
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph
		for t in range(0, self._tmax + 1):
			nas = []
			for comp in self._net_diff_graph.get_components():
				nas.append((comp, comp.getInitialWorld()))
			nas.append((self._net_diff_graph, self._net_diff_graph.getInitialWorld()))
			self._interpretations.append(nas)

		

	def isSatisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			for (n, world) in self._interpretations[time]:
				if (n.equals(comp)):
					result = world.isSatisfied(na[0], na[1])
					break
		else:
			result = True
		return result

	def areSatisfied(self, time, comp, nas):
		result = True
		for (label, interval) in nas:
			result = result and self.isSatisfied(time, comp, (label, interval))

		return result

	def applyFact(self, fact):
		for t in range(fact.getTimeLower(), fact.getTimeUpper() + 1):
			for (c, world) in self._interpretations[t]:
				if c.equals(fact.getComponent()):
					world.update(fact.getLabel(), fact.getBound())
					break


	def applyLocalRule(self, rule, t):
		if t <= self._tmax:
			tDelta = t - rule.getDelta()
			if (tDelta >= 0):
				for n in self._net_diff_graph.getNodes():
					if (self.areSatisfied(tDelta, n, rule.getTargetCriteria())):
						a = self._get_neighbours(n)
						b = self._get_qualified_neigh(tDelta, n, rule.getNeighNodes(), rule.getNeighEdges())
						c = self._interpretations[tDelta]
						bnd = rule.influence(neigh = a, qualified_neigh = b, nas = c)
						self._na_update(t, n, (rule.getTarget(), bnd))

	def applyGlobalRule(self, rule, t):
		bounds = []
		if t <= self._tmax:
			for n in self._net_diff_graph.getNodes():
				if (self.areSatisfied(t, n, rule.getLocalTarget())):
					bnd = self.getBound(t, n, rule.getLocalLabel())
					bounds.append(bnd)
			updated_bnd = rule.aggregate(bounds)
			self._na_update(t, self._net_diff_graph, (rule.getGlobalLabel(), updated_bnd))


	def getBound(self, time, comp, label):
		result = None
		for (c, world) in self._interpretations[time]:
			if(c.equals(comp)):
				result = world.getBound(label)
				break

		return result


	def _get_neighbours(self, node):
		return list(self._net_diff_graph.neighbors(node))
		#return self._net_diff_graph.get_neighbours(node)

	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidatos = self._get_neighbours(node)
		if(nc_node != None):
			for n in candidatos:
				if(not self.areSatisfied(time, n, nc_node)):
					candidatos.remove(n)
		if(nc_edge != None):
			for n in candidatos:
				if(not self.areSatisfied(time, NetDiffEdge(n.getId(), node.getId()), nc_edge)):
					candidatos.remove(n)

		result = candidatos

		return result

	def _na_update(self, time, comp, na):
		for (c, world) in self._interpretations[time]:
			if comp.equals(c):
				world.update(na[0], na[1])
				break
		

	def __str__(self):
		result = ''
		for t in range(0, len(self._interpretations)):
			result = result + 'time: ' + str(t) + '\n'
			for (c, world) in self._interpretations[t]:
					result = result + str(c) + '\n'
					result = result + str(world)

		return result