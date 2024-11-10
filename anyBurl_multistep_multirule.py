'''
Run pyreason for multiple timesteps for given number of rules

'''
import tracemalloc
import os
import time
import argparse
# import datetime
import importlib.metadata
import pyreason as pr


# Initialize parser
parser = argparse.ArgumentParser()
 
# Adding optional argument
parser.add_argument("-s", "--startrule", help = "Provide rule to start running from.")
parser.add_argument("-e", "--endrule", help = "Provide rule to end running from.")
parser.add_argument("-ts", "--timesteps", help = "Provide number of timesteps to reason for.")
parser.add_argument("-rf", "--rulefile", help = "Provide rule file containing all rules.")
parser.add_argument("-g", "--graph", help = "Provide graphml file to reason on.")
 
# Read arguments from command line
args = parser.parse_args()
 
if args.startrule:
    START_COUNT = int(args.startrule)
else:
    START_COUNT = 1

if args.endrule:
    END_COUNT = int(args.endrule)
else:
    END_COUNT = 1

if args.timesteps:
    TIMESTEPS = int(args.timesteps)
else:
    TIMESTEPS = 1

if args.rulefile:
    RULEFILE = str(args.rulefile)
else:
    RULEFILE = 'yago_1200_9_100_16ann_new' #Has 1775 rules

if args.graph:
    GRAPH = str(args.graph)
else:
    GRAPH = 'anyBurl_graphs/YAGO3-10/knowledge_graph_train.graphml'

# print(START_COUNT)
# print(END_COUNT)
# print(TIMESTEPS)

# All the rules are stored here
input_file = RULEFILE
# When the code is run
timestr = time.strftime("%Y%m%d-%H%M%S")
# Initializing log file
log_dir = "anyBurl_logs/"
log_file = log_dir + input_file + '_' + str(START_COUNT) + '_' + str(END_COUNT) + '_' + timestr + '.txt'

def write_to_log(to_write):
    global log_file
    with open(log_file, 'a+') as output_file:
        output_file.write("{}\n".format(to_write))

# write_to_log('Importing pyreason now...')
# start = time.time()
# tracemalloc.start()

# t = round(time.time()-start, 3)
# mem = round(tracemalloc.get_traced_memory()[1]/(10**6), 3)
# tracemalloc.stop()
# write_to_log('Pyreason import done!')
# write_to_log(f'Time:{t} sec, Memory:{mem} MB.')

def run_pyreason(train_graphml_file='', subset_rules_file=''):
    # write_to_log('Using pyreason {} '.format(importlib.metadata.version('pyreason')))
    # write_to_log('Rule count: {}'.format(rule_count))
    # start_time = time.time()
    # tracemalloc.start()
    # Pyreason settings and reset rules.
    pr.reset()
    pr.reset_rules()

    pr.settings.verbose = True
    pr.settings.atom_trace = False
    pr.settings.memory_profile = False
    pr.settings.canonical = False
    pr.settings.inconsistency_check = True
    pr.settings.static_graph_facts = True
    pr.settings.output_to_file = False
    pr.settings.store_interpretation_changes = True
    pr.settings.save_graph_attributes_to_trace = False
    pr.settings.parallel_computing = False
    pr.settings.use_gpu = True
    # pr.settings.parallel_computing = False

    # write_to_log('parallel_computing: {}'.format(pr.settings.parallel_computing))


    # Load all the files into pyreason
    pr.load_graphml(train_graphml_file)
    pr.add_rules_from_file(subset_rules_file, infer_edges=True)
    # pr.add_rule(pr.Rule('playsFor(X,x_0):[0.95822454308094,1] <-1 isAffiliatedTo(X,x_0):[0.1,1], Southend_United_F.C.(x_0)', 'x_rule', infer_edges = True))

    # end_time = time.time()
    # mem = round(tracemalloc.get_traced_memory()[1]/(10**6), 3)
    # tracemalloc.stop()
    # graph_time = end_time - start_time
    # write_to_log(f"Preparation time: {round(graph_time,2)} sec; Preparation memory: {mem} MB.")

    # write_to_log('Starting inference...')
    start_time = time.time()  # Assuming you have imported the time module
    tracemalloc.start()
    interpretation = pr.reason(timesteps=TIMESTEPS)
    end_time = time.time()
    reason_time = end_time - start_time
    mem = round(tracemalloc.get_traced_memory()[1]/(10**6), 3)
    tracemalloc.stop()
    write_to_log(f"Reasoning time: {round(reason_time/60,2)} min, Reasoning memory: {mem} MB.")
    trace_dir = "anyBurl_traces/"
    global input_file
    global timestr
    run_dir = input_file + '_' + str(START_COUNT) + '_' + str(END_COUNT) + '_' + timestr
    anyBurl_rule_trace_directory = trace_dir + run_dir

    # Save rule traces
    if not os.path.exists(anyBurl_rule_trace_directory):
        # Create the directory if it doesn't exist
        os.makedirs(anyBurl_rule_trace_directory)
    # start_time = time.time()
    # tracemalloc.start()
    pr.save_rule_trace(interpretation, f'{anyBurl_rule_trace_directory}')
    # end_time = time.time()
    # trace_save_time = end_time - start_time
    # mem = round(tracemalloc.get_traced_memory()[1]/(10**6), 3)
    # tracemalloc.stop()


    return True

def main():
    inp_ext = '.txt'
    rules_dir = 'anyBurl_rules/'
    global input_file
    global timestr
    all_rules_file = rules_dir + input_file + inp_ext

    # training graph
    input_train_graph = GRAPH
    output_dir = "anyburl_subrules/"

    output_rules_file = output_dir + 'subrule_' + input_file + '_' + str(START_COUNT) + '_' + str(END_COUNT) + '_' + timestr + '.txt'
    write_to_log("Output file={}".format(output_rules_file))
    # Open the rules file
    with open(all_rules_file, 'r') as rules_file:
        # Iterate over each rule
        for i, rule in enumerate(rules_file):
            if ((i >= START_COUNT-1) and (i < END_COUNT)):
                with open(output_rules_file, 'a+') as output_file:
                    output_file.write(rule)
            elif i >= END_COUNT:
                break

    # write_to_log("Running PyReason now...")
    # Run pyreason with i/p graph, rule_file, rule number used as i/p to the function
    write_to_log('Rules: {} to {}, Rule count: {}'.format(START_COUNT, END_COUNT, (END_COUNT - START_COUNT + 1) ))
    # print('Rules: {} to {}, Rule count: {}'.format(START_COUNT, END_COUNT, (END_COUNT - START_COUNT + 1) ))
    pyreason_ran = run_pyreason(train_graphml_file=input_train_graph, subset_rules_file=output_rules_file)
    if pyreason_ran:
        write_to_log("Success!")

if __name__ == "__main__":
    main()

