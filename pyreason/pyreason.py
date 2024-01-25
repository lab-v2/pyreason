# This is the file that will be imported when "import pyreason" is called. All content will be run automatically
import networkx as nx
import numba
import time
import sys
import pandas as pd
import memory_profiler as mp
from typing import List, Type, Callable, Tuple

from pyreason.scripts.utils.output import Output
from pyreason.scripts.utils.filter import Filter
from pyreason.scripts.program.program import Program
from pyreason.scripts.utils.graphml_parser import GraphmlParser
import pyreason.scripts.utils.yaml_parser as yaml_parser
import pyreason.scripts.utils.rule_parser as rule_parser
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.rules.rule import Rule
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
        self.__reverse_digraph = False
        self.__atom_trace = False
        self.__save_graph_attributes_to_trace = False
        self.__canonical = False
        self.__inconsistency_check = True
        self.__static_graph_facts = True
        self.__store_interpretation_changes = True
        self.__parallel_computing = False
        self.__update_mode = 'intersection'

    @property
    def verbose(self) -> bool:
        """Returns whether verbose mode is on or not. Default is True

        :return: bool
        """
        return self.__verbose
    
    @property
    def output_to_file(self) -> bool:
        """Returns whether output is going to be printed to file or not. Default is False

        :return: bool
        """
        return self.__output_to_file

    @property
    def output_file_name(self) -> str:
        """Returns whether name of the file output will be saved in. Only applicable if `output_to_file` is true. Default is pyreason_output

        :return: str
        """
        return self.__output_file_name

    @property
    def graph_attribute_parsing(self) -> bool:
        """Returns whether graph will be parsed for attributes or not. Default is True

        :return: bool
        """
        return self.__graph_attribute_parsing

    @property
    def abort_on_inconsistency(self) -> bool:
        """Returns whether program will abort when it encounters an inconsistency in the interpretation or not. Default is False

        :return: bool
        """
        return self.__abort_on_inconsistency

    @property
    def memory_profile(self) -> bool:
        """Returns whether program will profile maximum memory usage or not. Default is False

        :return: bool
        """
        return self.__memory_profile

    @property
    def reverse_digraph(self) -> bool:
        """Returns whether graph will be reversed or not.
        If graph is reversed, an edge a->b will become b->a. Default is False

        :return: bool
        """
        return self.__reverse_digraph

    @property
    def atom_trace(self) -> bool:
        """Returns whether to keep track of all atoms that are responsible for the firing of rules or not.
        NOTE: Turning this on may increase memory usage. Default is False

        :return: bool
        """
        return self.__atom_trace   

    @property
    def save_graph_attributes_to_trace(self) -> bool:
        """Returns whether to save the graph attribute facts to the rule trace. Graphs are large and turning this on can result in more memory usage.
        NOTE: Turning this on may increase memory usage. Default is False

        :return: bool
        """
        return self.__save_graph_attributes_to_trace        
    
    @property
    def canonical(self) -> bool:
        """Returns whether the interpretation is canonical or non-canonical. Default is False

        :return: bool
        """
        return self.__canonical
   
    @property
    def inconsistency_check(self) -> bool:
        """Returns whether to check for inconsistencies in the interpretation or not. Default is True

        :return: bool
        """
        return self.__inconsistency_check
    
    @property
    def static_graph_facts(self) -> bool:
        """Returns whether to make graph facts static or not. Default is True

        :return: bool
        """
        return self.__static_graph_facts

    @property
    def store_interpretation_changes(self) -> bool:
        """Returns whether to keep track of changes that occur in the interpretation. You will not be able to view
        interpretation results after reasoning. Default is True

        :return: bool
        """
        return self.__store_interpretation_changes

    @property
    def parallel_computing(self) -> bool:
        """Returns whether to use multiple CPU cores for inference. This will disable cacheing and pyreason will have
        to be re-compiled at each run - but after compilation it will be faster. Default is False

        :return: bool
        """
        return self.__parallel_computing

    @property
    def update_mode(self) -> str:
        """Returns the way interpretations are going to be updated. This could be "intersection" or "override"

        :return: str
        """
        return self.__update_mode

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

        :param value: Whether to parse graphml or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__graph_attribute_parsing = value

    @abort_on_inconsistency.setter
    def abort_on_inconsistency(self, value: bool) -> None:
        """Whether to abort program if inconsistency is found. Default is False

        :param value: Whether to abort on inconsistency or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__abort_on_inconsistency = value

    @memory_profile.setter
    def memory_profile(self, value: bool) -> None:
        """Whether to profile the program's memory usage. Default is False

        :param value: Whether to profile program's memory usage or not
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

        :param value: Whether to reverse graphml edges or not
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

        :param value: Whether to save all atoms or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__atom_trace = value
    
    @save_graph_attributes_to_trace.setter
    def save_graph_attributes_to_trace(self, value: bool) -> None:
        """Whether to save all graph attribute facts. Graphs are large so turning this on can be memory heavy
        NOTE: this can be very memory heavy. Default is False

        :param value: Whether to save all graph attribute facts in the trace or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__save_graph_attributes_to_trace = value
    
    @canonical.setter
    def canonical(self, value: bool) -> None:
        """Whether the interpretation should be canonical where bounds are reset at each timestep or not

        :param value: Whether to reset all bounds at each timestep (non-canonical) or not (canonical)
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__canonical = value
   
    @inconsistency_check.setter
    def inconsistency_check(self, value: bool) -> None:
        """Whether to check for inconsistencies in the interpretation or not

        :param value: Whether to check for inconsistencies or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__inconsistency_check = value
    
    @static_graph_facts.setter
    def static_graph_facts(self, value: bool) -> None:
        """Whether to make graphml attribute facts static or not

        :param value: Whether to make graphml facts static or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__static_graph_facts = value

    @store_interpretation_changes.setter
    def store_interpretation_changes(self, value: bool) -> None:
        """Whether to keep track of changes that occur to the interpretation. You will not be able to view interpretation
        results after reasoning.

        :param value: Whether to make graphml facts static or not
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__store_interpretation_changes = value

    @parallel_computing.setter
    def parallel_computing(self, value: bool) -> None:
        """Whether to use multiple CPU cores for inference. This will disable cacheing and pyreason will have
        to be re-compiled at each run - but after compilation it will be faster. Default is False

        :param value: Whether to make inference run on parallel hardware (multiple CPU cores)
        :raises TypeError: If not bool raise error
        """
        if not isinstance(value, bool):
            raise TypeError('value has to be a bool')
        else:
            self.__parallel_computing = value

    @update_mode.setter
    def update_mode(self, value: str) -> None:
        """The way interpretations are going to be updated. This could be "intersection" or "override". Default is
         'intersection'

        :param value: "intersection" or "override"
        :raises TypeError: If not str raise error
        """
        if not isinstance(value, str):
            raise TypeError('value has to be a str')
        else:
            self.__update_mode = value


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

__annotation_functions = []

__timestamp = ''
__program = None

__graphml_parser = GraphmlParser()
settings = _Settings()


def reset():
    """Resets certain variables to None to be able to do pr.reason() multiple times in a program
    without memory blowing up
    """
    global __node_facts, __edge_facts, __node_labels, __edge_labels
    __node_facts = None
    __edge_facts = None
    __node_labels = None
    __edge_labels = None


def reset_rules():
    """
    Resets rules to none
    """
    global __rules
    __rules = None


# FUNCTIONS
def load_graphml(path: str) -> None:
    """Loads graph from GraphMl file path into program

    :param path: Path for the GraphMl file
    """
    global __graph, __graphml_parser, __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels, settings
    
    # Parse graph
    __graph = __graphml_parser.parse_graph(path, settings.reverse_digraph)

    # Graph attribute parsing
    if settings.graph_attribute_parsing:
        __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels = __graphml_parser.parse_graph_attributes(settings.static_graph_facts)
    else:
        __non_fluent_graph_facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        __non_fluent_graph_facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        __specific_graph_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_graph_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))


def load_graph(graph: nx.DiGraph) -> None:
    """Load a networkx DiGraph into pyreason

    :param graph: Networkx DiGraph object to load into pyreason
    :type graph: nx.DiGraph
    :return: None
    """
    global __graph, __graphml_parser, __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels, settings
    
    # Load graph
    __graph = __graphml_parser.load_graph(graph)

    # Graph attribute parsing
    if settings.graph_attribute_parsing:
        __non_fluent_graph_facts_node, __non_fluent_graph_facts_edge, __specific_graph_node_labels, __specific_graph_edge_labels = __graphml_parser.parse_graph_attributes(settings.static_graph_facts)
    else:
        __non_fluent_graph_facts_node = numba.typed.List.empty_list(fact_node.fact_type)
        __non_fluent_graph_facts_edge = numba.typed.List.empty_list(fact_edge.fact_type)
        __specific_graph_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_graph_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))


def load_inconsistent_predicate_list(path: str) -> None:
    """Load IPL from YAML file path into program

    :param path: Path for the YAML IPL file
    """
    global __ipl
    __ipl = yaml_parser.parse_ipl(path)


def add_rule(pr_rule: Rule) -> None:
    """Add a rule to pyreason from text format. This format is not as modular as the YAML format.
    """
    global __rules

    # Add to collection of rules
    if __rules is None:
        __rules = numba.typed.List.empty_list(rule.rule_type)
    __rules.append(pr_rule.rule)


def add_rules_from_file(file_path: str, infer_edges: bool = False) -> None:
    """ Add a set of rules from a text file

    :param file_path: Path to the text file containing rules
    :type file_path: str
    :param infer_edges: Whether to infer edges on these rules if an edge doesn't exist between head variables and the body of the rule is satisfied
    :type infer_edges: bool
    :return: None
    """
    with open(file_path, 'r') as file:
        rules = [line.rstrip() for line in file if line.rstrip() != '' and line.rstrip()[0] != '#']

    rule_offset = 0 if __rules is None else len(__rules)
    for i, r in enumerate(rules):
        add_rule(Rule(r, f'rule_{i+rule_offset}', infer_edges))


def add_fact(pyreason_fact: Fact) -> None:
    """Add a PyReason fact to the program.

    :param pyreason_fact: PyReason fact created using pr.Fact(...)
    :return: None
    """
    global __node_facts, __edge_facts

    if pyreason_fact.type == 'node':
        f = fact_node.Fact(pyreason_fact.name, pyreason_fact.component, pyreason_fact.label, pyreason_fact.interval, pyreason_fact.t_lower, pyreason_fact.t_upper, pyreason_fact.static)
        if __node_facts is None:
            __node_facts = numba.typed.List.empty_list(fact_node.fact_type)
        __node_facts.append(f)

    else:
        f = fact_edge.Fact(pyreason_fact.name, pyreason_fact.component, pyreason_fact.label, pyreason_fact.interval, pyreason_fact.t_lower, pyreason_fact.t_upper, pyreason_fact.static)
        if __edge_facts is None:
            __edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)
        __edge_facts.append(f)


def add_annotation_function(function: Callable) -> None:
    """Function to add annotation functions to PyReason. The added functions can be used in rules

    :param function: Function to be added. This has to be under a numba `njit` decorator. function has signature: two parameters as input -- annotations, weights
    :type function: Callable
    :return: None
    """
    global __annotation_functions
    # Make sure that the functions are jitted so that they can be passed around in other jitted functions
    # TODO: Remove if necessary
    # assert hasattr(function, 'nopython_signatures'), 'The function to be added has to be under a `numba.njit` decorator'

    __annotation_functions.append(function)


def reason(timesteps: int=-1, convergence_threshold: int=-1, convergence_bound_threshold: float=-1, again: bool=False, node_facts: List[Type[fact_node.Fact]]=None, edge_facts: List[Type[fact_edge.Fact]]=None):
    """Function to start the main reasoning process. Graph and rules must already be loaded.

    :param timesteps: Max number of timesteps to run. -1 specifies run till convergence. If reasoning again, this is the number of timesteps to reason for extra (no zero timestep), defaults to -1
    :param convergence_threshold: Maximim number of interpretations that have changed between timesteps or fixed point operations until considered convergent. Program will end at convergence. -1 => no changes, perfect convergence, defaults to -1
    :param convergence_bound_threshold: Maximum change in any interpretation (bounds) between timesteps or fixed point operations until considered convergent, defaults to -1
    :param again: Whether to reason again on an existing interpretation, defaults to False
    :param node_facts: New node facts to use during the next reasoning process. Other facts from file will be discarded, defaults to None
    :param edge_facts: New edge facts to use during the next reasoning process. Other facts from file will be discarded, defaults to None
    :return: The final interpretation after reasoning.
    """
    global settings, __timestamp

    # Timestamp for saving files
    __timestamp = time.strftime('%Y%m%d-%H%M%S')

    if settings.output_to_file:
        sys.stdout = open(f"./{settings.output_file_name}_{__timestamp}.txt", "a")

    if not again or __program is None:
        if settings.memory_profile:
            start_mem = mp.memory_usage(max_usage=True)
            mem_usage, interp = mp.memory_usage((_reason, [timesteps, convergence_threshold, convergence_bound_threshold]), max_usage=True, retval=True)
            print(f"\nProgram used {mem_usage-start_mem} MB of memory")
        else:
            interp = _reason(timesteps, convergence_threshold, convergence_bound_threshold)
    else:
        if settings.memory_profile:
            start_mem = mp.memory_usage(max_usage=True)
            mem_usage, interp = mp.memory_usage((_reason_again, [timesteps, convergence_threshold, convergence_bound_threshold, node_facts, edge_facts]), max_usage=True, retval=True)
            print(f"\nProgram used {mem_usage-start_mem} MB of memory")
        else:
            interp = _reason_again(timesteps, convergence_threshold, convergence_bound_threshold, node_facts, edge_facts)
        
    return interp


def _reason(timesteps, convergence_threshold, convergence_bound_threshold):
    # Globals
    global __graph, __rules, __node_facts, __edge_facts, __ipl, __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels, __graphml_parser
    global settings, __timestamp, __program

    # Assert variables are of correct type

    if settings.output_to_file:
        sys.stdout = open(f"./{settings.output_file_name}_{__timestamp}.txt", "a")

    # Check variables that HAVE to be set. Exceptions
    if __graph is None:
        raise Exception('Graph not loaded. Use `load_graph` to load the graphml file')
    if __rules is None:
        raise Exception('There are no rules, use `add_rule` or `add_rules_from_file`')

    # Check variables that are highly recommended. Warnings
    if __node_labels is None and __edge_labels is None:
        __node_labels = numba.typed.List.empty_list(label.label_type)
        __edge_labels = numba.typed.List.empty_list(label.label_type)
        __specific_node_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.string))
        __specific_edge_labels = numba.typed.Dict.empty(key_type=label.label_type, value_type=numba.types.ListType(numba.types.Tuple((numba.types.string, numba.types.string))))

    if __node_facts is None:
        __node_facts = numba.typed.List.empty_list(fact_node.fact_type)
    if __edge_facts is None:
        __edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)

    if __ipl is None:
        __ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))

    # If graph attribute parsing, add results to existing specific labels and facts
    for label_name, nodes in __specific_graph_node_labels.items():
        if label_name in __specific_node_labels:
            __specific_node_labels[label_name].extend(nodes)
        else:
            __specific_node_labels[label_name] = nodes

    for label_name, edges in __specific_graph_edge_labels.items():
        if label_name in __specific_edge_labels:
            __specific_edge_labels[label_name].extend(edges)
        else:
            __specific_edge_labels[label_name] = edges

    all_node_facts = numba.typed.List.empty_list(fact_node.fact_type)
    all_edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)
    all_node_facts.extend(numba.typed.List(__node_facts))
    all_edge_facts.extend(numba.typed.List(__edge_facts))
    all_node_facts.extend(__non_fluent_graph_facts_node)
    all_edge_facts.extend(__non_fluent_graph_facts_edge)

    # Atom trace cannot be true when store interpretations is false
    if not settings.store_interpretation_changes:
        settings.atom_trace = False

    # Convert list of annotation functions into tuple to be numba compatible
    annotation_functions = tuple(__annotation_functions)

    # Setup logical program
    __program = Program(__graph, all_node_facts, all_edge_facts, __rules, __ipl, annotation_functions, settings.reverse_digraph, settings.atom_trace, settings.save_graph_attributes_to_trace, settings.canonical, settings.inconsistency_check, settings.store_interpretation_changes, settings.parallel_computing, settings.update_mode)
    __program.available_labels_node = __node_labels
    __program.available_labels_edge = __edge_labels
    __program.specific_node_labels = __specific_node_labels
    __program.specific_edge_labels = __specific_edge_labels

    # Run Program and get final interpretation
    interpretation = __program.reason(timesteps, convergence_threshold, convergence_bound_threshold, settings.verbose)

    return interpretation


def _reason_again(timesteps, convergence_threshold, convergence_bound_threshold, node_facts, edge_facts):
    # Globals
    global __graph, __rules, __node_facts, __edge_facts, __ipl, __node_labels, __edge_labels, __specific_node_labels, __specific_edge_labels, __graphml_parser
    global settings, __timestamp, __program

    assert __program is not None, 'To run `reason_again` you need to have reasoned once before'

    # Extend current set of facts with the new facts supplied
    all_edge_facts = numba.typed.List.empty_list(fact_edge.fact_type)
    all_node_facts = numba.typed.List.empty_list(fact_node.fact_type)
    if node_facts is not None:
        all_node_facts.extend(numba.typed.List(node_facts))
    if edge_facts is not None:
        all_edge_facts.extend(numba.typed.List(edge_facts))

    # Run Program and get final interpretation
    interpretation = __program.reason_again(timesteps, convergence_threshold, convergence_bound_threshold, all_node_facts, all_edge_facts, settings.verbose)

    return interpretation


def save_rule_trace(interpretation, folder: str='./'):
    """Saves the trace of the program. This includes every change that has occurred to the interpretation. If `atom_trace` was set to true
    this gives us full explainability of why interpretations changed

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :param folder: the folder in which to save the result, defaults to './'
    """
    global __timestamp, settings

    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to save rule trace'

    output = Output(__timestamp)
    output.save_rule_trace(interpretation, folder)


def get_rule_trace(interpretation) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns the trace of the program as 2 pandas dataframes (one for nodes, one for edges).
    This includes every change that has occurred to the interpretation. If `atom_trace` was set to true
    this gives us full explainability of why interpretations changed

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :returns two pandas dataframes (nodes, edges) representing the changes that occurred during reasoning
    """
    global __timestamp, settings

    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to save rule trace'

    output = Output(__timestamp)
    return output.get_rule_trace(interpretation)


def filter_and_sort_nodes(interpretation, labels: List[str], bound: interval.Interval=interval.closed(0,1), sort_by: str='lower', descending: bool=True):
    """Filters and sorts the node changes in the interpretation and returns as a list of Pandas dataframes that are easy to access

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :param labels: A list of strings, labels that are in the interpretation that are to be filtered
    :param bound: The bound that will filter any interpretation that is not in it. the default does not filter anything, defaults to interval.closed(0,1)
    :param sort_by: String that is either 'lower' or 'upper', sorts by the lower/upper bound, defaults to 'lower'
    :param descending: A bool that sorts by descending/ascending order, defaults to True
    :return: A list of Pandas dataframes that contain the filtered and sorted interpretations that are easy to access
    """
    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to filter and sort nodes'
    filterer = Filter(interpretation.time)
    filtered_df = filterer.filter_and_sort_nodes(interpretation, labels, bound, sort_by, descending)
    return filtered_df


def filter_and_sort_edges(interpretation, labels: List[str], bound: interval.Interval=interval.closed(0,1), sort_by: str='lower', descending: bool=True):
    """Filters and sorts the edge changes in the interpretation and returns as a list of Pandas dataframes that are easy to access

    :param interpretation: the output of `pyreason.reason()`, the final interpretation
    :param labels: A list of strings, labels that are in the interpretation that are to be filtered
    :param bound: The bound that will filter any interpretation that is not in it. the default does not filter anything, defaults to interval.closed(0,1)
    :param sort_by: String that is either 'lower' or 'upper', sorts by the lower/upper bound, defaults to 'lower'
    :param descending: A bool that sorts by descending/ascending order, defaults to True
    :return: A list of Pandas dataframes that contain the filtered and sorted interpretations that are easy to access
    """
    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to filter and sort edges'
    filterer = Filter(interpretation.time)
    filtered_df = filterer.filter_and_sort_edges(interpretation, labels, bound, sort_by, descending)
    return filtered_df
