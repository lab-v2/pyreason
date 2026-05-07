"""
Counterfactual Reasoning Tutorial
================================================

This tutorial extends the cybersecurity inconsistency tutorial by
demonstrating *counterfactual reasoning* on top of PyReason's annotated logic
engine. A counterfactual answers the question:

    "If fact F had not been true (or had been different),
     what would the inferred state of the world look like?"

PyReason does not have a built-in counterfactual operator. Instead we treat
counterfactuals as a meta-procedure: run reasoning on the baseline graph,
then re-run on a perturbed copy of the graph, and diff the two interpretations.
The diff tells us which downstream conclusions causally depended on the
perturbed fact.

Three demos:
    Demo 1 -- Single-fact counterfactual on a single rule
              "If web_server were not exposed, would it still be at risk?"

    Demo 2 -- Counterfactual on a multi-hop rule chain
              "If we remove the exposure fact, does the four-hop chain
              (exposure -> at_risk -> vulnerable -> compromised -> unpatched)
              still cascade?"

    Demo 3 -- Counterfactual interaction with inconsistencies
              "If we remove the asserted patch_confidence fact, does the
              rule-triggered inconsistency from PR #140 disappear?"

Reuses the graph and rules from cybersecurity_inconsistency_ex.py.

Real CVEs used (same as PR #140):
    cve_2021_3156   sudo 1.9.5p1      CVSS 7.8  CWE-121
    cve_2022_0185   linux_kernel_5_1  CVSS 8.4  CWE-121
    cve_2022_26923  openssl_3_0_1     CVSS 7.5  CWE-415
"""

import pyreason as pr
import networkx as nx
import pandas as pd


# ============================================================================
# GRAPH AND RULE BUILDERS
# ============================================================================
# We wrap graph/rule construction in functions because every counterfactual
# run needs a fresh PyReason state. PyReason keeps facts and rules in module-
# level globals, so re-running reasoning requires a full reset.

def build_graph():
    """Build the cybersecurity knowledge graph from PR #140."""
    g = nx.DiGraph()

    # Asset nodes
    g.add_nodes_from(['web_server', 'workstation_1', 'dev_server'])

    # Software nodes
    g.add_nodes_from(['sudo_1_9_5p1', 'linux_kernel_5_1', 'openssl_3_0_1'])

    # CVE nodes
    g.add_nodes_from(['cve_2021_3156', 'cve_2022_0185', 'cve_2022_26923'])

    # Asset -> Software edges
    g.add_edge('web_server',    'sudo_1_9_5p1',     runs=1)
    g.add_edge('workstation_1', 'linux_kernel_5_1', runs=1)
    g.add_edge('dev_server',    'openssl_3_0_1',    runs=1)

    # Software -> CVE edges
    g.add_edge('sudo_1_9_5p1',     'cve_2021_3156',  has_cve=1)
    g.add_edge('linux_kernel_5_1', 'cve_2022_0185',  has_cve=1)
    g.add_edge('openssl_3_0_1',    'cve_2022_26923', has_cve=1)

    return g


def add_baseline_rules():
    pr.add_rule(pr.Rule(
        'at_risk(X) <- runs(X, Y), has_cve(Y, Z)', 'exposure_rule'))
    pr.add_rule(pr.Rule(
        'vulnerable(X):[0.8, 1.0] <- at_risk(X)', 'vulnerability_rule'))
    pr.add_rule(pr.Rule(
        'compromised(X):[0.8, 1.0] <- vulnerable(X):[0.5, 1.0]',
        'compromise_rule'))
    pr.add_rule(pr.Rule(
        'patch_confidence(X):[0.0, 0.2] <- compromised(X):[0.5, 1.0]',
        'unpatched_rule'))


def add_baseline_facts(skip=None):
    """
    The `skip` argument is a set of fact names to OMIT -- this is how we
    implement "remove fact" counterfactuals. Reasoning runs without those
    facts, and we observe what no longer gets inferred downstream.
    """
    if skip is None:
        skip = set()

    facts = [
        ('cvss_2021_3156',  pr.Fact('severity(cve_2021_3156):[0.78, 0.78]',
                                    'cvss_2021_3156', 0, 2)),
        ('cvss_2022_0185',  pr.Fact('severity(cve_2022_0185):[0.84, 0.84]',
                                    'cvss_2022_0185', 0, 2)),
        ('cvss_2022_26923', pr.Fact('severity(cve_2022_26923):[0.75, 0.75]',
                                    'cvss_2022_26923', 0, 2)),
        ('dev_patch_db_fact',
         pr.Fact('patch_confidence(dev_server):[0.9, 1.0]',
                 'dev_patch_db_fact', 0, 4)),
    ]

    for name, fact in facts:
        if name not in skip:
            pr.add_fact(fact)


def reset_pyreason():
    """Reset PyReason to a clean state between counterfactual runs."""
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()


# ============================================================================
# THE COUNTERFACTUAL HARNESS
# ============================================================================
# This is the core abstraction of the tutorial. A counterfactual run is just:
#   1. Reset PyReason
#   2. Build the graph
#   3. Add rules and facts (potentially with some facts removed/added)
#   4. Run reasoning
#   5. Return the final interpretation as a DataFrame for diffing

def run_world(label, skip_facts=None, extra_facts=None, timesteps=4):
    """
    Run PyReason reasoning under a specific counterfactual scenario.

    Parameters
    ----------
    label : str
        Human-readable name for this run (e.g. "baseline", "remove_exposure").
    skip_facts : set of str, optional
        Names of baseline facts to omit (the counterfactual perturbation).
    extra_facts : list of pr.Fact, optional
        Additional facts to inject (for "what if we knew X" counterfactuals).
    timesteps : int
        How many timesteps to reason for.

    Returns
    -------
    dict
        Mapping of (node, predicate) -> [lower, upper] at the final timestep.
    """
    reset_pyreason()

    pr.settings.verbose = False
    pr.settings.atom_trace = True
    pr.settings.store_interpretation_changes = True
    pr.settings.inconsistency_check = True

    pr.load_graph(build_graph())
    add_baseline_rules()
    add_baseline_facts(skip=skip_facts)

    if extra_facts:
        for f in extra_facts:
            pr.add_fact(f)

    interp = pr.reason(timesteps=timesteps)

    # Collect cumulative final-state bounds for every (node, predicate).
    # filter_and_sort_nodes returns one DataFrame per timestep, each showing
    # the bounds known AT that timestep. We walk all timesteps and keep
    # the most recent bound seen for each (node, predicate) pair so we get
    # the true final state, not just whatever changed at the last timestep.
    predicates = ['at_risk', 'vulnerable', 'compromised', 'patch_confidence',
                  'severity']
    state = {}
    for pred in predicates:
        dfs = pr.filter_and_sort_nodes(interp, [pred])
        if not dfs:
            continue
        for df in dfs:
            if df.empty:
                continue
            for _, row in df.iterrows():
                state[(row['component'], pred)] = list(row[pred])

    return label, state, interp


def diff_worlds(baseline_state, cf_state):
    """
    Compare two reasoning outcomes and return the differences.

    Returns
    -------
    pandas.DataFrame
        Columns: node, predicate, baseline_bound, counterfactual_bound, change
        where `change` is one of: 'unchanged', 'collapsed', 'lost', 'gained',
        'shifted'.
    """
    all_keys = set(baseline_state.keys()) | set(cf_state.keys())
    rows = []
    for key in sorted(all_keys):
        node, pred = key
        b = baseline_state.get(key)
        c = cf_state.get(key)

        if b == c:
            change = 'unchanged'
        elif b is None:
            change = 'gained'
        elif c is None:
            change = 'lost'
        elif c == [0.0, 1.0] and b != [0.0, 1.0]:
            change = 'collapsed'   # bound widened to fully unknown
        else:
            change = 'shifted'

        rows.append({
            'node': node,
            'predicate': pred,
            'baseline_bound': b,
            'counterfactual_bound': c,
            'change': change,
        })

    df = pd.DataFrame(rows)
    return df


def print_diff(title, df):
    """Pretty-print a counterfactual diff, hiding unchanged rows."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)
    changed = df[df['change'] != 'unchanged']
    if changed.empty:
        print("  (no downstream changes -- the perturbed fact had no effect)")
    else:
        print(changed.to_string(index=False))
    print()


# ============================================================================
# DEMO 1 -- BASIC COUNTERFACTUAL ON A SINGLE EDGE
# ============================================================================
# Question: "If web_server did NOT run sudo_1_9_5p1, would it still be at_risk?"
#
# This isn't a fact-removal -- it's a graph perturbation. The exposure_rule
# fires off the `runs` and `has_cve` edges, so to counterfactually disconnect
# web_server from its CVE we have to rebuild the graph without that edge.
#
# We handle this by passing a custom graph to a one-off run.

def demo_1():
    print("\n" + "#" * 70)
    print("# DEMO 1 -- Single-edge counterfactual")
    print("#" * 70)
    print("""
We ask: 'If web_server did not run sudo_1_9_5p1, would it still be at_risk?'
This perturbs the graph itself, not just the facts. We rebuild the graph
without the runs(web_server, sudo_1_9_5p1) edge and re-run reasoning.
""")

    # --- Baseline run ---
    _, baseline_state, _ = run_world('baseline')

    # --- Counterfactual run with edge removed ---
    reset_pyreason()
    pr.settings.verbose = False
    pr.settings.atom_trace = True
    pr.settings.store_interpretation_changes = True

    g_cf = build_graph()
    g_cf.remove_edge('web_server', 'sudo_1_9_5p1')
    pr.load_graph(g_cf)
    add_baseline_rules()
    add_baseline_facts()

    interp_cf = pr.reason(timesteps=4)
    cf_state = {}
    for pred in ['at_risk', 'vulnerable', 'compromised', 'patch_confidence']:
        dfs = pr.filter_and_sort_nodes(interp_cf, [pred])
        if not dfs:
            continue
        for df in dfs:
            if df.empty:
                continue
            for _, row in df.iterrows():
                cf_state[(row['component'], pred)] = list(row[pred])

    diff = diff_worlds(baseline_state, cf_state)
    print_diff("DEMO 1 DIFF: remove edge runs(web_server, sudo_1_9_5p1)", diff)

    print("INTERPRETATION:")
    print("  web_server loses at_risk, vulnerable, and compromised.")
    print("  workstation_1 and dev_server are unaffected (their edges remain).")
    print("  This confirms the exposure_rule depends on the runs/has_cve chain.")


# ============================================================================
# DEMO 2 -- COUNTERFACTUAL ON A MULTI-HOP RULE CHAIN
# ============================================================================
# We test what happens when we inject a NEGATIVE counterfactual mid-chain --
# what if we asserted at_risk(workstation_1):[0,0] (definitely not at risk)
# even though the graph would otherwise infer it?
#
# asserting at_risk:[0,0] should clash with the rule's
# inference of at_risk:[1,1] -- this is itself a kind of inconsistency,
# which is great because it shows the boundary between counterfactuals
# and inconsistencies.

def demo_2():
    print("\n" + "#" * 70)
    print("# DEMO 2 -- Mid-chain counterfactual injection")
    print("#" * 70)
    print("""
We ask: 'What if we KNEW workstation_1 were not at risk, despite the graph?'
We inject a fact at_risk(workstation_1):[0.0, 0.0] and observe whether the
downstream chain still infers vulnerable / compromised / unpatched.
""")

    _, baseline_state, _ = run_world('baseline')

    extra = [pr.Fact('at_risk(workstation_1):[0.0, 0.0]',
                     'cf_not_at_risk', 0, 4)]
    _, cf_state, _ = run_world('cf_not_at_risk', extra_facts=extra)

    diff = diff_worlds(baseline_state, cf_state)
    print_diff("DEMO 2 DIFF: inject at_risk(workstation_1):[0.0, 0.0]", diff)

    print("INTERPRETATION:")
    print("  The exposure_rule still fires from runs/has_cve and tries to")
    print("  infer at_risk(workstation_1):[1,1]. The injected counterfactual")
    print("  asserts [0,0]. These bounds do not overlap -> PyReason resolves")
    print("  to [0.0, 1.0] (unknown). Downstream rules require >= 0.5 lower")
    print("  bound to fire, so the chain BREAKS at workstation_1.")
    print("  This shows counterfactuals propagate forward through rule chains.")


# ============================================================================
# DEMO 3 -- COUNTERFACTUAL INTERACTION WITH INCONSISTENCY
# ============================================================================
# dev_server has a rule-triggered inconsistency: the unpatched_rule
# infers patch_confidence:[0.0, 0.2] but a fact asserts [0.9, 1.0].
#
# Counterfactual question: "If we did NOT have the asserted patch_confidence
# fact, would the inconsistency disappear?"

def demo_3():
    print("\n" + "#" * 70)
    print("# DEMO 3 -- Counterfactual to diagnose an inconsistency")
    print("#" * 70)
    print("""
We had a rule-triggered inconsistency on dev_server: the unpatched_rule
infers patch_confidence:[0.0, 0.2] but the fact 'dev_patch_db_fact' asserts
patch_confidence:[0.9, 1.0]. We counterfactually remove that fact and check
whether the inconsistency disappears.
""")

    _, baseline_state, _ = run_world('baseline')
    _, cf_state, _ = run_world('cf_no_patch_fact',
                               skip_facts={'dev_patch_db_fact'})

    diff = diff_worlds(baseline_state, cf_state)
    print_diff("DEMO 3 DIFF: skip dev_patch_db_fact", diff)

    print("INTERPRETATION:")
    print("  In baseline, dev_server.patch_confidence collapsed to [0,1] due")
    print("  to the conflict between rule-inferred [0.0,0.2] and asserted")
    print("  [0.9,1.0]. With the fact removed, only the rule fires, so")
    print("  patch_confidence(dev_server) = [0.0, 0.2] cleanly. The")
    print("  inconsistency DISAPPEARS -- this counterfactual confirms the")
    print("  asserted fact was a necessary cause of the inconsistency.")
    print()
    print("  Counterfactuals are a tool for ATTRIBUTION: they isolate which")
    print("  inputs are load-bearing for a given downstream outcome.")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    demo_1()
    demo_2()
    demo_3()

