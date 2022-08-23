import yaml
import numba

# import mancalog.scripts.interval.interval as interval
import mancalog.scripts.numba_wrapper.numba_types.interval_type as interval
import mancalog.scripts.numba_wrapper.numba_types.label_type as label
import mancalog.scripts.numba_wrapper.numba_types.node_type as node
import mancalog.scripts.numba_wrapper.numba_types.rule_type as rule
import mancalog.scripts.numba_wrapper.numba_types.fact_type as fact

# from mancalog.scripts.facts.fact import Fact
# from mancalog.scripts.rules.rule import Rule
# from mancalog.scripts.components.node import Node
# from mancalog.scripts.components.label import Label
from mancalog.scripts.influence_functions.tipping_function import TippingFunction
from mancalog.scripts.influence_functions.sft_tipping_function import SftTippingFunction
from mancalog.scripts.influence_functions.ng_tipping_function import NgTippingFunction


class YAMLParser:

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
            delta_t = values['delta_t']

            # Set neigh_nodes
            neigh_nodes = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['neigh_nodes'] is not None:
                for nn in values['neigh_nodes']:
                    neigh_nodes.append((label.Label(nn[0]), interval.closed(nn[1], nn[2])))

            # Set neigh_edges
            neigh_edges = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['neigh_edges'] is not None:
                for ne in values['neigh_edges']:
                    neigh_edges.append((label.Label(ne[0]), interval.closed(ne[1], ne[2])))

            # Set influence function
            influence = self._get_influence_function(values['influence'])
            
            r = rule.Rule(target, target_criteria_node, target_criteria_edge, delta_t, neigh_nodes, neigh_edges, influence)
            rules.append(r)

        return rules


    def parse_facts(self, path):
        with open(path, 'r') as file:
            facts_yaml = yaml.safe_load(file)

        facts = numba.typed.List()
        for _, values in facts_yaml.items():
            n = node.Node(values['node'])
            l = label.Label(values['label'])
            bound = interval.closed(values['bound'][0], values['bound'][1])
            t_lower = values['t_lower']
            t_upper = values['t_upper']
            f = fact.Fact(n, l, bound, t_lower, t_upper)
            facts.append(f)

        return facts


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

        return node_labels, edge_labels


    def _get_influence_function(self, influence_function):
        f = SftTippingFunction()
        if influence_function == 'tp':
            f._threshold = 0.5
            f._bnd_update = interval.closed(1.0, 1.0)
            return f
        elif influence_function == 'sft_tp':
            return f
        elif influence_function == 'ng_tp':
            f._threshold = 1.0
            f._bnd_update = interval.closed(0.0, 0,2)
            return f
        else:
            raise NotImplementedError(f"The influence function: {influence_function} does not exist or has not yet been implemented. Please enter a known influence function")
    
     