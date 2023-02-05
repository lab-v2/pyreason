# Set numba environment variable
import os
package_path = os.path.abspath(os.path.dirname(__file__))
cache_path = os.path.join(package_path, 'cache')
cache_status_path = os.path.join(package_path, '.cache_status.yaml')
os.environ['NUMBA_CACHE_DIR'] =  cache_path

from pyreason.pyreason import *
import yaml


with open(cache_status_path) as file:
    cache_status = yaml.safe_load(file)

if not cache_status['initialized']:
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

    # Update cache status
    cache_status['initialized'] = True
    with open(cache_status_path, 'w') as file:
        yaml.dump(cache_status, file)
