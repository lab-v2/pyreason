PyReason Rules
==============
-  A rule is a statement that establishes a relationship between
   premises and a conclusion, allowing for the derivation of the
   conclusion if the premises are true. Rules are foundational to
   logical systems, facilitating the inference process. 

.. figure:: docs/source/tutorials/rule_image.png
   :alt: image

-  Every rule has a head and a body. The head determines what will
   change in the graph if the body is true.

Creating a New Rule Object
--------------------------

In PyReason, rules are used to create relationships between different elements in the graph. These relationships can be used to infer new facts or make decisions based on existing graph data. 


Rule Parameters
~~~~~~~~~~~~~~~


To create a new **Rule** object in PyReason, use the `Rule` class with the following parameters:

1. **rule_text (str)**: The rule in textual format (the actual rule logic).

2. **name (str)**: A name for the rule, which will appear in the rule trace.

3. **infer_edges (bool)**: Indicates whether new edges should be inferred when the rule is applied:
   - If set to **True**, it will connect unconnected nodes and fire.
   - If set to **False**, it will fire **only** for rules that are already connected.

4. **set_static (bool)**: Indicates whether the atom in the head should be set as static after the rule is applied. This means the bounds of that atom will no longer change.

5. **immediate_rule (bool)**: Indicates whether the rule is immediate. Immediate rules check for more applicable rules immediately after being applied.

6. **custom_thresholds (list)**: A list or map of custom thresholds for the rule. If not specified, default thresholds for **ANY** are used. This can be either a list of thresholds or a map of clause index to threshold.




Important Notes on Rule Formating: 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. The head of the rule is always on the left hand side of the rule.
2. The body of the rule is always on the right hand side of the rule.
3. You can include timestep in the rule by using the `<-timestep` body.
4. You can include multiple clauses in the rule by using the `<-timestep body1, body2, body3`.


More Examples
-------------

Refering to our :ref:`pyreason_graphs.rst` example, we want to create a rule to determine popularity. The rule will state that if a person has a friend who is popular *and* has the same pet as they do, then they are popular.

    .. code:: text

        head(x) : [1,1] <-1 body1(y) : [1,1] , body2(x,y) : [1,1] , body3(y,z) : [1,1] , body4(x,z) : [1,1]

The rule is read as follows: 

**Head**:

.. code:: text

    head(x) : [1,1]

**Body**:

.. code:: text

    head(y) : [1,1], body1(x,y) : [1,1], body2(y,z) : [1,1], body3(x,z) : [1,1]


- The **head** and **body** are separated by an arrow (`<-1`), and the rule is applied after `1` timestep.


Adding A Rule to PyReason
~~~~~~~~~~~~~~~~~~~~~~~~~
1. Add the rule directly

To add the rule directly, we must specify the rule and a name for it. Here we will use "popular_rule".

    .. code:: python

        import pyreason as pr
        pr.add_rule(pr.Rule('head(x) <-1 body1(y), body2(x,y), body3(y,z), body4(x,z)', 'rule_name'))

The name helps understand which rules fired during reasoning later on.

2. Add the rule from a .txt file

To add the rule from a text file, ensure the file is in .txt format, and contains the rule in the format shown above.

    .. code:: text

        head(x) <-1 body(y), body2(x,y), body3(y,z), body4(x,z)

Now we can load the rule from the file using the following code:

    .. code:: python

        import pyreason as pr
        pr.add_rules_from_file('rules.txt')


