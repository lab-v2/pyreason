class Rule:

    def __init__(self, target, target_criteria, delta, neigh_criteria, inf, thresholds):
        self._target = target
        self._target_criteria = target_criteria
        self._delta = delta
        self._neigh_criteria = neigh_criteria
        self._inf = inf
        self._thresholds = thresholds

    def get_target(self):
        return self._target

    def get_target_criteria(self):
        return self._target_criteria

    def get_delta(self):
        return self._delta

    def get_neigh_criteria(self):
        return self._neigh_criteria
    
    def get_influence(self):
        return self._inf

    def get_thresholds(self):
        return self._thresholds 
