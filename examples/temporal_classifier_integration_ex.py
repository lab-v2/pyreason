import pyreason as pr
import torch
import torch.nn as nn
import numpy as np
import random

# Set a seed for reproducibility.
seed_value = 65     # Good Gap Gap
# seed_value = 47     # Good Gap Good
# seed_value = 43     # Good Good Good
random.seed(seed_value)
np.random.seed(seed_value)
torch.manual_seed(seed_value)

# --- Part 1: Weld Quality Model Integration ---

# Create a dummy PyTorch model for detecting weld quality.
# Each weld is represented by 3 features and is classified as "good" or "gap".
weld_model = nn.Linear(3, 2)
class_names = ["good", "gap"]

# Define integration options:
# Only consider probabilities above 0.5, adjust lower bound for high confidence, and use a snap value.
interface_options = pr.ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

# Wrap the model using LogicIntegratedClassifier.
weld_quality_checker = pr.LogicIntegratedClassifier(
    weld_model,
    class_names,
    identifier="weld_object",
    interface_options=interface_options
)

# --- Part 2: Simulate Weld Inspections Over Time ---
pr.add_rule(pr.Rule("repair_attempted(weld_object) <-1 gap(weld_object)", "repair attempted rule"))
pr.add_rule(pr.Rule("defective(weld_object) <-0 gap(weld_object), repair_attempted(weld_object)", "defective rule"))

# Time step 1: Initial inspection shows the weld is good.
features_t0 = torch.rand(1, 3)  # Values chosen to indicate a good weld.
logits_t0, probs_t0, classifier_facts_t0 = weld_quality_checker(features_t0, t1=0, t2=0)
print("=== Weld Inspection at Time 0 ===")
print("Logits:", logits_t0)
print("Probabilities:", probs_t0)
for fact in classifier_facts_t0:
    pr.add_fact(fact)

# Time step 2: Second inspection detects a gap.
features_t1 = torch.rand(1, 3)  # Values chosen to simulate a gap.
logits_t1, probs_t1, classifier_facts_t1 = weld_quality_checker(features_t1, t1=1, t2=1)
print("\n=== Weld Inspection at Time 1 ===")
print("Logits:", logits_t1)
print("Probabilities:", probs_t1)
for fact in classifier_facts_t1:
    pr.add_fact(fact)


# Time step 3: Third inspection, the gap still persists.
features_t2 = torch.rand(1, 3)  # Values chosen to simulate persistent gap.
logits_t2, probs_t2, classifier_facts_t2 = weld_quality_checker(features_t2, t1=2, t2=2)
print("\n=== Weld Inspection at Time 2 ===")
print("Logits:", logits_t2)
print("Probabilities:", probs_t2)
for fact in classifier_facts_t2:
    pr.add_fact(fact)


# --- Part 3: Run the Reasoning Engine ---

# Enable atom tracing for debugging the rule application process.
pr.settings.atom_trace = True
interpretation = pr.reason(timesteps=2)
trace = pr.get_rule_trace(interpretation)

print("\n=== Reasoning Rule Trace ===")
print(trace[0])