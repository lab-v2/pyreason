from pyreason.pyreason import *
import os

# Set numba environment variable

package_path = os.path.abspath(os.path.dirname(pyreason.__file__))
cache_path = os.path.join(package_path, 'cache')
os.environ['NUMBA_CACHE_DIR'] =  cache_path
if not os.path.exists(cache_path):
    print('Imported PyReason for the first time. Initializing ... this will take a minute')
    graph_path = os.path.join(package_path, 'examples', 'hello-world', 'friends.graphml')
    labels_path = os.path.join(package_path, 'examples', 'hello-world', 'labels.yaml')
    facts_path = os.path.join(package_path, 'examples', 'hello-world', 'facts.yaml')
    rules_path = os.path.join(package_path, 'examples', 'hello-world', 'rules.yaml')
    ipl_path = os.path.join(package_path, 'examples', 'hello-world', 'ipl.yaml')

    settings.verbose = False
    load_graph(graph_path)
    load_labels(labels_path)
    load_facts(facts_path)
    load_rules(rules_path)
    load_inconsistent_predicate_list(ipl_path)
    reason(timesteps=2)
