# PyReason Python Library
pypi project: https://pypi.org/project/pyreason/

## Install
```bash
pip install pyreason
python
import pyreason
```
We import pyreason to initialize it for the first time, this may take a few minutes

## Usage
Example:
```python
import pyreason as pr

pr.load_graph(some_networkx_graph)
pr.add_rule(rule_written_in_pyreason_format)
pr.add_fact(pr.Fact(...))

pr.settings.verbose = True
interpretation = pr.reason()
```

`load_graph` and `add_rules` have to be called before `pr.reason`. Loading of facts and labels is optional but recommended; if they are not loaded the program will use only the information from attributes in the graph.

`settings` contains several parameters that can be modified by the user

`interpretation` is the final interpretation after the reasoning is complete. 
