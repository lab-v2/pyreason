Counterfactual Reasoning
=========================

.. note::

   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/counterfactual_tutorial_ex.py>`_

This tutorial extends the cybersecurity inconsistency tutorial. The
inconsistency tutorial asked: *"do these facts conflict?"* This
tutorial asks the opposite question: *"if I changed something, would
the conclusions still hold?"* That is what a counterfactual is -- a
"what if" question answered by re-running reasoning on a modified
input.

PyReason has no built-in counterfactual operator. We implement them
manually: run reasoning on the original graph, run again on a modified
copy, and compare the two final states. The differences tell us which
conclusions depended on the change.

.. note::

   This tutorial reuses the cybersecurity knowledge graph from the
   *Cybersecurity Inconsistency* tutorial. Familiarity with that tutorial
   is assumed.

What a Grounding Is
-------------------

Before the demos: a brief note on terminology, since the rest of the
tutorial leans on this concept.

A rule like ``at_risk(X) <- runs(X, Y), has_cve(Y, Z)`` does not "fire"
once. It fires once for each combination of nodes that satisfies the
body. Each such combination is called a **grounding**. In the
cybersecurity graph there are three groundings of this rule, one for
each asset:

============= =========================== ============================
Grounding for X = ...                     Y = ..., Z = ...
============= =========================== ============================
1             ``web_server``              ``sudo_1_9_5p1``, ``cve_2021_3156``
2             ``workstation_1``           ``linux_kernel_5_1``, ``cve_2022_0185``
3             ``dev_server``              ``openssl_3_0_1``, ``cve_2022_26923``
============= =========================== ============================

Each grounding is independent. Removing a graph edge or fact eliminates
any grounding that depended on it; the others fire normally. This is
why counterfactual perturbations have such localized effects -- they
surgically delete specific groundings without touching the rest.

The Three Demos
---------------

The script ``counterfactual_tutorial_ex.py`` walks through three
counterfactuals:

- **Demo 1** -- remove a graph edge. Show that one grounding of
  ``exposure_rule`` disappears, and the cascade collapses for the
  affected asset.
- **Demo 2** -- inject a contradicting fact. Show that PyReason
  detects the conflict and reports an inconsistency.
- **Demo 3** -- start from a graph that *already has* an inconsistency.
  Counterfactually remove a candidate cause and check whether the
  inconsistency disappears.

Each run writes a CSV trace alongside the script. Trace rows
are referenced inline below.

Demo 1: Remove a Graph Edge
---------------------------

**Question:** if ``web_server`` did not run ``sudo_1_9_5p1``, would it
still be classified as at risk?

The ``exposure_rule`` says: a host is at risk if it runs some software
that has a CVE. In PyReason, a graph edge with an attribute is treated
as a fact -- the ``runs=1`` edge between ``web_server`` and
``sudo_1_9_5p1`` becomes the fact ``runs(web_server, sudo_1_9_5p1)``
during reasoning. Removing the edge removes that fact, so the
grounding of ``exposure_rule`` for ``web_server`` no longer has
anything to bind ``Y`` to and cannot fire.

In the baseline trace, the rule fires three times -- once per asset.
The relevant rows are::

    Time Op Node           Label    Old Bound  New Bound  Caused By       Consistent  Clause-1
    0    1  web_server     at_risk  [0.0,1.0]  [1.0,1.0]  exposure_rule   True        [('web_server', 'sudo_1_9_5p1')]
    0    1  workstation_1  at_risk  [0.0,1.0]  [1.0,1.0]  exposure_rule   True        [('workstation_1', 'linux_kernel_5_1')]
    0    1  dev_server     at_risk  [0.0,1.0]  [1.0,1.0]  exposure_rule   True        [('dev_server', 'openssl_3_0_1')]

The ``Clause-1`` column shows which graph elements satisfied each
grounding's body. After we remove the edge, the counterfactual trace
contains only the second and third rows. The ``web_server`` row is
gone -- because the edge it depended on no longer exists.

The cascade follows automatically. ``vulnerability_rule``,
``compromise_rule``, and ``unpatched_rule`` all need their predecessor
to have fired. With ``at_risk(web_server)`` missing, none of them have
a valid grounding for ``web_server``.

Diff vs. baseline (final state of each run, side by side):

================  =================  =================  ==================
node              predicate          baseline           counterfactual
================  =================  =================  ==================
web_server        at_risk            [1.0, 1.0]         (none)
web_server        vulnerable         [0.8, 1.0]         (none)
web_server        compromised        [0.8, 1.0]         (none)
web_server        patch_confidence   [0.0, 0.2]         (none)
================  =================  =================  ==================

``workstation_1`` and ``dev_server`` are unaffected -- their groundings
remain intact. One edge removed, four conclusions lost, all on a single
asset. That is the basic shape of a counterfactual: a small input
change has a localized but compounded effect downstream.

Demo 2: Inject a Contradicting Fact
-----------------------------------

**Question:** what happens if we assert that ``workstation_1`` is
*definitely not* at risk, even though the graph would normally infer
that it is?

We add a fact ``at_risk(workstation_1):[0.0, 0.0]`` -- meaning "I am
100% certain this is false." The graph still says it should be
``[1.0, 1.0]`` (true), so two sources will disagree.

In the trace, the injected fact lands first::

    Time Op Node           Label    Old Bound  New Bound  Caused By       Consistent
    0    0  workstation_1  at_risk  [0.0,1.0]  [0.0,0.0]  cf_not_at_risk  True

Then the ``exposure_rule`` fires and tries to write ``[1.0, 1.0]``.
The two bounds do not overlap, so PyReason flags an inconsistency::

    Time Op Node           Label    Old Bound  New Bound  Caused By       Consistent
    0    1  workstation_1  at_risk  [0.0,0.0]  [0.0,1.0]  exposure_rule   False

    Inconsistency Message:
    "Inconsistency occurred. Conflicting bounds for at_risk(workstation_1).
     Update from [0.000, 0.000] to [1.000, 1.000] is not allowed.
     Setting bounds to [0,1] and static=True for this timestep."

For that one timestep, the bound is set to ``[0.0, 1.0]`` (fully
unknown) and marked static. At the next timestep, the injected fact
re-asserts itself (its time window covers all timesteps), pulling the
bound back to ``[0.0, 0.0]``. The final state shows ``[0.0, 0.0]`` --
the injection wins by being re-asserted.

**Why the cascade breaks downstream:**

The next rule in the chain is ``vulnerability_rule``::

    vulnerable(X):[0.8, 1.0] <- at_risk(X)

In the baseline trace, this rule fires three times (one grounding per
asset)::

    Time Op Node           Label       Caused By           Consistent  Clause-1
    0    2  web_server     vulnerable  vulnerability_rule  True        ['web_server']
    0    2  workstation_1  vulnerable  vulnerability_rule  True        ['workstation_1']
    0    2  dev_server     vulnerable  vulnerability_rule  True        ['dev_server']

In the counterfactual trace, only two rows appear -- the
``workstation_1`` grounding is missing::

    0    2  web_server     vulnerable  vulnerability_rule  True        ['web_server']
    0    2  dev_server     vulnerable  vulnerability_rule  True        ['dev_server']

That grounding does not fire because its body
(``at_risk(workstation_1)``) is held at ``[0.0, 0.0]``, which fails
the rule's threshold check. With no ``vulnerable(workstation_1)``,
``compromise_rule`` cannot fire for ``workstation_1`` either, and the
chain breaks one grounding at a time.

Diff vs. baseline:

================  =================  =================  ==================
node              predicate          baseline           counterfactual
================  =================  =================  ==================
workstation_1     at_risk            [1.0, 1.0]         [0.0, 0.0]
workstation_1     vulnerable         [0.8, 1.0]         (none)
workstation_1     compromised        [0.8, 1.0]         (none)
workstation_1     patch_confidence   [0.0, 0.2]         (none)
================  =================  =================  ==================

A single injected fact eliminated three downstream groundings, exactly
as in Demo 1 -- but via a different mechanism. In Demo 1 a graph edge
was removed; in Demo 2 a fact was added that produced an inconsistency,
and the resolved bound was incompatible with downstream rules.

Demo 3: Diagnose an Existing Inconsistency
------------------------------------------

Demos 1 and 2 perturbed an otherwise-consistent baseline. Demo 3 is
different: **the baseline already contains an inconsistency** before
any perturbation. The counterfactual question is: which fact is
causing it?

**The baseline inconsistency:**

The four-rule chain ends with ``unpatched_rule``, which says: a
compromised host has low patch confidence::

    patch_confidence(X):[0.0, 0.2] <- compromised(X):[0.5, 1.0]

This rule fires for all three assets. Separately, the fact
``dev_patch_db_fact`` asserts ``patch_confidence(dev_server):[0.9, 1.0]``
-- "the patch database says dev_server is well patched."

For ``dev_server``, both writes target the same atom with
non-overlapping bounds. Looking at the baseline trace::

    Time Op Node        Label             Old Bound  New Bound  Caused By           Consistent
    0    0  dev_server  patch_confidence  [0.0,1.0]  [0.9,1.0]  dev_patch_db_fact   True
    ...
    0    4  dev_server  patch_confidence  [0.9,1.0]  [0.0,1.0]  unpatched_rule      False

    Inconsistency Message:
    "Inconsistency occurred. Conflicting bounds for patch_confidence(dev_server).
     Update from [0.900, 1.000] to [0.000, 0.200] is not allowed.
     Setting bounds to [0,1] and static=True for this timestep."

For ``web_server`` and ``workstation_1`` the same rule operation is
consistent::

    0    4  web_server     patch_confidence  [0.0,1.0]  [0.0,0.2]  unpatched_rule  True
    0    4  workstation_1  patch_confidence  [0.0,1.0]  [0.0,0.2]  unpatched_rule  True

Why is only ``dev_server`` inconsistent? Because only ``dev_server``
had a prior asserted bound for ``patch_confidence`` (the
``dev_patch_db_fact``). The other two assets had the default
``[0.0, 1.0]`` bound, which the rule's update fits inside.

After the inconsistency, the asserted fact re-asserts at later
timesteps, so the final state ends up at ``[0.9, 1.0]``. But the
trace preserves the record of the conflict that occurred along the way.

**The counterfactual:**

We re-run reasoning with ``dev_patch_db_fact`` removed.

In the counterfactual trace, the same ``unpatched_rule`` grounding
fires for ``dev_server`` -- the rule body still holds. But now there
is no prior bound to conflict with::

    0    4  dev_server  patch_confidence  [0.0,1.0]  [0.0,0.2]  unpatched_rule  True

Consistent. No inconsistency message.

Diff vs. baseline:

================  =================  =================  ==================
node              predicate          baseline           counterfactual
================  =================  =================  ==================
dev_server        patch_confidence   [0.9, 1.0]         [0.0, 0.2]
================  =================  =================  ==================

Removing one fact eliminated the baseline inconsistency. This is the
diagnostic pattern -- when an inconsistency exists and you want to
know which fact caused it, counterfactually remove each candidate and
check whether the conflict goes away.

In a real system with many facts and many rules, this becomes a
systematic technique: remove each fact one at a time, observe which
removals eliminate the inconsistency, and you have identified the
load-bearing inputs.

Notice that the *grounding itself* is identical in both runs. The
``unpatched_rule`` grounding for ``dev_server`` fires in both. What
changes is the outcome of that grounding's update -- inconsistent in
the baseline, consistent in the counterfactual. That is a more subtle
effect than Demos 1 and 2, where the fact change eliminated
groundings outright. Here the grounding stays; only its consistency
changes.

Running the Code
----------------

::

    python examples/counterfactual_tutorial_ex.py

CSV traces are written to the working directory. The script runs
all three demos in sequence and prints the diffs above.

Summary
-------

Two things to take away:

1. **Counterfactuals are re-runs and diffs.** PyReason does not
   provide them as a built-in operator. The pattern is: run, perturb,
   run again, compare.

2. **Perturbations affect groundings.** The unit of rule firing is the
   grounding -- a specific instantiation of a rule's variables.
   Counterfactual changes either eliminate groundings (Demos 1 and 2)
   or change whether their resulting updates are consistent (Demo 3).
