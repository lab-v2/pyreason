import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

import numba
import numpy as np

# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)



class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, tmax, history, ipl, reverse_graph, atom_trace):
		self._tmax = tmax
		self._graph = graph
		self._history = history
		self._ipl = ipl
		self._reverse_graph = reverse_graph
		self._atom_trace = atom_trace

		# Initialize list of tuples for rules/facts to be applied, along with all the ground atoms that fired the rule
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.ListType(node_type), numba.types.ListType(edge_type))))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.ListType(node_type))))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.boolean)))

		# Keep track of all the rules that have affeceted each node/edge at each timestep/fp operation, and all ground atoms that have affected the rules as well
		self.rule_trace_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.ListType(node_type), numba.types.ListType(edge_type))))
		self.rule_trace_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.ListType(node_type))))

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
			fp_cnt = self._apply_rules(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.nodes()), numba.typed.List(self._graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self._ipl, self.rule_trace_node, self.rule_trace_edge, self._reverse_graph, self._atom_trace)
		else:
			fp_cnt = self._apply_rules_no_history(self.interpretations_node, self.interpretations_edge, self._tmax, rules, numba.typed.List(self._graph.nodes()), numba.typed.List(self._graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self._ipl, self.rule_trace_node, self.rule_trace_edge, self._reverse_graph, self._atom_trace)
		print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit
	def _apply_rules(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, ipl, rule_trace_node, rule_trace_edge, reverse_graph, atom_trace):
		fp_cnt = 1
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
						_na_update_node(interpretations_node, t, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type))
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
						_na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, numba.typed.List.empty_list(node_type))
						interpretations_edge[t][comp].world[l].set_static(static)
					# Resolve inconsistency
					else:
						resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)

			# Deleting facts that have been applied is very inefficient

			update = True
			while update:				
				# Has the interpretation changed?
				update = False

				# Apply the rules that need to be applied at this timestep and check of inconsistencies
				# Iterate through rules to be applied, and check if any timesteps match
				# Nodes
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_node)):
					if rules_to_be_applied_node[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd, qn, qe = rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3], rules_to_be_applied_node[i][4], rules_to_be_applied_node[i][5]

						# Check for inconsistencies
						if check_consistent_node(interpretations_node, t, comp, (l, bnd)):
							update = _na_update_node(interpretations_node, t, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, qn, qe) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, t, comp, (l, bnd), ipl, tmax, True)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_node[i] = (numba.types.int8(-1), rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3], rules_to_be_applied_node[i][4], rules_to_be_applied_node[i][5])
				
				# Edges
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_edge)):
					if rules_to_be_applied_edge[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd, qn = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3], rules_to_be_applied_edge[i][4]

						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, t, comp, (l, bnd)):
							update = _na_update_edge(interpretations_edge, t, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, qn) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, t, comp, (l, bnd), ipl, tmax, True)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_edge[i] = (numba.types.int8(-1), rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3], rules_to_be_applied_edge[i][4])


				# Final step, add more rules to the list if applicable
				for rule in rules:
					if t+rule.get_delta()<=tmax:
						for n in nodes:
							if are_satisfied_node(interpretations_node, t, n, rule.get_target_criteria()) and is_satisfied_node(interpretations_node, t, n, (rule.get_target(), interval.closed(0,1))):
								a = neighbors[n]
								# Find out if rule is applicable. returns list of list of qualified nodes and qualified edges. one for each clause
								result, qualified_nodes, qualified_edges = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, atom_trace)
								if result:
									bnd = influence(rule, qualified_nodes)
									qualified_nodes = qualified_nodes if atom_trace else numba.typed.List.empty_list(node_type)
									qualified_edges = qualified_edges if atom_trace else numba.typed.List.empty_list(edge_type)
									rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd, qualified_nodes, qualified_edges))
									update = True if (rule.get_delta()==0 or update) else False
								
						# Go through all edges and check if any rules apply to them.
						# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
						for e in edges:
							if are_satisfied_edge(interpretations_edge, t, e, rule.get_target_criteria()) and is_satisfied_node(interpretations_edge, t, e, (rule.get_target(), interval.closed(0,1))):
								# Node candidates are only source and target
								a = numba.typed.List([e[0], e[1]])
								# Find out if rule is applicable. returns list of list of qualified nodes and qualified edges. one for each clause
								result, qualified_nodes, _ = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, atom_trace)
								if result:
									bnd = influence(rule, qualified_nodes)
									qualified_nodes = qualified_nodes if atom_trace else numba.typed.List.empty_list(node_type)
									rules_to_be_applied_edge.append((numba.types.int8(t+rule.get_delta()), e, rule.get_target(), bnd, qualified_nodes))
									update = True if (rule.get_delta()==0 or update) else False
					
				if update:
					fp_cnt += 1

		return fp_cnt


	@staticmethod
	@numba.njit
	def _apply_rules_no_history(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, facts_to_be_applied_node, facts_to_be_applied_edge, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl, rule_trace_node, rule_trace_edge, reverse_graph, atom_trace):
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
						_na_update_node(interpretations_node, 0, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(edge_type))
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
						_na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, numba.typed.List.empty_list(node_type))
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
						comp, l, bnd, qn, qe = rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3], rules_to_be_applied_node[i][4], rules_to_be_applied_node[i][5]

						# Check for inconsistencies
						if check_consistent_node(interpretations_node, 0, comp, (l, bnd)):
							update = _na_update_node(interpretations_node, 0, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, qn, qe) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, 0, comp, (l, bnd), ipl, tmax, False)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_node[i] = (numba.types.int8(-1), rules_to_be_applied_node[i][1], rules_to_be_applied_node[i][2], rules_to_be_applied_node[i][3], rules_to_be_applied_node[i][4], rules_to_be_applied_node[i][5])


				# Edges
				idx_to_be_removed.clear()
				for i in range(len(rules_to_be_applied_edge)):
					if rules_to_be_applied_edge[i][0]==t:
						idx_to_be_removed.append(i)
						comp, l, bnd, qn = rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3], rules_to_be_applied_edge[i][4]

						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, 0, comp, (l, bnd)):
							update = _na_update_edge(interpretations_edge, 0, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, qn) or update
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, 0, comp, (l, bnd), ipl, tmax, False)

				# Delete rules that have been applied from list by changing t to -1
				for i in idx_to_be_removed:
					rules_to_be_applied_edge[i] = (numba.types.int8(-1), rules_to_be_applied_edge[i][1], rules_to_be_applied_edge[i][2], rules_to_be_applied_edge[i][3], rules_to_be_applied_edge[i][4])


				for rule in rules:
					# Go through all nodes and check if any rules apply to them
					# Only go through everything if the rule can be applied within the given timesteps. Otherwise it's an unnecessary loop
					if t+rule.get_delta()<=tmax:
						for n in nodes:
							if are_satisfied_node(interpretations_node, 0, n, rule.get_target_criteria()) and is_satisfied_node(interpretations_node, 0, n, (rule.get_target(), interval.closed(0,1))):
								a = neighbors[n]
								result, qualified_nodes, qualified_edges = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, atom_trace)
								if result:
									bnd = influence(rule, qualified_nodes)
									qualified_nodes = qualified_nodes if atom_trace else numba.typed.List.empty_list(node_type)
									qualified_edges = qualified_edges if atom_trace else numba.typed.List.empty_list(edge_type)
									rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd, qualified_nodes, qualified_edges))
									update = True if (rule.get_delta()==0 or update) else False
						# Go through all edges and check if any rules apply to them.
						# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
						for e in edges:
							if are_satisfied_edge(interpretations_edge, 0, e, rule.get_target_criteria()) and is_satisfied_node(interpretations_edge, 0, e, (rule.get_target(), interval.closed(0,1))):
								# Node candidates are only source and target
								a = numba.typed.List([e[0], e[1]])
								# Find out if rule is applicable. returns list of list of qualified nodes and qualified edges. one for each clause
								result, qualified_nodes, _ = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, atom_trace)
								if result:
									bnd = influence(rule, qualified_nodes)
									qualified_nodes = qualified_nodes if atom_trace else numba.typed.List.empty_list(node_type)
									rules_to_be_applied_edge.append((numba.types.int8(t+rule.get_delta()), e, rule.get_target(), bnd, qualified_nodes))
									update = True if (rule.get_delta()==0 or update) else False
			
		return fp_cnt				
		


@numba.njit
def _is_rule_applicable(interpretations_node, interpretations_edge, candidates, time, target_node, neigh_criteria, thresholds, reverse_graph, atom_trace):
	# Find qualified neighbors for each clause, before going to next check if qualified neighbors satisfy the clause. If not, rule is not applicable.
	# Store qualified neighbors for each clause in a list
	qualified_nodes = numba.typed.List.empty_list(node_type)
	qualified_edges = numba.typed.List.empty_list(edge_type)
	result = True
	for i, clause in enumerate(neigh_criteria):
		r, qn, qe = _get_qualified_components(interpretations_node, interpretations_edge, candidates, time, target_node, clause, thresholds[i], reverse_graph)
		result = r and result
		if result==False:
			break
		qualified_nodes.extend(qn)
		qualified_edges.extend(qe)

	# Remove duplicates from qualified neigh. Because the same node might be responsible for activating different clauses
	if result and atom_trace:
		qualified_nodes = _remove_duplicates_qualified_nodes(qualified_nodes)
		qualified_edges = _remove_duplicates_qualified_edges(qualified_edges)

	return (result, qualified_nodes, qualified_edges)


@numba.njit
def _get_qualified_components(interpretations_node, interpretations_edge, candidates, time, target_node, clause, thresholds, reverse_graph):
	# Get qualified nodes and edges for a particular clause in a rule. 
	# Stop collecting qualified nodes/edges if clause threshold is satisfied. Only for last statement in the clause! For previous statements we have to gather all qualified nodes/edges

	# This is the number of nodes/edges which need to be satisfied for the LAST subclause to be true
	qualified_components_target = _get_qualified_components_target(len(candidates), thresholds[-1])
	# Each element in result is a set of qual neigh for a subclause
	nodes = numba.typed.List(candidates)
	edge_nodes = numba.typed.List(candidates)
	filtered_nodes = numba.typed.List.empty_list(node_type)
	filtered_edges = numba.typed.List.empty_list(edge_type)
	result = True
	last_clause_cnt = 0
	for i, sub_clause in enumerate(clause):
		filtered_nodes.clear()
		filtered_edges.clear()

		if sub_clause[0]=='node':
			for n in nodes:
				if is_satisfied_node(interpretations_node, time, n, (sub_clause[1], sub_clause[2])):
					filtered_nodes.append(n)
					# If it is the last subclause check if it satisfies the threshold values each time a new qualified neighbor is added
					if i==len(sub_clause)-1:
						last_clause_cnt += 1
						if last_clause_cnt==qualified_components_target:
							# Threshold conditions have been satisfied, so break out of loop
							break

		elif sub_clause[0]=='edge':
			for n in edge_nodes:
				if is_satisfied_edge(interpretations_edge, time, (target_node, n) if reverse_graph else (n, target_node) , (sub_clause[1], sub_clause[2])):
					filtered_edges.append((n, target_node))
					# If it is the last subclause check if it satisfies the threshold values each time a new qualified neighbor is added
					if i==len(sub_clause)-1:
						last_clause_cnt += 1
						if last_clause_cnt==qualified_components_target:
							# Threshold conditions have been satisfied, so break out of loop
							break

		elif sub_clause[0]=='reverse_edge':
			for n in edge_nodes:
				if is_satisfied_edge(interpretations_edge, time, (n, target_node) if reverse_graph else (target_node, n) , (sub_clause[1], sub_clause[2])):
					filtered_edges.append((target_node, n))
					# If it is the last subclause check if it satisfies the threshold values each time a new qualified neighbor is added
					if i==len(sub_clause)-1:
						last_clause_cnt += 1
						if last_clause_cnt==qualified_components_target:
							# Threshold conditions have been satisfied, so break out of loop
							break

		# Double check if it satisfies threshold. This is necessary for less or less_equal
		if sub_clause[0]=='node':
			result = _satisfies_threshold(len(candidates), len(filtered_nodes), thresholds[i]) and result
		elif sub_clause[0]=='edge' or sub_clause[0]=='reverse_edge':
			result = _satisfies_threshold(len(candidates), len(filtered_edges), thresholds[i]) and result

		nodes = numba.typed.List(filtered_nodes)
		edge_nodes.clear()
		for e in filtered_edges:
			edge_nodes.append(e[0]) if sub_clause[0]=='edge' else edge_nodes.append(e[1])

	return (result, filtered_nodes, filtered_edges)


@numba.njit
def _remove_duplicates_qualified_nodes(qualified_nodes):
	new_qualified_nodes = numba.typed.List.empty_list(node_type)
	[new_qualified_nodes.append(n) for n in qualified_nodes if n not in new_qualified_nodes]
	return new_qualified_nodes


@numba.njit
def _remove_duplicates_qualified_edges(qualified_edges):
	new_qualified_edges = numba.typed.List.empty_list(edge_type)
	[new_qualified_edges.append(e) for e in qualified_edges if e not in new_qualified_edges]
	return new_qualified_edges


@numba.njit
def _satisfies_threshold(num_neigh, num_qualified_component, threshold):
	# Checks if qualified neighbors satisfy threshold. This is for one subclause
	if threshold[1]=='number':
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

	elif threshold[1]=='percent':
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
def _get_qualified_components_target(num_neigh, threshold):
	if threshold[1]=='number':
		if threshold[0]=='greater_equal' or threshold[0]=='equal':
			qualified_component_target = threshold[2]
		elif threshold[0]=='greater':
			qualified_component_target = threshold[2]+1
		elif threshold[0]=='less_equal' or threshold[0]=='less':
			qualified_component_target = num_neigh


	elif threshold[1]=='percent':
		if threshold[0]=='greater_equal':
			qualified_component_target = np.ceil(threshold[2]*0.01*num_neigh)
		elif threshold[0]=='greater':
			qualified_component_target = np.ceil(threshold[2]*0.01*num_neigh + 1) 	# Give the target +1 before ceil because it could be an int
		elif threshold[0]=='less_equal' or threshold[0]=='less':
			qualified_component_target = num_neigh
		elif threshold[0]=='equal':
			qualified_component_target = np.ceil(threshold[2]*0.01*num_neigh)

	return qualified_component_target


@numba.njit
def _na_update_node(interpretations, time, comp, na, ipl, rule_trace, fp_cnt, t_cnt, qn, qe):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required and if update is possible - static or not
		if world.world[na[0]] != na[1] and not world.world[na[0]].is_static():
			world.update(na[0], na[1])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1], qn, qe))
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper), numba.typed.List([comp]), numba.typed.List.empty_list(edge_type)))
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper), numba.typed.List([comp]), numba.typed.List.empty_list(edge_type)))
		return updated

	except:
		return False

@numba.njit
def _na_update_edge(interpretations, time, comp, na, ipl, rule_trace, fp_cnt, t_cnt, qn):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[time][comp]
		# Check if update is required
		if world.world[na[0]] != na[1]:
			world.update(na[0], na[1])
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1], qn))
			updated = True

			# Update complement of predicate (if exists) based on new knowledge of predicate
			for p1, p2 in ipl:
				if p1==na[0]:
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper), numba.typed.List(['('+comp[0]+','+comp[1]+')'])))
				if p2==na[0]:
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1] = interval.closed(lower, upper)
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(lower, upper), numba.typed.List(['('+comp[0]+','+comp[1]+')'])))
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
def influence(rule, qualified_neigh):
	if rule.get_annotation_function()=='':
		return interval.closed(rule.get_bnd().lower, rule.get_bnd().upper)
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
	# Add inconsistent predicates to a list 


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



