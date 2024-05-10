# Custom Thresholds Example

Here is an example that utilizes custom thresholds.

The following graph represents a network of People and a Text Message in their group chat.
<img src="../media/group_chat_graph.png"/>

In this case, we want to know when a text message has been viewed by all members of the group chat.

## Graph
First, lets create the group chat.

```python
import networkx as nx

# Create an empty graph
G = nx.Graph()

# Add nodes
nodes = ["TextMessage", "Zach", "Justin", "Michelle", "Amy"]
G.add_nodes_from(nodes)

# Add edges with attribute 'HaveAccess'
edges = [
    ("Zach", "TextMessage", {"HaveAccess": 1}),
    ("Justin", "TextMessage", {"HaveAccess": 1}),
    ("Michelle", "TextMessage", {"HaveAccess": 1}),
    ("Amy", "TextMessage", {"HaveAccess": 1})
]
G.add_edges_from(edges)

```


## Rules and Custom Thresholds
Considering that we only want a text message to be considered viewed by all if it has been viewed by everyone that can view it, we define the rule as follows:

```text
ViewedByAll(x) <- HaveAccess(x,y), Viewed(y)
```

The `head` of the rule is `popular(x)` and the body is `popular(y), Friends(x,y), owns(y,z), owns(x,z)`. The head and body are separated by an arrow and the time after which the head
will become true `<-1` in our case this happens after `1` timestep.

We add the rule into pyreason with:

```python
import pyreason as pr

pr.add_rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule')
```
Where `popular_rule` is just the name of the rule. This helps understand which rules fired during reasoning later on.

## Facts
The facts determine the initial conditions of elements in the graph. They can be specified from the graph attributes but in that
case they will be immutable later on. Adding PyReason facts gives us more flexibility.

In our case we want to set on of the people in our graph to be `popular` and use PyReason to see how others in the graph are affected by that.
We add a fact in PyReason like so:
```python
import pyreason as pr

pr.add_fact(pr.Fact(name='popular-fact', component='Mary', attribute='popular', bound=[1, 1], start_time=0, end_time=2))
```

This allows us to specify the component that has an initial condition, the initial condition itself in the form of bounds
as well as the start and end time of this condition. 

## Running PyReason
Find the full code for this example [here](hello-world.py)

The main line that runs the reasoning in that file is:
```python
interpretation = pr.reason(timesteps=2)
```
This specifies how many timesteps to run for.

## Expected Output
After running the python file, the expected output is:

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


We also output two CSV files detailing all the events that took place during reasoning (one for nodes, one for edges)