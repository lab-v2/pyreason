PyReason Infer Edges Example
============================

In this tutorial, we will look at how to run PyReason with infer edges. 
infer edges is a parameter in the :ref:`Rule Class <pyreason_rules>`. 

The following graph represents a network of People and a Text Message in their group chat.
.. image:: ../media/group_chat_graph.png

Graph
------------

First, we load in the GraphML. This graph has airports and flight connections.

.. code:: xml
    <?xml version='1.0' encoding='utf-8'?>
    <graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
    <key id="isConnectedTo" for="edge" attr.name="isConnectedTo" attr.type="long" />
    <key id="Amsterdam_Airport_Schiphol" for="node" attr.name="Amsterdam_Airport_Schiphol" attr.type="long" />
    <key id="Riga_International_Airport" for="node" attr.name="Riga_International_Airport" attr.type="long" />
    <key id="Chișinău_International_Airport" for="node" attr.name="Chișinău_International_Airport" attr.type="long" />
    <key id="Düsseldorf_Airport" for="node" attr.name="Düsseldorf_Airport" attr.type="long" />
    <key id="Dubrovnik_Airport" for="node" attr.name="Dubrovnik_Airport" attr.type="long" />
    <key id="Athens_International_Airport" for="node" attr.name="Athens_International_Airport" attr.type="long" />
    <key id="Yali" for="node" attr.name="Yali" attr.type="long" />
    <key id="Vnukovo_International_Airport" for="node" attr.name="Vnukovo_International_Airport" attr.type="long" />
    <key id="Hévíz-Balaton_Airport" for="node" attr.name="Hévíz-Balaton_Airport" attr.type="long" />
    <key id="Pobedilovo_Airport" for="node" attr.name="Pobedilovo_Airport" attr.type="long" />
    <graph id="G" edgedefault="directed">
    <node id="Amsterdam_Airport_Schiphol">
        <data key="Amsterdam_Airport_Schiphol">1</data>
        </node>
        <node id="Riga_International_Airport">
        <data key="Riga_International_Airport">1</data>
        </node>
        <node id="Chișinău_International_Airport">
        <data key="Chișinău_International_Airport">1</data>
        </node>
        <node id="Yali">
        <data key="Yali">1</data>
        </node>
        <node id="Düsseldorf_Airport">
        <data key="Düsseldorf_Airport">1</data>
        </node>
        <node id="Pobedilovo_Airport">
        <data key="Pobedilovo_Airport">1</data>
        </node>
        <node id="Dubrovnik_Airport">
        <data key="Dubrovnik_Airport">1</data>
        </node>
        <node id="Hévíz-Balaton_Airport">
        <data key="Hévíz-Balaton_Airport">1</data>
        </node>
        <node id="Athens_International_Airport">
        <data key="Athens_International_Airport">1</data>
        </node>
        <node id="Vnukovo_International_Airport">
        <data key="Vnukovo_International_Airport">1</data>
        </node>
        <edge source="Pobedilovo_Airport" target="Vnukovo_International_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Vnukovo_International_Airport" target="Hévíz-Balaton_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Düsseldorf_Airport" target="Dubrovnik_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Dubrovnik_Airport" target="Athens_International_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
    <edge source="Riga_International_Airport" target="Amsterdam_Airport_Schiphol">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Riga_International_Airport" target="Düsseldorf_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Chișinău_International_Airport" target="Riga_International_Airport">
            <data key="isConnectedTo">1</data>
        </edge>
        <edge source="Amsterdam_Airport_Schiphol" target="Yali">
        <data key="isConnectedTo">1</data>
        </edge>

    </graph>
    </graphml>

We then initialize and load the graph using the following code:

.. code:: python

    import pyreason as pr

    def test_anyBurl_rule_1():
        graph_path = 'knowledge_graph_test_subset.graphml'
        pr.reset()
        pr.reset_rules()
        # Modify pyreason settings to make verbose and to save the rule trace to a file
        pr.settings.verbose = True
        pr.settings.atom_trace = True
        pr.settings.memory_profile = False
        pr.settings.canonical = True
        pr.settings.inconsistency_check = False
        pr.settings.static_graph_facts = False
        pr.settings.output_to_file = False
        pr.settings.store_interpretation_changes = True
        pr.settings.save_graph_attributes_to_trace = True
        # Load all the files into pyreason
        pr.load_graphml(graph_path)

Next, add the Rule and set infer_edges to *True*

.. code:: python

    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

This will should connect exactly one new relationship between A and Y. The Rule states that if there is a connection from Y to B, and B is Amsterdam Airport Schiphol, and A is Vnukovo International Airport, then infer that there is a connection from A to Y."

Therefore the output of the graph after running 1 timestep should be a new connection [1,1] between Vnukovo_International_Airport (A) and Riga_International_Airport(Y).

Run the program with assertions for testing purposes:

.. code:: python
    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)
    # pr.save_rule_trace(interpretation)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()
    assert len(dataframes) == 2, 'Pyreason should run exactly 1 fixpoint operations'
    assert len(dataframes[1]) == 1, 'At t=1 there should be only 1 new isConnectedTo atom'
    assert ('Vnukovo_International_Airport', 'Yali') in dataframes[1]['component'].values.tolist() and dataframes[1]['isConnectedTo'].iloc[0] == [1, 1], '(Vnukovo_International_Airport, Yali) should have isConnectedTo bounds [1,1] for t=1 timesteps'

The expected output after running will list at timestep 0 the inital connections and timestep 1 the added connectioned due to the infer_edges parameter. 

.. code:: text
    Timestep: 0
    Timestep: 1

    Converged at time: 1
    Fixed Point iterations: 2
    TIMESTEP - 0
                                            component isConnectedTo
    0                 (Amsterdam_Airport_Schiphol, Yali)    [1.0, 1.0]
    1  (Riga_International_Airport, Amsterdam_Airport...    [1.0, 1.0]
    2   (Riga_International_Airport, Düsseldorf_Airport)    [1.0, 1.0]
    3  (Chișinău_International_Airport, Riga_Internat...    [1.0, 1.0]
    4            (Düsseldorf_Airport, Dubrovnik_Airport)    [1.0, 1.0]
    5  (Pobedilovo_Airport, Vnukovo_International_Air...    [1.0, 1.0]
    6  (Dubrovnik_Airport, Athens_International_Airport)    [1.0, 1.0]
    7  (Vnukovo_International_Airport, Hévíz-Balaton_...    [1.0, 1.0]

    TIMESTEP - 1
                                            component isConnectedTo
    0  (Vnukovo_International_Airport, Riga_Internati...    [1.0, 1.0]





