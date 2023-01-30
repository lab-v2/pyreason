from numba.experimental import structref
from numba import njit
import numpy as np

class Interval(structref.StructRefProxy):
    def __new__(cls, l, u, s=False):
        return structref.StructRefProxy.__new__(cls, l, u, s, l, u)

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
    
    @property
    @njit
    def prev_lower(self):
        return self.prev_l
    
    @property
    @njit
    def prev_upper(self):
        return self.prev_u

    @njit
    def set_lower_upper(self, l, u):
        self.l = l
        self.u = u
    
    @njit
    def reset(self):
        self.prev_l = self.l
        self.prev_u = self.u
        self.l = 0
        self.u = 1

    @njit
    def set_static(self, static):
        self.s = static
    
    @njit
    def is_static(self):
        return self.s

    @njit
    def has_changed(self):
        if self.lower==self.prev_lower and self.upper==self.prev_upper:
            return False
        else:
            return True
    
    @njit
    def intersection(self, interval):
        lower = max(self.lower, interval.lower)
        upper = min(self.upper, interval.upper)
        if lower > upper:
            lower = np.float32(0)
            upper = np.float32(1)
        return Interval(lower, upper, False, self.lower, self.upper)

    def to_str(self):
        return self.__repr__()

    def __repr__(self):
        return f'[{self.lower},{self.upper}]'

    def __contains__(self, item):
        if self.lower <= item.lower and self.upper >= item.upper:
            return True
        else:
            return False
