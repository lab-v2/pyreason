from mancalog.scripts.components.world import World
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge


class Interpretation:

	def __init__(self, net_diff_graph, tmax = 1):
		self.interpretations = []
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph
		for t in range(0, self._tmax + 1):
			nas = {}
			for comp in self._net_diff_graph.get_components():
				nas[comp] = comp.get_initial_world()
			
			# nas[self._net_diff_graph] = self._net_diff_graph.get_initial_world()
			self.interpretations.append(nas)

		

	def is_satisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			world = self.interpretations[time][comp]
			result = world.is_satisfied(na[0], na[1])
		else:
			result = True
		return result

	def are_satisfied(self, time, comp, nas):
		result = True
		for (label, interval) in nas:
			result = result and self.is_satisfied(time, comp, (label, interval))

		return result

	def apply_facts(self, facts):
		for fact in facts:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				world = self.interpretations[t][fact.get_component()]
				world.update(fact.get_label(), fact.get_bound()) 

	def apply_local_rules(self, rules):
		for t in range(self._tmax + 1):
			for rule in rules:
				self._apply_local_rule(rule, t)

	def _apply_local_rule(self, rule, t):
		if t <= self._tmax:
			tDelta = t - rule.get_delta()
			if (tDelta >= 0):
				for n in self._net_diff_graph.get_nodes():
					if (self.are_satisfied(tDelta, n, rule.get_target_criteria())):
						a = self._get_neighbours(n)
						b = self._get_qualified_neigh(tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
						bnd = rule.influence(neigh = a, qualified_neigh = b)
						self._na_update(t, n, (rule.get_target(), bnd))

	def apply_global_rule(self, rule, t):
		bounds = []
		if t <= self._tmax:
			for n in self._net_diff_graph.get_nodes():
				if (self.are_satisfied(t, n, rule.get_local_target())):
					bnd = self.get_bound(t, n, rule.get_local_label())
					bounds.append(bnd)
			updated_bnd = rule.aggregate(bounds)
			self._na_update(t, self._net_diff_graph, (rule.get_global_label(), updated_bnd))


	def get_bound(self, time, comp, label):
		result = None
		world = self.interpretations[time][comp]
		result = world.get_bound(label)

		return result


	def _get_neighbours(self, node):
		return list(self._net_diff_graph.neighbors(node))

	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidatos = self._get_neighbours(node)
		if(nc_node != None):
			for n in candidatos:
				if(not self.are_satisfied(time, n, nc_node)):
					candidatos.remove(n)
		if(nc_edge != None):
			for n in candidatos:
				if(not self.are_satisfied(time, Edge(n.get_id(), node.get_id()), nc_edge)):
					candidatos.remove(n)

		result = candidatos

		return result

	def _na_update(self, time, comp, na):
		world = self.interpretations[time][comp]
		world.update(na[0], na[1])

	def copy(self, interpretation):
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					self._na_update(t, comp, (label, interpretation.get_bound(t, comp, label)))
		

	def __str__(self):
		result = ''
		for t in range(0, len(self.interpretations)):
			result = result + 'TIME: ' + str(t) + '\n'
			for c in self.interpretations[t].keys():
				world = self.interpretations[t][c]
				result = result + str(c) + ':' + '\n'
				result = result + str(world) + '\n'

		return result

	def __eq__(self, interp):
		result = True
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					if self.get_bound(t, comp, label) != interp.get_bound(t, comp, label):
						result = False
						break
				
				if not result:
					break

			if not result:
				break

		return result