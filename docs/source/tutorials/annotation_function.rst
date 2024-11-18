PyReason Annotation Functions 
=============================

In this tutorial, we will look at use annotation functions in PyReason. 
Read more about annotation functions `here <https://pyreason--60.org.readthedocs.build/en/60/user_guide/3_pyreason_rules.html#annotation-functions>`_. 


.. note::
    Find the full, excecutable code `here <https://pyreason--60.org.readthedocs.build/en/60/examples_rst/annotation_function_example.html#annotation-function-example>`_


Average Annotation Function Example
------------------------------------
This example takes the average of the lower and higher bounds of the nodes in the graph.

Graph
------------

This example will use a graph created with 2 facts, and only 2 nodes. The annotation functions can be run on a graph of any size. See :ref:`PyReason Graphs <pyreason_graphs>` for more information on how to create graphs in PyReason.


Facts
------------
To initialize this graph, we will add 2 nodes ``P(A)`` and ``P(B)``, using ``add_fact``:

.. code:: python

    import pyreason as pr
    
    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
   



Annotation function
--------------------
Next, we will then add the annotation function to find the average of all the upper and lower bounds of the graph.

Here is the Average Annotation Function:

.. code:: python

    @numba.njit
    avg_ann_fn(annotations, weights):
        # annotations contains the bounds of the atoms that were used to ground the rule. It is a nested list that contains a list for each clause
        # You can access for example the first grounded atom's bound by doing: annotations[0][0].lower or annotations[0][0].upper

        # We want the normalised sum of the bounds of the grounded atoms
        sum_upper_bounds = 0
        sum_lower_bounds = 0
        num_atoms = 0
        for clause in annotations:
            for atom in clause:
                sum_lower_bounds += atom.lower
                sum_upper_bounds += atom.upper
                num_atoms += 1

        a = sum_lower_bounds / num_atoms
        b = sum_upper_bounds / num_atoms
        return a, b

This takes the annotations, or a list of the bounds of the grounded atoms and the weights of the grounded atoms, and returns the average of the upper and lower bounds repectivley. 

Next, we add this function in PyReason:

.. code:: python

    pr.add_annotation_function(avg_ann_fn)



Rules
------------
After we have created the graph, and added the annotation function, we add the annotation function to a Rule.

Create Rules of the general format when using an annotation function:

.. code:: text
    
    'average_function(A, B):avg_ann_fn <- P(A):[0, 1], P(B):[0, 1]'

The annotation function will be called when all clauses in the rule have been satisfied and the head of the rule is to be annotated.

.. code:: python

    pr.add_rule(pr.Rule('average_function(A, B):avg_ann_fn <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))


Running PyReason
-----------------
Begin the PyReason reasoning process with the added annotation function with:

.. code:: python

    interpretation = pr.reason(timesteps=1)


Expected Output
------------------
The expected output of this function is 

.. code:: python
    Timestep: 0

    Converged at time: 0
    Fixed Point iterations: 2
    TIMESTEP - 0
    component            average_function
    0    (A, B)  [0.10500000000000001, 1.0]

Where the lower bound of the head is now the average of the two lower bounds of the grounded atoms (0.01 and 0.2), and the upper bound is now the average of the lower bounds of the grounded atoms (1 and 1).



