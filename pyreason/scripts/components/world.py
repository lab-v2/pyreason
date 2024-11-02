import numba
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

import numpy as np
from numba import cuda


class World:
    
    def __init__(self, labels):
        self._labels = labels
        self._world = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
        for l in labels:
            self._world[l] = interval.closed(0.0, 1.0)

    @property
    def world(self):
        return self._world

    def make_world(labels, world):
        w = World(labels)
        w._world = world
        return w

    def is_satisfied(self, label, interval):
        result = False

        print(f'label: {label}, interval: {interval}')

        bnd = self._world[label]
        print(f'bnd: {bnd}')
        result = bnd in interval

        return result

    def update(self, label, interval):
        lwanted = None
        bwanted = None 
        
        current_bnd = self._world[label]
        new_bnd = current_bnd.intersection(interval)
        self._world[label] = new_bnd

    def get_bound(self, label):
        result = None

        result = self._world[label] 
        return result

    def get_world(self):
        return self._world


    def __str__(self):
        result = ''
        for label in self._world.keys():
            result = result + label.get_value() + ',' + self._world[label].to_str() + '\n'

        return result

    # Define the CUDA kernel
    # @cuda.jit
    # def is_satisfied_gpu(self, label_bound, rule_bound, result):
    #     """Check if 'bound' is within 'interval' on the GPU."""
    #     # Check if the lower and upper bounds of `bound` are within `interval`
    #     if label_bound.l <= rule_bound.l and label_bound.u <= rule_bound.u:
    #         result[0] = True
    #     else:
    #         result[0] = False

    # Wrapper function that retrieves `interval` and checks satisfaction on the GPU
    # def check_single_bound_on_gpu(self, label, rule_bound):
    #     # Assume world[label].interval is accessible and returns an IntervalGPU when converted
    #     # Retrieve the interval from the world using the label
    #     print(cuda.is_available())
    #     rule_bnd = self.convert_to_gpu_interval(rule_bound)
    #
    #     # Prepare a single bound IntervalGPU instance
    #     label_bnd = self.convert_to_gpu_interval(self._world[label])
    #
    #
    #     # Prepare result array to store a single boolean value
    #     result = np.zeros(1, dtype=np.bool_)
    #
    #     # Transfer `bound`, `interval`, and `result` to GPU
    #     d_label_bound = cuda.to_device(label_bnd)
    #     d_rule_bound = cuda.to_device(rule_bnd)
    #     d_result = cuda.to_device(result)
    #
    #     # Launch kernel with one thread (single check)
    #     self.is_satisfied_gpu[1, 1](d_label_bound, d_rule_bound, d_result)
    #
    #     # Copy result back to host
    #     return d_result.copy_to_host()[0]  # Returns True or False
    #
    # # Conversion function from structref Interval to GPU-compatible Interval
    # def convert_to_gpu_interval(self, interval_structref):
    #     """Convert a structref-based Interval to a GPU-compatible Interval."""
    #     return IntervalGPUType(
    #         l=interval_structref.lower(),
    #         u=interval_structref.upper(),
    #         s=interval_structref.static()
    #     )