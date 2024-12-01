Jupyter Notebook Usage
===========================

.. warning::
Using PyReason in a Jupyter Notebook can be a little tricky. And it is recommended to run PyReason in a normal python file.
However, if you want to use PyReason in a Jupyter Notebook, make sure you understand the points below.


1. When using functions like ``add_rule`` or ``add_fact`` in a Jupyter Notebook, make sure to run the cell only once. Running the cell multiple times will add the same rule/fact multiple times. It is recommended to store all the rules and facts in an array and then add them all at once in one cell towards the end
2. Functions like ``load_graph`` and ``load_graphml`` which are run multiple times can also have the same issue. Make sure to run them only once.

