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
#g.add_edge('l1','l2', cond=1) # Adding this edge will satisfy hackerControl(cb)

pr.settings.verbose = True
pr.settings.atom_trace = True
pr.settings.inconsistency_check = True

pr.load_graph(g)

# hackerControl is a closed-world pred, meaning that it will be grounded as [0,0] if its bounds are [0,1] (or if it is not in the interpretation dict)
pr.add_closed_world_predicate('hackerControl')

# Initial fact instantiation
pr.add_fact(pr.Fact('stepFrom(cb_1, cb_2)', 'step_from_fact', 0, 1))
pr.add_fact(pr.Fact('hackerControl(cb_1)', 'hacker_control_initial_fact', 0, 0))

# Future(Y) will fire for cb_2
pr.add_rule(pr.Rule('future(Y) <-1 stepFrom(X,Y), hackerControl(X)'))

#This rule will not fire for cb_2, as cond(cb_1, cb_2) is not grounded
pr.add_rule(pr.Rule('hackerControl(Y) <-1 hackerControl(X), hasLabel(X,L1), hasLabel(Y,L2), cond(L1, L2), stepFrom(X,Y)', 'hacker-control-rule'))

# At timestep 1, hackerControl(cb_1) and hackerControl(cb_2) have no associated bounds, so they are treated as [0,1].
# Because hackerControl is minimized, its bounds are gounded as [0,0].  Future(cb_2) has bounds [1,1], so inconsistent(cb_2) fires.
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
