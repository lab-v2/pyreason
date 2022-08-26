# MANCaLog
Implementation of MANCaLog: 
A Logic for Multi-Attribute Network Cascades.

Paper: [https://arxiv.org/abs/1301.0302](https://arxiv.org/abs/1301.0302)

## Table of Contents
<details>
  <summary>Table of Contents</summary>
  
1. [Usage](#1-usage)
2. [Setup & Run](#2-setup--run)
    * [Setup & Run on the ASU Agave Cluster (interactive)](#21-setup--run-on-the-asu-agave-cluster-interactive)
    * [Setup & Run on the ASU Agave Cluster (sbatch)](#22-setup--run-on-the-asu-agave-cluster-sbatch)
    * [Setup & Run on your Local System](#23-setup--run-on-your-local-system)
3. [Profiling](#3-profiling)
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

## 2. Setup & Run
There are three ways of running MANCaLog:
1. interactive session (on Agave cluster)
2. sbatch (on Agave cluster)
3. locally

To Run mancalog, you need to provide the following as command line arguments:

1. The path to a graphml file
2. The number of timesteps you want to run the diffusion
3. The path to the YAML rules file
4. The path to the YAML facts file
5. The path to the YAML labels file

### 2.1 Setup & Run on the ASU Agave Cluster (interactive)
To create an Anaconda environment and activate it, and then clone the repository, type the following in your Agave terminal:
```bash
module load anaconda/py3
conda create -n mancalog
source activate mancalog
git clone https://github.com/DyumanAditya/mancalog
cd mancalog
pip install -r requirements.txt
```
Now create an interavtive session with:
```bash
interactive -N 1 -n 50 -p htc -t 0-0:10
```
This starts an interactive session using 50 cores on one node for 10 minutes. You can change the time parameter based on your needs.

To run MANCaLog, type the following in your Agave terminal. Make sure you are in the top mancalog directory. Don't forget to replace the placeholders with the correct values.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml
```


### 2.2 Setup & Run on the ASU Agave Cluster (sbatch)
Open the run_on_agave.sh in a text editor, and modify the paths for the graph file, the rules file, the facts file and the labels file. In addition specify the number of timesteps to run for. Then in your Agave terminal, type:
```bash
sbatch run_on_agave.sh
```
This will submit a job to the cluster

### 2.3 Setup & Run on your Local System
Clone the repository and install the necessary packages to make mancalog run

```bash
git clone https://github.com/DyumanAditya/mancalog
cd mancalog
pip install -r requirements.txt
```
To run MANCaLog, type the following in your Agave terminal. Make sure you are in the top mancalog directory. Don't forget to replace the placeholders with the correct values.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml
```

## 3. Profiling
To Profile the code with cProfile:
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run} --rules_yaml_path /path/to/rules.yaml --facts_yaml_path /path/to/facts.yaml --labels_yaml_path /path/to/labels.yaml --profile true --profile_output output.txt
```