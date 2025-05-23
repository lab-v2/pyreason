import time

import pyreason as pr
import torch
import torch.nn as nn
import networkx as nx
import numpy as np
import random
from datetime import timedelta

seed_value = 65     # Good Gap Gap
# seed_value = 47     # Good Gap Good
# seed_value = 43     # Good Good Good
random.seed(seed_value)
np.random.seed(seed_value)
torch.manual_seed(seed_value)


def input_fn():
    return torch.rand(1, 3)  # Dummy input function for the model


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
weld_quality_checker = pr.TemporalLogicIntegratedClassifier(
    weld_model,
    class_names,
    identifier="weld_object",
    interface_options=interface_options,
    poll_interval=timedelta(seconds=0.5),
    # poll_interval=1,
    poll_condition="gap",
    input_fn=input_fn,
)

pr.add_rule(pr.Rule("repairing(weld_object) <-1 gap(weld_object)", "repair attempted rule"))
pr.add_rule(pr.Rule("defective(weld_object) <-1 gap(weld_object), repairing(weld_object)", "defective rule"))

max_iters = 5
for weld_iter in range(max_iters):
    # Time step 1: Initial inspection shows the weld is good.
    features = torch.rand(1, 3)  # Values chosen to indicate a good weld.
    t = pr.get_time()
    logits, probs, classifier_facts = weld_quality_checker(features, t1=t, t2=t)
    # print(f"=== Weld Inspection for Part: {weld_iter} ===")
    # print("Logits:", logits)
    # print("Probabilities:", probs)
    for fact in classifier_facts:
        pr.add_fact(fact)

    # Reasoning
    pr.settings.atom_trace = True
    pr.settings.verbose = False
    again = False if weld_iter == 0 else True
    interpretation = pr.reason(timesteps=1, again=again, restart=False)
    trace = pr.get_rule_trace(interpretation)
    print(f"\n=== Reasoning Rule Trace for Weld Part: {weld_iter} ===")
    print(trace[0], "\n\n")

    time.sleep(5)

    # Check if part is defective
    # if pr.get_logic_program().interp.query(pr.Query("defective(weld_object)")):
    if interpretation.query(pr.Query("defective(weld_object)")):
        print("Defective weld detected! \n Replacing the part.\n\n")
        # break
