import pandas as pd

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


class Filter:
    def __init__(self, tmax):
        self.tmax = tmax

    def filter_df_by_bound(self, dataframe, label, bound, display_other_labels=False):
        # dataframe is a list of dictionaries mapping labels to bounds
        if display_other_labels:    
            columns = ['component', label, 'other labels']
        else:
             columns = ['component', label]
        df = pd.DataFrame(columns=columns)
        d = {}
        for row in dataframe:
            if label in row.keys() and row[label] in bound:
                d['component'] = row['component']
                d[label] = row[label]
                if display_other_labels:
                    d['other labels'] = {x:row[x] for x in row.keys() if (x!='component' and x!=label)}
                df.loc[len(df.index)] = d
        return df    

    def filter_interpretation_by_bound(self, interpretation, label, bound):
        # Make use of rule trace in interpretation object to efficiently filter through data.
        # NOTE: bound cannot be [0,1] because rule_trace contains only atoms that have changed in the diffusion process
        assert(bound!=interval.closed(0,1))

        # Initialize nested dict
        df = {}
        nodes = []
        for t in range(self.tmax+1):
            df[t] = {}
            nodes.append({'component':[], label:[]})

        # change contains the timestep, fp operation, component, label and interval
        for change in interpretation.rule_trace_node:
            t, fp, comp, l, bnd = change
            df[t][(comp, l)] = bnd

        for t, d in df.items():
            for (comp, l), bnd in d.items():
                if l.get_value()==label and bnd in bound:
                    nodes[t]['component'].append(comp)
                    nodes[t][label].append(bnd)

        dataframes = []
        for t in range(self.tmax+1):
            dataframes.append(pd.DataFrame.from_dict(nodes[t]))
        return dataframes

        

