
class NetDiffGlobalRule:

	def __init__(self, global_label, local_label, local_target, aggregation):
		self._glabel = global_label
		self._llabel = local_label
		self._ltarget = local_target
		self._aggregation = aggregation

	def getGlobalLabel(self):
		return self._glabel

	def getLocalLabel(self):
		return self._llabel

	def getLocalTarget(self):
		return self._ltarget

	def getAggregation(self):
		return self._aggregation

	def aggregate(self, bounds):
		return self._aggregation.aggregate(bounds)
