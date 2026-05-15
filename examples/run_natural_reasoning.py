"""
Natural Language Reasoning with PyReason
=========================================
Wrapper script: user inputs a structured paragraph, sees reasoning results in English.

Pipeline:
    Step 1: LLM extracts facts and rules in plain English
    Step 2: LLM converts English into PyReason syntax
    Step 3: Parse the LLM output
    Step 4: Build graph, load facts/rules, run pr.reason()
    Step 5: Split results into Input (relevant facts) and Output (derived conclusions)
    Step 6: LLM summarizes each section in natural English

Setup:
    1. Install Ollama from https://ollama.com
    2. Pull the recommended model on terminal:
           ollama pull qwen3:14b
    3. Install Python dependencies:
           pip install ollama pyreason networkx
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

print("LLM is generating the conclusion... Please wait ~ 1-3 minutes")


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
pyreason_output = response_convert["message"]["content"].strip()

# Step 3: Parse the LLM output into facts and rules

parts = re.split(
    r'\*{0,2}\s*rules\s*\*{0,2}\s*:?',
    pyreason_output, maxsplit=1, flags=re.IGNORECASE
)
if len(parts) < 2:
    print("ERROR: could not parse LLM output.")
    exit(1)

facts_block, rules_block = parts[0], parts[1]
facts = [l.strip() for l in facts_block.split("\n") if "):" in l]
rules = [l.strip() for l in rules_block.split("\n") if "<-" in l]

if not rules:
    print("ERROR: No rules extracted.")
    exit(1)

# Relax rule body bounds:

# Auto-revise rules so inference chains can fire correctly
# PyReason defaults rule body clause bounds to [1,1]
# If the last rule derives strong_reputation(X):[0.8,1]
# Next rule uses strong_reputation(X) as body, the rule will never fire because [0.8,1] not equals to [1,1]

# Record the head bound of every rule.
head_bounds = {}
for r in rules:
    head = r.split('<-')[0].strip()
    pred = head.split('(')[0].lstrip('~').strip()
    m = re.search(r':\[([^\]]+)\]', head)
    if m:
        head_bounds[pred] = m.group(1)

def relax_body(rule_text):
    """If a body clause references a derived predicate, copy its head bound."""
    head, body = rule_text.split('<-', 1)
    clauses = [c.strip() for c in body.split(',')]
    fixed = []
    for c in clauses:
        if ':' in c:
            fixed.append(c)
            continue
        pred = c.split('(')[0].lstrip('~').strip()
        if pred in head_bounds:
            fixed.append(f"{c}:[{head_bounds[pred]}]")
        else:
            fixed.append(c)
    return f"{head.strip()} <- {', '.join(fixed)}"

rules = [relax_body(r) for r in rules]

# Helper Functions
def predicate_of(atom):
    """Return the predicate name from 'pred(args):[l,u]' or 'pred(args)'."""
    return atom.split('(')[0].lstrip('~').strip()

def entities_of(atom):
    """Return a tuple of entity names from inside the parentheses."""
    m = re.search(r'\(([^)]*)\)', atom)
    if not m:
        return ()
    return tuple(n.strip() for n in m.group(1).split(',') if n.strip())

# Step 4: Build graph and run PyReason
g = nx.DiGraph()
for f in facts:
    names = entities_of(f)
    g.add_nodes_from(names)
    if len(names) == 2:
        g.add_edge(names[0], names[1])
pr.load_graph(g)

for f in facts:
    pr.add_fact(pr.Fact(f))
for r in rules:
    pr.add_rule(pr.Rule(r))

# Run reasoning silently
pr.settings.verbose = False
_buf = io.StringIO()
_old_stdout = sys.stdout
sys.stdout = _buf
interpretation = pr.reason(timesteps=2)
sys.stdout = _old_stdout

# Step 5: Split the reasoning results into Input and Output

# Input  = original facts about entities that triggered at least one rule
# Output = new conclusions derived by rule firings
# Entities that never triggered a rule are hidden from the user entirely.
 
# Original (predicate, entities) pairs the user gave us.
original_atoms = set()
for f in facts:
    original_atoms.add((predicate_of(f), entities_of(f)))
 
# Predicate names that appear anywhere, split by arity.
node_labels, edge_labels = set(), set()
for atom in facts + [r.split('<-')[0] for r in rules]:
    args = entities_of(atom)
    if len(args) == 1:
        node_labels.add(predicate_of(atom))
    elif len(args) == 2:
        edge_labels.add(predicate_of(atom))
 
# Walk PyReason results: collect derived conclusions and mark useful entities.
derived = []
useful_entities = set()
 
for label in sorted(node_labels):
    for df in pr.filter_and_sort_nodes(interpretation, [label]):
        for _, row in df.iterrows():
            entity = row['component']
            bound = row[label]
            key = (label, (entity,))
            if key not in original_atoms:
                derived.append((label, (entity,), bound))
                useful_entities.add(entity)
 
for label in sorted(edge_labels):
    for df in pr.filter_and_sort_edges(interpretation, [label]):
        for _, row in df.iterrows():
            e = row['component']
            bound = row[label]
            key = (label, (e[0], e[1]))
            if key not in original_atoms:
                derived.append((label, (e[0], e[1]), bound))
                useful_entities.add(e[0])
                useful_entities.add(e[1])
 
# Input facts: keep only those involving a useful entity.
input_lines = [
    f for f in facts
    if any(e in useful_entities for e in entities_of(f))
]
 
# Output conclusions: every derived atom.
output_lines = [
    f"{label}({','.join(ents)}):{bound}"
    for label, ents, bound in derived
]

# Step 6: LLM summarizes each section
# Send input_lines and output_lines to LLM, "translate" to Natural Language
def summarize(reasoning_lines):
    """Send reasoning lines to LLM and return natural-English sentences."""
    if not reasoning_lines:
        return ""
    prompt = f"""Below are reasoning results from a logic engine.
Each line is: predicate(entity):[lower, upper]
 
Write ONE short English sentence per line:
- [1.0, 1.0] = certain.   e.g. "Leo works overtime."
- [0.0, 0.0] = false.     e.g. "Mia does not work overtime."
- work_overtime(peng):[0.8,1.0] e.g. "Peng is 80% likely to work overtime."
 
Other rules:
- Capitalize entity names (alice -> Alice).
- Convert snake_case predicates to readable English (works_overtime -> "works overtime").
- Use correct verb forms ("does not work", not "does not works").
- For single-word noun predicates (engineer, doctor, dog), use "is a/an".
- ONLY use the data given. Do NOT invent.
- Output one sentence per line, no headings, no bullets.
 
Reasoning results:
{chr(10).join(reasoning_lines)}
 
Output:
"""
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"].strip()

print("\nInput")
print(summarize(input_lines))

print("\nOutput")
print(summarize(output_lines))
