# This is the file that will be imported when "import pyreason" is called. All content will be run automatically
import numba
import time
import sys
import warnings
import memory_profiler as mp
from typing import List

from pyreason.scripts.utils.output import Output
from pyreason.scripts.utils.filter import Filter
from pyreason.scripts.program.program import Program
from pyreason.scripts.utils.graphml_parser import GraphmlParser
import pyreason.scripts.utils.yaml_parser as yaml_parser
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.fact_node_type as fact_node
import pyreason.scripts.numba_wrapper.numba_types.fact_edge_type as fact_edge
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval



# USER VARIABLES
class _Settings:
    def __init__(self):
        self.__verbose = True
        self.__output_to_file = False
        self.__output_file_name = 'pyreason_output'
        self.__graph_attribute_parsing = True
        self.__abort_on_inconsistency = False
        self.__memory_profile = False
        self.__reverse_digraph = True
        self.__atom_trace = False

    @property
    def verbose(self) -> bool:
        """Returns whether verbose mode is on or not

        :return: bool
        """
        return self.__verbose
    
    @property
    def output_to_file(self) -> bool:
        """Returns whether output is going to be printed to file or not

        :return: bool
        """
        return self.__output_to_file

    @property
    def output_file_name(self) -> str:
        """Returns whether name of the file output will be saved in. Only applicable if `output_to_file` is true

        :return: str
        """
        return self.__output_file_name

    @property
    def graph_attribute_parsing(self) -> bool:
        """Returns whether graph will be parsed for attributes or not

        :return: bool
        """
        return self.__graph_attribute_parsing

    @property
    def abort_on_inconsistency(self) -> bool:
        """Returns whether program will abort when it encounters an inconsistency in the interpretation or not

        :return: bool
        """
        return self.__abort_on_inconsistency

    @property
    def memory_profile(self) -> bool:
        """Returns whether program will profile maximum memory usage or not

        :return: bool
        """
        return self.__memory_profile

    @property
    def reverse_digraph(self) -> bool:
        """Returns whether graph will be reversed or not.
        If graph is reversed, an edge a->b will become b->a

        :return: bool
        """
        return self.__reverse_digraph

    @property
    def atom_trace(self) -> bool:
        """Returns whether to keep track of all atoms that are responsible for the firing of rules or not.
        NOTE: Turning this on may increase memory usage

        :return: bool
        """
        return self.__atom_trace        

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set verbose mode. Default is True

        :param value: verbose or not
        :raises TypeError: If not boolean, raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__verbose = value
    
    @output_to_file.setter
    def output_to_file(self, value: bool) -> None:
        """Set whether to put all output into a file. Default file name is `pyreason_output` and can be changed
        with `output_file_name`. Default is False

        :param value: whether to save to file or not
        :raises TypeError: If not boolean, raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__output_to_file = value

    @output_file_name.setter
    def output_file_name(self, file_name: str) -> None:
        """Set output file name if `output_to_file` is true. Default is `pyreason_output`

        :param file_name: File name
        :raises TypeError: If not string raise error
        """
        if not isinstance(file_name, str):
            raise TypeError('file_name has to be a string')
        else:
            self.__output_file_name = file_name

    @graph_attribute_parsing.setter
    def graph_attribute_parsing(self, value: bool) -> None:
        """Whether to parse graphml file for attributes. Default is True

        :param file_name: Whether to parse graphml or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__graph_attribute_parsing = value

    @abort_on_inconsistency.setter
    def abort_on_inconsistency(self, value: bool) -> None:
        """Whether to abort program if inconsistency is found. Default is False

        :param file_name: Whether to abort on inconsistency or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__abort_on_inconsistency = value

    @memory_profile.setter
    def memory_profile(self, value: bool) -> None:
        """Whether to profile the program's memory usage. Default is False

        :param file_name: Whether to profile program's memory usage or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__memory_profile = value

    @reverse_digraph.setter
    def reverse_digraph(self, value: bool) -> None:
        """Whether to reverse the digraph. if the graphml contains an edge: a->b
        setting reverse as true will make the edge b->a. Default is False

        :param file_name: Whether to reverse graphml edgesor not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__reverse_digraph = value

    @atom_trace.setter
    def atom_trace(self, value: bool) -> None:
        """Whether to save all atoms that were responsible for the firing of a rule.
        NOTE: this can be very memory heavy. Default is False

        :param file_name: Whether to save all atoms or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__atom_trace = value

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

__non_fluent_graph_facts_node = None
__non_fluent_graph_facts_edge = None
__specific_graph_node_labels = None
__specific_graph_edge_labels = None

__timestamp = ''

__graphml_parser = GraphmlParser()
settings = _Settings()


# FUNCTIONS
def load_graph(path: str) -> None:
    """Loads graph from GraphMl file path into program

    :param path: Path for the GraphMl file
    """
    global __graph, __graphml_parser, __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels, settings
    
    # Parse graph
    __graph = __graphml_parser.parse_graph(path, settings.reverse_digraph)

    # Graph attribute parsing
    if settings.graph_attribute_parsing:
        __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels = __graphml_parser.parse_graph_attributes()
    else:
        __non_fluent_graph_facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        __non_fluent_graph_facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        __specific_graph_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_graph_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))
    

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
    global __node_facts, __edge_facts, settings
    __node_facts, __edge_facts = yaml_parser.parse_facts(path, settings.reverse_digraph)

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


def reason(timesteps: int=-1, convergence_threshold: int=-1, convergence_bound_threshold: float=-1):
    """Function to start the main reasoning process. Graph and rules must already be loaded.

    :param timesteps: Max number of timesteps to run. -1 specifies run till convergence, defaults to -1
    :param convergence_threshold: Maximim number of interpretations that have changed between timesteps or fixed point operations until considered convergent. Program will end at convergence. -1 => no changes, perfect convergence, defaults to -1
    :param convergence_bound_threshold: Maximum change in any interpretation (bounds) between timesteps or fixed point operations until considered convergent, defaults to -1
    :return: The final interpretation after reasoning.
    """
    global settings, __timestamp

    # Timestamp for saving files
    __timestamp = time.strftime('%Y%m%d-%H%M%S')

    if settings.output_to_file:
        sys.stdout = open(f"./{settings.output_file_name}_{__timestamp}.txt", "a")

    if settings.memory_profile:
        start_mem = mp.memory_usage(max_usage=True)
        mem_usage, interpretation = mp.memory_usage((_reason, [timesteps, convergence_threshold, convergence_bound_threshold]), max_usage=True, retval=True)
        print(f"\nProgram used {mem_usage-start_mem} MB of memory")
    else:
        interpretation = _reason(timesteps, convergence_threshold, convergence_bound_threshold)

    return interpretation



def _reason(timesteps, convergence_threshold, convergence_bound_threshold):
    # Globals
    global __graph, __rules, __node_facts, __edge_facts, __ipl, __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels, __graphml_parser
    global settings, __timestamp

    # Assert variables are of correct type

    if settings.output_to_file:
        sys.stdout = open(f"./{settings.output_file_name}_{__timestamp}.txt", "a")

    # Check variables that HAVE to be set. Exceptions
    if __graph is None:
        raise Exception('Graph not loaded. Use `load_graph` to load the graphml file')
    if __rules is None:
        raise Exception('Rules not loaded. Use `load_rules` to load the rules yaml file')

    # Check variables that are highly recommended. Warnings
    if __node_labels is None and __edge_labels is None:
        warnings.warn('Labels yaml file has not been loaded. Use `load_labels`. Only graph attributes will be used as labels\n')
        __node_labels = numba.typed.List.empty_list(label.label_type)
        __edge_labels = numba.typed.List.empty_list(label.label_type)
        __specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))

    if __node_facts is None and __edge_facts is None:
        warnings.warn('Facts yaml file has not been loaded. Use `load_facts`. Only graph attributes will be used as facts\n')
        __node_facts = numba.typed.List.empty_list(fact_node.fact_type)
        __edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)

    if __ipl is None:
        warnings.warn('Inconsistent Predicate List yaml file has not been loaded. Use `load_ipl`. Loading IPL is optional\n')
        __ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))

    
    # If graph attribute parsing, add results to existing specific labels and facts
    __specific_node_labels.update(__specific_graph_node_labels)
    __specific_edge_labels.update(__specific_graph_edge_labels)
    __node_facts.extend(__non_fluent_graph_facts_node)
    __edge_facts.extend(__non_fluent_graph_facts_edge)   

    # Setup logical program
    program = Program(__graph, timesteps, __node_facts, __edge_facts, __rules, __ipl, settings.reverse_digraph, settings.atom_trace)
    program.available_labels_node = __node_labels
    program.available_labels_edge = __edge_labels
    program.specific_node_labels = __specific_node_labels
    program.specific_edge_labels = __specific_edge_labels

    # Run Program and get final interpretation
    interpretation = program.reason(convergence_threshold, convergence_bound_threshold, settings.verbose)

    return interpretation


def save_rule_trace(interpretation, folder: str='./'):
    """Saves the trace of the program. This includes every change that has occured to the interpretation. If `atom_trace` was set to true
    this gives us full explainability of why interpretations changed

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :param folder: the folder in which to save the result, defaults to './'
    """
    global __timestamp

    output = Output(__timestamp)
    output.save_rule_trace(interpretation, folder)


def filter_and_sort(interpretation, labels: List[str], bound: interval.Interval=interval.closed(0,1), sort_by: str='lower', descending: bool=True):
    """Filters and sorts the interpretation and returns as a list of Pandas dataframes that are easy to access

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :param labels: A list of strings, labels that are in the interpretation that are to be filtered
    :param bound: The bound that will filter any interpretation that is not in it. the default does not filter anything, defaults to interval.closed(0,1)
    :param sort_by: String that is either 'lower' or 'upper', sorts by the lower/upper bound, defaults to 'lower'
    :param descending: A bool that sorts by descending/ascending order, defaults to True
    :return: A list of Pandas dataframes that contain the filtered and sorted interpretations that are easy to access
    """
    filterer = Filter(interpretation.time)
    filtered_df = filterer.filter_and_sort(interpretation, labels, bound, sort_by, descending)
    return filtered_df
