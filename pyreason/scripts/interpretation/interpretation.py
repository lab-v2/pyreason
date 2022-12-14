import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.annotation_functions.annotation_functions as ann_fn

import numba

# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)

# Type for storing list of qualified nodes as well as the threshold that goes with it
subsets_value_type = numba.types.Tuple((numba.types.ListType(node_type), numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64))))
qualified_edges_value_type = numba.types.Tuple((numba.types.ListType(edge_type), numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64))))



class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, tmax, ipl, reverse_graph, atom_trace, convergence_threshold, convergence_bound_threshold):
		self._tmax = tmax
		self._graph = graph
		self._ipl = ipl
		self._reverse_graph = reverse_graph
		self._atom_trace = atom_trace
		self.time = 0

		# Set up convergence criteria
		if convergence_bound_threshold==-1 and convergence_threshold==-1:
			self._convergence_mode = 'perfect_convergence'
			self._convergence_delta = 0
		elif convergence_bound_threshold==-1:
			self._convergence_mode = 'delta_interpretation'
			self._convergence_delta = convergence_threshold
		else:
			self._convergence_mode = 'delta_bound'
			self._convergence_delta = convergence_bound_threshold

		# Initialize list of tuples for rules/facts to be applied, along with all the ground atoms that fired the rule. One to One correspondence between rules_to_be_applied_node and rules_to_be_applied_node_trace if atom_trace is true
		self.rules_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(edge_type))))
		self.rules_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type),)))
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.boolean)))

		# Keep track of all the rules that have affeceted each node/edge at each timestep/fp operation, and all ground atoms that have affected the rules as well
		self.rule_trace_node_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(edge_type))))
		self.rule_trace_edge_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type),)))
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

		self.interpretations_node = self._init_interpretations_node(numba.typed.List(self._graph.nodes()), self.available_labels_node, self.specific_node_labels)
		self.interpretations_edge = self._init_interpretations_edge(numba.typed.List(self._graph.edges()), self.available_labels_edge, self.specific_edge_labels)
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=numba.types.ListType(node_type))
		for n in self._graph.nodes():
			l = numba.typed.List.empty_list(node_type)
			[l.append(neigh) for neigh in self._graph.neighbors(n)]
			self.neighbors[n] = l


	@staticmethod
	@numba.njit
	def _init_interpretations_node(nodes, available_labels, specific_labels):
		interpretations = numba.typed.Dict.empty(key_type=node_type, value_type=world.world_type)
		# General labels
		for n in nodes:
			interpretations[n] = world.World(available_labels)
		# Specific labels
		for l, ns in specific_labels.items():
			for n in ns:
				interpretations[n].world[l] = interval.closed(0.0, 1.0)

		return interpretations

	
	@staticmethod
	@numba.njit
	def _init_interpretations_edge(edges, available_labels, specific_labels):
		interpretations = numba.typed.Dict.empty(key_type=edge_type, value_type=world.world_type)
		# General labels
		for e in edges:
			interpretations[e] = world.World(available_labels)
		# Specific labels
		for l, es in specific_labels.items():
			for e in es:
				interpretations[e].world[l] = interval.closed(0.0, 1.0)

		return interpretations

	def start_fp(self, facts_node, facts_edge, rules):
		max_facts_time = self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge)
		self._start_fp(rules, max_facts_time)


	@staticmethod
	@numba.njit
	def _init_facts(facts_node, facts_edge, facts_to_be_applied_node, facts_to_be_applied_edge):
		max_time = 0
		for fact in facts_node:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				facts_to_be_applied_node.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))
		for fact in facts_edge:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				facts_to_be_applied_edge.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))
		return max_time

		
	def _start_fp(self, rules, max_facts_time):
		fp_cnt, t = self._apply_rules(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.nodes()), numba.typed.List(self._graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.rules_to_be_applied_node_trace, self.rules_to_be_applied_edge_trace, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self._ipl, self.rule_trace_node, self.rule_trace_edge, self.rule_trace_node_atoms, self.rule_trace_edge_atoms, self._reverse_graph, self._atom_trace, max_facts_time, self._convergence_mode, self._convergence_delta)
		self.time = t
		print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit
	def _apply_rules(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace, facts_to_be_applied_node, facts_to_be_applied_edge, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl, rule_trace_node, rule_trace_edge, rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace, max_facts_time, convergence_mode, convergence_delta):
		fp_cnt = 0
		for t in range(tmax+1):
			print('Timestep:', t)
			# Reset Interpretation at beginning of timestep
			if t>0:
				# Reset nodes (only if not static)
				# General labels
				for n in nodes:
					for l in labels_node:
						if not interpretations_node[n].world[l].is_static():
							interpretations_node[n].world[l].reset()
				# Specific labels
				for l, ns in specific_labels_node.items():
					for n in ns:
						if not interpretations_node[n].world[l].is_static():
							interpretations_node[n].world[l].reset()				
				# Reset edges
				# General labels
				for e in edges:
					for l in labels_edge:
						if not interpretations_edge[e].world[l].is_static():
							interpretations_edge[e].world[l].reset()
				# Specific labels
				for l, es in specific_labels_edge.items():
					for e in es:
						if not interpretations_edge[e].world[l].is_static():
							interpretations_edge[e].world[l].reset()

			# Convergence parameters
			changes_cnt = 0
			bound_delta = 0
			max_rules_time = 0
			update = False

			# Start by applying facts
			# Nodes
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4]
					# Check if bnd is static. Then no need to update, just add to rule trace, and add ipl complement to rule trace as well
					if interpretations_node[comp].world[l].is_static():
						rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, l, interpretations_node[comp].world[l]))
						if atom_trace:
							rule_trace_node_atoms.append((numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type)))
						for p1, p2 in ipl:
							if p1==l:
								rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p2, interpretations_node[comp].world[p2]))
								if atom_trace:
									rule_trace_node_atoms.append((numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type)))
							elif p2==l:
								rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p1, interpretations_node[comp].world[p1]))
								if atom_trace:
									rule_trace_node_atoms.append((numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type)))
							
					else:
						# Check for inconsistencies (multiple facts)
						if check_consistent_node(interpretations_node, comp, (l, bnd)):
							u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode)
							if atom_trace:
								_update_rule_trace_node(rule_trace_node_atoms, numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type))

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl)
					if static:
						facts_to_be_applied_node[i] = (numba.types.int8(facts_to_be_applied_node[i][0]+1), comp, l, bnd, static)

			# Deleting facts that have been applied is very inefficient
			
			# Edges
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4]
					# Check if bnd is static. Then no need to update, just add to rule trace, and add ipl complement to rule trace as well
					if interpretations_edge[comp].world[l].is_static():
						rule_trace_edge.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, l, interpretations_edge[comp].world[l]))
						if atom_trace:
							rule_trace_edge_atoms.append((numba.typed.List.empty_list(node_type),))
						for p1, p2 in ipl:
							if p1==l:
								rule_trace_edge.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p2, interpretations_edge[comp].world[p2]))
								if atom_trace:
									rule_trace_edge_atoms.append((numba.typed.List.empty_list(node_type),))
							elif p2==l:
								rule_trace_edge.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p1, interpretations_edge[comp].world[p1]))
								if atom_trace:
									rule_trace_edge_atoms.append((numba.typed.List.empty_list(node_type),))
					else:
						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
							u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode)
							if atom_trace:
								_update_rule_trace_edge(rule_trace_edge_atoms, numba.typed.List.empty_list(node_type))

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl)
					if static:
						facts_to_be_applied_edge[i] = (numba.types.int8(facts_to_be_applied_edge[i][0]+1), comp, l, bnd, static)

			# Deleting facts that have been applied is very inefficient

			in_loop = True
			while in_loop:
				# This will become true only if delta_t = 0 for some rule, otherwise we go to the next timestep
				in_loop = False

				# Apply the rules that need to be applied at this timestep
				# Nodes
				for idx, i in enumerate(rules_to_be_applied_node):
					if i[0]==t:
						comp, l, bnd = i[1], i[2], i[3]

						# Check for inconsistencies
						if check_consistent_node(interpretations_node, comp, (l, bnd)):
							u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, False, convergence_mode)
							if atom_trace:
								qn, qe = rules_to_be_applied_node_trace[idx]
								_update_rule_trace_node(rule_trace_node_atoms, qn, qe)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl)

						# Delete rules that have been applied from list by changing t to -1
						rules_to_be_applied_node[idx] = (numba.types.int8(-1), comp, l, bnd)


				# Edges
				for idx, i in enumerate(rules_to_be_applied_edge):
					if i[0]==t:
						comp, l, bnd = i[1], i[2], i[3]

						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
							u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode)
							if atom_trace:
								qn, = rules_to_be_applied_edge_trace[idx]
								_update_rule_trace_edge(rule_trace_edge_atoms, qn)
							
							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl)

						# Delete rules that have been applied from list by changing t to -1
						rules_to_be_applied_edge[idx] = (numba.types.int8(-1), comp, l, bnd)


				# Fixed point
				if update:
					fp_cnt += 1
					for rule in rules:
						# Go through all nodes and check if any rules apply to them
						# Only go through everything if the rule can be applied within the given timesteps. Otherwise it's an unnecessary loop
						if t+rule.get_delta()<=tmax:
							for n in nodes:
								if are_satisfied_node(interpretations_node, n, rule.get_target_criteria()) and is_satisfied_node(interpretations_node, n, (rule.get_target(), interval.closed(0,1))):
									a = neighbors[n]
									result, annotations, qualified_nodes, qualified_edges = _is_rule_applicable(interpretations_node, interpretations_edge, a, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
									if result and not interpretations_node[n].world[rule.get_target()].is_static():
										bnd = influence(rule, annotations)
										max_rules_time = max(max_rules_time, t+rule.get_delta())
										rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
										if atom_trace:
											rules_to_be_applied_node_trace.append((qualified_nodes, qualified_edges))
										in_loop = True if rule.get_delta()==0 else False
							# Go through all edges and check if any rules apply to them.
							# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
							for e in edges:
								if are_satisfied_edge(interpretations_edge, e, rule.get_target_criteria()) and is_satisfied_node(interpretations_edge, e, (rule.get_target(), interval.closed(0,1))):
									# Node candidates are only source and target
									a = numba.typed.List([e[0], e[1]])
									# Find out if rule is applicable. returns list of list of qualified nodes and qualified edges. one for each clause
									result, annotations, qualified_nodes, _ = _is_rule_applicable(interpretations_node, interpretations_edge, a, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
									if result and not interpretations_edge[e].world[rule.get_target()].is_static():
										bnd = influence(rule, annotations)
										max_rules_time = max(max_rules_time, t+rule.get_delta())
										rules_to_be_applied_edge.append((numba.types.int8(t+rule.get_delta()), e, rule.get_target(), bnd))
										if atom_trace:
											rules_to_be_applied_edge_trace.append((qualified_nodes,))
										in_loop = True if rule.get_delta()==0 else False
				
			# Check for convergence after each timestep (perfect convergence or convergence specified by user)
			# Check number of changed interpretations or max bound change
			# User specified convergence
			if convergence_mode=='delta_interpretation':
				if changes_cnt <= convergence_delta:
					print(f'\nConverged at time: {t} with {int(changes_cnt)} changes from the previous interpretation')
					break
			elif convergence_mode=='delta_bound':
				if bound_delta <= convergence_delta:
					print(f'\nConverged at time: {t} with {float_to_str(bound_delta)} as the maximum bound change from the previous interpretation')
					break
			# Perfect convergence
			# Make sure there are no rules to be applied, and no facts that will be applied in the future. We do this by checking the max time any rule/fact is applicable
			# If no more rules/facts to be applied
			elif convergence_mode=='perfect_convergence':
				if (t>=max_facts_time and t>=max_rules_time) or (t>=max_facts_time and changes_cnt==0):
					if changes_cnt==0:
						print(f'\nConverged at time: {t}')
					else:
						print(f'\nMax timestep reached at {t}. {int(changes_cnt)} changes to interpretaion pending')	
					
					break

		return fp_cnt, t	
		


@numba.njit
def _is_rule_applicable(interpretations_node, interpretations_edge, candidates, target_node, neigh_criteria, thresholds, reverse_graph, ann_fn_subset, ann_fn_label):
	# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
	# Keep track of all the edges that are qualified
	# If its a node clause update (x1 or x2 etc.) qualified neighbors, if its an edge clause update the qualified neighbors for the source and target (x1, x2)
	# First gather all the qualified nodes for each clause
	subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=subsets_value_type)
	qualified_edges = numba.typed.Dict.empty(key_type=edge_type, value_type=qualified_edges_value_type)
	for i, clause in enumerate(neigh_criteria):
		if clause[0]=='node':
			subset = candidates if clause[1][0] not in subsets else subsets[clause[1][0]][0]
			subsets[clause[1][0]] = (get_qualified_components_node_clause(interpretations_node, subset, clause), thresholds[i])
		elif clause[0]=='edge':
			subset_source = candidates if clause[1][0] not in subsets else subsets[clause[1][0]][0]
			subset_target = candidates if clause[1][1] not in subsets else subsets[clause[1][1]][0]
			# If target is used, then use the target node
			if clause[1][0]=='target':
				subset_source = numba.typed.List([target_node])
			elif clause[1][1]=='target':
				subset_target = numba.typed.List([target_node])

			qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause, reverse_graph)
			subsets[clause[1][0]] = (qe[0], thresholds[i])
			subsets[clause[1][1]] = (qe[1], thresholds[i])
			qualified_edges[clause[1]] = (numba.typed.List(zip(subsets[clause[1][0]][0], subsets[clause[1][1]][0])), thresholds[i])

	# Now check if the thresholds are satisfied for each clause
	result = True
	for i, clause in enumerate(neigh_criteria):
		if clause[0]=='node':
			if thresholds[i][1][1]=='total':
				neigh_len = len(candidates)
			elif thresholds[i][1][1]=='available':
				neigh_len = len(subsets[clause[1][0]][0])
		
		# Same as above, keep for now in case changes are needed
		elif clause[0]=='edge':
			if thresholds[i][1][1]=='total':
				neigh_len = len(candidates)
			elif thresholds[i][1][1]=='available':
				neigh_len = len(subsets[clause[1][0]][0])

		qualified_neigh_len = len(subsets[clause[1][0]][0])
		result = _satisfies_threshold(neigh_len, qualified_neigh_len, thresholds[i]) and result


		if result==False:
			break

	# Now select the correct subset that is given in the rule and prepare it for final processing according to the threshold
	annotations = numba.typed.List.empty_list(interval.interval_type)
	final_subset_node = numba.typed.List.empty_list(node_type)
	final_subset_edge = numba.typed.List.empty_list(edge_type)
	# If all thresholds have been satisfied (result) AND the annotation function is a function (not just a fixed bound)
	if result and ann_fn_subset[0]!='':
		if ann_fn_subset[0]==ann_fn_subset[1]:
			# Then this is a node subset
			# Now get the final annotations to pass into the annotation function
			for node in subsets[ann_fn_subset[0]][0]:
				annotations.append(interpretations_node[node].world[ann_fn_label])
		else:
			# This is an edge subset
			# Now get the final annotations to pass into the annotation function
			for edge in qualified_edges[ann_fn_subset][0]:
				annotations.append(interpretations_edge[edge].world[ann_fn_label])

	return (result, annotations, final_subset_node, final_subset_edge)



@numba.njit
def get_qualified_components_node_clause(interpretations_node, candidates, clause):
	# Get all the qualified neighbors for a particular clause
	qualified_nodes = numba.typed.List.empty_list(node_type)
	for n in candidates:
		if is_satisfied_node(interpretations_node, n, (clause[2], clause[3])):
			qualified_nodes.append(n)

	return qualified_nodes


@numba.njit
def get_qualified_components_edge_clause(interpretations_edge, candidates_source, candidates_target, clause, reverse_graph):
	# Get all the qualified sources and targets for a particular clause
	qualified_nodes_source = numba.typed.List.empty_list(node_type)
	qualified_nodes_target = numba.typed.List.empty_list(node_type)
	for source in candidates_source:
		for target in candidates_target:
			edge = (source, target) if not reverse_graph else (target, source)
			if is_satisfied_edge(interpretations_edge, edge, (clause[2], clause[3])):
				qualified_nodes_source.append(source)
				qualified_nodes_target.append(target)

	return (qualified_nodes_source, qualified_nodes_target)
	


@numba.njit
def _satisfies_threshold(num_neigh, num_qualified_component, threshold):
	# Checks if qualified neighbors satisfy threshold. This is for one clause
	if threshold[1][0]=='number':
		if threshold[0]=='greater_equal':
			result = True if num_qualified_component >= threshold[2] else False
		elif threshold[0]=='greater':
			result = True if num_qualified_component > threshold[2] else False
		elif threshold[0]=='less_equal':
			result = True if num_qualified_component <= threshold[2] else False
		elif threshold[0]=='less':
			result = True if num_qualified_component < threshold[2] else False
		elif threshold[0]=='equal':
			result = True if num_qualified_component == threshold[2] else False

	elif threshold[1][0]=='percent':
		if num_neigh==0:
			result = False
		elif threshold[0]=='greater_equal':
			result = True if num_qualified_component/num_neigh >= threshold[2]*0.01 else False
		elif threshold[0]=='greater':
			result = True if num_qualified_component/num_neigh > threshold[2]*0.01 else False
		elif threshold[0]=='less_equal':
			result = True if num_qualified_component/num_neigh <= threshold[2]*0.01 else False
		elif threshold[0]=='less':
			result = True if num_qualified_component/num_neigh < threshold[2]*0.01 else False
		elif threshold[0]=='equal':
			result = True if num_qualified_component/num_neigh == threshold[2]*0.01 else False

	return result


@numba.njit
def _update_node(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Check if update is necessary with previous bnd
		prev_bnd = world.world[l].copy()
		world.update(l, bnd)
		world.world[l].set_static(static)
		if world.world[l]!=prev_bnd:
			updated = True
			updated_bnds.append(world.world[l])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, l, world.world[l].copy()))

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
					world.world[p1].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p1])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper)))
		
		# Gather convergence data
		change = 0
		if updated:
			# Find out if it has changed from previous interp
			current_bnd = world.world[l]
			prev_t_bnd = interval.closed(world.world[l].prev_lower, world.world[l].prev_upper)
			if current_bnd != prev_t_bnd:
				if convergence_mode=='delta_bound':
					for i in updated_bnds:
						lower_delta = abs(i.lower-prev_t_bnd.lower)
						upper_delta = abs(i.upper-prev_t_bnd.upper)
						max_delta = max(lower_delta, upper_delta)
						change = max(change, max_delta)
				else:
					change = 1 + ip_update_cnt

		return (updated, change)

	except:
		return (False, 0)

@numba.njit
def _update_rule_trace_node(rule_trace, qn, qe):
	rule_trace.append((qn, qe))
	

@numba.njit
def _update_edge(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Check if update is necessary with previous bnd
		prev_bnd = world.world[l].copy()
		world.update(l, bnd)
		world.world[l].set_static(static)
		if world.world[l]!=prev_bnd:
			updated = True
			updated_bnds.append(world.world[l])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, l, world.world[l].copy()))

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
					world.world[p1].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper)))
	
		# Gather convergence data
		change = 0
		if updated:
			# Find out if it has changed from previous interp
			current_bnd = world.world[l]
			prev_t_bnd = interval.closed(world.world[l].prev_lower, world.world[l].prev_upper)
			if current_bnd != prev_t_bnd:
				if convergence_mode=='delta_bound':
					for i in updated_bnds:
						lower_delta = abs(i.lower-prev_t_bnd.lower)
						upper_delta = abs(i.upper-prev_t_bnd.upper)
						max_delta = max(lower_delta, upper_delta)
						change = max(change, max_delta)
				else:
					change = 1 + ip_update_cnt
		
		return (updated, change)
	except:
		return (False, 0)

@numba.njit
def _update_rule_trace_edge(rule_trace, qn):
	rule_trace.append((qn,))
	

@numba.njit
def are_satisfied_node(interpretations, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_node(interpretations, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_node(interpretations, comp, na):
	result = False
	if (not (na[0] is None or na[1] is None)):
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[comp]
			result = world.is_satisfied(na[0], na[1])
		except:
			result = False
	else:
		result = True
	return result

@numba.njit
def are_satisfied_edge(interpretations, comp, nas):
	result = True
	if len(nas)>0:
		for (label, interval) in nas:
			result = result and is_satisfied_edge(interpretations, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_edge(interpretations, comp, na):
	result = False
	if (not (na[0] is None or na[1] is None)):
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[comp]
			result = world.is_satisfied(na[0], na[1])
		except:
			result = False
	else:
		result = True
	return result

@numba.njit
def influence(rule, annotations):
	func_name = rule.get_annotation_function()
	if func_name=='':
		return interval.closed(rule.get_bnd().lower, rule.get_bnd().upper)
	elif func_name=='average':
		return ann_fn.average(annotations)
	elif func_name=='average_lower':
		return ann_fn.average_lower(annotations)
	elif func_name=='minimum':
		return ann_fn.minimum(annotations)
	elif func_name=='maximum':
		return ann_fn.maximum(annotations)


@numba.njit
def check_consistent_node(interpretations, comp, na):
	world = interpretations[comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit
def check_consistent_edge(interpretations, comp, na):
	world = interpretations[comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit
def resolve_inconsistency_node(interpretations, comp, na, ipl):
	# Resolve inconsistency and set static
	world = interpretations[comp]
	world.world[na[0]].set_lower_upper(0, 1)
	world.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			world.world[p2].set_lower_upper(0, 1)
			world.world[p2].set_static(True)

		if p2==na[0]:
			world.world[p1].set_lower_upper(0, 1)
			world.world[p1].set_static(True)
	# Add inconsistent predicates to a list 


@numba.njit
def resolve_inconsistency_edge(interpretations, comp, na, ipl):
	# Resolve inconsistency and set static
	world = interpretations[comp]
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
def float_to_str(value):
	number = int(value)
	decimal = int(value % 1 * 1000)
	float_str = f'{number}.{decimal}'
	return float_str
