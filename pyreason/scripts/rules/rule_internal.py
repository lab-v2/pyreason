class Rule:

    def __init__(self, rule_name, rule_type, target, head_variables, delta, clauses, bnd, thresholds, ann_fn, weights, edges, static):
        self._rule_name = rule_name
        self._type = rule_type
        self._target = target
        self._head_variables = head_variables
        self._delta = delta
        self._clauses = clauses
        self._bnd = bnd
        self._thresholds = thresholds
        self._ann_fn = ann_fn
        self._weights = weights
        self._edges = edges
        self._static = static

    def get_rule_name(self):
        return self._rule_name

    def set_rule_name(self, rule_name):
        self._rule_name = rule_name

    def get_rule_type(self):
        return self._type

    def get_target(self):
        return self._target

    def get_head_variables(self):
        return self._head_variables

    def get_delta(self):
        return self._delta

    def get_clauses(self):
        return self._clauses

    def set_clauses(self, clauses):
        self._clauses = clauses
    
    def get_bnd(self):
        return self._bnd

    def get_thresholds(self):
        return self._thresholds

    def set_thresholds(self, thresholds):
        self._thresholds = thresholds

    def get_annotation_function(self):
        return self._ann_fn
    
    def get_edges(self):
        return self._edges

    def get_weights(self):
        return self._weights

    def is_static(self):
        return self._static

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return False
        clause_eq = []
        other_clause_eq = []
        for c in self._clauses:
            clause_eq.append((c[0], c[1], tuple(c[2]), c[3], c[4]))
        for c in other.get_clauses():
            other_clause_eq.append((c[0], c[1], tuple(c[2]), c[3], c[4]))
        if self._rule_name == other.get_rule_name() and self._type == other.get_rule_type() and self._target == other.get_target() and self._head_variables == other.get_head_variables() and self._delta == other.get_delta() and tuple(clause_eq) == tuple(other_clause_eq) and self._bnd == other.get_bnd():
            return True
        else:
            return False

    def __hash__(self):
        clause_hashes = []
        for c in self._clauses:
            clause_hash = (c[0], c[1], tuple(c[2]), c[3], c[4])
            clause_hashes.append(clause_hash)

        return hash((self._rule_name, self._type, self._target.get_value(), *self._head_variables, self._delta, *clause_hashes, self._bnd))
