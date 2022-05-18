import portion
from mancalog.scripts.components.world import World
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge


class Interpretation:

	def __init__(self, net_diff_graph, tmax = 1):
		self._interpretations = []
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph
		for t in range(0, self._tmax + 1):
			nas = {}
			for comp in self._net_diff_graph.get_components():
				nas[comp] = comp.getInitialWorld()
			
			nas[self._net_diff_graph] = self._net_diff_graph.getInitialWorld()
			self._interpretations.append(nas)

		

	def isSatisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			world = self._interpretations[time][comp]
			result = world.isSatisfied(na[0], na[1])
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
			world = self._interpretations[t][fact.getComponent()]
			world.update(fact.getLabel(), fact.getBound())


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
		world = self._interpretations[time][comp]
		result = world.getBound(label)

		return result


	def _get_neighbours(self, node):
		return list(self._net_diff_graph.neighbors(node))

	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidatos = self._get_neighbours(node)
		if(nc_node != None):
			for n in candidatos:
				if(not self.areSatisfied(time, n, nc_node)):
					candidatos.remove(n)
		if(nc_edge != None):
			for n in candidatos:
				if(not self.areSatisfied(time, Edge(n.getId(), node.getId()), nc_edge)):
					candidatos.remove(n)

		result = candidatos

		return result

	def _na_update(self, time, comp, na):
		world = self._interpretations[time][comp]
		world.update(na[0], na[1])
		

	def __str__(self):
		result = ''
		for t in range(0, len(self._interpretations)):
			result = result + 'TIME: ' + str(t) + '\n'
			for c in self._interpretations[t].keys():
				world = self._interpretations[t][c]
				result = result + str(c) + ':' + '\n'
				result = result + str(world) + '\n'

		return result

	def __eq__(self, interp):
		result = True
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					if self.getBound(t, comp, label) != interp.getBound(t, comp, label):
						result = False
						break
				
				if not result:
					break

			if not result:
				break

		return result