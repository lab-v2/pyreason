Understanding Key Concepts
==========================

RULE
~~~~

-  A rule is a statement that establishes a relationship between
   premises and a conclusion, allowing for the derivation of the
   conclusion if the premises are true. Rules are foundational to
   logical systems, facilitating the inference process. |rule_image|
-  Every rule has a head and a body. The head determines what will
   change in the graph if the body is true.

FACT
~~~~

-  A fact is a statement that is true in the graph. It is a basic unit
   of knowledge that is used to derive new information.
-  Facts are used to initialize the graph and are the starting point for
   reasoning.

ANNOTATED ATOM / FUNCTION
~~~~~~~~~~~~~~~~~~~~~~~~~
- An annotated atom or function in logic, refers to an atomic formula (or a simple predicate) that is augmented with additional information, such as a certainty factor, a probability, or other annotations that provide context or constraints.

INTERPRETATION
~~~~~~~~~~~~~~
- An interpretation is a mapping from the set of atoms to the set of truth values. It is a way of assigning truth values to the atoms in the graph.

FIXED POINT OPERATOR
~~~~~~~~~~~~~~~~~~~~

- In simple terms, a fixed point operator is a function that says if you have a set of atoms,
  return that set plus any atoms that can be derived by a single application of a rule in the program.


INCONSISTENT PREDICATE LIST
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- A logic program is consistent if there exists an interpretation that satisfies the logic program, i.e., makes all the rules true. If no such interpretation exists, the logic program is inconsistent. An inconsistent predicate list is a list of predicates that are inconsistent with each other.
- An example of an inconsistent predicate list is:

.. code-block::

  r1: grass_wet <- rained,
  r2: ~ grass_wet <- rained,
  f1: rained <-

- The above example is inconsistent because it contains two rules that are inconsistent with each other.
  The first rule states that the grass is wet if it rained, while the second rule states that the grass is not wet if it rained.
  The fact f1 states that it rained, which is consistent with the first rule, but inconsistent with the second rule.

.. |rule_image| image:: Rule_image.png
