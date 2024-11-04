PyReason Custom Threshold Example
=================================
In this tutorial, we will look at how to run PyReason with Custom Thresholds. 


Graph
------------

First we load in the GraphML, this graph has friends and text messages.

.. code:: xml
    
    <?xml version='1.0' encoding='utf-8'?>
    <graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
    <key id="d0" for="edge" attr.name="HaveAccess" attr.type="long" />
    <graph edgedefault="directed">
        <node id="TextMessage" />
        <node id="Zach" />
        <node id="Justin" />
        <node id="Michelle" />
        <node id="Amy" />
        <edge source="Zach" target="TextMessage">
        <data key="d0">1</data>
        </edge>
        <edge source="Justin" target="TextMessage">
        <data key="d0">1</data>
        </edge>
        <edge source="Michelle" target="TextMessage">
        <data key="d0">1</data>
        </edge>
        <edge source="Amy" target="TextMessage">
        <data key="d0">1</data>
        </edge>
    </graph>
    </graphml>

We then initialize and load the graph using the following code:

.. code:: python

    import pyreason as pr
    from pyreason import Threshold


    def test_custom_thresholds():
        # Reset PyReason
        pr.reset()
        pr.reset_rules()

        # Modify the paths based on where you've stored the files we made above
        graph_path = "group_chat_graph.graphml"

        # Modify pyreason settings to make verbose
        pr.reset_settings()
        pr.settings.verbose = True  # Print info to screen

        # Load all the files into pyreason
        pr.load_graphml(graph_path)

