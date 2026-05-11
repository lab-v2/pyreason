from setuptools import setup, find_packages

# Read the contents of README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='UTF-8')

setup(
    name='pyreason',
    version='4.0.0b1',
    author='Colton Payne',
    author_email='coltonpayne23@gmail.com',
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
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.12,<3.14',
    install_requires=[
        'networkx',
        'pyyaml',
        'pandas',
        'numba>=0.61.0',
        'numpy>=1.26.4',
        'memory_profiler',
        'pytest'
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    include_package_data=True
)
