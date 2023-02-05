class Rule:

    def __init__(self, name, target, target_criteria, delta, neigh_criteria, bnd, thresholds, ann_fn, ann_label, weights, edges):
        self._name = name
        self._target = target
        self._target_criteria = target_criteria
        self._delta = delta
        self._neigh_criteria = neigh_criteria
        self._bnd = bnd
        self._thresholds = thresholds
        self._ann_fn = ann_fn
        self._ann_label = ann_label
        self._weights = weights
        self._edges = edges

    def get_name(self):
        return self._name
    
    def get_target(self):
        return self._target

    def get_target_criteria(self):
        return self._target_criteria

    def get_delta(self):
        return self._delta

    def get_neigh_criteria(self):
        return self._neigh_criteria
    
    def get_bnd(self):
        return self._bnd

    def get_thresholds(self):
        return self._thresholds 

    def get_annotation_function(self):
        return self._ann_fn

    def get_ann_label(self):
        return self._ann_label
    
    def get_edges(self):
        return self._edges
