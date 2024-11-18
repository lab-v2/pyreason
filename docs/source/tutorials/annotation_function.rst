PyReason Annotation Functions 
=============================

In this tutorial, we will look at use annotation functions in PyReason. 
Read more about annotation functions `here <https://pyreason--60.org.readthedocs.build/en/60/user_guide/3_pyreason_rules.html#annotation-functions>`_. 



Average Annotation Function Example
-----------------------------------
This example takes the average of the lower and higher bounds of the nodes in the graph.

.. note::
    Find the full, excecutable code `here <https://pyreason--60.org.readthedocs.build/en/60/examples_rst/annF_average.html#annotation-function-example>`_

Graph
^^^^^^^

This example will use a graph created with 2 facts, and only 2 nodes. The annotation functions can be run on a graph of any size. See :ref:`PyReason Graphs <pyreason_graphs>` for more information on how to create graphs in PyReason.


Facts
^^^^^^^
To initialize this graph, we will add 2 nodes ``P(A)`` and ``P(B)``, using ``add_fact``:

.. code:: python

    import pyreason as pr
    
    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
   



Average Annotation Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Next, we will then add the annotation function to find the average of all the upper and lower bounds of the graph.

Here is the Average Annotation Function:

.. code:: python

    @numba.njit
    def avg_ann_fn(annotations, weights):
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
^^^^^^^
After we have created the graph, and added the annotation function, we add the annotation function to a Rule.

Create Rules of the general format when using an annotation function:

.. code:: text
    
    'average_function(A, B):avg_ann_fn <- P(A):[0, 1], P(B):[0, 1]'

The annotation function will be called when all clauses in the rule have been satisfied and the head of the rule is to be annotated.

.. code:: python

    pr.add_rule(pr.Rule('average_function(A, B):avg_ann_fn <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))


Running PyReason
^^^^^^^^^^^^^^^^^^^^^
Begin the PyReason reasoning process with the added annotation function with:

.. code:: python

    interpretation = pr.reason(timesteps=1)


Expected Output
^^^^^^^^^^^^^^^^^^^^^
The expected output of this function is 

.. code:: python
    Timestep: 0

    Converged at time: 0
    Fixed Point iterations: 2
    TIMESTEP - 0
    component            average_function
    0    (A, B)  [0.10500000000000001, 1.0]

Where the lower bound of the head is now the average of the two lower bounds of the grounded atoms (0.01 and 0.2), and the upper bound is now the average of the lower bounds of the grounded atoms (1 and 1).




Linear Combination Annotation Function
----------------------------------------

Now, we will define and use a new annotation function to compute a weighted linear combination of the bounds of grounded atoms in a rule.

.. note::
    Find the full, excecutable code `here <https://pyreason--60.org.readthedocs.build/en/60/examples_rst/annF_average.html#annotation-function-example>`_


The `map_to_unit_interval` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We will first define a helper function that maps a value from the interval `[lower, upper]` to the interval `[0, 1]`. This will be used in the main annotation function to normalize the bounds:

.. code:: python

    @numba.njit
    def map_to_unit_interval(value, lower, upper):
        """
        Map a value from the interval [lower, upper] to the interval [0, 1].
        The formula is f(t) = c + ((d - c) / (b - a)) * (t - a),
        where a = lower, b = upper, c = 0, and d = 1.
        """
        if upper == lower:
            return 0  # Avoid division by zero if upper == lower
        return (value - lower) / (upper - lower)


Graph
^^^^^^^^^^^^^^^^^^^^^

This example will use a graph created with 2 facts, and only 2 nodes. The annotation functions can be run on a graph of any size. See :ref:`PyReason Graphs <pyreason_graphs>` for more information on how to create graphs in PyReason.


Facts
^^^^^^^^^^^^^^
To initialize this graph, we will add 2 nodes ``P(A)`` and ``P(B)``, using ``add_fact``:

.. code:: python

    import pyreason as pr
    
    pr.add_fact(pr.Fact('P(A) : [0.3, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
   


Linear Combination Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Next, we define the annotation function that computes a weighted linear combination of the mapped lower and upper bounds of the grounded atoms. The weights are applied to normalize the values.
For simplicity sake, we define the constant at 0.2 within the function, this is alterable for any constant.

.. code:: python

    @numba.njit
    def lin_comb_ann_fn(annotations, weights):
        sum_lower_comb = 0
        sum_upper_comb = 0
        num_atoms = 0
        constant = 0.2
        
        # Iterate over the clauses in the rule
        for clause in annotations:
            for atom in clause:
                # Map the atom's lower and upper bounds to the interval [0, 1]
                mapped_lower = map_to_unit_interval(atom.lower, 0, 1)
                mapped_upper = map_to_unit_interval(atom.upper, 0, 1)

                # Apply the weights to the lower and upper bounds, and accumulate
                sum_lower_comb += constant * mapped_lower
                sum_upper_comb += constant * mapped_upper
                num_atoms += 1

        # Return the weighted linear combination of the lower and upper bounds
        return sum_lower_comb, sum_upper_comb


Running the New Annotation Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We now run the new annotation function within the PyReason framework:

.. code:: text
    
    linear_combination_function(A, B):lin_comb_ann_fn <- P(A):[0, 1], P(B):[0, 1]

The annotation function will be called when all clauses in the rule have been satisfied and the head of the rule is to be annotated.

.. code:: python

    pr.add_rule(pr.Rule('linear_combination_function(A, B):lin_comb_ann_fn <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))


Expected Output
^^^^^^^^^^^^^^^^^^^^^
Below is the expected output from running the `linear_combination_annotation_function`:

.. code:: text

    Timestep: 0
    Converged at time: 0
    Fixed Point iterations: 2
    TIMESTEP - 0
    component linear_combination_function
    0    (A, B)                  [0.1, 0.4]

In this output:
- The lower bound of the `linear_combination_function(A, B)` is computed as `0.1`, based on the weighted combination of the lower bounds of `P(A)` (0.3) and `P(B)` (0.2), both multiplied by the constant then added together.
- The upper bound of the `linear_combination_function(A, B)` is computed as `0.4`, based on the weighted combination of the upper bounds of `P(A)` (1) and `P(B)` (1), both multiplied by the constant then added together.
