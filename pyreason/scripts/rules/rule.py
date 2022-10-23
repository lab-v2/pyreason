class Rule:

    def __init__(self, target, tc_node, tc_edge, delta, neigh_nodes, neigh_edges, inf, thresholds):
        self._target = target
        self._tc_node = tc_node
        self._tc_edge = tc_edge
        self._delta = delta
        self._neigh_nodes = neigh_nodes
        self._neigh_edges = neigh_edges
        self._inf = inf
        self._thresholds = thresholds

    def get_target(self):
        return self._target

    def get_target_criteria_node(self):
        return self._tc_node
    
    def get_target_criteria_edge(self):
        return self._tc_edge

    def get_delta(self):
        return self._delta

    def get_neigh_nodes(self):
        return self._neigh_nodes

    def get_neigh_edges(self):
        return self._neigh_edges
    
    def get_influence(self):
        return self._inf

    def get_thresholds(self):
        return self._thresholds