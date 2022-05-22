from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.components.graph_component import GraphComponent
from networkx import Graph


class NetworkGraph(GraphComponent, Graph):

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
		return NetworkGraph.available_labels

	def get_components(self):
		components = list(self.nodes)
		for edge in self.edges:
			net_diff_edge = self.edges[edge[0], edge[1]]["net_diff_edge"]
			components.append(net_diff_edge)
		
		return components

	def get_nodes(self):
		return list(self.nodes)

	def add_node(self, node):
		net_diff_node = Node(node)
		super().add_node(net_diff_node)
	
	def get_edges(self):
		net_diff_edges = []
		for edge in self.edges:
			net_diff_edge = self.edges[edge[0], edge[1]]["net_diff_edge"]
			net_diff_edges.append(net_diff_edge)

		return net_diff_edges

	def add_edge(self, edge):
		net_diff_node1 = Node(edge[0])
		net_diff_node2 = Node(edge[1])
		net_diff_edge = Edge(edge[0], edge[1])
		super().add_edges_from([(net_diff_node1, net_diff_node2, {"net_diff_edge": net_diff_edge})])

	def get_id(self):
		return self._id

	def __str__(self):
		return self._id

	def __hash__(self):
		return hash(str(self))

