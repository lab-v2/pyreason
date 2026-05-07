Natural Language to PyReason
==============================
 
This tutorial shows how to convert a plain English paragraph into PyReason
facts and rules using a local AI model, then validate the output.
 
.. note::
   Find the full, executable code at `here <https://github.com/lab-v2/pyreason/blob/main/examples/natural_language_to_pyreason_ex.py>`_
 
The following paragraph is used as our example:
 
   *"John and Mary are both students. All students who study regularly tend to
   perform well academically. Mary studies regularly. Anyone who performs well
   academically is likely to graduate. John does not study regularly."*
 
Setup
-----
 
1. Download and install **Ollama** from https://ollama.com/download
 
2. Pull a local model:
 
   .. code:: bash
 
      ollama pull llama3.1:8b
 
3. Install the required packages:
 
   .. code:: bash
 
      pip install ollama pyreason
 
Paragraph
---------
 
The paragraph is stored as a Python string at the top of the script:
 
.. code:: python
 
   paragraph = (
       "John and Mary are both students. "
       "All students who study regularly tend to perform well academically. "
       "Mary studies regularly. Anyone who performs well academically is likely to graduate. "
       "John does not study regularly."
   )
 
Step 1 — Extract Facts and Rules in English
--------------------------------------------
 
The first prompt asks the AI to read the paragraph and separate it into
**facts** (specific statements about named people or things) and
**rules** (general patterns that apply to anyone).
 
.. code:: python
 
   PROMPT_EXTRACT = f"""Read the paragraph below and extract two things.
   FACTS: specific statements about a named person, place, or thing.
     - Include negative facts too (e.g. "John does not study regularly")
     - Only extract what is explicitly stated, do not assume or invent
 
   RULES: general IF-THEN patterns that apply to any person or thing.
     - These are generalizations, not about one specific person
 
   Output exactly this format, no extra text:
 
   Facts:
   - <fact 1>
 
   Rules:
   - <rule 1>
 
   Paragraph: {paragraph}
 
   Facts:
   """
 
   response_extract = ollama.chat(
       model="llama3.1:8b",
       messages=[{"role": "user", "content": PROMPT_EXTRACT}]
   )
   english_output = response_extract["message"]["content"].strip()
 
Expected output from Step 1:
 
.. code:: text
 
   Facts:
   - John and Mary are both students
   - Mary studies regularly
   - John does not study regularly
 
   Rules:
   - All students who study regularly tend to perform well academically
   - Anyone who performs well academically is likely to graduate
 
Step 2 — Convert to PyReason Syntax
-------------------------------------
 
The second prompt takes the English output from Step 1 and converts it
into PyReason's formal syntax.
 
Facts use specific names. Rules use variables ``X`` and ``Y``.
The annotation ``[lower, upper]`` on each statement represents confidence:
 
- ``[1,1]`` — completely true
- ``[0,0]`` — completely false
- ``[0.8,1]`` — likely true (for words like "tend to", "likely")
 
.. code:: python
 
   PROMPT_CONVERT = f"""Convert the facts and rules below into PyReason syntax.
 
   FACT syntax:
     predicate(Name):[1,1]            e.g. student(John):[1,1]
     predicate(Name):[0,0]            e.g. studies_regularly(John):[0,0]   (for completely false)
     predicate(Name1,Name2):[1,1]     e.g. enrolled_in(John,Math):[1,1]
 
   RULE syntax:
     head(X):[bound] <- condition1(X), condition2(X)
 
     head bound — how certain the conclusion is:
       [1,1]   definite  ("all", "always", "will")
       [0.8,1] likely    ("tend to", "likely", "usually")
       [0.5,1] possible  ("might", "can", "sometimes")
 
     conditions — what must be true. Use variables X, Y (never specific names):
       example: grandparent(X,Y) <- parent(X,Z), parent(Z,Y)
 
   Rules:
     1. Predicate names: lowercase_with_underscores only
     2. Facts use specific names (John, Mary). Rules use variables (X, Y).
     3. No markdown, no comments. Output ONLY the two sections.
 
   Facts and rules to convert:
   {english_output}
 
   Facts:
   """
 
   response_convert = ollama.chat(
       model="llama3.1:8b",
       messages=[{"role": "user", "content": PROMPT_CONVERT}]
   )
   pyreason_output = response_convert["message"]["content"].strip()
 
Expected output from Step 2:
 
.. code:: text
 
   Facts:
   student(John):[1,1]
   student(Mary):[1,1]
   studies_regularly(Mary):[1,1]
   studies_regularly(John):[0,0]
 
   Rules:
   performs_well_academically(X):[0.8,1] <- student(X), studies_regularly(X)
   graduate(X):[0.8,1] <- performs_well_academically(X)
 
Parsing the Output
------------------
 
The output is split into facts and rules using simple pattern matching.
A fact always contains ``):`` and a rule always contains ``<-``:
 
.. code:: python
 
   import re
   parts = re.split(r'\*{0,2}RULES\*{0,2}|Rules:', pyreason_output, maxsplit=1)
   facts_block, rules_block = parts[0], parts[1]
   facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
   rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]
 
The regex handles both ``Rules:`` and ``**RULES**`` since different models
may format the output differently.
 
Step 3 — Validate
------------------
 
Each rule is checked using ``pr.Rule()``:
 
.. code:: python
 
   for rule in rules:
       try:
           pr.Rule(rule)
           print(f"Rule passed {rule}")
       except Exception as e:
           print(f"ERROR {rule}\n{e}")
 
Expected output:
 
.. code:: text
 
   Validating rules...
   Rule passed performs_well_academically(X):[0.8,1] <- student(X), studies_regularly(X)
   Rule passed graduate(X):[0.8,1] <- performs_well_academically(X)