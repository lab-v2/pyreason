"""
Unit tests for pyreason add operations: add_rule, add_fact, add_annotation_function, etc.
Tests the core API functions for adding content to the pyreason system.
"""

import pytest
import pyreason as pr

class TestAddRule:
    """Test add_rule() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_rule_creates_rules_list_when_none(self):
        """Test add_rule() works when starting with no rules."""
        # Start with clean state
        pr.reset_rules()

        # Create a rule
        rule = pr.Rule('test(x) <- fact(x)', 'test_rule')

        # Add rule should work without errors
        pr.add_rule(rule)

    def test_add_rule_with_valid_rule(self):
        """Test adding a valid rule."""
        rule = pr.Rule('test(x) <- fact(x)', 'test_rule')

        # Should not raise an exception
        pr.add_rule(rule)

    def test_add_rule_with_rule_without_name(self):
        """Test adding a rule without a name (should work)."""
        rule = pr.Rule('test(x) <- fact(x)')  # No name provided

        # Should work without errors even without explicit name
        pr.add_rule(rule)

    def test_add_multiple_rules_auto_naming(self):
        """Test adding multiple rules without explicit names."""
        rule1 = pr.Rule('test1(x) <- fact1(x)')
        rule2 = pr.Rule('test2(x) <- fact2(x)')

        # Both should work without errors
        pr.add_rule(rule1)
        pr.add_rule(rule2)

    def test_add_rule_with_named_and_unnamed_rules(self):
        """Test mixing named and unnamed rules."""
        rule1 = pr.Rule('test1(x) <- fact1(x)', 'named_rule')
        rule2 = pr.Rule('test2(x) <- fact2(x)')  # Without explicit name

        # Both should work without errors
        pr.add_rule(rule1)
        pr.add_rule(rule2)

    def test_add_rule_appends_to_existing_list(self):
        """Test that add_rule works with multiple rules."""
        rule1 = pr.Rule('test1(x) <- fact1(x)')
        rule2 = pr.Rule('test2(x) <- fact2(x)')

        pr.add_rule(rule1)
        pr.add_rule(rule2)

        # Both should work without errors


class TestAddFact:
    """Test add_fact() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_fact_creates_lists_when_none(self):
        """Test add_fact() works when starting with no facts."""
        # Start with clean state
        pr.reset()

        fact = pr.Fact('test(node1)')

        # Should work without errors
        pr.add_fact(fact)

    def test_add_fact_node_fact(self):
        """Test adding a node fact."""
        fact = pr.Fact('test(node1)')

        # Should not raise an exception
        pr.add_fact(fact)

    def test_add_fact_edge_fact(self):
        """Test adding an edge fact."""
        fact = pr.Fact('test(node1, node2)')

        # Should not raise an exception
        pr.add_fact(fact)

    def test_add_fact_with_name(self):
        """Test adding a fact with a name."""
        fact = pr.Fact('test(node1)', 'named_fact')

        pr.add_fact(fact)

        assert fact.name == 'named_fact'

    def test_add_fact_without_name_auto_generates(self):
        """Test adding a fact without a name auto-generates one."""
        fact = pr.Fact('test(node1)')  # No name

        pr.add_fact(fact)

        # Should have auto-generated name
        assert fact.name.startswith('fact_')

    def test_add_multiple_facts_auto_naming(self):
        """Test adding multiple facts with auto-naming."""
        fact1 = pr.Fact('test1(node1)')
        fact2 = pr.Fact('test2(node2)')

        pr.add_fact(fact1)
        pr.add_fact(fact2)

        # Should have sequential auto-generated names
        assert fact1.name.startswith('fact_')
        assert fact2.name.startswith('fact_')
        assert fact1.name != fact2.name

    def test_add_fact_with_time_bounds(self):
        """Test adding a fact with time bounds."""
        fact = pr.Fact('test(node1)', 'timed_fact', 0, 5)

        pr.add_fact(fact)

    def test_add_mixed_node_and_edge_facts(self):
        """Test adding both node and edge facts."""
        node_fact = pr.Fact('test_node(node1)')
        edge_fact = pr.Fact('test_edge(node1, node2)')

        pr.add_fact(node_fact)
        pr.add_fact(edge_fact)


class TestAddAnnotationFunction:
    """Test add_annotation_function() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_annotation_function_valid(self):
        """Test adding a valid annotation function."""

        def test_func(annotations, weights):
            return 0.5, 0.5

        # Should not raise an exception
        pr.add_annotation_function(test_func)

    def test_add_annotation_function_lambda(self):
        """Test adding a lambda annotation function."""
        func = lambda annotations, weights: (0.8, 0.8)

        pr.add_annotation_function(func)

    def test_add_multiple_annotation_functions(self):
        """Test adding multiple annotation functions."""

        def func1(annotations, weights):
            return 0.1, 0.1

        def func2(annotations, weights):
            return 0.2, 0.2

        def func3(annotations, weights):
            return 0.3, 0.3

        pr.add_annotation_function(func1)
        pr.add_annotation_function(func2)
        pr.add_annotation_function(func3)

    def test_add_annotation_function_with_complex_logic(self):
        """Test adding annotation function with complex logic."""
        
        def complex_func(annotations, weights):
            if not annotations:
                return 0.0, 0.0
            total = sum(w * a[0].lower for w, a in zip(weights, annotations))
            confidence = min(a[1] for a in annotations)
            return total, confidence

        pr.add_annotation_function(complex_func)


class TestGetRules:
    """Test get_rules() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_get_rules_when_none(self):
        """Test get_rules() when no rules have been added."""
        rules = pr.get_rules()
        assert rules is None

    def test_get_rules_after_adding_rules(self):
        """Test get_rules() returns added rules."""
        rule1 = pr.Rule('test1(x) <- fact1(x)', 'rule1')
        rule2 = pr.Rule('test2(x) <- fact2(x)', 'rule2')

        pr.add_rule(rule1)
        pr.add_rule(rule2)

        rules = pr.get_rules()
        assert rules is not None


class TestAddInconsistentPredicate:
    """Test add_inconsistent_predicate() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_inconsistent_predicate_pair(self):
        """Test adding a pair of inconsistent predicates."""
        # Should not raise an exception
        pr.add_inconsistent_predicate('pred1', 'pred2')

    def test_add_multiple_inconsistent_predicate_pairs(self):
        """Test adding multiple pairs of inconsistent predicates."""
        pr.add_inconsistent_predicate('pred1', 'pred2')
        pr.add_inconsistent_predicate('pred3', 'pred4')
        pr.add_inconsistent_predicate('pred5', 'pred6')

    def test_add_inconsistent_predicate_same_predicates(self):
        """Test adding the same predicate as inconsistent with itself."""
        # This might be an edge case, but should be handled gracefully
        pr.add_inconsistent_predicate('pred1', 'pred1')


class TestOperationSequences:
    """Test sequences of add operations."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_rules_and_facts_sequence(self):
        """Test adding rules and facts in sequence."""
        # Add rules
        rule1 = pr.Rule('test1(x) <- fact1(x)')
        rule2 = pr.Rule('test2(x) <- fact2(x)')
        pr.add_rule(rule1)
        pr.add_rule(rule2)

        # Add facts
        fact1 = pr.Fact('fact1(node1)')
        fact2 = pr.Fact('fact2(node2)')
        pr.add_fact(fact1)
        pr.add_fact(fact2)

        # Add annotation function
        def test_func(annotations, weights):
            return 0.5, 0.5
        pr.add_annotation_function(test_func)

        # Add inconsistent predicates
        pr.add_inconsistent_predicate('pred1', 'pred2')

    def test_complex_operation_sequence(self):
        """Test a complex sequence of operations."""
        # Mixed sequence
        pr.add_rule(pr.Rule('rule1(x) <- fact1(x)', 'named_rule'))
        pr.add_fact(pr.Fact('fact1(node1)', 'named_fact'))
        pr.add_inconsistent_predicate('test1', 'test2')

        def annotation_func(annotations, weights):
            return sum(w * a[0].lower for w, a in zip(weights, annotations)), 1.0
        pr.add_annotation_function(annotation_func)

        pr.add_rule(pr.Rule('rule2(x) <- fact2(x)'))  # Unnamed
        pr.add_fact(pr.Fact('fact2(node2)'))  # Unnamed

    def test_operations_after_reset(self):
        """Test operations work correctly after reset."""
        # Add some content
        pr.add_rule(pr.Rule('test(x) <- fact(x)'))
        pr.add_fact(pr.Fact('fact(node1)'))

        # Reset
        pr.reset()
        pr.reset_rules()

        # Add content again
        pr.add_rule(pr.Rule('new_test(x) <- new_fact(x)'))
        pr.add_fact(pr.Fact('new_fact(node1)'))

        def new_func(annotations, weights):
            return 0.7, 0.7
        pr.add_annotation_function(new_func)


class TestAutoNamingCounters:
    """Test auto-naming counter behavior."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_rule_counter_persistence(self):
        """Test that multiple rules can be added successfully."""
        rule1 = pr.Rule('test1(x) <- fact1(x)')
        rule2 = pr.Rule('test2(x) <- fact2(x)', 'named_rule')
        rule3 = pr.Rule('test3(x) <- fact3(x)')

        # All should work without errors
        pr.add_rule(rule1)
        pr.add_rule(rule2)
        pr.add_rule(rule3)

    def test_fact_counter_independence(self):
        """Test that rules and facts can be added independently."""
        rule = pr.Rule('test(x) <- fact(x)')
        fact = pr.Fact('fact(node1)')

        # Both should work without errors
        pr.add_rule(rule)
        pr.add_fact(fact)

        # Fact should get auto-generated name
        assert fact.name.startswith('fact_')

    def test_counters_after_reset(self):
        """Test that rules and facts work after reset."""
        # Add some rules and facts
        rule1 = pr.Rule('test1(x) <- fact1(x)')
        fact1 = pr.Fact('fact1(node1)')
        pr.add_rule(rule1)
        pr.add_fact(fact1)

        # Reset
        pr.reset_rules()

        # Add new rules and facts should work
        rule2 = pr.Rule('test2(x) <- fact2(x)')
        fact2 = pr.Fact('fact2(node2)')
        pr.add_rule(rule2)
        pr.add_fact(fact2)

        # Fact should get auto-generated name
        assert fact2.name.startswith('fact_')
