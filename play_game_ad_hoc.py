import pyreason as pr
import time
import tracemalloc
import pandas as pd

soldiers_per_team = [1]
actions_per_soldier = [5]

pr.settings.verbose = True
pr.settings.atom_trace = True
pr.settings.memory_profile = False
pr.settings.canonical = True
pr.settings.inconsistency_check = False
pr.settings.static_graph_facts = False
pr.settings.resolution_levels = 3
pr.settings.step_size = 1
pr.settings.ad_hoc_grounding = True
# pr.settings.output_to_file = True
pr.settings.store_interpretation_changes = True
pr.settings.save_graph_attributes_to_trace = True
# pr.settings.output_file_name = f'out/scenario-ad-hoc-multi-agent/ad_hoc_multi_agent_{num_agents}'

d = {'TIME': [], 'MEMORY': []}

for i in soldiers_per_team:
    for j in actions_per_soldier:
        pr.reset()
        pr.load_graphml('pyreason/examples/adhoc-game-demo/game_graph_ad_hoc_low_res_multi_agent_1.graphml')
        pr.add_rules_from_file('pyreason/examples/adhoc-game-demo/rules.txt', infer_edges=True)
        # facts_node = []
        #

        # interpretation = pr.reason(again=False)
        # next_time = interpretation.time + 1
        #
        # facts_node.append(pr.fact_node.Fact('red_1_moveDown_fact_1', 'red-soldier-1', pr.label.Label('moveDown'), pr.interval.closed(1,1), next_time, next_time))
        # facts_node.append(pr.fact_node.Fact('red_1_moveDownOff_fact_1', 'red-soldier-1', pr.label.Label('moveDown'),
        #                                     pr.interval.closed(0,0), next_time+1, next_time+1))
        #
        # interpretation = pr.reason(again=True, node_facts=facts_node)
        # # print(interpretation.interpretations_edge)
        # # print(interpretation.interpretations_node)
        # print('========================================================')
        # next_time = interpretation.time + 1
        # # facts_node = []
        # # facts_node.append(pr.fact_node.Fact('red_1_moveDown_fact_2', 'red-soldier-1', pr.label.Label('moveDown'),
        # #                                     pr.interval.closed(1, 1), next_time, next_time))
        # # facts_node.append(pr.fact_node.Fact('red_1_moveDownOff_fact_2', 'red-soldier-1', pr.label.Label('moveDown'),
        # #                                     pr.interval.closed(0, 0), next_time + 1, next_time + 1))
        # #
        # # interpretation = pr.reason(again=True, node_facts=facts_node)
        # # print(interpretation.interpretations_edge)
        # # print(interpretation.interpretations_node)
        # pr.add_fact(pr.Fact('red_1_moveDown_fact_1', 'red-soldier-1', 'moveDown', [1, 1], 1, 1, static=False))
        # pr.add_fact(pr.Fact('red_1_moveDownOff_fact_1', 'red-soldier-1', 'moveDown', [0,0], 2, 2, static=False))
        #
        # pr.add_fact(pr.Fact('red_1_moveDown_fact_2', 'red-soldier-1', 'moveDown', [1, 1], 2, 2, static=False))
        # pr.add_fact(pr.Fact('red_1_moveDownOff_fact_2', 'red-soldier-1', 'moveDown', [0, 0], 3, 3, static=False))

        # pr.add_fact(pr.Fact('red_1_moveUp_fact_3', 'red-soldier-1', 'moveUp', [1, 1], 3, 3, static=False))
        # pr.add_fact(pr.Fact('red_1_moveUpOff_fact_3', 'red-soldier-1', 'moveUp', [0, 0], 4, 4, static=False))
        #
        # pr.add_fact(pr.Fact('red_1_moveDown_fact_4', 'red-soldier-1', 'moveDown', [1, 1], 4,4, static=False))
        # pr.add_fact(pr.Fact('red_1_moveDownOff_fact_4', 'red-soldier-1', 'moveDown', [0, 0], 5,5, static=False))
        #
        # pr.add_fact(pr.Fact('red_1_moveLeft_fact_5', 'red-soldier-1', 'moveLeft', [1, 1], 5,5, static=False))
        # pr.add_fact(pr.Fact('red_1_moveLeftOff_fact_5', 'red-soldier-1', 'moveLeft', [0, 0], 6,6, static=False))
        #
        pr.add_fact(pr.Fact('blue_1_moveDown_fact_1', 'blue-soldier-1', 'moveDown', [1, 1], 1, 1, static=False))
        pr.add_fact(pr.Fact('blue_1_moveDownOff_fact_1', 'blue-soldier-1', 'moveDown', [0, 0], 2, 2, static=False))
        #
        pr.add_fact(pr.Fact('blue_1_moveRight_fact_2', 'blue-soldier-1', 'moveRight', [1, 1], 2, 2, static=False))
        pr.add_fact(pr.Fact('blue_1_moveRightOff_fact_2', 'blue-soldier-1', 'moveRight', [0, 0], 3,3, static=False))
        pr.add_fact(pr.Fact('blue_1_moveRight_fact_3', 'blue-soldier-1', 'moveRight', [1, 1], 3, 3, static=False))
        pr.add_fact(pr.Fact('blue_1_moveRightOff_fact_3', 'blue-soldier-1', 'moveRight', [0, 0], 4, 4, static=False))

        #
        # pr.add_fact(pr.Fact('blue_1_moveLeft_fact_3', 'blue-soldier-1', 'moveLeft', [1, 1], 3,3, static=False))
        # pr.add_fact(pr.Fact('blue_1_moveLeftOff_fact_3', 'blue-soldier-1', 'moveLeft', [0, 0], 4,4, static=False))
        #
        # pr.add_fact(pr.Fact('blue_1_moveDUp_fact_4', 'blue-soldier-1', 'moveUp', [1, 1], 4,4, static=False))
        # pr.add_fact(pr.Fact('blue_1_moveUpOff_fact_4', 'blue-soldier-1', 'moveUp', [0, 0], 5,5, static=False))
        #
        # pr.add_fact(pr.Fact('blue_1_moveLeft_fact_5', 'blue-soldier-1', 'moveLeft', [1, 1], 5, 5, static=False))
        # pr.add_fact(pr.Fact('blue_1_moveLeftOff_fact_5', 'blue-soldier-1', 'moveLeft', [0, 0], 6,6, static=False))


        print(f'{i} Soldiers {j} actions')
        # start = time.time()
        # tracemalloc.start()
        interpretation = pr.reason()
        print(interpretation.interpretations_edge)
        print(interpretation.interpretations_node)
        # t = round(time.time()-start, 3)
        # mem = round(tracemalloc.get_traced_memory()[1]/(10**6), 3)
        # tracemalloc.stop()
        #
        # print('TIME:', t)
        # print('MEMORY:', mem)
        # d['TIME'].append(t)
        # d['MEMORY'].append(mem)
        # print()

#         dataframes = pr.filter_and_sort_edges(interpretation, ['atLoc'])
#         for t, df in enumerate(dataframes):
#             print(f'TIMESTEP - {t}')
#             print(df)
#             print()
#         dataframes = pr.filter_and_sort_nodes(interpretation, ['moveDown'])
#         for t, df in enumerate(dataframes):
#             print(f'TIMESTEP - {t}')
#             print(df)
#             print()
#
# df = pd.DataFrame(d)
# df.to_csv('profile.csv')
