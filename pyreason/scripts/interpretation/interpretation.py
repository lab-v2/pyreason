from typing import Union, Tuple

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

# Type for storing clause data
clause_data = numba.types.Tuple((numba.types.string, label.label_type, numba.types.ListType(numba.types.string)))

# Type for storing refine clause data
refine_data = numba.types.Tuple((numba.types.string, numba.types.string, numba.types.int8))

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

rules_to_be_applied_node_type = numba.types.Tuple((numba.types.uint16, node_type, label.label_type, interval.interval_type, numba.types.boolean))
rules_to_be_applied_edge_type = numba.types.Tuple((numba.types.uint16, edge_type, label.label_type, interval.interval_type, numba.types.boolean))
rules_to_be_applied_trace_type = numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), numba.types.string))
edges_to_be_added_type = numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type))


class Interpretation:
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, ipl, annotation_functions, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, persistent, inconsistency_check, store_interpretation_changes, update_mode, allow_ground_rules):
		self.graph = graph
		self.ipl = ipl
		self.annotation_functions = annotation_functions
		self.reverse_graph = reverse_graph
		self.atom_trace = atom_trace
		self.save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace
		self.persistent = persistent
		self.inconsistency_check = inconsistency_check
		self.store_interpretation_changes = store_interpretation_changes
		self.update_mode = update_mode
		self.allow_ground_rules = allow_ground_rules

		# Counter for number of ground atoms for each timestep, start with zero for the zeroth timestep
		self.num_ga = numba.typed.List.empty_list(numba.types.int64)
		self.num_ga.append(0)

		# For reasoning and reasoning again (contains previous time and previous fp operation cnt)
		self.time = 0
		self.prev_reasoning_data = numba.typed.List([0, 0])

		# Initialize list of tuples for rules/facts to be applied, along with all the ground atoms that fired the rule. One to One correspondence between rules_to_be_applied_node and rules_to_be_applied_node_trace if atom_trace is true
		self.rules_to_be_applied_node_trace = numba.typed.List.empty_list(rules_to_be_applied_trace_type)
		self.rules_to_be_applied_edge_trace = numba.typed.List.empty_list(rules_to_be_applied_trace_type)
		self.facts_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.string)
		self.facts_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.string)
		self.rules_to_be_applied_node = numba.typed.List.empty_list(rules_to_be_applied_node_type)
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(rules_to_be_applied_edge_type)
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
		self.nodes = numba.typed.List.empty_list(node_type)
		self.edges = numba.typed.List.empty_list(edge_type)
		self.nodes.extend(numba.typed.List(self.graph.nodes()))
		self.edges.extend(numba.typed.List(self.graph.edges()))

		self.interpretations_node, self.predicate_map_node = self._init_interpretations_node(self.nodes, self.specific_node_labels, self.num_ga)
		self.interpretations_edge, self.predicate_map_edge = self._init_interpretations_edge(self.edges, self.specific_edge_labels, self.num_ga)

		# Setup graph neighbors and reverse neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=numba.types.ListType(node_type))
		for n in self.graph.nodes():
			l = numba.typed.List.empty_list(node_type)
			[l.append(neigh) for neigh in self.graph.neighbors(n)]
			self.neighbors[n] = l

		self.reverse_neighbors = self._init_reverse_neighbors(self.neighbors)

	@staticmethod
	@numba.njit(cache=True)
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
	@numba.njit(cache=True)
	def _init_interpretations_node(nodes, specific_labels, num_ga):
		interpretations = numba.typed.Dict.empty(key_type=node_type, value_type=world.world_type)
		predicate_map = numba.typed.Dict.empty(key_type=label.label_type, value_type=list_of_nodes)

		# Initialize nodes
		for n in nodes:
			interpretations[n] = world.World(numba.typed.List.empty_list(label.label_type))

		# Specific labels
		for l, ns in specific_labels.items():
			predicate_map[l] = numba.typed.List(ns)
			for n in ns:
				interpretations[n].world[l] = interval.closed(0.0, 1.0)
				num_ga[0] += 1

		return interpretations, predicate_map

	@staticmethod
	@numba.njit(cache=True)
	def _init_interpretations_edge(edges, specific_labels, num_ga):
		interpretations = numba.typed.Dict.empty(key_type=edge_type, value_type=world.world_type)
		predicate_map = numba.typed.Dict.empty(key_type=label.label_type, value_type=list_of_edges)

		# Initialize edges
		for n in edges:
			interpretations[n] = world.World(numba.typed.List.empty_list(label.label_type))

		# Specific labels
		for l, es in specific_labels.items():
			predicate_map[l] = numba.typed.List(es)
			for e in es:
				interpretations[e].world[l] = interval.closed(0.0, 1.0)
				num_ga[0] += 1

		return interpretations, predicate_map

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

	def start_fp(self, tmax, facts_node, facts_edge, rules, verbose, convergence_threshold, convergence_bound_threshold, again=False, restart=True):
		self.tmax = tmax
		self._convergence_mode, self._convergence_delta = self._init_convergence(convergence_bound_threshold, convergence_threshold)
		max_facts_time = self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.atom_trace)
		self._start_fp(rules, max_facts_time, verbose, again, restart)

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

	def _start_fp(self, rules, max_facts_time, verbose, again, restart):
		if again:
			self.num_ga.append(self.num_ga[-1])
			if restart:
				self.time = 0
				self.prev_reasoning_data[0] = 0
		fp_cnt, t = self.reason(self.interpretations_node, self.interpretations_edge, self.predicate_map_node, self.predicate_map_edge, self.tmax, self.prev_reasoning_data, rules, self.nodes, self.edges, self.neighbors, self.reverse_neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.edges_to_be_added_node_rule, self.edges_to_be_added_edge_rule, self.rules_to_be_applied_node_trace, self.rules_to_be_applied_edge_trace, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.ipl, self.rule_trace_node, self.rule_trace_edge, self.rule_trace_node_atoms, self.rule_trace_edge_atoms, self.reverse_graph, self.atom_trace, self.save_graph_attributes_to_rule_trace, self.persistent, self.inconsistency_check, self.store_interpretation_changes, self.update_mode, self.allow_ground_rules, max_facts_time, self.annotation_functions, self._convergence_mode, self._convergence_delta, self.num_ga, verbose, again)
		self.time = t - 1
		# If we need to reason again, store the next timestep to start from
		self.prev_reasoning_data[0] = t
		self.prev_reasoning_data[1] = fp_cnt
		if verbose:
			print('Fixed Point iterations:', fp_cnt)

	@staticmethod
	@numba.njit(cache=True, parallel=False)
	def reason(interpretations_node, interpretations_edge, predicate_map_node, predicate_map_edge, tmax, prev_reasoning_data, rules, nodes, edges, neighbors, reverse_neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, edges_to_be_added_node_rule, edges_to_be_added_edge_rule, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, ipl, rule_trace_node, rule_trace_edge, rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, persistent, inconsistency_check, store_interpretation_changes, update_mode, allow_ground_rules, max_facts_time, annotation_functions, convergence_mode, convergence_delta, num_ga, verbose, again):
		t = prev_reasoning_data[0]
		fp_cnt = prev_reasoning_data[1]
		max_rules_time = 0
		timestep_loop = True
		facts_to_be_applied_node_new = numba.typed.List.empty_list(facts_to_be_applied_node_type)
		facts_to_be_applied_edge_new = numba.typed.List.empty_list(facts_to_be_applied_edge_type)
		facts_to_be_applied_node_trace_new = numba.typed.List.empty_list(numba.types.string)
		facts_to_be_applied_edge_trace_new = numba.typed.List.empty_list(numba.types.string)
		rules_to_remove_idx = set()
		rules_to_remove_idx.add(-1)
		while timestep_loop:
			if t==tmax:
				timestep_loop = False
			if verbose:
				with objmode():
					print('Timestep:', t, flush=True)
			# Reset Interpretation at beginning of timestep if non-persistent
			if t>0 and not persistent:
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

			# Start by applying facts
			# Nodes
			facts_to_be_applied_node_new.clear()
			facts_to_be_applied_node_trace_new.clear()
			nodes_set = set(nodes)
			for i in range(len(facts_to_be_applied_node)):
				if facts_to_be_applied_node[i][0] == t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_node[i][1], facts_to_be_applied_node[i][2], facts_to_be_applied_node[i][3], facts_to_be_applied_node[i][4], facts_to_be_applied_node[i][5]
					# If the component is not in the graph, add it
					if comp not in nodes_set:
						_add_node(comp, neighbors, reverse_neighbors, nodes, interpretations_node)
						nodes_set.add(comp)

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
							override = True if update_mode == 'override' else False
							u, changes = _update_node(interpretations_node, predicate_map_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, i, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, num_ga, mode=mode, override=override)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency if necessary otherwise override bounds
						else:
							mode = 'graph-attribute-fact' if graph_attribute else 'fact'
							if inconsistency_check:
								resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, i, atom_trace, rule_trace_node, rule_trace_node_atoms, rules_to_be_applied_node_trace, facts_to_be_applied_node_trace, store_interpretation_changes, mode=mode)
							else:
								u, changes = _update_node(interpretations_node, predicate_map_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, i, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, num_ga, mode=mode, override=True)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes

					if static:
						facts_to_be_applied_node_new.append((numba.types.uint16(facts_to_be_applied_node[i][0]+1), comp, l, bnd, static, graph_attribute))
						if atom_trace:
							facts_to_be_applied_node_trace_new.append(facts_to_be_applied_node_trace[i])

				# If time doesn't match, fact to be applied later
				else:
					facts_to_be_applied_node_new.append(facts_to_be_applied_node[i])
					if atom_trace:
						facts_to_be_applied_node_trace_new.append(facts_to_be_applied_node_trace[i])

			# Update list of facts with ones that have not been applied yet (delete applied facts)
			facts_to_be_applied_node[:] = facts_to_be_applied_node_new.copy()
			if atom_trace:
				facts_to_be_applied_node_trace[:] = facts_to_be_applied_node_trace_new.copy()
			facts_to_be_applied_node_new.clear()
			facts_to_be_applied_node_trace_new.clear()

			# Edges
			facts_to_be_applied_edge_new.clear()
			facts_to_be_applied_edge_trace_new.clear()
			edges_set = set(edges)
			for i in range(len(facts_to_be_applied_edge)):
				if facts_to_be_applied_edge[i][0]==t:
					comp, l, bnd, static, graph_attribute = facts_to_be_applied_edge[i][1], facts_to_be_applied_edge[i][2], facts_to_be_applied_edge[i][3], facts_to_be_applied_edge[i][4], facts_to_be_applied_edge[i][5]
					# If the component is not in the graph, add it
					if comp not in edges_set:
						_add_edge(comp[0], comp[1], neighbors, reverse_neighbors, nodes, edges, label.Label(''), interpretations_node, interpretations_edge, predicate_map_edge, num_ga, t)
						edges_set.add(comp)

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
							override = True if update_mode == 'override' else False
							u, changes = _update_edge(interpretations_edge, predicate_map_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, i, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode=mode, override=override)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							mode = 'graph-attribute-fact' if graph_attribute else 'fact'
							if inconsistency_check:
								resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, i, atom_trace, rule_trace_edge, rule_trace_edge_atoms, rules_to_be_applied_edge_trace, facts_to_be_applied_edge_trace, store_interpretation_changes, mode=mode)
							else:
								u, changes = _update_edge(interpretations_edge, predicate_map_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, i, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode=mode, override=True)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes

					if static:
						facts_to_be_applied_edge_new.append((numba.types.uint16(facts_to_be_applied_edge[i][0]+1), comp, l, bnd, static, graph_attribute))
						if atom_trace:
							facts_to_be_applied_edge_trace_new.append(facts_to_be_applied_edge_trace[i])

				# Time doesn't match, fact to be applied later
				else:
					facts_to_be_applied_edge_new.append(facts_to_be_applied_edge[i])
					if atom_trace:
						facts_to_be_applied_edge_trace_new.append(facts_to_be_applied_edge_trace[i])

			# Update list of facts with ones that have not been applied yet (delete applied facts)
			facts_to_be_applied_edge[:] = facts_to_be_applied_edge_new.copy()
			if atom_trace:
				facts_to_be_applied_edge_trace[:] = facts_to_be_applied_edge_trace_new.copy()
			facts_to_be_applied_edge_new.clear()
			facts_to_be_applied_edge_trace_new.clear()

			in_loop = True
			while in_loop:
				# This will become true only if delta_t = 0 for some rule, otherwise we go to the next timestep
				in_loop = False

				# Apply the rules that need to be applied at this timestep
				# Nodes
				rules_to_remove_idx.clear()
				for idx, i in enumerate(rules_to_be_applied_node):
					if i[0] == t:
						comp, l, bnd, set_static = i[1], i[2], i[3], i[4]
						# Check for inconsistencies
						if check_consistent_node(interpretations_node, comp, (l, bnd)):
							override = True if update_mode == 'override' else False
							u, changes = _update_node(interpretations_node, predicate_map_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, num_ga, mode='rule', override=override)

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							if inconsistency_check:
								resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, idx, atom_trace, rule_trace_node, rule_trace_node_atoms, rules_to_be_applied_node_trace, facts_to_be_applied_node_trace, store_interpretation_changes, mode='rule')
							else:
								u, changes = _update_node(interpretations_node, predicate_map_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, store_interpretation_changes, num_ga, mode='rule', override=True)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes

						# Delete rules that have been applied from list by adding index to list
						rules_to_remove_idx.add(idx)

				# Remove from rules to be applied and edges to be applied lists after coming out from loop
				rules_to_be_applied_node[:] = numba.typed.List([rules_to_be_applied_node[i] for i in range(len(rules_to_be_applied_node)) if i not in rules_to_remove_idx])
				edges_to_be_added_node_rule[:] = numba.typed.List([edges_to_be_added_node_rule[i] for i in range(len(edges_to_be_added_node_rule)) if i not in rules_to_remove_idx])
				if atom_trace:
					rules_to_be_applied_node_trace[:] = numba.typed.List([rules_to_be_applied_node_trace[i] for i in range(len(rules_to_be_applied_node_trace)) if i not in rules_to_remove_idx])

				# Edges
				rules_to_remove_idx.clear()
				for idx, i in enumerate(rules_to_be_applied_edge):
					if i[0] == t:
						comp, l, bnd, set_static = i[1], i[2], i[3], i[4]
						sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge, predicate_map_edge, num_ga, t)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value != '':
							for e in edges_added:
								if interpretations_edge[e].world[edge_l].is_static():
									continue
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									override = True if update_mode == 'override' else False
									u, changes = _update_edge(interpretations_edge, predicate_map_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode='rule', override=override)

									update = u or update

									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes
								# Resolve inconsistency
								else:
									if inconsistency_check:
										resolve_inconsistency_edge(interpretations_edge, e, (edge_l, bnd), ipl, t, fp_cnt, idx, atom_trace, rule_trace_edge, rule_trace_edge_atoms, rules_to_be_applied_edge_trace, facts_to_be_applied_edge_trace, store_interpretation_changes, mode='rule')
									else:
										u, changes = _update_edge(interpretations_edge, predicate_map_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode='rule', override=True)

										update = u or update

										# Update convergence params
										if convergence_mode=='delta_bound':
											bound_delta = max(bound_delta, changes)
										else:
											changes_cnt += changes

						else:
							# Check for inconsistencies
							if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
								override = True if update_mode == 'override' else False
								u, changes = _update_edge(interpretations_edge, predicate_map_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode='rule', override=override)

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes
							# Resolve inconsistency
							else:
								if inconsistency_check:
									resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, idx, atom_trace, rule_trace_edge, rule_trace_edge_atoms, rules_to_be_applied_edge_trace, facts_to_be_applied_edge_trace, store_interpretation_changes, mode='rule')
								else:
									u, changes = _update_edge(interpretations_edge, predicate_map_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, set_static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, store_interpretation_changes, num_ga, mode='rule', override=True)

									update = u or update
									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes

						# Delete rules that have been applied from list by adding the index to list
						rules_to_remove_idx.add(idx)

				# Remove from rules to be applied and edges to be applied lists after coming out from loop
				rules_to_be_applied_edge[:] = numba.typed.List([rules_to_be_applied_edge[i] for i in range(len(rules_to_be_applied_edge)) if i not in rules_to_remove_idx])
				edges_to_be_added_edge_rule[:] = numba.typed.List([edges_to_be_added_edge_rule[i] for i in range(len(edges_to_be_added_edge_rule)) if i not in rules_to_remove_idx])
				if atom_trace:
					rules_to_be_applied_edge_trace[:] = numba.typed.List([rules_to_be_applied_edge_trace[i] for i in range(len(rules_to_be_applied_edge_trace)) if i not in rules_to_remove_idx])

				# Fixed point
				if update:
					# Increase fp operator count
					fp_cnt += 1

					# Lists or threadsafe operations (when parallel is on)
					rules_to_be_applied_node_threadsafe = numba.typed.List([numba.typed.List.empty_list(rules_to_be_applied_node_type) for _ in range(len(rules))])
					rules_to_be_applied_edge_threadsafe = numba.typed.List([numba.typed.List.empty_list(rules_to_be_applied_edge_type) for _ in range(len(rules))])
					if atom_trace:
						rules_to_be_applied_node_trace_threadsafe = numba.typed.List([numba.typed.List.empty_list(rules_to_be_applied_trace_type) for _ in range(len(rules))])
						rules_to_be_applied_edge_trace_threadsafe = numba.typed.List([numba.typed.List.empty_list(rules_to_be_applied_trace_type) for _ in range(len(rules))])
					edges_to_be_added_edge_rule_threadsafe = numba.typed.List([numba.typed.List.empty_list(edges_to_be_added_type) for _ in range(len(rules))])

					for i in prange(len(rules)):
						rule = rules[i]

						# Only go through if the rule can be applied within the given timesteps, or we're running until convergence
						delta_t = rule.get_delta()
						if t + delta_t <= tmax or tmax == -1 or again:
							applicable_node_rules, applicable_edge_rules = _ground_rule(rule, interpretations_node, interpretations_edge, predicate_map_node, predicate_map_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace, allow_ground_rules, num_ga, t)

							# Loop through applicable rules and add them to the rules to be applied for later or next fp operation
							for applicable_rule in applicable_node_rules:
								n, annotations, qualified_nodes, qualified_edges, _ = applicable_rule
								# If there is an edge to add or the predicate doesn't exist or the interpretation is not static
								if rule.get_target() not in interpretations_node[n].world or not interpretations_node[n].world[rule.get_target()].is_static():
									bnd = annotate(annotation_functions, rule, annotations, rule.get_weights())
									# Bound annotations in between 0 and 1
									bnd_l = min(max(bnd[0], 0), 1)
									bnd_u = min(max(bnd[1], 0), 1)
									bnd = interval.closed(bnd_l, bnd_u)
									max_rules_time = max(max_rules_time, t + delta_t)
									rules_to_be_applied_node_threadsafe[i].append((numba.types.uint16(t + delta_t), n, rule.get_target(), bnd, rule.is_static_rule()))
									if atom_trace:
										rules_to_be_applied_node_trace_threadsafe[i].append((qualified_nodes, qualified_edges, rule.get_name()))

									# If delta_t is zero we apply the rules and check if more are applicable
									if delta_t == 0:
										in_loop = True
										update = False

							for applicable_rule in applicable_edge_rules:
								e, annotations, qualified_nodes, qualified_edges, edges_to_add = applicable_rule
								# If there is an edge to add or the predicate doesn't exist or the interpretation is not static
								if len(edges_to_add[0]) > 0 or rule.get_target() not in interpretations_edge[e].world or not interpretations_edge[e].world[rule.get_target()].is_static():
									bnd = annotate(annotation_functions, rule, annotations, rule.get_weights())
									# Bound annotations in between 0 and 1
									bnd_l = min(max(bnd[0], 0), 1)
									bnd_u = min(max(bnd[1], 0), 1)
									bnd = interval.closed(bnd_l, bnd_u)
									max_rules_time = max(max_rules_time, t+delta_t)
									# edges_to_be_added_edge_rule.append(edges_to_add)
									edges_to_be_added_edge_rule_threadsafe[i].append(edges_to_add)
									rules_to_be_applied_edge_threadsafe[i].append((numba.types.uint16(t+delta_t), e, rule.get_target(), bnd, rule.is_static_rule()))
									if atom_trace:
										# rules_to_be_applied_edge_trace.append((qualified_nodes, qualified_edges, rule.get_name()))
										rules_to_be_applied_edge_trace_threadsafe[i].append((qualified_nodes, qualified_edges, rule.get_name()))

									# If delta_t is zero we apply the rules and check if more are applicable
									if delta_t == 0:
										in_loop = True
										update = False

					# Update lists after parallel run
					for i in range(len(rules)):
						if len(rules_to_be_applied_node_threadsafe[i]) > 0:
							rules_to_be_applied_node.extend(rules_to_be_applied_node_threadsafe[i])
						if len(rules_to_be_applied_edge_threadsafe[i]) > 0:
							rules_to_be_applied_edge.extend(rules_to_be_applied_edge_threadsafe[i])
						if atom_trace:
							if len(rules_to_be_applied_node_trace_threadsafe[i]) > 0:
								rules_to_be_applied_node_trace.extend(rules_to_be_applied_node_trace_threadsafe[i])
							if len(rules_to_be_applied_edge_trace_threadsafe[i]) > 0:
								rules_to_be_applied_edge_trace.extend(rules_to_be_applied_edge_trace_threadsafe[i])
						if len(edges_to_be_added_edge_rule_threadsafe[i]) > 0:
							edges_to_be_added_edge_rule.extend(edges_to_be_added_edge_rule_threadsafe[i])

			# Check for convergence after each timestep (perfect convergence or convergence specified by user)
			# Check number of changed interpretations or max bound change
			# User specified convergence
			if convergence_mode == 'delta_interpretation':
				if changes_cnt <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {int(changes_cnt)} changes from the previous interpretation')
					# Be consistent with time returned when we don't converge
					t += 1
					break
			elif convergence_mode == 'delta_bound':
				if bound_delta <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {float_to_str(bound_delta)} as the maximum bound change from the previous interpretation')
					# Be consistent with time returned when we don't converge
					t += 1
					break
			# Perfect convergence
			# Make sure there are no rules to be applied, and no facts that will be applied in the future. We do this by checking the max time any rule/fact is applicable
			# If no more rules/facts to be applied
			elif convergence_mode == 'perfect_convergence':
				if t>=max_facts_time and t >= max_rules_time:
					if verbose:
						print(f'\nConverged at time: {t}')
					# Be consistent with time returned when we don't converge
					t += 1
					break

			# Increment t, update number of ground atoms
			t += 1
			num_ga.append(num_ga[-1])

		return fp_cnt, t

	def add_edge(self, edge, l):
		# This function is useful for pyreason gym, called externally
		_add_edge(edge[0], edge[1], self.neighbors, self.reverse_neighbors, self.nodes, self.edges, l, self.interpretations_node, self.interpretations_edge, self.predicate_map_edge, self.num_ga, -1)

	def add_node(self, node, labels):
		# This function is useful for pyreason gym, called externally
		if node not in self.nodes:
			_add_node(node, self.neighbors, self.reverse_neighbors, self.nodes, self.interpretations_node)
			for l in labels:
				self.interpretations_node[node].world[label.Label(l)] = interval.closed(0, 1)

	def delete_edge(self, edge):
		# This function is useful for pyreason gym, called externally
		_delete_edge(edge, self.neighbors, self.reverse_neighbors, self.edges, self.interpretations_edge, self.predicate_map_edge, self.num_ga)

	def delete_node(self, node):
		# This function is useful for pyreason gym, called externally
		_delete_node(node, self.neighbors, self.reverse_neighbors, self.nodes, self.interpretations_node, self.predicate_map_node, self.num_ga)

	def get_dict(self):
		# This function can be called externally to retrieve a dict of the interpretation values
		# Only values in the rule trace will be added

		# Initialize interpretations for each time and node and edge
		interpretations = {}
		for t in range(self.time+1):
			interpretations[t] = {}
			for node in self.nodes:
				interpretations[t][node] = InterpretationDict()
			for edge in self.edges:
				interpretations[t][edge] = InterpretationDict()

		# Update interpretation nodes
		for change in self.rule_trace_node:
			time, _, node, l, bnd = change
			interpretations[time][node][l._value] = (bnd.lower, bnd.upper)

			# If persistent, update all following timesteps as well
			if self. persistent:
				for t in range(time+1, self.time+1):
					interpretations[t][node][l._value] = (bnd.lower, bnd.upper)

		# Update interpretation edges
		for change in self.rule_trace_edge:
			time, _, edge, l, bnd, = change
			interpretations[time][edge][l._value] = (bnd.lower, bnd.upper)

			# If persistent, update all following timesteps as well
			if self. persistent:
				for t in range(time+1, self.time+1):
					interpretations[t][edge][l._value] = (bnd.lower, bnd.upper)

		return interpretations

	def get_final_num_ground_atoms(self):
		"""
		This function returns the number of ground atoms after the reasoning process, for the final timestep
		:return: int: Number of ground atoms in the interpretation after reasoning
		"""
		ga_cnt = 0

		for node in self.nodes:
			for l in self.interpretations_node[node].world:
				ga_cnt += 1
		for edge in self.edges:
			for l in self.interpretations_edge[edge].world:
				ga_cnt += 1

		return ga_cnt

	def get_num_ground_atoms(self):
		"""
		This function returns the number of ground atoms after the reasoning process, for each timestep
		:return: list: Number of ground atoms in the interpretation after reasoning for each timestep
		"""
		if self.num_ga[-1] == 0:
			self.num_ga.pop()
		return self.num_ga

	def query(self, query, return_bool=True) -> Union[bool, Tuple[float, float]]:
		"""
		This function is used to query the graph after reasoning
		:param query: A PyReason query object
		:param return_bool: If True, returns boolean of query, else the bounds associated with it
		:return: bool, or bounds
		"""

		comp_type = query.get_component_type()
		component = query.get_component()
		pred = query.get_predicate()
		bnd = query.get_bounds()

		# Check if the component exists
		if comp_type == 'node':
			if component not in self.nodes:
				return False if return_bool else (0, 0)
		else:
			if component not in self.edges:
				return False if return_bool else (0, 0)

		# Check if the predicate exists
		if comp_type == 'node':
			if pred not in self.interpretations_node[component].world:
				return False if return_bool else (0, 0)
		else:
			if pred not in self.interpretations_edge[component].world:
				return False if return_bool else (0, 0)

		# Check if the bounds are satisfied
		if comp_type == 'node':
			if self.interpretations_node[component].world[pred] in bnd:
				return True if return_bool else (self.interpretations_node[component].world[pred].lower, self.interpretations_node[component].world[pred].upper)
			else:
				return False if return_bool else (0, 0)
		else:
			if self.interpretations_edge[component].world[pred] in bnd:
				return True if return_bool else (self.interpretations_edge[component].world[pred].lower, self.interpretations_edge[component].world[pred].upper)
			else:
				return False if return_bool else (0, 0)


@numba.njit(cache=True)
def _ground_rule(rule, interpretations_node, interpretations_edge, predicate_map_node, predicate_map_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace, allow_ground_rules, num_ga, t):
	# Extract rule params
	rule_type = rule.get_type()
	head_variables = rule.get_head_variables()
	clauses = rule.get_clauses()
	thresholds = rule.get_thresholds()
	ann_fn = rule.get_annotation_function()
	rule_edges = rule.get_edges()

	if rule_type == 'node':
		head_var_1 = head_variables[0]
	else:
		head_var_1, head_var_2 = head_variables[0], head_variables[1]

	# We return a list of tuples which specify the target nodes/edges that have made the rule body true
	applicable_rules_node = numba.typed.List.empty_list(node_applicable_rule_type)
	applicable_rules_edge = numba.typed.List.empty_list(edge_applicable_rule_type)

	# Grounding procedure
	# 1. Go through each clause and check which variables have not been initialized in groundings
	# 2. Check satisfaction of variables based on the predicate in the clause

	# Grounding variable that maps variables in the body to a list of grounded nodes
	# Grounding edges that maps edge variables to a list of edges
	groundings = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
	groundings_edges = numba.typed.Dict.empty(key_type=edge_type, value_type=list_of_edges)

	# Dependency graph that keeps track of the connections between the variables in the body
	dependency_graph_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=list_of_nodes)
	dependency_graph_reverse_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=list_of_nodes)

	nodes_set = set(nodes)
	edges_set = set(edges)

	satisfaction = True
	for i, clause in enumerate(clauses):
		# Unpack clause variables
		clause_type = clause[0]
		clause_label = clause[1]
		clause_variables = clause[2]
		clause_bnd = clause[3]
		clause_operator = clause[4]

		# This is a node clause
		if clause_type == 'node':
			clause_var_1 = clause_variables[0]

			# Get subset of nodes that can be used to ground the variable
			# If we allow ground atoms, we can use the nodes directly
			if allow_ground_rules and clause_var_1 in nodes_set:
				grounding = numba.typed.List([clause_var_1])
			else:
				grounding = get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map_node, clause_label, nodes)

			# Narrow subset based on predicate
			qualified_groundings = get_qualified_node_groundings(interpretations_node, grounding, clause_label, clause_bnd)
			groundings[clause_var_1] = qualified_groundings
			qualified_groundings_set = set(qualified_groundings)
			for c1, c2 in groundings_edges:
				if c1 == clause_var_1:
					groundings_edges[(c1, c2)] = numba.typed.List([e for e in groundings_edges[(c1, c2)] if e[0] in qualified_groundings_set])
				if c2 == clause_var_1:
					groundings_edges[(c1, c2)] = numba.typed.List([e for e in groundings_edges[(c1, c2)] if e[1] in qualified_groundings_set])

			# Check satisfaction of those nodes wrt the threshold
			# Only check satisfaction if the default threshold is used. This saves us from grounding the rest of the rule
			# It doesn't make sense to check any other thresholds because the head could be grounded with multiple nodes/edges
			# if thresholds[i][1][0] == 'number' and thresholds[i][1][1] == 'total' and thresholds[i][2] == 1.0:
			satisfaction = check_node_grounding_threshold_satisfaction(interpretations_node, grounding, qualified_groundings, clause_label, thresholds[i]) and satisfaction

		# This is an edge clause
		elif clause_type == 'edge':
			clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]

			# Get subset of edges that can be used to ground the variables
			# If we allow ground atoms, we can use the nodes directly
			if allow_ground_rules and (clause_var_1, clause_var_2) in edges_set:
				grounding = numba.typed.List([(clause_var_1, clause_var_2)])
			else:
				grounding = get_rule_edge_clause_grounding(clause_var_1, clause_var_2, groundings, groundings_edges, neighbors, reverse_neighbors, predicate_map_edge, clause_label, edges)

			# Narrow subset based on predicate (save the edges that are qualified to use for finding future groundings faster)
			qualified_groundings = get_qualified_edge_groundings(interpretations_edge, grounding, clause_label, clause_bnd)

			# Check satisfaction of those edges wrt the threshold
			# Only check satisfaction if the default threshold is used. This saves us from grounding the rest of the rule
			# It doesn't make sense to check any other thresholds because the head could be grounded with multiple nodes/edges
			# if thresholds[i][1][0] == 'number' and thresholds[i][1][1] == 'total' and thresholds[i][2] == 1.0:
			satisfaction = check_edge_grounding_threshold_satisfaction(interpretations_edge, grounding, qualified_groundings, clause_label, thresholds[i]) and satisfaction

			# Update the groundings
			groundings[clause_var_1] = numba.typed.List.empty_list(node_type)
			groundings[clause_var_2] = numba.typed.List.empty_list(node_type)
			groundings_clause_1_set = set(groundings[clause_var_1])
			groundings_clause_2_set = set(groundings[clause_var_2])
			for e in qualified_groundings:
				if e[0] not in groundings_clause_1_set:
					groundings[clause_var_1].append(e[0])
					groundings_clause_1_set.add(e[0])
				if e[1] not in groundings_clause_2_set:
					groundings[clause_var_2].append(e[1])
					groundings_clause_2_set.add(e[1])

			# Update the edge groundings (to use later for grounding other clauses with the same variables)
			groundings_edges[(clause_var_1, clause_var_2)] = qualified_groundings

			# Update dependency graph
			# Add a connection between clause_var_1 -> clause_var_2 and vice versa
			if clause_var_1 not in dependency_graph_neighbors:
				dependency_graph_neighbors[clause_var_1] = numba.typed.List([clause_var_2])
			elif clause_var_2 not in dependency_graph_neighbors[clause_var_1]:
				dependency_graph_neighbors[clause_var_1].append(clause_var_2)
			if clause_var_2 not in dependency_graph_reverse_neighbors:
				dependency_graph_reverse_neighbors[clause_var_2] = numba.typed.List([clause_var_1])
			elif clause_var_1 not in dependency_graph_reverse_neighbors[clause_var_2]:
				dependency_graph_reverse_neighbors[clause_var_2].append(clause_var_1)

		# This is a comparison clause
		else:
			pass

		# Refine the subsets based on any updates
		if satisfaction:
			refine_groundings(clause_variables, groundings, groundings_edges, dependency_graph_neighbors, dependency_graph_reverse_neighbors)

		# If satisfaction is false, break
		if not satisfaction:
			break

	# If satisfaction is still true, one final refinement to check if each edge pair is valid in edge rules
	# Then continue to setup any edges to be added and annotations
	# Fill out the rules to be applied lists
	if satisfaction:
		# Create temp grounding containers to verify if the head groundings are valid (only for edge rules)
		# Setup edges to be added and fill rules to be applied
		# Setup traces and inputs for annotation function
		# Loop through the clause data and setup final annotations and trace variables
		# Three cases: 1.node rule, 2. edge rule with infer edges, 3. edge rule
		if rule_type == 'node':
			# Loop through all the head variable groundings and add it to the rules to be applied
			# Loop through the clauses and add appropriate trace data and annotations

			# If there is no grounding for head_var_1, we treat it as a ground atom and add it to the graph
			head_var_1_in_nodes = head_var_1 in nodes
			add_head_var_node_to_graph = False
			if allow_ground_rules and head_var_1_in_nodes:
				groundings[head_var_1] = numba.typed.List([head_var_1])
			elif head_var_1 not in groundings:
				if not head_var_1_in_nodes:
					add_head_var_node_to_graph = True
				groundings[head_var_1] = numba.typed.List([head_var_1])

			for head_grounding in groundings[head_var_1]:
				qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
				qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
				annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
				edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), rule_edges[-1])

				# Check for satisfaction one more time in case the refining process has changed the groundings
				satisfaction = check_all_clause_satisfaction(interpretations_node, interpretations_edge, clauses, thresholds, groundings, groundings_edges)
				if not satisfaction:
					continue

				for i, clause in enumerate(clauses):
					clause_type = clause[0]
					clause_label = clause[1]
					clause_variables = clause[2]

					if clause_type == 'node':
						clause_var_1 = clause_variables[0]

						# 1.
						if atom_trace:
							if clause_var_1 == head_var_1:
								qualified_nodes.append(numba.typed.List([head_grounding]))
							else:
								qualified_nodes.append(numba.typed.List(groundings[clause_var_1]))
							qualified_edges.append(numba.typed.List.empty_list(edge_type))
						# 2.
						if ann_fn != '':
							a = numba.typed.List.empty_list(interval.interval_type)
							if clause_var_1 == head_var_1:
								a.append(interpretations_node[head_grounding].world[clause_label])
							else:
								for qn in groundings[clause_var_1]:
									a.append(interpretations_node[qn].world[clause_label])
							annotations.append(a)

					elif clause_type == 'edge':
						clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
						# 1.
						if atom_trace:
							# Cases: Both equal, one equal, none equal
							qualified_nodes.append(numba.typed.List.empty_list(node_type))
							if clause_var_1 == head_var_1:
								es = numba.typed.List([e for e in groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_grounding])
								qualified_edges.append(es)
							elif clause_var_2 == head_var_1:
								es = numba.typed.List([e for e in groundings_edges[(clause_var_1, clause_var_2)] if e[1] == head_grounding])
								qualified_edges.append(es)
							else:
								qualified_edges.append(numba.typed.List(groundings_edges[(clause_var_1, clause_var_2)]))
						# 2.
						if ann_fn != '':
							a = numba.typed.List.empty_list(interval.interval_type)
							if clause_var_1 == head_var_1:
								for e in groundings_edges[(clause_var_1, clause_var_2)]:
									if e[0] == head_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_2 == head_var_1:
								for e in groundings_edges[(clause_var_1, clause_var_2)]:
									if e[1] == head_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							else:
								for qe in groundings_edges[(clause_var_1, clause_var_2)]:
									a.append(interpretations_edge[qe].world[clause_label])
							annotations.append(a)
					else:
						# Comparison clause (we do not handle for now)
						pass

				# Now that we're sure that the rule is satisfied, we add the head to the graph if needed (only for ground rules)
				if add_head_var_node_to_graph:
					_add_node(head_var_1, neighbors, reverse_neighbors, nodes, interpretations_node)

				# For each grounding add a rule to be applied
				applicable_rules_node.append((head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_be_added))

		elif rule_type == 'edge':
			head_var_1 = head_variables[0]
			head_var_2 = head_variables[1]

			# If there is no grounding for head_var_1 or head_var_2, we treat it as a ground atom and add it to the graph
			head_var_1_in_nodes = head_var_1 in nodes
			head_var_2_in_nodes = head_var_2 in nodes
			add_head_var_1_node_to_graph = False
			add_head_var_2_node_to_graph = False
			add_head_edge_to_graph = False
			if allow_ground_rules and head_var_1_in_nodes:
				groundings[head_var_1] = numba.typed.List([head_var_1])
			if allow_ground_rules and head_var_2_in_nodes:
				groundings[head_var_2] = numba.typed.List([head_var_2])

			if head_var_1 not in groundings:
				if not head_var_1_in_nodes:
					add_head_var_1_node_to_graph = True
				groundings[head_var_1] = numba.typed.List([head_var_1])
			if head_var_2 not in groundings:
				if not head_var_2_in_nodes:
					add_head_var_2_node_to_graph = True
				groundings[head_var_2] = numba.typed.List([head_var_2])

			# Artificially connect the head variables with an edge if both of them were not in the graph
			if not head_var_1_in_nodes and not head_var_2_in_nodes:
				add_head_edge_to_graph = True

			head_var_1_groundings = groundings[head_var_1]
			head_var_2_groundings = groundings[head_var_2]

			source, target, _ = rule_edges
			infer_edges = True if source != '' and target != '' else False

			# Prepare the edges that we will loop over.
			# For infer edges we loop over each combination pair
			# Else we loop over the valid edges in the graph
			valid_edge_groundings = numba.typed.List.empty_list(edge_type)
			for g1 in head_var_1_groundings:
				for g2 in head_var_2_groundings:
					if infer_edges:
						valid_edge_groundings.append((g1, g2))
					else:
						if (g1, g2) in edges_set:
							valid_edge_groundings.append((g1, g2))

			# Loop through the head variable groundings
			for valid_e in valid_edge_groundings:
				head_var_1_grounding, head_var_2_grounding = valid_e[0], valid_e[1]
				qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
				qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
				annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
				edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), rule_edges[-1])

				# Containers to keep track of groundings to make sure that the edge pair is valid
				# We do this because we cannot know beforehand the edge matches from source groundings to target groundings
				temp_groundings = groundings.copy()
				temp_groundings_edges = groundings_edges.copy()

				# Refine the temp groundings for the specific edge head grounding
				# We update the edge collection as well depending on if there's a match between the clause variables and head variables
				temp_groundings[head_var_1] = numba.typed.List([head_var_1_grounding])
				temp_groundings[head_var_2] = numba.typed.List([head_var_2_grounding])
				for c1, c2 in temp_groundings_edges.keys():
					if c1 == head_var_1 and c2 == head_var_2:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e == (head_var_1_grounding, head_var_2_grounding)])
					elif c1 == head_var_2 and c2 == head_var_1:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e == (head_var_2_grounding, head_var_1_grounding)])
					elif c1 == head_var_1:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e[0] == head_var_1_grounding])
					elif c2 == head_var_1:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e[1] == head_var_1_grounding])
					elif c1 == head_var_2:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e[0] == head_var_2_grounding])
					elif c2 == head_var_2:
						temp_groundings_edges[(c1, c2)] = numba.typed.List([e for e in temp_groundings_edges[(c1, c2)] if e[1] == head_var_2_grounding])

				refine_groundings(head_variables, temp_groundings, temp_groundings_edges, dependency_graph_neighbors, dependency_graph_reverse_neighbors)

				# Check if the thresholds are still satisfied
				# Check if all clauses are satisfied again in case the refining process changed anything
				satisfaction = check_all_clause_satisfaction(interpretations_node, interpretations_edge, clauses, thresholds, temp_groundings, temp_groundings_edges)

				if not satisfaction:
					continue

				if infer_edges:
					# Prevent self loops while inferring edges if the clause variables are not the same
					if source != target and head_var_1_grounding == head_var_2_grounding:
						continue
					edges_to_be_added[0].append(head_var_1_grounding)
					edges_to_be_added[1].append(head_var_2_grounding)

				for i, clause in enumerate(clauses):
					clause_type = clause[0]
					clause_label = clause[1]
					clause_variables = clause[2]

					if clause_type == 'node':
						clause_var_1 = clause_variables[0]
						# 1.
						if atom_trace:
							if clause_var_1 == head_var_1:
								qualified_nodes.append(numba.typed.List([head_var_1_grounding]))
							elif clause_var_1 == head_var_2:
								qualified_nodes.append(numba.typed.List([head_var_2_grounding]))
							else:
								qualified_nodes.append(numba.typed.List(temp_groundings[clause_var_1]))
							qualified_edges.append(numba.typed.List.empty_list(edge_type))
						# 2.
						if ann_fn != '':
							a = numba.typed.List.empty_list(interval.interval_type)
							if clause_var_1 == head_var_1:
								a.append(interpretations_node[head_var_1_grounding].world[clause_label])
							elif clause_var_1 == head_var_2:
								a.append(interpretations_node[head_var_2_grounding].world[clause_label])
							else:
								for qn in temp_groundings[clause_var_1]:
									a.append(interpretations_node[qn].world[clause_label])
							annotations.append(a)

					elif clause_type == 'edge':
						clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
						# 1.
						if atom_trace:
							# Cases:
							# 1. Both equal (cv1 = hv1 and cv2 = hv2 or cv1 = hv2 and cv2 = hv1)
							# 2. One equal (cv1 = hv1 or cv2 = hv1 or cv1 = hv2 or cv2 = hv2)
							# 3. None equal
							qualified_nodes.append(numba.typed.List.empty_list(node_type))
							if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_var_1_grounding and e[1] == head_var_2_grounding])
								qualified_edges.append(es)
							elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_var_2_grounding and e[1] == head_var_1_grounding])
								qualified_edges.append(es)
							elif clause_var_1 == head_var_1:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_var_1_grounding])
								qualified_edges.append(es)
							elif clause_var_1 == head_var_2:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_var_2_grounding])
								qualified_edges.append(es)
							elif clause_var_2 == head_var_1:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[1] == head_var_1_grounding])
								qualified_edges.append(es)
							elif clause_var_2 == head_var_2:
								es = numba.typed.List([e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] if e[1] == head_var_2_grounding])
								qualified_edges.append(es)
							else:
								qualified_edges.append(numba.typed.List(temp_groundings_edges[(clause_var_1, clause_var_2)]))

						# 2.
						if ann_fn != '':
							a = numba.typed.List.empty_list(interval.interval_type)
							if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[0] == head_var_1_grounding and e[1] == head_var_2_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[0] == head_var_2_grounding and e[1] == head_var_1_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_1 == head_var_1:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[0] == head_var_1_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_1 == head_var_2:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[0] == head_var_2_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_2 == head_var_1:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[1] == head_var_1_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							elif clause_var_2 == head_var_2:
								for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									if e[1] == head_var_2_grounding:
										a.append(interpretations_edge[e].world[clause_label])
							else:
								for qe in temp_groundings_edges[(clause_var_1, clause_var_2)]:
									a.append(interpretations_edge[qe].world[clause_label])
							annotations.append(a)

				# Now that we're sure that the rule is satisfied, we add the head to the graph if needed (only for ground rules)
				if add_head_var_1_node_to_graph and head_var_1_grounding == head_var_1:
					_add_node(head_var_1, neighbors, reverse_neighbors, nodes, interpretations_node)
				if add_head_var_2_node_to_graph and head_var_2_grounding == head_var_2:
					_add_node(head_var_2, neighbors, reverse_neighbors, nodes, interpretations_node)
				if add_head_edge_to_graph and (head_var_1, head_var_2) == (head_var_1_grounding, head_var_2_grounding):
					_add_edge(head_var_1, head_var_2, neighbors, reverse_neighbors, nodes, edges, label.Label(''), interpretations_node, interpretations_edge, predicate_map_edge, num_ga, t)

				# For each grounding combination add a rule to be applied
				# Only if all the clauses have valid groundings
				# if satisfaction:
				e = (head_var_1_grounding, head_var_2_grounding)
				applicable_rules_edge.append((e, annotations, qualified_nodes, qualified_edges, edges_to_be_added))

	# Return the applicable rules
	return applicable_rules_node, applicable_rules_edge


@numba.njit(cache=True)
def check_all_clause_satisfaction(interpretations_node, interpretations_edge, clauses, thresholds, groundings, groundings_edges):
	# Check if the thresholds are satisfied for each clause
	satisfaction = True
	for i, clause in enumerate(clauses):
		# Unpack clause variables
		clause_type = clause[0]
		clause_label = clause[1]
		clause_variables = clause[2]

		if clause_type == 'node':
			clause_var_1 = clause_variables[0]
			satisfaction = check_node_grounding_threshold_satisfaction(interpretations_node, groundings[clause_var_1], groundings[clause_var_1], clause_label, thresholds[i]) and satisfaction
		elif clause_type == 'edge':
			clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
			satisfaction = check_edge_grounding_threshold_satisfaction(interpretations_edge, groundings_edges[(clause_var_1, clause_var_2)], groundings_edges[(clause_var_1, clause_var_2)], clause_label, thresholds[i]) and satisfaction
	return satisfaction


@numba.njit(cache=True)
def refine_groundings(clause_variables, groundings, groundings_edges, dependency_graph_neighbors, dependency_graph_reverse_neighbors):
	# Loop through the dependency graph and refine the groundings that have connections
	all_variables_refined = numba.typed.List(clause_variables)
	variables_just_refined = numba.typed.List(clause_variables)
	new_variables_refined = numba.typed.List.empty_list(numba.types.string)
	while len(variables_just_refined) > 0:
		for refined_variable in variables_just_refined:
			# Refine all the neighbors of the refined variable
			if refined_variable in dependency_graph_neighbors:
				for neighbor in dependency_graph_neighbors[refined_variable]:
					old_edge_groundings = groundings_edges[(refined_variable, neighbor)]
					new_node_groundings = groundings[refined_variable]

					# Delete old groundings for the variable being refined
					del groundings[neighbor]
					groundings[neighbor] = numba.typed.List.empty_list(node_type)

					# Update the edge groundings and node groundings
					qualified_groundings = numba.typed.List([edge for edge in old_edge_groundings if edge[0] in new_node_groundings])
					groundings_neighbor_set = set(groundings[neighbor])
					for e in qualified_groundings:
						if e[1] not in groundings_neighbor_set:
							groundings[neighbor].append(e[1])
							groundings_neighbor_set.add(e[1])
					groundings_edges[(refined_variable, neighbor)] = qualified_groundings

					# Add the neighbor to the list of refined variables so that we can refine for all its neighbors
					if neighbor not in all_variables_refined:
						new_variables_refined.append(neighbor)

			if refined_variable in dependency_graph_reverse_neighbors:
				for reverse_neighbor in dependency_graph_reverse_neighbors[refined_variable]:
					old_edge_groundings = groundings_edges[(reverse_neighbor, refined_variable)]
					new_node_groundings = groundings[refined_variable]

					# Delete old groundings for the variable being refined
					del groundings[reverse_neighbor]
					groundings[reverse_neighbor] = numba.typed.List.empty_list(node_type)

					# Update the edge groundings and node groundings
					qualified_groundings = numba.typed.List([edge for edge in old_edge_groundings if edge[1] in new_node_groundings])
					groundings_reverse_neighbor_set = set(groundings[reverse_neighbor])
					for e in qualified_groundings:
						if e[0] not in groundings_reverse_neighbor_set:
							groundings[reverse_neighbor].append(e[0])
							groundings_reverse_neighbor_set.add(e[0])
					groundings_edges[(reverse_neighbor, refined_variable)] = qualified_groundings

					# Add the neighbor to the list of refined variables so that we can refine for all its neighbors
					if reverse_neighbor not in all_variables_refined:
						new_variables_refined.append(reverse_neighbor)

		variables_just_refined = numba.typed.List(new_variables_refined)
		all_variables_refined.extend(new_variables_refined)
		new_variables_refined.clear()


@numba.njit(cache=True)
def check_node_grounding_threshold_satisfaction(interpretations_node, grounding, qualified_grounding, clause_label, threshold):
	threshold_quantifier_type = threshold[1][1]
	if threshold_quantifier_type == 'total':
		neigh_len = len(grounding)

	# Available is all neighbors that have a particular label with bound inside [0,1]
	elif threshold_quantifier_type == 'available':
		neigh_len = len(get_qualified_node_groundings(interpretations_node, grounding, clause_label, interval.closed(0, 1)))

	qualified_neigh_len = len(qualified_grounding)
	satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, threshold)
	return satisfaction


@numba.njit(cache=True)
def check_edge_grounding_threshold_satisfaction(interpretations_edge, grounding, qualified_grounding, clause_label, threshold):
	threshold_quantifier_type = threshold[1][1]
	if threshold_quantifier_type == 'total':
		neigh_len = len(grounding)

	# Available is all neighbors that have a particular label with bound inside [0,1]
	elif threshold_quantifier_type == 'available':
		neigh_len = len(get_qualified_edge_groundings(interpretations_edge, grounding, clause_label, interval.closed(0, 1)))

	qualified_neigh_len = len(qualified_grounding)
	satisfaction = _satisfies_threshold(neigh_len, qualified_neigh_len, threshold)
	return satisfaction


@numba.njit(cache=True)
def get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes):
	# The groundings for a node clause can be either a previous grounding or all possible nodes
	if l in predicate_map:
		grounding = predicate_map[l] if clause_var_1 not in groundings else groundings[clause_var_1]
	else:
		grounding = nodes if clause_var_1 not in groundings else groundings[clause_var_1]
	return grounding


@numba.njit(cache=True)
def get_rule_edge_clause_grounding(clause_var_1, clause_var_2, groundings, groundings_edges, neighbors, reverse_neighbors, predicate_map, l, edges):
	# There are 4 cases for predicate(Y,Z):
	# 1. Both predicate variables Y and Z have not been encountered before
	# 2. The source variable Y has not been encountered before but the target variable Z has
	# 3. The target variable Z has not been encountered before but the source variable Y has
	# 4. Both predicate variables Y and Z have been encountered before
	edge_groundings = numba.typed.List.empty_list(edge_type)

	# Case 1:
	# We replace Y by all nodes and Z by the neighbors of each of these nodes
	if clause_var_1 not in groundings and clause_var_2 not in groundings:
		if l in predicate_map:
			edge_groundings = predicate_map[l]
		else:
			edge_groundings = edges

	# Case 2:
	# We replace Y by the sources of Z
	elif clause_var_1 not in groundings and clause_var_2 in groundings:
		for n in groundings[clause_var_2]:
			es = numba.typed.List([(nn, n) for nn in reverse_neighbors[n]])
			edge_groundings.extend(es)

	# Case 3:
	# We replace Z by the neighbors of Y
	elif clause_var_1 in groundings and clause_var_2 not in groundings:
		for n in groundings[clause_var_1]:
			es = numba.typed.List([(n, nn) for nn in neighbors[n]])
			edge_groundings.extend(es)

	# Case 4:
	# We have seen both variables before
	else:
		# We have already seen these two variables in an edge clause
		if (clause_var_1, clause_var_2) in groundings_edges:
			edge_groundings = groundings_edges[(clause_var_1, clause_var_2)]
		# We have seen both these variables but not in an edge clause together
		else:
			groundings_clause_var_2_set = set(groundings[clause_var_2])
			for n in groundings[clause_var_1]:
				es = numba.typed.List([(n, nn) for nn in neighbors[n] if nn in groundings_clause_var_2_set])
				edge_groundings.extend(es)

	return edge_groundings


@numba.njit(cache=True)
def get_qualified_node_groundings(interpretations_node, grounding, clause_l, clause_bnd):
	# Filter the grounding by the predicate and bound of the clause
	qualified_groundings = numba.typed.List.empty_list(node_type)
	for n in grounding:
		if is_satisfied_node(interpretations_node, n, (clause_l, clause_bnd)):
			qualified_groundings.append(n)

	return qualified_groundings


@numba.njit(cache=True)
def get_qualified_edge_groundings(interpretations_edge, grounding, clause_l, clause_bnd):
	# Filter the grounding by the predicate and bound of the clause
	qualified_groundings = numba.typed.List.empty_list(edge_type)
	for e in grounding:
		if is_satisfied_edge(interpretations_edge, e, (clause_l, clause_bnd)):
			qualified_groundings.append(e)

	return qualified_groundings


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
def _update_node(interpretations, predicate_map, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, num_ga, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Add label to world if it is not there
		if l not in world.world:
			world.world[l] = interval.closed(0, 1)
			num_ga[t_cnt] += 1
			if l in predicate_map:
				predicate_map[l].append(comp)
			else:
				predicate_map[l] = numba.typed.List([comp])

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
				if p1 == l:
					if p2 not in world.world:
						world.world[p2] = interval.closed(0, 1)
						if p2 in predicate_map:
							predicate_map[p2].append(comp)
						else:
							predicate_map[p2] = numba.typed.List([comp])
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
				if p2 == l:
					if p1 not in world.world:
						world.world[p1] = interval.closed(0, 1)
						if p1 in predicate_map:
							predicate_map[p1].append(comp)
						else:
							predicate_map[p1] = numba.typed.List([comp])
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
def _update_edge(interpretations, predicate_map, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, num_ga, mode, override=False):
	updated = False
	# This is to prevent a key error in case the label is a specific label
	try:
		world = interpretations[comp]
		l, bnd = na
		updated_bnds = numba.typed.List.empty_list(interval.interval_type)

		# Add label to world if it is not there
		if l not in world.world:
			world.world[l] = interval.closed(0, 1)
			num_ga[t_cnt] += 1
			if l in predicate_map:
				predicate_map[l].append(comp)
			else:
				predicate_map[l] = numba.typed.List([comp])

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
				if p1 == l:
					if p2 not in world.world:
						world.world[p2] = interval.closed(0, 1)
						if p2 in predicate_map:
							predicate_map[p2].append(comp)
						else:
							predicate_map[p2] = numba.typed.List([comp])
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
				if p2 == l:
					if p1 not in world.world:
						world.world[p1] = interval.closed(0, 1)
						if p1 in predicate_map:
							predicate_map[p1].append(comp)
						else:
							predicate_map[p1] = numba.typed.List([comp])
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
	for (l, bnd) in nas:
		result = result and is_satisfied_node(interpretations, comp, (l, bnd))
	return result


@numba.njit(cache=True)
def is_satisfied_node(interpretations, comp, na):
	result = False
	if not (na[0] is None or na[1] is None):
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


@numba.njit(cache=True)
def are_satisfied_edge(interpretations, comp, nas):
	result = True
	for (l, bnd) in nas:
		result = result and is_satisfied_edge(interpretations, comp, (l, bnd))
	return result


@numba.njit(cache=True)
def is_satisfied_edge(interpretations, comp, na):
	result = False
	if not (na[0] is None or na[1] is None):
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


@numba.njit(cache=True)
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


@numba.njit(cache=True)
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


@numba.njit(cache=True)
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


@numba.njit(cache=True)
def resolve_inconsistency_node(interpretations, comp, na, ipl, t_cnt, fp_cnt, idx, atom_trace, rule_trace, rule_trace_atoms, rules_to_be_applied_trace, facts_to_be_applied_trace, store_interpretation_changes, mode):
	world = interpretations[comp]
	if store_interpretation_changes:
		rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, na[0], interval.closed(0,1)))
		if mode == 'fact' or mode == 'graph-attribute-fact' and atom_trace:
			name = facts_to_be_applied_trace[idx]
		elif mode == 'rule' and atom_trace:
			name = rules_to_be_applied_trace[idx][2]
		else:
			name = '-'
		if atom_trace:
			_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[na[0]], f'Inconsistency due to {name}')
	# Resolve inconsistency and set static
	world.world[na[0]].set_lower_upper(0, 1)
	world.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], f'Inconsistency due to {name}')
			world.world[p2].set_lower_upper(0, 1)
			world.world[p2].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], f'Inconsistency due to {name}')
			world.world[p1].set_lower_upper(0, 1)
			world.world[p1].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(0,1)))
	# Add inconsistent predicates to a list


@numba.njit(cache=True)
def resolve_inconsistency_edge(interpretations, comp, na, ipl, t_cnt, fp_cnt, idx, atom_trace, rule_trace, rule_trace_atoms, rules_to_be_applied_trace, facts_to_be_applied_trace, store_interpretation_changes, mode):
	w = interpretations[comp]
	if store_interpretation_changes:
		rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, na[0], interval.closed(0,1)))
		if mode == 'fact' or mode == 'graph-attribute-fact' and atom_trace:
			name = facts_to_be_applied_trace[idx]
		elif mode == 'rule' and atom_trace:
			name = rules_to_be_applied_trace[idx][2]
		else:
			name = '-'
		if atom_trace:
			_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[na[0]], f'Inconsistency due to {name}')
	# Resolve inconsistency and set static
	w.world[na[0]].set_lower_upper(0, 1)
	w.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[p2], f'Inconsistency due to {name}')
			w.world[p2].set_lower_upper(0, 1)
			w.world[p2].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), w.world[p1], f'Inconsistency due to {name}')
			w.world[p1].set_lower_upper(0, 1)
			w.world[p1].set_static(True)
			if store_interpretation_changes:
				rule_trace.append((numba.types.uint16(t_cnt), numba.types.uint16(fp_cnt), comp, p1, interval.closed(0,1)))


@numba.njit(cache=True)
def _add_node(node, neighbors, reverse_neighbors, nodes, interpretations_node):
	nodes.append(node)
	neighbors[node] = numba.typed.List.empty_list(node_type)
	reverse_neighbors[node] = numba.typed.List.empty_list(node_type)
	interpretations_node[node] = world.World(numba.typed.List.empty_list(label.label_type))


@numba.njit(cache=True)
def _add_edge(source, target, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge, predicate_map, num_ga, t):
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
			num_ga[t] += 1
			if l in predicate_map:
				predicate_map[l].append(edge)
			else:
				predicate_map[l] = numba.typed.List([edge])
		else:
			interpretations_edge[edge] = world.World(numba.typed.List.empty_list(label.label_type))
	else:
		if l not in interpretations_edge[edge].world and l.value!='':
			new_edge = True
			interpretations_edge[edge].world[l] = interval.closed(0, 1)
			num_ga[t] += 1

			if l in predicate_map:
				predicate_map[l].append(edge)
			else:
				predicate_map[l] = numba.typed.List([edge])

	return edge, new_edge


@numba.njit(cache=True)
def _add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge, predicate_map, num_ga, t):
	changes = 0
	edges_added = numba.typed.List.empty_list(edge_type)
	for source in sources:
		for target in targets:
			edge, new_edge = _add_edge(source, target, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge, predicate_map, num_ga, t)
			edges_added.append(edge)
			changes = changes+1 if new_edge else changes
	return edges_added, changes


@numba.njit(cache=True)
def _delete_edge(edge, neighbors, reverse_neighbors, edges, interpretations_edge, predicate_map, num_ga):
	source, target = edge
	edges.remove(edge)
	num_ga[-1] -= len(interpretations_edge[edge].world)
	del interpretations_edge[edge]
	for l in predicate_map:
		if edge in predicate_map[l]:
			predicate_map[l].remove(edge)
	neighbors[source].remove(target)
	reverse_neighbors[target].remove(source)


@numba.njit(cache=True)
def _delete_node(node, neighbors, reverse_neighbors, nodes, interpretations_node, predicate_map, num_ga):
	nodes.remove(node)
	num_ga[-1] -= len(interpretations_node[node].world)
	del interpretations_node[node]
	del neighbors[node]
	del reverse_neighbors[node]
	for l in predicate_map:
		if node in predicate_map[l]:
			predicate_map[l].remove(node)

	# Remove all occurrences of node in neighbors
	for n in neighbors.keys():
		if node in neighbors[n]:
			neighbors[n].remove(node)
	for n in reverse_neighbors.keys():
		if node in reverse_neighbors[n]:
			reverse_neighbors[n].remove(node)


@numba.njit(cache=True)
def float_to_str(value):
	number = int(value)
	decimal = int(value % 1 * 1000)
	float_str = f'{number}.{decimal}'
	return float_str


@numba.njit(cache=True)
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


@numba.njit(cache=True)
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
