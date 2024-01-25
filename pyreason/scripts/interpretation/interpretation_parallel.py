import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.interpretation.interpretation_dict import InterpretationDict

import numba
from numba import objmode, prange


# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)

# Type for storing list of qualified nodes/edges
list_of_nodes = numba.types.ListType(node_type)
list_of_edges = numba.types.ListType(edge_type)

# Type for facts to be applied
facts_to_be_applied_node_type = numba.types.Tuple((numba.types.uint16, node_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean))
facts_to_be_applied_edge_type = numba.types.Tuple((numba.types.uint16, edge_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean))

# Type for returning list of applicable rules for a certain rule
# node/edge, annotations, qualified nodes, qualified edges, edges to be added
node_applicable_rule_type = numba.types.Tuple((
	node_type,
	numba.types.ListType(numba.types.ListType(interval.interval_type)),
	numba.types.ListType(numba.types.ListType(node_type)),
	numba.types.ListType(numba.types.ListType(edge_type)),
	numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type))
))

edge_applicable_rule_type = numba.types.Tuple((
	edge_type,
	numba.types.ListType(numba.types.ListType(interval.interval_type)),
	numba.types.ListType(numba.types.ListType(node_type)),
	numba.types.ListType(numba.types.ListType(edge_type)),
	numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type))
))


class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, ipl, annotation_functions, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, canonical, inconsistency_check, store_interpretation_changes, update_mode):
		self.graph = graph
		self.ipl = ipl
		self.annotation_functions = annotation_functions
		self.reverse_graph = reverse_graph
		self.atom_trace = atom_trace
		self.save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace
		self.canonical = canonical
		self.inconsistency_check = inconsistency_check
		self.store_interpretation_changes = store_interpretation_changes

		# For reasoning and reasoning again (contains previous time and previous fp operation cnt)
		self.time = 0
		self.prev_reasoning_data = numba.typed.List([0, 0])

		# Initialize list of tuples for rules/facts to be applied, along with all the ground atoms that fired the rule. One to One correspondence between rules_to_be_applied_node and rules_to_be_applied_node_trace if atom_trace is true
		self.rules_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), numba.types.string)))
		self.rules_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), numba.types.string)))
		self.facts_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.string)
		self.facts_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.string)
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, node_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, edge_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(facts_to_be_applied_node_type)
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(facts_to_be_applied_edge_type)
		self.edges_to_be_added_node_rule = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type)))
		self.edges_to_be_added_edge_rule = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type)))

		# Keep track of all the rules that have affected each node/edge at each timestep/fp operation, and all ground atoms that have affected the rules as well. Keep track of previous bounds and name of the rule/fact here
		self.rule_trace_node_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), interval.interval_type, numba.types.string)))
		self.rule_trace_edge_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), interval.interval_type, numba.types.string)))
		self.rule_trace_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, numba.types.uint16, node_type, label.label_type, interval.interval_type)))
		self.rule_trace_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, numba.types.uint16, edge_type, label.label_type, interval.interval_type)))

		# Nodes and edges of the graph
		self.nodes = numba.typed.List(self.graph.nodes())
		self.edges = numba.typed.List(self.graph.edges())

		# Make sure they are correct type
		if len(self.available_labels_node)==0:
			self.available_labels_node = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_node = numba.typed.List(self.available_labels_node)
		if len(self.available_labels_edge)==0:
			self.available_labels_edge = numba.typed.List.empty_list(label.label_type)
		else:
			self.available_labels_edge = numba.typed.List(self.available_labels_edge)

		self.interpretations_node = self._init_interpretations_node(numba.typed.List(self.graph.nodes()), self.available_labels_node, self.specific_node_labels)
		self.interpretations_edge = self._init_interpretations_edge(numba.typed.List(self.graph.edges()), self.available_labels_edge, self.specific_edge_labels)

		# Setup graph neighbors and reverse neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=numba.types.ListType(node_type))
		for n in self.graph.nodes():
			l = numba.typed.List.empty_list(node_type)
			[l.append(neigh) for neigh in self.graph.neighbors(n)]
			self.neighbors[n] = l

		self.reverse_neighbors = self._init_reverse_neighbors(self.neighbors)

	@staticmethod
	@numba.njit(cache=False)
	def _init_reverse_neighbors(neighbors):
		reverse_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=list_of_nodes)
		for n, neighbor_nodes in neighbors.items():
			for neighbor_node in neighbor_nodes:
				if neighbor_node in reverse_neighbors and n not in reverse_neighbors[neighbor_node]:
					reverse_neighbors[neighbor_node].append(n)
				else:
					reverse_neighbors[neighbor_node] = numba.typed.List([n])
			# This makes sure each node has a value
			if n not in reverse_neighbors:
				reverse_neighbors[n] = numba.typed.List.empty_list(node_type)

		return reverse_neighbors

	@staticmethod
	@numba.njit(cache=False)
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
	@numba.njit(cache=False)
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

	@staticmethod
	@numba.njit(cache=False)
	def _init_convergence(convergence_bound_threshold, convergence_threshold):
		if convergence_bound_threshold==-1 and convergence_threshold==-1:
			convergence_mode = 'perfect_convergence'
			convergence_delta = 0
		elif convergence_bound_threshold==-1:
			convergence_mode = 'delta_interpretation'
			convergence_delta = convergence_threshold
		else:
			convergence_mode = 'delta_bound'
			convergence_delta = convergence_bound_threshold
		return convergence_mode, convergence_delta

	def start_fp(self, tmax, facts_node, facts_edge, rules, verbose, convergence_threshold, convergence_bound_threshold, again=False):
		self.tmax = tmax
		self._convergence_mode, self._convergence_delta = self._init_convergence(convergence_bound_threshold, convergence_threshold)
		max_facts_time = self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.atom_trace)
		self._start_fp(rules, max_facts_time, verbose, again)

	@staticmethod
	@numba.njit(cache=False)
	def _init_facts(facts_node, facts_edge, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, atom_trace):
		max_time = 0
		for fact in facts_node:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				name = fact.get_name()
				graph_attribute = True if name=='graph-attribute-fact' else False
				facts_to_be_applied_node.append((numba.types.uint16(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static, graph_attribute))
				if atom_trace:
					facts_to_be_applied_node_trace.append(fact.get_name())
		for fact in facts_edge:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				name = fact.get_name()
				graph_attribute = True if name=='graph-attribute-fact' else False
				facts_to_be_applied_edge.append((numba.types.uint16(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static, graph_attribute))
				if atom_trace:
					facts_to_be_applied_edge_trace.append(fact.get_name())
		return max_time

	def _start_fp(self, rules, max_facts_time, verbose, again):
		fp_cnt, t = self.reason(self.interpretations_node, self.interpretations_edge, self.tmax, self.prev_reasoning_data, rules, self.nodes, self.edges, self.neighbors, self.reverse_neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.edges_to_be_added_node_rule, self.edges_to_be_added_edge_rule, self.rules_to_be_applied_node_trace, self.rules_to_be_applied_edge_trace, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.ipl, self.rule_trace_node, self.rule_trace_edge, self.rule_trace_node_atoms, self.rule_trace_edge_atoms, self.reverse_graph, self.atom_trace, self.save_graph_attributes_to_rule_trace, self.canonical, self.inconsistency_check, self.store_interpretation_changes, max_facts_time, self.annotation_functions, self._convergence_mode, self._convergence_delta, verbose, again)
		self.time = t - 1
		# If we need to reason again, store the next timestep to start from
		self.prev_reasoning_data[0] = t
		self.prev_reasoning_data[1] = fp_cnt
		if verbose:
			print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit(cache=False)
	def reason(interpretations_node, interpretations_edge, tmax, prev_reasoning_data, rules, nodes, edges, neighbors, reverse_neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, edges_to_be_added_node_rule, edges_to_be_added_edge_rule, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, ipl, rule_trace_node, rule_trace_edge, rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, canonical, inconsistency_check, store_interpretation_changes, max_facts_time, annotation_functions, convergence_mode, convergence_delta, verbose, again):
		t = prev_reasoning_data[0]
		fp_cnt = prev_reasoning_data[1]
		max_rules_time = 0
		timestep_loop = True
		facts_to_be_applied_node_new = numba.typed.List.empty_list(facts_to_be_applied_node_type)
		facts_to_be_applied_edge_new = numba.typed.List.empty_list(facts_to_be_applied_edge_type)
		rules_to_remove_idx = numba.typed.List.empty_list(numba.types.int64)
		while timestep_loop:
			if t==tmax:
				timestep_loop = False
			if verbose:
				with objmode():
					print('Timestep:', t, flush=True)
			# Reset Interpretation at beginning of timestep if non-canonical
			if t>0 and not canonical:
				# Reset nodes (only if not static)
				for n in nodes:
					w = interpretations_node[n].world
					for l in w:
						if not w[l].is_static():
							w[l].reset()

				# Reset edges (only if not static)
				for e in edges:
					w = interpretations_edge[e].world
					for l in w:
						if not w[l].is_static():
							w[l].reset()

			# Convergence parameters
			changes_cnt = 0
			bound_delta = 0
			update = False

			# Parameters for immediate rules
			immediate_node_rule_fire = False
			immediate_edge_rule_fire = False
			immediate_rule_applied = False
			# When delta_t = 0, we don't want to check the same rule with the same node/edge after coming back to the fp operator
			nodes_to_skip = numba.typed.Dict.empty(key_type=numba.types.int64, value_type=list_of_nodes)
			edges_to_skip = numba.typed.Dict.empty(key_type=numba.types.int64, value_type=list_of_edges)
			# Initialize the above
			for i in range(len(rules)):
				nodes_to_skip[i] = numba.typed.List.empty_list(node_type)
				edges_to_skip[i] = numba.typed.List.empty_list(edge_type)

			# Start by applying facts
			# Nodes
			facts_to_be_applied_node_new.clear()
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4], facts_to_be_applied_node[i][5]
					# Check if bnd is static. Then no need to update, just add to rule trace, check if graph attribute and add ipl complement to rule trace as well
					if l in interpretations_node[comp].world and interpretations_node[comp].world[l].is_static():
						# Check if we should even store any of the changes to the rule trace etc.
						# Inverse of this is: if not save_graph_attributes_to_rule_trace and graph_attribute
						if (save_graph_attributes_to_rule_trace or not graph_attribute) and store_interpretation_changes:
							rule_trace_node.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, l, bnd))
							if atom_trace:
								_update_rule_trace(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), bnd, facts_to_be_applied_node_trace[i])
							for p1, p2 in ipl:
								if p1==l:
									rule_trace_node.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, p2, interpretations_node[comp].world[p2]))
									if atom_trace:
										_update_rule_trace(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_node[comp].world[p2], facts_to_be_applied_node_trace[i])
								elif p2==l:
									rule_trace_node.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, p1, interpretations_node[comp].world[p1]))
									if atom_trace:
										_update_rule_trace(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_node[comp].world[p1], facts_to_be_applied_node_trace[i])

					else:
						# Check for inconsistencies (multiple facts)
						if check_consistent_node(interpretations_node, comp, (l, bnd)):
							mode = 'graph-attribute-fact' if graph_attribute else 'fact'
							u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, i, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode=mode)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency if necessary otherwise override bounds
						else:
							if inconsistency_check:
								resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_node, rule_trace_node_atoms, store_interpretation_changes)
							else:
								mode = 'graph-attribute-fact' if graph_attribute else 'fact'
								u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, i, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode=mode, override=True)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes

					if static:
						facts_to_be_applied_node_new.append((numba.types.uint16(facts_to_be_applied_node[i][0]+1), comp, l, bnd, static, graph_attribute))

				# If time doesn't match, fact to be applied later
				else:
					facts_to_be_applied_node_new.append(facts_to_be_applied_node[i])

			# Update list of facts with ones that have not been applied yet (delete applied facts)
			facts_to_be_applied_node[:] = facts_to_be_applied_node_new.copy()
			facts_to_be_applied_node_new.clear()

			# Edges
			facts_to_be_applied_edge_new.clear()
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4], facts_to_be_applied_edge[i][5]
					# Check if bnd is static. Then no need to update, just add to rule trace, check if graph attribute, and add ipl complement to rule trace as well
					if l in interpretations_edge[comp].world and interpretations_edge[comp].world[l].is_static():
						# Inverse of this is: if not save_graph_attributes_to_rule_trace and graph_attribute
						if (save_graph_attributes_to_rule_trace or not graph_attribute) and store_interpretation_changes:
							rule_trace_edge.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, l, interpretations_edge[comp].world[l]))
							if atom_trace:
								_update_rule_trace(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), bnd, facts_to_be_applied_edge_trace[i])
							for p1, p2 in ipl:
								if p1==l:
									rule_trace_edge.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, p2, interpretations_edge[comp].world[p2]))
									if atom_trace:
										_update_rule_trace(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_edge[comp].world[p2], facts_to_be_applied_edge_trace[i])
								elif p2==l:
									rule_trace_edge.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, p1, interpretations_edge[comp].world[p1]))
									if atom_trace:
										_update_rule_trace(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_edge[comp].world[p1], facts_to_be_applied_edge_trace[i])
					else:
						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
							mode = 'graph-attribute-fact' if graph_attribute else 'fact'
							u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, i, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode=mode)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							if inconsistency_check:
								resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms, store_interpretation_changes)
							else:
								mode = 'graph-attribute-fact' if graph_attribute else 'fact'
								u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, i, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode=mode, override=True)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes

					if static:
						facts_to_be_applied_edge_new.append((numba.types.uint16(facts_to_be_applied_edge[i][0]+1), comp, l, bnd, static, graph_attribute))

				# Time doesn't match, fact to be applied later
				else:
					facts_to_be_applied_edge_new.append(facts_to_be_applied_edge[i])

			# Update list of facts with ones that have not been applied yet (delete applied facts)
			facts_to_be_applied_edge[:] = facts_to_be_applied_edge_new.copy()
			facts_to_be_applied_edge_new.clear()

			in_loop = True
			while in_loop:
				# This will become true only if delta_t = 0 for some rule, otherwise we go to the next timestep
				in_loop = False

				# Apply the rules that need to be applied at this timestep
				# Nodes
				rules_to_remove_idx.clear()
				for idx, i in enumerate(rules_to_be_applied_node):
					# If we are coming here from an immediate rule firing with delta_t=0 we have to apply that one rule. Which was just added to the list to_be_applied
					if immediate_node_rule_fire and rules_to_be_applied_node[-1][4]:
						i = rules_to_be_applied_node[-1]
						idx = len(rules_to_be_applied_node) - 1

					if i[0]==t:
						comp, l, bnd, immediate, set_static = i[1], i[2], i[3], i[4], i[5]
						sources, targets, edge_l = edges_to_be_added_node_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

									update = u or update

									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes
								# Resolve inconsistency
								else:
									if inconsistency_check:
										resolve_inconsistency_edge(interpretations_edge, e, (edge_l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms, store_interpretation_changes)
									else:
										u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

										update = u or update

										# Update convergence params
										if convergence_mode=='delta_bound':
											bound_delta = max(bound_delta, changes)
										else:
											changes_cnt += changes
						else:
							# Check for inconsistencies
							if check_consistent_node(interpretations_node, comp, (l, bnd)):
								u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode='rule')

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes
							# Resolve inconsistency
							else:
								if inconsistency_check:
									resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_node, rule_trace_node_atoms, store_interpretation_changes)
								else:
									u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode='rule', override=True)

									update = u or update
									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes

						# Delete rules that have been applied from list by adding index to list
						rules_to_remove_idx.append(idx)

						# Break out of the apply rules loop if a rule is immediate. Then we go to the fp operator and check for other applicable rules then come back
						if immediate:
							# If delta_t=0 we want to apply one rule and go back to the fp operator
							# If delta_t>0 we want to come back here and apply the rest of the rules
							if immediate_edge_rule_fire:
								break
							elif not immediate_edge_rule_fire and u:
								immediate_rule_applied = True
								break

				# Remove from rules to be applied and edges to be applied lists after coming out from loop
				rules_to_be_applied_node[:] = numba.typed.List([rules_to_be_applied_node[i] for i in range(len(rules_to_be_applied_node)) if i not in rules_to_remove_idx])
				edges_to_be_added_node_rule[:] = numba.typed.List([edges_to_be_added_node_rule[i] for i in range(len(edges_to_be_added_node_rule)) if i not in rules_to_remove_idx])
				if atom_trace:
					rules_to_be_applied_node_trace[:] = numba.typed.List([rules_to_be_applied_node_trace[i] for i in range(len(rules_to_be_applied_node_trace)) if i not in rules_to_remove_idx])

				# Edges
				rules_to_remove_idx.clear()
				for idx, i in enumerate(rules_to_be_applied_edge):
					# If we broke from above loop to apply more rules, then break from here
					if immediate_rule_applied and not immediate_edge_rule_fire:
						break
					# If we are coming here from an immediate rule firing with delta_t=0 we have to apply that one rule. Which was just added to the list to_be_applied
					if immediate_edge_rule_fire and rules_to_be_applied_edge[-1][4]:
						i = rules_to_be_applied_edge[-1]
						idx = len(rules_to_be_applied_edge) - 1

					if i[0]==t:
						comp, l, bnd, immediate, set_static = i[1], i[2], i[3], i[4], i[5]
						sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

									update = u or update

									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes
								# Resolve inconsistency
								else:
									if inconsistency_check:
										resolve_inconsistency_edge(interpretations_edge, e, (edge_l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms, store_interpretation_changes)
									else:
										u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

										update = u or update

										# Update convergence params
										if convergence_mode=='delta_bound':
											bound_delta = max(bound_delta, changes)
										else:
											changes_cnt += changes

						else:
							# Check for inconsistencies
							if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
								u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes
							# Resolve inconsistency
							else:
								if inconsistency_check:
									resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms, store_interpretation_changes)
								else:
									u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

									update = u or update
									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes

						# Delete rules that have been applied from list by adding the index to list
						rules_to_remove_idx.append(idx)

						# Break out of the apply rules loop if a rule is immediate. Then we go to the fp operator and check for other applicable rules then come back
						if immediate:
							# If t=0 we want to apply one rule and go back to the fp operator
							# If t>0 we want to come back here and apply the rest of the rules
							if immediate_edge_rule_fire:
								break
							elif not immediate_edge_rule_fire and u:
								immediate_rule_applied = True
								break

				# Remove from rules to be applied and edges to be applied lists after coming out from loop
				rules_to_be_applied_edge[:] = numba.typed.List([rules_to_be_applied_edge[i] for i in range(len(rules_to_be_applied_edge)) if i not in rules_to_remove_idx])
				edges_to_be_added_edge_rule[:] = numba.typed.List([edges_to_be_added_edge_rule[i] for i in range(len(edges_to_be_added_edge_rule)) if i not in rules_to_remove_idx])
				if atom_trace:
					rules_to_be_applied_edge_trace[:] = numba.typed.List([rules_to_be_applied_edge_trace[i] for i in range(len(rules_to_be_applied_edge_trace)) if i not in rules_to_remove_idx])

				# Fixed point
				# if update or immediate_node_rule_fire or immediate_edge_rule_fire or immediate_rule_applied:
				if update:
					# Increase fp operator count only if not an immediate rule
					if not (immediate_node_rule_fire or immediate_edge_rule_fire):
						fp_cnt += 1

					for i in range(len(rules)):
						rule = rules[i]
						immediate_rule = rule.is_immediate_rule()
						immediate_node_rule_fire = False
						immediate_edge_rule_fire = False

						# Only go through if the rule can be applied within the given timesteps, or we're running until convergence
						delta_t = rule.get_delta()
						if t + delta_t <= tmax or tmax == -1 or again:
							applicable_node_rules = _ground_node_rule(rule, interpretations_node, interpretations_edge, nodes, neighbors, reverse_neighbors, atom_trace, reverse_graph, nodes_to_skip[i])
							applicable_edge_rules = _ground_edge_rule(rule, interpretations_node, interpretations_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace, reverse_graph, edges_to_skip[i])

							# Loop through applicable rules and add them to the rules to be applied for later or next fp operation
							for applicable_rule in applicable_node_rules:
								n, annotations, qualified_nodes, qualified_edges, edges_to_add = applicable_rule
								# If there is an edge to add or the predicate doesn't exist or the interpretation is not static
								if len(edges_to_add[0]) > 0 or rule.get_target() not in interpretations_node[n].world or not interpretations_node[n].world[rule.get_target()].is_static():
									bnd = annotate(annotation_functions, rule, annotations, rule.get_weights())
									bnd = interval.closed(bnd[0], bnd[1])
									max_rules_time = max(max_rules_time, t + delta_t)
									edges_to_be_added_node_rule.append(edges_to_add)
									rules_to_be_applied_node.append((numba.types.uint16(t + delta_t), n, rule.get_target(), bnd, immediate_rule, rule.is_static_rule()))
									if atom_trace:
										rules_to_be_applied_node_trace.append((qualified_nodes, qualified_edges, rule.get_name()))

									# We apply a rule on a node/edge only once in each timestep to prevent it from being added to the to_be_added list continuously (this will improve performance
									nodes_to_skip[i].append(n)

									# Handle loop parameters for the next (maybe) fp operation
									# If it is a t=0 rule or an immediate rule we want to go back for another fp operation to check for new rules that may fire
									# Next fp operation we will skip this rule on this node because anyway there won't be an update
									if delta_t == 0:
										in_loop = True
										update = False
									if immediate_rule and delta_t == 0:
										# immediate_rule_fire becomes True because we still need to check for more eligible rules, we're not done.
										in_loop = True
										update = True
										immediate_node_rule_fire = True
										break

							# Break, apply immediate rule then come back to check for more applicable rules
							if immediate_node_rule_fire:
								break

							for applicable_rule in applicable_edge_rules:
								e, annotations, qualified_nodes, qualified_edges, edges_to_add = applicable_rule
								# If there is an edge to add or the predicate doesn't exist or the interpretation is not static
								if len(edges_to_add[0]) > 0 or rule.get_target() not in interpretations_edge[e].world or not interpretations_edge[e].world[rule.get_target()].is_static():
									bnd = annotate(annotation_functions, rule, annotations, rule.get_weights())
									bnd = interval.closed(bnd[0], bnd[1])
									max_rules_time = max(max_rules_time, t+delta_t)
									edges_to_be_added_edge_rule.append(edges_to_add)
									rules_to_be_applied_edge.append((numba.types.uint16(t+delta_t), e, rule.get_target(), bnd, immediate_rule, rule.is_static_rule()))
									if atom_trace:
										rules_to_be_applied_edge_trace.append((qualified_nodes, qualified_edges, rule.get_name()))

									# We apply a rule on a node/edge only once in each timestep to prevent it from being added to the to_be_added list continuously (this will improve performance
									edges_to_skip[i].append(e)

									# Handle loop parameters for the next (maybe) fp operation
									# If it is a t=0 rule or an immediate rule we want to go back for another fp operation to check for new rules that may fire
									# Next fp operation we will skip this rule on this node because anyway there won't be an update
									if delta_t == 0:
										in_loop = True
										update = False
									if immediate_rule and delta_t == 0:
										# immediate_rule_fire becomes True because we still need to check for more eligible rules, we're not done.
										in_loop = True
										update = True
										immediate_edge_rule_fire = True
										break

							# Break, apply immediate rule then come back to check for more applicable rules
							if immediate_edge_rule_fire:
								break

					# Go through all the rules and go back to applying the rules if we came here because of an immediate rule where delta_t>0
					if immediate_rule_applied and not (immediate_node_rule_fire or immediate_edge_rule_fire):
						immediate_rule_applied = False
						in_loop = True
						update = False
						continue

			# Check for convergence after each timestep (perfect convergence or convergence specified by user)
			# Check number of changed interpretations or max bound change
			# User specified convergence
			if convergence_mode=='delta_interpretation':
				if changes_cnt <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {int(changes_cnt)} changes from the previous interpretation')
					# Be consistent with time returned when we don't converge
					t += 1
					break
			elif convergence_mode=='delta_bound':
				if bound_delta <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {float_to_str(bound_delta)} as the maximum bound change from the previous interpretation')
					# Be consistent with time returned when we don't converge
					t += 1
					break
			# Perfect convergence
			# Make sure there are no rules to be applied, and no facts that will be applied in the future. We do this by checking the max time any rule/fact is applicable
			# If no more rules/facts to be applied
			elif convergence_mode=='perfect_convergence':
				if t>=max_facts_time and t>=max_rules_time:
					if verbose:
						print(f'\nConverged at time: {t}')
					# Be consistent with time returned when we don't converge
					t += 1
					break

			# Increment t
			t += 1

		return fp_cnt, t

	def add_edge(self, edge, l):
		# This function is useful for pyreason gym, called externally
		_add_edge(edge[0], edge[1], self.neighbors, self.reverse_neighbors, self.nodes, self.edges, l, self.interpretations_node, self.interpretations_edge)

	def delete_edge(self, edge):
		# This function is useful for pyreason gym, called externally
		_delete_edge(edge, self.neighbors, self.reverse_neighbors, self.edges, self.interpretations_edge)

	def get_interpretation_dict(self):
		# This function can be called externally to retrieve a dict of the interpretation values
		# Only values in the rule trace will be added

		# Initialize interpretations for each time and node and edge
		interpretations = {}
		for t in range(self.tmax+1):
			interpretations[t] = {}
			for node in self.nodes:
				interpretations[t][node] = InterpretationDict()
			for edge in self.edges:
				interpretations[t][edge] = InterpretationDict()

		# Update interpretation nodes
		for change in self.rule_trace_node:
			time, _, node, l, bnd = change
			interpretations[time][node][l._value] = (bnd.lower, bnd.upper)

			# If canonical, update all following timesteps as well
			if self. canonical:
				for t in range(time+1, self.tmax+1):
					interpretations[t][node][l._value] = (bnd.lower, bnd.upper)

		# Update interpretation edges
		for change in self.rule_trace_edge:
			time, _, edge, l, bnd, = change
			interpretations[time][edge][l._value] = (bnd.lower, bnd.upper)

			# If canonical, update all following timesteps as well
			if self. canonical:
				for t in range(time+1, self.tmax+1):
					interpretations[t][edge][l._value] = (bnd.lower, bnd.upper)

		return interpretations


@numba.njit(cache=False, parallel=True)
def _ground_node_rule(rule, interpretations_node, interpretations_edge, nodes, neighbors, reverse_neighbors, atom_trace, reverse_graph, nodes_to_skip):
	# Extract rule params
	rule_type = rule.get_type()
	clauses = rule.get_clauses()
	thresholds = rule.get_thresholds()
	ann_fn = rule.get_annotation_function()
	rule_edges = rule.get_edges()

	# We return a list of tuples which specify the target nodes/edges that have made the rule body true
	applicable_rules = numba.typed.List.empty_list(node_applicable_rule_type)

	# Return empty list if rule is not node rule and if we are not inferring edges
	if rule_type != 'node' and rule_edges[0] == '':
		return applicable_rules

	# Steps
	# 1. Loop through all nodes and evaluate each clause with that node and check the truth with the thresholds
	# 2. Inside the clause loop it may be necessary to loop through all nodes/edges while grounding the variables
	# 3. If the clause is true add the qualified nodes and qualified edges to the atom trace, if on. Break otherwise
	# 4. After going through all clauses, add to the annotations list all the annotations of the specified subset. These will be passed to the annotation function
	# 5. Finally, if there are any edges to be added, place them in the list

	for piter in prange(len(nodes)):
		target_node = nodes[piter]
		if target_node in nodes_to_skip:
			continue
		# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
		# Keep track of qualified nodes and qualified edges
		# If it's a node clause update (x1 or x2 etc.) qualified neighbors, if it's an edge clause update the qualified neighbors for the source and target (x1, x2)
		subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
		qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
		qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
		annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
		edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), rule_edges[-1])

		satisfaction = True
		for i, clause in enumerate(clauses):
			# Unpack clause variables
			clause_type = clause[0]
			clause_label = clause[1]
			clause_variables = clause[2]
			clause_bnd = clause[3]
			clause_operator = clause[4]

			# Unpack thresholds
			# This value is total/available
			threshold_quantifier_type = thresholds[i][1][1]

			# This is a node clause
			# The groundings for node clauses are either the target node, neighbors of the target node, or an existing subset of nodes
			if clause_type == 'node':
				clause_var_1 = clause_variables[0]
				subset = get_node_rule_node_clause_subset(clause_var_1, target_node, subsets, neighbors)

				subsets[clause_var_1] = get_qualified_components_node_clause(interpretations_node, subset, clause_label, clause_bnd)

				if atom_trace:
					qualified_nodes.append(numba.typed.List(subsets[clause_var_1]))
					qualified_edges.append(numba.typed.List.empty_list(edge_type))

				# Add annotations if necessary
				if ann_fn != '':
					a = numba.typed.List.empty_list(interval.interval_type)
					for qn in subsets[clause_var_1]:
						a.append(interpretations_node[qn].world[clause_label])
					annotations.append(a)

			# This is an edge clause
			elif clause_type == 'edge':
				clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
				subset_source, subset_target = get_node_rule_edge_clause_subset(clause_var_1, clause_var_2, target_node, subsets, neighbors, reverse_neighbors, nodes)

				# Get qualified edges
				qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause_label, clause_bnd, reverse_graph)
				subsets[clause_var_1] = qe[0]
				subsets[clause_var_2] = qe[1]

				if atom_trace:
					qualified_nodes.append(numba.typed.List.empty_list(node_type))
					qualified_edges.append(numba.typed.List(zip(subsets[clause_var_1], subsets[clause_var_2])))

				# Add annotations if necessary
				if ann_fn != '':
					a = numba.typed.List.empty_list(interval.interval_type)
					for qe in numba.typed.List(zip(subsets[clause_var_1], subsets[clause_var_2])):
						a.append(interpretations_edge[qe].world[clause_label])
					annotations.append(a)
			else:
				# This is a comparison clause
				# Make sure there is at least one ground atom such that pred-num(x) : [1,1] or pred-num(x,y) : [1,1]
				# Remember that the predicate in the clause will not contain the "-num" where num is some number.
				# We have to remove that manually while checking
				# Steps:
				# 1. get qualified nodes/edges as well as number associated for first predicate
				# 2. get qualified nodes/edges as well as number associated for second predicate
				# 3. if there's no number in steps 1 or 2 return false clause
				# 4. do comparison with each qualified component from step 1 with each qualified component in step 2

				# It's a node comparison
				if len(clause_variables) == 2:
					clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
					subset_1 = get_node_rule_node_clause_subset(clause_var_1, target_node, subsets, neighbors)
					subset_2 = get_node_rule_node_clause_subset(clause_var_2, target_node, subsets, neighbors)

					# 1, 2
					qualified_nodes_for_comparison_1, numbers_1 = get_qualified_components_node_comparison_clause(interpretations_node, subset_1, clause_label, clause_bnd)
					qualified_nodes_for_comparison_2, numbers_2 = get_qualified_components_node_comparison_clause(interpretations_node, subset_2, clause_label, clause_bnd)

				# It's an edge comparison
				elif len(clause_variables) == 4:
					clause_var_1_source, clause_var_1_target, clause_var_2_source, clause_var_2_target = clause_variables[0], clause_variables[1], clause_variables[2], clause_variables[3]
					subset_1_source, subset_1_target = get_node_rule_edge_clause_subset(clause_var_1_source, clause_var_1_target, target_node, subsets, neighbors, reverse_neighbors, nodes)
					subset_2_source, subset_2_target = get_node_rule_edge_clause_subset(clause_var_2_source, clause_var_2_target, target_node, subsets, neighbors, reverse_neighbors, nodes)

					# 1, 2
					qualified_nodes_for_comparison_1_source, qualified_nodes_for_comparison_1_target, numbers_1 = get_qualified_components_edge_comparison_clause(interpretations_edge, subset_1_source, subset_1_target, clause_label, clause_bnd, reverse_graph)
					qualified_nodes_for_comparison_2_source, qualified_nodes_for_comparison_2_target, numbers_2 = get_qualified_components_edge_comparison_clause(interpretations_edge, subset_2_source, subset_2_target, clause_label, clause_bnd, reverse_graph)

			# Check if thresholds are satisfied
			# If it's a comparison clause we just need to check if the numbers list is not empty (no threshold support)
			if clause_type == 'comparison':
				if len(numbers_1) == 0 or len(numbers_2) == 0:
					satisfaction = False
				# Node comparison. Compare stage
				elif len(clause_variables) == 2:
					satisfaction, qualified_nodes_1, qualified_nodes_2 = compare_numbers_node_predicate(numbers_1, numbers_2, clause_operator, qualified_nodes_for_comparison_1, qualified_nodes_for_comparison_2)

					# Update subsets with final qualified nodes
					subsets[clause_var_1] = qualified_nodes_1
					subsets[clause_var_2] = qualified_nodes_2
					qualified_comparison_nodes = numba.typed.List(qualified_nodes_1)
					qualified_comparison_nodes.extend(qualified_nodes_2)

					if atom_trace:
						qualified_nodes.append(qualified_comparison_nodes)
						qualified_edges.append(numba.typed.List.empty_list(edge_type))

					# Add annotations for comparison clause. For now, we don't distinguish between LHS and RHS annotations
					if ann_fn != '':
						a = numba.typed.List.empty_list(interval.interval_type)
						for qn in qualified_comparison_nodes:
							a.append(interval.closed(1, 1))
						annotations.append(a)
				# Edge comparison. Compare stage
				else:
					satisfaction, qualified_nodes_1_source, qualified_nodes_1_target, qualified_nodes_2_source, qualified_nodes_2_target = compare_numbers_edge_predicate(numbers_1, numbers_2, clause_operator,
																																										  qualified_nodes_for_comparison_1_source,
																																										  qualified_nodes_for_comparison_1_target,
																																										  qualified_nodes_for_comparison_2_source,
																																										  qualified_nodes_for_comparison_2_target)
					# Update subsets with final qualified nodes
					subsets[clause_var_1_source] = qualified_nodes_1_source
					subsets[clause_var_1_target] = qualified_nodes_1_target
					subsets[clause_var_2_source] = qualified_nodes_2_source
					subsets[clause_var_2_target] = qualified_nodes_2_target

					qualified_comparison_nodes_1 = numba.typed.List(zip(qualified_nodes_1_source, qualified_nodes_1_target))
					qualified_comparison_nodes_2 = numba.typed.List(zip(qualified_nodes_2_source, qualified_nodes_2_target))
					qualified_comparison_nodes = numba.typed.List(qualified_comparison_nodes_1)
					qualified_comparison_nodes.extend(qualified_comparison_nodes_2)

					if atom_trace:
						qualified_nodes.append(numba.typed.List.empty_list(node_type))
						qualified_edges.append(qualified_comparison_nodes)

					# Add annotations for comparison clause. For now, we don't distinguish between LHS and RHS annotations
					if ann_fn != '':
						a = numba.typed.List.empty_list(interval.interval_type)
						for qe in qualified_comparison_nodes:
							a.append(interval.closed(1, 1))
						annotations.append(a)

			# Non comparison clause
			else:
				if threshold_quantifier_type == 'total':
					if clause_type == 'node':
						neigh_len = len(subset)
					else:
						neigh_len = sum([len(l) for l in subset_target])

				# Available is all neighbors that have a particular label with bound inside [0,1]
				elif threshold_quantifier_type == 'available':
					if clause_type == 'node':
						neigh_len = len(get_qualified_components_node_clause(interpretations_node, subset, clause_label, interval.closed(0,1)))
					else:
						neigh_len = len(get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause_label, interval.closed(0,1), reverse_graph)[0])

				qualified_neigh_len = len(subsets[clause_var_1])
				satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, thresholds[i]) and satisfaction

			# Exit loop if even one clause is not satisfied
			if not satisfaction:
				break

		if satisfaction:
			# Collect edges to be added
			source, target, _ = rule_edges

			# Edges to be added
			if source != '' and target != '':
				# Check if edge nodes are target
				if source == '__target':
					edges_to_be_added[0].append(target_node)
				elif source in subsets:
					edges_to_be_added[0].extend(subsets[source])
				else:
					edges_to_be_added[0].append(source)

				if target == '__target':
					edges_to_be_added[1].append(target_node)
				elif target in subsets:
					edges_to_be_added[1].extend(subsets[target])
				else:
					edges_to_be_added[1].append(target)

			# node/edge, annotations, qualified nodes, qualified edges, edges to be added
			applicable_rules.append((target_node, annotations, qualified_nodes, qualified_edges, edges_to_be_added))

	return applicable_rules


@numba.njit(cache=False, parallel=True)
def _ground_edge_rule(rule, interpretations_node, interpretations_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace, reverse_graph, edges_to_skip):
	# Extract rule params
	rule_type = rule.get_type()
	clauses = rule.get_clauses()
	thresholds = rule.get_thresholds()
	ann_fn = rule.get_annotation_function()
	rule_edges = rule.get_edges()

	# We return a list of tuples which specify the target nodes/edges that have made the rule body true
	applicable_rules = numba.typed.List.empty_list(edge_applicable_rule_type)

	# Return empty list if rule is not node rule
	if rule_type != 'edge':
		return applicable_rules

	# Steps
	# 1. Loop through all nodes and evaluate each clause with that node and check the truth with the thresholds
	# 2. Inside the clause loop it may be necessary to loop through all nodes/edges while grounding the variables
	# 3. If the clause is true add the qualified nodes and qualified edges to the atom trace, if on. Break otherwise
	# 4. After going through all clauses, add to the annotations list all the annotations of the specified subset. These will be passed to the annotation function
	# 5. Finally, if there are any edges to be added, place them in the list

	for piter in prange(len(edges)):
		target_edge = edges[piter]
		if target_edge in edges_to_skip:
			continue
		# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
		# Keep track of qualified nodes and qualified edges
		# If it's a node clause update (x1 or x2 etc.) qualified neighbors, if it's an edge clause update the qualified neighbors for the source and target (x1, x2)
		subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
		qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
		qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
		annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
		edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), rule_edges[-1])

		satisfaction = True
		for i, clause in enumerate(clauses):
			# Unpack clause variables
			clause_type = clause[0]
			clause_label = clause[1]
			clause_variables = clause[2]
			clause_bnd = clause[3]
			clause_operator = clause[4]

			# Unpack thresholds
			# This value is total/available
			threshold_quantifier_type = thresholds[i][1][1]

			# This is a node clause
			# The groundings for node clauses are either the source, target, neighbors of the source node, or an existing subset of nodes
			if clause_type == 'node':
				clause_var_1 = clause_variables[0]
				subset = get_edge_rule_node_clause_subset(clause_var_1, target_edge, subsets, neighbors)

				subsets[clause_var_1] = get_qualified_components_node_clause(interpretations_node, subset, clause_label, clause_bnd)
				if atom_trace:
					qualified_nodes.append(numba.typed.List(subsets[clause_var_1]))
					qualified_edges.append(numba.typed.List.empty_list(edge_type))

				# Add annotations if necessary
				if ann_fn != '':
					a = numba.typed.List.empty_list(interval.interval_type)
					for qn in subsets[clause_var_1]:
						a.append(interpretations_node[qn].world[clause_label])
					annotations.append(a)

			# This is an edge clause
			elif clause_type == 'edge':
				clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
				subset_source, subset_target = get_edge_rule_edge_clause_subset(clause_var_1, clause_var_2, target_edge, subsets, neighbors, reverse_neighbors, nodes)

				# Get qualified edges
				qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause_label, clause_bnd, reverse_graph)
				subsets[clause_var_1] = qe[0]
				subsets[clause_var_2] = qe[1]

				if atom_trace:
					qualified_nodes.append(numba.typed.List.empty_list(node_type))
					qualified_edges.append(numba.typed.List(zip(subsets[clause_var_1], subsets[clause_var_2])))

				# Add annotations if necessary
				if ann_fn != '':
					a = numba.typed.List.empty_list(interval.interval_type)
					for qe in numba.typed.List(zip(subsets[clause_var_1], subsets[clause_var_2])):
						a.append(interpretations_edge[qe].world[clause_label])
					annotations.append(a)

			else:
				# This is a comparison clause
				# Make sure there is at least one ground atom such that pred-num(x) : [1,1] or pred-num(x,y) : [1,1]
				# Remember that the predicate in the clause will not contain the "-num" where num is some number.
				# We have to remove that manually while checking
				# Steps:
				# 1. get qualified nodes/edges as well as number associated for first predicate
				# 2. get qualified nodes/edges as well as number associated for second predicate
				# 3. if there's no number in steps 1 or 2 return false clause
				# 4. do comparison with each qualified component from step 1 with each qualified component in step 2

				# It's a node comparison
				if len(clause_variables) == 2:
					clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
					subset_1 = get_edge_rule_node_clause_subset(clause_var_1, target_edge, subsets, neighbors)
					subset_2 = get_edge_rule_node_clause_subset(clause_var_2, target_edge, subsets, neighbors)

					# 1, 2
					qualified_nodes_for_comparison_1, numbers_1 = get_qualified_components_node_comparison_clause(interpretations_node, subset_1, clause_label, clause_bnd)
					qualified_nodes_for_comparison_2, numbers_2 = get_qualified_components_node_comparison_clause(interpretations_node, subset_2, clause_label, clause_bnd)

				# It's an edge comparison
				elif len(clause_variables) == 4:
					clause_var_1_source, clause_var_1_target, clause_var_2_source, clause_var_2_target = clause_variables[0], clause_variables[1], clause_variables[2], clause_variables[3]
					subset_1_source, subset_1_target = get_edge_rule_edge_clause_subset(clause_var_1_source, clause_var_1_target, target_edge, subsets, neighbors, reverse_neighbors, nodes)
					subset_2_source, subset_2_target = get_edge_rule_edge_clause_subset(clause_var_2_source, clause_var_2_target, target_edge, subsets, neighbors, reverse_neighbors, nodes)

					# 1, 2
					qualified_nodes_for_comparison_1_source, qualified_nodes_for_comparison_1_target, numbers_1 = get_qualified_components_edge_comparison_clause(interpretations_edge, subset_1_source, subset_1_target, clause_label, clause_bnd, reverse_graph)
					qualified_nodes_for_comparison_2_source, qualified_nodes_for_comparison_2_target, numbers_2 = get_qualified_components_edge_comparison_clause(interpretations_edge, subset_2_source, subset_2_target, clause_label, clause_bnd, reverse_graph)

			# Check if thresholds are satisfied
			# If it's a comparison clause we just need to check if the numbers list is not empty (no threshold support)
			if clause_type == 'comparison':
				if len(numbers_1) == 0 or len(numbers_2) == 0:
					satisfaction = False
				# Node comparison. Compare stage
				elif len(clause_variables) == 2:
					satisfaction, qualified_nodes_1, qualified_nodes_2 = compare_numbers_node_predicate(numbers_1, numbers_2, clause_operator, qualified_nodes_for_comparison_1, qualified_nodes_for_comparison_2)

					# Update subsets with final qualified nodes
					subsets[clause_var_1] = qualified_nodes_1
					subsets[clause_var_2] = qualified_nodes_2
					qualified_comparison_nodes = numba.typed.List(qualified_nodes_1)
					qualified_comparison_nodes.extend(qualified_nodes_2)

					if atom_trace:
						qualified_nodes.append(qualified_comparison_nodes)
						qualified_edges.append(numba.typed.List.empty_list(edge_type))

					# Add annotations for comparison clause. For now, we don't distinguish between LHS and RHS annotations
					if ann_fn != '':
						a = numba.typed.List.empty_list(interval.interval_type)
						for qn in qualified_comparison_nodes:
							a.append(interval.closed(1, 1))
						annotations.append(a)
				# Edge comparison. Compare stage
				else:
					satisfaction, qualified_nodes_1_source, qualified_nodes_1_target, qualified_nodes_2_source, qualified_nodes_2_target = compare_numbers_edge_predicate(numbers_1, numbers_2, clause_operator,
																																										  qualified_nodes_for_comparison_1_source,
																																										  qualified_nodes_for_comparison_1_target,
																																										  qualified_nodes_for_comparison_2_source,
																																										  qualified_nodes_for_comparison_2_target)
					# Update subsets with final qualified nodes
					subsets[clause_var_1_source] = qualified_nodes_1_source
					subsets[clause_var_1_target] = qualified_nodes_1_target
					subsets[clause_var_2_source] = qualified_nodes_2_source
					subsets[clause_var_2_target] = qualified_nodes_2_target

					qualified_comparison_nodes_1 = numba.typed.List(zip(qualified_nodes_1_source, qualified_nodes_1_target))
					qualified_comparison_nodes_2 = numba.typed.List(zip(qualified_nodes_2_source, qualified_nodes_2_target))
					qualified_comparison_nodes = numba.typed.List(qualified_comparison_nodes_1)
					qualified_comparison_nodes.extend(qualified_comparison_nodes_2)

					if atom_trace:
						qualified_nodes.append(numba.typed.List.empty_list(node_type))
						qualified_edges.append(qualified_comparison_nodes)

					# Add annotations for comparison clause. For now, we don't distinguish between LHS and RHS annotations
					if ann_fn != '':
						a = numba.typed.List.empty_list(interval.interval_type)
						for qe in qualified_comparison_nodes:
							a.append(interval.closed(1, 1))
						annotations.append(a)
			
			# Non comparison clause
			else:
				if threshold_quantifier_type == 'total':
					if clause_type == 'node':
						neigh_len = len(subset)
					else:
						neigh_len = sum([len(l) for l in subset_target])
	
				# Available is all neighbors that have a particular label with bound inside [0,1]
				elif threshold_quantifier_type == 'available':
					if clause_type == 'node':
						neigh_len = len(get_qualified_components_node_clause(interpretations_node, subset, clause_label, interval.closed(0, 1)))
					else:
						neigh_len = len(get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause_label, interval.closed(0, 1), reverse_graph)[0])
	
				qualified_neigh_len = len(subsets[clause_var_1])
				satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, thresholds[i]) and satisfaction
			
			# Exit loop if even one clause is not satisfied
			if not satisfaction:
				break

		# Here we are done going through each clause of the rule
		# If all clauses we're satisfied, proceed to collect annotations and prepare edges to be added
		if satisfaction:
			# Collect edges to be added
			source, target, _ = rule_edges

			# Edges to be added
			if source != '' and target != '':
				# Check if edge nodes are source/target
				if source == '__source':
					edges_to_be_added[0].append(target_edge[0])
				elif source == '__target':
					edges_to_be_added[0].append(target_edge[1])
				elif source in subsets:
					edges_to_be_added[0].extend(subsets[source])
				else:
					edges_to_be_added[0].append(source)

				if target == '__source':
					edges_to_be_added[1].append(target_edge[0])
				elif target == '__target':
					edges_to_be_added[1].append(target_edge[1])
				elif target in subsets:
					edges_to_be_added[1].extend(subsets[target])
				else:
					edges_to_be_added[1].append(target)

			# node/edge, annotations, qualified nodes, qualified edges, edges to be added
			applicable_rules.append((target_edge, annotations, qualified_nodes, qualified_edges, edges_to_be_added))

	return applicable_rules


@numba.njit(cache=False)
def get_node_rule_node_clause_subset(clause_var_1, target_node, subsets, neighbors):
	# The groundings for node clauses are either the target node, neighbors of the target node, or an existing subset of nodes
	if clause_var_1 == '__target':
		subset = numba.typed.List([target_node])
	else:
		subset = neighbors[target_node] if clause_var_1 not in subsets else subsets[clause_var_1]
	return subset


@numba.njit(cache=False)
def get_node_rule_edge_clause_subset(clause_var_1, clause_var_2, target_node, subsets, neighbors, reverse_neighbors, nodes):
	# There are 5 cases for predicate(Y,Z):
	# 1. Either one or both of Y, Z are the target node
	# 2. Both predicate variables Y and Z have not been encountered before
	# 3. The source variable Y has not been encountered before but the target variable Z has
	# 4. The target variable Z has not been encountered before but the source variable Y has
	# 5. Both predicate variables Y and Z have been encountered before

	# Case 1:
	# Check if 1st variable or 1st and 2nd variables are the target
	if clause_var_1 == '__target':
		subset_source = numba.typed.List([target_node])

		# If both variables are the same
		if clause_var_2 == '__target':
			subset_target = numba.typed.List([numba.typed.List([target_node])])
		elif clause_var_2 in subsets:
			subset_target = numba.typed.List([subsets[clause_var_2]])
		else:
			subset_target = numba.typed.List([neighbors[target_node]])

	# Check if 2nd variable is the target (this means 1st variable isn't the target)
	elif clause_var_2 == '__target':
		subset_source = reverse_neighbors[target_node] if clause_var_1 not in subsets else subsets[clause_var_1]
		subset_target = numba.typed.List([numba.typed.List([target_node]) for _ in subset_source])

	# Case 2:
	# We replace Y by all nodes and Z by the neighbors of each of these nodes
	elif clause_var_1 not in subsets and clause_var_2 not in subsets:
		subset_source = numba.typed.List(nodes)
		subset_target = numba.typed.List([neighbors[n] for n in subset_source])

	# Case 3:
	# We replace Y by the sources of Z
	elif clause_var_1 not in subsets and clause_var_2 in subsets:
		subset_source = numba.typed.List.empty_list(node_type)
		subset_target = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))

		for n in subsets[clause_var_2]:
			sources = reverse_neighbors[n]
			for source in sources:
				subset_source.append(source)
				subset_target.append(numba.typed.List([n]))

	# Case 4:
	# We replace Z by the neighbors of Y
	elif clause_var_1 in subsets and clause_var_2 not in subsets:
		subset_source = subsets[clause_var_1]
		subset_target = numba.typed.List([neighbors[n] for n in subset_source])

	# Case 5:
	else:
		subset_source = subsets[clause_var_1]
		subset_target = numba.typed.List([subsets[clause_var_2] for _ in subset_source])

	return subset_source, subset_target


@numba.njit(cache=False)
def get_edge_rule_node_clause_subset(clause_var_1, target_edge, subsets, neighbors):
	# The groundings for node clauses are either the source, target, neighbors of the source node, or an existing subset of nodes
	if clause_var_1 == '__source':
		subset = numba.typed.List([target_edge[0]])
	elif clause_var_1 == '__target':
		subset = numba.typed.List([target_edge[1]])
	else:
		subset = neighbors[target_edge[0]] if clause_var_1 not in subsets else subsets[clause_var_1]
	return subset


@numba.njit(cache=False)
def get_edge_rule_edge_clause_subset(clause_var_1, clause_var_2, target_edge, subsets, neighbors, reverse_neighbors, nodes):
	# There are 5 cases for predicate(Y,Z):
	# 1. Either one or both of Y, Z are the source or target node
	# 2. Both predicate variables Y and Z have not been encountered before
	# 3. The source variable Y has not been encountered before but the target variable Z has
	# 4. The target variable Z has not been encountered before but the source variable Y has
	# 5. Both predicate variables Y and Z have been encountered before
	# Case 1:
	# Check if 1st variable is the source
	if clause_var_1 == '__source':
		subset_source = numba.typed.List([target_edge[0]])

		# If 2nd variable is source/target/something else
		if clause_var_2 == '__source':
			subset_target = numba.typed.List([numba.typed.List([target_edge[0]])])
		elif clause_var_2 == '__target':
			subset_target = numba.typed.List([numba.typed.List([target_edge[1]])])
		elif clause_var_2 in subsets:
			subset_target = numba.typed.List([subsets[clause_var_2]])
		else:
			subset_target = numba.typed.List([neighbors[target_edge[0]]])

	# if 1st variable is the target
	elif clause_var_1 == '__target':
		subset_source = numba.typed.List([target_edge[1]])

		# if 2nd variable is source/target/something else
		if clause_var_2 == '__source':
			subset_target = numba.typed.List([numba.typed.List([target_edge[0]])])
		elif clause_var_2 == '__target':
			subset_target = numba.typed.List([numba.typed.List([target_edge[1]])])
		elif clause_var_2 in subsets:
			subset_target = numba.typed.List([subsets[clause_var_2]])
		else:
			subset_target = numba.typed.List([neighbors[target_edge[1]]])

	# Handle the cases where the 2nd variable is source/target but the 1st is something else (cannot be source/target)
	elif clause_var_2 == '__source':
		subset_source = reverse_neighbors[target_edge[0]] if clause_var_1 not in subsets else subsets[clause_var_1]
		subset_target = numba.typed.List([numba.typed.List([target_edge[0]]) for _ in subset_source])

	elif clause_var_2 == '__target':
		subset_source = reverse_neighbors[target_edge[1]] if clause_var_1 not in subsets else subsets[clause_var_1]
		subset_target = numba.typed.List([numba.typed.List([target_edge[1]]) for _ in subset_source])

	# Case 2:
	# We replace Y by all nodes and Z by the neighbors of each of these nodes
	elif clause_var_1 not in subsets and clause_var_2 not in subsets:
		subset_source = numba.typed.List(nodes)
		subset_target = numba.typed.List([neighbors[n] for n in subset_source])

	# Case 3:
	# We replace Y by the sources of Z
	elif clause_var_1 not in subsets and clause_var_2 in subsets:
		subset_source = numba.typed.List.empty_list(node_type)
		subset_target = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))

		for n in subsets[clause_var_2]:
			sources = reverse_neighbors[n]
			for source in sources:
				subset_source.append(source)
				subset_target.append(numba.typed.List([n]))

	# Case 4:
	# We replace Z by the neighbors of Y
	elif clause_var_1 in subsets and clause_var_2 not in subsets:
		subset_source = subsets[clause_var_1]
		subset_target = numba.typed.List([neighbors[n] for n in subset_source])

	# Case 5:
	else:
		subset_source = subsets[clause_var_1]
		subset_target = numba.typed.List([subsets[clause_var_2] for _ in subset_source])

	return subset_source, subset_target


@numba.njit(cache=False)
def get_qualified_components_node_clause(interpretations_node, candidates, l, bnd):
	# Get all the qualified neighbors for a particular clause
	qualified_nodes = numba.typed.List.empty_list(node_type)
	for n in candidates:
		if is_satisfied_node(interpretations_node, n, (l, bnd)):
			qualified_nodes.append(n)

	return qualified_nodes


@numba.njit(cache=False)
def get_qualified_components_node_comparison_clause(interpretations_node, candidates, l, bnd):
	# Get all the qualified neighbors for a particular comparison clause and return them along with the number associated
	qualified_nodes = numba.typed.List.empty_list(node_type)
	qualified_nodes_numbers = numba.typed.List.empty_list(numba.types.float64)
	for n in candidates:
		result, number = is_satisfied_node_comparison(interpretations_node, n, (l, bnd))
		if result:
			qualified_nodes.append(n)
			qualified_nodes_numbers.append(number)

	return qualified_nodes, qualified_nodes_numbers


@numba.njit(cache=False)
def get_qualified_components_edge_clause(interpretations_edge, candidates_source, candidates_target, l, bnd, reverse_graph):
	# Get all the qualified sources and targets for a particular clause
	qualified_nodes_source = numba.typed.List.empty_list(node_type)
	qualified_nodes_target = numba.typed.List.empty_list(node_type)
	for i, source in enumerate(candidates_source):
		for target in candidates_target[i]:
			edge = (source, target) if not reverse_graph else (target, source)
			if is_satisfied_edge(interpretations_edge, edge, (l, bnd)):
				qualified_nodes_source.append(source)
				qualified_nodes_target.append(target)

	return qualified_nodes_source, qualified_nodes_target


@numba.njit(cache=False)
def get_qualified_components_edge_comparison_clause(interpretations_edge, candidates_source, candidates_target, l, bnd, reverse_graph):
	# Get all the qualified sources and targets for a particular clause
	qualified_nodes_source = numba.typed.List.empty_list(node_type)
	qualified_nodes_target = numba.typed.List.empty_list(node_type)
	qualified_edges_numbers = numba.typed.List.empty_list(numba.types.float64)
	for i, source in enumerate(candidates_source):
		for target in candidates_target[i]:
			edge = (source, target) if not reverse_graph else (target, source)
			result, number = is_satisfied_edge_comparison(interpretations_edge, edge, (l, bnd))
			if result:
				qualified_nodes_source.append(source)
				qualified_nodes_target.append(target)
				qualified_edges_numbers.append(number)

	return qualified_nodes_source, qualified_nodes_target, qualified_edges_numbers


@numba.njit(cache=False)
def compare_numbers_node_predicate(numbers_1, numbers_2, op, qualified_nodes_1, qualified_nodes_2):
	result = False
	final_qualified_nodes_1 = numba.typed.List.empty_list(node_type)
	final_qualified_nodes_2 = numba.typed.List.empty_list(node_type)
	for i in range(len(numbers_1)):
		for j in range(len(numbers_2)):
			if op == '<':
				if numbers_1[i] < numbers_2[j]:
					result = True
			elif op == '<=':
				if numbers_1[i] <= numbers_2[j]:
					result = True
			elif op == '>':
				if numbers_1[i] > numbers_2[j]:
					result = True
			elif op == '>=':
				if numbers_1[i] >= numbers_2[j]:
					result = True
			elif op == '==':
				if numbers_1[i] == numbers_2[j]:
					result = True
			elif op == '!=':
				if numbers_1[i] != numbers_2[j]:
					result = True

			if result:
				final_qualified_nodes_1.append(qualified_nodes_1[i])
				final_qualified_nodes_2.append(qualified_nodes_2[j])
	return result, final_qualified_nodes_1, final_qualified_nodes_2


@numba.njit(cache=False)
def compare_numbers_edge_predicate(numbers_1, numbers_2, op, qualified_nodes_1a, qualified_nodes_1b, qualified_nodes_2a, qualified_nodes_2b):
	result = False
	final_qualified_nodes_1a = numba.typed.List.empty_list(node_type)
	final_qualified_nodes_1b = numba.typed.List.empty_list(node_type)
	final_qualified_nodes_2a = numba.typed.List.empty_list(node_type)
	final_qualified_nodes_2b = numba.typed.List.empty_list(node_type)
	for i in range(len(numbers_1)):
		for j in range(len(numbers_2)):
			if op == '<':
				if numbers_1[i] < numbers_2[j]:
					result = True
			elif op == '<=':
				if numbers_1[i] <= numbers_2[j]:
					result = True
			elif op == '>':
				if numbers_1[i] > numbers_2[j]:
					result = True
			elif op == '>=':
				if numbers_1[i] >= numbers_2[j]:
					result = True
			elif op == '==':
				if numbers_1[i] == numbers_2[j]:
					result = True
			elif op == '!=':
				if numbers_1[i] != numbers_2[j]:
					result = True

			if result:
				final_qualified_nodes_1a.append(qualified_nodes_1a[i])
				final_qualified_nodes_1b.append(qualified_nodes_1b[i])
				final_qualified_nodes_2a.append(qualified_nodes_2a[j])
				final_qualified_nodes_2b.append(qualified_nodes_2b[j])
	return result, final_qualified_nodes_1a, final_qualified_nodes_1b, final_qualified_nodes_2a, final_qualified_nodes_2b


@numba.njit(cache=False)
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


@numba.njit(cache=False)
def _update_node(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Add label to world if it is not there
		if l not in world.world:
			world.world[l] = interval.closed(0, 1)

		# Check if update is necessary with previous bnd
		prev_bnd = world.world[l].copy()

		# override will not check for inconsistencies
		if override:
			world.world[l].set_lower_upper(bnd.lower, bnd.upper)
		else:
			world.update(l, bnd)
		world.world[l].set_static(static)
		if world.world[l]!=prev_bnd:
			updated = True
			updated_bnds.append(world.world[l])

			# Add to rule trace if update happened and add to atom trace if necessary
			if (save_graph_attributes_to_rule_trace or not mode=='graph-attribute-fact') and store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, l, world.world[l].copy()))
				if atom_trace:
					# Mode can be fact or rule, updation of trace will happen accordingly
					if mode=='fact' or mode=='graph-attribute-fact':
						qn = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
						qe = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
						name = facts_to_be_applied_trace[idx]
						_update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name)
					elif mode=='rule':
						qn, qe, name = rules_to_be_applied_trace[idx]
						_update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name)

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					if atom_trace:
						_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], f'IPL: {l.get_value()}')
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					if store_interpretation_changes:
						rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					if atom_trace:
						_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], f'IPL: {l.get_value()}')
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
					world.world[p1].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p1])
					if store_interpretation_changes:
						rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(lower, upper)))

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


@numba.njit(cache=False)
def _update_edge(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Add label to world if it is not there
		if l not in world.world:
			world.world[l] = interval.closed(0, 1)

		# Check if update is necessary with previous bnd
		prev_bnd = world.world[l].copy()

		# override will not check for inconsistencies
		if override:
			world.world[l].set_lower_upper(bnd.lower, bnd.upper)
		else:
			world.update(l, bnd)
		world.world[l].set_static(static)
		if world.world[l]!=prev_bnd:
			updated = True
			updated_bnds.append(world.world[l])

			# Add to rule trace if update happened and add to atom trace if necessary
			if (save_graph_attributes_to_rule_trace or not mode=='graph-attribute-fact') and store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, l, world.world[l].copy()))
				if atom_trace:
					# Mode can be fact or rule, updation of trace will happen accordingly
					if mode=='fact' or mode=='graph-attribute-fact':
						qn = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
						qe = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
						name = facts_to_be_applied_trace[idx]
						_update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name)
					elif mode=='rule':
						qn, qe, name = rules_to_be_applied_trace[idx]
						_update_rule_trace(rule_trace_atoms, qn, qe, prev_bnd, name)

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					if atom_trace:
						_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], f'IPL: {l.get_value()}')
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					if store_interpretation_changes:
						rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					if atom_trace:
						_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], f'IPL: {l.get_value()}')
					lower = max(world.world[p1].lower, 1 - world.world[p2].upper)
					upper = min(world.world[p1].upper, 1 - world.world[p2].lower)
					world.world[p1].set_lower_upper(lower, upper)
					world.world[p1].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					if store_interpretation_changes:
						rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(lower, upper)))
	
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


@numba.njit(cache=False)
def _update_rule_trace(rule_trace, qn, qe, prev_bnd, name):
	rule_trace.append((qn, qe, prev_bnd.copy(), name))
	

@numba.njit(cache=False)
def are_satisfied_node(interpretations, comp, nas):
	result = True
	for (label, interval) in nas:
		result = result and is_satisfied_node(interpretations, comp, (label, interval))
	return result


@numba.njit(cache=False)
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


@numba.njit(cache=False)
def is_satisfied_node_comparison(interpretations, comp, na):
	result = False
	number = 0
	l, bnd = na
	l_str = l.value

	if not (l is None or bnd is None):
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[comp]
			for world_l in world.world.keys():
				world_l_str = world_l.value
				if l_str in world_l_str and world_l_str[len(l_str)+1:].replace('.', '').replace('-', '').isdigit():
					# The label is contained in the world
					result = world.is_satisfied(world_l, na[1])
					# Find the suffix number
					number = str_to_float(world_l_str[len(l_str)+1:])
					break

		except:
			result = False
	else:
		result = True
	return result, number


@numba.njit(cache=False)
def are_satisfied_edge(interpretations, comp, nas):
	result = True
	for (label, interval) in nas:
		result = result and is_satisfied_edge(interpretations, comp, (label, interval))
	return result


@numba.njit(cache=False)
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


@numba.njit(cache=False)
def is_satisfied_edge_comparison(interpretations, comp, na):
	result = False
	number = 0
	l, bnd = na
	l_str = l.value

	if not (l is None or bnd is None):
		# This is to prevent a key error in case the label is a specific label
		try:
			world = interpretations[comp]
			for world_l in world.world.keys():
				world_l_str = world_l.value
				if l_str in world_l_str and world_l_str[len(l_str)+1:].replace('.', '').replace('-', '').isdigit():
					# The label is contained in the world
					result = world.is_satisfied(world_l, na[1])
					# Find the suffix number
					number = str_to_float(world_l_str[len(l_str)+1:])
					break

		except:
			result = False
	else:
		result = True
	return result, number


@numba.njit(cache=False)
def annotate(annotation_functions, rule, annotations, weights):
	func_name = rule.get_annotation_function()
	if func_name == '':
		return rule.get_bnd().lower, rule.get_bnd().upper
	else:
		with numba.objmode(annotation='Tuple((float64, float64))'):
			for func in annotation_functions:
				if func.__name__ == func_name:
					annotation = func(annotations, weights)
		return annotation


@numba.njit(cache=False)
def check_consistent_node(interpretations, comp, na):
	world = interpretations[comp]
	if na[0] in world.world:
		bnd = world.world[na[0]]
	else:
		bnd = interval.closed(0, 1)
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit(cache=False)
def check_consistent_edge(interpretations, comp, na):
	world = interpretations[comp]
	if na[0] in world.world:
		bnd = world.world[na[0]]
	else:
		bnd = interval.closed(0, 1)
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit(cache=False)
def resolve_inconsistency_node(interpretations, comp, na, ipl, t_cnt, fp_cnt, atom_trace, rule_trace, rule_trace_atoms, store_interpretation_changes):
	world = interpretations[comp]
	if store_interpretation_changes:
		rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, na[0], interval.closed(0,1)))
		if atom_trace:
			_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[na[0]], 'Inconsistency')
	# Resolve inconsistency and set static
	world.world[na[0]].set_lower_upper(0, 1)
	world.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], 'Inconsistency')
			world.world[p2].set_lower_upper(0, 1)
			world.world[p2].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], 'Inconsistency')
			world.world[p1].set_lower_upper(0, 1)
			world.world[p1].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(0,1)))
	# Add inconsistent predicates to a list 


@numba.njit(cache=False)
def resolve_inconsistency_edge(interpretations, comp, na, ipl, t_cnt, fp_cnt, atom_trace, rule_trace, rule_trace_atoms, store_interpretation_changes):
	w = interpretations[comp]
	if store_interpretation_changes:
		rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, na[0], interval.closed(0,1)))
		if atom_trace:
			_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[na[0]], 'Inconsistency')
	# Resolve inconsistency and set static
	w.world[na[0]].set_lower_upper(0, 1)
	w.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[p2], 'Inconsistency')
			w.world[p2].set_lower_upper(0, 1)
			w.world[p2].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[p1], 'Inconsistency')
			w.world[p1].set_lower_upper(0, 1)
			w.world[p1].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(0,1)))


@numba.njit(cache=False)
def _add_node(node, neighbors, reverse_neighbors, nodes, interpretations_node):
	nodes.append(node)
	neighbors[node] = numba.typed.List.empty_list(node_type)
	reverse_neighbors[node] = numba.typed.List.empty_list(node_type)
	interpretations_node[node] = world.World(numba.typed.List.empty_list(label.label_type))


@numba.njit(cache=False)
def _add_edge(source, target, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	# If not a node, add to list of nodes and initialize neighbors
	if source not in nodes:
		_add_node(source, neighbors, reverse_neighbors, nodes, interpretations_node)

	if target not in nodes:
		_add_node(target, neighbors, reverse_neighbors, nodes, interpretations_node)

	# Make sure edge doesn't already exist
	# Make sure, if l=='', not to add the label
	# Make sure, if edge exists, that we don't override the l label if it exists
	edge = (source, target)
	new_edge = False
	if edge not in edges:
		new_edge = True
		edges.append(edge)
		neighbors[source].append(target)
		reverse_neighbors[target].append(source)
		if l.value!='':
			interpretations_edge[edge] = world.World(numba.typed.List([l]))
		else:
			interpretations_edge[edge] = world.World(numba.typed.List.empty_list(label.label_type))
	else:
		if l not in interpretations_edge[edge].world and l.value!='':
			new_edge = True
			interpretations_edge[edge].world[l] = interval.closed(0, 1)

	return (edge, new_edge)


@numba.njit(cache=False)
def _add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	changes = 0
	edges_added = numba.typed.List.empty_list(edge_type)
	for source in sources:
		for target in targets:
			edge, new_edge = _add_edge(source, target, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge)
			edges_added.append(edge)
			changes = changes+1 if new_edge else changes
	return edges_added, changes


@numba.njit(cache=False)
def _delete_edge(edge, neighbors, reverse_neighbors, edges, interpretations_edge):
	source, target = edge
	edges.remove(edge)
	del interpretations_edge[edge]
	neighbors[source].remove(target)
	reverse_neighbors[target].remove(source)


@numba.njit(cache=False)
def float_to_str(value):
	number = int(value)
	decimal = int(value % 1 * 1000)
	float_str = f'{number}.{decimal}'
	return float_str


@numba.njit(cache=False)
def str_to_float(value):
	decimal_pos = value.find('.')
	if decimal_pos != -1:
		after_decimal_len = len(value[decimal_pos+1:])
	else:
		after_decimal_len = 0
	value = value.replace('.', '')
	value = str_to_int(value)
	value = value / 10**after_decimal_len
	return value


@numba.njit(cache=False)
def str_to_int(value):
	if value[0] == '-':
		negative = True
		value = value.replace('-','')
	else:
		negative = False
	final_index, result = len(value) - 1, 0
	for i, v in enumerate(value):
		result += (ord(v) - 48) * (10 ** (final_index - i))
	result = -result if negative else result
	return result
