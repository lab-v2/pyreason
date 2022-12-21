from numba.experimental import structref
from numba import njit

class Interval(structref.StructRefProxy):
    def __new__(cls, l, u, s=False):
        lower = l
        upper = u
        return structref.StructRefProxy.__new__(cls, lower, upper, s)

    @property
    @njit
    def lower(self):
        return self.l

    @property
    @njit
    def upper(self):
        return self.u
    
    @property
    @njit
    def static(self):
        return self.s

    @njit
    def set_lower_upper(self, l, u):
        self.l = l
        self.u = u

    @njit
    def set_static(self, static):
        self.s = static
    
    @njit
    def is_static(self):
        return self.s

    def __repr__(self):
        return f'[{self.lower},{self.upper}]'

    def __contains__(self, item):
        if self.lower <= item.lower and self.upper >= item.upper:
            return True
        else:
            return False
