import pyreason as pr
import networkx as nx
import matplotlib.pyplot as plt

# Create a directed graph
G = nx.DiGraph()

# Add nodes with attributes
nodes = [
    ("Amsterdam_Airport_Schiphol", {"Amsterdam_Airport_Schiphol": 1}),
    ("Riga_International_Airport", {"Riga_International_Airport": 1}),
    ("Chișinău_International_Airport", {"Chișinău_International_Airport": 1}),
    ("Yali", {"Yali": 1}),
    ("Düsseldorf_Airport", {"Düsseldorf_Airport": 1}),
    ("Pobedilovo_Airport", {"Pobedilovo_Airport": 1}),
    ("Dubrovnik_Airport", {"Dubrovnik_Airport": 1}),
    ("Hévíz-Balaton_Airport", {"Hévíz-Balaton_Airport": 1}),
    ("Athens_International_Airport", {"Athens_International_Airport": 1}),
    ("Vnukovo_International_Airport", {"Vnukovo_International_Airport": 1})
]

G.add_nodes_from(nodes)

# Add edges with 'isConnectedTo' attribute
edges = [
    ("Pobedilovo_Airport", "Vnukovo_International_Airport", {"isConnectedTo": 1}),
    ("Vnukovo_International_Airport", "Hévíz-Balaton_Airport", {"isConnectedTo": 1}),
    ("Düsseldorf_Airport", "Dubrovnik_Airport", {"isConnectedTo": 1}),
    ("Dubrovnik_Airport", "Athens_International_Airport", {"isConnectedTo": 1}),
    ("Riga_International_Airport", "Amsterdam_Airport_Schiphol", {"isConnectedTo": 1}),
    ("Riga_International_Airport", "Düsseldorf_Airport", {"isConnectedTo": 1}),
    ("Chișinău_International_Airport", "Riga_International_Airport", {"isConnectedTo": 1}),
    ("Amsterdam_Airport_Schiphol", "Yali", {"isConnectedTo": 1}),
]

G.add_edges_from(edges)



pr.reset()
pr.reset_rules()
# Modify pyreason settings to make verbose and to save the rule trace to a file
pr.settings.verbose = True
pr.settings.atom_trace = True
pr.settings.memory_profile = False
pr.settings.canonical = True
pr.settings.inconsistency_check = False
pr.settings.static_graph_facts = False
pr.settings.output_to_file = False
pr.settings.store_interpretation_changes = True
pr.settings.save_graph_attributes_to_trace = True
# Load all the files into pyreason
pr.load_graph(G)
pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

# Run the program for two timesteps to see the diffusion take place
interpretation = pr.reason(timesteps=1)
#pr.save_rule_trace(interpretation)

# Display the changes in the interpretation for each timestep
dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
for t, df in enumerate(dataframes):
    print(f'TIMESTEP - {t}')
    print(df)
    print()
assert len(dataframes) == 2, 'Pyreason should run exactly 2 fixpoint operations'
assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
assert ('Vnukovo_International_Airport', 'Riga_International_Airport') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Riga_International_Airport) should have isConnectedTo bounds [1,1] for t=1 timesteps'
