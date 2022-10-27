import pickle

class Output:
    def __init__(self, timesteps):
        self.timesteps = timesteps

    def pickle_output(self, interpretation, filename='pyreason_pickle'):
        pass
        

    def write(self, interpretation, pickle=False):
        # Save nodes dataframe
        df_nodes = []
        for t in range(0, len(interpretation.interpretations_node)):
            rows = []
            for node, world in interpretation.interpretations_node[t].items():
                w = world.get_world()
                df_row = {str(x):w[x] for x in w.keys()}
                df_row['component'] = str(node)
                rows.append(df_row)

            if pickle:
                with open(f'./output/nodes_timestep_{t}.pkl', 'wb') as file:
                    pickle.dump(rows, file)
            else:
                df_nodes.append(rows)

        # Save edges to dataframe
        df_edges = []
        for t in range(0, len(interpretation.interpretations_edge)):
            rows = []
            for edge, world in interpretation.interpretations_edge[t].items():
                w = world.get_world()
                df_row = {str(x):w[x] for x in w.keys()}
                df_row['component'] = str(edge)
                rows.append(df_row)

            if pickle:
                with open(f'./output/edges_timestep_{t}.pkl', 'wb') as file:
                    pickle.dump(rows, file)
            else:
                df_edges.append(rows)

        if not pickle:
            return df_nodes, df_edges


            

    def read(self, component_type):
        out = []
        if component_type == 'nodes':
            for t in range(self.timesteps+1):
                with open(f'./output/nodes_timestep_{t}.pkl', 'rb') as file:
                    out.append(pickle.load(file))
            return out
        elif component_type == 'edges':
            for t in range(self.timesteps+1):
                with open(f'./output/edges_timestep_{t}.pkl', 'rb') as file:
                    out.append(pickle.load(file))
            return out
