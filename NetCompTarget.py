import portion
from NetDiffGraph import NetDiffGraph
from NetDiffNode import NetDiffNode
from NetDiffEdge import NetDiffEdge

class NetCompTarget:

	def __init__(self, component, label = None, interval = None):
		self._component = component
		self._label = label
		self._interval = interval

	def getBound(self):
		return self._interval

	def getLabel(self):
		return self._label

	def getComponent(self):
		return self._component

	def __str__(self):
		return str(self._component) + '\n' + str(self._label) + '\n' + str(self._interval)