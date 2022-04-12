import csv
from NetDiffGraph import NetDiffGraph
from NetDiffNode import NetDiffNode
from NetDiffEdge import NetDiffEdge
from NetDiffProgram import NetDiffProgram
from NetDiffFact import NetDiffFact
from NetDiffLocalRule import NetDiffLocalRule
from NetDiffGlobalRule import NetDiffGlobalRule
from Tipping import Tipping
from NetDiffGraph import NetDiffGraph
from NetDiffNode import NetDiffNode
from NetDiffEdge import NetDiffEdge
from Label import Label
from ELocalLabel import ELocalLabel
from NLocalLabel import NLocalLabel
from GlobalLabel import GlobalLabel
from Average import Average
from CFNetDiffFactRedLabels import CFNetDiffFactRedLabels
import portion

csv_graph_location = "../graph_data/graph(n=150, e=495).csv"
json_graph_location = "graph.json"

nodes = set()
edges = set()

with open(csv_graph_location, newline = '', encoding = 'utf-8') as csvfile:
	spamreader = csv.reader(csvfile, delimiter = ',')
	for row in spamreader:
		nodes.add(row[0])
		nodes.add(row[1])
		edges.add((row[0], row[1]))
aux_nodes = []
aux_edges = []
for node in nodes:
	aux_nodes.append(NetDiffNode(node))
for (n1, n2) in edges:
	aux_edges.append(NetDiffEdge(n1, n2))

nodes = aux_nodes
edges = aux_edges

facts_proportion = 0.01
facts_size = int(len(nodes) * facts_proportion)

#print(edges)
#net = NetDiffGraph('graph', nodes, edges)
#net = NetDiffGraph({1, 2, 3}, {(1, 2), (2, 3), (1, 3)})


tmax = 10

#nodes = [NetDiffNode('0'), NetDiffNode('1'), NetDiffNode('2'), NetDiffNode('3')]
#edges = [NetDiffEdge('0', '1'), NetDiffEdge('2', '1'), NetDiffEdge('2', '3')]

blue = NLocalLabel('blue')
yellow = NLocalLabel('yellow')
red = NLocalLabel('red')
global_red = GlobalLabel('global_red')

nllabels = [blue, yellow, red]
glabels = [global_red]

nodes[0].setLabels(nllabels)


graph = NetDiffGraph('graph', nodes, edges)
graph.setLabels(glabels)

#local_rules = [NetDiffLocalRule(red, [(blue, portion.closed(0.5,1))], 1,
#			[(yellow, portion.closed(0,1))], None, Tipping(0.5, portion.closed(0.7, 1)))]

local_rules = [NetDiffLocalRule(red, [], 1,
			[(red, portion.closed(1,1))], None, Tipping(0.5, portion.closed(1, 1)))]

#global_rules = [NetDiffGlobalRule(green, blue, [(red, portion.closed(0.5, 1))], Average())]

global_rules = [NetDiffGlobalRule(global_red, red, [], Average())]

facts = []
#facts = [NetDiffFact(nodes[1], blue, portion.closed(0.5, 1), 0, tmax), 
#		NetDiffFact(nodes[0], yellow, portion.closed(0.5, 1), 0, tmax), 
#		NetDiffFact(nodes[2], yellow, portion.closed(0.7, 1), 0, tmax)]

factoryFact = CFNetDiffFactRedLabels(graph, tmax)

for i in range(0, facts_size):
	facts.append(factoryFact.getRandomFact())


program = NetDiffProgram(graph, tmax, facts, local_rules, global_rules)

interp = program.diffusion()



with open(json_graph_location, "a", encoding = 'utf-8') as json_file:
	info = "data = '["
	global_data = "global_data = '["
	aux_global_data = "["
	for x in range(0, tmax + 1):
		for node in graph.getNodes():
			if interp.isSatisfied(x, node, (red, portion.closed(1,1))):
				node.set_color('red')
		info = info + graph.to_json_string() + ","
		bnd = interp.getBound(x, graph, global_red)
		global_data = global_data + aux_global_data + '{"x": ' + str(x) + ', "y":' + str(bnd.lower) + ', "group": 0},'+ '{"x": ' + str(x) + ', "y":' + str(bnd.upper) + ', "group" : 1}],'
		aux_global_data = aux_global_data + '{"x": ' + str(x) + ', "y":' + str(bnd.lower) + ', "group": 0},' + '{"x": ' + str(x) + ', "y":' + str(bnd.upper) + ', "group": 1},'
	global_data = global_data[:len(global_data) - 1]
	global_data = global_data + "]';"
	info = info[:len(info) - 1]
	info = info + "]';\n" + global_data
	json_file.write(info)
	#json_file.write(net.to_json_string())
	

'''
nodes = aux_nodes
edges = aux_edges
graph = NetDiffGraph('graph', nodes, edges)

with open(json_graph_location, "a", encoding = 'utf-8') as json_file:
	info = "data = '["
	global_data = "global_data = '["
	aux_global_data = "["
	for x in range(0, tmax + 1):
		info = info + graph.to_json_string() + ","
	info = info[:len(info) - 1]
	info = info + "]';"
	json_file.write(info)'''

print(graph.to_json_string())
print("cantidad de nodos: " + str(len(nodes)))
print("cantidad de arcos: " + str(len(edges)))

print('hechos: ' + str(facts_size))