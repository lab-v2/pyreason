from pyreason.scripts.components.world import World


class Node:
    available_labels = []
    
    def __init__(self, _id):
        self._id = _id
    
    def get_labels(self):
        return Node.available_labels

    def __str__(self):
        return self._id

    def __hash__(self):
        return hash(str(self))

    def get_id(self):
        return self._id

    def get_type(self):
        return 'node'

    def get_initial_world(self):
        return World(self.get_labels())

    def __repr__(self):
        return self.get_id()
        
    def __eq__(self, node):
        result = False
        if isinstance(self, type(node)):
            result = self is node

            result = result or (self._id == node.get_id())

        return result