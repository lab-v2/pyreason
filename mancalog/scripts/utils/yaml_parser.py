from ast import Raise
import portion
import yaml
from mancalog.scripts.facts.fact import Fact

from mancalog.scripts.rules.rule import Rule
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.label import Label
from mancalog.scripts.influence_functions.tipping_function import TippingFunction
from mancalog.scripts.influence_functions.sft_tipping_function import SftTippingFunction
from mancalog.scripts.influence_functions.ng_tipping_function import NgTippingFunction


class YAMLParser:

    def parse_rules(self, path):
        with open(path, 'r') as file:
            rules_yaml = yaml.safe_load(file)

        rules = []
        for _, values in rules_yaml.items():

            # Set rule target
            target = Label(values['target'])
            
            # Set rule target criteria
            target_criteria = None
            if values['target_criteria'] is not None:
                target_criteria = []
                for tc in values['target_criteria']:
                    target_criteria.append((Label(tc[0]), portion.closed(tc[1], tc[2])))

            # Set delta t
            delta_t = values['delta_t']

            # Set neigh_nodes
            neigh_nodes = None
            if values['neigh_nodes'] is not None:
                neigh_nodes = []
                for nn in values['neigh_nodes']:
                    neigh_nodes.append((Label(nn[0]), portion.closed(nn[1], nn[2])))

            # Set neigh_edges
            neigh_edges = None
            if values['neigh_edges'] is not None:
                neigh_edges = []
                for ne in values['neigh_edges']:
                    neigh_edges.append((Label(ne[0]), portion.closed(ne[1], ne[2])))

            # Set influence function
            influence = self._get_influence_function(values['influence'])
            
            rule = Rule(target, target_criteria, delta_t, neigh_nodes, neigh_edges, influence)
            rules.append(rule)

        return rules


    def parse_facts(self, path):
        with open(path, 'r') as file:
            facts_yaml = yaml.safe_load(file)

        facts = []
        for _, values in facts_yaml.items():
            node = Node(values['node'])
            label = Label(values['label'])
            bound = portion.closed(values['bound'][0], values['bound'][1])
            t_lower = values['t_lower']
            t_upper = values['t_upper']
            fact = Fact(node, label, bound, t_lower, t_upper)
            facts.append(fact)

        return facts


    def parse_labels(self, path):
        with open(path, 'r') as file:
            labels_yaml = yaml.safe_load(file)

        labels = []
        for _, values in labels_yaml.items():
            for l in values:
                label = Label(l)
                labels.append(label)

        return labels


    def _get_influence_function(self, influence_function):
        if influence_function == 'tp':
            return TippingFunction()
        elif influence_function == 'sft_tp':
            return SftTippingFunction()
        elif influence_function == 'ng_tp':
            return NgTippingFunction()
        else:
            raise NotImplementedError(f"The influence function: {influence_function} does not exist or has not yet been implemented. Please enter a known influence function")
    
     