import pyreason as pr
import networkx as nx

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

# ================================= RUN PYREASON ====================================

# Modify pyreason settings to make verbose and to save the rule trace to a file
pr.settings.verbose = True     # Print info to screen
pr.settings.atom_trace = True  # This allows us to view all the atoms that have made a certain rule fire


# Load all rules and the graph into pyreason
# Someone is "popular" if they have a friend who is popular and they both own the same pet
pr.load_graph(g)
pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
pr.add_fact(pr.Fact('popular-fact', 'Mary', 'popular', [1, 1], 0, 2))


# Run the program for two timesteps to see the diffusion take place
interpretation = pr.reason(timesteps=2)

# Display the changes in the interpretation for each timestep
dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

# Save all changes made to the interpretations a file
pr.save_rule_trace(interpretation)

# Get all interpretations in a dictionary
interpretations_dict = interpretation.get_interpretation_dict()

