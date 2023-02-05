import pickle
import csv
import os

class Output:
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def pickle_rule_trace(self, interpretation):
        # Pickle rule trace
        # DOES NOT WORK!!
        with open(f'./output/{self.timestamp}_rule_trace_nodes.pkl', 'wb') as file:
            pickle.dump(interpretation.rule_trace_node, file)
        with open(f'./output/{self.timestamp}_rule_trace_edges.pkl', 'wb') as file:
            pickle.dump(interpretation.rule_trace_edge, file)

    def pickle_list_of_inconsistencies(self, interpretation):
        with open(f'./output/{self.timestamp}_inconsistencies.pkl', 'wb') as file:
            pickle.dump(interpretation.inconsistencies, file)

    def pickle_interpretations(self, interpretation):
        # DOES NOT WORK!!
        # Warning! This could be very time and memory consuming for large graphs. Rule trace pickle is recommended
        with open(f'./output/{self.timestamp}_interpreations_node.pkl', 'wb') as file:
            pickle.dump(interpretation.interpretations_node, file)
        with open(f'./output/{self.timestamp}_interpreations_edge.pkl', 'wb') as file:
            pickle.dump(interpretation.interpretations_edge, file)

    def save_rule_trace(self, interpretation, folder='./'):
        # Saves the rule trace in a csv, human readable format
        header = ['Time', 'Fixed-Point-Operation', 'Node', 'Label', 'Old Bound', 'New Bound', 'Occurred Due To']

        # Nodes rule trace
        path = os.path.join(folder, f'rule_trace_nodes_{self.timestamp}.csv')
        with open(path, 'w') as f:
            data = []
            max_j = 0

            for i, r in enumerate(interpretation.rule_trace_node):
                row = [r[0], r[1], r[2], r[3]._value, '-', r[4].to_str(), '-']
                if interpretation.atom_trace:
                    qn, qe, old_bnd, name = interpretation.rule_trace_node_atoms[i]
                    row[4] = old_bnd.to_str()
                    # Go through all the changes in the rule trace
                    # len(qn) = len(qe) = num of clauses in rule that was used
                    row[6] = name

                    # Go through each clause
                    for j in range(len(qn)):
                        max_j = max(j, max_j)
                        if len(qe[j])==0:
                            # Node clause
                            row.append(list(qn[j]))
                        elif len(qn[j])==0:
                            # Edge clause
                            row.append(list(qe[j]))

                data.append(row)

            # Add Clause-num to header
            if interpretation.atom_trace:
                for i in range(1, max_j+2):
                    header.append(f'Clause-{i}')

            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
            


