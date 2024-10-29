PyReason Rules
==============
-  A rule is a statement that establishes a relationship between
   premises and a conclusion, allowing for the derivation of the
   conclusion if the premises are true. Rules are foundational to
   logical systems, facilitating the inference process. 

-  Every rule has a head and a body. The head determines what will
   change in the graph if the body is true.

Creating a New Rule Object
--------------------------

In PyReason, rules are used to create or modify predicate values associated with nodes or edges in the graph if the conditions in the rule body are met.


Rule Parameters
~~~~~~~~~~~~~~~

To create a new **Rule** object in PyReason, use the `Rule` class with the following parameters:

1. **rule_text** (str): 
   The rule in textual format. It should define a head and body using the syntax 

   `head <- body`, where the body can include predicates and optional bounds.

2. **name** (str): 
   A name for the rule, which will appear in the explainable rule trace.

3. **infer_edges** (bool, optional): 
   Indicates whether new edges should be inferred between the head variables when the rule is applied:
   
   - If set to **True**, the rule will connect unconnected nodes when the body is satisfied.
   - Else, set to **False**, the rule will **only** apply for nodes that are already connected, i.e edges already present in the graph (Default).

4. **set_static** (bool, optional): 
   Indicates whether the atom in the head should be set as static after the rule is applied. This means the bounds of that atom will no longer change for the duration of the program.

5. **custom_thresholds** (None, list, or dict, optional):
   A list or dictionary of custom thresholds for the rule.
   If not specified, default thresholds for ANY will be used. It can either be:

   - A list of thresholds corresponding to each clause.
   - A dictionary of thresholds mapping clause indices to specific thresholds.


Important Notes on Rule Formating: 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. The head of the rule is always on the left hand side of the rule.
2. The body of the rule is always on the right hand side of the rule.
3. You can include timestep in the rule by using the `<-timestep` body, if omitted, the rule will be applied with `timestep=0`.
4. You can include multiple clauses in the rule by using the `<-timestep clause1, clause2, clause3`. If bounds are not specified, they default to `[1,1]`.
5. A tilde `~` can be used to negate a clause in the body of the rule, or the head itself.


Rule Structure
--------------
Example rule in PyReason with correct formatting:

    .. code:: text

        head(x) : [1,1] <-1 clause1(y) : [1,1] , clause2(x,y) : [1,1] , clause3(y,z) : [1,1] , clause4(x,z) : [1,1]

The rule is read as follows: 

**Head**:

    .. code:: text

        head(x) : [1,1]

**Body**:

    .. code:: text

        clause1(x,y) : [1,1], clause2(y,z) : [1,1], clause3(x,z) : [1,1]


- The **head** and **body** are separated by an arrow (`<-`), and the rule is applied after `1` timestep.


Adding A Rule to PyReason
-------------------------
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


Rule Parsing
~~~~~~~~~~~~
Rule parser take in rule_text, name, custom_thresholds, infer_edges, set_static, and immediate_rule as input and reads the rule as follows:

1. Extract *delta_t* of rule if it exists, else, set it to 0
2. Add :[1,1] or :[0,0] to the end of each element if a bound is not specified
3. Check if there are custom thresholds for the rule such as forall in string form
4. Transform bound strings into pr.intervals
5. Find the target predicate, bounds, and annotation function if any.
6. Assign type of rule  

    - if one head variable -> 'node' type

    - else, 'edge' type

7. Get the variables in the body, if there's an operator in the body then discard anything that comes after the operator, but keep the variables
8. Create array of *thresholds* to keep track of for each neighbor criterion.

    .. code:: text

        thresholds = [(comparison, (number/percent, total/available), thresh)]

9. Create array to store clauses for nodes or edges: 

    .. code:: text

        clauses = node/edge, [subset]/[subset1, subset2], label, interval, operator

    - The length clauses array should be equal to custom_thresholds

10. Add edges between head variables if necessary
11. Returns Rule Object
    
    .. code:: python

        rule = rule.Rule(name, rule_type, target, head_variables, numba.types.uint16(t), clauses, target_bound, thresholds, ann_fn, weights, edges, set_static, immediate_rule)
        return rule



