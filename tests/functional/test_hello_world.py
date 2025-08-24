# Test if the simple hello world program works
#import pyreason as pr
import faulthandler
import json
import os
import subprocess
import sys
import textwrap

import pyreason.pyreason as pr


def test_hello_world():
    # Reset PyReason
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Modify pyreason settings to make verbose
    pr.settings.verbose = True     # Print info to screen
    # pr.settings.optimize_rules = False  # Disable rule optimization for debugging

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    faulthandler.enable()
    interpretation = pr.reason(timesteps=2)
    print("Reasoning")

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes[0]) == 1, 'At t=0 there should be one popular person'
    assert len(dataframes[1]) == 2, 'At t=1 there should be two popular people'
    assert len(dataframes[2]) == 3, 'At t=2 there should be three popular people'

    # Mary should be popular in all three timesteps
    assert 'Mary' in dataframes[0]['component'].values and dataframes[0].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
    assert 'Mary' in dataframes[1]['component'].values and dataframes[1].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
    assert 'Mary' in dataframes[2]['component'].values and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

    # Justin should be popular in timesteps 1, 2
    assert 'Justin' in dataframes[1]['component'].values and dataframes[1].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
    assert 'Justin' in dataframes[2]['component'].values and dataframes[2].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

    # John should be popular in timestep 3
    assert 'John' in dataframes[2]['component'].values and dataframes[2].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'


def test_hello_world_consistency():
    """Ensure hello world output matches with and without JIT."""
    script = textwrap.dedent(
        """
import json
import pyreason.pyreason as pr
pr.reset(); pr.reset_rules(); pr.reset_settings()
pr.settings.verbose = False
pr.load_graphml('./tests/functional/friends_graph.graphml')
pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))
interpretation = pr.reason(timesteps=2)
dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
res = [df[['component','popular']].to_dict('records') for df in dataframes]
print(json.dumps(res))
"""
    )
    env = os.environ.copy()
    jit_run = subprocess.run([
        sys.executable,
        "-c",
        script,
    ], capture_output=True, text=True, check=True, env=env)
    jit_res = json.loads(jit_run.stdout)
    env["NUMBA_DISABLE_JIT"] = "1"
    py_run = subprocess.run([
        sys.executable,
        "-c",
        script,
    ], capture_output=True, text=True, check=True, env=env)
    py_res = json.loads(py_run.stdout)
    assert jit_res == py_res
