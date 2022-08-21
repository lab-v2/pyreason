import argparse
import networkx as nx

from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.program.program import Program
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.utils.yaml_parser import YAMLParser
from mancalog.scripts.utils.output import Output


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
    output = Output()

    # Read graph & retrieve tmax
    tmax = args.timesteps
    graph_data = nx.read_graphml(args.graph_path)

    # Initialize labels
    node_labels, edge_labels = yaml_parser.parse_labels(args.labels_yaml_path)
    Node.available_labels = node_labels
    Edge.available_labels = edge_labels

    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))

    # Rules come here
    rules = yaml_parser.parse_rules(args.rules_yaml_path)

    # Facts come here
    facts = yaml_parser.parse_facts(args.facts_yaml_path)

    # Program comes here
    program = Program(graph, tmax, facts, rules)

    # Diffusion process
    interpretation = program.diffusion()

    # Write output to a pickle file. The output is a list of panda dataframes. The index of the list corresponds to the timestep
    output.write(interpretation)

    # Comment out the below code if you do not want to print the output
    # Read the pickle file, and print the dataframes for each timestep
    nodes = output.read('nodes')
    edges = output.read('edges')

    for df in nodes:
        print(df, '\n')

    for df in edges:
        print(df, '\n')


if __name__ == "__main__":
    main()