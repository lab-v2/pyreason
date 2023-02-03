from setuptools import setup, find_packages
from setuptools.command.install import install
import sys
import os

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

class Initialize(install):
    def run(self):
        install.run(self)
        sys.path.append('./')
        import pyreason as pr
        print('Initializing PyReason caches')
        graph_path = os.path.join('docs', 'hello-world', 'friends.graphml')
        labels_path = os.path.join('docs', 'hello-world', 'labels.yaml')
        facts_path = os.path.join('docs', 'hello-world', 'facts.yaml')
        rules_path = os.path.join('docs', 'hello-world', 'rules.yaml')
        ipl_path = os.path.join('docs', 'hello-world', 'ipl.yaml')

        pr.settings.verbose = False
        pr.load_graph(graph_path)
        pr.load_labels(labels_path)
        pr.load_facts(facts_path)
        pr.load_rules(rules_path)
        pr.load_inconsistent_predicate_list(ipl_path)
        pr.reason(timesteps=2)


setup(
    name = 'pyreason',
    version = '0.0.6',
    author = 'Dyuman Aditya',
    author_email = 'dyuman.aditya@gmail.com',
    description = 'An explainable inference software supporting annotated, real valued, graph based and temporal logic',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/lab-v2/pyreason',
    license = 'BSD 3-clause',
    project_urls = {
        'Bug Tracker': 'https://github.com/lab-v2/pyreason/issues',
        'Repository': 'https://github.com/lab-v2/pyreason'
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent"
    ],
    python_requires = '>3.6',
    install_requires = [
        'networkx',
        'pyyaml',
        'pandas',
        'numba',
        'numpy',
        'memory_profiler'
    ],
    packages = find_packages(),
    cmdclass = {
        'install': Initialize
    }
)
