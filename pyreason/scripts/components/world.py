import numba
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


class World:
    
    def __init__(self, labels):
        self._labels = labels
        self._world = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
        for l in labels:
            self._world[l] = interval.closed(0.0, 1.0)

    def make_world(labels, world):
        w = World(labels)
        w._world = world
        return w

    def is_satisfied(self, label, interval):
        result = False
        
        bnd = self._world[label]
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