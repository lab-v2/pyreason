from numpy import block
from torch import mul
from mancalog.scripts.components.world import World
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
# from numba import jit, prange
import multiprocessing
import itertools



class Interpretation:

	def __init__(self, net_diff_graph, tmax = 1):
		self.pool = multiprocessing.Pool(multiprocessing.cpu_count()-3)
		self.interpretations = []
		self._tmax = tmax
		self._net_diff_graph = net_diff_graph

		for t in range(0, self._tmax + 1):
			nas = {}
			for comp in self._net_diff_graph.get_components():
				nas[comp] = comp.get_initial_world()
			
			self.interpretations.append(nas)

		

	def is_satisfied(self, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			world = self.interpretations[time][comp]
			result = world.is_satisfied(na[0], na[1])
		else:
			result = True
		return result

	def are_satisfied(self, time, comp, nas):
		result = True
		for (label, interval) in nas:
			result = result and self.is_satisfied(time, comp, (label, interval))
		return result

	@staticmethod
	def are_satisfied_stat(interpretations, time, comp, nas):
		result = True
		for (label, interval) in nas:
			result = result and Interpretation.is_satisfied_stat(interpretations, time, comp, (label, interval))
		return result

	@staticmethod
	def is_satisfied_stat(interpretations, time, comp, na):
		result = False
		if (not (na[0] is None or na[1] is None)):
			world = interpretations[time][comp]
			result = world.is_satisfied(na[0], na[1])
		else:
			result = True
		return result


	def apply_facts(self, facts):
		# Parallelized
		# param_list = []
		# for fact in facts:
		# 	param_list += [*zip(itertools.repeat(self.interpretations, fact.get_time_upper()+1-fact.get_time_lower()), itertools.repeat(fact, fact.get_time_upper()+1-fact.get_time_lower()), list(range(fact.get_time_lower(), fact.get_time_upper() + 1)))]
		# interpretation = self.pool.starmap(self._apply_fact_stat, param_list)
		# self.interpretations = interpretation[0]
		# self.pool.close()
		# self.pool.join()

		# Non parallelized
		param_list = []
		for fact in facts:
			param_list += [*zip(itertools.repeat(fact, fact.get_time_upper()+1-fact.get_time_lower()), list(range(fact.get_time_lower(), fact.get_time_upper() + 1)))]
		for param in param_list:
			self._apply_fact(*param)

	def _apply_fact(self, fact, t):
		world = self.interpretations[t][fact.get_component()]
		world.update(fact.get_label(), fact.get_bound())

	@staticmethod
	def _apply_fact_stat(interpretations, fact, t):
		world = interpretations[t][fact.get_component()]
		world.update(fact.get_label(), fact.get_bound())
		return interpretations

	def apply_local_rules(self, rules):
		# Non parallelized
		# for t in range(self._tmax + 1):
		# 	param_list = []
		# 	nodes = self._net_diff_graph.get_nodes()
		# 	param_list = list(itertools.product(rules, [t], nodes))
		# 	for param in param_list:
		# 		self._apply_local_rule(*param)
		# 	# for rule in rules:
		# 	# 	self._apply_local_rule(rule, t)

		# Parallelized
		pool = multiprocessing.Pool(multiprocessing.cpu_count()-1)
		for t in range(self._tmax+1):
			param_list = []
			nodes = self._net_diff_graph.get_nodes()
			param_list = list(itertools.product([self.interpretations], [self._net_diff_graph], rules, [t], nodes))
			print(len(param_list))
			interpretations = self.pool.starmap(self._apply_local_rule_stat, param_list)

			print(type(interpretations[0]))
			self.interpretations = interpretations[0]
			print(type(self.interpretations))
		# self.pool.close()
		# self.pool.join()
		# pool.close()
		# pool.join()


	def _apply_local_rule(self, rule, t, n):
		tDelta = t - rule.get_delta()
		if (tDelta >= 0):
			if (self.are_satisfied(tDelta, n, rule.get_target_criteria())):
				a = self._get_neighbours(n)
				b = self._get_qualified_neigh(tDelta, n, rule.get_neigh_nodes(), rule.get_neigh_edges())
				bnd = rule.influence(neigh = a, qualified_neigh = b)
				self._na_update(t, n, (rule.get_target(), bnd))

	@staticmethod
	def _apply_local_rule_stat(interpretations, graph, rule, t, node):
		tDelta = t - rule.get_delta()
		if (tDelta >= 0):
			if Interpretation.are_satisfied_stat(interpretations, tDelta, node, rule.get_target_criteria()):
				a = Interpretation._get_neighbours_stat(graph, node)
				b = Interpretation._get_qualified_neigh_stat(interpretations, graph, tDelta, node, rule.get_neigh_nodes(), rule.get_neigh_edges())
				bnd = rule.influence(neigh=a, qualified_neigh=b)
				new_interpretations = Interpretation._na_update_stat(interpretations, t, node, (rule.get_target(), bnd))
		return interpretations

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
		world = self.interpretations[time][comp]
		result = world.get_bound(label)

		return result


	def _get_neighbours(self, node):
		return list(self._net_diff_graph.neighbors(node))

	@staticmethod
	def _get_neighbours_stat(graph, node):
		return list(graph.neighbors(node))

	def _get_qualified_neigh(self, time, node, nc_node = None, nc_edge = None):
		result = []
		candidatos = self._get_neighbours(node)
		if(nc_node != None):
			for n in candidatos:
				if(not self.are_satisfied(time, n, nc_node)):
					candidatos.remove(n)
		if(nc_edge != None):
			for n in candidatos:
				if(not self.are_satisfied(time, Edge(n.get_id(), node.get_id()), nc_edge)):
					candidatos.remove(n)

		result = candidatos

		return result

	@staticmethod
	def _get_qualified_neigh_stat(interpretations, graph, time, node, nc_node, nc_edge):
		result = []
		candidatos = Interpretation._get_neighbours_stat(graph, node)
		if(nc_node != None):
			for n in candidatos:
				if(not Interpretation.are_satisfied_stat(interpretations, time, n, nc_node)):
					candidatos.remove(n)
		if(nc_edge != None):
			for n in candidatos:
				if(not Interpretation.are_satisfied_stat(interpretations, time, Edge(n.get_id(), node.get_id()), nc_edge)):
					candidatos.remove(n)

		result = candidatos

		return result

	def _na_update(self, time, comp, na):
		world = self.interpretations[time][comp]
		world.update(na[0], na[1])

	@staticmethod
	def _na_update_stat(interpretations, time, comp, na):
		world = interpretations[time][comp]
		world.update(na[0], na[1])
		return interpretations

	def copy(self, interpretation):
		for t in range(0, self._tmax + 1):
			for comp in self._net_diff_graph.get_components():
				labels = comp.get_labels()
				for label in labels:
					self._na_update(t, comp, (label, interpretation.get_bound(t, comp, label)))
		

	def __str__(self):
		result = ''
		for t in range(0, len(self.interpretations)):
			result = result + 'TIME: ' + str(t) + '\n'
			for c in self.interpretations[t].keys():
				world = self.interpretations[t][c]
				result = result + str(c) + ':' + '\n'
				result = result + str(world) + '\n'

		return result

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