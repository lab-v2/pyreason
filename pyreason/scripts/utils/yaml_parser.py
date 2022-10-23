import yaml
import numba

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.node_type as node
import pyreason.scripts.numba_wrapper.numba_types.edge_type as edge
import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge

from pyreason.scripts.influence_functions.tipping_function import TippingFunction
from pyreason.scripts.influence_functions.sft_tipping_function import SftTippingFunction
from pyreason.scripts.influence_functions.ng_tipping_function import NgTippingFunction


class YAMLParser:
    def __init__(self, tmax):
        self.tmax = tmax

    def parse_rules(self, path):
        with open(path, 'r') as file:
            rules_yaml = yaml.safe_load(file)

        rules = numba.typed.List()
        # rules = []
        for _, values in rules_yaml.items():

            # Set rule target
            target = label.Label(values['target'])
            
            # Set rule target criteria (for node labels)
            target_criteria_node = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['target_criteria_node'] is not None:
                for tc in values['target_criteria_node']:
                    target_criteria_node.append((label.Label(tc[0]), interval.closed(tc[1], tc[2])))
            
            # Set rule target criteria (for edge labels)
            target_criteria_edge = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['target_criteria_edge'] is not None:
                for tc in values['target_criteria_edge']:
                    target_criteria_edge.append((label.Label(tc[0]), interval.closed(tc[1], tc[2])))

            # Set delta t
            delta_t = numba.types.int8(values['delta_t'])

            # Array of thresholds to keep track of for each neighbor criterion. Form [(comparison, number/percent, thresh)]
            thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.string, numba.types.float64)))

            # Set neigh_nodes
            neigh_nodes = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['neigh_nodes'] is not None:
                for nn in values['neigh_nodes']:
                    neigh_nodes.append((label.Label(nn[0]), interval.closed(nn[1][0], nn[1][1])))
                    thresholds.append((nn[2][0], nn[2][1], nn[2][2]))

            # Set neigh_edges
            neigh_edges = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['neigh_edges'] is not None:
                for ne in values['neigh_edges']:
                    neigh_edges.append((label.Label(ne[0]), interval.closed(ne[1][0], ne[1][1])))
                    thresholds.append((ne[2][0], ne[2][1], ne[2][2]))
            
            inf = values['ann_fn']

            r = rule.Rule(target, target_criteria_node, target_criteria_edge, delta_t, neigh_nodes, neigh_edges, inf, thresholds)
            rules.append(r)

        return rules


    def parse_facts(self, path):
        with open(path, 'r') as file:
            facts_yaml = yaml.safe_load(file)

        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        if facts_yaml['nodes'] is not None:
            for _, values in facts_yaml['nodes'].items():
                n = node.Node(str(values['node']))
                l = label.Label(values['label'])
                bound = interval.closed(values['bound'][0], values['bound'][1])
                if values['static']:
                    static = True
                    t_lower = 0
                    t_upper = self.tmax
                else:
                    static = False
                    t_lower = values['t_lower']
                    t_upper = values['t_upper']
                f = fact_node.Fact(n, l, bound, t_lower, t_upper, static)
                facts_node.append(f)

        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        if facts_yaml['edges'] is not None:
            for _, values in facts_yaml['edges'].items():
                e = edge.Edge(str(values['source']), str(values['target']))
                l = label.Label(values['label'])
                bound = interval.closed(values['bound'][0], values['bound'][1])
                t_lower = values['t_lower']
                t_upper = values['t_upper']
                f = fact_edge.Fact(e, l, bound, t_lower, t_upper)
                facts_edge.append(f)

        return facts_node, facts_edge


    def parse_labels(self, path):
        with open(path, 'r') as file:
            labels_yaml = yaml.safe_load(file)

        node_labels = []
        edge_labels = []
        for label_name in labels_yaml['node_labels']:
            l = label.Label(label_name)
            node_labels.append(l)

        for label_name in labels_yaml['edge_labels']:
            l = label.Label(label_name)
            edge_labels.append(l)

        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(node.node_type))
        for label_name in labels_yaml['node_specific_labels']:
            l = label.Label(label_name)
            specific_node_labels[l] = numba.typed.List.empty_list(node.node_type)
            for n in labels_yaml['node_specific_labels'][label_name]:
                specific_node_labels[l].append(node.Node(str(n)))

        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(edge.edge_type))
        for label_name in labels_yaml['edge_specific_labels']:
            l = label.Label(label_name)
            specific_edge_labels[l] = numba.typed.List.empty_list(edge.edge_type)
            for e in labels_yaml['edge_specific_labels'][label_name]:
                specific_edge_labels[l].append(edge.Edge(str(e[0]), str(e[1])))


        return node_labels, edge_labels, specific_node_labels, specific_edge_labels

    def parse_ipl(self, path):
        with open(path, 'r') as file:
            ipl_yaml = yaml.safe_load(file)

        ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))
        if ipl_yaml['ipl'] is not None:
            for labels in ipl_yaml['ipl']:
                ipl.append((label.Label(labels[0]), label.Label(labels[1])))

        return ipl


    def _get_influence_function(self, influence_function, threshold):
        f = SftTippingFunction()
        if influence_function == 'tp':
            f._threshold = 0.5
            f._bnd_update = interval.closed(1.0, 1.0)
            return f
        elif influence_function == 'sft_tp':
            f._threshold = threshold
            return f
        elif influence_function == 'ng_tp':
            f._threshold = 1.0
            f._bnd_update = interval.closed(0.0, 0,2)
            return f
        else:
            raise NotImplementedError(f"The influence function: {influence_function} does not exist or has not yet been implemented. Please enter a known influence function")
    
     