import networkx as nx
import numba
import warnings     # <-- warnings.warn()

import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.utils.fact_parser import _PREDICATE_RE, _COMPONENT_RE


class GraphmlParser:
    def __init__(self):
        self.graph = None
        self.non_fluent_facts = None

    def parse_graph(self, graph_path, reverse):
        self.graph = nx.read_graphml(graph_path)
        self.graph = nx.DiGraph(self.graph)
        if reverse:
            self.graph = self.graph.reverse()

        return self.graph

    def load_graph(self, graph):
        self.graph = nx.DiGraph(graph)
        return self.graph

    def parse_graph_attributes(self, static_facts):
        # init statements are to initializations. equivalent to [], {}, just in numba ()
        # PyReason's reasoner is JIT compiled with numba, so we need to use numba's typed lists and dicts to store the facts and labels.
        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))

        # n goes over every node added to the graph
        for n in self.graph.nodes:
            # validate node ID n
            if not _COMPONENT_RE.match(str(n)):
                warnings.warn(f"Skipping all attributes on Node ID {n!r}: does not match expected pattern")
                continue

            for key, value in self.graph.nodes[n].items():
                # check for empty values
                if not str(key).strip() or (isinstance(value, str) and not value.strip()):
                    warnings.warn(f"Skipping attribute {key!r} on node {n!r}: key and value must be non-empty")
                    continue

                # validate attribute key
                if not _PREDICATE_RE.match(str(key)):
                    warnings.warn(f"Skipping attribute {key!r} on node {n!r}: attribute key is not a valid predicate name")
                    continue

                # IF attribute is a float or int and it is less than 1, then make it a bound, else make it a label
                # check if added node has bounds or not --> if it has bounds, add them; if not, add it with bounds [1, 1]
                if (isinstance(value, (float, int)) and 1 >= value >= 0) or (
                        isinstance(value, str) and value.replace('.', '').isdigit() and 1 >= float(value) >= 0):
                    label_str = str(key)
                    lower_bnd = float(value)
                    upper_bnd = 1
                # bound is singular. could be: string of a numeric out of range, numeric out of range, or non-numeric string
                else:
                    # not numeric in [0,1] — figure out which sub-case
                    if isinstance(value, str):
                        # could be a numeric string out of range, OR a genuine non-numeric string
                        try:
                            parsed = float(value)
                            # parses as a number, but failed the in-range check above
                            warnings.warn(f"Skipping attribute {key!r} on node {n!r}: numeric value {parsed} is out of range [0, 1]")
                            continue
                        except ValueError:
                            # genuine non-numeric string --> categorical
                            label_str = f'{key}-{value}'
                            lower_bnd = 1
                            upper_bnd = 1
                    else:
                        # numeric type out of [0, 1], or unsupported type entirely
                        warnings.warn(f"Skipping attribute {key!r} on node {n!r}: value {value!r} is not a valid bound")
                        continue
                # use gave both bounds explicitly as a string separated by a comma, so split and use those as bounds instead of the default ones
                if isinstance(value, str):
                    bnd_str = value.split(',')
                    if len(bnd_str) == 2:
                        try:
                            low = float(bnd_str[0])   
                            up = float(bnd_str[1])   
                        except ValueError:
                            warnings.warn(f"Skipping attribute {key!r} on node {n!r}: interval values not parseable as floats")
                            continue 
                        if 1 >= low >= 0 and 1 >= up >= 0 and low <= up: 
                            lower_bnd = low
                            upper_bnd = up
                            label_str = str(key)
                        else:
                            warnings.warn(f"Skipping attribute {key!r} on node {n!r}: interval bounds [{low}, {up}] must be in [0, 1] with lower <= upper")
                            continue
                # wait to check label_str until after the rewrite 
                if not _PREDICATE_RE.match(label_str):
                    warnings.warn(f"Skipping attribute {key!r} on node {n!r}: combined label {label_str!r} does not match expected pattern")
                    continue

                # check if the label exists within the nodes processed
                if label.Label(label_str) not in specific_node_labels.keys():
                    specific_node_labels[label.Label(label_str)] = numba.typed.List.empty_list(numba.types.string)
                # record that the node n has this label
                specific_node_labels[label.Label(label_str)].append(n)
                # build a Fact object (not added to graph)
                f = fact_node.Fact('graph-attribute-fact', n, label.Label(label_str), interval.closed(lower_bnd, upper_bnd), 0, 0, static=static_facts)
                # append fact to list of all node facts
                facts_node.append(f)
        
        # e goes over every edge in the graph
        for e in self.graph.edges:
            # validate both endpoints of the edge
            if not _COMPONENT_RE.match(str(e[0])) or not _COMPONENT_RE.match(str(e[1])):
                warnings.warn(f"Skipping all attributes on Edge ID {e!r}: does not match expected pattern")
                continue

            for key, value in self.graph.edges[e].items():
                # check for empty values
                if not str(key).strip() or (isinstance(value, str) and not value.strip()):
                    warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: key and value must be non-empty")
                    continue

                # validate attribute key
                if not _PREDICATE_RE.match(str(key)):
                    warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: attribute key is not a valid predicate name")
                    continue
                
                # IF attribute is a float or int and it is less than 1, then make it a bound, else make it a label
                if (isinstance(value, (float, int)) and 1 >= value >= 0) or (
                        isinstance(value, str) and value.replace('.', '').isdigit() and 1 >= float(value) >= 0):
                    label_str = str(key)
                    lower_bnd = float(value)
                    upper_bnd = 1
                else:
                    if isinstance(value, str):
                        # could be a numeric string out of range, OR a genuine non-numeric string
                        try:
                            parsed = float(value)
                            warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: numeric value {parsed} is out of range [0, 1]")
                            continue
                        except ValueError:
                            # genuine non-numeric string --> categorical
                            label_str = f'{key}-{value}'
                            lower_bnd = 1
                            upper_bnd = 1
                    else:
                        # numeric type out of [0, 1], or unsupported type entirely
                        warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: value {value!r} is not a valid bound")
                        continue
                if isinstance(value, str):
                    bnd_str = value.split(',')
                    if len(bnd_str) == 2:
                        try:
                            low = float(bnd_str[0])
                            up = float(bnd_str[1])
                        except ValueError:
                            warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: interval values not parseable as floats")
                            continue 
                        if 1 >= low >= 0 and 1 >= up >= 0 and low <= up:
                            lower_bnd = low
                            upper_bnd = up
                            label_str = str(key)
                        else:
                            warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: interval bounds [{low}, {up}] must be in [0, 1] with lower <= upper")
                            continue
                # wait to check label_str until after the rewrite 
                if not _PREDICATE_RE.match(label_str):
                    warnings.warn(f"Skipping attribute {key!r} on edge {e!r}: combined label {label_str!r} does not match expected pattern")
                    continue

                if label.Label(label_str) not in specific_edge_labels.keys():
                    specific_edge_labels[label.Label(label_str)] = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.string)))
                specific_edge_labels[label.Label(label_str)].append((e[0], e[1]))
                f = fact_edge.Fact('graph-attribute-fact', (e[0], e[1]), label.Label(label_str), interval.closed(lower_bnd, upper_bnd), 0, 0, static=static_facts)
                facts_edge.append(f)
        
        print("Added ", len(facts_node), "graph-attribute node facts and ", len(facts_edge), "graph_attribute edge facts.")
        return facts_node, facts_edge, specific_node_labels, specific_edge_labels
