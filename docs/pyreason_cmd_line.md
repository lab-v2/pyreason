# PyReason Command Line Tool

## Install
```python
git clone https://github.com/lab-v2/pyreason
cd pyreason
pip install -r requirements.txt
python initialize.py
```

## Run
To Run pyreason, the required command line arguments are:

1. The path to a graphml file
2. The path to the YAML rules file

It is recommended that the following arguments are supplied as well, otherwise the program will only use the information from the graphml attributes:

1. The path to the YAML labels file
2. The path to the YAML facts file

For more optional command line arguments refer to (make doc) or type 
```python
python3 -m pyreason.scripts.diffuse -h
```

Example with placeholders:
```bash
python -m pyreason.scripts.diffuse --graph_path <path/to/graphml/file> --timesteps <Max number of timesteps to run> --rules_yaml_path <path/to/rules.yaml> --facts_yaml_path <path/to/facts.yaml> --labels_yaml_path <path/to/labels.yaml>
```
