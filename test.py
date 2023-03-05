import os
import pyreason as pr

package_path = os.path.abspath(os.path.dirname(__file__))
hello_world_path = os.path.join(package_path, 'pyreason/examples', 'hello-world')
graph_path = os.path.join(hello_world_path, 'friends.graphml')
labels_path = os.path.join(hello_world_path, 'labels.yaml')
facts_path = os.path.join(hello_world_path, 'facts.yaml')
rules_path = os.path.join(hello_world_path, 'rules.yaml')
ipl_path = os.path.join(hello_world_path, 'ipl.yaml')

pr.load_graph(path=graph_path)
pr.plot_graph()

pr.load_labels(path=labels_path)
pr.load_facts(path=facts_path)
pr.load_rules(path=rules_path)
pr.load_inconsistent_predicate_list(path=ipl_path)

pr.settings.verbose = True
interpretation = pr.reason(timesteps=30)
