import networkx as nx
import numba

from pyreason.scripts.interpretation.interpretation import Interpretation


class Program:
    available_labels_node = []
    available_labels_edge = []
    specific_node_labels = []
    specific_edge_labels = []

    def __init__(self,
                 graph: nx.Graph,
                 tmax: int,
                 facts_node: numba.typed.List,
                 facts_edge: numba.typed.List,
                 rules: numba.typed.List,
                 ipl: numba.typed.List,
                 reverse_graph: bool,
                 atom_trace: bool,
                 save_graph_attributes_to_rule_trace: bool):
        self._graph = graph
        self._tmax = tmax
        self._facts_node = facts_node
        self._facts_edge = facts_edge
        self._rules = rules
        self._ipl = ipl
        self._reverse_graph = reverse_graph
        self._atom_trace = atom_trace
        self._save_graph_attributes_to_rule_trace = save_graph_attributes_to_rule_trace

    def reason(self,
               convergence_threshold: int,
               convergence_bound_threshold: float,
               verbose: bool = True) -> Interpretation:
        # Set up available labels
        Interpretation.available_labels_node = self.available_labels_node
        Interpretation.available_labels_edge = self.available_labels_edge
        Interpretation.specific_node_labels = self.specific_node_labels
        Interpretation.specific_edge_labels = self.specific_edge_labels

        interp = Interpretation(graph=self._graph,
                                tmax=self._tmax,
                                ipl=self._ipl,
                                reverse_graph=self._reverse_graph,
                                atom_trace=self._atom_trace,
                                save_graph_attributes_to_rule_trace=self._save_graph_attributes_to_rule_trace,
                                convergence_threshold=convergence_threshold,
                                convergence_bound_threshold=convergence_bound_threshold)
        interp.start_fp(facts_node=self._facts_node,
                        facts_edge=self._facts_edge,
                        rules=self._rules,
                        verbose=verbose)

        return interp
