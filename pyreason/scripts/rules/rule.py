class Rule:

    def __init__(self, rule_name, rule_type, target, delta, clauses, bnd, thresholds, ann_fn, weights, edges, static, immediate_rule):
        self._rule_name = rule_name
        self._type = rule_type
        self._target = target
        self._delta = delta
        self._clauses = clauses
        self._bnd = bnd
        self._thresholds = thresholds
        self._ann_fn = ann_fn
        self._weights = weights
        self._edges = edges
        self._static = static
        self._immediate_rule = immediate_rule

    def get_rule_name(self):
        return self._rule_name

    def get_rule_type(self):
        return self._type

    def get_target(self):
        return self._target

    def get_delta(self):
        return self._delta

    def get_neigh_criteria(self):
        return self._clauses
    
    def get_bnd(self):
        return self._bnd

    def get_thresholds(self):
        return self._thresholds 

    def get_annotation_function(self):
        return self._ann_fn
    
    def get_edges(self):
        return self._edges

    def is_static(self):
        return self._static

    def is_immediate_rule(self):
        return self._immediate_rule
