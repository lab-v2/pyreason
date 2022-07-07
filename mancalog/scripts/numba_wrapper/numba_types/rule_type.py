class Rule:

	def __init__(self, target, tc, delta, neigh_nodes, neigh_edges, inf):
		self._target = target
		self._tc = tc
		self._delta = delta
		self._neigh_nodes = neigh_nodes
		self._neigh_edges = neigh_edges
		self._inf = inf

	def get_target(self):
		return self._target

	def get_target_criteria(self):
		return self._tc

	def get_delta(self):
		return self._delta

	def get_neigh_nodes(self):
		return self._neigh_nodes

	def get_neigh_edges(self):
		return self._neigh_edges

	def get_inf(self):
		return self._inf
	
	def influence(self, neigh, qualified_neigh):
		return self._inf.influence(neigh, qualified_neigh)


from numba import types
from numba.extending import typeof_impl
from numba.extending import type_callable
from numba.extending import models, register_model
from numba.extending import make_attribute_wrapper
from numba.extending import overload_attribute
from numba.extending import lower_builtin
from numba.core import cgutils
from numba.extending import unbox, NativeValue, box
from numba import njit


class RuleType(types.Type):
    def __init__(self):
        super(RuleType, self).__init__(name='Rule')

rule_type = RuleType()


@typeof_impl.register(Rule)
def typeof_node(val, c):
    return rule_type


# @type_callable(Rule)
# def type_interval(context):
#     def typer(target, tc, delta, neigh_nodes, neigh_edges, inf):
#         if isinstance(_id, types.UnicodeType):
#             return node_type
#     return typer


@register_model(RuleType)
class IntervalModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('lo', types.float64),
            ('hi', types.float64),
            ]
        models.StructModel.__init__(self, dmm, fe_type, members)