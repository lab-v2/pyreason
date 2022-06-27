from mancalog.scripts.interpretation.interpretation import Interpretation


class Program:

	def __init__(self, net_diff_graph, tmax, facts = [], local_rules = [], global_rules = []):
		self._net_diff_graph = net_diff_graph
		self._tmax = tmax
		self._facts = facts
		self._local_rules = local_rules
		self._global_rules = global_rules
		self._interp = None

	def diffusion(self):
		self._interp = Interpretation(self._net_diff_graph, self._tmax)
		old_interp = Interpretation(self._net_diff_graph, self._tmax)
		
		self._interp.apply_facts(self._facts)

		old_interp.copy(self._interp)
		self._interp.apply_local_rules(self._local_rules)

		#this while will be executed until a fixed point is reached
		while not old_interp == self._interp:
			old_interp.copy(self._interp)
			self._interp.apply_local_rules(self._local_rules)

		#global rules are not necessary for classic MANCaLog , I have used them in a MANCaLog extension
		for t in range(self._tmax + 1):
			for rule in self._global_rules:
				self._interp.apply_global_rule(rule, t)

		return self._interp		
