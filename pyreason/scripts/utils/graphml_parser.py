import networkx as nx
import numba

import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


class GraphmlParser:
    def __init__(self):
        self.graph = None
        self.non_fluent_facts = None

    def parse_graph(self,
                    graph_path: str,
                    reverse: bool):
        self.graph = nx.read_graphml(graph_path)
        if reverse:
            self.graph = self.graph.reverse()

        return self.graph

    def parse_graph_attributes(self,
                               graph_attribute_parsing: bool) -> (numba.typed.List, numba.typed.List,
                                                                  numba.typed.Dict, numba.typed.Dict):
        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type,
                                                      value_type=numba.types.ListType(numba.types.string))
        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type,
                                                      value_type=numba.types.ListType(numba.types.Tuple((
                                                          numba.types.string, numba.types.string))))

        if graph_attribute_parsing:
            for n in self.graph.nodes:
                for key, value in self.graph.nodes[n].items():
                    # IF attribute is a float or int, and it is less than 1, then make it a bound, else make it a label
                    if isinstance(value, (float, int)) and 1 >= value >= 0:
                        l = str(key)
                        l_bnd = float(value)
                    else:
                        l = l = f'{key}-{value}'
                        l_bnd = 1

                    if label.Label(l) not in specific_node_labels.keys():
                        specific_node_labels[label.Label(l)] = numba.typed.List.empty_list(numba.types.string)

                    specific_node_labels[label.Label(l)].append(n)
                    f = fact_node.Fact(name='graph-attribute-fact',
                                       component=n,
                                       label=label.Label(l),
                                       interval=interval.closed(l_bnd, 1),
                                       t_lower=0,
                                       t_upper=0,
                                       static=True)
                    facts_node.append(f)

            for e in self.graph.edges:
                for key, value in self.graph.edges[e].items():
                    # IF attribute is a float or int and it is less than 1, then make it a bound, else make it a label
                    if isinstance(value, (float, int)) and 1 >= value >= 0:
                        l = str(key)
                        l_bnd = float(value)
                    else:
                        l = l = f'{key}-{value}'
                        l_bnd = 1

                    if label.Label(l) not in specific_edge_labels.keys():
                        specific_edge_labels[label.Label(l)] = numba.typed.List.empty_list(numba.types.Tuple((
                            numba.types.string, numba.types.string)))
                    specific_edge_labels[label.Label(l)].append((e[0], e[1]))
                    f = fact_edge.Fact(name='graph-attribute-fact',
                                       component=(e[0], e[1]),
                                       label=label.Label(l),
                                       interval=interval.closed(l_bnd, 1),
                                       t_lower=0,
                                       t_upper=0,
                                       static=True)
                    facts_edge.append(f)

        return facts_node, facts_edge, specific_node_labels, specific_edge_labels
