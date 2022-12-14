import yaml
import numba
import numpy as np

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge


class YAMLParser:
    def __init__(self, tmax):
        self.tmax = tmax

    def parse_rules(self, path):
        with open(path, 'r') as file:
            rules_yaml = yaml.safe_load(file)

        rules = numba.typed.List.empty_list(rule.rule_type)
        for _, values in rules_yaml.items():

            # Set rule target
            target = label.Label(values['target'])
            
            # Set rule target criteria
            target_criteria = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, interval.interval_type)))
            if values['target_criteria'] is not None:
                for tc in values['target_criteria']:
                    target_criteria.append((label.Label(tc[0]), interval.closed(tc[1], tc[2])))

            # Set delta t
            delta_t = numba.types.int8(values['delta_t'])

            # neigh_criteria = [c1, c2, c3, c4]
            # thresholds = [t1, t2, t3, t4]
           
            # Array of thresholds to keep track of for each neighbor criterion. Form [(comparison, (number/percent, total/available), thresh)]
            thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64)))

            # Array to store clauses for nodes: node/edge, [subset]/[subset1, subset2], label, interval
            neigh_criteria = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), label.label_type, interval.interval_type)))
            if values['neigh_criteria'] is not None:
                # Loop through clauses
                for clause in values['neigh_criteria']:

                    # Append clause
                    clause_type = clause[0]
                    subset = (clause[1][0], clause[1][0]) if clause_type=='node' else (clause[1][0], clause[1][1])
                    l = label.Label(clause[2])
                    bnd = interval.closed(clause[3][0], clause[3][1])
                    neigh_criteria.append((clause_type, subset, l, bnd))

                    # Append threshold corresponding to clause
                    quantifier = clause[4][0]
                    if clause[4][1]=='number':
                        quantifier_type = ('number', 'total')
                    else:
                        quantifier_type = ('percent', clause[4][1][1])
                    thresh = clause[4][2]
                    thresholds.append((quantifier, quantifier_type, thresh))
            
            # If annotation function is a string, it is the name of the function. If it is a bound then set it to an empty string
            ann_fn = values['ann_fn']
            if isinstance(ann_fn, str):
                bnd = interval.closed(0, 1)
                subset = (values['subset_label'][0][0], values['subset_label'][0][0]) if len(values['subset_label'][0])==1 else (values['subset_label'][0][0], values['subset_label'][0][1])
                l = label.Label(values['subset_label'][1])
            elif isinstance(ann_fn, list):
                bnd = interval.closed(ann_fn[0], ann_fn[1])
                ann_fn = ''
                subset = ('', '')
                l = label.Label('')

            # If there are weights provided, store them
            # weights = np.array([1,2,3], dtype=np.float64, ndim=1)
            weights = np.ones(len(values['neigh_criteria']), dtype=np.float64)
            weights = np.append(weights, 0)
            if 'weights' in values and not values['weights']:
                weights = np.array(values['weights'], dtype=np.float64)   

            r = rule.Rule(target, target_criteria, delta_t, neigh_criteria, ann_fn, bnd, thresholds, subset, l, weights)
            rules.append(r)

        return rules


    def parse_facts(self, path, reverse):
        with open(path, 'r') as file:
            facts_yaml = yaml.safe_load(file)

        facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        if facts_yaml['nodes'] is not None:
            for _, values in facts_yaml['nodes'].items():
                n = str(values['node'])
                l = label.Label(values['label'])
                bound = interval.closed(values['bound'][0], values['bound'][1])
                if values['static']:
                    static = True
                    t_lower = 0
                    t_upper = 0
                else:
                    static = False
                    t_lower = values['t_lower']
                    t_upper = values['t_upper']
                f = fact_node.Fact(n, l, bound, t_lower, t_upper, static)
                facts_node.append(f)

        facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        if facts_yaml['edges'] is not None:
            for _, values in facts_yaml['edges'].items():
                e = (str(values['source']), str(values['target'])) if not reverse else (str(values['target']), str(values['source']))
                l = label.Label(values['label'])
                bound = interval.closed(values['bound'][0], values['bound'][1])
                if values['static']:
                    static = True
                    t_lower = 0
                    t_upper = 0
                else:
                    static = False
                    t_lower = values['t_lower']
                    t_upper = values['t_upper']
                f = fact_edge.Fact(e, l, bound, t_lower, t_upper, static)
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

        # Add an edge label for each edge
        edge_labels.append(label.Label('edge'))

        specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        for label_name in labels_yaml['node_specific_labels']:
            l = label.Label(label_name)
            specific_node_labels[l] = numba.typed.List.empty_list(numba.types.string)
            for n in labels_yaml['node_specific_labels'][label_name]:
                specific_node_labels[l].append(str(n))

        specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))
        for label_name in labels_yaml['edge_specific_labels']:
            l = label.Label(label_name)
            specific_edge_labels[l] = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.string)))
            for e in labels_yaml['edge_specific_labels'][label_name]:
                specific_edge_labels[l].append((str(e[0]), str(e[1])))


        return node_labels, edge_labels, specific_node_labels, specific_edge_labels

    def parse_ipl(self, path):
        with open(path, 'r') as file:
            ipl_yaml = yaml.safe_load(file)

        ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))
        if ipl_yaml['ipl'] is not None:
            for labels in ipl_yaml['ipl']:
                ipl.append((label.Label(labels[0]), label.Label(labels[1])))

        return ipl
