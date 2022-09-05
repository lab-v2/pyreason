import pickle

class Output:
    def __init__(self, timesteps):
        self.timesteps = timesteps

    def write(self, interpretation):
        # Save nodes dataframe
        for t in range(0, len(interpretation.interpretations_node)):
            rows = []
            for node, world in interpretation.interpretations_node[t].items():
                w = world.get_world()
                df_row = {str(x):w[x] for x in w.keys()}
                df_row['component'] = str(node)
                rows.append(df_row)

            with open(f'./output/nodes_timestep_{t}.pkl', 'wb') as file:
                pickle.dump(rows, file)

        # Save edges to dataframe
        for t in range(0, len(interpretation.interpretations_edge)):
            rows = []
            for edge, world in interpretation.interpretations_edge[t].items():
                w = world.get_world()
                df_row = {str(x):w[x] for x in w.keys()}
                df_row['component'] = str(edge)
                rows.append(df_row)

            with open(f'./output/edges_timestep_{t}.pkl', 'wb') as file:
                pickle.dump(rows, file)

            

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
