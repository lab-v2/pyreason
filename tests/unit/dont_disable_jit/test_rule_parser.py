import pytest
import numpy as np
from pyreason.scripts.utils.rule_parser import parse_rule
from pyreason.scripts.threshold.threshold import Threshold

#TODO: Add test with ~pred(comp):True win head or body or both
#TODO: Add tests for rules with ground atoms in head

# Tests in this class were partially generated with Claude Opus 4.5.
class TestValidRuleParsing:
    """Test cases for valid rule inputs that should parse successfully."""

    def test_basic_node_rule(self):
        """Basic node rule with two body clauses."""
        r = parse_rule("friend(X) <- person(X), nice(X)", "basic_rule", None)
        assert r.get_rule_name() == "basic_rule"
        assert r.get_rule_type() == "node"
        assert r.get_target().get_value() == "friend"
        assert len(r.get_clauses()) == 2
        assert r.get_delta() == 0

    def test_basic_node_rule_single_clause(self):
        """Node rule with a single body clause."""
        r = parse_rule("result(x) <- score(x)", "single", None)
        assert len(r.get_clauses()) == 1
        assert r.get_clauses()[0][1].get_value() == "score"

    def test_node_rule_name_none(self):
        """Rule with name=None."""
        r = parse_rule("a(X) <- b(X)", None, None)
        assert r.get_rule_name() is None

    def test_basic_edge_rule(self):
        """Basic edge rule with two head variables."""
        r = parse_rule("connected(X, Y) <- knows(X, Y)", "edge_rule", None)
        assert r.get_rule_type() == "edge"
        head_vars = list(r.get_head_variables())
        assert head_vars == ["X", "Y"]

    def test_edge_rule_infer_edges(self):
        """Edge rule with infer_edges=True produces non-empty edges tuple."""
        r = parse_rule("connected(X,Y) <- knows(X,Y)", "infer", None, infer_edges=True)
        edges = r.get_edges()
        assert edges[0] == "X"
        assert edges[1] == "Y"
        assert edges[2].get_value() == "connected"

    def test_edge_rule_multiple_body_vars(self):
        """Edge rule with body clauses sharing variables."""
        r = parse_rule("car_friend(x,y) <- owns_car(x,z), owns_car(y,z)", "cf", None)
        assert r.get_rule_type() == "edge"
        clauses = r.get_clauses()
        assert len(clauses) == 2
        assert list(clauses[0][2]) == ["x", "z"]
        assert list(clauses[1][2]) == ["y", "z"]

    def test_temporal_rule_delta_1(self):
        """Temporal rule with delta_t=1."""
        r = parse_rule("popular(x) <-1 popular(y), Friends(x,y)", "t1", None)
        assert r.get_delta() == 1

    def test_temporal_rule_delta_0(self):
        """Temporal rule with explicit delta_t=0."""
        r = parse_rule("defective(x) <-0 gap(x), repair(x)", "t0", None)
        assert r.get_delta() == 0

    def test_temporal_rule_delta_3(self):
        """Temporal rule with delta_t=3."""
        r = parse_rule("will_happen(X) <- 3 happened(X), triggered(X)", "t3", None)
        assert r.get_delta() == 3

    def test_annotation_function(self):
        """Rule with annotation function in head."""
        r = parse_rule("score(X):ann_fn <- metric1(X)", "ann", None)
        assert r.get_annotation_function() == "ann_fn"
        bnd = r.get_bnd()
        assert bnd.lower == 0.0
        assert bnd.upper == 1.0

    def test_annotation_function_edge(self):
        """Edge rule with annotation function and infer_edges."""
        r = parse_rule("avg(A,B):avg_fn <- P(A):[0,1], P(B):[0,1]", "avg", None, infer_edges=True)
        assert r.get_annotation_function() == "avg_fn"
        edges = r.get_edges()
        assert edges[2].get_value() == "avg"

    def test_explicit_head_bound(self):
        """Rule with explicit bound on head."""
        r = parse_rule("reliable(X):[0.8,1.0] <- tested(X):[0.9,1.0]", "hb", None)
        bnd = r.get_bnd()
        assert abs(bnd.lower - 0.8) < 1e-9
        assert abs(bnd.upper - 1.0) < 1e-9

    def test_explicit_body_bounds(self):
        """Rule with explicit bounds on body clauses."""
        r = parse_rule("reliable(X):[0.8,1.0] <- tested(X):[0.9,1.0], certified(X):[1.0,1.0]", "bb", None)
        clauses = r.get_clauses()
        assert abs(clauses[0][3].lower - 0.9) < 1e-9
        assert abs(clauses[0][3].upper - 1.0) < 1e-9
        assert abs(clauses[1][3].lower - 1.0) < 1e-9
        assert abs(clauses[1][3].upper - 1.0) < 1e-9

    def test_negation_in_body(self):
        """Negated body clause gets bound [0,0]."""
        r = parse_rule("available(X) <- active(X), ~busy(X)", "neg_body", None)
        clauses = r.get_clauses()
        # First clause: default [1,1]
        assert clauses[0][3].lower == 1.0 and clauses[0][3].upper == 1.0
        # Second clause (negated): [0,0]
        assert clauses[1][3].lower == 0.0 and clauses[1][3].upper == 0.0

    def test_negation_in_head(self):
        """Negated head gets bound [0,0]."""
        r = parse_rule("~pred(X) <- cond(X)", "neg_head", None)
        bnd = r.get_bnd()
        assert bnd.lower == 0.0 and bnd.upper == 0.0

    def test_negation_in_body_edge(self):
        """Negated edge body clause."""
        r = parse_rule("enemy(A,B) <- ~friend(A,B)", "neg_edge", None)
        clauses = r.get_clauses()
        assert clauses[0][3].lower == 0.0 and clauses[0][3].upper == 0.0
        assert r.get_rule_type() == "edge"

    def test_comparison_ge(self):
        """Comparison operator >=."""
        r = parse_rule("eligible(X) <- age(X) >= 18", "cmp_ge", None)
        clause = r.get_clauses()[0]
        assert clause[0] == "comparison"
        assert clause[4] == ">="

    def test_comparison_gt(self):
        """Comparison operator >."""
        r = parse_rule("eligible(X) <- score(X) > 0.5", "cmp_gt", None)
        assert r.get_clauses()[0][4] == ">"

    def test_comparison_eq(self):
        """Comparison operator ==."""
        r = parse_rule("same_class(x,y) <- c_id(x) == c_id(y)", "cmp_eq", None)
        assert r.get_clauses()[0][4] == "=="

    def test_comparison_ne(self):
        """Comparison operator !=."""
        r = parse_rule("diff_class(x,y) <- c_id(x) != c_id(y)", "cmp_ne", None)
        assert r.get_clauses()[0][4] == "!="

    def test_comparison_le(self):
        """Comparison operator <=."""
        r = parse_rule("low(X) <- score(X) <= 10", "cmp_le", None)
        assert r.get_clauses()[0][4] == "<="

    def test_comparison_lt(self):
        """Comparison operator <."""
        r = parse_rule("low(X) <- score(X) < 5", "cmp_lt", None)
        assert r.get_clauses()[0][4] == "<"

    def test_forall_quantifier(self):
        """Forall quantifier creates 100% percent threshold."""
        r = parse_rule("all_approved(X) <- forall(dept(Y)), approved(X, Y)", "forall", None)
        thresholds = list(r.get_thresholds())
        # First threshold (forall) should be 100% percent
        assert thresholds[0][0] == "greater_equal"
        assert thresholds[0][1] == ("percent", "total")
        assert thresholds[0][2] == 100.0

    def test_head_function_node(self):
        """Head with a function call on a node variable."""
        r = parse_rule("Processed(identity_func(X)) <- property(X)", "hf_node", None)
        head_fns = list(r.get_head_function())
        head_vars = list(r.get_head_variables())
        assert head_fns == ["identity_func"]
        assert head_vars == ["__temp_var_0"]

    def test_head_function_edge_first(self):
        """Head function on first arg of an edge rule."""
        r = parse_rule("Route(identity_func(A), B) <- path(A, B)", "hf_edge1", None)
        head_fns = list(r.get_head_function())
        head_vars = list(r.get_head_variables())
        assert head_fns == ["identity_func", ""]
        assert head_vars == ["__temp_var_0", "B"]

    def test_head_function_both(self):
        """Head functions on both edge args."""
        r = parse_rule("Link(f(A), g(B)) <- path(A, B)", "hf_both", None)
        head_fns = list(r.get_head_function())
        assert head_fns == ["f", "g"]
        head_vars = list(r.get_head_variables())
        assert head_vars == ["__temp_var_0", "__temp_var_1"]

    def test_custom_thresholds_list(self):
        """Custom thresholds provided as a list."""
        thresholds = [
            Threshold("greater_equal", ("number", "total"), 1.0),
            Threshold("greater_equal", ("percent", "total"), 80.0),
            Threshold("greater", ("number", "available"), 2.0),
        ]
        r = parse_rule("excellent(X) <- person(X), nice(X), helpful(X)", "thr_list", thresholds)
        result = list(r.get_thresholds())
        assert len(result) == 3
        assert result[0] == ("greater_equal", ("number", "total"), 1.0)
        assert result[1] == ("greater_equal", ("percent", "total"), 80.0)
        assert result[2] == ("greater", ("number", "available"), 2.0)

    def test_custom_thresholds_dict(self):
        """Custom thresholds provided as a dict (unmapped clauses get defaults)."""
        thresholds = {
            0: Threshold("greater_equal", ("number", "total"), 1.0),
            2: Threshold("greater_equal", ("percent", "total"), 75.0),
        }
        r = parse_rule("senior(X) <- employee(X), skilled(X), experienced(X)", "thr_dict", thresholds)
        result = list(r.get_thresholds())
        assert result[0] == ("greater_equal", ("number", "total"), 1.0)
        # Clause 1 uses default
        assert result[1] == ("greater_equal", ("number", "total"), 1.0)
        assert result[2] == ("greater_equal", ("percent", "total"), 75.0)

    def test_custom_weights(self):
        """Custom weights array is preserved."""
        weights = np.array([0.5, 0.3, 0.2], dtype=np.float64)
        r = parse_rule("trustworthy(X) <- verified(X), active(X), rated(X)", "w", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [0.5, 0.3, 0.2])

    def test_default_weights(self):
        """Default weights are all 1.0."""
        r = parse_rule("friend(X) <- person(X), nice(X)", "dw", None)
        np.testing.assert_array_equal(r.get_weights(), [1.0, 1.0])

    def test_set_static_true(self):
        """set_static=True is preserved."""
        r = parse_rule("verified(X) <- authenticated(X)", "st", None, set_static=True)
        assert r.is_static() is True

    def test_set_static_false(self):
        """Default set_static is False."""
        r = parse_rule("verified(X) <- authenticated(X)", "sf", None)
        assert r.is_static() is False

    def test_spaces_stripped(self):
        """Spaces around commas and arrow are stripped."""
        r1 = parse_rule("friend(X) <- person(X) , nice(X)", "sp", None)
        r2 = parse_rule("friend(X) <- person(X),nice(X)", "sp", None)
        assert r1.get_target().get_value() == r2.get_target().get_value()
        assert len(r1.get_clauses()) == len(r2.get_clauses())
        assert list(r1.get_head_variables()) == list(r2.get_head_variables())

    def test_complex_all_params(self):
        """Complex rule combining delta_t, head bound, edge, infer_edges, thresholds, weights, static."""
        thresholds = {
            0: Threshold("greater_equal", ("number", "total"), 1.0),
            1: Threshold("greater_equal", ("percent", "total"), 60.0),
        }
        weights = np.array([0.6, 0.4], dtype=np.float64)
        r = parse_rule(
            "promoted(X, Y) : [0.9, 1.0] <- 2 manager(X), reports_to(Y, X) : [0.8, 1.0]",
            "complex",
            thresholds,
            infer_edges=True,
            set_static=True,
            weights=weights,
        )
        assert r.get_rule_type() == "edge"
        assert r.get_delta() == 2
        assert abs(r.get_bnd().lower - 0.9) < 1e-9
        assert abs(r.get_bnd().upper - 1.0) < 1e-9
        assert r.is_static() is True
        edges = r.get_edges()
        assert edges[0] == "X"
        assert edges[1] == "Y"
        np.testing.assert_array_almost_equal(r.get_weights(), [0.6, 0.4])


# Tests in this class were partially generated with Claude Opus 4.5.
class TestInvalidRuleParsing:
    """Test cases for invalid rule inputs that should raise validation errors."""

    def test_none_rule_text(self):
        """None rule_text raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            parse_rule(None, "r", None)

    def test_integer_rule_text(self):
        """Integer rule_text raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            parse_rule(123, "r", None)

    def test_empty_rule_text(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_rule("", "r", None)

    def test_whitespace_only(self):
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_rule("   ", "r", None)

    def test_missing_arrow(self):
        """Rule without '<-' raises ValueError."""
        with pytest.raises(ValueError, match="'<-'"):
            parse_rule("friend(X) person(X)", "r", None)

    def test_double_arrow(self):
        """Rule with two '<-' raises ValueError."""
        with pytest.raises(ValueError, match="exactly one"):
            parse_rule("a(X) <- b(X) <- c(X)", "r", None)

    def test_wrong_arrow(self):
        """Rule with '->' instead of '<-' raises ValueError."""
        with pytest.raises(ValueError, match="'<-'"):
            parse_rule("friend(X) -> person(X)", "r", None)

    def test_empty_head(self):
        """Empty head raises ValueError."""
        with pytest.raises(ValueError, match="head"):
            parse_rule("<- person(X)", "r", None)

    def test_empty_body(self):
        """Empty body raises ValueError."""
        with pytest.raises(ValueError, match="body"):
            parse_rule("friend(X) <-", "r", None)

    def test_empty_body_spaces(self):
        """Body with only spaces raises ValueError."""
        with pytest.raises(ValueError, match="body"):
            parse_rule("friend(X) <-   ", "r", None)

    def test_head_missing_parens(self):
        """Head without parentheses raises ValueError."""
        with pytest.raises(ValueError, match="parentheses"):
            parse_rule("friend <- person(X)", "r", None)

    def test_head_multiple_colons(self):
        """Head with multiple colons raises ValueError."""
        with pytest.raises(ValueError, match="colons"):
            parse_rule("p(X):[0.8,1.0]:extra <- b(X)", "r", None)

    def test_body_trailing_comma(self):
        """Trailing comma in body raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_rule("pred(X) <- body(X),", "r", None)

    def test_body_clause_no_parens(self):
        """Body clause without parentheses raises ValueError."""
        with pytest.raises(ValueError, match="parentheses"):
            parse_rule("pred(X) <- bodyX", "r", None)

    def test_body_double_comma(self):
        """Double comma in body raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_rule("pred(X) <- a(X),, b(X)", "r", None)

    def test_head_bound_non_numeric(self):
        """Non-numeric head bound raises ValueError."""
        with pytest.raises(ValueError, match="numeric"):
            parse_rule("p(X):[abc,def] <- b(X)", "r", None)

    def test_head_bound_lower_gt_upper(self):
        """Head bound with lower > upper raises ValueError."""
        with pytest.raises(ValueError, match="greater than"):
            parse_rule("p(X):[0.9,0.1] <- b(X)", "r", None)

    def test_head_bound_negative(self):
        """Negative head bound raises ValueError."""
        with pytest.raises(ValueError, match="range"):
            parse_rule("p(X):[-0.5,1.0] <- b(X)", "r", None)

    def test_head_bound_above_one(self):
        """Head bound above 1 raises ValueError."""
        with pytest.raises(ValueError, match="range"):
            parse_rule("p(X):[0.5,1.5] <- b(X)", "r", None)

    def test_body_bound_lower_gt_upper(self):
        """Body bound with lower > upper raises ValueError."""
        with pytest.raises(ValueError, match="greater than"):
            parse_rule("p(X) <- b(X):[0.9,0.1]", "r", None)

    def test_body_bound_out_of_range(self):
        """Body bound with negative value raises ValueError."""
        with pytest.raises(ValueError, match="range"):
            parse_rule("p(X) <- b(X):[-0.5,1.0]", "r", None)

    def test_bound_single_value(self):
        """Bound with single value raises ValueError."""
        with pytest.raises(ValueError, match="2 values"):
            parse_rule("p(X):[0.5] <- b(X)", "r", None)

    def test_bound_three_values(self):
        """Bound with three values raises ValueError."""
        with pytest.raises(ValueError, match="2 values"):
            parse_rule("p(X):[0.1,0.5,0.9] <- b(X)", "r", None)

    def test_threshold_list_wrong_len(self):
        """Threshold list with wrong length raises ValueError."""
        thresholds = [
            Threshold("greater_equal", ("number", "total"), 1.0),
            Threshold("greater_equal", ("number", "total"), 1.0),
            Threshold("greater_equal", ("number", "total"), 1.0),
        ]
        with pytest.raises(ValueError):
            parse_rule("p(X) <- a(X), b(X)", "r", thresholds)

    def test_threshold_dict_oob(self):
        """Threshold dict with out-of-bounds key raises ValueError."""
        thresholds = {5: Threshold("greater_equal", ("number", "total"), 1.0)}
        with pytest.raises(ValueError):
            parse_rule("p(X) <- a(X), b(X), c(X)", "r", thresholds)

    def test_threshold_empty_dict(self):
        """Empty threshold dict raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_rule("p(X) <- a(X), b(X)", "r", {})

    def test_weights_wrong_length(self):
        """Weights array with wrong length raises ValueError."""
        weights = np.array([0.5, 0.3, 0.2], dtype=np.float64)
        with pytest.raises(ValueError, match="Number of weights"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)

    def test_weights_not_array(self):
        """Non-array weights that can't be converted raises TypeError."""
        with pytest.raises(TypeError, match="numpy array"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights="invalid")

    def test_weights_list_converted(self):
        """List of weights is automatically converted to numpy array."""
        weights = [0.5, 0.5]
        r = parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [0.5, 0.5])

    def test_weights_non_numeric(self):
        """Non-numeric weights raise TypeError."""
        weights = np.array(['a', 'b'], dtype=object)
        with pytest.raises(TypeError, match="numeric values"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)

    def test_weights_nan(self):
        """Weights containing NaN raise ValueError."""
        weights = np.array([0.5, np.nan], dtype=np.float64)
        with pytest.raises(ValueError, match="finite"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)

    def test_weights_inf(self):
        """Weights containing Inf raise ValueError."""
        weights = np.array([0.5, np.inf], dtype=np.float64)
        with pytest.raises(ValueError, match="finite"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)

    def test_weights_negative(self):
        """Negative weights raise ValueError."""
        weights = np.array([0.5, -0.3], dtype=np.float64)
        with pytest.raises(ValueError, match="non-negative"):
            parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)

    def test_weights_zero_allowed(self):
        """Zero weights are allowed."""
        weights = np.array([0.0, 1.0], dtype=np.float64)
        r = parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [0.0, 1.0])

    def test_weights_integer_converted(self):
        """Integer weights are converted to float64."""
        weights = np.array([1, 2, 3], dtype=np.int32)
        r = parse_rule("p(X) <- a(X), b(X), c(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [1.0, 2.0, 3.0])
        assert r.get_weights().dtype == np.float64

    def test_weights_single_clause(self):
        """Single weight for single clause."""
        weights = np.array([0.7], dtype=np.float64)
        r = parse_rule("p(X) <- a(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [0.7])

    def test_weights_greater_than_one(self):
        """Weights greater than 1.0 are allowed."""
        weights = np.array([2.5, 3.0], dtype=np.float64)
        r = parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [2.5, 3.0])

    def test_weights_not_summing_to_one(self):
        """Weights that don't sum to 1.0 are allowed."""
        weights = np.array([0.3, 0.4], dtype=np.float64)
        r = parse_rule("p(X) <- a(X), b(X)", "r", None, weights=weights)
        np.testing.assert_array_almost_equal(r.get_weights(), [0.3, 0.4])

    def test_malformed_forall(self):
        """Malformed forall expression (missing closing paren) raises ValueError."""
        with pytest.raises(ValueError, match="forall"):
            parse_rule("p(X) <- forall(dept", "r", None)


# Tests in this class were partially generated with Claude Opus 4.5.
class TestEdgeCasesAndBoundary:
    """Test edge cases and boundary conditions."""

    def test_bound_at_boundaries(self):
        """Bound [0.0, 1.0] is valid."""
        r = parse_rule("p(X):[0.0,1.0] <- b(X)", "r", None)
        assert abs(r.get_bnd().lower - 0.0) < 1e-9
        assert abs(r.get_bnd().upper - 1.0) < 1e-9

    def test_bound_zero_zero(self):
        """Bound [0, 0] is valid."""
        r = parse_rule("p(X):[0,0] <- b(X)", "r", None)
        assert r.get_bnd().lower == 0.0
        assert r.get_bnd().upper == 0.0

    def test_large_delta_t(self):
        """Large delta_t value parses correctly."""
        r = parse_rule("p(X) <- 999 b(X)", "r", None)
        assert r.get_delta() == 999

    def test_many_body_clauses(self):
        """Rule with 5+ body clauses parses correctly."""
        r = parse_rule("p(X) <- a(X), b(X), c(X), d(X), e(X)", "r", None)
        assert len(r.get_clauses()) == 5

    def test_underscore_and_numbers(self):
        """Predicates with underscores and numbers are preserved."""
        r = parse_rule("my_pred_2(X) <- another_3(X)", "r", None)
        assert r.get_target().get_value() == "my_pred_2"
        assert r.get_clauses()[0][1].get_value() == "another_3"

    def test_mixed_case_preserved(self):
        """Mixed case in predicates is preserved."""
        r = parse_rule("MyPred(X) <- BodyPred(X)", "r", None)
        assert r.get_target().get_value() == "MyPred"
        assert r.get_clauses()[0][1].get_value() == "BodyPred"

    def test_all_comparison_operators(self):
        """All 6 comparison operators are detected."""
        ops = {">=": "age(X)>=18", ">": "age(X)>18", "<=": "age(X)<=18",
               "<": "age(X)<18", "==": "c_id(X)==c_id(Y)", "!=": "c_id(X)!=c_id(Y)"}
        for expected_op, body_str in ops.items():
            r = parse_rule(f"p(X) <- {body_str}", "r", None)
            assert r.get_clauses()[0][4] == expected_op, f"Failed for operator {expected_op}"

    def test_single_char_predicates(self):
        """Single character predicates work."""
        r = parse_rule("a(X) <- b(X)", "r", None)
        assert r.get_target().get_value() == "a"
        assert r.get_clauses()[0][1].get_value() == "b"

    def test_infer_edges_silently_disabled_for_node(self):
        """Node rule with infer_edges=True silently disables it."""
        r = parse_rule("friend(X) <- person(X)", "r", None, infer_edges=True)
        edges = r.get_edges()
        # Should be the default empty edges, not an error
        assert edges[0] == ""
        assert edges[1] == ""

    def test_negation_with_explicit_bound(self):
        """Negation with explicit bound computes ~[l,u] = [1-u, 1-l]."""
        r = parse_rule("p(X) <- ~body(X):[0.5,0.8]", "r", None)
        clause = r.get_clauses()[0]
        assert abs(clause[3].lower - 0.2) < 1e-9
        assert abs(clause[3].upper - 0.5) < 1e-9

    def test_negation_with_explicit_bound_head(self):
        """Negated head with explicit bound computes ~[l,u] = [1-u, 1-l]."""
        r = parse_rule("~p(X):[0.5,0.8] <- cond(X)", "r", None)
        bnd = r.get_bnd()
        assert abs(bnd.lower - 0.2) < 1e-9
        assert abs(bnd.upper - 0.5) < 1e-9

    def test_negation_body_no_bound(self):
        """Negated body without explicit bound still gives [0,0]."""
        r = parse_rule("p(X) <- ~body(X)", "r", None)
        clause = r.get_clauses()[0]
        assert clause[3].lower == 0.0
        assert clause[3].upper == 0.0

    def test_negation_with_one_one_bound(self):
        """~body(X):[1,1] -> [1-1, 1-1] = [0,0]."""
        r = parse_rule("p(X) <- ~body(X):[1,1]", "r", None)
        clause = r.get_clauses()[0]
        assert clause[3].lower == 0.0
        assert clause[3].upper == 0.0

    def test_negation_with_zero_zero_bound(self):
        """~body(X):[0,0] -> [1-0, 1-0] = [1,1]."""
        r = parse_rule("p(X) <- ~body(X):[0,0]", "r", None)
        clause = r.get_clauses()[0]
        assert clause[3].lower == 1.0
        assert clause[3].upper == 1.0

    def test_bound_nan_head(self):
        """NaN in head bound raises ValueError."""
        with pytest.raises(ValueError, match="number"):
            parse_rule("p(X):[nan,1.0] <- b(X)", "r", None)

    def test_bound_nan_body(self):
        """NaN in body bound raises ValueError."""
        with pytest.raises(ValueError, match="number"):
            parse_rule("p(X) <- b(X):[0.5,nan]", "r", None)

    def test_bound_inf_head(self):
        """Inf in head bound raises ValueError."""
        with pytest.raises(ValueError, match="range"):
            parse_rule("p(X):[inf,1.0] <- b(X)", "r", None)

    def test_bound_negative_inf_body(self):
        """Negative inf in body bound raises ValueError."""
        with pytest.raises(ValueError, match="range"):
            parse_rule("p(X) <- b(X):[-inf,1.0]", "r", None)

    def test_head_predicate_starts_with_digit(self):
        """Head predicate starting with digit raises ValueError."""
        with pytest.raises(ValueError, match="digit"):
            parse_rule("1pred(X) <- b(X)", "r", None)

    def test_head_predicate_invalid_chars(self):
        """Head predicate with invalid chars raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            parse_rule("pred-name(X) <- b(X)", "r", None)

    def test_body_predicate_starts_with_digit(self):
        """Body predicate starting with digit raises ValueError."""
        with pytest.raises(ValueError, match="digit"):
            parse_rule("p(X) <- a(X), 2body(X)", "r", None)

    def test_body_predicate_invalid_chars(self):
        """Body predicate with invalid chars raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            parse_rule("p(X) <- body-name(X)", "r", None)

    def test_double_negation_head(self):
        """Double negation in head raises ValueError."""
        with pytest.raises(ValueError, match="Double negation"):
            parse_rule("~~p(X) <- b(X)", "r", None)

    def test_double_negation_body(self):
        """Double negation in body raises ValueError."""
        with pytest.raises(ValueError, match="Double negation"):
            parse_rule("p(X) <- ~~b(X)", "r", None)

    def test_head_variable_starts_with_digit(self):
        """Head variable starting with digit raises ValueError."""
        with pytest.raises(ValueError, match="digit"):
            parse_rule("p(1X) <- b(Y)", "r", None)

    def test_body_variable_invalid_chars(self):
        """Body variable with invalid chars raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            parse_rule("p(X) <- b(X-Y)", "r", None)

    def test_empty_head_parentheses(self):
        """Empty head parentheses raises ValueError."""
        with pytest.raises(ValueError, match="at least one variable"):
            parse_rule("p() <- b(X)", "r", None)

    def test_head_missing_closing_paren(self):
        """Head missing closing paren raises ValueError."""
        with pytest.raises(ValueError, match="closing parenthesis"):
            parse_rule("p(X <- b(X)", "r", None)

    def test_threshold_dict_negative_key(self):
        """Negative threshold dict key raises ValueError."""
        thresholds = {-1: Threshold("greater_equal", ("number", "total"), 1.0)}
        with pytest.raises(ValueError, match="non-negative"):
            parse_rule("p(X) <- a(X), b(X)", "r", thresholds)

    def test_forall_no_inner_predicate(self):
        """forall without inner predicate parens raises ValueError."""
        with pytest.raises(ValueError, match="inner predicate"):
            parse_rule("p(X) <- forall(dept)", "r", None)
