from mancalog.scripts.components.edge import Edge
import mancalog.scripts.numba_wrapper.numba_types.node_type as node
import mancalog.scripts.numba_wrapper.numba_types.edge_type as edge
import mancalog.scripts.numba_wrapper.numba_types.world_type as world
import mancalog.scripts.numba_wrapper.numba_types.label_type as label

import itertools
import numba
import time


class Interpretation:
	available_labels_node = []
	available_labels_edge = []

	def __init__(self, net_diff_graph, tmax = 1):
		# self.interpretations = []
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph

		# start = time.time()
		# for t in range(0, self._tmax + 1):
		# 	nas = {}
		# 	for comp in self._net_diff_graph.get_components():
		# 		nas[comp] = comp.get_initial_world()
		# 	self.interpretations.append(nas)
		# end = time.time()
		# print(end-start)

		# TODO: Uncomment after world constructor works
		# start = time.time()
		# self.node_interpretations = Interpretation._init_interpretations_node(self._tmax, self._net_diff_graph.get_nodes(), self.available_labels_node)
		# self.edge_interpretations = Interpretation._init_interpretations_edge(self._tmax, self._net_diff_graph.get_edges(), self.available_labels_edge)
		# end = time.time()
		# print(end-start)
		# start = time.time()

		# TODO: Move to jitted function after world constructor is complete
		self.interpretations_node = numba.typed.List()
		node.Node.available_labels = self.available_labels_node
		for t in range(0, self._tmax + 1):
			nas = numba.typed.Dict.empty(key_type=node.node_type, value_type=world.world_type)
			for n in self._net_diff_graph.get_nodes():
				nas[n] = n.get_initial_world()
			self.interpretations_node.append(nas)
		
		self.interpretations_edge = numba.typed.List()
		edge.Edge.available_labels = self.available_labels_edge
		for t in range(0, self._tmax + 1):
			nas = numba.typed.Dict.empty(key_type=edge.edge_type, value_type=world.world_type)
			for e in self._net_diff_graph.get_edges():
				nas[e] = e.get_initial_world()
			self.interpretations_edge.append(nas)
		# end = time.time()
		# print(end-start)
		
		# Setup graph neighbors
		self.neighbors = numba.typed.Dict.empty(key_type=node.node_type, value_type=numba.types.ListType(node.node_type))
		for n in self._net_diff_graph.get_nodes():
			l = numba.typed.List.empty_list(node.node_type)
			[l.append(neigh) for neigh in self._net_diff_graph.neighbors(n)]
			self.neighbors[n] = l



	@staticmethod
	@numba.njit
	def _init_interpretations_node(tmax, nodes, available_labels):
		interpretations = numba.typed.List()
		for t in range(tmax+1):
			nas = numba.typed.Dict.empty(key_type=node.node_type, value_type=world.world_type)
			for n in nodes:
				nas[n] = n.get_initial_world(available_labels)
			interpretations.append(nas)
		return interpretations
	
	@staticmethod
	@numba.njit
	def _init_interpretations_edge(tmax, edges, available_labels):
		interpretations = numba.typed.List()
		for t in range(tmax+1):
			nas = numba.typed.Dict.empty(key_type=edge.edge_type, value_type=world.world_type)
			for e in edges:
				nas[e] = e.get_initial_world(available_labels)
			interpretations.append(nas)
		return interpretations



		

	def is_satisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			if comp.get_type()=='node':
				world = self.interpretations_node[time][comp]
			elif comp.get_type=='edge':
				world = self.interpretations_edge[time][comp]
			result = world.is_satisfied(na[0], na[1])
		else:
			result = True
		return result

	def are_satisfied(self, time, comp, nas):
		result = True
		for (label, interval) in nas:
			result = result and self.is_satisfied(time, comp, (label, interval))
		return result

	# @staticmethod
	# @numba.njit
	# def are_satisfied_stat(interpretations, time, comp, nas):
	# 	result = True
	# 	for (label, interval) in nas:
	# 		result = result and Interpretation.is_satisfied_stat(interpretations, time, comp, (label, interval))
	# 	return result

	# @staticmethod
	# def is_satisfied_stat(interpretations, time, comp, na):
	# 	result = False
	# 	if (not (na[0] is None or na[1] is None)):
	# 		world = interpretations[time][comp]
	# 		result = world.is_satisfied(na[0], na[1])
	# 	else:
	# 		result = True
	# 	return result


	def apply_facts(self, facts):
		param_list = []
		for fact in facts:
			param_list += [*zip(itertools.repeat(fact, fact.get_time_upper()+1-fact.get_time_lower()), list(range(fact.get_time_lower(), fact.get_time_upper() + 1)))]
		for param in param_list:
			self._apply_fact(*param)

	def _apply_fact(self, fact, t):
		comp = fact.get_component()
		if comp.get_type()=='node':
			world = self.interpretations_node[t][comp]
		elif comp.get_type()=='edge':
			world = self.interpretations_edge[t][comp]
		world.update(fact.get_label(), fact.get_bound())

	@staticmethod
	def _apply_fact_stat(interpretations, fact, t):
		world = interpretations[t][fact.get_component()]
		world.update(fact.get_label(), fact.get_bound())
		return interpretations

	def apply_local_rules(self, rules):
		# for t in range(self._tmax + 1):
		# 	# param_list = []
		# 	# nodes = self._net_diff_graph.get_nodes()
		# 	# param_list = list(itertools.product(rules, [t], nodes))
		# 	# for param in param_list:
		# 	# 	self._apply_local_rule(*param)
		# 	for rule in rules:
		# 		self._apply_local_rule(rule, t)
		start = time.time()
		self._apply_local_rule_stat(self.interpretations_node, self._tmax, rules, numba.typed.List(self._net_diff_graph.get_nodes()), self.neighbors)
		end = time.time()
		print('apply rules', end-start)



	def _apply_local_rule(self, rule, t):
		tDelta = t - rule.get_delta()
		if (tDelta >= 0):
			for n in self._net_diff_graph.get_nodes():
				if (self.are_satisfied(tDelta, n, rule.get_target_criteria())):
					a = self._get_neighbors(n)
					b = self._get_qualified_neigh(tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
					bnd = rule.influence(neigh = a, qualified_neigh = b)
					self._na_update(t, n, (rule.get_target(), bnd))

	@staticmethod
	@numba.njit
	def _apply_local_rule_stat(interpretations, tmax, rules, nodes, neighbors):
		for t in range(tmax+1):
			for rule in rules:
				tDelta = t - rule.get_delta()
				if (tDelta >= 0):
					for n in nodes:
						if are_satisfied_stat(interpretations, tDelta, n, rule.get_target_criteria()):
							a = neighbors[n]
							b = _get_qualified_neigh_stat(interpretations, neighbors[n], tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
							bnd = rule.influence(neigh=a, qualified_neigh=b)
							_na_update_stat(interpretations, t, n, (rule.get_target(), bnd))
		# tDelta = t - rule.get_delta()
		# if (tDelta >= 0):
		# 	if Interpretation.are_satisfied_stat(interpretations, tDelta, node, rule.get_target_criteria()):
		# 		a = Interpretation._get_neighbors_stat(graph, node)
		# 		b = Interpretation._get_qualified_neigh_stat(interpretations, graph, tDelta, node, rule.get_neigh_nodes(), rule.get_neigh_edges())
		# 		bnd = rule.influence(neigh=a, qualified_neigh=b)
		# 		new_interpretations = Interpretation._na_update_stat(interpretations, t, node, (rule.get_target(), bnd))
		# return interpretations

	def apply_global_rule(self, rule, t):
		bounds = []
		if t <= self._tmax:
			for n in self._net_diff_graph.get_nodes():
				if (self.are_satisfied(t, n, rule.get_local_target())):
					bnd = self.get_bound(t, n, rule.get_local_label())
					bounds.append(bnd)
			updated_bnd = rule.aggregate(bounds)
			self._na_update(t, self._net_diff_graph, (rule.get_global_label(), updated_bnd))


	def get_bound(self, time, comp, label):
		result = None
		if comp.get_type()=='node':
			world = self.interpretations_node[time][comp]
		elif comp.get_type()=='edge':
			world = self.interpretations_edge[time][comp]
		result = world.get_bound(label)

		return result


	def _get_neighbors(self, node):
		return list(self._net_diff_graph.neighbors(node))

	# @staticmethod
	# def _get_neighbors_stat(graph, node):
	# 	return list(graph.neighbors(node))

	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidates = self._get_neighbors(node)
		if(nc_node != None):
			for n in candidates:
				if(not self.are_satisfied(time, n, nc_node)):
					candidates.remove(n)
		if(nc_edge != None):
			for n in candidates:
				if(not self.are_satisfied(time, Edge(n.get_id(), node.get_id()), nc_edge)):
					candidates.remove(n)

		result = candidates

		return result

	# @staticmethod
	# def _get_qualified_neigh_stat(interpretations, candidates, time, node, nc_node, nc_edge):
	# 	result = []
	# 	if(nc_node != None):
	# 		candidates = [n for n in candidates if Interpretation.are_satisfied_stat(interpretations, time, n, nc_node)]
	# 	if(nc_edge != None):
	# 		candidates = [n for n in candidates if Interpretation.are_satisfied_stat(interpretations, time, Edge(n.get_id(), node.get_id()), nc_edge)]

	# 	result = candidates

	# 	return result

	def _na_update(self, time, comp, na):
		if comp.get_type()=='node':
			world = self.interpretations_node[time][comp]
		if comp.get_type()=='edge':
			world = self.interpretations_edge[time][comp]
		world.update(na[0], na[1])

	# @staticmethod
	# def _na_update_stat(interpretations, time, comp, na):
	# 	world = interpretations[time][comp]
	# 	world.update(na[0], na[1])
	# 	# return interpretations

	def copy(self, interpretation):
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					self._na_update(t, comp, (label, interpretation.get_bound(t, comp, label)))
		

	def __eq__(self, interp):
		result = True
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					if self.get_bound(t, comp, label) != interp.get_bound(t, comp, label):
					# if not self.get_bound(t, comp, label).equals(interp.get_bound(t, comp, label)):
						result = False
						break
				
				if not result:
					break

			if not result:
				break

		return result


@numba.njit
def _get_qualified_neigh_stat(interpretations, candidates, time, node, nc_node, nc_edge):
	result = numba.typed.List()
	if(nc_node != None):
		[result.append(n) for n in candidates if are_satisfied_stat(interpretations, time, n, nc_node)]
	# For some reason the following lines do not work with jit. These are not necessary when labels are for nodes only
	# if(nc_edge != None):
	# 	[result.append(n) for n in candidates if are_satisfied_stat_edge(interpretations, time, edge.Edge(n.get_id(), node.get_id()), nc_edge)]

	return result

@numba.njit
def _na_update_stat(interpretations, time, comp, na):
	world = interpretations[time][comp]
	world.update(na[0], na[1])
	# return interpretations

@numba.njit
def are_satisfied_stat(interpretations, time, comp, nas):
	result = True
	for (label, interval) in nas:
		result = result and is_satisfied_stat(interpretations, time, comp, (label, interval))
	return result

@numba.njit
def is_satisfied_stat(interpretations, time, comp, na):
	result = False
	if (not (na[0] is None or na[1] is None)):
		world = interpretations[time][comp]
		result = world.is_satisfied(na[0], na[1])
	else:
		result = True
	return result

# @numba.njit
# def are_satisfied_stat_edge(interpretations, time, comp, nas):
# 	result = True
# 	for (label, interval) in nas:
# 		result = result and is_satisfied_stat_edge(interpretations, time, comp, (label, interval))
# 	return result

# @numba.njit
# def is_satisfied_stat_edge(interpretations, time, comp, na):
# 	result = False
# 	if (not (na[0] is None or na[1] is None)):
# 		world = interpretations[time][comp]
# 		result = world.is_satisfied(na[0], na[1])
# 	else:
# 		result = True
# 	return result