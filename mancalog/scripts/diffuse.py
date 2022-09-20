import io
import time
import argparse
import cProfile
import pstats
import sys
import memory_profiler as mp

import mancalog.scripts.interval.interval as interval
from mancalog.scripts.program.program import Program
from mancalog.scripts.graph.network_graph import NetworkGraph
from mancalog.scripts.utils.yaml_parser import YAMLParser
from mancalog.scripts.utils.graphml_parser import GraphmlParser
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
    parser.add_argument("--save_output_to_file", type=bool, default=False)
    parser.add_argument("--read_graph_attributes", type=bool, default=True)
    parser.add_argument("--history", type=int, default=1)

    return parser.parse_args()

# TODO: Make facts for edges supported
def main(args):
    if args.save_output_to_file:
        sys.stdout = open("./output/mancalog_output.txt", "w")

    graphml_parser = GraphmlParser()
    yaml_parser = YAMLParser()
    start = time.time()
    graph_data = graphml_parser.parse_graph(args.graph_path)
    end = time.time()
    print('Time to read graph:', end-start)

    if args.read_graph_attributes:
        start = time.time()
        non_fluent_facts, specific_node_labels, specific_edge_labels = graphml_parser.parse_graph_attributes(args.timesteps) 
        end = time.time()
        print('Time to read graph attributes:', end-start)

    # Read graph & retrieve tmax
    tmax = args.timesteps

    # Take a subgraph of the actual data
    # graph_data = nx.subgraph(graph_data, ['n2825', 'n2625', 'n2989'])
    start = time.time()
    graph = NetworkGraph('graph', list(graph_data.nodes), list(graph_data.edges))
    end = time.time()
    print('Time to initialize graph for diffusion:', end-start)
    del graph_data

    # Initialize labels
    node_labels, edge_labels, snl, sel = yaml_parser.parse_labels(args.labels_yaml_path)
    if args.read_graph_attributes:
        specific_node_labels.update(snl)
        specific_edge_labels.update(sel)
    else:
        specific_node_labels = snl
        specific_edge_labels = sel

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
    start = time.time()
    interpretation = program.diffusion(args.history)
    end = time.time()
    print('Time to complete diffusion:', end-start)
    print('Finished diffusion')

    # Write output to a pickle file. The output is a list of panda dataframes. The index of the list corresponds to the timestep
    # Warning: writing for a large graph can be very time consuming
    print('Writing dataframe to pickle files (this may take a while, remove this if not necessary)')
    timesteps = args.timesteps if args.history else 0
    output = Output(timesteps)
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
    idx = args.timesteps if args.history else 0
    filtered_df = filterer.filter_by_bound(dataframe=nodes[idx], label='success', bound=interval.closed(0.7,1), display_other_labels=False)
    print(filtered_df)


if __name__ == "__main__":
    args = argparser()


    if args.profile:
        profiler = cProfile.Profile()
        profiler.enable()
        main(args)
        profiler.disable()
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('tottime')
        stats.print_stats()
        with open('./profiling/' + args.profile_output, 'w+') as f:
            f.write(s.getvalue())

    else:
        start_mem = mp.memory_usage(max_usage=True)
        mem_usage = mp.memory_usage((main, [args]), max_usage=True)
        print(f"\nProgram used {mem_usage-start_mem} MB of memory")
        # main(args)