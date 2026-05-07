LLM Generated PyReason Rules
============================

Introduction
------------
In this tutorial, we use a Large Language Model (Claude) to 
generate a valid PyReason rule for a simple knowledge graph. We then
validate the generated rule with PyReason's rule parser and run inference
to show it fires on the graph.

.. note:: 
   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/llm_generated_rules_ex.py>`_

Knowledge Graph
---------------
We build a small academic knowledge graph with three types of nodes - students, majors, and departments.
They are connected by two predicates: ``major_in`` and ``in_department``.

.. code:: python

    import networkx as nx
    g = nx.DiGraph()

    g.add_edge('alice', 'math', major_in=1)
    g.add_edge('bob',   'math', major_in=1)
    g.add_edge('mary',  'cs',   major_in=1)

    # Major -> Department
    g.add_edge('math', 'math_dept', in_department=1)
    g.add_edge('cs',   'cs_dept',   in_department=1)

The Prompt
----------
The prompt describes a specific reasoning goal: deriving which department a student belongs to.
The head predicate name is fixed to ensure consistent, comparable output across LLMs.

.. code:: python

    PROMPT = """\
    You are generating a rule for a PyReason knowledge graph.

    ### Task
    Write a single PyReason rule that derives which department a student belongs to,
    given that a student is enrolled in a major and that major belongs to a department.

    ### Available predicates
    - major_in(Student, Major) - student in enrolled in a major
    - in_department(Major, Department) - major belongs to a department

    ### PyReason rule syntax
    head_predicate(X,Y) <-N body_predicate_1(X,Z),body_predicates_2(Z,Y)

    - N is the delta: use 0 for immediate firing
    - Variables are single uppercase letters (X,Y,Z)
    - Head predicate name must be: student_in_dept

    ### Output format
    Output the rule on a single line. No explanation, no markdown, no punctuation.

    ### Example (Different predicates, shows syntax only)
    grandparent(X,Y)<-0 parent(X,Z),parent(Z,Y)
    """

Generating the Rule
-------------------
We call the Anthropic API to send the prompt to Claude and split the response into individual rule string.

.. code:: python

    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{"role": "user", "content": PROMPT}],
    )

    rule_str = response.content[0].text.strip()


A typical response looks like:

.. code:: text

    student_in_dept(X,Y)<-0 major_in(X,Z),in_department(Z,Y)

Validating the Rule
-------------------
The rule is passed through ``pr.Rule()`` to confirm it is syntactically valid 
before loading it into the reasoner. If invalid, the script exits immediately.

.. code:: python

    import pyreason as pr

    try:
        pr.Rule(rule_str)
        print(f"[VALID] {rule_str}")
    except Exception as e:
        sys.exit(f"[INVALID] {rule_str}\nError: {e}")

Running inference
-----------------
Load the valid rule into PyReason with ``infer_edges=True`` so that new edges 
are created when the rule fires between currently unconnected nodes.

.. code:: python

    pr.settings.verbose = False
    pr.load_graph(g)
    pr.add_rule(pr.Rule(rule_str, name="student_in_dept_rule", infer_edges=True))

    interpretation = pr.reason(timesteps=2)

    print("\nInferred student-department relationships:")
    for df in pr.filter_and_sort_edges(interpretation, ["student_in_dept"]):
        if not df.empty:
            print(df.to_string(index=False))

Expected output:

.. code:: text

    Inferred student-department relationships:
                component   student_in_dept
    0   (alice, math_dept)      [1.0, 1.0]
    1   (bob,   math_dept)      [1.0, 1.0]
    2     (mary,  cs_dept)      [1.0, 1.0]


Cross-LLM Consistency
---------------------
The same prompt was tested against Claude, GPT-4, and Gemini through their 
web interfaces. All three produced the same valid rule:

.. code:: text

    Claude:  student_in_dept(X,Y)<-0 major_in(X,Z),in_department(Z,Y)
    GPT-4:   student_in_dept(X,Y)<-0 major_in(X,Z),in_department(Z,Y)
    Gemini:  student_in_dept(X,Y)<-0 major_in(X,Z),in_department(Z,Y)

This demonstrates that a well-constrained prompt consistently produces identical, 
valid PyReason rules across different LLMs.