<img src="https://raw.githubusercontent.com/lab-v2/pyreason/main/media/pyreason_logo.jpg"/>

[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Documentation Status](https://readthedocs.org/projects/pyreason/badge/?version=latest)](https://pyreason.readthedocs.io/en/latest/?badge=latest)
[![pypi](https://github.com/lab-v2/pyreason/actions/workflows/python-publish.yml/badge.svg)](https://github.com/lab-v2/pyreason/actions/workflows/python-publish.yml)
[![Tests](https://github.com/lab-v2/pyreason/actions/workflows/python-package-version-test.yml/badge.svg)](https://github.com/lab-v2/pyreason/actions/workflows/python-package-version-test.yml)


An explainable inference software supporting annotated, real valued, graph based and temporal logic.

## Links
[📃 Paper](https://arxiv.org/abs/2302.13482)

[📽️ Video](https://www.youtube.com/watch?v=E1PSl3KQCmo)

[🌐 Website](https://neurosymbolic.asu.edu/pyreason/)

[🏋️‍♂️ PyReason Gym](https://github.com/lab-v2/pyreason-gym)

[🗎 Documentation](https://pyreason.readthedocs.io/en/latest/)

Check out the [PyReason Hello World](https://pyreason.readthedocs.io/en/latest/tutorials/Basic%20tutorial.html) program if you're new, or want get get a feel for the software.


## Table of Contents
  
1. [Introduction](#1-introduction)
2. [Documentation](#2-documentation)
3. [Install](#3-install)
5. [Bibtex](#4-bibtex)
6. [License](#5-license)
7. [Contact](#6-contact)


## 1. Introduction
PyReason is a graphical inference tool that uses a set of logical rules and facts (initial conditions) to reason over graph structures. To get more details, refer to the paper/video/hello-world-example mentioned above.

## 2. Documentation 
All API documentation and code examples can be found on [ReadTheDocs](https://pyreason.readthedocs.io/en/latest/)

## 3. Install
PyReason can be installed as a python library using

```bash
pip install pyreason
```
The Python versions that are currently supported are `3.7`, `3.8`, `3.9`, `3.10`. If you want multi-core parallel support only `3.9` and `3.10` versions work due to limited numba support.

## 4. Bibtex
If you used this software in your work please cite our paper

Bibtex:
```
@inproceedings{aditya_pyreason_2023,
title = {{PyReason}: Software for Open World Temporal Logic},
booktitle = {{AAAI} Spring Symposium},
author = {Aditya, Dyuman and Mukherji, Kaustuv and Balasubramanian, Srikar and Chaudhary, Abhiraj and Shakarian, Paulo},
year = {2023}}
```

## 5. License
This repository is licensed under [BSD-2-Clause](https://github.com/lab-v2/pyreason/blob/main/LICENSE.md).

Trademark Permission PyReason™ and PyReason Design Logo <img src="https://raw.githubusercontent.com/lab-v2/pyreason/main/media/pyreason_logo.jpg" width="50"/>™ are trademarks of the Arizona Board of Regents/Arizona State University. Users of the software are permitted to use PyReason™ in association with the software for any purpose, provided such use is related to the software (e.g., Powered by PyReason™). Additionally, educational institutions are permitted to use the PyReason Design Logo <img src="https://raw.githubusercontent.com/lab-v2/pyreason/main/media/pyreason_logo.jpg" width="50"/>™ for non-commercial purposes.


## 6. Contact
Dyuman Aditya - dyuman.aditya@asu.edu

Kaustuv Mukherji - kmukher2@asu.edu

Paulo Shakarian - pshak02@asu.edu
