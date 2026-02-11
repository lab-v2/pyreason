import time
import sys
import os

import torch
import torch.nn as nn
import networkx as nx
import numpy as np
import random
from datetime import timedelta

from pyreason.scripts.learning.classification.temporal_classifier import TemporalLogicIntegratedClassifier
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.rules.rule import Rule
from pyreason.pyreason import _Settings as Settings, reason, reset_settings, get_rule_trace, add_fact, add_rule, load_graph, save_rule_trace, get_time, Query

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
interface_options = ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

# Wrap the model using LogicIntegratedClassifier.
weld_quality_checker = TemporalLogicIntegratedClassifier(
    weld_model,
    class_names,
    identifier="weld_object",
    interface_options=interface_options,
    poll_interval=timedelta(seconds=0.5),
    # poll_interval=1,
    poll_condition="gap",
    input_fn=input_fn,
)

add_rule(Rule("repairing(weld_object) <-1 gap(weld_object)", "repair attempted rule"))
add_rule(Rule("defective(weld_object) <-1 gap(weld_object), repairing(weld_object)", "defective rule"))

max_iters = 5
for weld_iter in range(max_iters):
    # Time step 1: Initial inspection shows the weld is good.
    features = torch.rand(1, 3)  # Values chosen to indicate a good weld.
    t = get_time()
    logits, probs, classifier_facts = weld_quality_checker(features, t1=t, t2=t)
    # print(f"=== Weld Inspection for Part: {weld_iter} ===")
    # print("Logits:", logits)
    # print("Probabilities:", probs)
    for fact in classifier_facts:
        add_fact(fact)

    settings = Settings
    # Reasoning
    settings.atom_trace = True
    settings.verbose = False
    again = False if weld_iter == 0 else True
    interpretation = reason(timesteps=1, again=again, restart=False)
    trace = get_rule_trace(interpretation)
    print(f"\n=== Reasoning Rule Trace for Weld Part: {weld_iter} ===")
    print(trace[0], "\n\n")

    time.sleep(5)

    # Check if part is defective
    # if get_logic_program().interp.query(Query("defective(weld_object)")):
    if interpretation.query(Query("defective(weld_object)")):
        print("Defective weld detected! \n Replacing the part.\n\n")
        break
