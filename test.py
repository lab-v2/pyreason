import os
from pyreason.pyreason import load_graph, plot_graph, \
    load_labels, load_facts, load_rules, load_inconsistent_predicate_list, reason

package_path = os.path.abspath(os.path.dirname(__file__))
hello_world_path = os.path.join(package_path, 'pyreason/examples', 'hello-world')
graph_path = os.path.join(hello_world_path, 'friends.graphml')
labels_path = os.path.join(hello_world_path, 'labels.yaml')
facts_path = os.path.join(hello_world_path, 'facts.yaml')
rules_path = os.path.join(hello_world_path, 'rules.yaml')
ipl_path = os.path.join(hello_world_path, 'ipl.yaml')

load_graph(path=graph_path)
plot_graph()

# load_labels(path=labels_path)
# load_facts(path=facts_path)
# load_rules(path=rules_path)
# load_inconsistent_predicate_list(path=ipl_path)
# reason(timesteps=2)
