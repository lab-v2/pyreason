import argparse
import networkx as nx

from mancalog.scripts.program import Program
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.components.label import Label
from mancalog.scripts.graph.network_graph import NetworkGraph


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph_path", type=str)
    parser.add_argument("--timesteps", type=int)
    return parser.parse_args()


def main():
    args = argparser()

    # Read graph & retrieve tmax
    tmax = args.timesteps
    graph_data = nx.read_graphml(args.graoh_path)

    # Initialize labels
    success = Label('success')
    labels = [success]
    Node._labels = labels
    Edge._labels = []

    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))

    # Rules come here
    rules = []

    # Facts come here
    facts = []

    # Program comes here
    program = Program(graph, tmax, facts, rules)

    # Diffusion process
    interpretation = program.diffusion()

    # Print if needed
    # print(str(interpretation))


if __name__ == "__main__":
    main()