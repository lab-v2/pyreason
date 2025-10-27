from pyreason.scripts.interpretation.interpretation import Interpretation as Interpretation
from pyreason.scripts.interpretation.interpretation_parallel import Interpretation as InterpretationParallel
from pyreason.scripts.interpretation.interpretation_fp import Interpretation as InterpretationFP


class Program:
	specific_node_labels = []
	specific_edge_labels = []

	def __init__(self, graph, facts_node, facts_edge, rules, ipl, annotation_functions, head_functions, reverse_graph, atom_trace, save_graph_attributes_to_rule_trace, canonical, inconsistency_check, store_interpretation_changes, parallel_computing, update_mode, allow_ground_rules, fp_version):
		self._graph = graph
		self._facts_node = facts_node
		self._facts_edge = facts_edge
		self._rules = rules
		self._ipl = ipl
		self._annotation_functions = annotation_functions
		self._head_functions = head_functions
		self._reverse_graph = reverse_graph
		self._atom_trace = atom_trace
		self._save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace
		self._canonical = canonical
		self._inconsistency_check = inconsistency_check
		self._store_interpretation_changes = store_interpretation_changes
		self._parallel_computing = parallel_computing
		self._update_mode = update_mode
		self._allow_ground_rules = allow_ground_rules
		self._fp_version = fp_version
		self.interp = None

	def reason(self, tmax, convergence_threshold, convergence_bound_threshold, verbose=True):
		self._tmax = tmax
		# Set up available labels
		Interpretation.specific_node_labels = self.specific_node_labels
		Interpretation.specific_edge_labels = self.specific_edge_labels

		# Instantiate correct interpretation class based on whether we parallelize the code or not. (We cannot parallelize with cache on)
		if self._parallel_computing:
			self.interp = InterpretationParallel(self._graph, self._ipl, self._annotation_functions, self._head_functions, self._reverse_graph, self._atom_trace, self._save_graph_attributes_to_rule_trace, self._canonical, self._inconsistency_check, self._store_interpretation_changes, self._update_mode, self._allow_ground_rules)
		elif self._fp_version:
			self.interp = InterpretationFP(self._graph, self._ipl, self._annotation_functions, self._head_functions, self._reverse_graph, self._atom_trace, self._save_graph_attributes_to_rule_trace, self._canonical, self._inconsistency_check, self._store_interpretation_changes, self._update_mode, self._allow_ground_rules)
		else:
			self.interp = Interpretation(self._graph, self._ipl, self._annotation_functions, self._head_functions, self._reverse_graph, self._atom_trace, self._save_graph_attributes_to_rule_trace, self._canonical, self._inconsistency_check, self._store_interpretation_changes, self._update_mode, self._allow_ground_rules)
		self.interp.start_fp(self._tmax, self._facts_node, self._facts_edge, self._rules, verbose, convergence_threshold, convergence_bound_threshold)

		return self.interp
	
	def reason_again(self, tmax, restart, convergence_threshold, convergence_bound_threshold, facts_node, facts_edge, verbose=True):
		assert self.interp is not None, 'Call reason before calling reason again'
		if restart:
			self._tmax = tmax
		else:
			self._tmax = self.interp.time + tmax
		self.interp.start_fp(self._tmax, facts_node, facts_edge, self._rules, verbose, convergence_threshold, convergence_bound_threshold, again=True, restart=restart)

		return self.interp

	def reset_graph(self):
		self._graph = None
		self.interp = None

	def reset_rules(self):
		self._rules = None

	def reset_facts(self):
		self._facts_node = None
		self._facts_edge = None
