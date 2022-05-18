import argparse
import portion
import random
import networkx as nx
from torch import rand

from mancalog.scripts.facts.fact import Fact
from mancalog.scripts.rules.rule import Rule
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.components.label import Label
from mancalog.scripts.program.program import Program
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.influence_functions.tipping_function import TippingFunction


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph_path", type=str, required=True)
    parser.add_argument("--timesteps", type=int, required=True)
    return parser.parse_args()


def main():
    args = argparser()

    # Read graph & retrieve tmax
    tmax = args.timesteps
    graph_data = nx.read_graphml(args.graph_path)
    # graph_data = nx.subgraph(graph_data, ['n2825', 'n2625', 'n2989'])
    # print(graph_data.nodes)

    # Initialize labels
    # TODO: Make a parser to read the labels needed
    success = Label('success')
    failure = Label('failure')
    labels = [success, failure]
    Node.available_labels = labels
    Edge.available_labels = []

    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))

    # Rules come here
    # TODO: Make a parser to read the rules from a csv
    # Nodes that have the success label with bounds between 0 and 1, will be influenced next timestep if half its neighbors have success between 0.5 and 1
    rule1 = Rule(success, [(success, portion.closed(0,1))], 1, [(success, portion.closed(0.5, 1))], None, TippingFunction(0.5, portion.closed(0.7, 1)))
    rule2 = Rule(failure, [(failure, portion.closed(0,1))], 1, [(failure, portion.closed(0.5, 1))], None, TippingFunction(0.5, portion.closed(0.7, 1)))
    rules = [rule1, rule2]

    # Facts come here
    # TODO: Make a parser to read the facts from a csv
    facts = []
    for node in list(graph.nodes):
        success_bnd = [random.randint(0, 10)/10 for i in range(2)]
        failure_bnd = [random.randint(0, 10)/10 for i in range(2)]
        success_bnd.sort()
        failure_bnd.sort()
        success_fact = Fact(node, success, portion.closed(success_bnd[0], success_bnd[1]), 0, 0)
        failure_fact = Fact(node, failure, portion.closed(failure_bnd[0], failure_bnd[1]), 0, 0)
        facts.append(success_fact)
        facts.append(failure_fact)


    # Program comes here
    program = Program(graph, tmax, facts, rules)

    # Diffusion process
    interpretation = program.diffusion()

    # Print if needed
    # print(str(interpretation))


if __name__ == "__main__":
    main()