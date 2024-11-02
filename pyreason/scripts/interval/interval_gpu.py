from numba import njit
import numpy as np

# Regular Interval class without structref for GPU compatibility
class IntervalGPU:
    def __init__(self, l, u, s=False):
        self.l = l  # lower bound
        self.u = u  # upper bound
        self.s = s  # static flag
        self.prev_l = l  # previous lower bound
        self.prev_u = u  # previous upper bound

    @staticmethod
    @njit
    def create(l, u, s=False):
        return IntervalGPU(l, u, s)

    @njit
    def get_lower(self):
        return self.l

    @njit
    def get_upper(self):
        return self.u

    @njit
    def is_static(self):
        return self.s

    @njit
    def get_prev_lower(self):
        return self.prev_l

    @njit
    def get_prev_upper(self):
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
    def has_changed(self):
        return not (self.l == self.prev_l and self.u == self.prev_u)

    @njit
    def intersection(self, interval):
        lower = max(self.l, interval.l)
        upper = min(self.u, interval.u)
        if lower > upper:
            lower = np.float32(0)
            upper = np.float32(1)
        return IntervalGPU.create(lower, upper, False)

    def __repr__(self):
        return f'[{self.l},{self.u}]'

    def __eq__(self, interval):
        return interval.l == self.l and interval.u == self.u

    def __contains__(self, item):
        return self.l <= item.l and self.u >= item.u