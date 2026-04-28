import time 
import sys
import os
from datetime import timedelta
import sys
sys.setrecursionlimit(10000)

import pyreason as pr
import torch
import torch.nn as nn
import networkx as nx
import numpy as np
import random
from pyreason.scripts.learning.classification.temporal_classifier import TemporalLogicIntegratedClassifier
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.rules.rule import Rule
from pyreason.pyreason import _Settings as Settings, reason, reset_settings, get_rule_trace, add_rule, add_fact, load_graph, save_rule_trace, get_time, Query


#seedValue = 47 # all cloudy
#seedValue = 42 # all sunny
#seedValue = 102 # mix of cloudy, sunny, might_storm
seedValue = 91 # working example

random.seed(seedValue)
np.random.seed(seedValue)
torch.manual_seed(seedValue)

def input_fn():
    # numbers come from how many features you want to use that affect the model
    # the end range number is the number of features/inputs going into the model
                                                   # ranges possible for features based on real world data
    cloud_cover = torch.rand(1, 1) * 100           # 0–100
    humidity = 20 + torch.rand(1, 1) * 80          # 20–100
    precip_rate = torch.rand(1, 1) * 15            # 0–15
    return torch.cat([cloud_cover, humidity, precip_rate], dim=1)

# first number is the number of features affecting the input
# second number is the number of classifiers we want to use for the output
model = nn.Linear(3, 3)
# classifiers for output (equal to second number)
conditions = ["sunny", "cloudy", "rainy"]

interface_options = ModelInterfaceOptions(
    threshold=0.5,  #
    set_lower_bound=True,   #
    set_upper_bound=False,  #
    snap_value=1.0  # if set_upper_bound is False, snap_value will be ignored
)

conditions_checker = TemporalLogicIntegratedClassifier(
    model,
    conditions,
    identifier = "sky",
    interface_options=interface_options,
    poll_interval=timedelta(seconds=1),  # how often the model should be polled for new data
    poll_condition = "cloudy",           # condition to check for when polling the model
    input_fn=input_fn
)

add_rule(Rule("storm_warning(sky) <-1 rainy(sky)", "warning rule"))
add_rule(Rule("cancel_voyage(sky) <-1 rainy(sky), storm_warning(sky)", "cancel rule"))

max_iterations = 5
for condition_iter in range(max_iterations):
    print(f"Iteration {condition_iter + 1}/{max_iterations}")
    features = input_fn()
    # t is to track timesteps 
    t = get_time()
    logits, probs, classifier_facts = conditions_checker(features, t1=t, t2=t)

    for fact in classifier_facts:
        add_fact(fact)

    settings = Settings
    settings.atom_trace = True
    settings.verbose = False
    # if-else chain to be able to know the state of the model when taking timesteps. starts at false, then is always true
    again = False if condition_iter == 0 else True
    interpretation = reason(timesteps=1, again=again, restart=False)
    trace = get_rule_trace(interpretation)
    print(f"\n=== Reasoning Rule Trace for Iteration: {condition_iter} ===")
    print(trace[0], "\n\n")

    time.sleep(2)

    if interpretation.query(Query("cancel_voyage(sky)")):
        print("Cancel voyage! Unsafe sky conditions detected.\n")
        break