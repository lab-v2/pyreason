"""
Unit tests for pyreason input validation and edge cases.
Tests parameter validation, boundary conditions, and error handling across all API functions.
"""

import pytest
import networkx as nx
import pyreason as pr


class TestParameterValidation:
    """Test parameter validation across all pyreason functions."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_rule_parameter_validation(self):
        """Test Rule object parameter validation."""
        # Valid rule creation
        rule = pr.Rule('test(x) <- fact(x)', 'test_rule')
        assert rule is not None

        # Test with None parameters
        with pytest.raises((TypeError, ValueError, AttributeError)):
            pr.Rule(None)


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_numeric_extremes(self):
        """Test numeric extreme values."""
        


class TestTypeValidation:
    """Test type validation across all functions."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_wrong_object_types_for_add_operations(self):
        """Test passing wrong object types to add functions."""
        # Wrong type for add_rule
        with pytest.raises((TypeError, AttributeError)):
            pr.add_rule("string_instead_of_rule")

        with pytest.raises((TypeError, AttributeError)):
            pr.add_rule(123)

        # Wrong type for add_fact
        with pytest.raises((TypeError, AttributeError)):
            pr.add_fact("string_instead_of_fact")

        with pytest.raises((TypeError, AttributeError)):
            pr.add_fact(123)


class TestStateValidation:
    """Test validation of system state before operations."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_operations_after_reset_validation(self):
        """Test that operations work correctly after reset."""
        # Add some content
        rule = pr.Rule('test(x) <- fact(x)')
        fact = pr.Fact('fact(node1)')
        pr.add_rule(rule)
        pr.add_fact(fact)

        # Reset
        pr.reset()

        # Operations should still work
        new_rule = pr.Rule('new_test(x) <- new_fact(x)')
        new_fact = pr.Fact('new_fact(node1)')
        pr.add_rule(new_rule)
        pr.add_fact(new_fact)


class TestConcurrentModification:
    """Test behavior under concurrent modification scenarios."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()


    def test_modifying_settings_during_operations(self):
        """Test modifying settings during other operations."""
        # Load graph
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        # Change settings
        pr.settings.verbose = True
        pr.settings.memory_profile = False

        # Add rule
        rule = pr.Rule('test(x) <- fact(x)')
        pr.add_rule(rule)

        # Change settings again
        pr.settings.graph_attribute_parsing = False

class TestErrorRecovery:
    """Test system recovery from various error conditions."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_recovery_after_invalid_operations(self):
        """Test that system recovers after invalid operations."""
        # Try invalid operations
        try:
            pr.add_rule(None)
        except Exception:
            pass

        try:
            pr.load_graph("invalid")
        except Exception:
            pass

        # Valid operations should still work
        valid_rule = pr.Rule('test(x) <- fact(x)')
        valid_fact = pr.Fact('fact(node1)')
        valid_graph = nx.DiGraph()
        valid_graph.add_edge('A', 'B')

        pr.add_rule(valid_rule)
        pr.add_fact(valid_fact)
        pr.load_graph(valid_graph)

    def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        # Successfully add some content
        rule = pr.Rule('test(x) <- fact(x)')
        pr.add_rule(rule)

        # Try to load invalid file
        try:
            pr.load_graphml('nonexistent.graphml')
        except Exception:
            pass

        # System should still be functional
        fact = pr.Fact('fact(node1)')
        pr.add_fact(fact)

        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

    def test_reset_after_errors(self):
        """Test that reset works after various errors."""

        # Cause various errors
        try:
            pr.add_rule(None)
        except Exception:
            pass

        try:
            pr.load_graph(123)
        except Exception:
            pass

        # Reset should work
        pr.reset()
        pr.reset_settings()

        # System should be clean and functional
        rule = pr.Rule('test(x) <- fact(x)')
        pr.add_rule(rule)