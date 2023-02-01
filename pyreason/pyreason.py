# This is the file that will be imported when "import pyreason" is called. All content will be run automatically
import numba
import time
import sys
import warnings
import memory_profiler as mp

from pyreason.scripts.program.program import Program
from pyreason.scripts.utils.graphml_parser import GraphmlParser
import pyreason.scripts.utils.yaml_parser as yaml_parser
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge



# USER VARIABLES
timesteps = -1
output_to_file = False
output_file_name = 'pyreason_output'
graph_attribute_parsing = True
abort_on_inconsistency = False
memory_profile = True
reverse_digraph = True
atom_trace = False
convergence_threshold = -1
convergence_bound_threshold = -1


# VARIABLES
__graph = None
__rules = None
__node_facts = None
__edge_facts = None
__ipl = None
__node_labels = None
__edge_labels = None
__specific_node_labels = None
__specific_edge_labels = None

__graphml_parser = GraphmlParser()


# FUNCTIONS
def load_graph(path: str) -> None:
    """Loads graph from GraphMl file path into program

    :param path: Path for the GraphMl file
    """
    global __graph, __graphml_parser
    __graph = __graphml_parser.parse_graph(path, reverse_digraph)
    

def load_labels(path: str) -> None:
    """Load labels from YAML file path into program

    :param path: Path for the YAML labels file
    """
    global __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels
    __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels = yaml_parser.parse_labels(path)

def load_facts(path: str) -> None:
    """Load facts from YAML file path into program

    :param path: Path for the YAML facts file
    """
    global __node_facts, __edge_facts
    __node_facts, __edge_facts = yaml_parser.parse_facts(path, reverse_digraph)

def load_rules(path: str) -> None:
    """Load rules from YAML file path into program

    :param path: Path for the YAML rules file
    """
    global __rules
    __rules = yaml_parser.parse_rules(path)

def load_inconsistent_predicate_list(path: str) -> None:
    """Load IPL from YAML file path into program

    :param path: Path for the YAML IPL file
    """
    global __ipl
    __ipl = yaml_parser.parse_ipl(path)


def run():
    global memory_profile, output_to_file, output_file_name

    # Timestamp for saving files
    timestamp = time.strftime('%Y%m%d-%H%M%S')

    if output_to_file:
        sys.stdout = open(f"./{output_file_name}_{timestamp}.txt", "a")

    if memory_profile:
        start_mem = mp.memory_usage(max_usage=True)
        mem_usage = mp.memory_usage((_run, [timestamp]), max_usage=True)
        print(f"\nProgram used {mem_usage-start_mem} MB of memory")
    else:
        _run(timestamp)



def _run(timestamp):
    # Globals
    global __graph, __rules, __node_facts, __edge_facts, __ipl, __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels, __graphml_parser
    global timesteps, output_to_file, output_file_name, graph_attribute_parsing, abort_on_inconsistency, reverse_digraph, atom_trace, convergence_threshold, convergence_bound_threshold

    if output_to_file:
        sys.stdout = open(f"./{output_file_name}_{timestamp}.txt", "a")

    # Check variables that HAVE to be set. Exceptions
    if __graph is None:
        raise Exception('Graph not loaded. Use `load_graph` to load the graphml file')
    if __rules is None:
        raise Exception('Rules not loaded. Use `load_rules` to load the rules yaml file')

    # Check variables that are highly recommended. Warnings
    if __node_labels is None and __edge_labels is None:
        warnings.warn('Labels yaml file has not been loaded. Use `load_labels`. Only graph attributes will be used as labels')
        __node_labels = numba.typed.List.empty_list(label.label_type)
        __edge_labels = numba.typed.List.empty_list(label.label_type)
        __specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))

    if __node_facts is None and __edge_facts is None:
        warnings.warn('Facts yaml file has not been loaded. Use `load_facts`. Only graph attributes will be used as facts')
        __node_facts = numba.typed.List.empty_list(fact_node.fact_type)
        __edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)

    if __ipl is None:
        warnings.warn('Inconsistent Predicate List yaml file has not been loaded. Use `load_ipl`. Loading IPL is optional')
        __ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))

    
    # Graph attribute parsing
    if graph_attribute_parsing:
        non_fluent_graph_facts_node, non_fluent_graph_facts_edge, specific_graph_node_labels, specific_graph_edge_labels = __graphml_parser.parse_graph_attributes(timesteps)
    else:
        non_fluent_graph_facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        non_fluent_graph_facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        specific_graph_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        specific_graph_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))

    # If graph attribute parsing, add results to existing specific labels and facts
    __specific_node_labels.update(specific_graph_node_labels)
    __specific_edge_labels.update(specific_graph_edge_labels)
    __node_facts.extend(non_fluent_graph_facts_node)
    __edge_facts.extend(non_fluent_graph_facts_edge)   

    # Setup logical program
    program = Program(__graph, timesteps, __node_facts, __edge_facts, __rules, __ipl, reverse_digraph, atom_trace)
    program.available_labels_node = __node_labels
    program.available_labels_edge = __edge_labels
    program.specific_node_labels = __specific_node_labels
    program.specific_edge_labels = __specific_edge_labels

    # Run Program and get final interpretation
    interpretation = program.diffusion(convergence_threshold, convergence_bound_threshold)

    return interpretation
