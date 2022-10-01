from mancalog.scripts.interpretation.interpretation import Interpretation


class Program:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = []
	specific_edge_labels = []

	def __init__(self, graph, tmax, facts, rules, ipls):
		self._graph = graph
		self._tmax = tmax
		self._facts = facts
		self._rules = rules
		self._ipls = ipls

	def diffusion(self, history):
		# Set up available labels
		Interpretation.available_labels_node = self.available_labels_node
		Interpretation.available_labels_edge = self.available_labels_edge
		Interpretation.specific_node_labels = self.specific_node_labels
		Interpretation.specific_edge_labels = self.specific_edge_labels

		interp = Interpretation(self._graph, self._tmax, history)
		old_interp = Interpretation(self._graph, self._tmax, history)
		
		interp.apply_facts(self._facts)

		old_interp.copy(interp)
		interp.apply_rules(self._rules, self._facts)

		# This while will be executed until a fixed point is reached
		fp_op_cnt = 0
		while not old_interp == interp:
			fp_op_cnt += self._tmax
			old_interp.copy(interp)
			interp.apply_rules(self._rules, self._facts)

		print('Fixed Point iterations:', fp_op_cnt)
		return interp		
