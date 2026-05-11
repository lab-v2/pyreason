Natural Language to PyReason Tutorial
======================================

Welcome to the Natural Language to PyReason tutorial! In this document we outline
a pipeline that converts a plain English paragraph into PyReason facts and rules
using a Large Language Model (LLM). If you want to combine the flexibility of
natural language input with the precision of symbolic reasoning, this is the
right place!

.. note::
   Find the full, executable code `here <https://github.com/lab-v2/pyreason/blob/main/examples/natural_language_to_pyreason_ex.py>`_

The goal of this tutorial is to take a paragraph like this:

::

   Carlos and Emma are both lawyers. All lawyers who win cases regularly tend to
   build a strong reputation. Emma wins cases regularly. Anyone with a strong
   reputation is likely to attract high-profile clients. Carlos does not win
   cases regularly.

And automatically convert it into PyReason facts and rules, then validate that
they parse correctly with PyReason.

The pipeline needs three things:

1. An LLM (we use Ollama with a local model)
2. A two-stage prompt design (one prompt for extraction, one for conversion)
3. A parser that turns the LLM's text output back into structured facts and rules

Setup
-----

We use `Ollama <https://ollama.com>`_ to run an LLM locally. Different models
have different trade-offs between speed and stability — we discuss this at the
end of the tutorial. For best results, we recommend ``qwen3:14b``.

1. Install Ollama from `ollama.com <https://ollama.com>`_
2. Pull the model:

.. code:: bash

   ollama pull qwen3:14b

3. Install the Python dependencies:

.. code:: bash

   pip install ollama pyreason

Reading the Paragraph
----------------------

The script reads the paragraph from the user. The user types lines and presses
Enter twice when done:

.. code:: python

   import ollama
   import pyreason as pr
   import re

   print("Enter your paragraph (press Enter twice when done):")
   lines = []
   while True:
       line = input()
       if line == "" and lines:
           break
       lines.append(line)
   paragraph = " ".join(lines).strip()

Step 1: Extract Facts and Rules in English
-------------------------------------------

The first prompt asks the LLM to read the paragraph and produce structured
English. No PyReason syntax appears yet — this step is purely about language
understanding.

.. code:: python

   PROMPT_EXTRACT = f"""Read the paragraph below and extract two things.
   FACTS: specific statements about a named person, place, or thing.
     - Extract EVERY fact mentioned, including type/category facts like "A is a student". Do not skip any.
     - Include negative facts too (e.g. "John does not study regularly")
     - Only extract what is explicitly stated, do not assume or invent
   RULES: general IF-THEN patterns that apply to any person or thing.
     - These are generalizations, not about one specific person

   Output exactly this format, no extra text:

   Facts:
   - <fact 1>
   - <fact 2>

   Rules:
   - <rule 1>
   - <rule 2>

   Paragraph: {{paragraph}}

   Facts:
   """

Three design choices in this prompt deserve attention:

1. **Extract EVERY fact** including type facts. Without this instruction, the
   LLM tends to drop background facts like "Carlos is a lawyer" because they
   feel like context, not assertions. But these facts are exactly what later
   rules need to fire.
2. **Negation must be preserved.** LLMs default to extracting positive
   statements and silently drop "X does not Y" sentences. The bullet point
   about negation prevents this.
3. **The prompt ends with** ``Facts:`` — this is a completion primer. The LLM
   continues writing from where the prompt ended, jumping directly into the
   structured output rather than producing chatty preamble like "Sure, here are
   the facts I extracted...".

We send this prompt to the model:

.. code:: python

   response_extract = ollama.chat(
       model="qwen3:14b",
       messages=[{"role": "user", "content": PROMPT_EXTRACT}]
   )
   english_output = response_extract["message"]["content"].strip()
   print(f"\n{english_output}")

For our example paragraph, the LLM produces:

::

   Facts:
   - Carlos is a lawyer
   - Emma is a lawyer
   - Emma wins cases regularly
   - Carlos does not win cases regularly

   Rules:
   - All lawyers who win cases regularly tend to build a strong reputation
   - Anyone with a strong reputation is likely to attract high-profile clients

Step 2: Convert to PyReason Syntax
-----------------------------------

The second prompt takes the English output from Step 1 and converts it into
PyReason syntax. This is the harder step because PyReason's syntax rarely
appears in LLM training data, so the prompt has to teach it.

.. code:: python

   PROMPT_CONVERT = f"""Convert the facts and rules below into PyReason syntax.

   FACT syntax and examples:
     predicate(node):[l,u]
     predicate(node):[1,1] ([1,1] means completely true)             e.g. student(alice):[1,1] (Alice is a student)
     predicate(node):[0,0] ([0,0] means completely false)            e.g. student(marie):[0,0] (Marie is not a student)
     predicate(node):[0.8,1] ([0.8,1] means likely, "tend to", "usually") e.g. doctor(bob):[0.8,1] (Bob is likely a doctor)
     predicate(node1,node2):[1,1]     e.g. enrolled_in(ryan,cs):[1,1] (Ryan enrolled in cs major)

   RULE syntax:
     head(X):[bound] <- condition1(X), condition2(X,Y)
     Use variables X, Y (never specific names):
     example: grandparent(X,Y) <- parent(X,Z), parent(Z,Y)
     Include ALL conditions from the English rule, even if they seem redundant.

   Constraints:
     1. Predicate names: lowercase_with_underscores, no spaces, no capital letters.
     2. Rule's head name describes WHAT, bound [l,u] describes HOW CERTAIN.
        Don't use uncertain name for rule's head.
     3. Facts use specific names (john, mary) lower case is prefered in specific name.
        Rules use variables (X, Y).
     4. Negation in facts: use [0,0] on the SAME predicate, never invent a new predicate.
        e.g. "Alice is not student" -> student(alice):[0,0]  NOT not_student(alice):[1,1]
     5. Rules with one condition use only X: good_grade(X) <- study_hard(X)
        Only introduce Y or Z when two different entities are involved.

   ### No markdown, no code blocks, no comments. Output ONLY the two sections.

   Facts and rules to convert:
   {{english_output}}

   Facts:
   <fact 1>
   <fact 2>

   Rules:
   <rule 1>
   <rule 2>
   """

The prompt enforces five constraints. The most important conceptually is
**constraint 2**: predicate names describe *what* a thing is, and bounds
describe *how certain* we are about it. Mixing these — for example writing
``likely_to_graduate(X):[0.8,1]`` — breaks the chain of reasoning, because
later rules will not be able to reference the predicate by a consistent name.

Constraint 4 is also subtle. Negation in PyReason is expressed by setting the
bound to ``[0,0]`` on the same predicate, not by introducing a new
``not_<predicate>`` predicate. This matters because PyReason treats predicate
names as opaque symbols — a rule that needs to detect "not a student" must
check ``student(X):[0,0]``, not ``not_student(X):[1,1]``.

The end of the prompt includes ``Facts:`` and ``Rules:`` template scaffolding
with ``<fact 1>`` / ``<rule 1>`` placeholders. This acts as a strong format
anchor — the LLM sees the exact shape of the expected output and fills in the
slots, which reduces format drift.

We send this prompt to the model:

.. code:: python

   response_convert = ollama.chat(
       model="qwen3:14b",
       messages=[{"role": "user", "content": PROMPT_CONVERT}]
   )
   pyreason_output = response_convert["message"]["content"].strip()
   print(f"\n{pyreason_output}")

For our example, the LLM produces:

::

   Facts:
   lawyer(carlos):[1,1]
   lawyer(emma):[1,1]
   wins_cases_regularly(emma):[1,1]
   wins_cases_regularly(carlos):[0,0]

   Rules:
   strong_reputation(X):[0.8,1] <- lawyer(X), wins_cases_regularly(X)
   attract_high_profile_clients(X):[0.8,1] <- strong_reputation(X)

Notice how:

- "Carlos does not win cases regularly" became
  ``wins_cases_regularly(carlos):[0,0]`` — the **same** predicate with a
  falsified bound.
- "tend to build a strong reputation" became
  ``strong_reputation(X):[0.8,1]`` — uncertainty lives in the bound, not in
  the predicate name.
- The two rules **chain**: rule 1's head ``strong_reputation`` appears
  verbatim in rule 2's body.

Parsing the LLM Output
-----------------------

The LLM returns plain text with a ``Facts:`` section and a ``Rules:`` section.
We use a regex to split the output at the ``Rules:`` header:

.. code:: python

   parts = re.split(
       r'\*{0,2}\s*rules\s*\*{0,2}\s*:?',
       pyreason_output,
       maxsplit=1,
       flags=re.IGNORECASE
   )

   if len(parts) < 2:
       print("\nERROR: Could not parse LLM output - Rules section not found.")
       print("Raw output was:")
       print(pyreason_output)
       exit(1)

The regex tolerates several variations of the header that LLMs sometimes
produce: ``Rules:``, ``RULES:``, ``**Rules**``, with or without trailing colon
and surrounding whitespace. This robustness matters because even with a clean
prompt, LLM output formatting drifts between runs.

Once we have the two blocks, we extract facts and rules by recognizing each
line's syntactic markers:

.. code:: python

   facts_block, rules_block = parts[0], parts[1]
   facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
   rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]

   if not rules:
       print("\nERROR: No rules extracted. LLM may have formatted output incorrectly.")
       exit(1)

A fact line always contains ``):`` (the closing parenthesis of the predicate
followed by the bound colon). A rule line always contains ``<-`` (the
implication arrow). These two markers are reliable structural signals — they
don't depend on the LLM cooperating with header formatting.

Step 3: Validate with PyReason
-------------------------------

Now that we have parsed rules as strings, we check each one by constructing a
``pr.Rule`` object. If PyReason's parser rejects it, we catch the error:

.. code:: python

   print("\nValidating rules...")
   for rule in rules:
       try:
           pr.Rule(rule)
           print(f"Rule passed {rule}")
       except Exception as e:
           print(f"ERROR {rule}\n{e}")

For our example, both rules pass:

::

   Validating rules...
   Rule passed strong_reputation(X):[0.8,1] <- lawyer(X), wins_cases_regularly(X)
   Rule passed attract_high_profile_clients(X):[0.8,1] <- strong_reputation(X)

This validation step catches LLM mistakes early. If the LLM produced malformed
syntax (an unbalanced parenthesis, a missing arrow, an invalid bound), the
``pr.Rule()`` constructor raises an exception and we see exactly which rule
failed.

Testing on Other Paragraphs
----------------------------

The same pipeline handles paragraphs from any domain. Here are several test
cases we used during development:

**Medical**

::

   Tom and Lisa are both nurses. All nurses who work night shifts tend to
   experience fatigue. Lisa works night shifts. Anyone who experiences
   fatigue is likely to make errors. Tom does not work night shifts.

**Animals**

::

   Rex and Bella are both dogs. All dogs that exercise daily tend to stay
   healthy. Bella exercises daily. Any dog that stays healthy is likely to
   live long. Rex does not exercise daily.

**Relational (Edge Rule)**

::

   Alice and Bob are colleagues. All colleagues who share projects tend to
   collaborate well. Alice and Bob share a project. Anyone who collaborates
   well is likely to get promoted. Carol and Dave are colleagues but do not
   share any projects.

The relational case is the most challenging because it involves two-entity
relationships, which the LLM must encode as edge facts like
``colleague(alice,bob)`` and edge rules like
``collaborate_well(X,Y) <- colleague(X,Y), share_project(X,Y)``.

Notes on Model Choice
---------------------

We tested several local Ollama models with the prompts above:

- **llama3.1:8b** — fast but unstable. Often drops facts or invents predicates.
- **mistral-nemo:12b** — better than llama3.1, but suffers from naming drift
  (``works_night_shift`` vs ``works_night_shifts``) and occasionally wraps
  output in markdown code blocks.
- **qwen2.5:14b** — significantly more stable, but in rare cases produces
  corrupted syntax like ``lawyeremma:[][1,1]`` when handling compound subjects.
- **qwen3:14b** — the most consistent in our tests. Recommended.

Smaller models are accessible but less reliable; larger models are reliable but
require better hardware. The prompt design above mitigates the issue but cannot
fully eliminate it.

What's Next
-----------

This pipeline is intentionally minimal to illustrate the core idea — taking
natural language and turning it into PyReason syntax that parses correctly.
Practical extensions could include:

- Loading the validated facts and rules into a graph and running
  ``pr.reason()`` to derive new conclusions.
- A retry loop that catches syntax errors and asks the LLM to fix its own
  output.
- A post-inference step that translates PyReason's results back into natural
  English.
- Validation that detects predicate-naming drift across rules (e.g. rule 1's
  head uses ``strong_reputation`` but rule 2's body uses
  ``has_strong_reputation``) and prompts the LLM to unify the names.