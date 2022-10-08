from mancalog.scripts.components.edge import Edge
import mancalog.scripts.numba_wrapper.numba_types.node_type as node
import mancalog.scripts.numba_wrapper.numba_types.edge_type as edge
import mancalog.scripts.numba_wrapper.numba_types.world_type as world
import mancalog.scripts.numba_wrapper.numba_types.label_type as label
import mancalog.scripts.numba_wrapper.numba_types.interval_type as interval

import numba
import operator


class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node.node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge.edge_type))

	def __init__(self, graph, tmax, history, ipl):
		self._tmax = tmax
		self._graph = graph
		self._history = history
		self._ipl = ipl

		# Variable specific if no history. First fp operation
		if not self._history:
			self.first_fp = True

		# Initialize list of tuples for rules/facts to be applied
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node.node_type, label.label_type, interval.interval_type)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge.edge_type, label.label_type, interval.interval_type)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node.node_type, label.label_type, interval.interval_type)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge.edge_type, label.label_type, interval.interval_type)))

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
		self._apply_fact(facts, self.facts_to_be_applied_node)


	@staticmethod
	@numba.njit
	def _apply_fact(facts, facts_to_be_applied_node):
		for fact in facts:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				facts_to_be_applied_node.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound()))

		

	def apply_rules(self, rules, facts):
		if self._history:
			update = self._apply_rules(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self._ipl)
		else:
			update = self._apply_rules_no_history(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.get_nodes()), numba.typed.List(self._graph.get_edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self._ipl)
			update = True if self.first_fp else update
			self.first_fp = False
		return update

	@staticmethod
	@numba.njit
	def _apply_rules(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, ipl):
		update = False
		for t in range(tmax+1):
			# List of all the indices that need to be removed if applied to interpretation
			idx_to_be_removed = numba.typed.List.empty_list(numba.types.int64)
			
			# Start by applying the facts
			# Nodes
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3]
					# Check for inconsistencies
					if check_consistent_node(interpretations_node, t, comp, (l, bnd)):
						update = _na_update_node(interpretations_node, t, comp, (l, bnd), ipl) or update
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, t, comp, (l, bnd), ipl, tmax, True)
						update = True
			
			# Delete facts that have been applied
			facts_to_be_applied_node_copy = numba.typed.List(facts_to_be_applied_node)
			for i in idx_to_be_removed:
				facts_to_be_applied_node.remove(facts_to_be_applied_node_copy[i])
			
			# Edges
			idx_to_be_removed.clear()
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3]
					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, t, comp, (l, bnd)):
						update = _na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl) or update
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)
						update = True

			# Delete facts that have been applied
			facts_to_be_applied_edge_copy = numba.typed.List(facts_to_be_applied_edge)
			for i in idx_to_be_removed:
				facts_to_be_applied_edge.remove(facts_to_be_applied_edge_copy[i])

			# Apply the rules that need to be applied at this timestep and check of inconsistencies
			# Iterate through rules to be applied, and check if any timesteps match
			# Nodes
			idx_to_be_removed.clear()
			for i in range(len(rules_to_be_applied_node)):
				if rules_to_be_applied_node[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3]

					# Check for inconsistencies
					if check_consistent_node(interpretations_node, t, comp, (l, bnd)):
						update = _na_update_node(interpretations_node, t, comp, (l, bnd), ipl) or update
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, t, comp, (l, bnd), ipl, tmax, True)
						update = True

			# Delete rules that have been applied from list
			rules_to_be_applied_node_copy = numba.typed.List(rules_to_be_applied_node)
			for i in idx_to_be_removed:
				rules_to_be_applied_node.remove(rules_to_be_applied_node_copy[i])
			
			# Edges
			idx_to_be_removed.clear()
			for i in range(len(rules_to_be_applied_edge)):
				if rules_to_be_applied_edge[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3]

					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, t, comp, (l, bnd)):
						update = _na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl) or update
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)
						update = True

			# Delete rules that have been applied from list
			rules_to_be_applied_edge_copy = numba.typed.List(rules_to_be_applied_edge)
			for i in idx_to_be_removed:
				rules_to_be_applied_edge.remove(rules_to_be_applied_edge_copy[i])

			# Final step, add more rules to the list if applicable
			for rule in rules:
				if t+rule.get_delta()<=tmax:
					for n in nodes:
						if are_satisfied_node(interpretations_node, t, n, rule.get_target_criteria_node()):
							a = neighbors[n]
							b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], t, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
							bnd = influence(inf_name=rule.get_influence(), neigh=a, qualified_neigh=b, thresholds=rule.get_thresholds())
							rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
					# Go through all edges and check if any rules apply to them.
					# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
					for e in edges:
						if are_satisfied_edge(interpretations_edge, t, e, rule.get_target_criteria_edge()):
							# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
							# When making this, refer to the nodes loop section (4 lines above)
							# Then append the information to rules_to_be_applied_edge
							pass
		return update



	@staticmethod
	@numba.njit
	def _apply_rules_no_history(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl):
		update = False
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
					for l in labels_edge:
						interpretations_edge[0][e].world[l].set_lower_upper(0, 1)
				# Specific labels
				for l, es in specific_labels_edge.items():
					for e in es:
						interpretations_edge[0][e].world[l].set_lower_upper(0, 1)

			# List of all the indices that need to be removed if applied to interpretation
			idx_to_be_removed = numba.typed.List.empty_list(numba.types.int64)

			# Start by applying facts (NOTE: the variable update will only be true if facts apply for the first function call. DO NOT delete facts to be applied)
			# Nodes
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3]
					# Check for inconsistencies
					if check_consistent_node(interpretations_node, 0, comp, (l, bnd)):
						_na_update_node(interpretations_node, 0, comp, (l, bnd), ipl)
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, 0, comp, (l, bnd), ipl, tmax, True)
			
			# Edges
			idx_to_be_removed.clear()
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3]
					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, 0, comp, (l, bnd)):
						_na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl)
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, 0, comp, (l, bnd), ipl, tmax, True)

			# Apply the rules that need to be applied at this timestep
			# Nodes
			idx_to_be_removed.clear()
			for i in range(len(rules_to_be_applied_node)):
				if rules_to_be_applied_node[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3]

					# Check for inconsistencies
					if check_consistent_node(interpretations_node, 0, comp, (l, bnd)):
						_na_update_node(interpretations_node, 0, comp, (l, bnd), ipl)
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, 0, comp, (l, bnd), ipl, tmax, False)

			# Delete rules that have been applied from list
			rules_to_be_applied_node_copy = numba.typed.List(rules_to_be_applied_node)
			for i in idx_to_be_removed:
				rules_to_be_applied_node.remove(rules_to_be_applied_node_copy[i])

			# Edges
			idx_to_be_removed.clear()
			for i in range(len(rules_to_be_applied_edge)):
				if rules_to_be_applied_edge[i][0]==t:
					idx_to_be_removed.append(i)
					comp, l, bnd = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3]

					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, 0, comp, (l, bnd)):
						_na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl)
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, 0, comp, (l, bnd), ipl, tmax, False)

			# Delete rules that have been applied from list
			rules_to_be_applied_edge_copy = numba.typed.List(rules_to_be_applied_edge)
			for i in idx_to_be_removed:
				rules_to_be_applied_edge.remove(rules_to_be_applied_edge_copy[i])


			for rule in rules:
				# Go through all nodes and check if any rules apply to them
				# Only go through everything if the rule can be applied within the given timesteps. Otherwise it's an unnecessary loop
				if t+rule.get_delta()<=tmax:
					for n in nodes:
						if are_satisfied_node(interpretations_node, 0, n, rule.get_target_criteria_node()):
							a = neighbors[n]
							b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], 0, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
							bnd = influence(inf_name=rule.get_influence(), neigh=a, qualified_neigh=b, thresholds=rule.get_thresholds())
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
		


@numba.njit
def _get_qualified_neigh(interpretations_node, interpretations_edge, candidates, time, _node, nc_node, nc_edge):
	result_node = numba.typed.List.empty_list(numba.typed.List.empty_list(node.node_type))
	result_edge = numba.typed.List.empty_list(numba.typed.List.empty_list(node.node_type))
	for _ in range(len(nc_node)):
		result_node.append(numba.typed.List.empty_list(node.node_type))
	for _ in range(len(nc_edge)):
		result_edge.append(numba.typed.List.empty_list(node.node_type))

	# Get 2D array of qualified neighbors for neighbor criteria. Each element corresponds to 1 nc
	if(len(nc_node)>0):
		for i, nc in enumerate(nc_node):
			[result_node[i].append(n) for n in candidates if are_satisfied_node(interpretations_node, time, n, [nc])]
			
	if(len(nc_edge)>0):
		for i, nc in enumerate(nc_edge):
			[result_edge[i].append(n) for n in candidates if are_satisfied_edge(interpretations_edge, time, edge.Edge(n.get_id(), _node.get_id()), [nc])]

	# Merge all qualifed neigh into one
	for i in result_edge:
		result_node.append(i)
	return result_node

@numba.njit
def _na_update_node(interpretations, time, comp, na, ipl):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required and if update is possible - static or not
		if world.world[na[0]] != na[1] and not world.world[na[0]].is_static():
			world.update(na[0], na[1])
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
		return updated

	except:
		return False

@numba.njit
def _na_update_edge(interpretations, time, comp, na, ipl):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required
		if world.world[na[0]] != na[1]:
			world.update(na[0], na[1])
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
		return updated
	except:
		return False

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
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[time][comp]
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
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[time][comp]
			result = world.is_satisfied(na[0], na[1])
		except:
			result = False
	else:
		result = True
	return result

@numba.njit
def influence(inf_name, neigh, qualified_neigh, thresholds):
	# For each value in qualified neigh, check if it satisfies threshold. len(thresholds) = len(qualified_neigh)
	result = False
	for i in range(len(qualified_neigh)):
		if thresholds[i][1]=='number':
			if thresholds[i][0]=='greater_equal':
				result = True if len(qualified_neigh[i]) >= thresholds[i][2] else False
			elif thresholds[i][0]=='greater':
				result = True if len(qualified_neigh[i]) > thresholds[i][2] else False
			elif thresholds[i][0]=='less_equal':
				result = True if len(qualified_neigh[i]) <= thresholds[i][2] else False
			elif thresholds[i][0]=='less':
				result = True if len(qualified_neigh[i]) < thresholds[i][2] else False
			elif thresholds[i][0]=='equal':
				result = True if len(qualified_neigh[i]) == thresholds[i][2] else False
			
		elif thresholds[i][1]=='percent' and len(neigh)!=0:
			if thresholds[i][0]=='greater_equal':
				result = True if len(qualified_neigh[i])/len(neigh) >= thresholds[i][2]*0.01 else False
			elif thresholds[i][0]=='greater':
				result = True if len(qualified_neigh[i])/len(neigh)  > thresholds[i][2]*0.01 else False
			elif thresholds[i][0]=='less_equal':
				result = True if len(qualified_neigh[i])/len(neigh)  <= thresholds[i][2]*0.01 else False
			elif thresholds[i][0]=='less':
				result = True if len(qualified_neigh[i])/len(neigh)  < thresholds[i][2]*0.01 else False
			elif thresholds[i][0]=='equal':
				result = True if len(qualified_neigh[i])/len(neigh)  == thresholds[i][2]*0.01 else False
		
		if result==False:
			break
	
	# If result is true, then all qualified neighbors have passed and we can influence the node
	if result:
		if inf_name=='sft_tp':
			return interval.closed(0.7, 1)
		if inf_name=='ng_tp':
			return interval.closed(0, 0.2)
		if inf_name=='tp':
			return interval.closed(1, 1)
	else:
		return interval.closed(0,1)


@numba.njit
def check_consistent_node(interpretations, time, comp, na):
	world = interpretations[time][comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit
def check_consistent_edge(interpretations, time, comp, na):
	world = interpretations[time][comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit
def resolve_inconsistency_node(interpretations, time, comp, na, ipl, tmax, history):
	# Resolve inconsistency and set static for each timestep if history is on
	r = range(time, tmax+1) if history else range(time, time+1)
	for t in r:
		world = interpretations[t][comp]
		world.world[na[0]].set_lower_upper(0, 1)
		world.world[na[0]].set_static(True)
		for p1, p2 in ipl:
			if p1==na[0]:
				world.world[p2].set_lower_upper(0, 1)
				world.world[p2].set_static(True)

			if p2==na[0]:
				world.world[p1].set_lower_upper(0, 1)
				world.world[p1].set_static(True)


@numba.njit
def resolve_inconsistency_edge(interpretations, time, comp, na, ipl, tmax, history):
	# Resolve inconsistency and set static for each timestep if history is on
	r = range(time, tmax+1) if history else range(time, time+1)
	for t in r:
		world = interpretations[t][comp]
		world.world[na[0]].set_lower_upper(0, 1)
		world.world[na[0]].set_static(True)
		for p1, p2 in ipl:
			if p1==na[0]:
				world.world[p2].set_lower_upper(0, 1)
				world.world[p2].set_static(True)

			if p2==na[0]:
				world.world[p1].set_lower_upper(0, 1)
				world.world[p1].set_static(True)



