PyReason Annotation Functions 
=============================

In this tutorial, we will look at use annotation functions in PyReason. 
Read more about annotation functions `here <https://pyreason.readthedocs.io/en/latest/user_guide/3_pyreason_rules.html#annotation-functions>`_.

.. note::
    Find the full, executable code for both annotation functions `here <https://github.com/lab-v2/pyreason/blob/main/examples/annotation_function_ex.py>`_


Average Annotation Function Example
-----------------------------------
This example takes the average of the lower and higher bounds of the nodes in the graph.

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

Create Rules of this general format when using an annotation function:

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

.. code:: text
    
    Timestep: 0
    Converged at time: 0
    Fixed Point iterations: 2
    TIMESTEP - 0
    component            average_function
    0    (A, B)  [0.10500000000000001, 1.0]

In this output:
    - The lower bound of the ``avg_ann_fn(A, B)`` is computed as ``0.105``, based on the weighted combination of the lower bounds of ``P(A)`` (0.01) and ``P(B)`` (0.2), averaged together.
    - The upper bound of the ``linear_combination_function(A, B)`` is computed as ``0.4``, based on the weighted combination of the upper bounds of ``P(A)`` (1.0) and ``P(B)`` (1.0), averaged together.



Linear Combination Annotation Function
----------------------------------------

Now, we will define and use a new annotation function to compute a weighted linear combination of the bounds of grounded atoms in a rule.


The `map_interval` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We will first define a helper function that maps a value from the interval `[lower, upper]` to the interval `[0, 1]`. This will be used in the main annotation function to normalize the bounds:

.. code:: python

    @numba.njit
    def map_interval(t, a, b, c, d):
        """
        Maps a value `t` from the interval [a, b] to the interval [c, d] using the formula:
        
            f(t) = c + ((d - c) / (b - a)) * (t - a)
        
        Parameters:
        - t: The value to be mapped.
        - a: The lower bound of the original interval.
        - b: The upper bound of the original interval.
        - c: The lower bound of the target interval.
        - d: The upper bound of the target interval.
        
        Returns:
        - The value `t` mapped to the new interval [c, d].
            """
        # Apply the formula to map the value t
        mapped_value = c + ((d - c) / (b - a)) * (t - a)
        
        return mapped_value


Graph
^^^^^^^^^^^^^^^^^^^^^

This example will use a graph created with 2 facts, and only 2 nodes. The annotation functions can be run on a graph of any size. See :ref:`PyReason Graphs <pyreason_graphs>` for more information on how to create graphs in PyReason.


Facts
^^^^^^^^^^^^^^
To initialize this graph, we will add 3 nodes ``A``, ``B``, and ``C``, using ``add_fact``:

.. code:: python

    import pyreason as pr
    
    pr.add_fact(pr.Fact('A : [.1, 1]')) 
    pr.add_fact(pr.Fact('B : [.2, 1]'))  
    pr.add_fact(pr.Fact('C : [.4, 1]'))
   


Linear Combination Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Next, we define the annotation function that computes a weighted linear combination of the mapped lower and upper bounds of the grounded atoms. The weights are applied to normalize the values.
For simplicity sake, we define the constant at 0.2 within the function, this is alterable for any constant, or for the weights in the graph.

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
            
            # Apply the constant weight to the lower and upper bounds, and accumulate
            sum_lower_comb += constant * atom.lower
            sum_upper_comb += constant * atom.upper
            num_atoms += 1

    
    #if the lower and upper are equal, return [0,1]
    if sum_lower_comb == sum_upper_comb:
        return 0,1
    
    if sum_lower_comb> sum_upper_comb:
        sum_lower_comb,sum_upper_comb= sum_upper_comb, sum_lower_comb

    if sum_upper_comb>1:
        sum_lower_comb = map_interval(sum_lower_comb, sum_lower_comb, sum_upper_comb, 0,1)

        sum_upper_comb = map_interval(sum_upper_comb, sum_lower_comb, sum_lower_comb,0,1)

    # Return the weighted linear combination of the lower and upper bounds
    return sum_lower_comb, sum_upper_comb



We now add the new annotation function within the PyReason framework:

.. code:: python
    
    # Register the custom annotation function with PyReason
    pr.add_annotation_function(lin_comb_ann_fn)


Rules
^^^^^^^
After we have created the graph, and added the annotation function, we add the annotation function to a Rule.

Create Rules of this general format when using an annotation function:

.. code:: text
    
    linear_combination_function(A, B):lin_comb_ann_fn <- A:[0, 1], B:[0, 1], C:[0, 1]


.. code:: python

    pr.add_rule(pr.Rule('linear_combination_function(A, B):lin_comb_ann_fn <- A:[0, 1], B:[0, 1], C:[0, 1]', infer_edges=True))

The annotation function will be called when all clauses in the rule have been satisfied and the head of the Rule is to be annotated.

Running PyReason
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Begin the PyReason reasoning process with the added annotation function with:

.. code:: python

    interpretation = pr.reason(timesteps=1)


Expected Output
^^^^^^^^^^^^^^^^^^^^^
Below is the expected output from running the ``linear_combination_annotation_function``:

.. code:: text

    Timestep: 0

    Converged at time: 0
    Fixed Point iterations: 2
    TIMESTEP - 0
    component                linear_combination_function
    0    (A, B)  [0.24000000000000005, 0.6000000000000001]

In this output:
    - The lower bound of the ``linear_combination_function(A, B, C)`` is computed as ``0.24000000000000005``, based on the weighted combination of the lower bounds of ``A`` (0.1), ``B`` (0.2), and ``C`` (0.4)  multiplied by the constant(0.2) then added together.
    - The upper bound of the ``linear_combination_function(A, B, C)`` is computed as ``0.6000000000000001``, based on the weighted combination of the upper bounds of ``A`` (1), ``B`` (1), and ``C`` (1)  multiplied by the constant(0.2) then added together.
