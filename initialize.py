# Run this script after cloning repository to generate the numba caches. This script runs the hello-world program internally
import pyreason as pr
import os
import yaml

print('Initializing PyReason caches')

graph_path = os.path.join('pyreason', 'examples', 'hello-world', 'friends.graphml')
labels_path = os.path.join('pyreason', 'examples', 'hello-world', 'labels.yaml')
facts_path = os.path.join('pyreason', 'examples', 'hello-world', 'facts.yaml')
rules_path = os.path.join('pyreason', 'examples', 'hello-world', 'rules.yaml')
ipl_path = os.path.join('pyreason', 'examples', 'hello-world', 'ipl.yaml')

pr.settings.verbose = False
pr.load_graph(graph_path)
pr.load_labels(labels_path)
pr.load_facts(facts_path)
pr.load_rules(rules_path)
pr.load_inconsistent_predicate_list(ipl_path)
pr.reason(timesteps=2)

cache_status_path = './pyreason/.cache_status.yaml'
with open(cache_status_path) as file:
    cache_status = yaml.safe_load(file)

with open(cache_status_path, 'w') as file:
    cache_status['initialized'] = True
    yaml.dump(cache_status, file)
    