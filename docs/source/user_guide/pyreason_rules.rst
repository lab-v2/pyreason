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

How to Create Rules
-------------------

In PyReason, rules are used to create relationships between different elements in the graph. These relationships can be used to infer new facts or make decisions based on existing graph data. 


### PyReason Rule Class

To create a new **Rule** object in PyReason, use the `Rule` class with the following parameters:

1. **rule_text**: The rule in textual format (the actual rule logic).
2. **name**: A name for the rule. This name will appear in the rule trace.
3. **infer_edges**: A boolean indicating whether new edges should be inferred when the rule is applied.
4. **set_static**: A boolean indicating whether the atom in the head should be set as static after the rule is applied. This means the bounds of that atom will no longer change.
5. **immediate_rule**: A boolean indicating whether the rule is immediate. Immediate rules check for more applicable rules immediately after being applied.
6. **custom_thresholds**: A list or map of custom thresholds for the rule. If not specified, default thresholds for ANY are used. This can be a list of thresholds, or a map of clause index to threshold.




Important Notes on Rule Formating: 

1. The head of the rule is always on the left hand side of the rule.
2. The body of the rule is always on the right hand side of the rule.
3. You can include timestep in the rule by using the `<-timestep` body.
4. You can include multiple bodies in the rule by using the `<-timestep body1, body2, body3`.
5. To compare two nodes, both the nodes should have an attribute in common.
    1. For example using the :ref:`pyreason_graphs.rst` example, in the rule below, both the people have an attribute 'Friends' in common which is the friends in the graph.
    2. So, we can compare the Friends status of both the customers to check if they are the Friends or not.

    .. code-block:: python
        pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y)'))

6. To compare a particular attribute of a node with another node, you need to use the attribute like attribute "owns" is used here. 
    1. Note that nodes can be attributes themeselves, and thus refered to by node name
    .. code-block:: python
        pr.add_rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule')


More Examples
-------------

Refering to our :ref:`pyreason_graphs.rst` example, we want to create a rule to determine popularity. The rule will state that if a person has a friend who is popular *and* has the same pet as they do, then they are popular.

    .. code:: text

        popular(x) : [1,1] <-1 popular(y) : [1,1] , Friends(x,y) : [1,1] , owns(y,z) : [1,1] , owns(x,z) : [1,1]

The rule is read as follows: 

- **Head**: `popular(x) : [1,1]`

- **Body**: `popular(y) : [1,1], Friends(x,y) : [1,1], owns(y,z) : [1,1], owns(x,z) : [1,1]`

- The **head** and **body** are separated by an arrow (`<-1`), and the rule is applied after `1` timestep.


### Adding the Rule to PyReason

1. Add the rule directly

To add the rule directly, we must specify the rule and a name for it. Here we will use "popular_rule".

    .. code:: python

        import pyreason as pr
        pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))

The name helps understand which rules fired during reasoning later on.

2. Add the rule from a .txt file

To add the rule from a text file, ensure the file is in .txt format, and contains the rule in the format shown above.

    .. code:: text

        popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)

Now we can load the rule from the file using the following code:

    .. code:: python

        import pyreason as pr
        pr.add_rules_from_file('rules.txt')


