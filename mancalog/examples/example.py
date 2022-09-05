import argparse

from mancalog.scripts.utils.graphml_parser import GraphmlParser
from mancalog.scripts.utils.filter import Filter
import mancalog.scripts.interval.interval as interval
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
    graphml_parser = GraphmlParser()
    yaml_parser = YAMLParser()
    graph_data = graphml_parser.parse_graph(args.graph_path)
    non_fluent_facts, specific_node_labels, specific_edge_labels = graphml_parser.parse_graph_attributes(args.timesteps) 

    # Read graph & retrieve tmax
    tmax = args.timesteps

    # Take a subgraph of the actual data
    # graph_data = nx.subgraph(graph_data, ['n2825', 'n2625', 'n2989'])
    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))

    # Initialize labels
    node_labels, edge_labels, snl, sel = yaml_parser.parse_labels(args.labels_yaml_path)
    specific_node_labels.update(snl)
    specific_edge_labels.update(sel)

    # Rules come here
    rules = yaml_parser.parse_rules(args.rules_yaml_path)

    # Facts come here
    facts = yaml_parser.parse_facts(args.facts_yaml_path)
    facts += non_fluent_facts

    # Program comes here
    program = Program(graph, tmax, facts, rules)
    program.available_labels_node = node_labels
    program.available_labels_edge = edge_labels
    program.specific_node_labels = specific_node_labels
    program.specific_edge_labels = specific_edge_labels

    # Diffusion process
    print('Graph loaded successfully, rules, labels and facts parsed successfully')
    print('Starting diffusion')
    interpretation = program.diffusion()
    print('Finished diffusion')

    # Write output to a pickle file. The output is a list of panda dataframes. The index of the list corresponds to the timestep
    # Warning: writing for a large graph can be very time consuming
    print('Writing dataframe to pickle files (this may take a while, remove this if not necessary)')
    output = Output(args.timesteps)
    output.write(interpretation)
    print('Finished writing dataframe to pickle files')

    # Comment out the below code if you do not want to print the output
    # Read the pickle file, and print the dataframes for each timestep
    print('Reading dataframe from pickled files')
    nodes = output.read('nodes')
    edges = output.read('edges')
    print('Finished reading dataframe')

    # This is how you filter the dataframe to show only nodes that have success in a certain interval
    print('Filtering data...')
    filterer = Filter()
    filtered_df = filterer.filter_by_bound(dataframe=nodes[0], label='success', bound=interval.closed(0.7,1), display_other_labels=True)
    print(filtered_df)


if __name__ == "__main__":
    main()