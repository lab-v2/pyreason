import pandas as pd


class Filter:

    def filter_by_bound(self, dataframe, label, bound):
        filtered_df = dataframe.loc[(dataframe[label] <= bound) & (dataframe[label] >= bound)]
        return filtered_df
