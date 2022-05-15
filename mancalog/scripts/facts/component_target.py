import portion
from mancalog.scripts.graph.network_graph import Graph
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge


class ComponentTarget:
	
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