Graphs
===============
PyReason reasons over knowledge graphs. Graphs serve as a knowledge base with initial conditions given to nodes and edges.
These initial conditions are used along with :ref:`PyReason rules <pyreason_rules>` that we'll see later on to infer new relations or attributes.


How to Load a Graph in RyReason
-------------------------------
In PyReason there are two ways to load graphs:


1. Using a NetworkX `DiGraph <https://networkx.org/documentation/stable/reference/classes/digraph.html>`_ object
2. Using a `GraphML <https://networkx.org/documentation/stable/reference/readwrite/graphml.html>`_ file which is an encoding of a directed graph


NetworkX allows you to manually add nodes and edges, whereas GraphML reads in a directed graph from a file.


NetworkX Example
~~~~~~~~~~~~~~~~
Using NetworkX, you can create a `directed graph <https://en.wikipedia.org/wiki/Directed_graph>`_ object. Users can add and remove nodes and edges from the graph.

Read more about NetworkX `here <https://networkx.org/>`_.

Given a network of people and their pets, we can create a graph using NetworkX.

#. Mary is friends with Justin
#. Mary is friends with John
#. Justin is friends with John

And

#. Mary owns a cat
#. Justin owns a cat and a dog
#. John owns a dog

.. code-block:: python

    import networkx as nx

    # Create a NetowrkX Directed graph object
    g = nx.DiGraph()

    # Add the people as nodes
    g.add_nodes_from(['John', 'Mary', 'Justin'])
    g.add_nodes_from(['Dog', 'Cat'])

    # Add the edges and their attributes. When an attribute = x which is <= 1, the annotation
    # associated with it will be [x,1]. NOTE: These attributes are immutable unless specified otherwise in pyreason settings
    # Friend edges
    g.add_edge('Justin', 'Mary', Friends=1)
    g.add_edge('John', 'Mary', Friends=1)
    g.add_edge('John', 'Justin', Friends=1)

    # Pet edges
    g.add_edge('Mary', 'Cat', owns=1)
    g.add_edge('Justin', 'Cat', owns=1)
    g.add_edge('Justin', 'Dog', owns=1)
    g.add_edge('John', 'Dog', owns=1)
   
After the graph has been created, in the same file, the DiGraph object can be loaded with:

.. code-block:: python

    import pyreason as pr
    pr.load_graph(graph)



GraphML Example
~~~~~~~~~~~~~~~~
Using `GraphML <https://en.wikipedia.org/wiki/GraphML>`_, you can read a graph in from a file. Below is the file format for the graph that we made above:

.. code-block:: xml

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

.. code-block:: python

    import pyreason as pr
    pr.load_graphml('path_to_file')


Initial Conditions
------------------
PyReason uses graph attributes (assigned to nodes or edges) as initial conditions, and converts them to *static facts*. *Static facts* do not change over time.
Once the graph is loaded, all attributes will remain the same until the end of the section of PyReason using the graph. 


Graph Attributes to PyReason Bounds
~~~~~~~~~~~~~~~~~~~~
Since PyReason uses bounds to that are associated to attributes, it is important to understand how PyReason changes NetworkX attributes to bounds.
In NetworkX graphs, each node/edge can hold key/value attribute pairs in an associated attribute dictionary. These attributes get transformed into "bounds".
Bounds are between 0 (false) and 1 (true).  The attribute value of the key/value pair in Networkx, is translated into the lower bound in PyReason.

For example in the graph above, the attribute "Friends" is set to 1. This is translated into the lower bound of the interval ``[1,1]``.

.. note::
    Creating False bounds ``[0,0]`` is a little tricky since the value of a NetworkX attribute cannot be a list, and PyReason only modifies the
    lower bound keeping the upper bound as 1. To do this, we can set the attribute as a string as seen below.

.. code-block:: python

    import networkx as nx
    g = nx.DiGraph()
    g.add_node("some_node", attribute1=1, attribute2="0,0")


When the graph is loaded: 

.. code-block:: text

    "some_node" is given the attribute1: [1,1], and attribute2 :[0,0].

If the attribute is set equal to a single value, the assumed upper bound is 1. If a specific pair of bounds is required (e.g., for coordinates or ranges), the value should be provided as a string in a specific format.
