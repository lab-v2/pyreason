from mancalog.scripts.components.edge import Edge
import mancalog.scripts.numba_wrapper.numba_types.node_type as node
import mancalog.scripts.numba_wrapper.numba_types.edge_type as edge
import mancalog.scripts.numba_wrapper.numba_types.world_type as world
import mancalog.scripts.numba_wrapper.numba_types.label_type as label
import mancalog.scripts.numba_wrapper.numba_types.interval_type as interval

import numba


class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node.node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge.edge_type))

	def __init__(self, net_diff_graph, tmax):
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph

		# Make sure they are correct type
		if len(self.available_labels_node)==0:
			self.available_labels_node = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_node = numba.typed.List(self.available_labels_node)
		if len(self.available_labels_edge)==0:
			self.available_labels_edge = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_edge = numba.typed.List(self.available_labels_edge)

		self.interpretations_node = Interpretation._init_interpretations_node(self._tmax, numba.typed.List(self._net_diff_graph.get_nodes()), self.available_labels_node, self.specific_node_labels)
		self.interpretations_edge = Interpretation._init_interpretations_edge(self._tmax, numba.typed.List(self._net_diff_graph.get_edges()), self.available_labels_edge, self.specific_edge_labels)
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node.node_type, value_type=numba.types.ListType(node.node_type))
		for n in self._net_diff_graph.get_nodes():
			l = numba.typed.List.empty_list(node.node_type)
			[l.append(neigh) for neigh in self._net_diff_graph.neighbors(n)]
			self.neighbors[n] = l




	@staticmethod
	@numba.njit
	def _init_interpretations_node(tmax, nodes, available_labels, specific_labels):
		interpretations = numba.typed.List()
		for t in range(tmax+1):
			nas = numba.typed.Dict.empty(key_type=node.node_type, value_type=world.world_type)
			# General labels
			for n in nodes:
				nas[n] = n.get_initial_world(available_labels)
			# Specific labels
			for l, ns in specific_labels.items():
				for n in ns:
					nas[n].world[l] = interval.closed(0.0, 1.0)
			interpretations.append(nas)
		return interpretations
	
	@staticmethod
	@numba.njit
	def _init_interpretations_edge(tmax, edges, available_labels, specific_labels):
		interpretations = numba.typed.List()
		for t in range(tmax+1):
			nas = numba.typed.Dict.empty(key_type=edge.edge_type, value_type=world.world_type)
			# General labels
			for e in edges:
				nas[e] = e.get_initial_world(available_labels)
			# Specific labels
			for l, es in specific_labels.items():
				for e in es:
					nas[e].world[l] = interval.closed(0.0, 1.0)
			interpretations.append(nas)
		return interpretations
		

	def is_satisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			if comp.get_type()=='node':
				world = self.interpretations_node[time][comp]
			elif comp.get_type=='edge':
				world = self.interpretations_edge[time][comp]
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
		self._apply_fact_stat(self.interpretations_node, facts)

	def _apply_fact(self, fact, t):
		comp = fact.get_component()
		if comp.get_type()=='node':
			world = self.interpretations_node[t][comp]
		elif comp.get_type()=='edge':
			world = self.interpretations_edge[t][comp]
		world.update(fact.get_label(), fact.get_bound())

	@staticmethod
	@numba.njit
	def _apply_fact_stat(interpretations_node, facts):
		for fact in facts:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				world = interpretations_node[t][fact.get_component()]
				world.update(fact.get_label(), fact.get_bound()) 
		

	def apply_local_rules(self, rules):
		self._apply_local_rule_stat(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._net_diff_graph.get_nodes()), numba.typed.List(self._net_diff_graph.get_edges()), self.neighbors)


	def _apply_local_rule(self, rule, t):
		tDelta = t - rule.get_delta()
		if (tDelta >= 0):
			for n in self._net_diff_graph.get_nodes():
				if (self.are_satisfied(tDelta, n, rule.get_target_criteria())):
					a = self._get_neighbors(n)
					b = self._get_qualified_neigh(tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
					bnd = rule.influence(neigh = a, qualified_neigh = b)
					self._na_update(t, n, (rule.get_target(), bnd))

	@staticmethod
	@numba.njit
	def _apply_local_rule_stat(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors):
		for t in range(tmax+1):
			for rule in rules:
				tDelta = t - rule.get_delta()
				if (tDelta >= 0):
					# Go through all nodes and check if any rules apply to them
					for n in nodes:
						if are_satisfied_stat_node(interpretations_node, tDelta, n, rule.get_target_criteria_node()):
							a = neighbors[n]
							b = _get_qualified_neigh_stat(interpretations_node, interpretations_edge, neighbors[n], tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
							bnd = rule.influence(neigh=a, qualified_neigh=b)
							_na_update_stat_node(interpretations_node, t, n, (rule.get_target(), bnd))
					# Go through all edges and check if any rules apply to them.
					# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
					for e in edges:
						if are_satisfied_stat_edge(interpretations_edge, tDelta, e, rule.get_target_criteria_edge()):
							# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
							# When making this, refer to the nodes loop section (4 lines above)
							pass
			print('Completed timestep:', t)
							

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
		if comp.get_type()=='node':
			world = self.interpretations_node[time][comp]
		elif comp.get_type()=='edge':
			world = self.interpretations_edge[time][comp]
		result = world.get_bound(label)

		return result


	def _get_neighbors(self, node):
		return list(self._net_diff_graph.neighbors(node))


	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidates = self._get_neighbours(node)
		if(nc_node != None):
			candidates[:] = (n for n in candidates if self.are_satisfied(time, n, nc_node))
		if(nc_edge != None):
			candidates[:] = (n for n in candidates if self.are_satisfied(time, Edge(n.get_id(), node.get_id()), nc_edge))

		result = candidates

		return result

	def _na_update(self, time, comp, na):
		if comp.get_type()=='node':
			world = self.interpretations_node[time][comp]
		if comp.get_type()=='edge':
			world = self.interpretations_edge[time][comp]
		world.update(na[0], na[1])

	def copy(self, interpretation):
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					self._na_update(t, comp, (label, interpretation.get_bound(t, comp, label)))
		

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


@numba.njit
def _get_qualified_neigh_stat(interpretations_node, interpretations_edge, candidates, time, node, nc_node, nc_edge):
	result = numba.typed.List()
	if(len(nc_node)>0):
		[result.append(n) for n in candidates if are_satisfied_stat_node(interpretations_node, time, n, nc_node)]
	if(len(nc_edge)>0):
		[result.append(n) for n in candidates if are_satisfied_stat_edge(interpretations_edge, time, edge.Edge(n.get_id(), node.get_id()), nc_edge)]

	return result

@numba.njit
def _na_update_stat_node(interpretations, time, comp, na):
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		world.update(na[0], na[1])
	except:
		return

@numba.njit
def _na_update_stat_edge(interpretations, time, comp, na):
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		world.update(na[0], na[1])
	except:
		return

@numba.njit
def are_satisfied_stat_node(interpretations, time, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_stat_node(interpretations, time, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_stat_node(interpretations, time, comp, na):
	result = False
	if (not (na[0] is None or na[1] is None)):
		world = interpretations[time][comp]
		# This is to prevent a key error in case the label is a specific label
		try:
			result = world.is_satisfied(na[0], na[1])
		except:
			result = False
	else:
		result = True
	return result

@numba.njit
def are_satisfied_stat_edge(interpretations, time, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_stat_edge(interpretations, time, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_stat_edge(interpretations, time, comp, na):
	result = False
	if (not (na[0] is None or na[1] is None)):
		world = interpretations[time][comp]
		# This is to prevent a key error in case the label is a specific label
		try:
			result = world.is_satisfied(na[0], na[1])
		except:
			result = False
	else:
		result = True
	return result
