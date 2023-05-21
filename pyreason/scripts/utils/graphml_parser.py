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
        
    def parse_graph(self, graph_path, reverse):
        self.graph = nx.read_graphml(graph_path)
        if reverse:
            self.graph = self.graph.reverse()

        return self.graph

    def parse_graph_attributes(self, static_facts):
        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))
        for n in self.graph.nodes:
            for key, value in self.graph.nodes[n].items():
                # IF attribute is a float or int and it is less than 1, then make it a bound, else make it a label
                if isinstance(value, (float, int)) and value<=1 and value>=0:
                    l = str(key)
                    l_bnd = float(value)
                    u_bnd = 1
                else:
                    l = f'{key}-{value}'
                    l_bnd = 1
                    u_bnd = 1
                if isinstance(value, str):
                    bnd_str = value.split(',')
                    if len(bnd_str)==2:
                        try:
                            low = int(bnd_str[0])
                            up = int(bnd_str[1])
                            if low<=1 and low>=0 and up<=1 and up>=0:
                                l_bnd = low
                                u_bnd = up
                                l = str(key)
                        except:
                            pass
                
                if label.Label(l) not in specific_node_labels.keys():
                    specific_node_labels[label.Label(l)] = numba.typed.List.empty_list(numba.types.string)
                specific_node_labels[label.Label(l)].append(n)
                f = fact_node.Fact('graph-attribute-fact', n, label.Label(l), interval.closed(l_bnd, u_bnd), 0, 0, static=static_facts)
                facts_node.append(f)
        for e in self.graph.edges:
            for key, value in self.graph.edges[e].items():
                # IF attribute is a float or int and it is less than 1, then make it a bound, else make it a label
                if isinstance(value, (float, int)) and value<=1 and value>=0:
                    l = str(key)
                    l_bnd = float(value)
                    u_bnd = 1
                else:
                    l = f'{key}-{value}'
                    l_bnd = 1
                    u_bnd = 1
                if isinstance(value, str):
                    bnd_str = value.split(',')
                    if len(bnd_str)==2:
                        try:
                            low = int(bnd_str[0])
                            up = int(bnd_str[1])
                            if low<=1 and low>=0 and up<=1 and up>=0:
                                l_bnd = low
                                u_bnd = up
                                l = str(key)
                        except:
                            pass

                if label.Label(l) not in specific_edge_labels.keys():
                    specific_edge_labels[label.Label(l)] = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.string)))
                specific_edge_labels[label.Label(l)].append((e[0], e[1]))
                f = fact_edge.Fact('graph-attribute-fact', (e[0], e[1]), label.Label(l), interval.closed(l_bnd, u_bnd), 0, 0, static=static_facts)
                facts_edge.append(f)

        return facts_node, facts_edge, specific_node_labels, specific_edge_labels                
