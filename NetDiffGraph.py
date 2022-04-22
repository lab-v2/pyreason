from NetDiffNode import NetDiffNode
from NetDiffEdge import NetDiffEdge
from NetDiffGraphElement import NetDiffGraphElement
from networkx import Graph

class NetDiffGraph(NetDiffGraphElement, Graph):

	def __init__(self, id, nodes = [], edges = []):
		super().__init__()
		self._id = id
		for node in nodes:
			self.add_node(node)

		for edge in edges:
			self.add_edge(edge)

	def to_json_string(self):
		result = '{"nodes": ['
		for node in self.nodes:
			result = result + node.to_json_string() + ","
		result = result[: (len(result) - 1)]
		result = result + '], "edges": ['

		for edge in self.edges:
			result = result + edge["net_diff_edge"].to_json_string() + ","

		result = result[: (len(result) - 1)]
		result = result + ']}'

		return result

	def get_labels(self):
		return NetDiffGraph._labels

	def get_components(self):
		components = list(self.nodes)
		for edge in self.edges:
			net_diff_edge = self.edges[edge[0], edge[1]]["net_diff_edge"]
			components.append(net_diff_edge)
		
		return components

	def getNodes(self):
		return list(self.nodes)

	def add_node(self, node):
		net_diff_node = NetDiffNode(node)
		super().add_node(net_diff_node)
	
	def getEdges(self):
		net_diff_edges = []
		for edge in self.edges:
			net_diff_edge = self.edges[edge[0], edge[1]]["net_diff_edge"]
			net_diff_edges.append(net_diff_edge)

		return net_diff_edges

	def add_edge(self, edge):
		net_diff_node1 = NetDiffNode(edge[0])
		net_diff_node2 = NetDiffNode(edge[1])
		net_diff_edge = NetDiffEdge(edge[0], edge[1])
		super().add_edges_from([(net_diff_node1, net_diff_node2, {"net_diff_edge": net_diff_edge})])

	def getId(self):
		return self._id

	def __str__(self):
		return self._id

	def __hash__(self):
		return hash(str(self))

