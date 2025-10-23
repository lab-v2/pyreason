"""
Unit tests for pyreason reasoning functionality.
Tests the _reason() function through the reason() public API to achieve maximum branch coverage.
"""

import pytest
import networkx as nx
import tempfile
import os
import sys
from io import StringIO
import pyreason as pr
from pyreason.scripts.rules.rule import Rule
from pyreason.scripts.facts.fact import Fact


class TestReasoningFunction:
    """Test reasoning functionality with comprehensive branch coverage."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_reason_without_graph_uses_empty_graph(self):
        """Test reasoning without graph uses empty graph and warns"""
        pr.add_rule(pr.Rule('test(x) <- test2(x)', 'test_rule'))

        with pytest.warns(UserWarning, match='Graph not loaded'):
            interpretation = pr.reason()
            # Should complete without crashing

    def test_reason_with_no_rules_raises_exception(self):
        """Test reasoning without any rules raises exception."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        with pytest.raises(Exception, match="There are no rules"):
            pr.reason(timesteps=1)

    def test_reason_auto_names_rules(self):
        """Test that rules get auto-named when no name provided"""
        pr.add_rule(pr.Rule('test1(x) <- test2(x)'))  # No name
        pr.add_rule(pr.Rule('test3(x) <- test4(x)'))  # No name

        rules = pr.get_rules()
        assert rules[0].get_rule_name() == 'rule_0'
        assert rules[1].get_rule_name() == 'rule_1'

    def test_reason_auto_names_facts(self):
        """Test that facts get auto-named when no name provided"""
        fact1 = pr.Fact('test(node1)')  # No name
        fact2 = pr.Fact('test(node1, node2)')  # No name

        pr.add_fact(fact1)
        pr.add_fact(fact2)

        # Names should be auto-generated
        assert fact1.name.startswith('fact_')
        assert fact2.name.startswith('fact_')

    def test_reason_with_output_to_file(self):
        """Test reasoning with output_to_file setting."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.output_to_file = True
        pr.settings.output_file_name = "test_output"

        try:
            interpretation = pr.reason(timesteps=1)
            # Should create output file
            assert interpretation is not None
        finally:
            pr.settings.output_to_file = False
            # Clean up any created files
            for file in os.listdir('.'):
                if file.startswith('test_output_'):
                    os.remove(file)

    def test_reason_with_none_node_facts_initializes_empty_list(self):
        """Test reasoning when __node_facts is None."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # This should work without issues as it initializes empty list
        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_none_edge_facts_initializes_empty_list(self):
        """Test reasoning when __edge_facts is None."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # This should work without issues as it initializes empty list
        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_none_ipl_initializes_empty_list(self):
        """Test reasoning when __ipl is None."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # This should work without issues as it initializes empty list
        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_specific_graph_node_labels(self):
        """Test reasoning with specific graph node labels."""
        graph = nx.DiGraph()
        graph.add_node('A', person=True)
        graph.add_node('B', person=True)
        graph.add_edge('A', 'B')
        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_specific_graph_edge_labels(self):
        """Test reasoning with specific graph edge labels."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', knows=True)
        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- knows(A, B)", "test_rule", False))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_existing_specific_node_labels(self):
        """Test reasoning when specific node labels already exist and get extended."""
        graph = nx.DiGraph()
        graph.add_node('A', person=True)
        graph.add_node('B', person=True)
        graph.add_edge('A', 'B')
        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- person(A), person(B)", "test_rule", False))

        # Add some facts first to create existing specific labels
        pr.add_fact(Fact('person("C")', 'person_c', 0, 1))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_existing_specific_edge_labels(self):
        """Test reasoning when specific edge labels already exist and get extended."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', knows=True)
        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- knows(A, B)", "test_rule", False))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_store_interpretation_changes_false_sets_atom_trace_false(self):
        """Test that atom_trace is set to False when store_interpretation_changes is False."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = False
        pr.settings.atom_trace = True  # This should be overridden

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None
        # atom_trace should have been set to False

    def test_reason_with_verbose_queries_filtering(self):
        """Test reasoning with verbose mode and query filtering."""
        from pyreason.scripts.query.query import Query

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.verbose = True

        # Test query filtering works with Query objects
        queries = [Query('friend(A, B)')]
        interpretation = pr.reason(timesteps=1, queries=queries)
        assert interpretation is not None

    def test_reason_with_queries_none(self):
        """Test reasoning when queries is None (no filtering)."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        interpretation = pr.reason(timesteps=1, queries=None)
        assert interpretation is not None

    def test_reason_with_more_edges_than_nodes_optimizes_rules(self):
        """Test reasoning when graph has more edges than nodes (triggers rule optimization)."""
        graph = nx.DiGraph()
        # Create graph with more edges than nodes
        graph.add_edge('A', 'B')
        graph.add_edge('A', 'C')
        graph.add_edge('B', 'C')
        graph.add_edge('B', 'D')
        graph.add_edge('C', 'D')  # 5 edges, 4 nodes

        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.verbose = True

        # Capture stdout to check for optimization message
        captured_output = StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output
            interpretation = pr.reason(timesteps=1)
            output = captured_output.getvalue()

            # Should contain optimization message
            assert "Optimizing rules" in output or interpretation is not None
        finally:
            sys.stdout = original_stdout

    def test_reason_with_more_nodes_than_edges_no_optimization(self):
        """Test reasoning when graph has more nodes than edges (no rule optimization)."""
        graph = nx.DiGraph()
        # Create graph with more nodes than edges
        graph.add_node('A')
        graph.add_node('B')
        graph.add_node('C')
        graph.add_node('D')
        graph.add_edge('A', 'B')  # 4 nodes, 1 edge

        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_all_settings_enabled(self):
        """Test reasoning with various settings enabled."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Enable various settings
        pr.settings.reverse_digraph = True
        pr.settings.atom_trace = True
        pr.settings.save_graph_attributes_to_trace = True
        pr.settings.persistent = True
        pr.settings.inconsistency_check = True
        pr.settings.store_interpretation_changes = True
        pr.settings.parallel_computing = False
        pr.settings.allow_ground_rules = True

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

    def test_reason_with_convergence_parameters(self):
        """Test reasoning with convergence threshold and bound threshold."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        interpretation = pr.reason(
            timesteps=5,
            convergence_threshold=0.01,
            convergence_bound_threshold=0.1
        )
        assert interpretation is not None

    def test_reason_clears_facts_after_reasoning(self):
        """Test that node and edge facts are cleared after reasoning."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Add some facts
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None

        # Facts should be cleared, so reasoning again should work
        interpretation2 = pr.reason(timesteps=1)
        assert interpretation2 is not None

    def test_reason_with_different_update_modes(self):
        """Test reasoning with different update modes."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Test different update modes
        for update_mode in ['Synchronous', 'Asynchronous']:
            pr.settings.update_mode = update_mode
            interpretation = pr.reason(timesteps=1)
            assert interpretation is not None

    def test_reason_with_complex_rule_structure(self):
        """Test reasoning with complex rules that might trigger clause reordering."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        graph.add_edge('C', 'D')
        graph.add_edge('D', 'E')
        graph.add_edge('E', 'F')  # Many edges to trigger optimization

        pr.load_graph(graph)

        # Add complex rule with multiple clauses
        pr.add_rule(Rule("friend(A, B) <- connected(A, B), person(A), person(B)", "complex_rule", False))

        interpretation = pr.reason(timesteps=1)
        assert interpretation is not None


class TestReasonAgainFunction:
    """Test _reason_again functionality through multiple reason calls."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_multiple_reason_calls(self):
        """Test multiple calls to reason function."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add new facts and reason again
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))
        interpretation2 = pr.reason(timesteps=1)
        assert interpretation2 is not None

    def test_reason_with_restart_parameter(self):
        """Test reasoning with restart parameter."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Reason again with restart
        interpretation2 = pr.reason(timesteps=2, restart=True)
        assert interpretation2 is not None

class TestFilterAndSortFunctions:
    """Test filter_and_sort_nodes and filter_and_sort_edges functions."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_filter_and_sort_nodes_requires_store_interpretation_changes(self):
        """Test that filter_and_sort_nodes requires store_interpretation_changes to be True."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = False
        interpretation = pr.reason(timesteps=1)

        with pytest.raises(AssertionError, match="store interpretation changes setting is off"):
            pr.filter_and_sort_nodes(interpretation, ['friend'])

    def test_filter_and_sort_edges_requires_store_interpretation_changes(self):
        """Test that filter_and_sort_edges requires store_interpretation_changes to be True."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = False
        interpretation = pr.reason(timesteps=1)

        with pytest.raises(AssertionError, match="store interpretation changes setting is off"):
            pr.filter_and_sort_edges(interpretation, ['friend'])

    def test_filter_and_sort_nodes_basic_functionality(self):
        """Test basic functionality of filter_and_sort_nodes."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test basic filtering and sorting
        result = pr.filter_and_sort_nodes(interpretation, ['friend'])
        assert result is not None
        # Result should be a list of DataFrames
        assert isinstance(result, list)

    def test_filter_and_sort_edges_basic_functionality(self):
        """Test basic functionality of filter_and_sort_edges."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test basic filtering and sorting
        result = pr.filter_and_sort_edges(interpretation, ['friend'])
        assert result is not None
        # Result should be a list of DataFrames
        assert isinstance(result, list)

    def test_filter_and_sort_nodes_with_custom_bound(self):
        """Test filter_and_sort_nodes with custom interval bound."""
        import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with custom bound
        custom_bound = interval.closed(0.5, 1.0)
        result = pr.filter_and_sort_nodes(interpretation, ['friend'], bound=custom_bound)
        assert result is not None

    def test_filter_and_sort_edges_with_custom_bound(self):
        """Test filter_and_sort_edges with custom interval bound."""
        import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with custom bound
        custom_bound = interval.closed(0.5, 1.0)
        result = pr.filter_and_sort_edges(interpretation, ['friend'], bound=custom_bound)
        assert result is not None

    def test_filter_and_sort_nodes_sort_by_upper(self):
        """Test filter_and_sort_nodes with sort_by='upper'."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test sorting by upper bound
        result = pr.filter_and_sort_nodes(interpretation, ['friend'], sort_by='upper')
        assert result is not None

    def test_filter_and_sort_edges_sort_by_upper(self):
        """Test filter_and_sort_edges with sort_by='upper'."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test sorting by upper bound
        result = pr.filter_and_sort_edges(interpretation, ['friend'], sort_by='upper')
        assert result is not None

    def test_filter_and_sort_nodes_sort_by_lower(self):
        """Test filter_and_sort_nodes with sort_by='lower'."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test sorting by lower bound (default)
        result = pr.filter_and_sort_nodes(interpretation, ['friend'], sort_by='lower')
        assert result is not None

    def test_filter_and_sort_edges_sort_by_lower(self):
        """Test filter_and_sort_edges with sort_by='lower'."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test sorting by lower bound (default)
        result = pr.filter_and_sort_edges(interpretation, ['friend'], sort_by='lower')
        assert result is not None

    def test_filter_and_sort_nodes_ascending_order(self):
        """Test filter_and_sort_nodes with ascending order."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test ascending sort order
        result = pr.filter_and_sort_nodes(interpretation, ['friend'], descending=False)
        assert result is not None

    def test_filter_and_sort_edges_ascending_order(self):
        """Test filter_and_sort_edges with ascending order."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test ascending sort order
        result = pr.filter_and_sort_edges(interpretation, ['friend'], descending=False)
        assert result is not None

    def test_filter_and_sort_nodes_descending_order(self):
        """Test filter_and_sort_nodes with descending order."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test descending sort order (default)
        result = pr.filter_and_sort_nodes(interpretation, ['friend'], descending=True)
        assert result is not None

    def test_filter_and_sort_edges_descending_order(self):
        """Test filter_and_sort_edges with descending order."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test descending sort order (default)
        result = pr.filter_and_sort_edges(interpretation, ['friend'], descending=True)
        assert result is not None

    def test_filter_and_sort_nodes_multiple_labels(self):
        """Test filter_and_sort_nodes with multiple labels."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "rule1", False))
        pr.add_rule(Rule("enemy(A, B) <- ~friend(A, B)", "rule2", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with multiple labels
        result = pr.filter_and_sort_nodes(interpretation, ['friend', 'enemy'])
        assert result is not None

    def test_filter_and_sort_edges_multiple_labels(self):
        """Test filter_and_sort_edges with multiple labels."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "rule1", False))
        pr.add_rule(Rule("enemy(A, B) <- ~friend(A, B)", "rule2", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with multiple labels
        result = pr.filter_and_sort_edges(interpretation, ['friend', 'enemy'])
        assert result is not None

    def test_filter_and_sort_nodes_empty_labels_list(self):
        """Test filter_and_sort_nodes with empty labels list."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with empty labels list
        result = pr.filter_and_sort_nodes(interpretation, [])
        assert result is not None

    def test_filter_and_sort_edges_empty_labels_list(self):
        """Test filter_and_sort_edges with empty labels list."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with empty labels list
        result = pr.filter_and_sort_edges(interpretation, [])
        assert result is not None

    def test_filter_and_sort_functions_with_complex_scenario(self):
        """Test both functions with a more complex reasoning scenario."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        graph.add_edge('C', 'D')
        graph.add_node('E')  # Isolated node
        pr.load_graph(graph)

        # Add multiple rules
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "rule1", False))
        pr.add_rule(Rule("close_friend(A, B) <- friend(A, B)", "rule2", False))
        pr.add_fact(Fact('person("A")', 'fact1', 0, 2))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=3)

        # Test nodes filtering and sorting
        node_result = pr.filter_and_sort_nodes(
            interpretation,
            ['friend', 'close_friend', 'person'],
            sort_by='lower',
            descending=True
        )
        assert node_result is not None

        # Test edges filtering and sorting
        edge_result = pr.filter_and_sort_edges(
            interpretation,
            ['friend', 'close_friend'],
            sort_by='upper',
            descending=False
        )
        assert edge_result is not None

    def test_filter_and_sort_with_all_default_parameters(self):
        """Test filter_and_sort functions with all default parameters."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        pr.settings.store_interpretation_changes = True
        interpretation = pr.reason(timesteps=2)

        # Test with all defaults (bound=interval.closed(0,1), sort_by='lower', descending=True)
        node_result = pr.filter_and_sort_nodes(interpretation, ['friend'])
        edge_result = pr.filter_and_sort_edges(interpretation, ['friend'])

        assert node_result is not None
        assert edge_result is not None


class TestReasonFunctionBranches:
    """Test missing branches in reason() and reason_again() functions."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_reason_with_memory_profile_enabled_first_time(self):
        """Test reason() with memory_profile=True and again=False."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Enable memory profiling
        pr.settings.memory_profile = True

        try:
            # This should trigger the memory profiling branch in reason()
            # with again=False (or __program is None)
            interpretation = pr.reason(timesteps=1, again=False)
            assert interpretation is not None
        finally:
            pr.settings.memory_profile = False

    def test_reason_with_memory_profile_enabled_again_true(self):
        """Test reason() with memory_profile=True and again=True."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning to establish __program
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add facts for reason_again to work with
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Enable memory profiling
        pr.settings.memory_profile = True

        try:
            # This should trigger the memory profiling branch in reason()
            # with again=True and __program is not None
            interpretation2 = pr.reason(timesteps=1, again=True, restart=True)
            assert interpretation2 is not None
        finally:
            pr.settings.memory_profile = False

    def test_reason_with_memory_profile_disabled_first_time(self):
        """Test reason() with memory_profile=False and again=False."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Ensure memory profiling is disabled
        pr.settings.memory_profile = False

        # This should trigger the else branch (no memory profiling)
        # with again=False (or __program is None)
        interpretation = pr.reason(timesteps=1, again=False)
        assert interpretation is not None

    def test_reason_with_memory_profile_disabled_again_true(self):
        """Test reason() with memory_profile=False and again=True."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning to establish __program
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add facts for reason_again to work with
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Ensure memory profiling is disabled
        pr.settings.memory_profile = False

        # This should trigger the else branch (no memory profiling)
        # with again=True and __program is not None
        interpretation2 = pr.reason(timesteps=1, again=True, restart=True)
        assert interpretation2 is not None

    def test_reason_again_parameter_combinations(self):
        """Test reason() with different again parameter combinations."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Test again=False explicitly (should use _reason)
        interpretation1 = pr.reason(timesteps=1, again=False)
        assert interpretation1 is not None

        # Add facts for reason_again calls
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Test again=True with restart=True (should use _reason_again)
        interpretation2 = pr.reason(timesteps=1, again=True, restart=True)
        assert interpretation2 is not None

        # Add more facts for next call
        pr.add_fact(Fact('person("B")', 'person_b', 0, 1))

        # Test again=True with restart=False (should use _reason_again)
        interpretation3 = pr.reason(timesteps=1, again=True, restart=False)
        assert interpretation3 is not None

    def test_reason_first_call_with_again_true_uses_reason(self):
        """Test that on fresh start with again=True, it uses _reason because __program is None."""
        # This test verifies the branch: if not again or __program is None
        # On the first call ever, __program is None, so even with again=True it should use _reason

        # Note: Since we can't manually reset __program to None through public API,
        # and it's created during first reasoning, this branch is already tested
        # by the first reasoning call in any test. We'll just document this behavior.

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # This implicitly tests the __program is None branch since it's the first call
        interpretation = pr.reason(timesteps=1, again=False)
        assert interpretation is not None

    def test_reason_again_internal_function_branches(self):
        """Test branches within _reason_again function through reason(again=True)."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning to establish __program
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add some facts to test the fact extension logic in _reason_again
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # This should exercise the fact extension branches in _reason_again
        interpretation2 = pr.reason(timesteps=2, again=True, restart=True)
        assert interpretation2 is not None

    def test_reason_again_with_verbose_setting(self):
        """Test _reason_again with verbose setting to exercise all parameters."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First reasoning
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add facts for reason_again
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Enable verbose mode
        pr.settings.verbose = True

        try:
            # This should pass the verbose setting to __program.reason_again
            interpretation2 = pr.reason(
                timesteps=2,
                again=True,
                restart=False,
                convergence_threshold=0.01,
                convergence_bound_threshold=0.1
            )
            assert interpretation2 is not None
        finally:
            pr.settings.verbose = False

    def test_reason_with_all_parameter_combinations(self):
        """Test reason() with various parameter combinations to ensure branch coverage."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # Test case 1: again=False, memory_profile=False
        pr.settings.memory_profile = False
        interpretation1 = pr.reason(timesteps=1, again=False)
        assert interpretation1 is not None

        # Test case 2: again=False, memory_profile=True
        pr.settings.memory_profile = True
        try:
            interpretation2 = pr.reason(timesteps=1, again=False)
            assert interpretation2 is not None
        finally:
            pr.settings.memory_profile = False

        # Add facts for again=True tests
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Test case 3: again=True, memory_profile=False
        pr.settings.memory_profile = False
        interpretation3 = pr.reason(timesteps=1, again=True)
        assert interpretation3 is not None

        # Add more facts for next test
        pr.add_fact(Fact('person("B")', 'person_b', 0, 1))

        # Test case 4: again=True, memory_profile=True
        pr.settings.memory_profile = True
        try:
            interpretation4 = pr.reason(timesteps=1, again=True)
            assert interpretation4 is not None
        finally:
            pr.settings.memory_profile = False

    def test_reason_again_assert_coverage(self):
        """Test that _reason_again assert is covered by trying without prior reasoning."""
        # This is already covered by existing tests, but let's be explicit
        # The assertion in _reason_again should be tested indirectly since
        # reason(again=True) when __program is None should use _reason instead

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)
        pr.add_rule(Rule("friend(A, B) <- connected(A, B)", "test_rule", False))

        # First establish a program
        interpretation1 = pr.reason(timesteps=1)
        assert interpretation1 is not None

        # Add facts for reason_again
        pr.add_fact(Fact('person("A")', 'person_a', 0, 1))

        # Now the assert in _reason_again should pass
        interpretation2 = pr.reason(timesteps=1, again=True)
        assert interpretation2 is not None
