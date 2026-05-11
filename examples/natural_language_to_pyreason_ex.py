"""
Natural Language to PyReason
============================
Converts a plain English paragraph into PyReason facts and rules using a
local LLM (via Ollama), then validates the rules with PyReason.
 
Pipeline:
    Step 1: Read paragraph -> LLM extracts facts and rules in plain English
    Step 2: LLM converts English facts/rules into PyReason syntax
    Step 3: Parse the LLM output into facts and rules
    Step 4: Validate each rule with pr.Rule()
 
Setup:
    1. Install Ollama from https://ollama.com
    2. Pull the recommended model:
           ollama pull qwen3:14b
    3. Install Python dependencies:
           pip install ollama pyreason
"""
 
import ollama
import pyreason as pr
import re
 
 
# Model used for both LLM calls. Change here to swap models.
MODEL_NAME = "qwen3:14b"

# Read the paragraph from the user
lines = []
while True:
    line = input()
    if line == "" and lines:
        break
    lines.append(line)
paragraph = " ".join(lines).strip()


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

print("LLM is reading paragraph")
print(f"\n{paragraph}\n")
print("Step 1: Extract facts and rules in English...")

response_extract = ollama.chat(
    model=MODEL_NAME,
    messages = [{"role":"user", "content": PROMPT_EXTRACT}]
)
english_output = response_extract["message"]["content"].strip()
print(f"\n{english_output}")

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

print("\nStep 2: Converting to PyReason syntax...")

response_convert = ollama.chat(
    model=MODEL_NAME,
    messages = [{"role": "user", "content": PROMPT_CONVERT}]
)

pyreason_output = response_convert["message"]["content"].strip()
print(f"\n{pyreason_output}")

# Step 3: Parse the LLM output into facts and rules
parts = re.split(r'\*{0,2}\s*rules\s*\*{0,2}\s*:?', pyreason_output, maxsplit=1, flags=re.IGNORECASE)

if len(parts) < 2:
    print("\nERROR: Could not parse LLM output — Rules section not found.")
    print("Raw output was:")
    print(pyreason_output)
    exit(1)

facts_block, rules_block = parts[0], parts[1]
facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]

if not rules:
    print("\nERROR: No rules extracted. LLM may have formatted output incorrectly.")
    exit(1)

# Step 4: Validate each rule with PyReason
print("\nValidating rules...")
for rule in rules:
    try: 
        pr.Rule(rule)
        print(f"Rule passed {rule}")
    except Exception as e:
        print(f"ERROR {rule}\n{e}")