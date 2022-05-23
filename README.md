# MANCaLog
Implementation of MANCaLog: 
A Logic for Multi-Attribute Network Cascades.

Paper: [https://arxiv.org/abs/1301.0302](https://arxiv.org/abs/1301.0302)

## Table of Contents
<details>
  <summary>Table of Contents</summary>
  
1. [Setup on the ASU Agave Cluster](#1-setup-on-the-asu-agave-cluster)
2. [Setup on your Local System](#2-setup-on-your-local-system)
3. [Run on the Agave Cluster](#3-run-on-the-agave-cluster)
4. [Run on your Local System](#4-run-on-your-local-system)
</details>

## Setup on the ASU Agave Cluster
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

## Setup on your Local System
Clone the repository and install the necessary packages to make mancalog run

```bash
git clone https://github.com/DyumanAditya/mancalog
cd mancalog
pip install -r requirements.txt
```

## Run on the Agave Cluster
Start an interactive session in your terminal by typing the following:
```bash
interactive -n 16 -N 1 -t 0-0:10
```
This starts an interactive session using 16 cores on one node for 10 minutes. You can change the parameters based on your needs.


Now type this into your terminal to run MANCaLog. make sure you are in the top `mancalog` directory.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run}
```

## Run on your Local System
Type this into your terminal to run MANCaLog. make sure you are in the top `mancalog` directory.
```bash
python3 -m mancalog.scripts.diffuse --graph_path /path/to/graphml/file --timesteps {integer number of timesteps to run}
```

