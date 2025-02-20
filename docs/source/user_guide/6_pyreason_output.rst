.. _pyreason_output:

PyReason Output
===========================

This section outline four functions that help display and explain the PyReason output and reasoning process.

Filter and Sort Nodes
-----------------------
This function filters and sorts the node changes in the interpretation and returns as a list of Pandas dataframes that contain the filtered and sorted interpretations that are easy to access.

Basic Tutorial Example
^^^^^^^^^^^^^^^^^^^^^^^^
To see ``filter_and_sort_nodes`` in action we will look at the example usage in PyReasons Basic Tutorial.

.. note:: 
   Find the full, explained tutorial here `here <https://pyreason.readthedocs.io/en/latest/tutorials/basic_tutorial.html>`_


The tutorial take in a basic graph of people and their pets, then adds a Rule and a Fact.


.. code:: python

    pr.load_graph(g)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 2))

    # Run the program for two timesteps to see the diffusion take place
    faulthandler.enable()
    interpretation = pr.reason(timesteps=2)

We add the ``filter_and_sort_nodes`` after the interpretation is run, before PyReason prints the output: 

.. code:: python

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

This will print the nodes at each timestep in the reasoning process.

Expected Output
^^^^^^^^^^^^^^^^^
Using ``filter_and_sort_nodes``, the expected output is :

.. code:: python

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



Filter and Sort Edges
----------------------
This function filters and sorts the edge changes in the interpretation and returns a list of Pandas dataframes that contain the filtered and sorted interpretations, making them easy to access.

Infer Edges Example
^^^^^^^^^^^^^^^^^^^^^^^^
To see ``filter_and_sort_edges`` in action, we will look at the example usage in PyReason's Infer Edges Tutorial.

.. note:: 
   Find the full, explained tutorial here `here <https://pyreason.readthedocs.io/en/latest/tutorials/infer_edges.html>`_.

The tutorial takes in a basic graph of airports and connections, then infers an edges between two unconnected airports.

.. code:: python

    pr.load_graph(G)
    pr.add_rule(pr.Rule('isConnectedTo(A, Y) <-1  isConnectedTo(Y, B), Amsterdam_Airport_Schiphol(B), Vnukovo_International_Airport(A)', 'connected_rule_1', infer_edges=True))

    # Run the program for two timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=1)


We add the ``filter_and_sort_edges`` function after the interpretation is run, before PyReason prints the output:

.. code:: python

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_edges(interpretation, ['isConnectedTo'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

This will print the edges at each timestep in the reasoning process.

Expected Output
^^^^^^^^^^^^^^^^
Using ``filter_and_sort_edges``, the expected output is:

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



Get Rule Trace
---------------
This function returns the trace of the program as 2 pandas dataframes (one for nodes, one for edges).
This includes every change that has occurred to the interpretation. If ``atom_trace`` was set to true
this gives us full explainability of why interpretations changed

Advanced Tutorial Example
^^^^^^^^^^^^^^^^^^^^^^^

To see ``get_rule_trace`` in action we will look at the example usage in PyReasons Advanced Tutorial.

.. note:: 
   Find the full, explained tutorial here `here https://pyreason.readthedocs.io/en/latest/tutorials/advanced_tutorial.html>`_


The tutorial takes in a graph of we have customers, cars, pets and their relationships. We first have customer_details followed by car_details , pet_details , travel_details.

We will only add the ``get_rule_trace`` function after the interpretation:

.. code:: python

    interpretation = pr.reason(timesteps=5)
    nodes_trace, edges_trace = pr.get_rule_trace(interpretation)


Expected Output
^^^^^^^^^^^^^^^^
Using ``get_rule_trace``, the expected output of ``nodes_trace`` and ``edges_trace`` is:

Click `here <https://github.com/lab-v2/pyreason/blob/main/examples/csv%20outputs/advanced_rule_trace_nodes_20241119-012153.csv>`_ for the full table.

**Nodes Trace:**

.. code:: text

        Time  Fixed-Point-Operation         Node  ...      Occurred Due To               Clause-1      Clause-2
    0      0                      0  popular-fac  ...  popular(customer_0)                   None          None
    1      1                      2  popular-fac  ...  popular(customer_0)                   None          None
    2      1                      2   customer_4  ...        cool_car_rule  [(customer_4, Car_4)]       [Car_4]
    3      1                      2   customer_6  ...        cool_car_rule  [(customer_6, Car_4)]       [Car_4]
    4      1                      2   customer_3  ...        cool_pet_rule  [(customer_3, Pet_2)]       [Pet_2]
    5      1                      2   customer_4  ...        cool_pet_rule  [(customer_4, Pet_2)]       [Pet_2]
    6      1                      3   customer_4  ...          trendy_rule           [customer_4]  [customer_4]
    7      2                      4  popular-fac  ...  popular(customer_0)                   None          None
    8      2                      4   customer_4  ...        cool_car_rule  [(customer_4, Car_4)]       [Car_4]
    9      2                      4   customer_6  ...        cool_car_rule  [(customer_6, Car_4)]       [Car_4]
    10     2                      4   customer_3  ...        cool_pet_rule  [(customer_3, Pet_2)]       [Pet_2]
    11     2                      4   customer_4  ...        cool_pet_rule  [(customer_4, Pet_2)]       [Pet_2]
    12     2                      5   customer_4  ...          trendy_rule           [customer_4]  [customer_4]
    13     3                      6  popular-fac  ...  popular(customer_0)                   None          None
    14     3                      6   customer_4  ...        cool_car_rule  [(customer_4, Car_4)]       [Car_4]
    15     3                      6   customer_6  ...        cool_car_rule  [(customer_6, Car_4)]       [Car_4]
    16     3                      6   customer_3  ...        cool_pet_rule  [(customer_3, Pet_2)]       [Pet_2]
    17     3                      6   customer_4  ...        cool_pet_rule  [(customer_4, Pet_2)]       [Pet_2]
    18     3                      7   customer_4  ...          trendy_rule           [customer_4]  [customer_4]
    19     4                      8  popular-fac  ...  popular(customer_0)                   None          None
    20     4                      8   customer_4  ...        cool_car_rule  [(customer_4, Car_4)]       [Car_4]
    21     4                      8   customer_6  ...        cool_car_rule  [(customer_6, Car_4)]       [Car_4]
    22     4                      8   customer_3  ...        cool_pet_rule  [(customer_3, Pet_2)]       [Pet_2]
    23     4                      8   customer_4  ...        cool_pet_rule  [(customer_4, Pet_2)]       [Pet_2]
    24     4                      9   customer_4  ...          trendy_rule           [customer_4]  [customer_4]
    25     5                     10  popular-fac  ...  popular(customer_0)                   None          None
    26     5                     10   customer_4  ...        cool_car_rule  [(customer_4, Car_4)]       [Car_4]
    27     5                     10   customer_6  ...        cool_car_rule  [(customer_6, Car_4)]       [Car_4]
    28     5                     10   customer_3  ...        cool_pet_rule  [(customer_3, Pet_2)]       [Pet_2]
    29     5                     10   customer_4  ...        cool_pet_rule  [(customer_4, Pet_2)]       [Pet_2]
    30     5                     11   customer_4  ...          trendy_rule           [customer_4]  [customer_4]

**Edges Trace**

Click `here <https://github.com/lab-v2/pyreason/blob/main/examples/csv%20outputs/advanced_rule_trace_edges_20241119-012153.csv>`_ for the full table.


.. code:: text

        Time  ...                                           Clause-2
    0      0  ...         [(customer_1, Car_0), (customer_1, Car_8)]
    1      0  ...         [(customer_1, Car_0), (customer_1, Car_8)]
    2      0  ...  [(customer_2, Car_1), (customer_2, Car_3), (cu...
    3      0  ...         [(customer_1, Car_0), (customer_1, Car_8)]
    4      0  ...         [(customer_1, Car_0), (customer_1, Car_8)]
    ..   ...  ...                                                ...
    61     5  ...         [(customer_0, Car_2), (customer_0, Car_7)]
    62     5  ...         [(customer_5, Car_5), (customer_5, Car_2)]
    63     5  ...  [(customer_3, Car_3), (customer_3, Car_0), (cu...
    64     5  ...         [(customer_6, Car_6), (customer_6, Car_4)]
    65     5  ...         [(customer_0, Car_2), (customer_0, Car_7)]




Save Rule Trace
---------------
This function saves the trace of the program as two pandas dataframes (one for nodes, one for edges).
This includes every change that has occurred to the interpretation. If ``atom_trace`` was set to true,
this provides full explainability of why interpretations changed.

Infer Edges Tutorial Example
^^^^^^^^^^^^^^^^^^^^^^^^^^

To see ``save_rule_trace`` in action, we will look at an example usage in PyReason's Infer Edges Tutorial.

.. note::  
   Find the full, explained tutorial here `here <https://pyreason.readthedocs.io/en/latest/tutorials/infer_edges.html>`_.

This tutorial takes a graph with airports and their connections. 

We will only add the ``save_rule_trace`` function after the interpretation:

.. code:: python

    interpretation = pr.reason(timesteps=1)
    pr.save_rule_trace(interpretation, folder='./rule_trace_output')

Expected Output
^^^^^^^^^^^^^^^^
Using ``save_rule_trace``, the expected output is:

**Saved Nodes Trace:**

The nodes trace will be saved as a CSV file in the specified folder. It will contain the time, the fixed-point operation, the node, and the clause information that led to the change in each timestep. Here's an example snippet of how the data will look when saved:

Click `here <https://github.com/lab-v2/pyreason/blob/main/examples/csv%20outputs/infer_edges_rule_trace_nodes_20241119-140955.csv>`_ for the full table.



.. code:: text

    Time,Fixed-Point-Operation,Node,Label,Old Bound,New Bound,Occurred Due To
    0,0,Amsterdam_Airport_Schiphol,Amsterdam_Airport_Schiphol,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Riga_International_Airport,Riga_International_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Chișinău_International_Airport,Chișinău_International_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Yali,Yali,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Düsseldorf_Airport,Düsseldorf_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Pobedilovo_Airport,Pobedilovo_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Dubrovnik_Airport,Dubrovnik_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Hévíz-Balaton_Airport,Hévíz-Balaton_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Athens_International_Airport,Athens_International_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact
    0,0,Vnukovo_International_Airport,Vnukovo_International_Airport,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact



**Saved Edges Trace:**

The edges trace will be saved as another CSV file. It will contain the time, the edge relationship changes, and the clauses that were involved. Here’s a snippet of how the edge trace will look when saved:

Click `here <https://github.com/lab-v2/pyreason/blob/main/examples/csv%20outputs/infer_edges_rule_trace_edges_20241119-140955.csv>`_ for the full table.


.. code:: text

    Time,Fixed-Point-Operation,Edge,Label,Old Bound,New Bound,Occurred Due To,Clause-1,Clause-2,Clause-3
    0,0,"('Amsterdam_Airport_Schiphol', 'Yali')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Riga_International_Airport', 'Amsterdam_Airport_Schiphol')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Riga_International_Airport', 'Düsseldorf_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Chișinău_International_Airport', 'Riga_International_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Düsseldorf_Airport', 'Dubrovnik_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Pobedilovo_Airport', 'Vnukovo_International_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Dubrovnik_Airport', 'Athens_International_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    0,0,"('Vnukovo_International_Airport', 'Hévíz-Balaton_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",graph-attribute-fact,,,
    1,1,"('Vnukovo_International_Airport', 'Riga_International_Airport')",isConnectedTo,"[0.0,1.0]","[1.0,1.0]",connected_rule_1,"[('Riga_International_Airport', 'Amsterdam_Airport_Schiphol')]",['Amsterdam_Airport_Schiphol'],['Vnukovo_International_Airport']

Reading PyReasons Explainable Trace
------------------------------------
When using the functions ``save_rule_trace`` and ``get_rule_trace``, PyReason will output an explainable trace of the reasoning process.

In the trace, the columens represent the following:
 - ``time``: the current timestep 
 - ``Fixed-Point Operation``: 
 - ``Edge``: The edge or node that has changed if applicable
 - ``Label``: The predicate or head of the rule 
 - ``Old Bound`` and ``New Bound``: Bound before and after reasoning step
 - ``Occured Due to``: what the the change in the step was due to, either ``fact`` or ``rule``
 - ``Clause-x``: What grounded the clause in the rule

Get Dictionary
--------------------------
The function ``interpretation.get_dict()`` can be called externally to retrieve a dictionary of the interpretation values. The dictionary is triply nested from ``time`` -> ``graph component`` -> ``predicate`` -> ``bound``.

Basic Tutorial Example
^^^^^^^^^^^^^^^^
To see ``interpretation.get_dict()`` in action we will look at the example usage in PyReasons Basic Tutorial.

.. note:: 
   Find the full, explained tutorial here `here <https://pyreason.readthedocs.io/en/latest/tutorials/basic_tutorial.html>`_

Call ``.get_dict()`` function on the interpretation, and print using ``pprint``.

.. code:: python

    import pyreason as pr
    from pprint import pprint

    interpretation = pr.reason(timesteps=2)
    interpretations_dict = interpretation.get_dict()
    pprint(interpretations_dict)

Expected Output
^^^^^^^^^^^^^^^^
Using ``.get_dict()``, the expected output is: 


.. code:: text 

    {0: {'Cat': {},
        'Dog': {},
        'John': {},
        'Justin': {},
        'Mary': {'popular': (1.0, 1.0)},
        ('John', 'Dog'): {},
        ('John', 'Justin'): {},
        ('John', 'Mary'): {},
        ('Justin', 'Cat'): {},
        ('Justin', 'Dog'): {},
        ('Justin', 'Mary'): {},
        ('Mary', 'Cat'): {}},
    1: {'Cat': {},
        'Dog': {},
        'John': {},
        'Justin': {'popular': (1.0, 1.0)},
        'Mary': {'popular': (1.0, 1.0)},
        ('John', 'Dog'): {},
        ('John', 'Justin'): {},
        ('John', 'Mary'): {},
        ('Justin', 'Cat'): {},
        ('Justin', 'Dog'): {},
        ('Justin', 'Mary'): {},
        ('Mary', 'Cat'): {}},
    2: {'Cat': {},
        'Dog': {},
        'John': {'popular': (1.0, 1.0)},
        'Justin': {'popular': (1.0, 1.0)},
        'Mary': {'popular': (1.0, 1.0)},
        ('John', 'Dog'): {},
        ('John', 'Justin'): {},
        ('John', 'Mary'): {},
        ('Justin', 'Cat'): {},
        ('Justin', 'Dog'): {},
        ('Justin', 'Mary'): {},
        ('Mary', 'Cat'): {}}}


``interpretation.get_dict()`` first goes through each time step, then the components of the graph, and finally the predicates and bounds.
