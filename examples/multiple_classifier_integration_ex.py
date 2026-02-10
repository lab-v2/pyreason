import pyreason as pr
import torch
import torch.nn as nn
import networkx as nx
import numpy as np
import random


# seed_value = 41  # legitimate, high risk
# seed_value = 42  # fraud, low risk
seed_value = 44  # fraud, high risk
random.seed(seed_value)
np.random.seed(seed_value)
torch.manual_seed(seed_value)


# --- Part 1: Fraud Detector Model Integration ---
# Create a dummy PyTorch model for transaction fraud detection.
fraud_model = nn.Linear(5, 2)
fraud_class_names = ["fraud", "legitimate"]
transaction_features = torch.rand(1, 5)

# Define integration options: only probabilities > 0.5 will trigger bounds adjustment.
fraud_interface_options = pr.ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

# Wrap the fraud detection model.
fraud_detector = pr.LogicIntegratedClassifier(
    fraud_model,
    fraud_class_names,
    model_name="fraud_detector",
    interface_options=fraud_interface_options
)

# Run the fraud detector.
logits_fraud, probabilities_fraud, fraud_facts = fraud_detector(transaction_features)   # Talk about time
print("=== Fraud Detector Output ===")
print("Logits:", logits_fraud)
print("Probabilities:", probabilities_fraud)
print("\nGenerated Fraud Detector Facts:")
for fact in fraud_facts:
    print(fact)

# Context and reasoning
for fact in fraud_facts:
    pr.add_fact(fact)

# Add additional contextual facts:
# 1. The transaction is from a suspicious location.
pr.add_fact(pr.Fact("suspicious_location(AccountA)", "transaction_fact"))
# 2. Link the transaction to AccountA.
pr.add_fact(pr.Fact("transaction(AccountA)", "transaction_link"))
# 3. Register AccountA as an account.
pr.add_fact(pr.Fact("account(AccountA)", "account_fact"))

# Define reasoning rules:
# Rule A: If the fraud detector flags fraud and the transaction is suspicious, mark AccountA for investigation.
pr.add_rule(pr.Rule("requires_investigation(acc) <- transaction(acc), suspicious_location(acc), fraud_detector(fraud)", "investigation_rule"))

# --- Set up Graph and Load ---
# Build a simple graph of accounts.
G = nx.DiGraph()
G.add_node("AccountA")
G.add_node("AccountB")
G.add_node("AccountC")
# Add edges with an attribute "relationship" set to "associated".
G.add_edge("AccountA", "AccountB", associated=1)
G.add_edge("AccountB", "AccountC", associated=1)
# Load the graph into PyReason. The edge attribute "relationship" is interpreted as the predicate 'associated'.
pr.load_graph(G)

# Define propagation rules to spread investigation and critical action flags via the "associated" relationship.
pr.add_rule(pr.Rule("requires_investigation(y) <- requires_investigation(x), associated(x,y)", "investigation_propagation_rule"))

# --- Part 5: Run the Reasoning Engine ---
# Run the reasoning engine.
pr.settings.allow_ground_rules = True
pr.settings.atom_trace = True
interpretation = pr.reason()

# Display reasoning results for 'requires_investigation'.
print("\n=== Reasoning Results for 'requires_investigation' ===")
trace = pr.get_rule_trace(interpretation)
print(f"RULE TRACE: \n\n{trace[0]}\n")


# --- Part 2: Risk Evaluator Model Integration ---
# Create another dummy PyTorch model for evaluating account risk.
risk_model = nn.Linear(5, 2)
risk_class_names = ["high_risk", "low_risk"]
risk_features = torch.rand(1, 5)

# Define integration options for the risk evaluator.
risk_interface_options = pr.ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=True,
    snap_value=1.0
)

# Wrap the risk evaluation model.
risk_evaluator = pr.LogicIntegratedClassifier(
    risk_model,
    risk_class_names, # document len
    model_name="risk_evaluator", # binded constant
    interface_options=risk_interface_options
)

# Run the risk evaluator.
logits_risk, probabilities_risk, risk_facts = risk_evaluator(risk_features)
print("\n=== Risk Evaluator Output ===")
print("Logits:", logits_risk)
print("Probabilities:", probabilities_risk)
print("\nGenerated Risk Evaluator Facts:")
for fact in risk_facts:
    print(fact)

# --- Context and Reasoning again ---
for fact in risk_facts:
    pr.add_fact(fact)

# Rule B: If the fraud detector flags fraud and the risk evaluator flags high risk, mark AccountA for critical action.
pr.add_rule(pr.Rule("critical_action(acc) <- transaction(acc), suspicious_location(acc), fraud_detector(fraud), risk_evaluator(high_risk)", "critical_action_rule"))
pr.add_rule(pr.Rule("critical_action(y) <- critical_action(x), associated(x,y)", "critical_propagation_rule"))

interpretation = pr.reason(again=True)

# Display reasoning results for 'critical_action'.
print("\n=== Reasoning Results for 'critical_action' (Reasoning again) ===")
trace = pr.get_rule_trace(interpretation)
print(f"RULE TRACE: \n\n{trace[0]}\n")
