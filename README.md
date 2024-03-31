# PyReason
<img src="https://raw.githubusercontent.com/lab-v2/pyreason/main/media/pyreason_logo.jpg"/>

[![Python Build](https://github.com/lab-v2/pyreason/actions/workflows/python-publish.yml/badge.svg)](https://github.com/lab-v2/pyreason/actions/workflows/python-publish.yml)
[![Python version compatibility](https://github.com/lab-v2/pyreason/actions/workflows/python-package-version-test.yml/badge.svg)](https://github.com/lab-v2/pyreason/actions/workflows/python-package-version-test.yml)

An explainable inference software supporting annotated, real valued, graph based and temporal logic.

## Links
[📃 Paper](https://arxiv.org/abs/2302.13482)

[📽️ Video](https://www.youtube.com/watch?v=E1PSl3KQCmo)

[🌐 Website](https://neurosymbolic.asu.edu/pyreason/)

[🏋️‍♂️ PyReason Gym](https://github.com/lab-v2/pyreason-gym)

Check out the [PyReason Hello World](https://github.com/lab-v2/pyreason/blob/main/docs/hello-world.md) program if you're new, or want get get a feel for the software.


## Table of Contents
  
1. [Introduction](#1-introduction)
2. [Install](#2-install)
    * [Install as a Python Library](#21-install-as-a-python-library)
    * [Install as a command line tool](#22-install-as-a-command-line-tool)
3. [Usage](#3-usage)
4. [Bibtex](#4-bibtex)
5. [License](#5-license)
6. [Contact](#6-contact)


## 1. Introduction
PyReason makes use of 4 files:

1. A GraphMl file containing the graph (required)
2. A YAML file containing the pyreason rules (required)
3. A YAML file containing the pyreason facts (optional but recommended)
4. A YAML file containing the pyreason labels (optional but recommended)
5. A YAML file containing the pyreason ipl (inconsistent predicate list) (optional)

The format of these files is very important. Please refer to the [example YAML files provided](https://github.com/lab-v2/pyreason/blob/main/pyreason/examples/example_yamls) when making your own rules/facts/labels/ipl. TODO: make doc for each format.

## 2. Install
PyReason can be installed as a python library (recommended) or as a command line tool

## 2.1 Install as a Python Library
We import pyreason to initialize it for the first time, this may take a few minutes
```bash
pip install pyreason
python
import pyreason
```

## 2.2 Install as a Command Line Tool

```bash
git clone https://github.com/lab-v2/pyreason
cd pyreason
pip install -r requirements.txt
python initialize.py
```

## 3. Usage
Please refer to the documentation that is relevant to you
1. [Usage as Python Library](https://github.com/lab-v2/pyreason/blob/main/docs/pyreason_library.md)
2. [Usage as a Command Line Tool](https://github.com/lab-v2/pyreason/blob/main/docs/pyreason_cmd_line.md)

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
This repository is licensed under [BSD-3-Clause](https://github.com/lab-v2/pyreason/blob/main/LICENSE.md)

## 6. Contact
Dyuman Aditya - dyuman.aditya@asu.edu

Kaustuv Mukherji - kmukher2@asu.edu

Paulo Shakarian - pshak02@asu.edu
