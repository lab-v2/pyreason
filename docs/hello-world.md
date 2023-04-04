# PyReason Hello World! 🚀

Welcome to PyReason! In this document we outline a simple program that demonstrates some of the capabilities of the software. If this is your first time looking at the software, you're in the right place.

The following graph represents a network of people and the pets that they own. 

<img src="../media/hello_world_friends_graph.png"/>

1. Mary is friends with Justin
2. Mary is friends with John
3. Justin is friends with John

And
1. Mary owns a cat
2. Justin owns a cat and a dog
3. John owns a dog

All of this is represented in [GraphML format](../pyreason/examples/hello-world/friends.graphml).  

Let's assume that a person's popularity (for illustration 😀) is determined by whether they have AT LEAST ONE friend who is popular AND who has the same pet that they do. If this is true, then they are considered popular.

PyReason needs 4 files to run:
1. labels.yaml
2. facts.yaml
3. rules.yaml
4. ipl.yaml

These are all YAML files but need to be in a specific PyReason format to work. See the examples below, or the [example yamls](../pyreason/examples/example_yamls/)

## Labels
Our labels.yaml file will look like this:

```yaml
---
# Labels that apply to all nodes
node_labels:
    - popular

# Labels that apply to all edges
edge_labels:
    - owns
    - friends

# Labels that apply to specific nodes. In this case nothing
node_specific_labels:

# Labels that apply to specific edges. In this case nothing
edge_specific_labels:
```

Each node will receive a `popular` label, and each edge will get a `owns` and `friends` label. The bounds for each of these are set to `[0, 1]` initially.

## Facts
To set initial conditions on labels we need a facts.yaml file. This is how we initialize the bounds to what we want before the program runs

Our facts.yaml will look like:

```yaml
---
# List all facts below
nodes:
    fact_1:
        node: Mary          # Name of the node
        label: popular      # Name of the label of the node
        bound: [1, 1]       # Bound of the label
        static: false       # Whether it applies to all timesteps and cannot change
        t_lower: 0          # Starting time
        t_upper: 2          # Ending time. 

edges:
    fact_1:
        source: Mary       # Source of the edge
        target: Cat        # Target of the edge
        label: owns        # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_2:
        source: Justin     # Source of the edge
        target: Cat        # Target of the edge
        label: owns        # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_3:
        source: Justin     # Source of the edge
        target: Dog        # Target of the edge
        label: owns        # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_4:
        source: John       # Source of the edge
        target: Dog        # Target of the edge
        label: owns        # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_5:
        source: Justin     # Source of the edge
        target: Mary       # Target of the edge
        label: friends     # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_6:
        source: John       # Source of the edge
        target: Justin     # Target of the edge
        label: friends     # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 

    fact_7:
        source: John       # Source of the edge
        target: Mary       # Target of the edge
        label: friends     # Name of the label of the node
        bound: [1, 1]      # Bound of the label
        static: true
        t_lower: 0         # Starting time
        t_upper: 0         # Ending time. 
```

This tells us who is friends with who and who owns what.


## Rules

Now lets define the rules.yaml file which will tell the program how bounds should changed if certain criteria are satisfied. In our case we want a person's `popular` label to be set to `[0,1]` if they have AT LEAST ONE friend who is `popular: [1,1]` AND who has the same pet as they do. We represent this in the following PyReason rule format

```yaml
---
# All Rules come under here
rule_1:
    target: popular     # Target label

    target_criteria:       # List of all target criteria
        # All criteria come here in the form [label, lower_bound, upper_bound]
        - [popular, 0, 1]

    delta_t: 1             # Delta t, time when this rule is applicable

    neigh_criteria:        # List of all neighbour criteria in the form [criteria on node/edge, variable, label, [lower_bound, upper_bound], [equal/greater/less/greater_equal/less_equal, number/[percent, total/available], value]]
        - [node, [x1], popular, [1,1], [greater_equal, number, 1]]
        - [edge, [target, x1], friends, [1,1], [greater_equal, number, 1]]
        - [edge, [x1, x2], owns, [1,1], [greater_equal, number, 1]]
        - [edge, [target, x2], owns, [1,1], [greater_equal, number, 1]]

    ann_fn: [1,1]          # Annotation function name or bound. See annotation_functions.py for list of available functions. The name of that function comes here
                           # Could be func_name or [l, u]
```

The `neigh_criteria` describes the conditions on the neighbors to be satisfied for the rule to fire.

In English this rule says: rule_1 will fire in 1 timestep on node `x`'s `popular` label if `x` has the label popular associated with it, and if node `x` has at least one popular neighbor and has the same pet as node `x`. When the rule fires on node `x`, the label `popular` will be set to `[1,1]`

There are 4 clauses in the rule (`neigh_criteria`):
(Variables in clauses represent subsets of neighbors. The first mention of a variable means it is the entire set of neighbors)
1. In the subset `x1` there should be at least one node with `popular: [1,1]`
2. Out of subset `x1` (all the nodes that are neighbors and have `popular: [1,1]`), there should be at least one node that is a friend with the target node.
3. Out of all the neighbors that are popular and friends with the target node, `x2` is the subset of all the pets that they own.
4. There should be at least one pet in `x2` that is the target node's pet as well

## IPL (Inconsistent Predicate List)
For now we will leave this file empty because we are not dealing with predicates/labels that can be inconsistent with one another.

The ipl.yaml will look like:
```yaml
---
ipl: null
```


## Running PyReason

Run PyReason as a python package:
```bash
python -m pyreason.scripts.diffuse --graph_path pyreason/examples/hello-world/friends.graphml --timesteps 2 --rules_yaml_path pyreason/examples/hello-world/rules.yaml --facts_yaml_path pyreason/examples/hello-world/facts.yaml --labels_yaml_path pyreason/examples/hello-world/labels.yaml --ipl pyreason/examples/hello-world/ipl.yaml --filter_label popular
```

Typing `python -m pyreason.scripts.diffuse -h` will display more command line options

## Expected Output
The output after running this is:

```
 TIMESTEP - 0
  component    popular
0      Mary  [1.0,1.0]


 TIMESTEP - 1
  component    popular
0      Mary  [1.0,1.0]
1    Justin  [1.0,1.0]


 TIMESTEP - 2
  component    popular
0      Mary  [1.0,1.0]
1    Justin  [1.0,1.0]
2      John  [1.0,1.0]

```

1. For timestep 0 we set `Mary -> popular: [1,1]` in the facts
2. For timestep 1, Justin is the only node who has one popular friend (Mary) and who has the same pet as Mary (cat). Therefore `Justin -> popular: [1,1]`
3. For timestep 2, since Justin has just become popular, John now has one popular friend (Justin) and the same pet as Justin (dog). Therefore `Justin -> popular: [1,1]`
