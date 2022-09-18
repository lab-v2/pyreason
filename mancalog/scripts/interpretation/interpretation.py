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

	def __init__(self, graph, tmax, history):
		self._tmax = tmax
		self._graph = graph
		self._history = history

		# Initialize list of tuples for rules to be applied, only if history is off
		if not self._history:
			self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node.node_type, label.label_type, interval.interval_type)))
			self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge.edge_type, label.label_type, interval.interval_type)))

		# Make sure they are correct type
		if len(self.available_labels_node)==0:
			self.available_labels_node = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_node = numba.typed.List(self.available_labels_node)
		if len(self.available_labels_edge)==0:
			self.available_labels_edge = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_edge = numba.typed.List(self.available_labels_edge)

		self.interpretations_node = self._init_interpretations_node(self._tmax, numba.typed.List(self._graph.get_nodes()), self.available_labels_node, self.specific_node_labels, self._history)
		self.interpretations_edge = self._init_interpretations_edge(self._tmax, numba.typed.List(self._graph.get_edges()), self.available_labels_edge, self.specific_edge_labels, self._history)
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node.node_type, value_type=numba.types.ListType(node.node_type))
		for n in self._graph.get_nodes():
			l = numba.typed.List.empty_list(node.node_type)
			[l.append(neigh) for neigh in self._graph.neighbors(n)]
			self.neighbors[n] = l


	@staticmethod
	@numba.njit
	def _init_interpretations_node(tmax, nodes, available_labels, specific_labels, history):
		interpretations = numba.typed.List()
		if history:
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
		else:
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
	def _init_interpretations_edge(tmax, edges, available_labels, specific_labels, history):
		interpretations = numba.typed.List()
		if history:
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
		else:
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


	def apply_facts(self, facts):
		if self._history:
			self._apply_fact(self.interpretations_node, facts)


	@staticmethod
	@numba.njit
	def _apply_fact(interpretations_node, facts):
		for fact in facts:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				world = interpretations_node[t][fact.get_component()]
				world.update(fact.get_label(), fact.get_bound())
		

	def apply_rules(self, rules, facts):
		if self._history:
			self._apply_rule(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), self.neighbors)
		else:
			self._apply_rule_no_history(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, facts, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels)


	@staticmethod
	@numba.njit
	def _apply_rule(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors):
		for t in range(tmax+1):
			for rule in rules:
				tDelta = t - rule.get_delta()
				if (tDelta >= 0):
					# Go through all nodes and check if any rules apply to them
					for n in nodes:
						if are_satisfied_node(interpretations_node, tDelta, n, rule.get_target_criteria_node()):
							a = neighbors[n]
							b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
							bnd = rule.influence(neigh=a, qualified_neigh=b)
							_na_update_node(interpretations_node, t, n, (rule.get_target(), bnd))
					# Go through all edges and check if any rules apply to them.
					# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
					for e in edges:
						if are_satisfied_edge(interpretations_edge, tDelta, e, rule.get_target_criteria_edge()):
							# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
							# When making this, refer to the nodes loop section (4 lines above)
							pass

	@staticmethod
	@numba.njit
	def _apply_rule_no_history(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts, labels_node, labels_edge, specific_labels_node, specific_labels_edge):
		for t in range(tmax+1):
			# Apply facts and reset interpretation before starting
			if t>0:
				# Reset nodes
				# General labels
				for n in nodes:
					for l in labels_node:
						interpretations_node[0][n].world[l].set_lower_upper(0, 1)
				# Specific labels
				for l, ns in specific_labels_node.items():
					for n in ns:
						interpretations_node[0][n].world[l].set_lower_upper(0, 1)
				# Reset edges
				# General labels
				for e in edges:
					interpretations_edge[0][e].world[l].set_lower_upper(0, 1)
				# Specific labels
				for l, es in specific_labels_edge.items():
					for e in es:
						interpretations_edge[0][e].world[l].set_lower_upper(0, 1)

			for fact in facts:
				if t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
					world = interpretations_node[0][fact.get_component()]
					world.update(fact.get_label(), fact.get_bound())				

			# Apply the rules that need to be applied at this timestep
			for i in range(len(rules_to_be_applied_node)):
				if rules_to_be_applied_node[i][0]==t:
					_na_update_node(interpretations_node, 0, rules_to_be_applied_node[i][1], (rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3]))
			# Remove from queue after applied. For now don't remove - will affect performance

			for i in range(len(rules_to_be_applied_edge)):
				if rules_to_be_applied_edge[i][0]==t:
					_na_update_edge(interpretations_edge, 0, rules_to_be_applied_edge[i][1], (rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3]))

			for rule in rules:
				# Go through all nodes and check if any rules apply to them
				for n in nodes:
					if are_satisfied_node(interpretations_node, 0, n, rule.get_target_criteria_node()):
						a = neighbors[n]
						b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], 0, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
						bnd = rule.influence(neigh=a, qualified_neigh=b)
						rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
				# Go through all edges and check if any rules apply to them.
				# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
				for e in edges:
					if are_satisfied_edge(interpretations_edge, 0, e, rule.get_target_criteria_edge()):
						# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
						# When making this, refer to the nodes loop section (4 lines above)
						# Then append the information to rules_to_be_applied_edge
						pass


	def _get_neighbors(self, node):
		return list(self._graph.neighbors(node))


	def copy(self, interpretation):
		tmax = self._tmax if self._history else 0
		self._copy(self.interpretations_node, self.interpretations_edge, interpretation.interpretations_node, interpretation.interpretations_edge, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), tmax, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels)


	@staticmethod
	@numba.njit
	def _copy(interpretations_node_1, interpretations_edge_1, interpretations_node_2, interpretations_edge_2, nodes, edges, tmax, labels_node, labels_edge, specific_labels_node, specific_labels_edge):
		for t in range(tmax+1):
			# Copy the standard labels
			for n in nodes:
				for l in labels_node:
					_na_update_node(interpretations_node_1, t, n, (l, _get_bound_node(interpretations_node_2, t, n, l)))
			for e in edges:
				for l in labels_edge:
					_na_update_edge(interpretations_edge_1, t, e, (l, _get_bound_edge(interpretations_edge_2, t, e, l)))
			# Copy the specific labels
			for l, ns in specific_labels_node.items():
				for n in ns:
					_na_update_node(interpretations_node_1, t, n, (l, _get_bound_node(interpretations_node_2, t, n, l)))
			for l, es in specific_labels_edge.items():
				for e in es:
					_na_update_edge(interpretations_edge_1, t, e, (l, _get_bound_edge(interpretations_edge_2, t, e, l)))


	def __eq__(self, interp):
		tmax = self._tmax if self._history else 0
		return self._eq(self.interpretations_node, self.interpretations_edge, interp.interpretations_node, interp.interpretations_edge, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), tmax, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels)


	@staticmethod
	@numba.njit
	def _eq(interpretations_node_1, interpretations_edge_1, interpretations_node_2, interpretations_edge_2, nodes, edges, tmax, labels_node, labels_edge, specific_labels_node, specific_labels_edge):
		result = True
		for t in range(tmax+1):
			# Compare the standard labels
			for n in nodes:
				for l in labels_node:
					if _get_bound_node(interpretations_node_1, t, n, l) != _get_bound_node(interpretations_node_2, t, n, l):
						result = False
						return result
			for e in edges:
				for l in labels_edge:
					if _get_bound_edge(interpretations_edge_1, t, e, l) != _get_bound_edge(interpretations_edge_2, t, e, l):
						result = False
						return result
			# Compare the specific labels
			for l, ns in specific_labels_node.items():
				for n in ns:
					if _get_bound_node(interpretations_node_1, t, n, l) != _get_bound_node(interpretations_node_2, t, n, l):
						result = False
						return result
			for l, es in specific_labels_edge.items():
				for e in es:
					if _get_bound_edge(interpretations_edge_1, t, e, l) != _get_bound_edge(interpretations_edge_2, t, e, l):
						result = False
						return result
		return result
				



@numba.njit
def _get_bound_node(interpretations_node, time, comp, l):
	world = interpretations_node[time][comp]
	return world.get_bound(l)


@numba.njit
def _get_bound_edge(interpretations_edge, time, comp, l):
	world = interpretations_edge[time][comp]
	return world.get_bound(l)


@numba.njit
def _get_qualified_neigh(interpretations_node, interpretations_edge, candidates, time, node, nc_node, nc_edge):
	result = numba.typed.List()
	if(len(nc_node)>0):
		[result.append(n) for n in candidates if are_satisfied_node(interpretations_node, time, n, nc_node)]
	if(len(nc_edge)>0):
		[result.append(n) for n in candidates if are_satisfied_edge(interpretations_edge, time, edge.Edge(n.get_id(), node.get_id()), nc_edge)]

	return result

@numba.njit
def _na_update_node(interpretations, time, comp, na):
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		world.update(na[0], na[1])
	except:
		return

@numba.njit
def _na_update_edge(interpretations, time, comp, na):
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		world.update(na[0], na[1])
	except:
		return

@numba.njit
def are_satisfied_node(interpretations, time, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_node(interpretations, time, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_node(interpretations, time, comp, na):
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
def are_satisfied_edge(interpretations, time, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_edge(interpretations, time, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_edge(interpretations, time, comp, na):
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
