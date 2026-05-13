from setuptools import setup, find_packages

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='UTF-8')

setup(
    name='pyreason',
    author='Dyuman Aditya',
    author_email='dyuman.aditya@gmail.com',
    description='An explainable inference software supporting annotated, real valued, graph based and temporal logic',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lab-v2/pyreason',
    license='BSD 3-clause',
    project_urls={
        'Bug Tracker': 'https://github.com/lab-v2/pyreason/issues',
        'Repository': 'https://github.com/lab-v2/pyreason'
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.10',
    install_requires=[
        'networkx>=3.1',
        'pyyaml>=6.0',
        'pandas>=2.0.0',
        'numba>=0.65.1',
        'numpy>=2.1,<2.5',
        'memory_profiler',
        'pytest'
    ],
    packages=find_packages(),
    include_package_data=True
)
