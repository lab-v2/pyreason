PyReason Graphs
==============
**PyReason Graphs ** (Brief Intro)
PyReason supports direct reasoning over knowledge graphs. PyReason graphs have full explainability of the reasoning process. (add more)

-Notes: go more indepth about use cases of Graphs, connection to Nuero symbolic reasoning, other pyreason logic concepts etc.

Methods for Loading Graphs
^^^^^^^^^^^^^^^^^^^^^^^^^^
In PyReason there are two Methods for loading graphs: Networkx and GraphMl 


Networkx Example
^^^^^^^^^^^^^^^^
You can also build a graph using Networkx.

.. code:: python
    import networkx as nx

    # ================================ CREATE GRAPH====================================
    # Create a Directed graph
    g = nx.DiGraph()

    # Add the nodes
    g.add_nodes_from(['John', 'Mary', 'Justin'])
    g.add_nodes_from(['Dog', 'Cat'])

    # Add the edges and their attributes. When an attribute = x which is <= 1, the annotation
    # associated with it will be [x,1]. NOTE: These attributes are immutable
    # Friend edges
    g.add_edge('Justin', 'Mary', Friends=1)
    g.add_edge('John', 'Mary', Friends=1)
    g.add_edge('John', 'Justin', Friends=1)

    # Pet edges
    g.add_edge('Mary', 'Cat', owns=1)
    g.add_edge('Justin', 'Cat', owns=1)
    g.add_edge('Justin', 'Dog', owns=1)
    g.add_edge('John', 'Dog', owns=1)
   


GraphMl Example
^^^^^^^^^^^^^^^
Using GraphMl, you can also read in from a file.

.. code:: xml
<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="owns" for="edge" attr.name="owns" attr.type="long" />
  <key id="Friends" for="edge" attr.name="Friends" attr.type="long" />
  <graph edgedefault="directed">
    <node id="John" />
    <node id="Mary" />
    <node id="Justin" />
    <node id="Dog" />
    <node id="Cat" />
    <edge source="John" target="Mary">
      <data key="Friends">1</data>
    </edge>
    <edge source="John" target="Justin">
      <data key="Friends">1</data>
    </edge>
    <edge source="John" target="Dog">
      <data key="owns">1</data>
    </edge>
    <edge source="Mary" target="Cat">
      <data key="owns">1</data>
    </edge>
    <edge source="Justin" target="Mary">
      <data key="Friends">1</data>
    </edge>
    <edge source="Justin" target="Cat">
      <data key="owns">1</data>
    </edge>
    <edge source="Justin" target="Dog">
      <data key="owns">1</data>
    </edge>
  </graph>
</graphml>

Then load the graph using the following:

.. code:: python

   import pyreason as pr
   pr.load_graphml('path_to_file')

?? Add image output of graph possibly?
