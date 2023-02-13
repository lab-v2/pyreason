import pyreason.scripts.numba_wrapper.numba_types.world_type as world
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.annotation_functions.annotation_functions as ann_fn

import numba
import time
from numba import objmode, config


# Types for the dictionaries
node_type = numba.types.string
edge_type = numba.types.UniTuple(numba.types.string, 2)

# Type for storing list of qualified nodes
list_of_nodes = numba.types.ListType(node_type)



class Interpretation:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node_type))
	specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge_type))

	def __init__(self, graph, tmax, ipl, reverse_graph, atom_trace, convergence_threshold, convergence_bound_threshold):
		self.tmax = tmax
		self.graph = graph
		self.ipl = ipl
		self.reverse_graph = reverse_graph
		self.atom_trace = atom_trace
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
		self.rules_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), numba.types.string)))
		self.rules_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.string)))
		self.facts_to_be_applied_node_trace = numba.typed.List.empty_list(numba.types.string)
		self.facts_to_be_applied_edge_trace = numba.typed.List.empty_list(numba.types.string)
		self.rules_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type)))
		self.rules_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type)))
		self.facts_to_be_applied_node = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, node_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.facts_to_be_applied_edge = numba.typed.List.empty_list(numba.types.Tuple((numba.types.int8, edge_type, label.label_type, interval.interval_type, numba.types.boolean)))
		self.edges_to_be_added_node_rule = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type)))
		self.edges_to_be_added_edge_rule = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(node_type), numba.types.ListType(node_type), label.label_type)))

		# Keep track of all the rules that have affeceted each node/edge at each timestep/fp operation, and all ground atoms that have affected the rules as well. Keep track of previous bounds and name of the rule/fact here
		self.rule_trace_node_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), numba.types.ListType(numba.types.ListType(edge_type)), interval.interval_type, numba.types.string)))
		self.rule_trace_edge_atoms = numba.typed.List.empty_list(numba.types.Tuple((numba.types.ListType(numba.types.ListType(node_type)), interval.interval_type, numba.types.string)))
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

	def start_fp(self, facts_node, facts_edge, rules, verbose):
		max_facts_time = self._init_facts(facts_node, facts_edge, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.atom_trace)
		self._start_fp(rules, max_facts_time, verbose)


	@staticmethod
	@numba.njit(cache=True)
	def _init_facts(facts_node, facts_edge, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, atom_trace):
		max_time = 0
		for fact in facts_node:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				facts_to_be_applied_node.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))
				if atom_trace:
					facts_to_be_applied_node_trace.append(fact.get_name())
		for fact in facts_edge:
			for t in range(fact.get_time_lower(), fact.get_time_upper() + 1):
				max_time = max(max_time, t)
				facts_to_be_applied_edge.append((numba.types.int8(t), fact.get_component(), fact.get_label(), fact.get_bound(), fact.static))
				if atom_trace:
					facts_to_be_applied_edge_trace.append(fact.get_name())
		return max_time

		
	def _start_fp(self, rules, max_facts_time, verbose):
		fp_cnt, t = self.reason(self.interpretations_node, self.interpretations_edge, self.tmax, rules, numba.typed.List(self.graph.nodes()), numba.typed.List(self.graph.edges()), self.neighbors, self.rules_to_be_applied_node, self.rules_to_be_applied_edge, self.edges_to_be_added_node_rule, self.edges_to_be_added_edge_rule, self.rules_to_be_applied_node_trace, self.rules_to_be_applied_edge_trace, self.facts_to_be_applied_node, self.facts_to_be_applied_edge, self.facts_to_be_applied_node_trace, self.facts_to_be_applied_edge_trace, self.available_labels_node, self.available_labels_edge, self.specific_node_labels, self.specific_edge_labels, self.ipl, self.rule_trace_node, self.rule_trace_edge, self.rule_trace_node_atoms, self.rule_trace_edge_atoms, self.reverse_graph, self.atom_trace, max_facts_time, self._convergence_mode, self._convergence_delta, verbose)
		self.time = t
		if verbose:
			print('Fixed Point iterations:', fp_cnt)


	@staticmethod
	@numba.njit(cache=True)
	def reason(interpretations_node, interpretations_edge, tmax, rules, nodes, edges, neighbors, rules_to_be_applied_node, rules_to_be_applied_edge, edges_to_be_added_node_rule, edges_to_be_added_edge_rule, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace, facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace, facts_to_be_applied_edge_trace, labels_node, labels_edge, specific_labels_node, specific_labels_edge, ipl, rule_trace_node, rule_trace_edge, rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace, max_facts_time, convergence_mode, convergence_delta, verbose):
		fp_cnt = 0
		for t in range(tmax+1):
			if verbose:
				with objmode():
					print('Timestep:', t, flush=True)
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
						rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, l, bnd))
						if atom_trace:
							_update_rule_trace_node(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), bnd, facts_to_be_applied_node_trace[i])
						for p1, p2 in ipl:
							if p1==l:
								rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p2, interpretations_node[comp].world[p2]))
								if atom_trace:
									_update_rule_trace_node(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_node[comp].world[p2], facts_to_be_applied_node_trace[i])
							elif p2==l:
								rule_trace_node.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p1, interpretations_node[comp].world[p1]))
								if atom_trace:
									_update_rule_trace_node(rule_trace_node_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), interpretations_node[comp].world[p1], facts_to_be_applied_node_trace[i])
							
					else:
						# Check for inconsistencies (multiple facts)
						if check_consistent_node(interpretations_node, comp, (l, bnd)):
							u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, static, convergence_mode, atom_trace, rules_to_be_applied_node_trace, i, facts_to_be_applied_node_trace, rule_trace_node_atoms, mode='fact')

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_node, rule_trace_node_atoms)
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
							_update_rule_trace_edge(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), bnd, facts_to_be_applied_edge_trace[i])
						for p1, p2 in ipl:
							if p1==l:
								rule_trace_edge.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p2, interpretations_edge[comp].world[p2]))
								if atom_trace:
									_update_rule_trace_edge(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), interpretations_edge[comp].world[p2], facts_to_be_applied_edge_trace[i])
							elif p2==l:
								rule_trace_edge.append((numba.types.int8(t), numba.types.int8(fp_cnt), comp, p1, interpretations_edge[comp].world[p1]))
								if atom_trace:
									_update_rule_trace_edge(rule_trace_edge_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), interpretations_edge[comp].world[p1], facts_to_be_applied_edge_trace[i])
					else:
						# Check for inconsistencies
						if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
							u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, static, convergence_mode, atom_trace, rules_to_be_applied_edge_trace, i, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, mode='fact')

							update = u or update
							# Update convergence params
							if convergence_mode=='delta_bound':
								bound_delta = max(bound_delta, changes)
							else:
								changes_cnt += changes
						# Resolve inconsistency
						else:
							resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms)
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
						sources, targets, edge_l = edges_to_be_added_node_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, mode='rule')

									update = u or update

									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes
								# Resolve inconsistency
								else:
									resolve_inconsistency_edge(interpretations_edge, e, (edge_l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms)
						else:
							# Check for inconsistencies
							if check_consistent_node(interpretations_node, comp, (l, bnd)):
								u, changes = _update_node(interpretations_node, comp, (l, bnd), ipl, rule_trace_node, fp_cnt, t, False, convergence_mode, atom_trace, rules_to_be_applied_node_trace, idx, facts_to_be_applied_node_trace, rule_trace_node_atoms, mode='rule')

								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes
							# Resolve inconsistency
							else:
								resolve_inconsistency_node(interpretations_node, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_node, rule_trace_node_atoms)

						# Delete rules that have been applied from list by changing t to -1
						rules_to_be_applied_node[idx] = (numba.types.int8(-1), comp, l, bnd)


				# Edges
				for idx, i in enumerate(rules_to_be_applied_edge):
					if i[0]==t:
						comp, l, bnd = i[1], i[2], i[3]
						sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
						edges_added, changes = _add_edges(sources, targets, neighbors, nodes, edges, edge_l, interpretations_node, interpretations_edge)
						changes_cnt += changes

						# Update bound for newly added edges. Use bnd to update all edges if label is specified, else use bnd to update normally
						if edge_l.value!='':
							for e in edges_added:
								if check_consistent_edge(interpretations_edge, e, (edge_l, bnd)):
									u, changes = _update_edge(interpretations_edge, e, (edge_l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, mode='rule')

									update = u or update

									# Update convergence params
									if convergence_mode=='delta_bound':
										bound_delta = max(bound_delta, changes)
									else:
										changes_cnt += changes
								# Resolve inconsistency
								else:
									resolve_inconsistency_edge(interpretations_edge, e, (edge_l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms)

						else:
							# Check for inconsistencies
							if check_consistent_edge(interpretations_edge, comp, (l, bnd)):
								u, changes = _update_edge(interpretations_edge, comp, (l, bnd), ipl, rule_trace_edge, fp_cnt, t, False, convergence_mode, atom_trace, rules_to_be_applied_edge_trace, idx, facts_to_be_applied_edge_trace, rule_trace_edge_atoms, mode='rule')
								
								update = u or update
								# Update convergence params
								if convergence_mode=='delta_bound':
									bound_delta = max(bound_delta, changes)
								else:
									changes_cnt += changes
							# Resolve inconsistency
							else:
								resolve_inconsistency_edge(interpretations_edge, comp, (l, bnd), ipl, t, fp_cnt, atom_trace, rule_trace_edge, rule_trace_edge_atoms)

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
									result, annotations, qualified_nodes, qualified_edges, edges_to_add = _is_rule_applicable(interpretations_node, interpretations_edge, a, n, rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_annotation_function(), rule.get_annotation_label(), rule.get_edges(), atom_trace)
									if result and not interpretations_node[n].world[rule.get_target()].is_static():
										bnd = influence(rule, annotations, rule.get_weights())
										max_rules_time = max(max_rules_time, t+rule.get_delta())
										edges_to_be_added_node_rule.append(edges_to_add)
										rules_to_be_applied_node.append((numba.types.int8(t+rule.get_delta()), n, rule.get_target(), bnd))
										if atom_trace:
											rules_to_be_applied_node_trace.append((qualified_nodes, qualified_edges, rule.get_name()))
										in_loop = True if rule.get_delta()==0 else False
							# Go through all edges and check if any rules apply to them.
							# Comment out the following lines if there are no labels or rules that deal with edges. It will be an unnecessary loop
							for e in edges:
								if are_satisfied_edge(interpretations_edge, e, rule.get_target_criteria()) and is_satisfied_node(interpretations_edge, e, (rule.get_target(), interval.closed(0,1))):
									# Node candidates are only source and target
									a = numba.typed.List([e[0], e[1]])
									# Find out if rule is applicable. returns list of list of qualified nodes and qualified edges. one for each clause
									result, annotations, qualified_nodes, _, edges_to_add = _is_rule_applicable(interpretations_node, interpretations_edge, a, e[0], rule.get_neigh_criteria(), rule.get_thresholds(), reverse_graph, rule.get_annotation_function(), rule.get_annotation_label(), rule.get_edges(), atom_trace)
									if result and not interpretations_edge[e].world[rule.get_target()].is_static():
										bnd = influence(rule, annotations, rule.get_weights())
										max_rules_time = max(max_rules_time, t+rule.get_delta())
										edges_to_be_added_edge_rule.append(edges_to_add)
										rules_to_be_applied_edge.append((numba.types.int8(t+rule.get_delta()), e, rule.get_target(), bnd))
										if atom_trace:
											rules_to_be_applied_edge_trace.append((qualified_nodes, rule.get_name()))
										in_loop = True if rule.get_delta()==0 else False
				
			# Check for convergence after each timestep (perfect convergence or convergence specified by user)
			# Check number of changed interpretations or max bound change
			# User specified convergence
			if convergence_mode=='delta_interpretation':
				if changes_cnt <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {int(changes_cnt)} changes from the previous interpretation')
					break
			elif convergence_mode=='delta_bound':
				if bound_delta <= convergence_delta:
					if verbose:
						print(f'\nConverged at time: {t} with {float_to_str(bound_delta)} as the maximum bound change from the previous interpretation')
					break
			# Perfect convergence
			# Make sure there are no rules to be applied, and no facts that will be applied in the future. We do this by checking the max time any rule/fact is applicable
			# If no more rules/facts to be applied
			elif convergence_mode=='perfect_convergence':
				if (t>=max_facts_time and t>=max_rules_time) or (t>=max_facts_time and changes_cnt==0):
					if verbose:
						print(f'\nConverged at time: {t}')					
					break

		return fp_cnt, t	
		


@numba.njit(cache=True)
def _is_rule_applicable(interpretations_node, interpretations_edge, candidates, target_node, neigh_criteria, thresholds, reverse_graph, ann_fn, ann_fn_label, edges, atom_trace):
	# Initialize dictionary where keys are strings (x1, x2 etc.) and values are lists of qualified neighbors
	# Keep track of all the edges that are qualified
	# If its a node clause update (x1 or x2 etc.) qualified neighbors, if its an edge clause update the qualified neighbors for the source and target (x1, x2)
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
			subset = candidates if clause[1][0] not in subsets else subsets[clause[1][0]]
			subsets[clause[1][0]] = get_qualified_components_node_clause(interpretations_node, subset, clause)
			if atom_trace:
				qualified_nodes.append(numba.typed.List(subsets[clause[1][0]]))
				qualified_edges.append(numba.typed.List.empty_list(edge_type))

		elif clause[0]=='edge':
			subset_source = candidates if clause[1][0] not in subsets else subsets[clause[1][0]]
			subset_target = candidates if clause[1][1] not in subsets else subsets[clause[1][1]]
			# If target is used, then use the target node
			if clause[1][0]=='target':
				subset_source = numba.typed.List([target_node])
			elif clause[1][1]=='target':
				subset_target = numba.typed.List([target_node])

			qe = get_qualified_components_edge_clause(interpretations_edge, subset_source, subset_target, clause, reverse_graph)
			subsets[clause[1][0]] = qe[0]
			subsets[clause[1][1]] = qe[1]

			if atom_trace:
				qualified_nodes.append(numba.typed.List.empty_list(node_type))
				qualified_edges.append(numba.typed.List(zip(subsets[clause[1][0]], subsets[clause[1][1]])))
		
		# Check if clause satisfies threshold
		if thresholds[i][1][1]=='total':
			neigh_len = len(candidates)
		elif thresholds[i][1][1]=='available':
			neigh_len = len(subsets[clause[1][0]])

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
			if source in subsets:
				edges_to_be_added[0].extend(subsets[source])
			else:
				edges_to_be_added[0].append(source)
			
			if target in subsets:
				edges_to_be_added[1].extend(subsets[target])
			else:
				edges_to_be_added[1].append(target)

	return (satisfaction, annotations, qualified_nodes, qualified_edges, edges_to_be_added)




@numba.njit(cache=True)
def get_qualified_components_node_clause(interpretations_node, candidates, clause):
	# Get all the qualified neighbors for a particular clause
	qualified_nodes = numba.typed.List.empty_list(node_type)
	for n in candidates:
		if is_satisfied_node(interpretations_node, n, (clause[2], clause[3])):
			qualified_nodes.append(n)

	return qualified_nodes


@numba.njit(cache=True)
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
def _update_node(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, mode):
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

			# Add to rule trace if update happened and add to atom trace if necessary
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, l, world.world[l].copy()))
			if atom_trace:
				# Mode can be fact or rule, updation of trace will happen accordingly
				if mode=='fact':
					qn = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
					qe = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
					name = facts_to_be_applied_trace[idx]
					_update_rule_trace_node(rule_trace_atoms, qn, qe, prev_bnd, name)
				elif mode=='rule':
					qn, qe, name = rules_to_be_applied_trace[idx]
					_update_rule_trace_node(rule_trace_atoms, qn, qe, prev_bnd, name)
			

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					if atom_trace:
						_update_rule_trace_node(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], f'IPL: {l.get_value()}')
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					if atom_trace:
						_update_rule_trace_node(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], f'IPL: {l.get_value()}')
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
	

@numba.njit(cache=True)
def _update_edge(interpretations, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, mode):
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

			# Add to rule trace if update happened and add to atom trace if necessary
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, l, world.world[l].copy()))
			if atom_trace:
				# Mode can be fact or rule, updation of trace will happen accordingly
				if mode=='fact':
					qn = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
					name = facts_to_be_applied_trace[idx]
					_update_rule_trace_edge(rule_trace_atoms, qn, prev_bnd, name)
				elif mode=='rule':
					qn, name = rules_to_be_applied_trace[idx]
					_update_rule_trace_edge(rule_trace_atoms, qn, prev_bnd, name)
			

		# Update complement of predicate (if exists) based on new knowledge of predicate
		if updated:
			ip_update_cnt = 0
			for p1, p2 in ipl:
				if p1==l:
					if atom_trace:
						_update_rule_trace_edge(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), world.world[p2], f'IPL: {l.get_value()}')
					lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
					upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
					world.world[p2].set_lower_upper(lower, upper)
					world.world[p2].set_static(static)
					ip_update_cnt += 1
					updated_bnds.append(world.world[p2])
					rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(lower, upper)))
				if p2==l:
					if atom_trace:
						_update_rule_trace_edge(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), world.world[p1], f'IPL: {l.get_value()}')
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


@numba.njit(cache=True)
def _update_rule_trace_node(rule_trace, qn, qe, prev_bnd, name):
	rule_trace.append((qn, qe, prev_bnd.copy(), name))

@numba.njit(cache=True)
def _update_rule_trace_edge(rule_trace, qn, prev_bnd, name):
	rule_trace.append((qn, prev_bnd.copy(), name))
	

@numba.njit(cache=True)
def are_satisfied_node(interpretations, comp, nas):
	result = True
	if len(nas)>0:
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
	if len(nas)>0:
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
def resolve_inconsistency_node(interpretations, comp, na, ipl, t_cnt, fp_cnt, atom_trace, rule_trace, rule_trace_atoms):
	world = interpretations[comp]
	rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], world.world[na[0]].copy()))
	if atom_trace:
		_update_rule_trace_node(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[na[0]], 'Inconsistency')
	# Resolve inconsistency and set static
	world.world[na[0]].set_lower_upper(0, 1)
	world.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace_node(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p2], 'Inconsistency')
			world.world[p2].set_lower_upper(0, 1)
			world.world[p2].set_static(True)
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace_node(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type)), world.world[p1], 'Inconsistency')
			world.world[p1].set_lower_upper(0, 1)
			world.world[p1].set_static(True)
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(0,1)))
	# Add inconsistent predicates to a list 


@numba.njit(cache=True)
def resolve_inconsistency_edge(interpretations, comp, na, ipl, t_cnt, fp_cnt, atom_trace, rule_trace, rule_trace_atoms):
	world = interpretations[comp]
	rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, na[0], world.world[na[0]].copy()))
	if atom_trace:
		_update_rule_trace_edge(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), world.world[na[0]], 'Inconsistency')
	# Resolve inconsistency and set static
	world.world[na[0]].set_lower_upper(0, 1)
	world.world[na[0]].set_static(True)
	for p1, p2 in ipl:
		if p1==na[0]:
			if atom_trace:
				_update_rule_trace_edge(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), world.world[p2], 'Inconsistency')
			world.world[p2].set_lower_upper(0, 1)
			world.world[p2].set_static(True)
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p2, interval.closed(0,1)))

		if p2==na[0]:
			if atom_trace:
				_update_rule_trace_edge(rule_trace_atoms, numba.typed.List.empty_list(numba.typed.List.empty_list(node_type)), world.world[p1], 'Inconsistency')
			world.world[p1].set_lower_upper(0, 1)
			world.world[p1].set_static(True)
			rule_trace.append((numba.types.int8(t_cnt), numba.types.int8(fp_cnt), comp, p1, interval.closed(0,1)))


@numba.njit(cache=True)
def _add_node(node, neighbors, nodes, l, interpretations_node):
	nodes.append(node)
	neighbors[node] = numba.typed.List.empty_list(node_type)
	# Make sure, if node exists, that we don't override the l label if it exists
	if l.value!='':
		interpretations_node[node] = world.World(numba.typed.List([l]))

@numba.njit(cache=True)
def _add_edge(source, target, neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	# If not a node, add to list of nodes and initialize neighbors
	# Make sure, if node exists, that we don't override the l label if it exists
	if source not in nodes:
		_add_node(source, neighbors, nodes, l, interpretations_node)
	else:
		if l not in interpretations_node[source].world and l.value!='':
			interpretations_node[source].world[l] = interval.closed(0,1)

	if target not in nodes:
		_add_node(target, neighbors, nodes, l, interpretations_node)
	else:
		if l not in interpretations_node[target].world and l.value!='':
			interpretations_node[target].world[l] = interval.closed(0,1)

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
		if l not in interpretations_edge[edge].world and l.value!='':
			new_edge = True
			interpretations_edge[edge].world[l] = interval.closed(0,1)

	return (edge, new_edge)
		


@numba.njit(cache=True)
def _add_edges(sources, targets, neighbors, nodes, edges, l, interpretations_node, interpretations_edge):
	changes = 0
	edges = numba.typed.List.empty_list(edge_type)
	for source in sources:
		for target in targets:
			edge, new_edge = _add_edge(source, target, neighbors, nodes, edges, l, interpretations_node, interpretations_edge)
			edges.append(edge)
			changes = changes+1 if new_edge else changes 
	return (edges, changes)


@numba.njit(cache=True)
def float_to_str(value):
	number = int(value)
	decimal = int(value % 1 * 1000)
	float_str = f'{number}.{decimal}'
	return float_str
