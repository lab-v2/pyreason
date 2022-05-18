from mancalog.scripts.program.program import Program
from mancalog.scripts.facts.fact import Fact
from mancalog.scripts.rules.rule import Rule
from mancalog.scripts.influence_functions.tipping_function import TippingFunction
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.components.label import Label
import portion
import networkx as nx

#max time for diffusion process
tmax = 3

#list of ids representing the nodes in the graph
nodes = ['0', '1', '2', '3']
#list of tuples representing the edges in the graph
edges = [('0', '1'), ('2', '1'), ('2', '3')]

#three labels that can be applied to the nodes
blue = Label('blue')
yellow = Label('yellow')
red = Label('red')


nllabels = [blue, yellow, red]

#nllabels is assigned as the set of labels that can be applied to the nodes
Node.available_labels = nllabels
#the set of labels that can be applied to the edges is empty
Edge.available_labels = []

#NetDiffGraph is an extension of a networkx graph
graph = NetworkGraph('graph', nodes, edges)
net_diff_node = list(graph.nodes)

#mancalog rule that says "red nodes that are blue with confidence between 0.5 and 1
#will be influenced next time by neighbors that are yellow with confidence between 0.5 and 1 according to function Tipping"
local_rule1 = Rule(red, [(blue, portion.closed(0.5,1))], 1,[(yellow, portion.closed(0.5, 1))], None, TippingFunction(0.5, portion.closed(0.7, 1)))

#mancalog rule that says "blue nodes that are red with confidence between 0.7 and 1
#will be influenced next time by neighbors that are yellow with confidence between 0.5 and 1 according to function Tipping"
local_rule2 = Rule(blue, [(red, portion.closed(0.7,1))], 1,[(yellow, portion.closed(0.5, 1))], None, TippingFunction(0.5, portion.closed(0.7, 1)))

local_rules = [local_rule2, local_rule1]


#mancalog fact that says "node 1 is blue with confidence interval [0.5, 1] at time [0, tmax]"
net_diff_fact1 = Fact(net_diff_node[1], blue, portion.closed(0.5, 1), 0, tmax)
#mancalog fact that says "node 0 is yellow with confidence interval [0.5, 1] at time [0, tmax]"
net_diff_fact2 = Fact(net_diff_node[0], yellow, portion.closed(0.5, 1), 0, tmax)
#mancalog fact that says "node 2 is yellow with confidence interval [0.7, 1] at time [0, tmax]"
net_diff_fact3 = Fact(net_diff_node[2], yellow, portion.closed(0.7, 1), 0, tmax)
facts = [net_diff_fact1, net_diff_fact2, net_diff_fact3]


program = Program(graph, tmax, facts, local_rules)

#mancalog interpretation that contains the final bounds for each label in each node and edge
interp = program.diffusion()

# interp.p()
print(str(interp))