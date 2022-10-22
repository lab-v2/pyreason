import io
import time
import cProfile
import pstats
import sys
import memory_profiler as mp

import pyreason.scripts.interval.interval as interval
from pyreason.scripts.program.program import Program
from pyreason.scripts.graph.network_graph import NetworkGraph
from pyreason.scripts.utils.yaml_parser import YAMLParser
from pyreason.scripts.utils.graphml_parser import GraphmlParser
from pyreason.scripts.utils.filter import Filter
from pyreason.scripts.utils.output import Output
from pyreason.scripts.utils.args import argparser


# TODO: Make facts for edges supported
def main(args):
    if args.output_to_file:
        sys.stdout = open(f"./output/{args.output_file_name}.txt", "w")

    graphml_parser = GraphmlParser()
    yaml_parser = YAMLParser(args.timesteps)
    start = time.time()
    graph_data = graphml_parser.parse_graph(args.graph_path)
    end = time.time()
    print('Time to read graph:', end-start)

    if args.graph_attribute_parsing:
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
    if args.graph_attribute_parsing:
        specific_node_labels.update(snl)
        specific_edge_labels.update(sel)
    else:
        specific_node_labels = snl
        specific_edge_labels = sel

    # Rules come here
    rules = yaml_parser.parse_rules(args.rules_yaml_path)

    # Facts come here
    facts_node, facts_edge = yaml_parser.parse_facts(args.facts_yaml_path)
    facts_node += non_fluent_facts

    # Inconsistent predicate list
    ipl = yaml_parser.parse_ipl(args.ipl_yaml_path)

    # Program comes here
    program = Program(graph, tmax, facts_node, rules, ipl)
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
    # print('Writing interpretation')
    # timesteps = args.timesteps if args.history else 0
    # output = Output(timesteps)
    # df_nodes, df_edges = output.write(interpretation)
    # print('Finished writing interpretation')

    # Read the pickle file, and print the dataframes for each timestep
    # print('Reading dataframe from pickled files')
    # nodes = output.read('nodes')
    # edges = output.read('edges')
    # print('Finished reading dataframe')

    # This is how you filter the dataframe to show only nodes that have success in a certain interval
    print('Filtering data...')
    filterer = Filter(args.timesteps)
    filtered_df = filterer.filter_interpretation_by_bound(interpretation, label='failure', bound=interval.closed(0.7, 1))

    # You can index into filtered_df to get a particular timestep
    # This is for each timestep
    for t in range(args.timesteps+1):
        print(f'\n TIMESTEP - {t}')
        print(filtered_df[t])
        print()




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
        if args.memory_profile:
            start_mem = mp.memory_usage(max_usage=True)
            mem_usage = mp.memory_usage((main, [args]), max_usage=True)
            print(f"\nProgram used {mem_usage-start_mem} MB of memory")
        else:
            main(args)