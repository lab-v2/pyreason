from pyreason.scripts.components.world import World


class Edge:
    available_labels = []
    
    def __init__(self, source, target):
        self._source = source
        self._target = target
        self._id = source + ':' + target
    
    def get_labels(self):
        return Edge.available_labels


    def get_source(self):
        return self._source

    def get_target(self):
        return self._target

    def get_id(self):
        return self._id

    def get_type(self):
        return 'edge'

    def get_initial_world(self):
        return World(self.get_labels())
    
    def __str__(self):
        return self._id

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return self.get_id()
        
    def __eq__(self, edge):
        result = False
        if isinstance(self, type(edge)):
            result = self is edge

            result = result or (self._source == edge.get_source() and self._target == edge.get_target())

        return result