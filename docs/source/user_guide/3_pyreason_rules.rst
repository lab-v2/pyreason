.. _pyreason_rules:

Rules
==============
This section outlines Rule creation and implementation. See :ref:`here <rule>` for more information on Rules in logic.

Creating a New Rule Object
--------------------------

In PyReason, rules are used to create or modify predicate bounds associated with nodes or edges in the graph if the conditions in the rule body are met.


Rule Parameters
~~~~~~~~~~~~~~~

To create a new **Rule** object in PyReason, use the ``Rule`` class with the following parameters:

#. ``rule_text`` **(str)**:
   The rule in textual format. It should define a head and body using the syntax 

   ``head <- body``, where the body can include predicates and optional bounds. See more on PyReason rule format :ref:`here <rule_formatting>`.

#. ``name`` **(str, optional)**:
   A name for the rule, which will appear in the explainable rule trace.

#. ``infer_edges`` **(bool, optional)**:
   Indicates whether new edges should be inferred between the head variables when the rule is applied:
   
   * If set to **True**, the rule will connect unconnected nodes when the body is satisfied.
   * Else, set to **False**, the rule will **only** apply for nodes that are already connected, i.e edges already present in the graph (Default).

#. ``set_static`` **(bool, optional)**:
   Indicates whether the atom in the head should be set as static after the rule is applied. This means the bounds of that atom will no longer change for the duration of the program.

#. ``custom_thresholds`` **(None, list, or dict, optional)**:
   A list or dictionary of custom thresholds for the rule.
   If not specified, default thresholds for ANY will be used. It can either be:

   - A list of thresholds corresponding to each clause.
   - A dictionary of thresholds mapping clause indices to specific thresholds.

#. ``weights`` **(None, numpy.ndarray, optional)**:
    A numpy array of weights for the rule passed to an annotation function. The weights can be used to calculate the annotation for the head of the rule. If not specified, the weights will default to 1 for each clause.


.. _rule_formatting:
Important Notes on Rule Formating: 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. The head of the rule is always on the left hand side of the rule.
2. The body of the rule is always on the right hand side of the rule.
3. You can include timestep in the rule by using the ``<-timestep`` body, if omitted, the rule will be applied with ``timestep=0``.
4. You can include multiple clauses in the rule by using the ``<-timestep clause1, clause2, clause3``. If bounds are not specified, they default to ``[1,1]``.
5. A tilde ``~`` can be used to negate a clause in the body of the rule, or the head itself.


Rule Structure
--------------
Example rule in PyReason with correct formatting:

.. code-block:: text

    head(x) : [1,1] <-1 clause1(y) : [1,1] , clause2(x,y) : [1,1] , clause3(y,z) : [1,1] , clause4(x,z) : [1,1]

which is equivalent to:

.. code-block:: text

    head(x) <-1 clause1(y), clause2(x,y), clause3(y,z), clause4(x,z)

The rule is read as follows: 

**Head**:

.. code-block:: text

    head(x) : [1,1]

**Body**:

.. code-block:: text

    clause1(x,y) : [1,1], clause2(y,z) : [1,1], clause3(x,z) : [1,1]


The **head** and **body** are separated by an arrow (``<-``), and the rule is applied to the head after ``1`` timestep if the body conditions are met.


Adding A Rule to PyReason
-------------------------
Add the rule directly
~~~~~~~~~~~~~~~~~~~~~~

To add the rule directly, we must specify the rule and (optionally) a name for it.

.. code-block:: python

    import pyreason as pr
    pr.add_rule(pr.Rule('head(x) <-1 body1(y), body2(x,y), body3(y,z), body4(x,z)', 'rule_name'))

The name helps understand which rules fired during reasoning later on.

Add the rule from a .txt file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add the rule from a text file, ensure the file is in .txt format, and contains the rule in the format shown above. This
allows for multiple rules to be added at once, with each rule on a new line. Comments can be added to the file using the ``#`` symbol, and will be ignored by PyReason.

    .. code-block:: text

        head1(x) <-1 body(y), body2(x,y), body3(y,z), body4(x,z)
        head2(x) <-1 body(y), body2(x,y), body3(y,z), body4(x,z)
        # This is a comment and will be ignored

Now we can load the rules from the file using the following code:

    .. code-block:: python

        import pyreason as pr
        pr.add_rules_from_file('rules.txt')

Annotation Functions
--------------------

What are annotation functions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Annotation Functions are specific user defined Python functions that are called when all clauses in a rule have been
satisfied to annotate (give bounds to) the head of the rule. Annotation functions have access to the bounds of grounded
atoms for each clause in the rule and users can use these bounds to make an annotation for the target of the rule.

The Structure of an annotation function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Only specifically structured annotation functions are allowed. The function has to be

#. decorated with ``@numba.njit``
#. has to take in 2 parameters whether you use them or not
#. has to return 2 numbers

**Example User Defined Annotation Function:**



.. code-block:: python

    import numba
    import numpy as np

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


This annotation function calculates the average of the bounds of all grounded atoms in the rule. The function is decorated
with ``@numba.njit`` to ensure that it is compiled to machine code for faster execution. The function takes in two parameters,
``annotations`` and ``weights``, which are the bounds of the grounded atoms and the weights associated with each clause of the rule set by the user when the rule is added.
The function returns two numbers, which are the lower and upper bounds of the annotation for the head of the rule.

Adding an Annotation Function to a PyReason Rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the following to add an annotation function into pyreason so that it can be used by rules

.. code-block:: python

    import pyreason as pr
    pr.add_annotation_function(avg_ann_fn)

Then you can create rules of the following format:

.. code-block:: text

    head(x) : avg_ann_fn <- clause1(y), clause2(x,y), clause3(y,z), clause4(x,z)

The annotation function will be called when all clauses in the rule have been satisfied and the head of the rule is to be annotated.
The ``annotations`` parameter in the annotation function will contain the bounds of the grounded atoms for each of the 4 clauses in the rule.

Head Functions and Functional Arguments
---------------------------------------

PyReason also supports applying user-defined functions directly within the **arguments of a rule head**. These head functions make it
possible to transform the node or edge identifiers that will receive the rule's annotation. Common use cases include normalising IDs,
mapping relationships, or selecting a subset of grounded nodes before the head is produced.

Registering a Head Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Head functions, just like annotation functions, must be compiled with ``numba.njit`` and registered with PyReason before they can be
used by rules. A head function receives a list of grounded variable bindings (each binding is a ``numba.typed.List`` of strings) and
returns a new list containing the head substitutions that should be produced for that argument.

.. code-block:: python

    import numba
    import pyreason as pr

    @numba.njit
    def identity_func(groundings):
        """
        Return the same grounded values that were passed in.
        `groundings` is a list where each element is the list of nodes bound to a variable.
        For example, if the rule body binds ``X`` to ``[a, b]`` and ``Y`` to ``[c, d]``, 
        then ``groundings`` will be ``[[a, b], [c, d]]``.
        """
        return numba.typed.List([groundings[0][0]])

    pr.add_head_function(identity_func)

Using Functions in the Rule Head
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once registered, a head function can be referenced in the textual rule by replacing a head argument with a function call. The parser
automatically rewrites the argument to use an internal placeholder variable and associates the call with the registered function.

.. code-block:: text

    Processed(identity_func(X)) <- property(X), property(Y), connected(X, Y)

During grounding, the rule body binds ``X`` and ``Y`` exactly as usual. Before emitting the head atom, PyReason invokes
``identity_func`` with the grounded values for ``X`` (and any additional arguments if the function requires them). The function's return
value determines which nodes (or edges) will receive the ``Processed`` label.

Edge Rules with Head Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Head functions may be used for either argument of an edge rule. Each head argument is handled independently, so you can transform the
source, the target, or both.

.. code-block:: text

    Route(identity_func(A), B) <- property(X), property(Y), connected(X, Y)
    Path(A, identity_func(B)) <- property(X), property(Y), connected(X, Y)
    Link(identity_func(A), identity_func(B)) <- property(X), property(Y), connected(X, Y)

In the example above, every head argument that uses ``identity_func`` will receive the transformed grounding returned by the function.
If both arguments reference a function, each function call is resolved separately before the head edge is emitted.

Guidelines and Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Head functions must be decorated with ``@numba.njit`` so that they can execute inside PyReason's JIT-compiled reasoning loop.
* Each argument supplied to the function corresponds to a grounded variable from the rule body; that argument is represented as a
  ``numba.typed.List`` of strings containing all candidate nodes for that variable.
* The function must return a ``numba.typed.List`` of strings that represent the substituted values for the head argument.
* Multiple head functions can be registered, and you can mix plain variables and function calls within the same rule head.
* If you need the original grounding unchanged, simply return it from the function (as shown in ``identity_func``).

By leveraging head functions you can encapsulate common transformations and keep your rule text concise while still benefitting from
PyReason's compiled execution path.


Custom Thresholds
-----------------

Custom thresholds allow you to specify specific thresholds for the clauses in the body of the rule. By default, with no
custom thresholds specified, the rule will use the default thresholds for ANY. Custom thresholds can be specified as:

1. A list of thresholds corresponding to each clause. Where the size of the list should be equal to the number of clauses in the rule.
2. A dictionary of thresholds mapping clause indices to specific thresholds. The first clause has an index of 0.

The Threshold Class
~~~~~~~~~~~~~~~~~~~
PyReason's ``Threshold`` class is used to define custom thresholds for a rule. The class has the following parameters:

#. ``quantifier`` **(str)**: "greater_equal", "greater", "less_equal", "less", "equal"
#. ``quantifier_type`` **(tuple)**: A tuple of two elements indicating the type of quantifier, where the first is either ``"number"`` or ``"percent"``
and the second is either ``"total"`` or ``"available"``. ``"total"`` refers to all groundings of the clause, while ``"available"`` refers to the groundings that have the predicate of the clause.
#. ``thresh`` **(int)**: The value of the threshold

An example usage can be found :ref:`here <custom_thresholds_tutorial>`.
