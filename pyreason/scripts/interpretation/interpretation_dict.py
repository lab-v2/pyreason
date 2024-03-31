class InterpretationDict(dict):
    """
    This class is specific for the interpretation for a specific timestep.
    """
    def __int__(self):
        super().__init__()

    def __setitem__(self, key, value):
        assert len(value) == 2, 'Lower bound and Upper bound are required to set an Interpretation'
        self.__dict__[key] = (value[0], value[1])

    def __getitem__(self, key):
        if key not in self.__dict__.keys():
            return tuple((0, 1))
        else:
            return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)
