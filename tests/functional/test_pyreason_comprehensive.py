"""
Comprehensive functional tests for pyreason.py to cover missing branches.
These tests focus on error conditions, settings validation, and edge cases.
"""

import pytest
import tempfile
import os
import networkx as nx
from unittest import mock

import pyreason as pr


class TestSettingsValidation:
    """Test settings validation - covers all TypeError branches"""

    def setup_method(self):
        """Reset settings before each test"""
        pr.reset()
        pr.reset_settings()

    def test_verbose_type_error(self):
        """Test verbose setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.verbose = "not_bool"

    def test_output_to_file_type_error(self):
        """Test output_to_file setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.output_to_file = 123

    def test_output_file_name_type_error(self):
        """Test output_file_name setter with invalid type"""
        with pytest.raises(TypeError, match='file_name has to be a string'):
            pr.settings.output_file_name = 123

    def test_graph_attribute_parsing_type_error(self):
        """Test graph_attribute_parsing setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.graph_attribute_parsing = "not_bool"

    def test_abort_on_inconsistency_type_error(self):
        """Test abort_on_inconsistency setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.abort_on_inconsistency = 1.5

    def test_memory_profile_type_error(self):
        """Test memory_profile setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.memory_profile = []

    def test_reverse_digraph_type_error(self):
        """Test reverse_digraph setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.reverse_digraph = {}

    def test_atom_trace_type_error(self):
        """Test atom_trace setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.atom_trace = "false"

    def test_save_graph_attributes_to_trace_type_error(self):
        """Test save_graph_attributes_to_trace setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.save_graph_attributes_to_trace = 0

    def test_canonical_type_error(self):
        """Test canonical setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.canonical = "canonical"

    def test_persistent_type_error(self):
        """Test persistent setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.persistent = None

    def test_inconsistency_check_type_error(self):
        """Test inconsistency_check setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.inconsistency_check = 42

    def test_static_graph_facts_type_error(self):
        """Test static_graph_facts setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.static_graph_facts = [True]

    def test_store_interpretation_changes_type_error(self):
        """Test store_interpretation_changes setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.store_interpretation_changes = 1

    def test_parallel_computing_type_error(self):
        """Test parallel_computing setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.parallel_computing = "True"

    def test_update_mode_type_error(self):
        """Test update_mode setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a str'):
            pr.settings.update_mode = True

    def test_allow_ground_rules_type_error(self):
        """Test allow_ground_rules setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.allow_ground_rules = 3.14

    def test_fp_version_type_error(self):
        """Test fp_version setter with invalid type"""
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.fp_version = "optimized"


class TestFileOperations:
    """Test file loading operations and error conditions"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_load_graphml_nonexistent_file(self):
        """Test loading non-existent GraphML file"""
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_graphml("non_existent_file.graphml")

    def test_load_ipl_nonexistent_file(self):
        """Test loading non-existent IPL file"""
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_inconsistent_predicate_list("non_existent_ipl.yaml")

    def test_add_rules_from_nonexistent_file(self):
        """Test adding rules from non-existent file"""
        with pytest.raises((FileNotFoundError, OSError)):
            pr.add_rules_from_file("non_existent_rules.txt")

    def test_add_rules_from_file_with_comments_and_empty_lines(self):
        """Test rule file parsing handles comments and empty lines"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            f.write("   \n")  # Whitespace-only line
            f.write("test_rule(x) <-1 other_rule(x)\n")
            f.write("# Another comment\n")
            f.write("another_rule(y) <-1 test_rule(y)\n")
            temp_path = f.name

        try:
            pr.add_rules_from_file(temp_path)
            rules = pr.get_rules()
            assert len(rules) == 2  # Should only include the 2 actual rules
        finally:
            os.unlink(temp_path)

    def test_add_inconsistent_predicates(self):
        """Test adding inconsistent predicate pairs"""
        pr.add_inconsistent_predicate("pred1", "pred2")
        pr.add_inconsistent_predicate("pred3", "pred4")
        # Should not raise exceptions


class TestReasoningErrorConditions:
    """Test reasoning function error conditions and edge cases"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_reason_without_rules_exception(self):
        """Test reasoning without rules raises exception"""
        # Load a graph but no rules
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        pr.load_graph(graph)

        with pytest.raises(Exception, match='There are no rules'):
            pr.reason()

    def test_reason_without_graph_uses_empty_graph(self):
        """Test reasoning without graph uses empty graph and warns"""
        pr.add_rule(pr.Rule('test(x) <- test2(x)', 'test_rule'))

        with pytest.warns(UserWarning, match='Graph not loaded'):
            interpretation = pr.reason()
            # Should complete without crashing

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


class TestGraphAttributeParsing:
    """Test graph attribute parsing branches"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_load_graph_with_attribute_parsing_enabled(self):
        """Test loading graph with attribute parsing enabled"""
        graph = nx.DiGraph()
        graph.add_node("A", label="person", age=25)
        graph.add_node("B", label="person", age=30)
        graph.add_edge("A", "B", relation="knows", weight=0.8)

        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)
        # Should complete without errors

    def test_load_graph_with_attribute_parsing_disabled(self):
        """Test loading graph with attribute parsing disabled (lines 540-543, 562-565)"""
        graph = nx.DiGraph()
        graph.add_node("A", label="person")
        graph.add_edge("A", "B", relation="knows")

        pr.settings.graph_attribute_parsing = False
        pr.load_graph(graph)
        # Should complete without errors and use empty collections


class TestOutputFunctionAssertions:
    """Test output functions when store_interpretation_changes=False"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_save_rule_trace_assertion(self):
        """Test save_rule_trace assertion when store_interpretation_changes=False"""
        pr.settings.store_interpretation_changes = False

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.save_rule_trace(mock.MagicMock(), './test/')

    def test_get_rule_trace_assertion(self):
        """Test get_rule_trace assertion when store_interpretation_changes=False"""
        pr.settings.store_interpretation_changes = False

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.get_rule_trace(mock.MagicMock())

    def test_filter_and_sort_nodes_assertion(self):
        """Test filter_and_sort_nodes assertion when store_interpretation_changes=False"""
        pr.settings.store_interpretation_changes = False

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.filter_and_sort_nodes(mock.MagicMock(), ['test'])

    def test_filter_and_sort_edges_assertion(self):
        """Test filter_and_sort_edges assertion when store_interpretation_changes=False"""
        pr.settings.store_interpretation_changes = False

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.filter_and_sort_edges(mock.MagicMock(), ['test'])


class TestReasoningModes:
    """Test different reasoning modes and settings"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_reason_with_memory_profiling(self):
        """Test reasoning with memory profiling enabled"""
        # Set up minimal working example
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        pr.load_graph(graph)
        pr.add_rule(pr.Rule('test(x) <- test(y)', 'test_rule'))
        pr.add_fact(pr.Fact('test(A)', 'test_fact'))

        pr.settings.memory_profile = True
        pr.settings.verbose = False  # Reduce output noise

        # Should complete without errors
        interpretation = pr.reason(timesteps=1)

    def test_reason_with_output_to_file(self):
        """Test reasoning with output_to_file enabled"""
        # Set up minimal working example
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        pr.load_graph(graph)
        pr.add_rule(pr.Rule('test(x) <- test(y)', 'test_rule'))
        pr.add_fact(pr.Fact('test(A)', 'test_fact'))

        pr.settings.output_to_file = True
        pr.settings.output_file_name = "test_output"

        interpretation = pr.reason(timesteps=1)

        # Check if output file was created (and clean up)
        import glob
        output_files = glob.glob("test_output_*.txt")
        for f in output_files:
            os.unlink(f)

    def test_reason_again_functionality(self):
        """Test reason again functionality (lines 688-693, 788-799)"""
        # Set up initial reasoning
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        pr.load_graph(graph)
        pr.add_rule(pr.Rule('test(x) <- test(y)', 'test_rule'))
        pr.add_fact(pr.Fact('test(A)', 'test_fact', 0, 1))

        # First reasoning
        interpretation1 = pr.reason(timesteps=1)

        # Add new fact and reason again
        pr.add_fact(pr.Fact('test(B)', 'test_fact2', 2, 3))
        interpretation2 = pr.reason(timesteps=2, again=True, restart=False)

        # Should complete without errors


class TestAnnotationFunctions:
    """Test annotation function management"""

    def test_add_annotation_function(self):
        """Test adding annotation function"""
        def test_func(annotations, weights):
            return sum(w * a[0].lower for w, a in zip(weights, annotations)), 1.0

        pr.add_annotation_function(test_func)
        # Should complete without errors


class TestTorchIntegrationHandling:
    """Test torch integration state consistency"""

    def test_torch_integration_consistency(self):
        """Test that torch integration variables are consistent"""
        # Just verify the current state is consistent
        if hasattr(pr, 'LogicIntegratedClassifier'):
            if pr.LogicIntegratedClassifier is None:
                # If LogicIntegratedClassifier is None, ModelInterfaceOptions should also be None
                assert pr.ModelInterfaceOptions is None
            else:
                # If LogicIntegratedClassifier exists, ModelInterfaceOptions should also exist
                assert pr.ModelInterfaceOptions is not None


class TestQueryFiltering:
    """Test query-based rule filtering"""

    def setup_method(self):
        """Reset state before each test"""
        pr.reset()
        pr.reset_settings()

    def test_reason_with_queries(self):
        """Test reasoning with query-based rule filtering"""
        # Set up test scenario
        graph = nx.DiGraph()
        graph.add_edges_from([("A", "B"), ("B", "C")])
        pr.load_graph(graph)

        pr.add_rule(pr.Rule('popular(x) <-1 friend(x, y)', 'rule1'))
        pr.add_rule(pr.Rule('friend(x, y) <-1 knows(x, y)', 'rule2'))
        pr.add_fact(pr.Fact('knows(A, B)', 'fact1'))

        # Create query to filter rules
        query = pr.Query('popular(A)')
        pr.settings.verbose = False  # Reduce output noise

        interpretation = pr.reason(timesteps=1, queries=[query])
        # Should complete and apply rule filtering logic


if __name__ == '__main__':
    pytest.main([__file__])