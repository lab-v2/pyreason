# Test if the simple hello world program works
import pyreason as pr
import faulthandler
import tracemalloc
import os
import time
timestr = time.strftime("%Y%m%d-%H%M%S")
# Initializing log file
log_dir = "synthetic_logs/"
log_file = log_dir + 'synthetic_graph' + '_' + timestr + '.txt'
def write_to_log(to_write):
    global log_file
    with open(log_file, 'a+') as output_file:
        output_file.write("{}\n".format(to_write))
def hello_world():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = 'synthetic_graphs/gpu_graph_3_6.graphml'


    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    pr.settings.use_gpu = False
    # pr.settings.optimize_rules = False  # Disable rule optimization for debugging

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    # pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_rule(pr.Rule('head(X) <-1 attr1(X,Y)', 'popular_rule', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    start_time = time.time()  # Assuming you have imported the time module
    tracemalloc.start()
    interpretation = pr.reason(timesteps=2)
    end_time = time.time()
    reason_time = end_time - start_time
    mem = round(tracemalloc.get_traced_memory()[1] / (10 ** 6), 3)
    tracemalloc.stop()
    write_to_log(f"Reasoning time: {round(reason_time / 60, 2)} min, Reasoning memory: {mem} MB.")

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['head'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()


hello_world()
