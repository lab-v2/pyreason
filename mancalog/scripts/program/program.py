from mancalog.scripts.interpretation.interpretation import Interpretation


class Program:
	available_labels_node = []
	available_labels_edge = []
	specific_node_labels = []
	specific_edge_labels = []

	def __init__(self, net_diff_graph, tmax, facts, rules, ipls):
		self._net_diff_graph = net_diff_graph
		self._tmax = tmax
		self._facts = facts
		self._rules = rules
		self._ipls = ipls
		self._interp = None

	def diffusion(self, history):
		# Set up available labels
		Interpretation.available_labels_node = self.available_labels_node
		Interpretation.available_labels_edge = self.available_labels_edge
		Interpretation.specific_node_labels = self.specific_node_labels
		Interpretation.specific_edge_labels = self.specific_edge_labels

		self._interp = Interpretation(self._net_diff_graph, self._tmax, history)
		old_interp = Interpretation(self._net_diff_graph, self._tmax, history)
		
		self._interp.apply_facts(self._facts)

		old_interp.copy(self._interp)
		self._interp.apply_rules(self._rules, self._facts)

		#this while will be executed until a fixed point is reached
		fp_op_cnt = 1
		print('Fixed Point iteration:', fp_op_cnt)
		while not old_interp == self._interp:
			fp_op_cnt += 1
			old_interp.copy(self._interp)
			self._interp.apply_rules(self._rules, self._facts)
			print('Fixed Point iteration:', fp_op_cnt)

		return self._interp		
