import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

import numba

# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)


class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, tmax, history, ipl, reverse_graph):
		self._tmax = tmax
		self._graph = graph
		self._history = history
		self._ipl = ipl
		self._reverse_graph = reverse_graph

		# Initialize list of tuples for rules/facts to be applied
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.boolean)))

		# Keep track of all the rules that have affeceted each node/edge at each timestep/fp operation
		self.rule_trace_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, numba.types.int8, node_type, label.label_type, interval.interval_type)))
		self.rule_trace_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, numba.types.int8, edge_type, label.label_type, interval.interval_type)))

		# Make sure they are correct type
		if len(self.available_labels_node)==0:
			self.available_labels_node = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_node = numba.typed.List(self.available_labels_node)
		if len(self.available_labels_edge)==0:
			self.available_labels_edge = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_edge = numba.typed.List(self.available_labels_edge)

		self.interpretations_node = self._init_interpretations_node(self._tmax, numba.typed.List(self._graph.nodes()), self.available_labels_node, self.specific_node_labels, self._history)
		self.interpretations_edge = self._init_interpretations_edge(self._tmax, numba.typed.List(self._graph.edges()), self.available_labels_edge, self.specific_edge_labels, self._history)
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=numba.types.ListType(node_type))
		for n in self._graph.nodes():
			l = numba.typed.List.empty_list(node_type)
			[l.append(neigh) for neigh in self._graph.neighbors(n)]
			self.neighbors[n] = l


	@staticmethod
	@numba.njit
	def _init_interpretations_node(tmax, nodes, available_labels, specific_labels, history):
		interpretations = numba.typed.List()
		if history:
			for t in range(tmax+1):
				nas = numba.typed.Dict.empty(key_type=node_type, value_type=world.world_type)
				# General labels
				for n in nodes:
					nas[n] = world.World(available_labels)
				# Specific labels
				for l, ns in specific_labels.items():
					for n in ns:
						nas[n].world[l] = interval.closed(0.0, 1.0)
				interpretations.append(nas)
		else:
			nas = numba.typed.Dict.empty(key_type=node_type, value_type=world.world_type)
			# General labels
			for n in nodes:
				nas[n] = world.World(available_labels)
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
				nas = numba.typed.Dict.empty(key_type=edge_type, value_type=world.world_type)
				# General labels
				for e in edges:
					nas[e] = world.World(available_labels)
				# Specific labels
				for l, es in specific_labels.items():
					for e in es:
						nas[e].world[l] = interval.closed(0.0, 1.0)
				interpretations.append(nas)
		else:
			nas = numba.typed.Dict.empty(key_type=edge_type, value_type=world.world_type)
			# General labels
			for e in edges:
				nas[e] = world.World(available_labels)
			# Specific labels
			for l, es in specific_labels.items():
				for e in es:
					nas[e].world[l] = interval.closed(0.0, 1.0)
			interpretations.append(nas)

		return interpretations

	def start_fp(self, facts_node, facts_edge, rules):
		self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge)
		self._start_fp(rules)


	@staticmethod
	@numba.njit
	def _init_facts(facts_node, facts_edge, facts_to_be_applied_node, facts_to_be_applied_edge):
		for fact in facts_node:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				facts_to_be_applied_node.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))
		for fact in facts_edge:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				facts_to_be_applied_edge.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))

		
	def _start_fp(self, rules):
		if self._history:
			fp_cnt = self._apply_rules(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.nodes()), numba.typed.List(self._graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self._ipl, self.rule_trace_node, self.rule_trace_edge, self._reverse_graph)
		else:
			fp_cnt = self._apply_rules_no_history(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.nodes()), numba.typed.List(self._graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self._ipl, self.rule_trace_node, self.rule_trace_edge, self._reverse_graph)
		print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit
	def _apply_rules(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, ipl, rule_trace_node, rule_trace_edge, reverse_graph):
		fp_cnt = 0
		# List of all the indices that need to be removed if applied to interpretation
		idx_to_be_removed = numba.typed.List.empty_list(numba.types.int64)
		for t in range(tmax+1):
			print('Timestep:', t)
			# Start by applying the facts
			# Nodes
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4]
					# Check for inconsistencies
					if check_consistent_node(interpretations_node, t, comp, (l, bnd)):
						_na_update_node(interpretations_node, t, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t)
						interpretations_node[t][comp].world[l].set_static(static)
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, t, comp, (l, bnd), ipl, tmax, True)

			# Deleting facts that have been applied is very inefficient
			
			# Edges
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4]
					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, t, comp, (l, bnd)):
						_na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t)
						interpretations_edge[t][comp].world[l].set_static(static)
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)

			# Deleting facts that have been applied is very inefficient

			update = True
			while update:				
				# Has the interpretation changed?
				update = False
				fp_cnt += 1

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
							update = _na_update_node(interpretations_node, t, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, t, comp, (l, bnd), ipl, tmax, True)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_node[i] = (numba.types.int8(-1), rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3])
				
				# Edges
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_edge)):
					if rules_to_be_applied_edge[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3]

						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, t, comp, (l, bnd)):
							update = _na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_edge[i] = (numba.types.int8(-1), rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3])


				# Final step, add more rules to the list if applicable
				for rule in rules:
					if t+rule.get_delta()<=tmax:
						for n in nodes:
							if are_satisfied_node(interpretations_node, t, n, rule.get_target_criteria()):
								a = neighbors[n]
								b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], t, n, rule.get_neigh_criteria(), reverse_graph)
								bnd = influence(inf_name=rule.get_influence(), neigh=a, qualified_neigh=b, thresholds=rule.get_thresholds())
								rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
								update = True if (rule.get_delta()==0 or update) else False
						# Go through all edges and check if any rules apply to them.
						# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
						for e in edges:
							if are_satisfied_edge(interpretations_edge, t, e, rule.get_target_criteria()):
								# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
								# When making this, refer to the nodes loop section (4 lines above)
								# Then append the information to rules_to_be_applied_edge
					
								pass

		return fp_cnt


	@staticmethod
	@numba.njit
	def _apply_rules_no_history(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl, rule_trace_node, rule_trace_edge, reverse_graph):
		fp_cnt = 0
		# List of all the indices that need to be removed if applied to interpretation
		idx_to_be_removed = numba.typed.List.empty_list(numba.types.int64)
		for t in range(tmax+1):
			print('Timestep:', t)
			# Reset Interpretation at beginning of timestep
			if t>0:
				# Reset nodes (only if not static)
				# General labels
				for n in nodes:
					for l in labels_node:
						if not interpretations_node[0][n].world[l].is_static():
							interpretations_node[0][n].world[l] = interval.closed(0, 1)
				# Specific labels
				for l, ns in specific_labels_node.items():
					for n in ns:
						if not interpretations_node[0][n].world[l].is_static():
							interpretations_node[0][n].world[l] = interval.closed(0, 1)
				# Reset edges
				# General labels
				for e in edges:
					for l in labels_edge:
						if not interpretations_edge[0][e].world[l].is_static():
							interpretations_edge[0][e].world[l] = interval.closed(0, 1)
				# Specific labels
				for l, es in specific_labels_edge.items():
					for e in es:
						if not interpretations_edge[0][e].world[l].is_static():
							interpretations_edge[0][e].world[l] = interval.closed(0, 1)

			# Start by applying facts
			# Nodes
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4]
					# Check for inconsistencies (multiple facts)
					if check_consistent_node(interpretations_node, 0, comp, (l, bnd)):
						_na_update_node(interpretations_node, 0, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t)
						interpretations_node[0][comp].world[l].set_static(static)
					# Resolve inconsistency
					else:
						resolve_inconsistency_node(interpretations_node, 0, comp, (l, bnd), ipl, tmax, True)

			# Deleting facts that have been applied is very inefficient
			
			# Edges
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4]
					# Check for inconsistencies
					if check_consistent_edge(interpretations_edge, 0, comp, (l, bnd)):
						_na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t)
						interpretations_edge[0][comp].world[l].set_static(static)
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, 0, comp, (l, bnd), ipl, tmax, True)

			# Deleting facts that have been applied is very inefficient

			update = True
			while update:
				fp_cnt += 1
				# Has the interpretation changed?
				update = False

				# Apply the rules that need to be applied at this timestep
				# Nodes
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_node)):
					if rules_to_be_applied_node[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd = rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3]

						# Check for inconsistencies
						if check_consistent_node(interpretations_node, 0, comp, (l, bnd)):
							update = _na_update_node(interpretations_node, 0, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, 0, comp, (l, bnd), ipl, tmax, False)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_node[i] = (numba.types.int8(-1), rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3])


				# Edges
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_edge)):
					if rules_to_be_applied_edge[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3]

						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, 0, comp, (l, bnd)):
							update = _na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, 0, comp, (l, bnd), ipl, tmax, False)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_edge[i] = (numba.types.int8(-1), rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3])


				for rule in rules:
					# Go through all nodes and check if any rules apply to them
					# Only go through everything if the rule can be applied within the given timesteps. Otherwise it's an unnecessary loop
					if t+rule.get_delta()<=tmax:
						for n in nodes:
							if are_satisfied_node(interpretations_node, 0, n, rule.get_target_criteria()):
								a = neighbors[n]
								b = _get_qualified_neigh(interpretations_node, interpretations_edge, neighbors[n], 0, n, rule.get_neigh_criteria(), reverse_graph)
								bnd = influence(inf_name=rule.get_influence(), neigh=a, qualified_neigh=b, thresholds=rule.get_thresholds())
								rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
								update = True if (rule.get_delta()==0 or update) else False
						# Go through all edges and check if any rules apply to them.
						# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
						for e in edges:
							if are_satisfied_edge(interpretations_edge, 0, e, rule.get_target_criteria()):
								# If needed make some influence function for the edge target. As of now, edges don't have neighbors!
								# When making this, refer to the nodes loop section (4 lines above)
								# Then append the information to rules_to_be_applied_edge
								pass
			
		return fp_cnt				
		


@numba.njit
def _get_qualified_neigh(interpretations_node, interpretations_edge, candidates, time, target_node, neigh_criteria, reverse_graph):
	# List with dimensions: clause, subclause, qualified_neigh.
	result = numba.typed.List.empty_list(numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)))
	
	# Initialize 3d array
	for i in range(len(neigh_criteria)):
		result.append(numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)))
		for _ in range(len(neigh_criteria[i])):
			result[i].append(numba.typed.List.empty_list(node_type))


	# Get 3D array of qualified neighbors for neighbor criteria. Each element in result_node/edge corresponds to 1 nc, each element in that corresponds to 1 clause
	# Filter candidates in loop until last sub clause
	for i, clause in enumerate(neigh_criteria):
		neighbors = numba.typed.List(candidates)
		filtered_neighbors = numba.typed.List.empty_list(node_type)
		for j, sub_clause in enumerate(clause):
			filtered_neighbors.clear()
			if sub_clause[0]=='node':
				[filtered_neighbors.append(n) for n in neighbors if is_satisfied_node(interpretations_node, time, n, (sub_clause[1], sub_clause[2]))]
			elif sub_clause[0]=='edge':
				[filtered_neighbors.append(n) for n in neighbors if is_satisfied_edge(interpretations_edge, time, (target_node, n) if reverse_graph else (n, target_node), (sub_clause[1], sub_clause[2]))]

			neighbors = numba.typed.List(filtered_neighbors)
			result[i][j] = neighbors

	return result


@numba.njit
def _na_update_node(interpretations, time, comp, na, ipl, rule_trace, fp_cnt, t_cnt):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required and if update is possible - static or not
		if world.world[na[0]] != na[1] and not world.world[na[0]].is_static():
			world.update(na[0], na[1])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1]))
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper)))
		return updated

	except:
		return False

@numba.njit
def _na_update_edge(interpretations, time, comp, na, ipl, rule_trace, fp_cnt, t_cnt):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required
		if world.world[na[0]] != na[1]:
			world.update(na[0], na[1])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1]))
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper)))
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
	# Start off with true. If anything is false, this becomes false, otherwise stays true
	prev_result = True
	for i in range(len(qualified_neigh)):
		for j in range(len(qualified_neigh[i])):
			if thresholds[i][j][1]=='number':
				if thresholds[i][j][0]=='greater_equal':
					result = True if len(qualified_neigh[i][j]) >= thresholds[i][j][2] else False
				elif thresholds[i][j][0]=='greater':
					result = True if len(qualified_neigh[i][j]) > thresholds[i][j][2] else False
				elif thresholds[i][j][0]=='less_equal':
					result = True if len(qualified_neigh[i][j]) <= thresholds[i][j][2] else False
				elif thresholds[i][j][0]=='less':
					result = True if len(qualified_neigh[i][j]) < thresholds[i][j][2] else False
				elif thresholds[i][j][0]=='equal':
					result = True if len(qualified_neigh[i][j]) == thresholds[i][j][2] else False

			elif thresholds[i][j][1]=='percent':
				if len(neigh)==0:
					result = False
				elif thresholds[i][j][0]=='greater_equal':
					result = True if len(qualified_neigh[i][j])/len(neigh) >= thresholds[i][j][2]*0.01 else False
				elif thresholds[i][j][0]=='greater':
					result = True if len(qualified_neigh[i][j])/len(neigh) > thresholds[i][j][2]*0.01 else False
				elif thresholds[i][j][0]=='less_equal':
					result = True if len(qualified_neigh[i][j])/len(neigh) <= thresholds[i][j][2]*0.01 else False
				elif thresholds[i][j][0]=='less':
					result = True if len(qualified_neigh[i][j])/len(neigh) < thresholds[i][j][2]*0.01 else False
				elif thresholds[i][j][0]=='equal':
					result = True if len(qualified_neigh[i][j])/len(neigh) == thresholds[i][j][2]*0.01 else False
			
			# AND condition for each sub clause and clause
			prev_result = result and prev_result

	# If result is true, then all qualified neighbors have passed and we can influence the node
	if prev_result:
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
		world.world[na[0]] = interval.closed(0, 1, static=True)
		for p1, p2 in ipl:
			if p1==na[0]:
				world.world[p2] = interval.closed(0, 1, static=True)

			if p2==na[0]:
				world.world[p1] = interval.closed(0, 1, static=True)


@numba.njit
def resolve_inconsistency_edge(interpretations, time, comp, na, ipl, tmax, history):
	# Resolve inconsistency and set static for each timestep if history is on
	r = range(time, tmax+1) if history else range(time, time+1)
	for t in r:
		world = interpretations[t][comp]
		world.world[na[0]] = interval.closed(0, 1, static=True)
		for p1, p2 in ipl:
			if p1==na[0]:
				world.world[p2] = interval.closed(0, 1, static=True)

			if p2==na[0]:
				world.world[p1] = interval.closed(0, 1, static=True)



