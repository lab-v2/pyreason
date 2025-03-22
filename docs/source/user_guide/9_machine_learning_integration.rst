Integrating PyReason with Machine Learning
===========================

PyReason can be integrated with machine learning models by incorporating the predictions from the machine learning model
as facts in the graph and reasoning over them with logical rules. This allows users to combine the strengths of machine learning
models with the interpretability and reasoning capabilities of PyReason.

Classifier Integration Example
-----------------------------
.. note::
   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/classifier_integration_ex.py>`_

In this section, we will outline how to perform ML integration using a simple classification example. We assume
that we have a fraud detection model that predicts whether a transaction is fraudulent or not. We will use the predictions
to reason over a knowledge base of account information to identify potential fraudulent activities. For this example, we
use an untrained linear model just to demonstrate, but in practice, this can be replaced by any PyTorch classification model.

We start by defining our classifier model.

.. code-block:: python

    import torch
    import torch.nn as nn


    model = nn.Linear(5, 2)
    class_names = ["fraud", "legitimate"]

Next, we define how we want to incorporate the predictions from the model into the graph. Since the model outputs a probability
over the classes, we can specify how we integrate this probability into the graph. There are a few options the user can define
using a ``ModelInterfaceOptions`` object:

1. ``threshold`` **(float)**: The threshold beyond which the prediction is incorporated as a fact in the graph. If the probability
   of the class is lower than the threshold, no information is added to the graph. Defaults to 0.5.
2. ``set_lower_bound`` **(bool)**: If True, the lower bound of the probability is set as the fact in the graph.
   if False the lower bound will be 0. Defaults to True.
3. ``set_upper_bound`` **(bool)**: If True, the upper bound of the probability is set as the fact in the graph.
   if False, the upper bound will be 1. Defaults to True.
4. ``snap_value`` **(float)**: If set, all the probabilities that crossed the threshold are snapped to this value. Defaults to 1.0.
   The upper/lower bounds are set to this value according to the ``set_lower_bound`` and ``set_upper_bound`` options.

In our binary classification model, we want predictions that cross the threshold of ``0.5`` to be added to the graph.
For this example we will use a ``snap_value`` of ``1.0`` and set the lower bound of the probability as the fact in the graph.
Therefore any prediction with a probability greater than ``0.5`` will be added to the graph as a fact with bounds of ``[1.0, 1.0]``.

.. code-block:: python

    interface_options = pr.ModelInterfaceOptions(
        threshold=0.5,         # Only process probabilities above 0.5
        set_lower_bound=True,  # Modify the lower bound.
        set_upper_bound=False, # Keep the upper bound unchanged at 1.0.
        snap_value=1.0         # Use 1.0 as the snap value.
    )


Next, we create a ``LogicIntegratedClassifier`` object that helps us integrate the predictions from the model into the graph.

.. code-block:: python

    fraud_detector = pr.LogicIntegratedClassifier(
        model,
        class_names,
        model_name="fraud_detector",
        interface_options=interface_options
    )


To run the model, we perform the same steps as we would with a regular PyTorch model. In this example we use a dummy input.
This gives us a list of facts that can then be added to PyReason.

.. code-block:: python

    transaction_features = torch.rand(1, 5)

    # Get the prediction from the model
    logits, probabilities, classifier_facts = fraud_detector(transaction_features)

We now add the facts to PyReason as normal.

.. code-block:: python

    # Add the classifier-generated facts.
    for fact in classifier_facts:
        pr.add_fact(fact)



Next, we define a knowledge graph that contains information about accounts and its relationships. we also define some context
about the transaction and rules that we want to reason over with the classifier predictions.

.. code-block:: python
    # Create a networkx graph representing a network of accounts.
    G = nx.DiGraph()
    # Add account nodes.
    G.add_node("AccountA", account=1)
    G.add_node("AccountB", account=1)
    G.add_node("AccountC", account=1)

    # Add edges with an attribute "associated".
    G.add_edge("AccountA", "AccountB", associated=1)
    G.add_edge("AccountB", "AccountC", associated=1)
    pr.load_graph(G)

    # Add additional contextual information:
    # 1. A fact indicating the transaction comes from a suspicious location. This could come from a separate fraud detection system.
    pr.add_fact(pr.Fact("suspicious_location(AccountA)", "transaction_fact"))

    # Define a rule: if the fraud detector flags a transaction as fraud and the transaction info is suspicious,
    # then mark the associated account (AccountA) as requiring investigation.
    pr.add_rule(pr.Rule("requires_investigation(acc) <- account(acc), fraud_detector(fraud), suspicious_location(acc)", "investigation_rule"))

    # Define a propagation rule:
    # If an account requires investigation and is connected (via the "associated" relationship) to another account,
    # then the connected account is also flagged for investigation.
    pr.add_rule(pr.Rule("requires_investigation(y) <- requires_investigation(x), associated(x,y)", "propagation_rule"))


Finally, we run the reasoning process and print the output.

.. code-block:: python

    # Run the reasoning engine to allow the investigation flag to propagate through the network.
    pr.settings.allow_ground_rules = True   # The ground rules allow us to use the classifier prediction facts
    pr.settings.atom_trace = True
    interpretation = pr.reason()

    trace = pr.get_rule_trace(interpretation)
    print(f"RULE TRACE: \n\n{trace[0]}\n")



This simple example demonstrates the integration of a machine learning model with PyReason. In practice more complex models
can be used, along with larger and more complex knowledge graphs.
