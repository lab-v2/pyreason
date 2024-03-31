import csv
import os
import pandas as pd


class Output:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.rule_trace_node = None
        self.rule_trace_edge = None

    def _parse_internal_rule_trace(self, interpretation):
        header_node = ['Time', 'Fixed-Point-Operation', 'Node', 'Label', 'Old Bound', 'New Bound', 'Occurred Due To']

        # Nodes rule trace
        data = []
        max_j = -1

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
                    if len(qe[j]) == 0:
                        # Node clause
                        row.append(list(qn[j]))
                    elif len(qn[j]) == 0:
                        # Edge clause
                        row.append(list(qe[j]))

            data.append(row)

        # Add Clause-num to header
        if interpretation.atom_trace and max_j != -1:
            for i in range(1, max_j + 2):
                header_node.append(f'Clause-{i}')

        # Store the trace in a DataFrame
        self.rule_trace_node = pd.DataFrame(data, columns=header_node)

        header_edge = ['Time', 'Fixed-Point-Operation', 'Edge', 'Label', 'Old Bound', 'New Bound', 'Occurred Due To']

        # Edges rule trace
        data = []
        max_j = -1

        for i, r in enumerate(interpretation.rule_trace_edge):
            row = [r[0], r[1], r[2], r[3]._value, '-', r[4].to_str(), '-']
            if interpretation.atom_trace:
                qn, qe, old_bnd, name = interpretation.rule_trace_edge_atoms[i]
                row[4] = old_bnd.to_str()
                # Go through all the changes in the rule trace
                # len(qn) = num of clauses in rule that was used
                row[6] = name

                # Go through each clause
                for j in range(len(qn)):
                    max_j = max(j, max_j)
                    if len(qe[j]) == 0:
                        # Node clause
                        row.append(list(qn[j]))
                    elif len(qn[j]) == 0:
                        # Edge clause
                        row.append(list(qe[j]))

            data.append(row)

        # Add Clause-num to header
        if interpretation.atom_trace and max_j != -1:
            for i in range(1, max_j + 2):
                header_edge.append(f'Clause-{i}')

        # Store the trace in a DataFrame
        self.rule_trace_edge = pd.DataFrame(data, columns=header_edge)

    def save_rule_trace(self, interpretation, folder='./'):
        if self.rule_trace_node is None and self.rule_trace_edge is None:
            self._parse_internal_rule_trace(interpretation)

        path_nodes = os.path.join(folder, f'rule_trace_nodes_{self.timestamp}.csv')
        path_edges = os.path.join(folder, f'rule_trace_edges_{self.timestamp}.csv')
        self.rule_trace_node.to_csv(path_nodes, index=False)
        self.rule_trace_edge.to_csv(path_edges, index=False)

    def get_rule_trace(self, interpretation):
        if self.rule_trace_node is None and self.rule_trace_edge is None:
            self._parse_internal_rule_trace(interpretation)

        return self.rule_trace_node, self.rule_trace_edge
