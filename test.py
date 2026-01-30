"""
Test file to demonstrate rule parsing with various optional parameters.
Use this to step through rule parsing with a debugger.
"""

import numpy as np
import pyreason as pr
from pyreason.scripts.rules.rule import Rule
from pyreason.scripts.threshold.threshold import Threshold

# Reset pyreason state
pr.reset()
pr.reset_settings()

print("=" * 80)
print("RULE PARSING EXAMPLES WITH ALL OPTIONAL PARAMETERS")
print("=" * 80)

# ==============================================================================
# Example 1: Basic rule (no optional parameters)
# ==============================================================================
print("\n1. Basic Node Rule (no optional params)")
rule1 = Rule(
    rule_text="friend(X) <- person(X), nice(X)",
    name="basic_rule"
)
print(f"   Created: {rule1.rule.get_rule_name()}")

# ==============================================================================
# Example 2: Rule with infer_edges=True
# ==============================================================================
print("\n2. Edge Rule with infer_edges=True")
rule2 = Rule(
    rule_text="connected(X, Y) <- knows(X, Y), likes(X, Y)",
    name="infer_edges_rule",
    infer_edges=True  # Will create edges between X and Y if rule fires
)
print(f"   Created: {rule2.rule.get_rule_name()}")
print(f"   Infers edges: {rule2.rule.get_edges()}")

# ==============================================================================
# Example 3: Rule with set_static=True
# ==============================================================================
print("\n3. Rule with set_static=True")
rule3 = Rule(
    rule_text="verified(X) <- authenticated(X), admin(X)",
    name="static_rule",
    set_static=True  # Once verified, the bound won't change
)
print(f"   Created: {rule3.rule.get_rule_name()}")
print(f"   Static: {rule3.rule.is_static()}")

# ==============================================================================
# Example 4: Rule with custom_thresholds as a LIST
# ==============================================================================
print("\n4. Rule with custom_thresholds (as list)")
# Each threshold corresponds to each clause in order
# Threshold(quantifier, (quantifier_type, aggregation), threshold_value)
custom_thresh_list = [
    Threshold("greater_equal", ("number", "total"), 1.0),    # For person(X)
    Threshold("greater_equal", ("percent", "total"), 80.0),  # For nice(X) - 80% of total
    Threshold("greater", ("number", "available"), 2.0)       # For helpful(X) - more than 2
]

rule4 = Rule(
    rule_text="excellent(X) <- person(X), nice(X), helpful(X)",
    name="threshold_list_rule",
    custom_thresholds=custom_thresh_list
)
print(f"   Created: {rule4.rule.get_rule_name()}")
print(f"   Number of clauses: {len(rule4.rule.get_clauses())}")
print(f"   Thresholds: {[t for t in rule4.rule.get_thresholds()]}")

# ==============================================================================
# Example 5: Rule with custom_thresholds as a DICT
# ==============================================================================
print("\n5. Rule with custom_thresholds (as dict)")
# Dict maps clause index to threshold (0-indexed)
# Unmapped clauses use default threshold
custom_thresh_dict = {
    0: Threshold("greater_equal", ("number", "total"), 1.0),   # For employee(X)
    2: Threshold("greater_equal", ("percent", "total"), 75.0)  # For experienced(X)
    # Clause 1 (skilled(X)) will use default threshold
}

rule5 = Rule(
    rule_text="senior(X) <- employee(X), skilled(X), experienced(X)",
    name="threshold_dict_rule",
    custom_thresholds=custom_thresh_dict
)
print(f"   Created: {rule5.rule.get_rule_name()}")
print(f"   Thresholds: {[t for t in rule5.rule.get_thresholds()]}")

# ==============================================================================
# Example 6: Rule with custom weights
# ==============================================================================
print("\n6. Rule with custom weights")
# Weights are used in annotation functions for weighted combinations
weights = np.array([0.5, 0.3, 0.2], dtype=np.float64)  # Must match number of clauses

rule6 = Rule(
    rule_text="trustworthy(X) <- verified(X), active(X), rated(X)",
    name="weighted_rule",
    weights=weights
)
print(f"   Created: {rule6.rule.get_rule_name()}")
print(f"   Weights: {rule6.rule.get_weights()}")

# ==============================================================================
# Example 7: Rule with annotation function in head
# ==============================================================================
print("\n7. Rule with annotation function")
rule7 = Rule(
    rule_text="score(X) : ann_fn <- metric1(X), metric2(X), metric3(X)",
    name="annotation_function_rule"
)
print(f"   Created: {rule7.rule.get_rule_name()}")
print(f"   Annotation function: '{rule7.rule.get_annotation_function()}'")

# ==============================================================================
# Example 8: Rule with explicit bounds in head and body
# ==============================================================================
print("\n8. Rule with explicit bounds")
rule8 = Rule(
    rule_text="reliable(X) : [0.8, 1.0] <- tested(X) : [0.9, 1.0], certified(X) : [1.0, 1.0]",
    name="bounded_rule"
)
print(f"   Created: {rule8.rule.get_rule_name()}")
#print(f"   Head bound: {rule8.rule.get_target_bound()}")
print(f"   Clauses: {[(c[1].get_value(), c[3]) for c in rule8.rule.get_clauses()]}")

# ==============================================================================
# Example 9: Rule with delta_t (temporal rule)
# ==============================================================================
print("\n9. Temporal rule with delta_t")
rule9 = Rule(
    rule_text="will_happen(X) <- 3 happened(X), triggered(X)",
    name="temporal_rule"
    # The '3' after '<-' means the rule fires 3 timesteps after conditions are met
)
print(f"   Created: {rule9.rule.get_rule_name()}")
#print(f"   Delta t: {rule9.rule.get_delta_t()}")

# ==============================================================================
# Example 10: Rule with negation in body
# ==============================================================================
print("\n10. Rule with negation")
rule10 = Rule(
    rule_text="available(X) <- active(X), ~busy(X)",
    name="negation_rule"
)
print(f"   Created: {rule10.rule.get_rule_name()}")
print(f"   Clauses: {[(c[1].get_value(), c[3]) for c in rule10.rule.get_clauses()]}")

# ==============================================================================
# Example 11: Rule with comparison operators
# ==============================================================================
print("\n11. Rule with comparison operators")
rule11 = Rule(
    rule_text="eligible(X) <- age(X) >= 18, score(X) > 0.5",
    name="comparison_rule"
)
print(f"   Created: {rule11.rule.get_rule_name()}")
for i, clause in enumerate(rule11.rule.get_clauses()):
    print(f"   Clause {i}: type={clause[0]}, label={clause[1].get_value()}, operator='{clause[4]}'")

# ==============================================================================
# Example 12: Complex rule with MULTIPLE optional parameters
# ==============================================================================
print("\n12. Complex rule combining multiple optional parameters")
complex_thresholds = {
    0: Threshold("greater_equal", ("number", "total"), 1.0),
    1: Threshold("greater_equal", ("percent", "total"), 60.0)
}
complex_weights = np.array([0.6, 0.4], dtype=np.float64)

rule12 = Rule(
    rule_text="promoted(X, Y) : [0.9, 1.0] <- 2 manager(X), reports_to(Y, X) : [0.8, 1.0]",
    name="complex_rule",
    infer_edges=True,
    set_static=True,
    custom_thresholds=complex_thresholds,
    weights=complex_weights
)
print(f"   Created: {rule12.rule.get_rule_name()}")
#print(f"   Delta t: {rule12.rule.get_delta_t()}")
#print(f"   Static: {rule12.rule.is_static_rule()}")
print(f"   Infers edges: {rule12.rule.get_edges()}")
print(f"   Thresholds: {[t for t in rule12.rule.get_thresholds()]}")
print(f"   Weights: {rule12.rule.get_weights()}")
#print(f"   Head bound: {rule12.rule.get_target_bound()}")

# ==============================================================================
# Example 13: Rule with forall quantifier (special threshold)
# ==============================================================================
print("\n13. Rule with forall quantifier")
rule13 = Rule(
    rule_text="all_approved(X) <- forall(department(Y)), approved(X, Y)",
    name="forall_rule"
)
print(f"   Created: {rule13.rule.get_rule_name()}")
print(f"   Thresholds: {[t for t in rule13.rule.get_thresholds()]}")
print(f"   Note: forall is automatically converted to 100% threshold")

# ==============================================================================
# Add all rules to pyreason
# ==============================================================================
print("\n" + "=" * 80)
print("ADDING RULES TO PYREASON")
print("=" * 80)

all_rules = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8,
             rule9, rule10, rule11, rule12, rule13]

for rule in all_rules:
    pr.add_rule(rule)
    print(f"✓ Added: {rule.rule.get_rule_name()}")

print(f"\nTotal rules added: {len(pr.get_rules())}")

print("\n" + "=" * 80)
print("SETUP COMPLETE - Ready to debug!")
print("Set breakpoints in rule_parser.py:parse_rule() to step through parsing")
print("=" * 80)
