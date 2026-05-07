"""
Natural Language to PyReason
============================
Converts a plain English paragraph to PyReason logic facts and rules

Pipeline: 
    Step 1: Extract facts and rules in plain English
    Step 2: Convert English facts/rules into PyReason syntax
    Step 3: Validate the rules with PyReason

How to set up: 
    1. Install Ollama
    2. Open a terminal and run: ollama pull llama3.1:8b
    3. Run: pip install ollama
"""

import ollama
import pyreason as pr
import re

# Paragraph

# TEST paragraph
# paragraph = "John and Mary are both students. " \
# "All students who study regularly tend to perform well academically. " \
# "Mary studies regularly. Anyone who performs well academically is likely to graduate. " \
# "John does not study regularly." 

print("Enter your paragraph (press Enter twice when done):")
lines = []
while True:
    line = input()
    if line == "" and lines:
        break
    lines.append(line)
paragraph = " ".join(lines).strip()


# Step 1: Extract facts and rules in English 
# Ask LLM to read the paragraph and separate facts from rules in plain English

PROMPT_EXTRACT = f"""Read the paragraph below and extract two things.
FACTS: specific statements about a named person, place, or thing.
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

print("\nLLM is reading paragraph")
print(f"\n{paragraph}\n")
print("Step 1: Extract facts and rules in English...")

response_extract = ollama.chat(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": PROMPT_EXTRACT}]
)
english_output = response_extract["message"]["content"].strip()
print(f"\n{english_output}")

# Step 2: Convert to PyReason syntax
# Takes the English facts and rules and covert them into PyReason syntax.

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

print("\nStep 2: Converting to PyReason syntax...")

response_convert = ollama.chat(
    model="llama3.1:8b",
    messages=[{"role": "user", "content": PROMPT_CONVERT}]
)

pyreason_output = response_convert["message"]["content"].strip()
print(f"\n{pyreason_output}")

# Parse
parts = re.split(r'\*{0,2}RULES\*{0,2}|Rules:', pyreason_output, maxsplit=1)
facts_block, rules_block = parts[0], parts[1]
facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]


# Validate
print("Validating rules...")
for rule in rules:
    try: 
        pr.Rule(rule)
        print(f"Rule passed {rule}")
    except Exception as e:
        print(f"ERROR {rule}\n{e}")
