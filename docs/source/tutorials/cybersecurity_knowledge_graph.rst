Cybersecurity Knowledge Graph
==============================

In this tutorial, we build a small cybersecurity knowledge graph using PyReason.
We model network assets, the software they run, and real CVEs that affect that
software. We then demonstrate how PyReason infers which assets are at risk and
how it detects two types of inconsistency.

.. note::

   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/cybersecurity_knowledge_graph_ex.py>`_

Background
----------

A **CVE** (Common Vulnerabilities and Exposures) is a standardised ID for a
known security vulnerability, for example ``CVE-2021-3156``.

A **CVSS score** rates the severity of a CVE on a 0--10 scale. We divide by 10
to normalise it into the [0, 1] range used by PyReason annotation bounds.

The CVEs in this tutorial are real entries from the
`National Vulnerability Database <https://nvd.nist.gov/vuln/search>`_:

+------------------+---------------------+-------+----------------------------------+
| CVE ID           | Software            | CVSS  | Description                      |
+==================+=====================+=======+==================================+
| CVE-2021-3156    | sudo 1.9.5p1        | 7.8   | Heap buffer overflow (CWE-121)   |
+------------------+---------------------+-------+----------------------------------+
| CVE-2022-0185    | Linux Kernel 5.1    | 8.4   | Stack overflow (CWE-121)         |
+------------------+---------------------+-------+----------------------------------+
| CVE-2022-26923   | OpenSSL 3.0.1       | 7.5   | Double free (CWE-415)            |
+------------------+---------------------+-------+----------------------------------+

Graph
-----

The graph has three layers of nodes connected by directed edges:

.. code-block:: text

   [asset]  --runs-->  [software]  --has_cve-->  [CVE]

.. code-block:: python

   import pyreason as pr
   import networkx as nx

   pr.reset()
   pr.reset_rules()

   g = nx.DiGraph()

   # Asset nodes
   g.add_nodes_from(['web_server', 'workstation_1', 'dev_server'])

   # Software nodes
   g.add_nodes_from(['sudo_1_9_5p1', 'linux_kernel_5_1', 'openssl_3_0_1'])

   # CVE nodes
   g.add_nodes_from(['CVE_2021_3156', 'CVE_2022_0185', 'CVE_2022_26923'])

   # Which asset runs which software
   g.add_edge('web_server',    'sudo_1_9_5p1',     runs=1)
   g.add_edge('workstation_1', 'linux_kernel_5_1', runs=1)
   g.add_edge('dev_server',    'openssl_3_0_1',    runs=1)

   # Which CVE affects which software
   g.add_edge('sudo_1_9_5p1',     'CVE_2021_3156',  has_cve=1)
   g.add_edge('linux_kernel_5_1', 'CVE_2022_0185',  has_cve=1)
   g.add_edge('openssl_3_0_1',    'CVE_2022_26923', has_cve=1)

We then configure PyReason and load the graph:

.. code-block:: python

   pr.settings.verbose = True
   pr.settings.atom_trace = True
   pr.settings.inconsistency_check = True

   pr.load_graph(g)

We declare ``vulnerable`` and ``patched`` as mutually exclusive predicates.
Setting one automatically updates the other to its negated bound:

.. code-block:: python

   pr.add_inconsistent_predicate('vulnerable', 'patched')

Rules
-----

The rules we want to add are:

1. An asset is ``at_risk`` if it runs software that has a CVE.
2. An asset that is ``at_risk`` is also ``vulnerable`` with confidence [0.8, 1.0].

.. code-block:: python

   pr.add_rule(pr.Rule('at_risk(x) <- runs(x,y), has_cve(y,z)', 'exposure_rule'))
   pr.add_rule(pr.Rule('vulnerable(x):[0.8,1.0] <- at_risk(x)', 'vulnerability_rule'))

Facts
-----

We seed the graph with CVE severity scores from NVD, normalised to [0, 1]:

.. code-block:: python

   pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.78,0.78]',  'sudo_cve_severity',    0, 2))
   pr.add_fact(pr.Fact('severity(CVE_2022_0185):[0.84,0.84]',  'kernel_cve_severity',  0, 2))
   pr.add_fact(pr.Fact('severity(CVE_2022_26923):[0.75,0.75]', 'openssl_cve_severity', 0, 2))

Inconsistency Demo 1: Monotonic Reasoning Violation
-----------------------------------------------------

PyReason's reasoning is monotonic -- bounds can only get tighter over time.
Two data sources disagree on the severity of ``CVE_2021_3156`` with
non-overlapping bounds, which PyReason cannot reconcile:

.. code-block:: python

   pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.8,1.0]', 'severity_source_A', 0, 2))
   pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.0,0.1]', 'severity_source_B', 0, 2))

``[0.8, 1.0]`` and ``[0.0, 0.1]`` do not overlap. PyReason flags the conflict
and resolves the annotation to ``[0.0, 1.0]`` (complete uncertainty).

Inconsistency Demo 2: Inconsistent Predicate List (IPL) Conflict
-----------------------------------------------------------------

An asset management database says ``web_server`` is patched. A vulnerability
scanner says it is vulnerable. Both assert high confidence:

.. code-block:: python

   pr.add_fact(pr.Fact('patched(web_server):[0.9,1.0]',    'patch_db_fact',     0, 2))
   pr.add_fact(pr.Fact('vulnerable(web_server):[0.9,1.0]', 'vuln_scanner_fact', 0, 2))

Because ``vulnerable`` and ``patched`` are in the IPL, these two facts
contradict each other. PyReason resolves both to ``[0.0, 1.0]`` and flags
the conflict in the rule trace.

Running PyReason
----------------

.. code-block:: python

   interpretation = pr.reason(timesteps=2)

Expected Output
---------------

**Assets at risk:**

.. code-block:: text

   TIMESTEP 0:
          component     at_risk
   0     web_server  [1.0, 1.0]
   1  workstation_1  [1.0, 1.0]
   2     dev_server  [1.0, 1.0]

All three assets are marked ``at_risk`` because each runs software with a
known CVE.

**CVE severity (Demo 1):**

.. code-block:: text

   TIMESTEP 0:
           component      severity
   0   CVE_2022_0185  [0.84, 0.84]
   1  CVE_2022_26923  [0.75, 0.75]
   2   CVE_2021_3156    [0.0, 0.1]

The conflict on ``CVE_2021_3156`` is detected and logged in the rule trace.
The other two CVEs retain their precise scores.

**Vulnerable / patched (Demo 2):**

.. code-block:: text

   TIMESTEP 0:
          component   vulnerable      patched
   0  workstation_1  [0.8, 1.0]  [0.0, 0.2]
   1     dev_server  [0.8, 1.0]  [0.0, 0.2]
   2     web_server  [0.0, 1.0]  [0.0, 1.0]

``web_server`` resolves to complete uncertainty on both predicates due to the
IPL conflict. The other two assets show normal IPL behaviour -- setting
``vulnerable:[0.8, 1.0]`` automatically forces ``patched`` to ``[0.0, 0.2]``.

The full rule trace can be saved for inspection:

.. code-block:: python

   node_trace, edge_trace = pr.get_rule_trace(interpretation)
   pr.save_rule_trace(interpretation)
