# Changed from recomputing hash(str(self)) every lookup to a cached hash.
# Same-text Labels still compare and hash equal.


class Label:

    def __init__(self, value):
        self._value = value
        # Lazy hash cache: _value is never reassigned after construction.
        self._hash = None

    @property
    def value(self):
        # Numba LabelType exposed `.value`; annotation fns still use it.
        return self._value

    @value.setter
    def value(self, value):
        # Unit tests assign `.value` directly (former Numba attribute).
        self._value = value
        self._hash = None

    def get_value(self):
        return self._value

    def __eq__(self, label):
        result = (self._value == label.get_value()) and isinstance(label, type(self))
        return result

    def __str__(self):
        return self._value

    def __hash__(self):
        h = self._hash
        if h is None:
            h = self._hash = hash(str(self))
        return h

    def __repr__(self):
        return self.get_value()
