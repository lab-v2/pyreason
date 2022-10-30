import pickle

class Output:
    def __init__(self, timesteps, timestamp):
        self.timesteps = timesteps
        self.timestamp = timestamp

    def pickle_rule_trace(self, interpretation):
        # Pickle rule trace
        with open(f'./output/{self.timestamp}_rule_trace_nodes.pkl', 'wb') as file:
            pickle.dump(interpretation.rule_trace_node, file)
        with open(f'./output/{self.timestamp}_rule_trace_edges.pkl', 'wb') as file:
            pickle.dump(interpretation.rule_trace_edge, file)

    def pickle_list_of_inconsistencies(self, interpretation):
        with open(f'./output/{self.timestamp}_inconsistencies.pkl', 'wb') as file:
            pickle.dump(interpretation.inconsistencies, file)

    def pickle_interpretations(self, interpretation):
        # Warning! This could be very time and memory consuming for large graphs. Rule trace pickle is recommended
        with open(f'./output/{self.timestamp}_interpreations_node.pkl', 'wb') as file:
            pickle.dump(interpretation.interpretations_node, file)
        with open(f'./output/{self.timestamp}_interpreations_edge.pkl', 'wb') as file:
            pickle.dump(interpretation.interpretations_edge, file)
