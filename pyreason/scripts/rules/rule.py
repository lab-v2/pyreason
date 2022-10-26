class Rule:

    def __init__(self, target, target_criteria, delta, neigh_nodes, neigh_edges, inf, thresholds_node, thresholds_edge):
        self._target = target
        self._target_criteria = target_criteria
        self._delta = delta
        self._neigh_nodes = neigh_nodes
        self._neigh_edges = neigh_edges
        self._inf = inf
        self._thresholds_node = thresholds_node
        self._thresholds_edge = thresholds_edge

    def get_target(self):
        return self._target

    def get_target_criteria(self):
        return self._target_criteria

    def get_delta(self):
        return self._delta

    def get_neigh_nodes(self):
        return self._neigh_nodes

    def get_neigh_edges(self):
        return self._neigh_edges
    
    def get_influence(self):
        return self._inf

    def get_thresholds_node(self):
        return self._thresholds_node
    
    def get_thresholds_edge(self):
        return self._thresholds_edge
