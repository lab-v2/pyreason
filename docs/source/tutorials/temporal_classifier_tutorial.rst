Temporal Classifier Tutorial
=============================

This tutorial demonstrates how to use the ``TemporalLogicIntegratedClassifier``
to combine a neural network with PyReason's temporal logic reasoning. The classifier
converts ML model outputs into PyReason facts at each timestep, allowing rules
to reason about how observations evolve over time.

.. note::
   Find the full, executable code `here 
<https://github.com/lab-v2/pyreason/blob/main/examples/weather_temporal_classifier_ex.py>`_

Scenario
--------

We monitor sky conditions over time using a neural classifier that outputs
one of three weather states: ``sunny``, ``cloudy``, or ``rainy``. The classifier
takes three simulated sensor features as input:

1. Cloud cover (0–100%)
2. Humidity (20–100%)
3. Precipitation rate (0–15 mm/hr)

Over multiple timesteps, temporal rules derive a storm warning from sustained
rain, and ultimately conclude that a voyage should be cancelled when conditions
remain unsafe.

Setting Up the Classifier
--------------------------

We start by defining a simple linear model with three input features and three
output classes. Since this is a demo, the model is untrained — its outputs depend
on the random seed.

.. code:: python

   import torch
   import torch.nn as nn

   model = nn.Linear(3, 3)
   conditions = ["sunny", "cloudy", "rainy"]

We also define an input function that produces realistic feature values:

.. code:: python

   def input_fn():
       cloud_cover = torch.rand(1, 1) * 100      # 0–100
       humidity = 20 + torch.rand(1, 1) * 80     # 20–100
       precip_rate = torch.rand(1, 1) * 15       # 0–15
       return torch.cat([cloud_cover, humidity, precip_rate], dim=1)

Configuring the Interface
--------------------------

The ``ModelInterfaceOptions`` control how model probabilities are converted
into PyReason facts. We require a probability threshold of ``0.5`` for a class
to be emitted as a fact, and snap the upper bound to ``1.0``:

.. code:: python

   from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions

   interface_options = ModelInterfaceOptions(
       threshold=0.5,
       set_lower_bound=True,
       set_upper_bound=False,
       snap_value=1.0
   )

Wrapping with the Temporal Classifier
--------------------------------------

The ``TemporalLogicIntegratedClassifier`` wraps the model so it can be polled
across timesteps and emit facts at each call:

.. code:: python

   from datetime import timedelta
   from pyreason.scripts.learning.classification.temporal_classifier import 
TemporalLogicIntegratedClassifier

   conditions_checker = TemporalLogicIntegratedClassifier(
       model,
       conditions,
       identifier="sky",
       interface_options=interface_options,
       poll_interval=timedelta(seconds=1),
       poll_condition="cloudy",
       input_fn=input_fn
   )

Rules
-----

We define two temporal rules. The ``<-1`` operator means "look at the antecedent
from one timestep ago."

1. A storm warning is derived one step after rain is observed.
2. A voyage is cancelled when both rain and a storm warning hold simultaneously.

.. code:: python

   import pyreason as pr
   from pyreason.scripts.rules.rule import Rule

   pr.add_rule(Rule("storm_warning(sky) <-1 rainy(sky)", "warning rule"))
   pr.add_rule(Rule("cancel_voyage(sky) <-1 rainy(sky), storm_warning(sky)", "cancel rule"))

Running the Loop
----------------

Each iteration polls the classifier, adds the resulting facts to PyReason,
runs reasoning for one timestep, and checks whether ``cancel_voyage`` has fired:

.. code:: python

   from pyreason.pyreason import _Settings as Settings, reason, get_rule_trace, add_fact, get_time, 
Query

   max_iterations = 5
   for condition_iter in range(max_iterations):
       features = input_fn()
       t = get_time()
       logits, probs, classifier_facts = conditions_checker(features, t1=t, t2=t)

       for fact in classifier_facts:
           add_fact(fact)

       settings = Settings
       settings.atom_trace = True
       settings.verbose = False
       again = False if condition_iter == 0 else True
       interpretation = reason(timesteps=1, again=again, restart=False)

       if interpretation.query(Query("cancel_voyage(sky)")):
           print("Cancel voyage! Unsafe sky conditions detected.")
           break

Expected Output
---------------

With seed ``91``, the classifier produces a sequence where ``cloudy`` is observed
at timestep 0 followed by sustained ``rainy`` observations. The full chain fires
as follows:

- **t=0:** ``cloudy(sky)`` observed.
- **t=1:** ``rainy(sky)`` observed.
- **t=2:** ``rainy(sky)`` observed again. ``storm_warning(sky)`` is derived from t=1's rain.
- **t=3:** ``rainy(sky)`` and ``storm_warning(sky)`` both hold at t=2 → ``cancel_voyage(sky)`` fires.

Different seeds produce different classification sequences, so the chain will
not always reach the terminal state. Try seeds ``47`` (cloudy only), ``42``
(sunny only), or ``102`` (mixed but no terminal trigger) to compare.
