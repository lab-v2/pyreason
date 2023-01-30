class Label:
    
    def __init__(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def __eq__(self, label):
        result = (self._value == label.get_value()) and isinstance(label, type(self))
        return result

    def __str__(self):
        return self._value

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return self.get_value()