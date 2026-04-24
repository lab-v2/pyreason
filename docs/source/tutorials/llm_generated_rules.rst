LLM Generated PyReason Rules
============================

Introduction
------------
In this tutorial, we use a Large Language Model (Claude) to 
generate valid PyReason rules for a simple knowledge graph. We then
validate the generated rules with PyReason's rule parser and run inference
to show them fire on the graph.

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
The prompt instructs Claude to generate two PyReason rules and constrains output to a strict format.

.. code:: python

    PROMPT = """\
    Generate exactly 2 PyReason rules for this knowledge graph.

    ### Predicates in the graph
    - major_in(Student, Major)         — e.g., major_in(alice, math)
    - in_department(Major, Department) — e.g., in_department(math, math_dept)

    ### PyReason Rule Syntax
        head(X, Y) <-0 body1(...), body2(...)

    - Use `<-0` (rule fires immediately) or `<-1` (fires after 1 timestep)
    - Body predicates are separated by commas

    ### Variables are uppercase letters (X, Y, Z)

    ### Constraints
    - Each rule must have exactly 2 body predicates
    - Body predicates must share at least one variable (to create a meaningful join)
    - Use only the predicates listed above in the body
    - You may invent a new head predicate name

    ### Example (different graph, shows syntax only)
        grandparent(X, Y) <-0 parent(X, Z), parent(Z, Y)

    ### Output format
    Output only the 2 rules, one per line. No markdown, no explanation, no numbering.
    """

Generating Rules
----------------
We call the Anthropic API to send the prompt to Claude and split the response into individual rule string.

.. code:: python

    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
    )
    rules = [line.strip() for line in response.content[0].text.splitlines() if line.strip()]


A possible response looks like this: 

.. code:: text

    student_in_department(X, Z) <-0 major_in(X, Y), in_department(Y, Z)
    shares_department(X, Y) <-1 major_in(X, Z), major_in(Y, Z)

Validating Rules
----------------
Every rule is passed through ``pr.Rule()`` to confirm it is syntactically valid before loading it into the reasoner.

.. code:: python

    import pyreason as pr

    valid_rules = []
    for rule_str in rules:
        try:
            pr.Rule(rule_str)
            valid_rules.append(rule_str)
            print(f"  [VALID]   {rule_str}")
        except Exception as e:
            print(f"  [INVALID] {rule_str}  Error: {e}")

Running inference
-----------------
Load valid rules into PyReason with ``infer_edges=True`` so that new edges can be created when a rule head describes
a relationship between two currently unconnected nodes.

.. code:: python

    pr.load_graph(g)

    for i, rule_str in enumerate(valid_rules):
        pr.add_rule(pr.Rule(rule_str, name=f"rule_{i}", infer_edges=True))

    interpretation = pr.reason(timesteps=2)

    head_predicates = [r.split("(")[0].strip() for r in valid_rules]
    for df in pr.filter_and_sort_edges(interpretation, head_predicates):
        if not df.empty:
            print(df.to_string(index=False))

Cross-LLM Consistency
---------------------
The same prompt was tested against Claude, GPT-4 (ChatGPT), and Gemini 
through their web interfaces. All three produced valid rules with equivalent body structure:

.. code:: text

    Claude: student_in_department(X, Z) <-0 major_in(X, Y), in_department(Y, Z)
            shares_department(X, Y) <-1 major_in(X, Z), major_in(Y, Z)

    Gemini: student_in_department(X, Z) <-0 major_in(X, Y), in_department(Y, Z)
            classmate_in_major(X, Z) <-0 major_in(X, Y), major_in(Z, Y)

    ChatGPT: student_in_department(X, Y) <-0 major_in(X, Z), in_department(Z, Y)
             same_department(X, Y) <-1 major_in(X, Z), major_in(Y, Z)