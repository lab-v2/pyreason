import io
import time
import cProfile
import pstats
import sys
import memory_profiler as mp

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval
from pyreason.scripts.program.program import Program
import pyreason.scripts.utils.yaml_parser as yaml_parser
from pyreason.scripts.utils.graphml_parser import GraphmlParser
from pyreason.scripts.utils.filter import Filter
from pyreason.scripts.utils.output import Output
from pyreason.scripts.args import argparser



def main(args):
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    if args.output_to_file:
        sys.stdout = open(f"./output/{args.output_file_name}_{timestamp}.txt", "w")

    # Initialize parsers
    graphml_parser = GraphmlParser()

    start = time.time()
    graph = graphml_parser.parse_graph(args.graph_path, args.reverse_digraph)
    end = time.time()
    print('Time to read graph:', end-start)

    if args.graph_attribute_parsing:
        start = time.time()
        non_fluent_facts_node, non_fluent_facts_edge, specific_node_labels, specific_edge_labels = graphml_parser.parse_graph_attributes() 
        end = time.time()
        print('Time to read graph attributes:', end-start)
    else:
        non_fluent_facts_node = []
        non_fluent_facts_edge = []

    tmax = args.timesteps

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

    # Facts come here. Add non fluent facts that came from the graph
    facts_node, facts_edge = yaml_parser.parse_facts(args.facts_yaml_path, args.reverse_digraph)
    facts_node += non_fluent_facts_node
    facts_edge += non_fluent_facts_edge

    # Inconsistent predicate list
    ipl = yaml_parser.parse_ipl(args.ipl_yaml_path)

    # Program comes here
    program = Program(graph, tmax, facts_node, facts_edge, rules, ipl, args.reverse_digraph, args.atom_trace)
    program.available_labels_node = node_labels
    program.available_labels_edge = edge_labels
    program.specific_node_labels = specific_node_labels
    program.specific_edge_labels = specific_edge_labels

    # Reasoning process
    print('Graph loaded successfully, rules, labels, facts and ipl parsed successfully')
    print('Starting diffusion')
    start = time.time()
    interpretation = program.reason(args.convergence_threshold, args.convergence_bound_threshold)
    end = time.time()
    print('Time to complete diffusion:', end-start)
    print('Finished diffusion')

    # Save the rule trace to a file
    output = Output(timestamp)
    output.save_rule_trace(interpretation, folder='./output')

    # This is how you filter the dataframe to show only nodes that have success in a certain interval
    print('Filtering data...')
    filterer = Filter(interpretation.time)
    filtered_df = filterer.filter_and_sort(interpretation, labels=args.filter_labels, bound=interval.closed(0, 1), sort_by=args.filter_sort_by, descending=args.descending)

    # You can index into filtered_df to get a particular timestep
    # This is for each timestep
    for t in range(interpretation.time+1):
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
        with open('./profiling/' + args.profile_output + '.txt', 'w+') as f:
            f.write(s.getvalue())

    else:
        if args.memory_profile:
            start_mem = mp.memory_usage(max_usage=True)
            mem_usage = mp.memory_usage((main, [args]), max_usage=True)
            print(f"\nProgram used {mem_usage-start_mem} MB of memory")
        else:
            main(args)