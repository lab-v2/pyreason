# Test if the simple hello world program works
import pyreason as pr
import faulthandler
import networkx as nx
from typing import Tuple
from pprint import pprint



# Reset PyReason
pr.reset()
pr.reset_rules()
pr.reset_settings()


# ================================ CREATE GRAPH====================================
# Create a Directed graph
g = nx.DiGraph()

# Add the nodes
g.add_nodes_from(['John', 'Mary', 'Justin'])
g.add_nodes_from(['Dog', 'Cat'])

# Add the edges and their attributes. When an attribute = x which is <= 1, the annotation
# associated with it will be [x,1]. NOTE: These attributes are immutable
# Friend edges
g.add_edge('Justin', 'Mary', Friends=1)
g.add_edge('John', 'Mary', Friends=1)
g.add_edge('John', 'Justin', Friends=1)

# Pet edges
g.add_edge('Mary', 'Cat', owns=1)
g.add_edge('Justin', 'Cat', owns=1)
g.add_edge('Justin', 'Dog', owns=1)
g.add_edge('John', 'Dog', owns=1)


# Modify pyreason settings to make verbose
pr.settings.verbose = True     # Print info to screen
# pr.settings.optimize_rules = False  # Disable rule optimization for debugging

# Load all the files into pyreason
pr.load_graph(g)
pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

# Run the program for two timesteps to see the diffusion take place
faulthandler.enable()
interpretation = pr.reason(timesteps=2)
pr.save_rule_trace(interpretation)

interpretations_dict = interpretation.get_dict()
print("stra")
pprint(interpretations_dict)
print("end")
#Display the changes in the interpretation for each timestep
dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()



assert len(dataframes[0]) == 1, 'At t=0 there should be one popular person'
assert len(dataframes[1]) == 2, 'At t=1 there should be two popular people'
assert len(dataframes[2]) == 3, 'At t=2 there should be three popular people'

# Mary should be popular in all three timesteps
assert 'Mary' in dataframes[0]['component'].values and dataframes[0].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
assert 'Mary' in dataframes[1]['component'].values and dataframes[1].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
assert 'Mary' in dataframes[2]['component'].values and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

# Justin should be popular in timesteps 1, 2
assert 'Justin' in dataframes[1]['component'].values and dataframes[1].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
assert 'Justin' in dataframes[2]['component'].values and dataframes[2].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

# John should be popular in timestep 3
assert 'John' in dataframes[2]['component'].values and dataframes[2].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'
