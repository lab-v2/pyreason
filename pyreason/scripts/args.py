import argparse

def argparser():
    parser = argparse.ArgumentParser()
    # General
    parser.add_argument("--graph_path", type=str, required=True, help='[REQUIRED] The path pointing to the graphml file')
    parser.add_argument("--timesteps", type=int, required=True, help='[REQUIRED] The number of timesteps to run the diffusion')
    # YAML
    parser.add_argument("--labels_yaml_path", type=str, required=True, help='[REQUIRED] The path pointing to the labels YAML file')
    parser.add_argument("--rules_yaml_path", type=str, required=True, help='[REQUIRED] The path pointing to the rules YAML file')
    parser.add_argument("--facts_yaml_path", type=str, required=True, help='[REQUIRED] The path pointing to the facts YAML file')
    parser.add_argument("--ipl_yaml_path", type=str, required=True, help='[REQUIRED] The path pointing to the IPL YAML file')
    # Profile
    parser.add_argument("--no-profile", dest='profile', action='store_false', help='Do not profile the code using cProfile. Profiling is off by Default')
    parser.add_argument("--profile", dest='profile', action='store_true', help='Profile the code using cProfile. Profiling is off by Default')
    parser.set_defaults(profile=False)
    parser.add_argument("--profile_output", type=str, default='profile_output', help='If profile is switched on, specify the file name of the profile output')
    # Output form - on screen or in file
    parser.add_argument("--no-output_to_file", dest='output_to_file', action='store_false', help='Print all output from the program onto the console screen. This is on by default')
    parser.add_argument("--output_to_file", dest='output_to_file', action='store_true', help='Print all output from the program into a file. This is off by default')
    parser.add_argument("--output_file_name", type=str, default='pyreason_output', help='If output_to_file option has been specified, name of the file to print the output')
    parser.set_defaults(output_to_file=False)
    # Graph attribute parsing
    parser.add_argument("--no-graph_attribute_parsing", dest='graph_attribute_parsing', action='store_false', help='Option to not make non fluent facts based on the attributes of the graph.')
    parser.add_argument("--graph_attribute_parsing", dest='graph_attribute_parsing', action='store_true', help='Option to make non fluent facts based on the attributes of the graph. On by default')
    parser.set_defaults(graph_attribute_parsing=True)
    # History of interpretations
    parser.add_argument("--no-history", dest='history', action='store_false', help='This option is recommended and on by default. Keeps track of only the latest interpretation from the last timestep. Optimized for large graphs')
    parser.add_argument("--history", dest='history', action='store_true', help='This option is not recommended and off by default. Keeps track of all interpretations over all timesteps. Not optimized for large graphs. Only switch on if you know what you are doing')
    parser.set_defaults(history=False)
    # Interpretation inconsistency check (not done)
    parser.add_argument("--abort_on_inconsistency", dest='abort_on_inconsistency', action='store_true', help='Stop the program if there are inconsistencies, do not fix them automatically')
    parser.set_defaults(abort_on_inconsistency=False)
    # Memory profiling
    parser.add_argument("--no-memory_profile", dest='memory_profile', action='store_false', help='Option to disable memory profiling. Memory profiling is on by default')
    parser.add_argument("--memory_profile", dest='memory_profile', action='store_true',help='Option to enable memory profiling. Memory profiling is on by default')
    parser.set_defaults(memory_profile=True)
    # Reverse Digraph
    parser.add_argument("--reverse_digraph", dest='reverse_digraph', action='store_true', help='Option to reverse the edges of a directed graph')
    parser.set_defaults(reverse_digraph=False)
    # Rule trace with ground atoms (not done)
    parser.add_argument("--atom_trace", dest='atom_trace', action='store_true', help='Option to track the ground atoms which lead to a rule firing. This could be very memory heavy. Default is off')
    parser.set_defaults(atom_trace=False)

    # Pickling options

    # Filtering options
    parser.add_argument("--filter_sort_by", help='Sort output by lower or upper bound', default='lower')
    parser.add_argument("--filter_label", help='Filter the output by this label;', default='disruption')
    parser.add_argument("--filter_ascending", dest='descending', action='store_false', help='Sort by ascending order instead of descending')
    parser.add_argument("--filter_descending", dest='descending', action='store_true', help='Sort by descending order instead of descending')
    parser.set_defaults(descending=True)
    




    return parser.parse_args()