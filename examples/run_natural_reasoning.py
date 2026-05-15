"""
Pipeline:
Natural Language -> Logic -> Natural Language:
User inputs English paragraph, the scipt calls LLM to extract Facts and Rules.
Then calls LLM again to convert the Facts and Rules to PyReason Syntax.
And run the PyReason Inference.
Lastly, calls LLM again to "translate" the inference result in English as outputs.
"""

import ollama
import pyreason as pr
import networkx as nx
import re
import sys
import io

MODEL_NAME = "qwen3:14b"

# Read User Input
print("\nEnter text:")
lines = []
while True:
    line = input()
    if line == "" and lines:
        break
    lines.append(line)
paragraph = " ".join(lines).strip()

print("LLM is generating the conclusion... Please wait ~ 30 seconds")


# Step 1: Extract facts and rules in English 
# Ask LLM to read the paragraph and split it into:
#   - Facts: specific statements about a named person, place, or thing
#   - Rules: general IF-THEN patterns that apply to anyone

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
 
Paragraph: {paragraph}
 
Facts:
"""

response_extract = ollama.chat(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": PROMPT_EXTRACT}]
)
english_output = response_extract["message"]["content"].strip()

# Step 2: Convert English facts and rules into PyReason syntax
# Now we teach the LLM the PyReason syntax via examples and constraints,
# Then ask it to convert the English output from Step 1.

PROMPT_CONVERT = f"""Convert the facts and rules below into PyReason syntax.
 
FACT syntax and examples:
  predicate(node):[l,u]
  predicate(node):[1,1] ([1,1] means completely true)           e.g. student(alice):[1,1] (Alice is a student)
  predicate(node):[0,0] ([0,0] means completely false)          e.g. student(marie):[0,0] (Marie is not a student)
  predicate(node):[0.8,1] ([0.8,1] means likely, "tend to", "usually") e.g. doctor(bob):[0.8,1] (Bob is likely a doctor)
  predicate(node1,node2):[1,1]     e.g. enrolled_in(ryan,cs):[1,1] (Ryan enrolled in cs major)
  
RULE syntax:
  head(X):[bound] <- condition1(X), condition2(X,Y)
  Use variables X, Y (never specific names):
  example: grandparent(X,Y) <- parent(X,Z), parent(Z,Y)
  Include ALL conditions from the English rule, even if they seem redundant.
 
Constraints:
  1. Predicate names: lowercase_with_underscores, no spaces, no capital letters.
  2. Rule's head name describes WHAT, bound [l,u] describes HOW CERTAIN. Don't use uncertain name for rule's head.
  3. Facts use specific names (john, mary) lower case is prefered in specific name. Rules use variables (X, Y).
  4. Negation in facts: use [0,0] on the SAME predicate, never invent a new predicate.
     e.g. "Alice is not student" → student(alice):[0,0]  NOT not_student(alice):[1,1]
  5. Rules with one condition use only X: good_grade(X) <- study_hard(X)
     Only introduce Y or Z when two different entities are involved.

### No markdown, no code blocks, no comments. Output ONLY the two sections.
 
Facts and rules to convert:
{english_output}
 
Facts:
<fact 1>
<fact 2>
 
Rules:
<rule 1>
<rule 2>
"""

response_convert = ollama.chat(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": PROMPT_CONVERT}]
)
pyreason_output = response_convert["message"]["content"]

# Step 3: Parse the LLM output into facts and rules

parts = re.split(
    r'\*{0,2}\s*rules\s*\*{0,2}s*:?',
    pyreason_output, maxsplit=1, flags=re.IGNORECASE
)
if len(parts) < 2:
    print("Error: could not parse LLM output.")
    exit(1)

facts_block, rules_block = parts[0], parts[1]
facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]

if not rules:
    print("ERROR: No rules extracted.")
    exit(1)
    
         