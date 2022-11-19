import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.annotation_functions.annotation_functions as ann_fn

import numba
import numpy as np

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
								result, annotations, qualified_nodes, qualified_edges = _is_rule_applicable(interpretations_node, interpretations_edge, a, t, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
								if result:
									bnd = influence(rule, annotations)
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
								result, annotations, qualified_nodes, _ = _is_rule_applicable(interpretations_node, interpretations_edge, a, t, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
								if result:
									bnd = influence(rule, annotations)
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
								result, annotations, qualified_nodes, qualified_edges = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
								if result:
									bnd = influence(rule, annotations)
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
								result, annotations, qualified_nodes, _ = _is_rule_applicable(interpretations_node, interpretations_edge, a, 0, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_subset(), rule.get_label())
								if result:
									bnd = influence(rule, annotations)
									qualified_nodes = qualified_nodes if atom_trace else numba.typed.List.empty_list(node_type)
									rules_to_be_applied_edge.append((numba.types.int8(t+rule.get_delta()), e, rule.get_target(), bnd, qualified_nodes))
									update = True if (rule.get_delta()==0 or update) else False
			
				if update:
					fp_cnt += 1

		return fp_cnt				
		


@numba.njit
def _is_rule_applicable(interpretations_node, interpretations_edge, candidates, time, target_node, neigh_criteria, thresholds, reverse_graph, ann_fn_subset, ann_fn_label):
	# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
	# Keep track of all the edges that are qualified
	# If its a node clause update (x1 or x2 etc.) qualified neighbors, if its an edge clause update the qualified neighbors for the source and target (x1, x2)
	# First gather all the qualified nodes for each clause
	subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=subsets_value_type)
	qualified_edges = numba.typed.Dict.empty(key_type=edge_type, value_type=qualified_edges_value_type)
	for i, clause in enumerate(neigh_criteria):
		if clause[0]=='node':
			subset = candidates if clause[1][0] not in subsets else subsets[clause[1][0]][0]
			subsets[clause[1][0]] = (get_qualified_components_node_clause(interpretations_node, subset, time, clause), thresholds[i])
		elif clause[0]=='edge':
			subset_source = candidates if clause[1][0] not in subsets else subsets[clause[1][0]][0]
			subset_target = candidates if clause[1][1] not in subsets else subsets[clause[1][1]][0]
			# If target is used, then use the target node
			if clause[1][0]=='target':
				subset_source = numba.typed.List([target_node])
			elif clause[1][1]=='target':
				subset_target = numba.typed.List([target_node])
				 
			qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, time, clause, reverse_graph)
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
	if result and ann_fn_subset[0]!='':
		if ann_fn_subset[0]==ann_fn_subset[1]:
			# Then this is a node subset
			final_subset_node = _get_final_qualified_nodes(subsets[ann_fn_subset[0]][0], subsets[ann_fn_subset[0]][1], len(candidates))
			# Now get the final annotations to pass into the annotation function
			for node in final_subset_node:
				annotations.append(interpretations_node[time][node].world[ann_fn_label])
		else:
			# This is an edge subset
			final_subset_edge = _get_final_qualified_edges(qualified_edges[ann_fn_subset][0], qualified_edges[ann_fn_subset][1], len(candidates))
			# Now get the final annotations to pass into the annotation function
			for edge in final_subset_edge:
				annotations.append(interpretations_edge[time][edge].world[ann_fn_label])

	return (result, annotations, final_subset_node, final_subset_edge)



@numba.njit
def get_qualified_components_node_clause(interpretations_node, candidates, time, clause):
	# Get all the qualified neighbors for a particular clause
	qualified_nodes = numba.typed.List.empty_list(node_type)
	for n in candidates:
		if is_satisfied_node(interpretations_node, time, n, (clause[2], clause[3])):
			qualified_nodes.append(n)

	return qualified_nodes


@numba.njit
def get_qualified_components_edge_clause(interpretations_edge, candidates_source, candidates_target, time, clause, reverse_graph):
	# Get all the qualified sources and targets for a particular clause
	qualified_nodes_source = numba.typed.List.empty_list(node_type)
	qualified_nodes_target = numba.typed.List.empty_list(node_type)
	for source in candidates_source:
		for target in candidates_target:
			edge = (source, target) if not reverse_graph else (target, source)
			if is_satisfied_edge(interpretations_edge, time, edge, (clause[2], clause[3])):
				qualified_nodes_source.append(source)
				qualified_nodes_target.append(target)

	return (qualified_nodes_source, qualified_nodes_target)


@numba.njit
def _get_final_qualified_nodes(subset, threshold, total_num_neigh):
	# Here subset is a list of nodes
	if threshold[1][1]=='available':
		num_neigh = len(subset)
	elif threshold[1][1]=='total':
		num_neigh =  total_num_neigh
	target = _get_qualified_components_target(num_neigh, threshold)

	final_subset = numba.typed.List.empty_list(node_type)
	for i in range(target):
		if i<len(subset):
			final_subset.append(subset[i])

	return final_subset


@numba.njit
def _get_final_qualified_edges(subset, threshold, total_num_neigh):
	# Here subset is a list of edges
	if threshold[1][1]=='available':
		num_neigh = len(subset)
	elif threshold[1][1]=='total':
		num_neigh =  total_num_neigh
	target = _get_qualified_components_target(num_neigh, threshold)

	final_subset = numba.typed.List.empty_list(edge_type)
	for i in range(target):
		if i<len(subset):
			final_subset.append(subset[i])

	return final_subset
	


@numba.njit
def _satisfies_threshold(num_neigh, num_qualified_component, threshold):
	# Checks if qualified neighbors satisfy threshold. This is for one subclause
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
			prev_bnd = world.world[na[0]]
			world.update(na[0], na[1])
			if world.world[na[0]]==prev_bnd:
				updated = False
			else:
				updated = True
				rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1], qn, qe))


			# Update complement of predicate (if exists) based on new knowledge of predicate
			if updated:
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
			prev_bnd = world.world[na[0]]
			world.update(na[0], na[1])
			if world.world[na[0]]==prev_bnd:
				updated = False
			else:
				updated = True
				rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], na[1], qn))

			# Update complement of predicate (if exists) based on new knowledge of predicate
			if updated:
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
def influence(rule, annotations):
	func_name = rule.get_annotation_function()
	if func_name=='':
		return interval.closed(rule.get_bnd().lower, rule.get_bnd().upper)
	elif func_name=='average':
		return ann_fn.average(annotations)
	elif func_name=='minimum':
		return ann_fn.minimum(annotations)
	elif func_name=='maximum':
		return ann_fn.maximum(annotations)


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



