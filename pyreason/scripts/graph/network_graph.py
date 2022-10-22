from pyreason.scripts.components.graph_component import GraphComponent
from networkx import DiGraph

import pyreason.scripts.numba_wrapper.numba_types.node_type as node
import pyreason.scripts.numba_wrapper.numba_types.edge_type as edge


class NetworkGraph(GraphComponent, DiGraph):

	def __init__(self, id, nodes = [], edges = []):
		super().__init__()
		self._id = id
		for n in nodes:
			self.add_node(n)

		for e in edges:
			self.add_edge(e)

	def to_json_string(self):
		result = '{"nodes": ['
		for n in self.nodes:
			result = result + n.to_json_string() + ","
		result = result[: (len(result) - 1)]
		result = result + '], "edges": ['

		for e in self.edges:
			result = result + e["net_diff_edge"].to_json_string() + ","

		result = result[: (len(result) - 1)]
		result = result + ']}'

		return result

	def get_labels(self):
		return NetworkGraph.available_labels

	def get_components(self):
		components = list(self.nodes)
		for e in self.edges:
			net_diff_edge = self.edges[e[0], e[1]]["net_diff_edge"]
			components.append(net_diff_edge)
		
		return components

	def get_nodes(self):
		return list(self.nodes)

	def add_node(self, n):
		net_diff_node = node.Node(n)
		super().add_node(net_diff_node)
	
	def get_edges(self):
		net_diff_edges = []
		for e in self.edges:
			net_diff_edge = self.edges[e[0], e[1]]["net_diff_edge"]
			net_diff_edges.append(net_diff_edge)

		return net_diff_edges

	def add_edge(self, e):
		net_diff_node1 = node.Node(e[0])
		net_diff_node2 = node.Node(e[1])
		net_diff_edge = edge.Edge(e[0], e[1])
		super().add_edges_from([(net_diff_node2, net_diff_node1, {"net_diff_edge": net_diff_edge})])

	def get_id(self):
		return self._id

	def get_type(self):
		return 'graph'

	def __str__(self):
		return self._id

	def __hash__(self):
		return hash(str(self))

