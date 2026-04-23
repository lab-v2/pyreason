"""
Example: Cybersecurity Knowledge Graph with Inconsistency Detection
====================================================================
This example builds a small cybersecurity knowledge graph containing
network assets (servers and workstations), the software they run, and
real CVEs (Common Vulnerabilities and Exposures) from the National
Vulnerability Database (NVD) that affect that software.

CVSS scores are normalised to [0, 1] by dividing by 10 to serve as
PyReason annotation bounds.

Graph structure:
  [asset] --runs--> [software] --has_cve--> [CVE]

Two types of inconsistency are demonstrated:

  1. Same-predicate non-overlapping bounds (monotonic reasoning violation):
     Two data sources assert conflicting severity scores for the same CVE.
     The bounds do not overlap so PyReason resolves to [0.0, 1.0].

  2. Inconsistent Predicate List (IPL) conflict:
     "vulnerable" and "patched" are declared as mutually exclusive.
     Asserting both for the same asset creates a contradiction which
     PyReason resolves to [0.0, 1.0] on both predicates.

Real CVEs used:
  - CVE-2021-3156   sudo 1.9.5p1      CVSS 7.8  CWE-121 (heap buffer overflow)
  - CVE-2022-0185   Linux Kernel 5.1  CVSS 8.4  CWE-121 (stack overflow)
  - CVE-2022-26923  OpenSSL 3.0.1     CVSS 7.5  CWE-415 (double free)
"""

import pyreason as pr
import networkx as nx

# Reset PyReason to a clean state
pr.reset()
pr.reset_rules()

# ================================ CREATE GRAPH ================================
g = nx.DiGraph()

# Asset nodes -- servers and workstations in a small enterprise network
g.add_nodes_from(['web_server', 'workstation_1', 'dev_server'])

# Software nodes -- specific vulnerable versions
g.add_nodes_from(['sudo_1_9_5p1', 'linux_kernel_5_1', 'openssl_3_0_1'])

# CVE nodes -- real vulnerability identifiers from NVD
g.add_nodes_from(['CVE_2021_3156', 'CVE_2022_0185', 'CVE_2022_26923'])

# Asset --> Software edges (which asset runs which software version)
g.add_edge('web_server',    'sudo_1_9_5p1',     runs=1)
g.add_edge('workstation_1', 'linux_kernel_5_1', runs=1)
g.add_edge('dev_server',    'openssl_3_0_1',    runs=1)

# Software --> CVE edges (which CVE affects which software version)
g.add_edge('sudo_1_9_5p1',     'CVE_2021_3156',  has_cve=1)
g.add_edge('linux_kernel_5_1', 'CVE_2022_0185',  has_cve=1)
g.add_edge('openssl_3_0_1',    'CVE_2022_26923', has_cve=1)

# ================================ CONFIGURE ===================================
pr.settings.verbose = True
pr.settings.atom_trace = True        # Enable atom trace for full explainability
pr.settings.inconsistency_check = True  # Enable inconsistency detection (default)

# ================================ LOAD GRAPH ==================================
pr.load_graph(g)

# Declare vulnerable and patched as inconsistent predicates
# When vulnerable(x):[l,u] is set, PyReason automatically sets
# patched(x):[1-u, 1-l] -- and vice versa
pr.add_inconsistent_predicate('vulnerable', 'patched')

# ================================ ADD RULES ===================================
# Rule 1: If an asset runs software that has a CVE, the asset is at risk
# This is the core two-hop transitive inference: asset --> software --> CVE
pr.add_rule(pr.Rule(
    'at_risk(x) <- runs(x,y), has_cve(y,z)',
    'exposure_rule'
))

# Rule 2: An asset that is at risk is also vulnerable with high confidence
# This chains off exposure_rule and also triggers the IPL for patched
pr.add_rule(pr.Rule(
    'vulnerable(x):[0.8,1.0] <- at_risk(x)',
    'vulnerability_rule'
))

# ================================ ADD FACTS ===================================
# CVE severity scores from NVD, normalised to [0,1] by dividing by 10
# CVE-2021-3156:  CVSS 7.8 / 10 = 0.78
pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.78,0.78]',  'sudo_cve_severity',    0, 2))
# CVE-2022-0185:  CVSS 8.4 / 10 = 0.84
pr.add_fact(pr.Fact('severity(CVE_2022_0185):[0.84,0.84]',  'kernel_cve_severity',  0, 2))
# CVE-2022-26923: CVSS 7.5 / 10 = 0.75
pr.add_fact(pr.Fact('severity(CVE_2022_26923):[0.75,0.75]', 'openssl_cve_severity', 0, 2))

# ---- Inconsistency Demo 1: Monotonic reasoning violation ----
# Two data sources disagree on the severity of CVE_2021_3156
# [0.8, 1.0] and [0.0, 0.1] do not overlap -- PyReason flags the conflict
# and resolves severity(CVE_2021_3156) to [0.0, 1.0] (complete uncertainty)
pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.8,1.0]', 'severity_source_A', 0, 2))
pr.add_fact(pr.Fact('severity(CVE_2021_3156):[0.0,0.1]', 'severity_source_B', 0, 2))

# ---- Inconsistency Demo 2: Inconsistent Predicate List (IPL) conflict ----
# Asset management DB says web_server was patched -- high confidence
pr.add_fact(pr.Fact('patched(web_server):[0.9,1.0]',    'patch_db_fact',     0, 2))
# Vulnerability scanner says web_server is vulnerable -- also high confidence
# Since vulnerable and patched are in the IPL, this creates a contradiction
# PyReason resolves both to [0.0, 1.0] and logs the conflict in the trace
pr.add_fact(pr.Fact('vulnerable(web_server):[0.9,1.0]', 'vuln_scanner_fact', 0, 2))

# ================================ REASON ======================================
print('=' * 60)
print('Running PyReason -- Cybersecurity Knowledge Graph')
print('=' * 60)
interpretation = pr.reason(timesteps=2)

# ================================ VIEW RESULTS ================================
print('\n' + '=' * 60)
print('Assets at risk (inferred by exposure_rule)')
print('=' * 60)
dataframes = pr.filter_and_sort_nodes(interpretation, ['at_risk'])
for t, df in enumerate(dataframes):
    print(f'\nTIMESTEP {t}:')
    print(df)

print('\n' + '=' * 60)
print('CVE Severity (Demo 1: monotonic violation on CVE_2021_3156)')
print('=' * 60)
dataframes = pr.filter_and_sort_nodes(interpretation, ['severity'])
for t, df in enumerate(dataframes):
    print(f'\nTIMESTEP {t}:')
    print(df)

print('\n' + '=' * 60)
print('Vulnerable / Patched (Demo 2: IPL conflict on web_server)')
print('=' * 60)
dataframes = pr.filter_and_sort_nodes(interpretation, ['vulnerable', 'patched'])
for t, df in enumerate(dataframes):
    print(f'\nTIMESTEP {t}:')
    print(df)

# ================================ VIEW TRACE ==================================
print('\n' + '=' * 60)
print('Rule Trace (full explainability)')
print('=' * 60)
node_trace, edge_trace = pr.get_rule_trace(interpretation)
print('\nNode trace:')
print(node_trace.to_string())

if not edge_trace.empty:
    print('\nEdge trace:')
    print(edge_trace.to_string())

# Save the rule trace to CSV files for further inspection
pr.save_rule_trace(interpretation)
print('\nRule trace saved to current directory.')
