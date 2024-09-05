# Set numba environment variable
import os
package_path = os.path.abspath(os.path.dirname(__file__))
cache_path = os.path.join(package_path, 'cache')
cache_status_path = os.path.join(package_path, '.cache_status.yaml')
os.environ['NUMBA_CACHE_DIR'] = cache_path


from pyreason.pyreason import *
import yaml
from importlib.metadata import version
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass


with open(cache_status_path) as file:
    cache_status = yaml.safe_load(file)

if not cache_status['initialized']:
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

    # Update cache status
    cache_status['initialized'] = True
    with open(cache_status_path, 'w') as file:
        yaml.dump(cache_status, file)
