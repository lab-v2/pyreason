import pytest
from pyreason.scripts.utils.fact_parser import parse_fact
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


# Tests in this class were generated with Claude Sonnet 4.5.
class TestValidFactParsing:
    """Test cases for valid fact inputs that should parse successfully."""

    def test_simple_node_fact_implicit_true(self):
        """Test parsing a simple node fact without explicit bound (defaults to True)."""
        pred, component, bound, fact_type = parse_fact("pred(node)")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 1.0 and bound.upper == 1.0
        assert fact_type == "node"

    def test_simple_node_fact_explicit_true(self):
        """Test parsing a node fact with explicit True bound."""
        pred, component, bound, fact_type = parse_fact("pred(node):True")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 1.0 and bound.upper == 1.0
        assert fact_type == "node"

    def test_simple_node_fact_explicit_false(self):
        """Test parsing a node fact with explicit False bound."""
        pred, component, bound, fact_type = parse_fact("pred(node):False")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 0.0 and bound.upper == 0.0
        assert fact_type == "node"

    def test_negated_node_fact(self):
        """Test parsing a negated node fact (should be False)."""
        pred, component, bound, fact_type = parse_fact("~pred(node)")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 0.0 and bound.upper == 0.0
        assert fact_type == "node"

    def test_node_fact_with_interval_bound(self):
        """Test parsing a node fact with interval bound."""
        pred, component, bound, fact_type = parse_fact("pred(node):[0.5,0.8]")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 0.5 and bound.upper == 0.8
        assert fact_type == "node"

    def test_simple_edge_fact(self):
        """Test parsing a simple edge fact."""
        pred, component, bound, fact_type = parse_fact("pred(node1,node2)")
        assert pred == "pred"
        assert component == ("node1", "node2")
        assert bound.lower == 1.0 and bound.upper == 1.0
        assert fact_type == "edge"

    def test_edge_fact_with_explicit_bound(self):
        """Test parsing an edge fact with explicit bound."""
        pred, component, bound, fact_type = parse_fact("pred(node1,node2):True")
        assert pred == "pred"
        assert component == ("node1", "node2")
        assert bound.lower == 1.0 and bound.upper == 1.0
        assert fact_type == "edge"

    def test_edge_fact_with_interval_bound(self):
        """Test parsing an edge fact with interval bound."""
        pred, component, bound, fact_type = parse_fact("pred(n1,n2):[0.2,0.9]")
        assert pred == "pred"
        assert component == ("n1", "n2")
        assert bound.lower == 0.2 and bound.upper == 0.9
        assert fact_type == "edge"

    def test_fact_with_spaces(self):
        """Test that spaces are properly handled (should be stripped)."""
        pred, component, bound, fact_type = parse_fact("pred ( node ) : True")
        assert pred == "pred"
        assert component == "node"
        assert bound.lower == 1.0 and bound.upper == 1.0
        assert fact_type == "node"

    def test_fact_with_underscores_and_numbers(self):
        """Test parsing facts with underscores and numbers in names."""
        pred, component, bound, fact_type = parse_fact("my_pred_2(node_1)")
        assert pred == "my_pred_2"
        assert component == "node_1"
        assert fact_type == "node"

    def test_predicate_with_trailing_numbers(self):
        """Test that predicates can contain digits after the first character."""
        pred, component, bound, fact_type = parse_fact("pred123(node)")
        assert pred == "pred123"
        assert component == "node"
        assert fact_type == "node"

    def test_predicate_starting_with_underscore(self):
        """Test that predicates can start with an underscore."""
        pred, component, bound, fact_type = parse_fact("_pred(node)")
        assert pred == "_pred"
        assert component == "node"
        assert fact_type == "node"

    def test_interval_with_zeros(self):
        """Test parsing interval bounds with zero values."""
        pred, component, bound, fact_type = parse_fact("pred(node):[0.0,0.0]")
        assert pred == "pred"
        assert bound.lower == 0.0 and bound.upper == 0.0

    def test_interval_with_ones(self):
        """Test parsing interval bounds with one values."""
        pred, component, bound, fact_type = parse_fact("pred(node):[1.0,1.0]")
        assert pred == "pred"
        assert bound.lower == 1.0 and bound.upper == 1.0


# Tests in this class were generated with Claude Sonnet 4.5.
class TestInvalidFactParsing:
    """Test cases for invalid fact inputs that should raise validation errors."""

    def test_missing_opening_parenthesis(self):
        """Test that missing opening parenthesis raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("prednode)")

    def test_missing_closing_parenthesis(self):
        """Test that missing closing parenthesis raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node")

    def test_missing_both_parentheses(self):
        """Test that missing both parentheses raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("prednode")

    def test_empty_predicate(self):
        """Test that empty predicate raises an error."""
        with pytest.raises(ValueError):
            parse_fact("(node)")

    def test_empty_component(self):
        """Test that empty component raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred()")

    def test_empty_string(self):
        """Test that empty string raises an error."""
        with pytest.raises(ValueError):
            parse_fact("")

    def test_only_whitespace(self):
        """Test that whitespace-only string raises an error."""
        with pytest.raises(ValueError):
            parse_fact("   ")

    def test_multiple_colons(self):
        """Test that multiple colons in input raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):True:False")

    def test_invalid_bound_single_value(self):
        """Test that interval bound with single value raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node):[0.5]")

    def test_invalid_bound_three_values(self):
        """Test that interval bound with three values raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node):[0.5,0.6,0.7]")

    def test_invalid_bound_empty_interval(self):
        """Test that empty interval raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node):[]")

    def test_invalid_bound_non_numeric(self):
        """Test that non-numeric interval values raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):[a,b]")

    def test_invalid_bound_text(self):
        """Test that invalid text bound raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):invalid")

    def test_missing_closing_bracket(self):
        """Test that missing closing bracket in interval raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node):[0.5,0.8")

    def test_missing_opening_bracket(self):
        """Test that missing opening bracket in interval raises an error."""
        with pytest.raises((ValueError, IndexError)):
            parse_fact("pred(node):0.5,0.8]")

    def test_interval_lower_greater_than_upper(self):
        """Test that interval with lower > upper raises an error or warning."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):[0.9,0.1]")

    def test_interval_out_of_range_negative(self):
        """Test that interval values < 0 raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):[-0.5,0.5]")

    def test_interval_out_of_range_greater_than_one(self):
        """Test that interval values > 1 raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node):[0.5,1.5]")

    def test_empty_component_in_edge(self):
        """Test that empty component in edge fact raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(,node2)")

    def test_empty_component_in_edge_second(self):
        """Test that empty second component in edge fact raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node1,)")

    def test_empty_both_components_in_edge(self):
        """Test that both empty components in edge fact raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(,)")

    def test_too_many_components_in_edge(self):
        """Test that more than 2 components in edge fact raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node1,node2,node3)")

    def test_negation_with_explicit_bound(self):
        """Test that negation with explicit bound raises an error (ambiguous)."""
        with pytest.raises(ValueError):
            parse_fact("~pred(node):True")

    def test_negation_with_interval_bound(self):
        """Test that negation with interval bound raises an error (ambiguous)."""
        with pytest.raises(ValueError):
            parse_fact("~pred(node):[0.5,0.8]")

    def test_double_negation(self):
        """Test that double negation raises an error."""
        with pytest.raises(ValueError):
            parse_fact("~~pred(node)")

    def test_nested_parentheses(self):
        """Test that nested parentheses raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred((node))")

    def test_special_characters_in_predicate(self):
        """Test that special characters in predicate raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred@#$(node)")

    def test_predicate_starting_with_digit(self):
        """Test that predicate starting with a digit raises an error."""
        with pytest.raises(ValueError):
            parse_fact("123pred(node)")

    def test_predicate_starting_with_single_digit(self):
        """Test that predicate that is just a digit raises an error."""
        with pytest.raises(ValueError):
            parse_fact("1(node)")

    def test_colon_in_component(self):
        """Test that colon in component raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node:test)")

    def test_parentheses_in_component(self):
        """Test that parentheses in component raise an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(node(test))")

    def test_whitespace_only_component(self):
        """Test that whitespace-only component raises an error."""
        with pytest.raises(ValueError):
            parse_fact("pred(   )")

    def test_whitespace_only_predicate(self):
        """Test that whitespace-only predicate raises an error."""
        with pytest.raises(ValueError):
            parse_fact("   (node)")


# Tests in this class were generated with Claude Sonnet 4.5.
class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_interval_at_boundaries(self):
        """Test interval at valid boundaries [0,1]."""
        pred, component, bound, fact_type = parse_fact("pred(node):[0,1]")
        assert bound.lower == 0.0 and bound.upper == 1.0

    def test_very_long_predicate_name(self):
        """Test that very long predicate names are handled."""
        long_pred = "a" * 1000
        pred, component, bound, fact_type = parse_fact(f"{long_pred}(node)")
        assert pred == long_pred

    def test_very_long_component_name(self):
        """Test that very long component names are handled."""
        long_comp = "n" * 1000
        pred, component, bound, fact_type = parse_fact(f"pred({long_comp})")
        assert component == long_comp

    def test_high_precision_floats(self):
        """Test parsing intervals with high precision floats."""
        pred, component, bound, fact_type = parse_fact("pred(node):[0.123456789,0.987654321]")
        assert abs(bound.lower - 0.123456789) < 1e-9
        assert abs(bound.upper - 0.987654321) < 1e-9

    def test_scientific_notation_in_interval(self):
        """Test parsing intervals with scientific notation."""
        pred, component, bound, fact_type = parse_fact("pred(node):[1e-5,1e-3]")
        assert abs(bound.lower - 1e-5) < 1e-10
        assert abs(bound.upper - 1e-3) < 1e-10

    def test_case_sensitivity_in_boolean(self):
        """Test that boolean values are case-insensitive."""
        for bool_val in ["True", "TRUE", "true", "False", "FALSE", "false"]:
            pred, component, bound, fact_type = parse_fact(f"pred(node):{bool_val}")
            assert bound.lower in [0.0, 1.0] and bound.upper in [0.0, 1.0]

    def test_mixed_case_in_predicate(self):
        """Test that mixed case in predicate is preserved."""
        pred, component, bound, fact_type = parse_fact("MyPred(node)")
        assert pred == "MyPred"

    def test_mixed_case_in_component(self):
        """Test that mixed case in component is preserved."""
        pred, component, bound, fact_type = parse_fact("pred(MyNode)")
        assert component == "MyNode"
