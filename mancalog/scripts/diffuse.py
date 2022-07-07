import io
import argparse
import cProfile
import pstats
import networkx as nx

import mancalog.scripts.interval.interval as interval
from mancalog.scripts.components.node import Node
from mancalog.scripts.components.edge import Edge
from mancalog.scripts.program.program import Program
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.utils.yaml_parser import YAMLParser
from mancalog.scripts.utils.filter import Filter
from mancalog.scripts.utils.output import Output


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph_path", type=str, required=True)
    parser.add_argument("--timesteps", type=int, required=True)
    parser.add_argument("--labels_yaml_path", type=str, required=True)
    parser.add_argument("--rules_yaml_path", type=str, required=True)
    parser.add_argument("--facts_yaml_path", type=str, required=True)
    parser.add_argument("--profile", type=bool, required=False, default=False)
    parser.add_argument("--profile_output", type=str)
    return parser.parse_args()


def main(args, graph_data):
    yaml_parser = YAMLParser()

    # Read graph & retrieve tmax
    tmax = args.timesteps
    # graph_data = nx.read_graphml(args.graph_path)

    # Take a subgraph of the actual data
    # graph_data = nx.subgraph(graph_data, ['n2825', 'n2625', 'n2989'])

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
    import time
    start = time.time()
    interpretation = program.diffusion()
    end = time.time()
    print(end-start)

    # Write output to a pickle file. The output is a list of panda dataframes. The index of the list corresponds to the timestep
    output = Output()
    output.write(interpretation)

    # Comment out the below code if you do not want to print the output
    # Read the pickle file, and print the dataframes for each timestep
    nodes = output.read('nodes')
    edges = output.read('edges')

    # This is how you filter the dataframe to show only nodes that have success in a certain interval
    filterer = Filter()
    filtered_df = filterer.filter_by_bound(dataframe=nodes[args.timesteps-1], label='success', bound=interval.closed(0.7,1))
    print(filtered_df)

    # The code below will print all the dataframes from each timestep for both edges and nodes
    # for df in nodes:
    #     print(df, '\n')

    # for df in edges:
    #     print(df, '\n')


if __name__ == "__main__":
    args = argparser()
    import random
    sampled_graph = nx.read_graphml(args.graph_path)
    # sampled_nodes = random.sample(list(graph_data.nodes), 10000)
    # sampled_graph = graph_data.subgraph(sampled_nodes+['n2825'])

    if args.profile:
        profiler = cProfile.Profile()
        profiler.enable()
        main(args, sampled_graph)
        profiler.disable()
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('tottime')
        stats.print_stats()
        with open('./profiling/' + args.profile_output, 'w+') as f:
            f.write(s.getvalue())

    else:
        main(args, sampled_graph)