import argparse

def argparser():
    parser = argparse.ArgumentParser()
    # General
    parser.add_argument("--graph_path", type=str, required=True)
    parser.add_argument("--timesteps", type=int, required=True)
    # YAML
    parser.add_argument("--labels_yaml_path", type=str, required=True)
    parser.add_argument("--rules_yaml_path", type=str, required=True)
    parser.add_argument("--facts_yaml_path", type=str, required=True)
    parser.add_argument("--ipl_yaml_path", type=str, required=True)
    # Profile
    parser.add_argument("--no-profile", dest='profile', action='store_false')
    parser.add_argument("--profile", dest='profile', action='store_true')
    parser.set_defaults(profile=False)
    parser.add_argument("--profile_output", type=str)
    # Output form - on screen or in file
    parser.add_argument("--no-output_to_file", dest='output_to_file', action='store_false')
    parser.add_argument("--output_to_file", dest='output_to_file', action='store_true')
    parser.add_argument("--output_file_name", type=str, default='mancalog_output')
    parser.set_defaults(output_to_file=False)
    # Graph attribute parsing
    parser.add_argument("--no-graph_attribute_parsing", dest='graph_attribute_parsing', action='store_false')
    parser.add_argument("--graph_attribute_parsing", dest='graph_attribute_parsing', action='store_true')
    parser.set_defaults(graph_attribute_parsing=True)
    # History of interpretations
    parser.add_argument("--no-history", dest='history', action='store_false')
    parser.add_argument("--history", dest='history', action='store_true')
    parser.set_defaults(history=False)
    # Interpretation inconsistency check
    parser.add_argument("--no-inconsistency_check", dest='inconsistency_check', action='store_false')
    parser.add_argument("--inconsistency_check", dest='inconsistency_check', action='store_true')
    parser.set_defaults(inconsistency_check=True)


    return parser.parse_args()