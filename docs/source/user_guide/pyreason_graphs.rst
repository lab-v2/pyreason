PyReason Graphs
===============

PyReason supports direct reasoning over knowledge graphs. PyReason graphs have full explainability of the reasoning process. Graphs serve as the knowledge base for PyReason, with initial conditions and attributes. 
PyReason uses rules to create new relationships or change attribute relationships in a graph. Pyreason reasons on an inputed graph and evolves the graph over time.

How to Load a Graph in RyReason
-------------------------------
In PyReason there are two ways to create graphs: NetworkX and GraphML
NetworkX allows you to manually add nodes and edges, whereas GraphML reads in a directed graph from a file.


NetworkX Example
~~~~~~~~~~~~~~~~
Using NetworkX, you can create a `directed <https://en.wikipedia.org/wiki/Directed_graph>`_  graph object. Users can add and remove nodes and edges from the graph.

Read more about NetworkX `here <https://networkx.org/documentation/stable/reference/classes/digraph.html>`_.

The following graph represents a network of people and the pets that
they own.

1. Mary is friends with Justin
2. Mary is friends with John
3. Justin is friends with John

And

1. Mary owns a cat
2. Justin owns a cat and a dog
3. John owns a dog

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
   
After the graph has been created, it can be loaded with:

.. code:: python

  import pyreason as pr
  pr.load_graph(graph: nx.DiGraph)



GraphML Example
~~~~~~~~~~~~~~~~
Using `GraphML <https://en.wikipedia.org/wiki/GraphML>`_, you can read a graph in from a file.

.. code:: xml

   <?xml version='1.0' encoding='utf-8'?>
   <graphml
       xmlns="http://graphml.graphdrawing.org/xmlns"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
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


Initial Conditions
------------------
PyReason uses graph attributes (assigned to nodes or edges), to convert to *static facts*. *Static facts* do not change over time.
Once the graph is loaded, all attributes will remain the same until the end of the section of PyReason using the graph. 



Additional Considerations
--------------------------
Attributes to Bounds:

In Pyreason graphs, each node, and edge can hold key/value attribute pairs in an associated attribute dictionary (the keys must be hashable).

These attributes get transformed into "bounds". Bounds are between 0 (false) and 1 (true).  The attribute value in Networkx, is translated into the lower bound in PyReason. 

When an attribiute is set to 0, the assumed upper bound is 1 which create [0,1], an inconsistant predicate. To avoid this, and make the bounds [0,0] set the attributes with a string.
.. code:: python

    import networkx as nx
    g = nx.DiGraph()
    g.add_node("some_node", attribute1=1, attribute2="0,0")


When the graph is loaded: 

  .. code:: text

    "some_node" is given the attribute1: [1,1], and attribute2 :[0,0]. 

If the attribute is set equal to a single value, the assumed upper bound is 1. If a specific pair of bounds is required (e.g., for coordinates or ranges), the value should be provided as a string in a specific format.
