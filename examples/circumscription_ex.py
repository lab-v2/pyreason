import pyreason as pr
import networkx as nx
from pprint import pprint

pr.reset()
pr.reset_rules()

g = nx.DiGraph()

g.add_nodes_from(['cb_1', 'cb_2', 'l1', 'l2'])
g.add_edge('cb_1', 'cb_2', stepFrom =1)
g.add_edge('cb_1',  'l1', hasLabel = 1)
g.add_edge('cb_2',  'l2', hasLabel = 1)
#g.add_edge('l1','l2', cond=1) # Adding this edge will 

pr.settings.verbose = True
pr.settings.atom_trace = True
pr.settings.inconsistency_check = True

pr.load_graph(g)

pr.add_minimized_predicate('hackerControl')
pr.add_fact(pr.Fact('stepFrom(cb_1, cb_2)', 'step_from_fact', 0, 1))
pr.add_fact(pr.Fact('hackerControl(cb_1)', 'hacker_control_initial_fact'))
pr.add_rule(pr.Rule('future(Y) <-1 stepFrom(X,Y), hackerControl(X)'))
pr.add_rule(pr.Rule('hackerControl(Y) <-1 hackerControl(X), hasLabel(X,L1), hasLabel(Y,L2), cond(L1, L2), stepFrom(X,Y)', 'hacker-control-rule'))
pr.add_rule(pr.Rule('hackerControl(Y) <-1 hackerControl(X), hasLabel(X,L1), hasLabel(Y,L2), cond_1(L1, L2), stepFrom(X,Y)', 'hacker-control-rule-1'))
pr.add_rule(pr.Rule('inconsistent(Y) <- future(Y), ~hackerControl(Y), ~hackerControl(X)', 'inconsistent_rule'))


interpretation = pr.reason(timesteps=2)
interp_dict = interpretation.get_dict()

pprint(interp_dict)

# Filter and sort nodes based on hackerControl
dataframes = pr.filter_and_sort_nodes(interpretation, ['hackerControl'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

# Filter and sort edges based on inconsistent
edge_dataframes = pr.filter_and_sort_nodes(interpretation, ['inconsistent'])
for t, df in enumerate(edge_dataframes):
    print(f'TIMESTEP - {t} (inconsistent nodes)')
    print(df)
    print()
