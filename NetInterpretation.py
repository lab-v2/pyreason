from NetDiffWorld import NetDiffWorld

class NetInterpretation:

	def __init__(self, net_diff_graph, labels):
		self._nas = []
		for comp in net_diff_graph.get_components():
			self._nas.add((comp, NetDiffWorld(labels)))
		