import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.annotation_functions.annotation_functions as ann_fn

import numba
from numba import objmode


# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)

# Type for storing list of qualified nodes
list_of_nodes = numba.types.ListType(node_type)

# Type for storing int tuple
int_tuple = numba.types.UniTuple(numba.types.int64, 2)


class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, ipl, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, canonical, inconsistency_check, store_interpretation_changes):
		self.graph = graph
		self.ipl = ipl
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
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, node_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, edge_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, node_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.uint16, edge_type, label.label_type, interval.interval_type, numba.types.boolean, numba.types.boolean)))
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
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=numba.types.ListType(node_type))
		for n in self.graph.nodes():
			l = numba.typed.List.empty_list(node_type)
			[l.append(neigh) for neigh in self.graph.neighbors(n)]
			self.neighbors[n] = l

	@staticmethod
	@numba.njit(cache=True)
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
	@numba.njit(cache=True)
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
	@numba.njit(cache=True)
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

	def start_fp(self, tmax, facts_node, facts_edge, rules, verbose, convergence_threshold, convergence_bound_threshold):
		self.tmax = tmax
		self._convergence_mode, self._convergence_delta = self._init_convergence(convergence_bound_threshold, convergence_threshold)
		max_facts_time = self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.atom_trace)
		self._start_fp(rules, max_facts_time, verbose)

	@staticmethod
	@numba.njit(cache=True)
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

	def _start_fp(self, rules, max_facts_time, verbose):
		fp_cnt, t = self.reason(self.interpretations_node, self.interpretations_edge, self.tmax, self.prev_reasoning_data, rules, self.nodes, self.edges, self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.edges_to_be_added_node_rule, self.edges_to_be_added_edge_rule, self.rules_to_be_applied_node_trace, self.rules_to_be_applied_edge_trace, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self.ipl, self.rule_trace_node, self.rule_trace_edge, self.rule_trace_node_atoms, self.rule_trace_edge_atoms, self.reverse_graph, self.atom_trace, self.save_graph_attributes_to_rule_trace, self.canonical, self.inconsistency_check, self.store_interpretation_changes, max_facts_time, self._convergence_mode, self._convergence_delta, verbose)
		self.time = t - 1
		# If we need to reason again, store the next timestep to start from
		self.prev_reasoning_data[0] = t
		self.prev_reasoning_data[1] = fp_cnt
		if verbose:
			print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit(cache=True)
	def reason(interpretations_node, interpretations_edge, tmax, prev_reasoning_data, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, edges_to_be_added_node_rule, edges_to_be_added_edge_rule, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl, rule_trace_node, rule_trace_edge, rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, canonical, inconsistency_check, store_interpretation_changes, max_facts_time, convergence_mode, convergence_delta, verbose):
		t = prev_reasoning_data[0]
		fp_cnt = prev_reasoning_data[1]
		max_rules_time = 0
		timestep_loop = True
		facts_to_remove_idx = numba.typed.List.empty_list(numba.types.int64)
		rules_to_remove_idx = numba.typed.List.empty_list(numba.types.int64)
		while timestep_loop:
			if t==tmax:
				timestep_loop=False
			if verbose:
				with objmode():
					print('Timestep:', t, flush=True)
			# Reset Interpretation at beginning of timestep if non-canonical
			if t>0 and not canonical:
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
			update = False

			# Parameters for immediate rules
			immediate_node_rule_fire = False
			immediate_edge_rule_fire = False
			immediate_rule_applied = False
			# When delta_t = 0, we don't want to check the same rule with the same node/edge after coming back to the fp operator
			nodes_to_skip = numba.typed.List.empty_list(int_tuple)
			edges_to_skip = numba.typed.List.empty_list(int_tuple)

			# Start by applying facts
			# Nodes
			facts_to_remove_idx.clear()
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0]==t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4], facts_to_be_applied_node[i][5]
					# Check if bnd is static. Then no need to update, just add to rule trace, check if graph attribute and add ipl complement to rule trace as well
					if interpretations_node[comp].world[l].is_static():
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
						facts_to_be_applied_node[i] = (numba.types.uint16(facts_to_be_applied_node[i][0]+1), comp, l, bnd, static, graph_attribute)
					else:
						# Add to list to be removed later
						facts_to_remove_idx.append(i)

			# Delete facts that are not static
			facts_to_be_applied_node[:] = numba.typed.List([facts_to_be_applied_node[i] for i in range(len(facts_to_be_applied_node)) if i not in facts_to_remove_idx])

			# Edges
			facts_to_remove_idx.clear()
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4], facts_to_be_applied_edge[i][5]
					# Check if bnd is static. Then no need to update, just add to rule trace, check if graph attribute, and add ipl complement to rule trace as well
					if interpretations_edge[comp].world[l].is_static():
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
						facts_to_be_applied_edge[i] = (numba.types.uint16(facts_to_be_applied_edge[i][0]+1), comp, l, bnd, static, graph_attribute)
					else:
						# Add to list to be removed later
						facts_to_remove_idx.append(i)

			# Delete facts that are not static
			facts_to_be_applied_edge[:] = numba.typed.List([facts_to_be_applied_edge[i] for i in range(len(facts_to_be_applied_edge)) if i not in facts_to_remove_idx])

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
						idx = -1

					if i[0]==t:
						comp, l, bnd, immediate = i[1], i[2], i[3], i[4]
						sources, targets, edge_l = edges_to_be_added_node_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

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
										u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

										update = u or update

										# Update convergence params
										if convergence_mode=='delta_bound':
											bound_delta = max(bound_delta, changes)
										else:
											changes_cnt += changes
						else:
							# Check for inconsistencies
							if check_consistent_node(interpretations_node, comp, (l, bnd)):
								u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode='rule')

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
									u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, mode='rule', override=True)

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

				# Edges
				rules_to_remove_idx.clear()
				for idx, i in enumerate(rules_to_be_applied_edge):
					# If we broke from above loop to apply more rules, then break from here
					if immediate_rule_applied and not immediate_edge_rule_fire:
						break
					# If we are coming here from an immediate rule firing with delta_t=0 we have to apply that one rule. Which was just added to the list to_be_applied
					if immediate_edge_rule_fire and rules_to_be_applied_edge[-1][4]:
						i = rules_to_be_applied_edge[-1]
						idx = -1

					if i[0]==t:
						comp, l, bnd, immediate = i[1], i[2], i[3], i[4]
						sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

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
										u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

										update = u or update

										# Update convergence params
										if convergence_mode=='delta_bound':
											bound_delta = max(bound_delta, changes)
										else:
											changes_cnt += changes

						else:
							# Check for inconsistencies
							if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
								u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule')

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
									u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, mode='rule', override=True)

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
						# Go through all nodes and check if any rules apply to them
						# Only go through everything if the rule can be applied within the given timesteps, or we're running until convergence or it's an immediate rule.
						# Otherwise, it's an unnecessary loop
						delta_t = rule.get_delta()
						if t+delta_t<=tmax or tmax==-1:
							for j in range(len(nodes)):
								if (i, j) in nodes_to_skip:
									continue
								n = nodes[j]
								target_criteria_satisfaction = are_satisfied_node(interpretations_node, n, rule.get_target_criteria())
								if (target_criteria_satisfaction and is_satisfied_node(interpretations_node, n, (rule.get_target(), interval.closed(0,1)))) or (target_criteria_satisfaction and rule.get_target().value==''):
									result, annotations, qualified_nodes, qualified_edges, edges_to_add = _is_rule_applicable(interpretations_node, interpretations_edge, neighbors, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_annotation_function(), rule.get_annotation_label(), rule.get_edges(), atom_trace)
									if (result and rule.get_target().value=='') or (result and not interpretations_node[n].world[rule.get_target()].is_static()):
										bnd = influence(rule, annotations, rule.get_weights())
										max_rules_time = max(max_rules_time, t+delta_t)
										edges_to_be_added_node_rule.append(edges_to_add)
										rules_to_be_applied_node.append((numba.types.uint16(t+delta_t), n, rule.get_target(), bnd, immediate_rule))
										if atom_trace:
											rules_to_be_applied_node_trace.append((qualified_nodes, qualified_edges, rule.get_name()))

										# We apply a rule on a node/edge only once in each timestep to prevent it from being added to the to_be_added list continuously (this will improve performance
										nodes_to_skip.append((i, j))

										# Handle loop parameters for the next (maybe) fp operation
										# If it is a t=0 rule or an immediate rule we want to go back for another fp operation to check for new rules that may fire
										# Next fp operation we will skip this rule on this node because anyway there won't be an update
										if delta_t==0:
											in_loop = True
											update = False
										if immediate_rule and delta_t==0:
											# immediate_rule_fire becomes True because we still need to check for more eligible rules, we're not done.
											in_loop = True
											update = True
											immediate_node_rule_fire = True
											break

							# Break, apply immediate rule then come back to check for more applicable rules
							if immediate_node_rule_fire:
								break

							# Go through all edges and check if any rules apply to them.
							# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
							for j in range(len(edges)):
								if (i, j) in edges_to_skip:
									continue
								e = edges[j]
								target_criteria_satisfaction = are_satisfied_edge(interpretations_edge, e, rule.get_target_criteria())
								if (target_criteria_satisfaction and is_satisfied_node(interpretations_edge, e, (rule.get_target(), interval.closed(0,1)))) or (target_criteria_satisfaction and rule.get_target().value==''):
									# Find out if rule is applicable. returns list of list, of qualified nodes and qualified edges. one for each clause
									result, annotations, qualified_nodes, qualified_edges, edges_to_add = _is_rule_applicable_edge(interpretations_node, interpretations_edge, neighbors, e, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_annotation_function(), rule.get_annotation_label(), rule.get_edges(), atom_trace)
									if (result and rule.get_target().value=='') or (result and not interpretations_edge[e].world[rule.get_target()].is_static()):
										bnd = influence(rule, annotations, rule.get_weights())
										max_rules_time = max(max_rules_time, t+delta_t)
										edges_to_be_added_edge_rule.append(edges_to_add)
										rules_to_be_applied_edge.append((numba.types.uint16(t+delta_t), e, rule.get_target(), bnd, immediate_rule))
										if atom_trace:
											rules_to_be_applied_edge_trace.append((qualified_nodes, qualified_edges, rule.get_name()))

										# We apply a rule on a node/edge only once in each timestep to prevent it from being added to the to_be_added list continuously (this will improve performance
										edges_to_skip.append((i, j))

										# Handle loop parameters for the next (maybe) fp operation
										# If it is a t=0 rule or an immediate rule we want to go back for another fp operation to check for new rules that may fire
										# Next fp operation we will skip this rule on this node because anyway there won't be an update
										if delta_t==0:
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
				if (t>=max_facts_time and t>=max_rules_time) or (t>=max_facts_time and changes_cnt==0):
					if verbose:
						print(f'\nConverged at time: {t}')
					# Be consistent with time returned when we don't converge
					t += 1
					break

			# Increment t
			t += 1

		return fp_cnt, t	


@numba.njit(cache=True)
def _is_rule_applicable(interpretations_node, interpretations_edge, neighbors, target_node, neigh_criteria, thresholds, reverse_graph, ann_fn, ann_fn_label, edges, atom_trace):
	# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
	# Keep track of all the edges that are qualified
	# If it's a node clause update (x1 or x2 etc.) qualified neighbors, if it's an edge clause update the qualified neighbors for the source and target (x1, x2)
	# First gather all the qualified nodes for each clause
	subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
	qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
	qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
	annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
	edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), edges[-1])

	# Steps
	# 1. Gather all qualified nodes/edges, and check if they satisfy the thresholds. If not, break
	# 2. Gather all annotations associated with the qualified nodes/edges
	# 3. Assemble all constants for atom trace (this happens inside step 1 for efficiency)
	# 4. Collect edges and nodes to be added to the graph when rule fires

	# 1.
	satisfaction = True
	for i, clause in enumerate(neigh_criteria):
		# Gather qualified nodes/edges
		if clause[0]=='node':
			if clause[1][0]=='target':
				subset = numba.typed.List([target_node])
			else:
				subset = neighbors[target_node] if clause[1][0] not in subsets else subsets[clause[1][0]]

			subsets[clause[1][0]] = get_qualified_components_node_clause(interpretations_node, subset, clause[2], clause[3])
			if atom_trace:
				qualified_nodes.append(numba.typed.List(subsets[clause[1][0]]))
				qualified_edges.append(numba.typed.List.empty_list(edge_type))

		elif clause[0]=='edge':
			# Set sources for possible edges, if target use target node as source
			if clause[1][0]=='target':
				subset_source = numba.typed.List([target_node])
			else:
				subset_source = neighbors[target_node] if clause[1][0] not in subsets else subsets[clause[1][0]]

			subset_target = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
			if clause[1][1]=='target':
				# Set targets for possible edges, if target use target node as target
				for source in subset_source:
					subset_target.append(numba.typed.List([target_node]))
			else:
				for source in subset_source:
					subset_target.append(neighbors[source] if clause[1][1] not in subsets else subsets[clause[1][1]])

			qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause[2], clause[3], reverse_graph)
			subsets[clause[1][0]] = qe[0]
			subsets[clause[1][1]] = qe[1]

			if atom_trace:
				qualified_nodes.append(numba.typed.List.empty_list(node_type))
				qualified_edges.append(numba.typed.List(zip(subsets[clause[1][0]], subsets[clause[1][1]])))

		# Check if the clause satisfies threshold
		if thresholds[i][1][1]=='total':
			if clause[0]=='node':
				neigh_len = len(subset)
			elif clause[0]=='edge':
				neigh_len = sum([len(l) for l in subset_target])

		# Available is all neighbors that have a particular label with bound inside [0,1]
		elif thresholds[i][1][1]=='available':
			if clause[0]=='node':
				neigh_len = len(get_qualified_components_node_clause(interpretations_node, subset, clause[2], interval.closed(0,1)))
			if clause[0]=='edge':
				neigh_len = len(get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause[2], interval.closed(0,1), reverse_graph)[0])

		qualified_neigh_len = len(subsets[clause[1][0]])
		satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, thresholds[i]) and satisfaction
		# Exit loop if even one clause is not satisfied
		if satisfaction==False:
			break

	# 2.
	# Add to the subsets that will be used in annotation function
	if satisfaction:
		for clause in neigh_criteria:
			if ann_fn!='':
				a = numba.typed.List.empty_list(interval.interval_type)
				if clause[0]=='node':
					for qn in subsets[clause[1][0]]:
						a.append(interpretations_node[qn].world[ann_fn_label])
				elif clause[0]=='edge':
					for qe in numba.typed.List(zip(subsets[clause[1][0]], subsets[clause[1][1]])):
						a.append(interpretations_edge[qe].world[ann_fn_label])

				annotations.append(a)

	# 4.
	# Collect edges to be added
	if satisfaction:
		source, target, _ = edges

		# Edges to be added
		if source!='' and target!='':
			# Check if edge nodes are target
			if source=='target':
				edges_to_be_added[0].append(target_node)
			elif source in subsets:
				edges_to_be_added[0].extend(subsets[source])
			else:
				edges_to_be_added[0].append(source)

			if target=='target':
				edges_to_be_added[1].append(target_node)			
			elif target in subsets:
				edges_to_be_added[1].extend(subsets[target])
			else:
				edges_to_be_added[1].append(target)

	return (satisfaction, annotations, qualified_nodes, qualified_edges, edges_to_be_added)


@numba.njit(cache=True)
def _is_rule_applicable_edge(interpretations_node, interpretations_edge, neighbors, target_edge, neigh_criteria, thresholds, reverse_graph, ann_fn, ann_fn_label, edges, atom_trace):
	# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
	# Keep track of all the edges that are qualified
	# If it's a node clause update (x1 or x2 etc.) qualified neighbors, if it's an edge clause update the qualified neighbors for the source and target (x1, x2)
	# First gather all the qualified nodes for each clause
	subsets = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
	qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
	qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
	annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
	edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), edges[-1])

	# Steps
	# 1. Gather all qualified nodes/edges, and check if they satisfy the thresholds. If not, break
	# 2. Gather all annotations associated with the qualified nodes/edges
	# 3. Assemble all constants for atom trace (this happens inside step 1 for efficiency)
	# 4. Collect edges and nodes to be added to the graph when rule fires

	# 1.
	satisfaction = True
	for i, clause in enumerate(neigh_criteria):
		# Gather qualified nodes/edges
		# For nodes gather source neighbors only, not target neighbors
		if clause[0]=='node':
			if clause[1][0]=='source':
				subset = numba.typed.List([target_edge[0]])
			elif clause[1][0]=='target':
				subset = numba.typed.List([target_edge[1]])
			else:
				subset = neighbors[target_edge[0]] if clause[1][0] not in subsets else subsets[clause[1][0]]

			subsets[clause[1][0]] = get_qualified_components_node_clause(interpretations_node, subset, clause[2], clause[3])
			if atom_trace:
				qualified_nodes.append(numba.typed.List(subsets[clause[1][0]]))
				qualified_edges.append(numba.typed.List.empty_list(edge_type))

		elif clause[0]=='edge':
			# Set sources for possible edges, if target use target node as source
			# By default we take the subset_source to be the neighbors of the source node.
			if clause[1][0]=='source':
				subset_source = numba.typed.List([target_edge[0]])
			elif clause[1][0]=='target':
				subset_source = numba.typed.List([target_edge[1]])
			else:
				subset_source = neighbors[target_edge[0]] if clause[1][0] not in subsets else subsets[clause[1][0]]
				
			subset_target = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
			if clause[1][1]=='source':
				# Set targets for possible edges, if source use source node as target
				for source in subset_source:
					subset_target.append(numba.typed.List([target_edge[0]]))
			elif clause[1][1]=='target':
				# Set targets for possible edges, if target use target node as target
				for source in subset_source:
					subset_target.append(numba.typed.List([target_edge[1]]))
			else:
				for source in subset_source:
					subset_target.append(neighbors[source] if clause[1][1] not in subsets else subsets[clause[1][1]])

			qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause[2], clause[3], reverse_graph)
			subsets[clause[1][0]] = qe[0]
			subsets[clause[1][1]] = qe[1]

			if atom_trace:
				qualified_nodes.append(numba.typed.List.empty_list(node_type))
				qualified_edges.append(numba.typed.List(zip(subsets[clause[1][0]], subsets[clause[1][1]])))

		# Check if the clause satisfies threshold
		if thresholds[i][1][1]=='total':
			if clause[0]=='node':
				neigh_len = len(subset)
			elif clause[0]=='edge':
				neigh_len = sum([len(l) for l in subset_target])

		# Available is all neighbors that have a particular label with bound inside [0,1]
		elif thresholds[i][1][1]=='available':
			if clause[0]=='node':
				neigh_len = len(get_qualified_components_node_clause(interpretations_node, subset, clause[2], interval.closed(0,1)))
			if clause[0]=='edge':
				neigh_len = len(get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause[2], interval.closed(0,1), reverse_graph)[0])

		qualified_neigh_len = len(subsets[clause[1][0]])
		satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, thresholds[i]) and satisfaction
		# Exit loop if even one clause is not satisfied
		if satisfaction==False:
			break

	# 2.
	# Add to the subsets that will be used in annotation function
	if satisfaction:
		for clause in neigh_criteria:
			if ann_fn!='':
				a = numba.typed.List.empty_list(interval.interval_type)
				if clause[0]=='node':
					for qn in subsets[clause[1][0]]:
						a.append(interpretations_node[qn].world[ann_fn_label])
				elif clause[0]=='edge':
					for qe in numba.typed.List(zip(subsets[clause[1][0]], subsets[clause[1][1]])):
						a.append(interpretations_edge[qe].world[ann_fn_label])

				annotations.append(a)

	# 4.
	# Collect edges to be added
	if satisfaction:
		source, target, _ = edges

		# Edges to be added
		if source!='' and target!='':
			# Check if edge nodes are source or target
			if source=='source':
				edges_to_be_added[0].append(target_edge[0])
			elif source=='target':
				edges_to_be_added[0].append(target_edge[1])
			elif source in subsets:
				edges_to_be_added[0].extend(subsets[source])
			else:
				edges_to_be_added[0].append(source)

			if target=='source':
				edges_to_be_added[1].append(target_edge[0])
			elif target=='target':
				edges_to_be_added[1].append(target_edge[1])			
			elif target in subsets:
				edges_to_be_added[1].extend(subsets[target])
			else:
				edges_to_be_added[1].append(target)

	return (satisfaction, annotations, qualified_nodes, qualified_edges, edges_to_be_added)


@numba.njit(cache=True)
def get_qualified_components_node_clause(interpretations_node, candidates, l, bnd):
	# Get all the qualified neighbors for a particular clause
	qualified_nodes = numba.typed.List.empty_list(node_type)
	for n in candidates:
		if is_satisfied_node(interpretations_node, n, (l, bnd)):
			qualified_nodes.append(n)

	return qualified_nodes


@numba.njit(cache=True)
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

	return (qualified_nodes_source, qualified_nodes_target)
	

@numba.njit(cache=True)
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


@numba.njit(cache=True)
def _update_node(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

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


@numba.njit(cache=True)
def _update_edge(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

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


@numba.njit(cache=True)
def _update_rule_trace(rule_trace, qn, qe, prev_bnd, name):
	rule_trace.append((qn, qe, prev_bnd.copy(), name))
	

@numba.njit(cache=True)
def are_satisfied_node(interpretations, comp, nas):
	result = True
	for (label, interval) in nas:
		result = result and is_satisfied_node(interpretations, comp, (label, interval))
	return result


@numba.njit(cache=True)
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


@numba.njit(cache=True)
def are_satisfied_edge(interpretations, comp, nas):
	result = True
	for (label, interval) in nas:
		result = result and is_satisfied_edge(interpretations, comp, (label, interval))
	return result


@numba.njit(cache=True)
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


@numba.njit(cache=True)
def influence(rule, annotations, weights):
	func_name = rule.get_annotation_function()
	if func_name=='':
		return interval.closed(rule.get_bnd().lower, rule.get_bnd().upper)
	elif func_name=='average':
		return ann_fn.average(annotations, weights)
	elif func_name=='average_lower':
		return ann_fn.average_lower(annotations, weights)
	elif func_name=='minimum':
		return ann_fn.minimum(annotations, weights)
	elif func_name=='maximum':
		return ann_fn.maximum(annotations, weights)


@numba.njit(cache=True)
def check_consistent_node(interpretations, comp, na):
	world = interpretations[comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit(cache=True)
def check_consistent_edge(interpretations, comp, na):
	world = interpretations[comp]
	bnd = world.world[na[0]]
	if (na[1].lower > bnd.upper) or (bnd.lower > na[1].upper):
		return False
	else:
		return True


@numba.njit(cache=True)
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


@numba.njit(cache=True)
def resolve_inconsistency_edge(interpretations, comp, na, ipl, t_cnt, fp_cnt, atom_trace, rule_trace, rule_trace_atoms, store_interpretation_changes):
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


@numba.njit(cache=True)
def _add_node(node, neighbors, nodes, interpretations_node):
	nodes.append(node)
	neighbors[node] = numba.typed.List.empty_list(node_type)
	interpretations_node[node] = world.World(numba.typed.List.empty_list(label.label_type))


@numba.njit(cache=True)
def _add_edge(source, target, neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	# If not a node, add to list of nodes and initialize neighbors
	if source not in nodes:
		_add_node(source, neighbors, nodes, interpretations_node)

	if target not in nodes:
		_add_node(target, neighbors, nodes, interpretations_node)

	# Make sure edge doesnt already exist
	# Make sure, if l=='', not to add the label
	# Make sure, if edge exists, that we don't override the l label if it exists
	edge = (source, target)
	new_edge = False
	if edge not in edges:
		new_edge = True
		edges.append(edge)
		neighbors[source].append(target)
		if l.value!='':
			interpretations_edge[edge] = world.World(numba.typed.List([l]))
		else:
			interpretations_edge[edge] = world.World(numba.typed.List.empty_list(label.label_type))
	else:
		if l not in interpretations_edge[edge].world and l.value!='':
			new_edge = True
			interpretations_edge[edge].world[l] = interval.closed(0,1)

	return (edge, new_edge)


@numba.njit(cache=True)
def _add_edges(sources, targets, neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	changes = 0
	edges_added = numba.typed.List.empty_list(edge_type)
	for source in sources:
		for target in targets:
			edge, new_edge = _add_edge(source, target, neighbors, nodes, edges, l, interpretations_node, interpretations_edge)
			edges_added.append(edge)
			changes = changes+1 if new_edge else changes
	return (edges_added, changes)


@numba.njit(cache=True)
def float_to_str(value):
	number = int(value)
	decimal = int(value % 1 * 1000)
	float_str = f'{number}.{decimal}'
	return float_str
