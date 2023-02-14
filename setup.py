from setuptools import setup, find_packages

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name = 'pyreason',
    version = '1.1.0',
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
    include_package_data=True
)
