class Rule:

    def __init__(self, target, target_criteria, delta, neigh_criteria, ann_fn, bnd, thresholds, subset, label):
        self._target = target
        self._target_criteria = target_criteria
        self._delta = delta
        self._neigh_criteria = neigh_criteria
        self._ann_fn = ann_fn
        self._bnd = bnd
        self._thresholds = thresholds
        self._subset = subset
        self._label = label

    def get_target(self):
        return self._target

    def get_target_criteria(self):
        return self._target_criteria

    def get_delta(self):
        return self._delta

    def get_neigh_criteria(self):
        return self._neigh_criteria
    
    def get_annotation_function(self):
        return self._ann_fn
    
    def get_bnd(self):
        return self._bnd

    def get_thresholds(self):
        return self._thresholds 
    
    def get_subset(self):
        return self._subset

    def get_label(self):
        return self._label 
