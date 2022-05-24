import argparse
import networkx as nx

from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.program.program import Program
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.utils.yaml_parser import YAMLParser


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph_path", type=str, default='mancalog/examples/example_graph/honda_subgraph.graphml')
    parser.add_argument("--timesteps", type=int, default=2)
    parser.add_argument("--labels_yaml_path", type=str, default='mancalog/examples/example_yamls/labels.yaml')
    parser.add_argument("--rules_yaml_path", type=str, default='mancalog/examples/example_yamls/rules.yaml')
    parser.add_argument("--facts_yaml_path", type=str, default='mancalog/examples/example_yamls/facts.yaml')
    return parser.parse_args()


def main():
    args = argparser()
    yaml_parser = YAMLParser()

    # Read graph & retrieve tmax
    tmax = args.timesteps
    graph_data = nx.read_graphml(args.graph_path)

    # Initialize labels
    labels = yaml_parser.parse_labels(args.labels_yaml_path)
    Node.available_labels = labels
    Edge.available_labels = []

    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))

    # Rules come here
    rules = yaml_parser.parse_rules(args.rules_yaml_path)

    # Facts come here
    facts = yaml_parser.parse_facts(args.facts_yaml_path)

    # Program comes here
    program = Program(graph, tmax, facts, rules)

    # Diffusion process
    interpretation = program.diffusion()

    # Print if needed
    print(str(interpretation))


if __name__ == "__main__":
    main()