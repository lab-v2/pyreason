'''
Visualizing graphs with Networkx
Author: Kaustuv Mukherji
Initially written: 09-27-2022
Last updated: 12-04-2022
'''

import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from textwrap import wrap

def get_subgraph(whole_graph, node_list):
    return nx.subgraph(whole_graph, node_list)

def make_visuals(graph_data, nodelist):
    pos_g=nx.kamada_kawai_layout(graph_data)
    plt.figure()
    color_map = []
    for node in list(graph_data.nodes):
        if node in nodelist:
            color_map.append('red')
        else:
            color_map.append('green')
    labels_g=nx.get_node_attributes(graph_data, "name")
    nx.draw(graph_data, pos=pos_g, node_color=color_map, node_size=100, font_size=10, font_color='DarkBlue', with_labels=True, labels=labels_g)