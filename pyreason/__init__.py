# ruff: noqa: F403 F405 (Ignore Pyreason import * for public api)
# Set numba environment variable
import os
import sys
package_path = os.path.abspath(os.path.dirname(__file__))
cache_path = os.path.join(package_path, 'cache')
cache_status_path = os.path.join(package_path, '.cache_status.yaml')
os.environ['NUMBA_CACHE_DIR'] = cache_path


from pyreason.pyreason import *
import yaml
from importlib.metadata import PackageNotFoundError, version

try:
    # Read the installed package version for callers that inspect pyreason.__version__.
    __version__ = version(__name__)
except PackageNotFoundError:
    # Editable or source checkouts may not be installed as a distribution yet.
    pass


with open(cache_status_path) as file:
    cache_status = yaml.safe_load(file)

# Skip first-import Numba warmup under test runners so collection stays fast.
running_tests = 'pytest' in sys.modules or 'unittest' in sys.modules

if not cache_status['initialized'] and not running_tests:
    print('Imported PyReason for the first time. Initializing caches for faster runtimes ... this will take a minute')
    graph_path = os.path.join(package_path, 'examples', 'hello-world', 'friends_graph.graphml')

    settings.verbose = False
    load_graphml(graph_path)
    add_rule(Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    add_fact(Fact('popular(Mary)', 'popular_fact', 0, 2))
    reason(timesteps=2)

    reset()
    reset_rules()
    print('PyReason initialized!')
    print()

    # Remember that the first-import warmup finished so later imports skip it.
    cache_status['initialized'] = True
    with open(cache_status_path, 'w') as file:
        yaml.dump(cache_status, file)
