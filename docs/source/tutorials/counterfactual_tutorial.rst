Counterfactual Reasoning
=========================

.. note::

   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/counterfactual_tutorial_ex.py>`_

This tutorial extends the cybersecurity inconsistency tutorial by adding
*counterfactual reasoning* on top of PyReason's annotated logic engine.
Where the inconsistency tutorial asked "do these facts conflict?", the
counterfactual tutorial asks "what would the inferred world look like if
this fact were not true (or were different)?"

PyReason does not provide a built-in counterfactual operator. Instead we
implement counterfactuals as a meta-procedure: run reasoning on the
baseline graph, run again on a perturbed copy, then diff the two
interpretations. The diff identifies which downstream conclusions
causally depended on the perturbation.

.. note::

   This tutorial reuses the cybersecurity knowledge graph from the
   *Cybersecurity Inconsistency* tutorial and assumes familiarity with
   that material.

Background
----------

A **counterfactual** in logic answers a "what if" question by re-running
inference under a hypothetically modified set of premises. Counterfactual
reasoning is widely used in:

- **Causal attribution** -- isolating which inputs are load-bearing for a
  given conclusion.
- **Inconsistency diagnosis** -- determining which premise is responsible
  for an observed contradiction.
- **Robustness analysis** -- checking how sensitive a conclusion is to
  small perturbations of the input.

In PyReason terms, the perturbation is one of:

1. **Removing a baseline fact** -- "what if we didn't know X?"
2. **Injecting a contrary fact** -- "what if we knew NOT X?"
3. **Modifying the graph** (removing edges or nodes) -- "what if this
   relationship didn't exist?"

The Counterfactual Harness
--------------------------

Counterfactuals require multiple PyReason runs that share rules and a
graph template but differ in their facts or topology. The harness
``run_world`` in this tutorial wraps each run in a function that:

1. Resets PyReason state (``pr.reset()``, ``pr.reset_rules()``,
   ``pr.reset_settings()``).
2. Builds a fresh graph (optionally with edges/nodes removed).
3. Loads baseline rules.
4. Loads baseline facts (optionally with some omitted via ``skip_facts``).
5. Optionally injects extra facts (``extra_facts``).
6. Runs reasoning to a fixed point and collects bounds for every
   ``(node, predicate)`` pair across all timesteps.

The state-collection loop walks every timestep DataFrame returned by
``filter_and_sort_nodes`` and keeps the latest bound seen for each pair.
This produces the cumulative final state, not just whatever changed at
the last timestep -- a subtle but important detail. Looking only at the
last DataFrame can miss bounds that were set earlier and never updated.

Two such state dictionaries can then be diffed via ``diff_worlds`` to
produce a counterfactual report. Diff classifies each ``(node, predicate)``
change as ``unchanged``, ``gained``, ``lost``, ``collapsed``, or
``shifted``.

Demo 1: Single-edge counterfactual
-----------------------------------

**Question:** *If* ``web_server`` *did not run* ``sudo_1_9_5p1`` *, would
it still be at_risk?*

This perturbation is structural -- the ``exposure_rule`` requires the
two-hop pattern ``runs(X, Y), has_cve(Y, Z)``. Removing the
``runs(web_server, sudo_1_9_5p1)`` edge breaks the first hop, so the rule
should no longer fire for ``web_server``.

Observed outcome:

================  =================  =================  ==================  =========
node              predicate          baseline_bound     counterfactual      change
================  =================  =================  ==================  =========
web_server        at_risk            [1.0, 1.0]         (none)              lost
web_server        vulnerable         [0.8, 1.0]         (none)              lost
web_server        compromised        [0.8, 1.0]         (none)              lost
web_server        patch_confidence   [0.0, 0.2]         (none)              lost
================  =================  =================  ==================  =========

``workstation_1`` and ``dev_server`` are unaffected because their edges
remain intact. The entire downstream chain on ``web_server`` is causally
rooted in that single edge -- one structural perturbation, four lost
conclusions, all on the same node.

Demo 2: Mid-chain counterfactual injection
-------------------------------------------

**Question:** *What if we asserted that* ``workstation_1`` *is NOT at
risk, even though the graph would otherwise infer it?*

We inject ``at_risk(workstation_1):[0.0, 0.0]`` as a fact. The graph
topology would normally cause the ``exposure_rule`` to infer
``at_risk(workstation_1):[1.0, 1.0]``.

Observed outcome:

================  =================  =================  ==================  =========
node              predicate          baseline_bound     counterfactual      change
================  =================  =================  ==================  =========
workstation_1     at_risk            [1.0, 1.0]         [0.0, 0.0]          shifted
workstation_1     vulnerable         [0.8, 1.0]         (none)              lost
workstation_1     compromised        [0.8, 1.0]         (none)              lost
workstation_1     patch_confidence   [0.0, 0.2]         (none)              lost
================  =================  =================  ==================  =========

A subtlety worth flagging here: the ``at_risk`` bound *does not* collapse
to ``[0.0, 1.0]`` (the standard inconsistency-resolution outcome). It
stays at ``[0.0, 0.0]``. This is because PyReason's annotated logic is
**monotonic** -- bounds can only tighten over time, never widen. The
injected ``[0.0, 0.0]`` arrives first; the rule's later attempt to write
``[1.0, 1.0]`` would require widening the bound, so the write is
silently rejected.

The downstream effect is what we expected, but the mechanism is more
subtle than "inconsistency resolution kicks in." With ``at_risk`` pinned
at ``[0.0, 0.0]``, the ``vulnerability_rule`` cannot fire (its body atom
is effectively false), and the rest of the chain breaks. The final three
predicates are lost on ``workstation_1``.

This demo illustrates two things at once:

1. **Counterfactual injection at one stage of a rule chain neutralizes
   all downstream inferences for that node.** A single ``[0.0, 0.0]``
   fact is enough to break the cascade.
2. **Fact-arrival order matters in PyReason.** An early tight bound can
   block later rule writes that would otherwise fire. Worth keeping in
   mind when designing rule sets where multiple sources may write to the
   same predicate.

Demo 3: Counterfactual to diagnose an inconsistency
----------------------------------------------------

The cybersecurity inconsistency tutorial introduced a rule-triggered
inconsistency on ``dev_server``: the ``unpatched_rule`` infers
``patch_confidence(dev_server):[0.0, 0.2]`` while the fact
``dev_patch_db_fact`` asserts ``[0.9, 1.0]``.

**Counterfactual question:** *If we did not have* ``dev_patch_db_fact``,
*would the inconsistency disappear?*

We re-run reasoning with that single fact omitted.

Observed outcome:

================  =================  =================  ==================  =========
node              predicate          baseline_bound     counterfactual      change
================  =================  =================  ==================  =========
dev_server        patch_confidence   [0.9, 1.0]         [0.0, 0.2]          shifted
================  =================  =================  ==================  =========

In the baseline, ``patch_confidence(dev_server)`` ends up at ``[0.9,
1.0]`` -- the asserted fact's bound. The same monotonicity behavior from
Demo 2 is at work here: the asserted fact arrives first, and the rule's
attempted ``[0.0, 0.2]`` write would require widening, so it is rejected.
The conflict is *latent* -- two pieces of evidence point in opposite
directions, but only one survives.

With ``dev_patch_db_fact`` removed, the rule's bound writes cleanly to
``[0.0, 0.2]``. The diff between the two runs makes the latent conflict
visible: removing one fact flips the conclusion entirely.

This pattern is **counterfactual attribution for inconsistencies**. When
a baseline conclusion is suspicious -- maybe two sources should be
disagreeing but the engine reports a clean answer -- counterfactual
removal of each contributing fact in turn reveals which inputs are
load-bearing for the surviving conclusion. In a more complex setting
where many facts contribute through many rules, this becomes a
systematic technique for blame assignment.

Running the Code
----------------

Execute the tutorial script::

    python examples/counterfactual_tutorial_ex.py

Key Takeaways
-------------

1. **Counterfactuals are a meta-procedure on top of PyReason**, not a
   built-in operator. They are implemented by re-running reasoning with
   perturbed inputs and diffing the outcomes.

2. **Counterfactual perturbations propagate through rule chains.**
   Pinning a predicate at one stage of the chain neutralizes all
   downstream inferences for the affected node.

3. **Monotonicity governs what survives.** PyReason bounds can only
   tighten, never widen. When two writes conflict, the earlier (or
   tighter) one wins and the later one is silently rejected -- meaning
   contradictions can be *latent* rather than loudly flagged.

4. **Counterfactuals diagnose latent inconsistencies.** When two premises
   conflict but only one survives, counterfactual removal of each in
   turn reveals which premise is the load-bearing contributor.

5. **Three perturbation types:** fact removal, fact injection, and graph
   modification. Arbitrary combinations are supported by the harness.
