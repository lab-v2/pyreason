import pandas as pd

import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


class Filter:
    def __init__(self, tmax):
        self.tmax = tmax 

    def filter_by_bound(self, interpretation, label, bound):
        # Make use of rule trace in interpretation object to efficiently filter through data.
        # NOTE: if bound is [0,1] then we won't be able to display all nodes/edge labels that have not been changed

        # Initialize nested dict
        df = {}
        nodes = []
        for t in range(self.tmax+1):
            df[t] = {}
            nodes.append({'component':[], label:[]})

        # change contains the timestep, fp operation, component, label and interval
        for change in interpretation.rule_trace_node:
            t, fp, comp, l, bnd, qn, qe = change
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

    def filter_and_sort(self, interpretation, label, bound, sort_by='lower', descending=True):
        # Make use of rule trace in interpretation object to efficiently filter through data.
        
        # Initialize nested dict
        df = {}
        nodes = []
        for t in range(self.tmax+1):
            df[t] = {}
            nodes.append({'component':[], label:[]})

        # Create a list that needs to be sorted.
        list_to_be_sorted = []
        # change contains the timestep, fp operation, component, label and interval
        # for change in interpretation.rule_trace_node:
        for change in interpretation.rule_trace_node:
            t, fp, comp, l, bnd, qn, qe = change
            list_to_be_sorted.append((bnd, t, comp, l))

        # Sort the list
        reverse = True if descending else False
        if sort_by=='lower':
            list_to_be_sorted.sort(key=lambda x: x[0].lower, reverse=reverse)
        elif sort_by=='upper':
            list_to_be_sorted.sort(key=lambda x: x[0].upper, reverse=reverse)

        # Add sorted elements to df
        for i in list_to_be_sorted:
            bnd, t, comp, l = i
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
