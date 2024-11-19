.. _pyreason_expected_output:

PyReason Expected Output
===========================

This section outline four functions that help display and explain the PyReason output and reasoning process.

Filter and Sort Nodes
-----------------------
This function filters and sorts the node changes in the interpretation and returns as a list of Pandas dataframes that contain the filtered and sorted interpretations that are easy to access.

Basic Tutorial Example
^^^^^^^^^^^^^^^^^^^^^^^^
To see ``filter_and_sort_nodes`` in action we will look at the example usage in PyReasons Basic Tutorial.

.. note:: 
   Find the full, explained tutorial here `here <https://pyreason--60.org.readthedocs.build/en/60/tutorials/basic_tutorial.html#pyreason-basic-tutorial>`_


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
   Find the full, explained tutorial here `here <https://pyreason--60.org.readthedocs.build/en/60/tutorials/infer_edges.html#pyreason-infer-edges>`_.

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
   Find the full, explained tutorial here `here <https://pyreason--60.org.readthedocs.build/en/60/tutorials/advanced_tutorial.html#running-pyreason-with-an-advanced-graph>`_


The tutorial takes in a graph of we have customers, cars, pets and their relationships. We first have customer_details followed by car_details , pet_details , travel_details.

We will only add the ``get_rule_trace`` function after the interpretation:

.. code:: python

    interpretation = pr.reason(timesteps=5)
    nodes_trace, edges_trace = pr.get_rule_trace(interpretation)


Expected Output
^^^^^^^^^^^^^^^^
Using ``get_rule_trace``, the expected output of ``nodes_trace`` and ``edges_trace`` is:

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

Advanced Tutorial Example
^^^^^^^^^^^^^^^^^^^^^^^^^^

To see ``save_rule_trace`` in action, we will look at an example usage in PyReason's Advanced Tutorial.

.. note::  
   Find the full, explained tutorial here `here <https://pyreason--60.org.readthedocs.build/en/60/tutorials/advanced_tutorial.html#running-pyreason-with-an-advanced-graph>`_.

The tutorial takes in a graph with customers, cars, pets, and their relationships. We first have `customer_details`, followed by `car_details`, `pet_details`, and `travel_details`.

We will only add the ``save_rule_trace`` function after the interpretation:

.. code:: python

    interpretation = pr.reason(timesteps=5)
    pr.save_rule_trace(interpretation, folder='./rule_trace_output')

Expected Output
^^^^^^^^^^^^^^^^
Using ``save_rule_trace``, the expected output is:

**Saved Nodes Trace:**

The nodes trace will be saved as a CSV file in the specified folder. It will contain the time, the fixed-point operation, the node, and the clause information that led to the change in each timestep. Here's an example snippet of how the data will look when saved:

.. code:: text

    Time,Fixed-Point-Operation,Node,Label,Old Bound,New Bound,Occurred Due To,Clause-1,Clause-2
    0,0,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    1,2,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    1,2,customer_4,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_4', 'Car_4')]",['Car_4']
    1,2,customer_6,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_6', 'Car_4')]",['Car_4']
    1,2,customer_3,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_3', 'Pet_2')]",['Pet_2']
    1,2,customer_4,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_4', 'Pet_2')]",['Pet_2']
    1,3,customer_4,trendy,"[0.0,1.0]","[1.0,1.0]",trendy_rule,['customer_4'],['customer_4']
    2,4,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    2,4,customer_4,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_4', 'Car_4')]",['Car_4']
    2,4,customer_6,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_6', 'Car_4')]",['Car_4']
    2,4,customer_3,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_3', 'Pet_2')]",['Pet_2']
    2,4,customer_4,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_4', 'Pet_2')]",['Pet_2']
    2,5,customer_4,trendy,"[0.0,1.0]","[1.0,1.0]",trendy_rule,['customer_4'],['customer_4']
    3,6,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    3,6,customer_4,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_4', 'Car_4')]",['Car_4']
    3,6,customer_6,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_6', 'Car_4')]",['Car_4']
    3,6,customer_3,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_3', 'Pet_2')]",['Pet_2']
    3,6,customer_4,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_4', 'Pet_2')]",['Pet_2']
    3,7,customer_4,trendy,"[0.0,1.0]","[1.0,1.0]",trendy_rule,['customer_4'],['customer_4']
    4,8,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    4,8,customer_4,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_4', 'Car_4')]",['Car_4']
    4,8,customer_6,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_6', 'Car_4')]",['Car_4']
    4,8,customer_3,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_3', 'Pet_2')]",['Pet_2']
    4,8,customer_4,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_4', 'Pet_2')]",['Pet_2']
    4,9,customer_4,trendy,"[0.0,1.0]","[1.0,1.0]",trendy_rule,['customer_4'],['customer_4']
    5,10,popular-fac,popular-fac,"[0.0,1.0]","[1.0,1.0]",popular(customer_0),,
    5,10,customer_4,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_4', 'Car_4')]",['Car_4']
    5,10,customer_6,cool_car,"[0.0,1.0]","[1.0,1.0]",cool_car_rule,"[('customer_6', 'Car_4')]",['Car_4']
    5,10,customer_3,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_3', 'Pet_2')]",['Pet_2']
    5,10,customer_4,cool_pet,"[0.0,1.0]","[1.0,1.0]",cool_pet_rule,"[('customer_4', 'Pet_2')]",['Pet_2']
    5,11,customer_4,trendy,"[0.0,1.0]","[1.0,1.0]",trendy_rule,['customer_4'],['customer_4']

**Saved Edges Trace:**

The edges trace will be saved as another CSV file. It will contain the time, the edge relationship changes, and the clauses that were involved. Here’s a snippet of how the edge trace will look when saved:

.. code:: text

    Time,Fixed-Point-Operation,Edge,Label,Old Bound,New Bound,Occurred Due To,Clause-1,Clause-2
    0,1,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    0,1,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    0,1,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    0,1,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    0,1,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    0,1,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    0,1,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    0,1,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    0,1,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    0,1,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    0,1,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    1,3,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    1,3,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    1,3,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    1,3,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    1,3,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    1,3,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    1,3,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    1,3,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    1,3,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    1,3,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    1,3,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    2,5,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    2,5,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    2,5,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    2,5,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    2,5,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    2,5,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    2,5,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    2,5,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    2,5,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    2,5,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    2,5,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    3,7,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    3,7,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    3,7,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    3,7,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    3,7,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    3,7,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    3,7,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    3,7,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    3,7,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    3,7,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    3,7,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    4,9,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    4,9,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    4,9,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    4,9,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    4,9,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    4,9,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    4,9,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    4,9,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    4,9,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    4,9,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    4,9,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    5,11,"('customer_3', 'customer_1')",car_friend,"[0.0,1.0]","[1.0,1.0]",car_friend_rule,"[('customer_3', 'Car_0')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    5,11,"('customer_0', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    5,11,"('customer_0', 'customer_2')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]","[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]"
    5,11,"('customer_2', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_2', 'Car_1'), ('customer_2', 'Car_3'), ('customer_2', 'Car_11')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    5,11,"('customer_3', 'customer_1')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_1', 'Car_0'), ('customer_1', 'Car_8')]"
    5,11,"('customer_3', 'customer_4')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]","[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]"
    5,11,"('customer_4', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"
    5,11,"('customer_4', 'customer_5')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_4', 'Car_4'), ('customer_4', 'Car_9')]","[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]"
    5,11,"('customer_5', 'customer_3')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_3', 'Car_3'), ('customer_3', 'Car_0'), ('customer_3', 'Car_10')]"
    5,11,"('customer_5', 'customer_6')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_5', 'Car_5'), ('customer_5', 'Car_2')]","[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]"
    5,11,"('customer_6', 'customer_0')",same_color_car,"[0.0,1.0]","[1.0,1.0]",same_car_color_rule,"[('customer_6', 'Car_6'), ('customer_6', 'Car_4')]","[('customer_0', 'Car_2'), ('customer_0', 'Car_7')]"

---
