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
# Immediate rule (delta_t=0): popularity spreads to friends who share a pet,
# and the whole cascade resolves within a single timestep via the fixpoint.
pr.add_rule(pr.Rule('popular(x) <- popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 0))

# Run the program for a single timestep (t=0) to see the full diffusion take place
faulthandler.enable()
interpretation = pr.reason(timesteps=0)
pr.save_rule_trace(interpretation)

interpretations_dict = interpretation.get_dict()
print("start")
pprint(interpretations_dict)
print("end")

# Display the interpretation at timestep 0
dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
df = dataframes[0]
print('TIMESTEP - 0')
print(df)
print()

assert len(dataframes) == 1, 'There should only be one timestep (t=0)'
