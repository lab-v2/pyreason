# Changed from a Numba typed Dict world to a plain Python dict.
# Labels still map to the same Interval bounds.

from pyreason.scripts.interval.interval import closed, intersect_world_update


class World:

    def __init__(self, labels, world=None):
        self._labels = list(labels)
        if world is None:
            self._world = {}
            for lbl in self._labels:
                self._world[lbl] = closed(0.0, 1.0)
        else:
            self._world = world

    @property
    def labels(self):
        return self._labels

    @property
    def world(self):
        return self._world

    @staticmethod
    def make_world(labels, world):
        # Former Numba boxer entry point — keep the same call shape.
        return World(labels, world)

    def is_satisfied(self, label, interval):
        bnd = self._world[label]
        result = bnd in interval
        return result

    def update(self, label, interval):
        current_bnd = self._world[label]
        # Use the former jitted intersection so prev bounds ride through updates.
        new_bnd = intersect_world_update(current_bnd, interval)
        self._world[label] = new_bnd

    def get_bound(self, label):
        return self._world[label]

    def get_world(self):
        return self._world

    def __str__(self):
        result = ""
        for lbl in self._world.keys():
            result = result + lbl.get_value() + "," + self._world[lbl].to_str() + "\n"
        return result
