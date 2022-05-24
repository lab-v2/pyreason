# MANCaLog
Implementation of MANCaLog: 
A Logic for Multi-Attribute Network Cascades.

Paper: [https://arxiv.org/abs/1301.0302](https://arxiv.org/abs/1301.0302)

## Table of Contents
<details>
  <summary>Table of Contents</summary>
  
1. [Usage](#1-usage)
2. [Setup](#2-setup)
    * [Setup on the ASU Agave Cluster](#21-setup-on-the-asu-agave-cluster)
    * [Setup on your Local System](#22-setup-on-your-local-system)
3. [Run](#3-run)
    * [Run on the Agave Cluster](#31-run-on-the-agave-cluster)
    * [Run on your Local System](#32-run-on-your-local-system)
4. [Profiling](#4-profiling)
</details>

## 1. Usage
To run mancalog you need 3 files:

1. A YAML file containing the mancalog rules
2. A YAML file containing the mancalog facts
3. A YAML file containing the mancalog labels

The format of these files is very important. Please refer to the [example YAML files provided](mancalog/examples/example_yamls/) when making your own rules/facts/labels.

[An example file](mancalog/examples/) is provided to illustrate how mancalog works on a subset of a Honda supply chain graph.

To run the example, clone the repository, then:
```bash
cd mancalog
python3 -m mancalog.examples.example
```
This example file uses the example yaml files for rules, facts and labels.

## 2. Setup

### 2.1 Setup on the ASU Agave Cluster
Log into your ASURITE agave account, and open a terminal.

To create an Anaconda environment and activate it, type the following in your terminal:
```bash
module load anaconda/py3
conda create -n mancalog
source activate mancalog
```

Now clone the repository and install the necessary packages to make mancalog run

```bash
git clone https://github.com/DyumanAditya/mancalog
cd mancalog
pip install -r requirements.txt
```

### 2.2 Setup on your Local System
Clone the repository and install the necessary packages to make mancalog run

```bash
git clone https://github.com/DyumanAditya/mancalog
cd mancalog
pip install -r requirements.txt
```

## 3. Run

To Run mancalog, you need to provide the following as command line arguments:

1. The path to a graphml file
2. The number of timesteps you want to run the diffusion
3. The path to the YAML rules file
4. The path to the YAML facts file
5. The path to the YAML labels file

### 3.1 Run on the Agave Cluster
Start an interactive session in your terminal by typing the following:
```bash
interactive -n 16 -N 1 -t 0-0:10
```
This starts an interactive session using 16 cores on one node for 10 minutes. You can change the parameters based on your needs.


Now type this into your terminal to run MANCaLog. Make sure you are in the top `mancalog` directory. Don't forget to replace the placeholders with the correct values.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml
```

### 3.2 Run on your Local System
Type this into your terminal to run MANCaLog. Make sure you are in the top `mancalog` directory. Don't forget to replace the placeholders with the correct values.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml
```

## 4. Profiling
To Profile the code with cProfile:
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml --profile true --profile_output output.txt
```