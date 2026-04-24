Load Rules and Facts From File
==================================

Introduction
------------
Loading facts and rules from files is crucial for practical PyReason usage. 
It provides scalability for large rule sets, reusability across projects, 
and allows non-programmers to edit domain knowledge without touching Python code.

In this tutorial, we will focus on four functions that load facts and rules 
from CSV or JSON files: ``add_fact_from_csv``, ``add_fact_from_json``, 
``add_rule_from_csv``, and ``add_rule_from_json``.

.. note:: 
   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/load_rules_facts_from_file_ex.py>`_

Graph
----------------------
Let's build a simple student-major-department knowledge graph. Alice, Bob, 
and Mary are students — Alice and Bob enroll in the math major, while Mary 
enrolls in CS. Each major belongs to a department: math belongs to the math 
department, and CS belongs to the CS department.

.. code:: python

    import networkx as nx

    # A simple student/major/department knowledge graph

    g = nx.DiGraph()
    student_names = ['alice', 'bob', 'mary']
    g.add_nodes_from(student_names)

    majors = ['math', 'cs']
    g.add_nodes_from(majors)

    departments = ['math_dept', 'cs_dept']
    g.add_nodes_from(departments)

    g.add_edge('alice', 'math', enroll=1)
    g.add_edge('bob', 'math', enroll=1)
    g.add_edge('mary', 'cs', enroll=1)

    g.add_edge('math', 'math_dept', in_department=1)
    g.add_edge('cs', 'cs_dept', in_department=1)


Load Rules from CSV 
----------------------
Rules can be loaded from a CSV file. Each row has four columns:
``rule_text``, ``name``, ``infer_edges``, ``set_static``.

.. code:: text

    rule_text,name,infer_edges,set_static
    "under_department(X,Y) <-0 enroll(X,Z), in_department(Z,Y)",under_department_rule,true,false

Note: when the rule text contains a comma, wrap the whole field in quotes.

Then load the file using:

.. code:: python

    import pyreason as pr
    pr.add_rule_from_csv('examples/rules.csv')

Load Rules from JSON
-----------------------
Rules can also be loaded from a JSON file. The JSON should be array of objects.
Example: 

.. code:: text

    [
        {
            "rule_text": "under_department(X,Y) <-0 enroll(X,Z), in_department(Z,Y)",
            "name": "under_department_rule",
            "infer_edges": true,
            "set_static": false
        },    
        {
            "rule_text": "eligible(X) <-1 under_department(X,Y), scholarship(Y)",
            "name": "eligible_scholarship_rule",
            "infer_edges": false,
            "set_static": false
        }
    ]

Then load the file using:

.. code:: python

    pr.add_rule_from_json('examples/rules.json')

Loading Facts from CSV
----------------------
Facts can be loaded from a CSV file. Each row should have up to 5 comma-separated values in this order: ``fact_text, name, start_time, end_time, static``.

.. code:: text

    fact_text,name,start_time,end_time,static
    scholarship(math_dept),scholarship_math_dept,0,2,False

Then load the file using:

.. code:: python

    pr.add_fact_from_csv('examples/facts.csv')

Loading Facts from JSON
-----------------------
Facts can also be loaded from a JSON file. The JSON should be an array of objects. 
Example:

.. code:: text

    [
        {
            "fact_text": "scholarship(math_dept)",
            "name": "scholarship_math_dept",
            "start_time": 0,
            "end_time": 2,
            "static": false
        }
    ]

Then load the file using:

.. code:: python

    pr.add_fact_from_json('examples/facts.json')


Running PyReason
----------------

After loading the graph, rules, and facts using any combination of the 
four loading functions above, run the reasoning:

.. code:: python

    interpretation = pr.reason(timesteps=2)
    dataframes = pr.filter_and_sort_nodes(interpretation, ['eligible'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

Expected Output
---------------
.. code::


    TIMESTEP - 0
    Empty DataFrame
    Columns: [component, eligible]
    Index: []

    TIMESTEP - 1
      component    eligible
    0     alice  [1.0, 1.0]
    1       bob  [1.0, 1.0]

    TIMESTEP - 2
      component    eligible
    0     alice  [1.0, 1.0]
    1       bob  [1.0, 1.0]

At timestep 1, ``alice`` and ``bob`` become eligible because they are in 
``math_dept`` and ``math_dept`` has a scholarship. ``mary`` is not eligible 
because ``cs_dept`` has no scholarship fact.


Further Details
---------------

For a complete description of parameters and advanced features (such as 
``custom_thresholds``, ``weights``, error handling with ``raise_errors``), 
see the full API reference in `pyreason.py 
<https://github.com/lab-v2/pyreason/blob/main/pyreason/pyreason.py#L868>`_.
