import pickle
import pandas as pd


class Output:

    def write(self, interpretation):
        # For each timestep create a dataframe with graph component -> bounds
        dfs_nodes = []
        dfs_edges = []
        columns_nodes = ['component']
        columns_edges = ['component']
        for t in range(0, len(interpretation.interpretations_node)):
            data_nodes = []
            data_edges = []
            for i, c in enumerate(interpretation.interpretations_node[t].keys()):
                world = interpretation.interpretations_node[t][c].get_world()
                if c.get_type() == 'node':
                    data_nodes.append([str(c)])
                    for atom in world:
                        data_nodes[i].append(atom[1])
                        if atom[0] not in columns_nodes:
                            columns_nodes.append(atom[0])
                elif c.get_type() == 'edge':
                    data_edges.append([str(c)])
                    for atom in world:
                        data_edges[i].append(atom[1])
                        if atom[0] not in columns_edges:
                            columns_edges.append(atom[0])
            dfs_nodes.append(pd.DataFrame(data_nodes, columns=columns_nodes))
            dfs_edges.append(pd.DataFrame(data_edges, columns=columns_edges))

        # Save list of dataframes for both nodes and edges
        with open('./output/nodes.pkl', 'wb') as file:
            pickle.dump(dfs_nodes, file)
        with open('./output/edges.pkl', 'wb') as file:
            pickle.dump(dfs_edges, file)


        # with open(path+'nodes.pkl', 'rb') as file:
        #     nodes = pickle.load(file)
        #     print(type(nodes[0]))
    def read(self, component_type):
        if component_type == 'nodes':
            with open('./output/nodes.pkl', 'rb') as file:
                return pickle.load(file)
        elif component_type == 'edges':
            with open('./output/edges.pkl', 'rb') as file:
                return pickle.load(file)
