# _ground_rule() Function Analysis

**Source File:** `pyreason/scripts/interpretation/interpretation.py`
**Location:** Lines 784-1226 (444 lines)
**Complexity:** Extremely High (Cyclomatic Complexity ~40-50)

---

## Function Overview

The `_ground_rule()` function is the most complex single function in PyReason. It orchestrates the entire rule grounding process: finding all variable bindings that satisfy a rule's body clauses, then preparing the data structures needed to apply the rule's head.

**Purpose:** Given a rule, find all ways to bind the rule's variables to concrete entities (nodes/edges) such that:
1. All body clauses are satisfied
2. All thresholds are met
3. The dependency graph remains consistent

**Output:** Two lists of applicable rule instances ready for application:
- `applicable_rules_node`: List of node rule instances
- `applicable_rules_edge`: List of edge rule instances

---

### What is an "Applicable Rule Instance"?

An **applicable rule instance** is a complete data package representing ONE specific way a rule fires. It contains everything needed to apply the rule's head to a specific entity.

**Concrete Example:**

```
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

Graph:
  infected(Alice) = [0.9, 1.0]
  neighbor edges: (Alice, Bob), (Alice, Carol)

Grounding Process:
  Step 1: Find X satisfying infected(X) → X = [Alice]
  Step 2: Find Y where neighbor(X,Y) exists → Y = [Bob, Carol]
  Step 3: Create instances for each valid Y

Result: TWO applicable rule instances:
  Instance 1: Update risk(Bob)
  Instance 2: Update risk(Carol)
```

Each instance is a tuple containing 5 components:

**For Node Rules:** `(head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_be_added)`

**For Edge Rules:** `(edge, annotations, qualified_nodes, qualified_edges, edges_to_be_added)`

---

### Component Breakdown

**1. `head_grounding` (node rules) or `edge` (edge rules)**
- **Type:** `str` for nodes, `Tuple[str, str]` for edges
- **Purpose:** The specific entity that will be updated when this rule fires
- **Example (node rule):** `'Bob'` means "update the predicate on node Bob"
- **Example (edge rule):** `('Alice', 'Carol')` means "update the predicate on edge (Alice, Carol)"
- **NOT just candidates:** This is the FINAL, specific entity after all filtering and refinement

**2. `annotations`**
- **Type:** `List[List[Interval]]`
- **Purpose:** Provides input to the annotation function to compute the new interval
- **Structure:** Outer list = one entry per clause; Inner list = intervals from entities satisfying that clause
- **Example:**
  ```python
  # Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
  # For instance where Y=Bob
  annotations = [
      [Interval(0.9, 1.0)],      # Clause 1: infected(Alice)
      [Interval(0.5, 0.7)]       # Clause 2: neighbor edge's interval
  ]
  # Annotation function (e.g., 'max') uses these to compute: risk(Bob) = [0.9, 1.0]
  ```
- **Only populated if:** Rule has an annotation function (`ann_fn != ''`)

**3. `qualified_nodes`**
- **Type:** `List[List[str]]`
- **Purpose:** Provenance tracking - which specific nodes satisfied each clause
- **Structure:** Outer list = one entry per clause; Inner list = nodes that made clause true
- **Example:**
  ```python
  # Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
  # For instance where Y=Bob
  qualified_nodes = [
      ['Alice'],    # Clause 1 (infected(X)): Alice satisfied it
      [],           # Clause 2 (neighbor(X,Y)): edge clause, so empty
  ]
  ```
- **Only populated if:** `atom_trace=True` (detailed provenance enabled)
- **Use case:** Explainability - "Why is risk(Bob)=[0.9,1.0]? Because infected(Alice)=[0.9,1.0] and neighbor(Alice,Bob) exists"

**4. `qualified_edges`**
- **Type:** `List[List[Tuple[str, str]]]`
- **Purpose:** Provenance tracking - which specific edges satisfied each clause
- **Example:**
  ```python
  # Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
  # For instance where Y=Bob
  qualified_edges = [
      [],                  # Clause 1 (infected(X)): node clause, so empty
      [('Alice', 'Bob')]   # Clause 2 (neighbor(X,Y)): this edge satisfied it
  ]
  ```
- **Only populated if:** `atom_trace=True`

**5. `edges_to_be_added`**
- **Type:** `Tuple[List[str], List[str], Label]`
- **Purpose:** New edges to create in the graph (for `infer_edges` rules)
- **Structure:** `(sources, targets, label)` where new edges are Cartesian product of sources × targets
- **Example (infer_edges rule):**
  ```python
  # Rule: infected(X) ∧ neighbor(X,Y) → risk(X,Y) [infer_edges]
  # Creates new 'risk' edges
  edges_to_be_added = (
      ['Alice'],          # Sources
      ['Bob', 'Carol'],   # Targets
      Label('risk')       # Label for new edges
  )
  # Will create: risk(Alice, Bob) and risk(Alice, Carol)
  ```
- **Example (regular rule):** `([], [], Label(''))` (no edges to add)

---

### Complete Example: Multiple Instances

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

Graph:
  infected(Alice) = [0.9, 1.0]
  infected(Carol) = [0.8, 0.85]
  neighbor edges: (Alice, Bob), (Alice, Dave), (Carol, Eve)

Grounding Result:
  X = [Alice, Carol]
  Y = [Bob, Dave, Eve]
  Valid combinations: (Alice→Bob), (Alice→Dave), (Carol→Eve)

Output: THREE applicable rule instances in applicable_rules_node:

Instance 1:
  head_grounding: 'Bob'
  annotations: [[Interval(0.9, 1.0)], [Interval(...)]]
  qualified_nodes: [['Alice'], []]
  qualified_edges: [[], [('Alice', 'Bob')]]
  edges_to_be_added: ([], [], Label(''))

Instance 2:
  head_grounding: 'Dave'
  annotations: [[Interval(0.9, 1.0)], [Interval(...)]]
  qualified_nodes: [['Alice'], []]
  qualified_edges: [[], [('Alice', 'Dave')]]
  edges_to_be_added: ([], [], Label(''))

Instance 3:
  head_grounding: 'Eve'
  annotations: [[Interval(0.8, 0.85)], [Interval(...)]]
  qualified_nodes: [['Carol'], []]
  qualified_edges: [[], [('Carol', 'Eve')]]
  edges_to_be_added: ([], [], Label(''))

Next step: Each instance passed to _update_node() which applies:
  risk(Bob) = annotate(annotations_1)
  risk(Dave) = annotate(annotations_2)
  risk(Eve) = annotate(annotations_3)
```

---

### Key Insight: One Rule → Many Instances

- **Input:** ONE rule with variables
- **Output:** MULTIPLE instances (one per valid variable binding)
- **Each instance:** Complete, self-contained data package
- **Each instance → one update:** `_update_node()` or `_update_edge()` called once per instance
- **Separation of concerns:** `_ground_rule()` finds WHAT to update; later functions handle HOW to update

---

## Section 1: Initialization & Setup (Lines 784-820)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Rule Grounding**: The process of finding concrete entity bindings for rule variables
- **Groundings Dictionary**: Maps variable names (strings) to lists of node/edge identifiers that satisfy constraints
- **Dependency Graph**: Tracks relationships between variables introduced by edge clauses
- **Predicate Map**: Reverse index from predicates to components (optimization for finding initial candidates)

---

### Function Signature (Line 784)

```python
def _ground_rule(rule, interpretations_node, interpretations_edge, predicate_map_node,
                 predicate_map_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace,
                 allow_ground_rules, num_ga, t, head_functions):
```

**Parameter Table:**

| Parameter | Type | Definition |
|-----------|------|------------|
| `rule` | `Rule` | Rule object containing clauses, head, thresholds, annotation function |
| `interpretations_node` | `Dict[str, World]` | Current node interpretations (node → World) |
| `interpretations_edge` | `Dict[Tuple, World]` | Current edge interpretations (edge → World) |
| `predicate_map_node` | `Dict[Label, List[str]]` | Reverse index: predicate → nodes with that predicate |
| `predicate_map_edge` | `Dict[Label, List[Tuple]]` | Reverse index: predicate → edges with that predicate |
| `nodes` | `List[str]` | All nodes in graph |
| `edges` | `List[Tuple[str, str]]` | All edges in graph |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency: node → successors |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency: node → predecessors |
| `atom_trace` | `bool` | Whether to record detailed provenance (ground atoms) |
| `allow_ground_rules` | `bool` | Whether to allow ground atoms (variables that are literal node/edge names) |
| `num_ga` | `List[int]` | Ground atom count per timestep (for tracking) |
| `t` | `int` | Current timestep index |
| `head_functions` | `Tuple[Function]` | Registry of user-defined head functions |

**Returns:** `Tuple[List, List]` - (applicable_rules_node, applicable_rules_edge)

---

### Rule Parameter Extraction (Lines 785-793)

```python
rule_type = rule.get_type()
head_variables = rule.get_head_variables()
head_fns = rule.get_head_function()
head_fns_vars = rule.get_head_function_vars()
clauses = rule.get_clauses()
thresholds = rule.get_thresholds()
ann_fn = rule.get_annotation_function()
rule_edges = rule.get_edges()
```

**Purpose:** Extract all configuration from the rule object into local variables for faster access during grounding.

**Extracted Data:**
- `rule_type`: `'node'` or `'edge'` - determines which branch to take for head processing
- `head_variables`: List of variable names in rule head (1 for node rules, 2 for edge rules)
- `head_fns`: List of head function names (empty string if no function)
- `head_fns_vars`: Nested list of variables used as arguments to head functions
- `clauses`: List of clause tuples `(type, label, variables, bound, operator)`
- `thresholds`: List of threshold tuples for each clause
- `ann_fn`: Annotation function name (empty string if none)
- `rule_edges`: Tuple `(source_var, target_var, label)` for infer_edges feature

---

### Head Variable Unpacking (Lines 795-798)

```python
if rule_type == 'node':
    head_var_1 = head_variables[0]
else:
    head_var_1, head_var_2 = head_variables[0], head_variables[1]
```

**Purpose:** Unpack head variable names for convenient access.

**Node Rules:** Single head variable (e.g., `processed(Y)` → `head_var_1 = 'Y'`)
**Edge Rules:** Two head variables (e.g., `risk(X,Y)` → `head_var_1 = 'X'`, `head_var_2 = 'Y'`)

---

### Return Container Initialization (Lines 800-802)

```python
applicable_rules_node = numba.typed.List.empty_list(node_applicable_rule_type)
applicable_rules_edge = numba.typed.List.empty_list(edge_applicable_rule_type)
```

**Purpose:** Initialize typed lists to store rule application instances.

**Structure of `node_applicable_rule_type`:**
```
Tuple[
    str,                          # head_grounding (node identifier)
    List[List[Interval]],         # annotations (for annotation function)
    List[List[str]],              # qualified_nodes (for atom trace)
    List[List[Tuple]],            # qualified_edges (for atom trace)
    Tuple[List, List, Label]      # edges_to_be_added
]
```

**Structure of `edge_applicable_rule_type`:**
```
Tuple[
    Tuple[str, str],              # edge (source, target)
    List[List[Interval]],         # annotations
    List[List[str]],              # qualified_nodes
    List[List[Tuple]],            # qualified_edges
    Tuple[List, List, Label]      # edges_to_be_added
]
```

---

### Grounding Data Structure Initialization (Lines 804-815)

```python
# Grounding variable that maps variables in the body to a list of grounded nodes
# Grounding edges that maps edge variables to a list of edges
groundings = numba.typed.Dict.empty(key_type=numba.types.string, value_type=list_of_nodes)
groundings_edges = numba.typed.Dict.empty(key_type=edge_type, value_type=list_of_edges)

# Dependency graph that keeps track of the connections between the variables in the body
dependency_graph_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=list_of_nodes)
dependency_graph_reverse_neighbors = numba.typed.Dict.empty(key_type=node_type, value_type=list_of_nodes)
```

**Data Structure Purpose:**

| Data Structure | Purpose | Example |
|----------------|---------|---------|
| `groundings` | Maps variable names to lists of candidate nodes | `{'X': [Alice, Bob], 'Y': [Carol]}` |
| `groundings_edges` | Maps variable pairs to lists of candidate edges | `{('X', 'Y'): [(Alice, Carol), (Bob, Carol)]}` |
| `dependency_graph_neighbors` | Forward dependencies: which variables are constrained by this variable | `{'X': ['Y']}` means X constrains Y |
| `dependency_graph_reverse_neighbors` | Backward dependencies: which variables constrain this variable | `{'Y': ['X']}` means Y is constrained by X |

**Why Both `groundings` and `groundings_edges`?**
- `groundings`: Stores individual node bindings for each variable
- `groundings_edges`: Stores valid edge combinations between variable pairs
- Need both because: knowing `X=[Alice, Bob]` and `Y=[Carol, Dave]` doesn't tell us which edges actually exist
- Example: If edges are `(Alice, Carol)` and `(Bob, Dave)`, then `(Alice, Dave)` and `(Bob, Carol)` are invalid

**Dependency Graph vs Neighbor Graph:**
- **Neighbor Graph**: Physical graph structure (edges in actual knowledge graph)
- **Dependency Graph**: Logical constraints between variables in rule body
- Example: Rule `infected(X) ∧ neighbor(X,Y) ∧ age(Y,Z)` creates dependency graph: `X→Y→Z`
- Purpose: Enables `refine_groundings()` to propagate constraints (if X narrows, Y must narrow, Z must narrow)

---

### Helper Sets and Satisfaction Flag (Lines 817-820)

```python
nodes_set = set(nodes)
edges_set = set(edges)

satisfaction = True
```

**Purpose:**
- `nodes_set`, `edges_set`: O(1) membership testing (used in lines 835, 862, 1069)
- `satisfaction`: Tracks whether all clauses processed so far have been satisfied
  - Initialized to `True`
  - ANDed with each clause's threshold satisfaction
  - If becomes `False`, loop breaks early (line 912)

---

## Data Structure Lifetime & Evolution

**Initialization (Section 1):**
```
groundings = {}
groundings_edges = {}
dependency_graph_neighbors = {}
dependency_graph_reverse_neighbors = {}
satisfaction = True
```

**After Node Clause `infected(X)`:**
```
groundings = {'X': [Alice, Bob, Carol]}
groundings_edges = {}  # No change
dependency_graph_neighbors = {}  # No change
dependency_graph_reverse_neighbors = {}  # No change
```

**After Edge Clause `neighbor(X,Y)`:**
```
groundings = {
    'X': [Alice, Carol],     # Narrowed (Bob had no neighbors)
    'Y': [Dave, Eve, Frank]  # Added
}
groundings_edges = {
    ('X', 'Y'): [(Alice, Dave), (Alice, Eve), (Carol, Frank)]
}
dependency_graph_neighbors = {'X': ['Y']}
dependency_graph_reverse_neighbors = {'Y': ['X']}
```

---

**Bugs Found:** 0

**Key Insights:**
- **Numba constraints**: All data structures must be statically typed for JIT compilation
- **Dual indexing**: Both forward (`groundings`) and relational (`groundings_edges`) views maintained
- **Dependency tracking**: Enables sophisticated constraint propagation during refinement
- **Early exit optimization**: `satisfaction` flag enables short-circuiting when clause fails

---

## Section 2: Clause Loop - Node & Edge Clause Processing (Lines 821-901)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Clause Sequencing**: Process clauses left-to-right, progressively narrowing variable bindings
- **Grounding Consistency**: After binding a variable, filter existing edge groundings to maintain consistency
- **Dependency Graph Construction**: Build constraint relationships between variables for refinement
- **Threshold Validation**: Ensure quantifier requirements (e.g., "at least 50% of neighbors") are met
- **Ground Atoms**: Special case where variable name is a literal entity (e.g., `infected(Alice)` where 'Alice' is a constant)

---

### Loop Setup & Clause Unpacking (Lines 821-828)

```python
satisfaction = True
for i, clause in enumerate(clauses):
    # Unpack clause variables
    clause_type = clause[0]
    clause_label = clause[1]
    clause_variables = clause[2]
    clause_bnd = clause[3]
    _clause_operator = clause[4]
```

**Clause Structure:**
- `clause[0]`: Type - `'node'`, `'edge'`, or `'comparison'`
- `clause[1]`: Label - Predicate name (e.g., `Label('infected')`)
- `clause[2]`: Variables - List of variable names (e.g., `['X']` or `['X', 'Y']`)
- `clause[3]`: Bound - Required interval for satisfaction (e.g., `Interval(0.7, 1.0)`)
- `clause[4]`: Operator - Comparison operator (unused in node/edge clauses)

**Why enumerate?**
- `i` is used to index into `thresholds[i]` for this clause's threshold

---

### Node Clause Processing (Lines 830-854)

**Logic Flow:**
1. Check if variable is a ground atom (literal constant)
2. Get candidate nodes from predicate_map or all nodes
3. Filter candidates by satisfaction (qualified_groundings)
4. Update `groundings[clause_var_1]`
5. **Critical:** Filter existing `groundings_edges` to maintain consistency
6. Check threshold satisfaction

#### Concrete Example 1: First Node Clause

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

Initial State (before any clauses):
  groundings = {}
  groundings_edges = {}
  
Processing Clause 1: infected(X)
  clause_type = 'node'
  clause_label = Label('infected')
  clause_variables = ['X']
  clause_bnd = Interval(0.7, 1.0)  # Require at least 70% certainty

Step 1 (Line 835-838): Get candidate nodes
  allow_ground_rules = False (assume)
  'X' in nodes_set? NO (X is a variable, not literal 'X')
  → Call get_rule_node_clause_grounding('X', {}, predicate_map_node, Label('infected'), nodes)
  
  predicate_map_node[Label('infected')] = [Alice, Bob, Carol, Dave]
  → grounding = [Alice, Bob, Carol, Dave]

Step 2 (Line 841): Filter by satisfaction
  Call get_qualified_node_groundings(interpretations_node, grounding, Label('infected'), Interval(0.7, 1.0))
  
  Check each nodes infected interval:
    Alice: infected = [0.9, 1.0]  → Is [0.9,1.0] ⊆ [0.7,1.0]? YES ✓
    Bob: infected = [0.6, 0.7]    → Is [0.6,0.7] ⊆ [0.7,1.0]? NO (0.6 < 0.7)
    Carol: infected = [0.85, 0.9] → Is [0.85,0.9] ⊆ [0.7,1.0]? YES ✓
    Dave: infected = [0.5, 0.6]   → Is [0.5,0.6] ⊆ [0.7,1.0]? NO
  
  → qualified_groundings = [Alice, Carol]

Step 3 (Line 842): Update groundings
  groundings['X'] = [Alice, Carol]

Step 4 (Line 843-848): Filter existing edge groundings
  qualified_groundings_set = {Alice, Carol}
  for (c1, c2) in groundings_edges:  # Currently empty
    # No iterations (groundings_edges is still empty)

Step 5 (Line 854): Check threshold
  satisfaction = check_node_grounding_threshold_satisfaction(...) and True
  Assuming default threshold (≥1 node): satisfaction = True

Result After Clause 1:
  groundings = {'X': [Alice, Carol]}
  groundings_edges = {}
  satisfaction = True
```

#### Concrete Example 2: Second Node Clause (Variable Already Bound)

```python
Rule: infected(X) ∧ vaccinated(X) ∧ neighbor(X,Y) → risk(Y)

State After infected(X):
  groundings = {'X': [Alice, Carol]}
  groundings_edges = {}

Processing Clause 2: vaccinated(X)
  clause_type = 'node'
  clause_label = Label('vaccinated')
  clause_variables = ['X']
  clause_bnd = Interval(0.5, 1.0)

Step 1 (Line 838): Get candidate nodes
  'X' in groundings? YES
  → Call get_rule_node_clause_grounding('X', groundings, ...)
  
  Since 'X' already in groundings:
    → Returns groundings['X'] = [Alice, Carol]  (reuses existing)
  
  → grounding = [Alice, Carol]

Step 2 (Line 841): Filter by satisfaction
  Check vaccinated intervals:
    Alice: vaccinated = [0.7, 0.8] → ✓
    Carol: vaccinated = [0.3, 0.4] → ✗ (0.3 < 0.5)
  
  → qualified_groundings = [Alice]

Step 3 (Line 842): Update groundings
  groundings['X'] = [Alice]  # Narrowed from [Alice, Carol] to [Alice]

Result After Clause 2:
  groundings = {'X': [Alice]}
  groundings_edges = {}
```

---

### Critical Detail: Edge Filtering After Node Clause (Lines 844-848)

**Problem:** What if a node clause AFTER an edge clause narrows a variable that's in an existing edge?

```python
Rule: neighbor(X,Y) ∧ infected(X) → risk(Y)
```

**Example Scenario:**

```python
State After neighbor(X,Y):
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Dave, Eve, Frank]}
  groundings_edges = {('X','Y'): [(Alice,Bob), (Alice,Dave), (Carol,Eve), (Carol,Frank)]}

Processing infected(X):
  qualified_groundings = [Alice]  # Carol doesn't satisfy infected
  groundings['X'] = [Alice]  # ← X narrowed from [Alice, Carol] to [Alice]
  
  Problem: groundings_edges still has Carol edges!
  → [(Alice,Bob), (Alice,Dave), (Carol,Eve), (Carol,Frank)]
  But Carol no longer in groundings['X']!

Solution (Lines 844-848): Filter edges
  qualified_groundings_set = {Alice}
  
  For (c1, c2) = ('X', 'Y'):
    Line 845: c1 == 'X'? YES
    Line 846: Keep edges where e[0] in {Alice}
      (Alice, Bob) → ✓
      (Alice, Dave) → ✓
      (Carol, Eve) → ✗ (Carol not in {Alice})
      (Carol, Frank) → ✗
    
    groundings_edges[('X','Y')] = [(Alice, Bob), (Alice, Dave)]
  
  Result: Edge groundings now consistent with node groundings!
```

**Why This Matters:**
- Maintains invariant: All edges in `groundings_edges[(v1, v2)]` must have endpoints in `groundings[v1]` and `groundings[v2]`
- Without this filtering, later refinement would fail
- Enables correct Cartesian product calculation in head processing

---

### Edge Clause Processing (Lines 856-901)

**Logic Flow:**
1. Check if edge is a ground atom
2. Get candidate edges
3. Filter by satisfaction
4. Check threshold
5. **Extract unique nodes** from qualified edges into `groundings`
6. Store edges in `groundings_edges`
7. **Build dependency graph** (forward and reverse)

#### Concrete Example 3: First Edge Clause

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

State After infected(X):
  groundings = {'X': [Alice, Carol]}
  groundings_edges = {}
  dependency_graph_neighbors = {}
  dependency_graph_reverse_neighbors = {}

Graph Structure:
  Edges: (Alice, Bob), (Alice, Dave), (Carol, Eve), (Carol, Frank)
  All edges have neighbor predicate with bound [1.0, 1.0]

Processing Clause 2: neighbor(X,Y)
  clause_type = 'edge'
  clause_label = Label('neighbor')
  clause_variables = ['X', 'Y']
  clause_bnd = Interval(0.9, 1.0)

Step 1 (Line 862-865): Get candidate edges
  allow_ground_rules = False
  ('X', 'Y') in edges_set? NO (variables, not literals)
  → Call get_rule_edge_clause_grounding('X', 'Y', groundings, groundings_edges, ...)
  
  'X' in groundings? YES → groundings['X'] = [Alice, Carol]
  'Y' in groundings? NO
  → Case 3: X bound, Y unbound (see Layer 7A analysis)
  
  For Alice:
    neighbors[Alice] = [Bob, Dave]
    → edges: [(Alice, Bob), (Alice, Dave)]
  For Carol:
    neighbors[Carol] = [Eve, Frank]
    → edges: [(Carol, Eve), (Carol, Frank)]
  
  → grounding = [(Alice, Bob), (Alice, Dave), (Carol, Eve), (Carol, Frank)]

Step 2 (Line 868): Filter by satisfaction
  Call get_qualified_edge_groundings(interpretations_edge, grounding, Label('neighbor'), Interval(1.0, 1.0))
  
  Check each edge:
    (Alice, Bob): neighbor = [1.0, 1.0] → ✓
    (Alice, Dave): neighbor = [1.0, 1.0] → ✓
    (Carol, Eve): neighbor = [1.0, 1.0] → ✓
    (Carol, Frank): neighbor = [1.0, 1.0] → ✓

  → qualified_groundings = [(Alice, Bob), (Alice, Dave), (Carol, Eve), (Carol, Frank)]

Step 3 (Line 874): Check threshold (none in this example)
  satisfaction = check_edge_grounding_threshold_satisfaction(...) and True
  → satisfaction = True (assume)

Step 4 (Lines 877-887): Extract unique nodes from edges
  Initialize:
    groundings['X'] = []  # Line 877
    groundings['Y'] = []  # Line 878
    groundings_clause_1_set = {}  # Line 879
    groundings_clause_2_set = {}  # Line 880
  
  For edge (Alice, Bob):
    e[0] = Alice not in {}? YES → append Alice, add to set
    e[1] = Bob not in {}? YES → append Bob, add to set
    groundings['X'] = [Alice], groundings['Y'] = [Bob]
  
  For edge (Alice, Dave):
    e[0] = Alice not in {Alice}? NO → skip
    e[1] = Dave not in {Bob}? YES → append Dave
    groundings['X'] = [Alice], groundings['Y'] = [Bob, Dave]
  
  For edge (Carol, Eve):
    e[0] = Carol not in {Alice}? YES → append Carol
    e[1] = Eve not in {Bob, Dave}? YES → append Eve
    groundings['X'] = [Alice, Carol], groundings['Y'] = [Bob, Dave, Eve]
  
  For edge (Carol, Frank):
    e[0] = Carol not in {Alice, Carol}? NO → skip
    e[1] = Frank not in {Bob, Dave, Eve}? YES → append Frank
    groundings['X'] = [Alice, Carol], groundings['Y'] = [Bob, Dave, Eve, Frank]

Step 5 (Line 890): Store edge groundings
  groundings_edges[('X', 'Y')] = [(Alice, Bob), (Alice, Dave), (Carol, Eve), (Carol, Frank)]

Step 6 (Lines 892-901): Build dependency graph
  
  Forward (X → Y):
    Line 894: 'X' not in dependency_graph_neighbors? YES
    Line 895: dependency_graph_neighbors['X'] = ['Y']
  
  Reverse (Y ← X):
    Line 898: 'Y' not in dependency_graph_reverse_neighbors? YES
    Line 899: dependency_graph_reverse_neighbors['Y'] = ['X']

Result After Clause 2:
  groundings = {
    'X': [Alice, Carol],
    'Y': [Bob, Dave, Eve, Frank]
  }
  groundings_edges = {
    ('X', 'Y'): [(Alice, Bob), (Alice, Dave), (Carol, Eve), (Carol, Frank)]
  }
  dependency_graph_neighbors = {'X': ['Y']}
  dependency_graph_reverse_neighbors = {'Y': ['X']}
```

---

### Dependency Graph Construction (Lines 892-901)

**Purpose:** Track which variables constrain which other variables for refinement propagation.

**Construction Logic:**

```python
# Forward dependency: clause_var_1 → clause_var_2
if clause_var_1 not in dependency_graph_neighbors:
    dependency_graph_neighbors[clause_var_1] = [clause_var_2]
elif clause_var_2 not in dependency_graph_neighbors[clause_var_1]:
    dependency_graph_neighbors[clause_var_1].append(clause_var_2)

# Reverse dependency: clause_var_2 ← clause_var_1
if clause_var_2 not in dependency_graph_reverse_neighbors:
    dependency_graph_reverse_neighbors[clause_var_2] = [clause_var_1]
elif clause_var_1 not in dependency_graph_reverse_neighbors[clause_var_2]:
    dependency_graph_reverse_neighbors[clause_var_2].append(clause_var_1)
```

**Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ age(Y,Z) → risk(Z)

After neighbor(X,Y):
  dependency_graph_neighbors = {'X': ['Y']}
  dependency_graph_reverse_neighbors = {'Y': ['X']}

After age(Y,Z):
  dependency_graph_neighbors = {'X': ['Y'], 'Y': ['Z']}
  dependency_graph_reverse_neighbors = {'Y': ['X'], 'Z': ['Y']}

Dependency Chain: X → Y → Z
  - If X narrows, Y must be re-filtered (Y depends on X)
  - If Y narrows, Z must be re-filtered (Z depends on Y)
```

**Why Both Forward and Reverse?**
- **Forward (neighbors):** Used by `refine_groundings()` to propagate changes downstream
  - "If X changes, which variables need updating?" → Look at `dependency_graph_neighbors['X']`
- **Reverse:** Used to propagate changes upstream (less common, but enables bidirectional refinement)

---

### Ground Atoms Feature (Lines 835-836, 862-863)

**What are Ground Atoms?**
Rules where a variable is actually a literal constant, not a variable to be bound.

**Example:**

```python
Rule: vaccinated(Alice) ∧ neighbor(Alice,Y) → protected(Y)
```

Here `'Alice'` is a constant, not a variable to ground.

**Handling:**

```python
# Node clause
if allow_ground_rules and clause_var_1 in nodes_set:
    grounding = [clause_var_1]  # Treat variable as literal node
else:
    grounding = get_rule_node_clause_grounding(...)  # Normal grounding

# Edge clause
if allow_ground_rules and (clause_var_1, clause_var_2) in edges_set:
    grounding = [(clause_var_1, clause_var_2)]  # Treat as literal edge
else:
    grounding = get_rule_edge_clause_grounding(...)
```

**Purpose:** Enable rules with specific constants (rare use case).

---

**Key Insights:**

- **Progressive Narrowing:** Each clause filters existing groundings, creating a funnel effect
- **Consistency Maintenance:** Lines 844-848 are critical for maintaining invariants between `groundings` and `groundings_edges`
- **Dependency Tracking:** Edge clauses build the constraint graph needed for refinement
- **Dual Extraction:** Edge clauses populate both node groundings (extracted from edges) and edge groundings (original edges)
- **Duplicate Prevention:** Lines 882-887 use sets to ensure each node appears only once in groundings
- **Early Exit:** Threshold failure sets `satisfaction=False`, enabling break at line 912

---

## Section 3: Clause Loop - Comparison & Refinement (Lines 903-914)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Comparison Clauses**: Unimplemented feature for arithmetic comparisons between variables (e.g., `X < Y`)
- **Constraint Propagation**: Refinement process that propagates variable narrowing through dependency graph
- **Fixed-Point Iteration**: Refinement continues until no more changes occur
- **Bidirectional Propagation**: Changes flow both forward and backward through dependency graph
- **Early Exit**: Break immediately when satisfaction becomes false to avoid wasted work

---

### Comparison Clause Handling (Lines 903-905)

```python
# This is a comparison clause
else:
    pass
```

**Status:** Completely unimplemented - empty stub.

**What Would Comparison Clauses Do?**

Hypothetical examples:
```python
# Compare variable values
Rule: age(X, A) ∧ age(Y, B) ∧ A > B → older(X, Y)

# Compare bounds
Rule: infected(X) ∧ infected(Y) ∧ X.lower > Y.upper → more_infected(X, Y)

# Arithmetic constraints
Rule: score(X, S1) ∧ score(Y, S2) ∧ S1 + S2 > 100 → high_combined(X, Y)
```

**Why Unimplemented?**
- Complex semantics: How to handle interval arithmetic?
- Performance: Comparisons might require evaluating all combinations
- Use case: Rare in typical logic programming scenarios

**Current Workaround:**
Users must implement comparisons in annotation functions or post-processing.

---

### Refinement Call (Lines 907-909)

```python
# Refine the subsets based on any updates
if satisfaction:
    refine_groundings(clause_variables, groundings, groundings_edges, 
                     dependency_graph_neighbors, dependency_graph_reverse_neighbors)
```

**Why Only If Satisfaction?**
- If satisfaction is false, we'll break at line 912 anyway
- No point refining if rule will be discarded
- Optimization: Avoid expensive refinement when unnecessary

**When Does Refinement Happen?**
After EVERY clause (node, edge, or comparison) that passes satisfaction check.

---

### What Does Refinement Do?

**Purpose:** Propagate variable narrowing through the dependency graph to maintain consistency.

**Algorithm Overview:**

```
Input: clause_variables (just processed), groundings, groundings_edges, dependency_graph

1. Mark clause_variables as "just refined"
2. While there are newly refined variables:
   a. For each newly refined variable V:
      - For each forward neighbor N (V → N):
        * Filter edges: Keep only edges where V endpoint matches current V groundings
        * Extract new N groundings from filtered edges
        * Mark N as newly refined
      - For each reverse neighbor R (R → V):
        * Filter edges: Keep only edges where V endpoint matches current V groundings
        * Extract new R groundings from filtered edges
        * Mark R as newly refined
   b. Newly refined variables become the next iteration's "just refined"
3. Continue until no new variables are refined (fixed point)

Output: Updated groundings and groundings_edges (consistent with dependency graph)
```

---

### Concrete Example: Refinement Propagation

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ vaccinated(Y) → risk(X)

Initial Graph:
  Nodes: Alice, Bob, Carol, Dave, Eve
  Edges: (Alice, Bob), (Alice, Carol), (Carol, Dave), (Dave, Eve)
  
  infected(Alice) = [0.9, 1.0]
  infected(Carol) = [0.8, 0.9]
  
  vaccinated(Bob) = [0.7, 0.8]
  vaccinated(Carol) = [0.6, 0.7]
  vaccinated(Dave) = [0.3, 0.4]  # Too low!
  vaccinated(Eve) = [0.9, 1.0]

Processing:

Clause 1: infected(X)
  groundings = {'X': [Alice, Carol]}
  
Clause 2: neighbor(X,Y)
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Carol, Dave, Eve]}
  groundings_edges = {
    ('X', 'Y'): [(Alice, Bob), (Alice, Carol), (Carol, Dave), (Carol, Eve)]
  }
  dependency_graph_neighbors = {'X': ['Y']}
  dependency_graph_reverse_neighbors = {'Y': ['X']}

Clause 3: vaccinated(Y)
  BEFORE refinement:
    Get candidates: groundings['Y'] = [Bob, Carol, Dave, Eve]
    Filter by vaccinated >= 0.5:
      Bob: [0.7, 0.8] ✓
      Carol: [0.6, 0.7] ✓
      Dave: [0.3, 0.4] ✗ (too low)
      Eve: [0.9, 1.0] ✓
    
    qualified_groundings = [Bob, Carol, Eve]
    groundings['Y'] = [Bob, Carol, Eve]  # Dave removed!
  
  REFINEMENT TRIGGERED (line 909):
    clause_variables = ['Y']  # Y just got narrowed
    
    Call refine_groundings(['Y'], groundings, groundings_edges, ...)
    
    Iteration 1:
      variables_just_refined = ['Y']
      
      For refined_variable = 'Y':
        'Y' in dependency_graph_neighbors? NO (Y has no forward neighbors)
        'Y' in dependency_graph_reverse_neighbors? YES → ['X']
        
        For reverse_neighbor = 'X':
          old_edge_groundings = [(Alice, Bob), (Alice, Carol), (Carol, Dave), (Carol, Eve)]
          new_node_groundings = groundings['Y'] = [Bob, Carol, Eve]
          
          Filter edges where edge[1] (target) in [Bob, Carol, Eve]:
            (Alice, Bob): Bob in [Bob, Carol, Eve]? YES ✓
            (Alice, Carol): Carol in [Bob, Carol, Eve]? YES ✓
            (Carol, Dave): Dave in [Bob, Carol, Eve]? NO ✗ (Dave removed!)
            (Carol, Eve): Eve in [Bob, Carol, Eve]? YES ✓
          
          qualified_groundings = [(Alice, Bob), (Alice, Carol), (Carol, Eve)]
          
          Extract new X groundings:
            Alice (from (Alice, Bob))
            Alice (from (Alice, Carol)) - duplicate, skip
            Carol (from (Carol, Eve))
          
          groundings['X'] = [Alice, Carol]  # Unchanged
          groundings_edges[('X', 'Y')] = [(Alice, Bob), (Alice, Carol), (Carol, Eve)]
          
          Mark 'X' as newly refined? NO ('X' already in all_variables_refined)
      
      new_variables_refined = []  # No new variables
    
    Iteration 2:
      variables_just_refined = []  # Empty - STOP
    
    Fixed point reached!

Result After Clause 3 + Refinement:
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Carol, Eve]}
  groundings_edges = {('X', 'Y'): [(Alice, Bob), (Alice, Carol), (Carol, Eve)]}
  
  Edge (Carol, Dave) REMOVED because Dave doesn't satisfy vaccinated!
  Consistency maintained: All edges have endpoints in groundings.
```

---

### Why Refinement is Critical

**Without Refinement:**
```python
After vaccinated(Y):
  groundings['Y'] = [Bob, Carol, Eve]  # Dave removed
  groundings_edges[('X','Y')] = [(Alice, Bob), (Alice, Carol), (Carol, Dave), (Carol, Eve)]
  
Problem: Edge (Carol, Dave) still exists, but Dave not in groundings['Y']!
Inconsistency: Edge groundings don't match node groundings
```

**With Refinement:**
```python
After refinement:
  groundings['Y'] = [Bob, Carol, Eve]
  groundings_edges[('X','Y')] = [(Alice, Bob), (Alice, Carol), (Carol, Eve)]
  
Consistency: All edges have both endpoints in their respective groundings!
```

**What Refinement Prevents:**
1. **Dangling references:** Edges pointing to removed nodes
2. **Invalid combinations:** Cartesian products including invalid entities
3. **Cascading inconsistencies:** Changes in one variable affecting connected variables

---

### Concrete Example: Multi-Hop Propagation

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ age(Y,Z) → complex(Z)

Dependency Chain: X → Y → Z

State After All Clauses (before refinement):
  groundings = {'X': [Alice, Bob], 'Y': [Carol, Dave, Eve], 'Z': [10, 20, 30, 40]}
  groundings_edges = {
    ('X', 'Y'): [(Alice, Carol), (Alice, Dave), (Bob, Eve)],
    ('Y', 'Z'): [(Carol, 10), (Carol, 20), (Dave, 30), (Eve, 40)]
  }

Now suppose we narrow X:
  groundings['X'] = [Alice]  # Bob removed

Refinement Propagation:

Iteration 1: Refine X
  X → Y dependency
  Filter ('X', 'Y') edges where source in [Alice]:
    (Alice, Carol) ✓
    (Alice, Dave) ✓
    (Bob, Eve) ✗ (Bob removed)
  
  groundings_edges[('X', 'Y')] = [(Alice, Carol), (Alice, Dave)]
  Extract Y groundings: [Carol, Dave]
  groundings['Y'] = [Carol, Dave]  # Eve removed!
  
  Mark Y as newly refined

Iteration 2: Refine Y
  Y → Z dependency
  Filter ('Y', 'Z') edges where source in [Carol, Dave]:
    (Carol, 10) ✓
    (Carol, 20) ✓
    (Dave, 30) ✓
    (Eve, 40) ✗ (Eve removed)
  
  groundings_edges[('Y', 'Z')] = [(Carol, 10), (Carol, 20), (Dave, 30)]
  Extract Z groundings: [10, 20, 30]
  groundings['Z'] = [10, 20, 30]  # 40 removed!
  
  Mark Z as newly refined

Iteration 3: Refine Z
  Z has no forward neighbors → STOP

Result:
  Narrowing X → Narrowed Y → Narrowed Z
  All edges consistent throughout the chain!
```

---

### Early Exit (Lines 911-913)

```python
# If satisfaction is false, break
if not satisfaction:
    break
```

**When Does This Happen?**
- Threshold check fails (lines 854, 874)
- Explicit check: `len(qualified_groundings) == 0` (BUG-149 recommends this)

**What Happens After Break?**
- Remaining clauses not processed
- `satisfaction = False` when we reach line 918
- Line 918 condition fails: `if satisfaction:` is false
- Skip all head processing
- Return empty `applicable_rules_node` and `applicable_rules_edge`
- **Result:** Rule doesn't fire for this timestep

**Example:**
```python
Rule: infected(X) ∧ vaccinated(X) ∧ neighbor(X,Y) → protected(Y)

Clause 1: infected(X) → X = [Alice, Bob]
Clause 2: vaccinated(X) → X = [] (no overlap!)
  satisfaction = False (threshold: need at least 1)
  BREAK at line 913

Clauses 3+ not processed
Line 918: if satisfaction → False, skip head processing
Return: ([], [])  # No rules to apply
```

---

### Bugs Found

**BUG-152 (LOW): Comparison Clauses Completely Unimplemented**
**Location:** Lines 903-905
**Description:**
The comparison clause branch is an empty stub:
```python
else:
    pass
```

This means:
- Comparison operators in clauses are silently ignored
- No error message or warning to user
- Rules with comparisons may appear to work but actually don't

**Impact:**
- User confusion if they try to use comparison clauses
- Silent failure mode (no error)
- Documented feature that doesn't work?

**Fix:**
Either:
1. **Implement comparison clauses** (large feature)
2. **Raise error** if comparison clause detected:
   ```python
   else:
       raise NotImplementedError("Comparison clauses not yet supported")
   ```
3. **Document limitation** in user-facing docs

---

**BUG-153 (LOW): Refinement Called Even for First Clause**
**Location:** Line 909
**Description:**
Refinement is called after EVERY clause, including the first one:

```python
for i, clause in enumerate(clauses):
    # Process clause
    # ...
    
    if satisfaction:
        refine_groundings(clause_variables, ...)  # Always called
```

For the first clause:
- No edges exist yet in `groundings_edges`
- No dependencies in `dependency_graph_neighbors/reverse_neighbors`
- Refinement loop executes but does nothing (no neighbors to refine)

**Impact:**
- Unnecessary function call overhead
- Minor performance impact (loop executes once, finds no neighbors, exits)
- Not a correctness bug, just inefficiency

**Fix:**
Skip refinement for first clause:
```python
if satisfaction and i > 0:  # Skip for first clause
    refine_groundings(clause_variables, ...)
```

Or check if dependency graph is non-empty:
```python
if satisfaction and len(dependency_graph_neighbors) > 0:
    refine_groundings(clause_variables, ...)
```

**Trade-off:** Code clarity vs minor performance gain. Current code is simpler.

---

**BUG-154 (MEDIUM): No Validation After Refinement**
**Location:** Line 909
**Description:**
After refinement, groundings might become empty due to constraint propagation, but there's no check:

```python
refine_groundings(clause_variables, groundings, ...)
# No validation here!
# Continue to next clause or head processing
```

**Example Scenario:**
```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ vaccinated(Y)

Clause 1: infected(X) → X = [Alice, Bob]
Clause 2: neighbor(X,Y) → Y = [Carol, Dave, Eve]
  groundings_edges[('X','Y')] = [(Alice, Carol), (Bob, Dave), (Bob, Eve)]

Clause 3: vaccinated(Y) → Y = [] (no one vaccinated!)
  Refinement propagates back to X
  Filters ('X','Y') edges where Y in [] → all removed
  Extracts new X: [] (empty!)
  
Result: groundings['X'] = [], groundings['Y'] = []
But satisfaction still True! (threshold check passed before refinement)
```

**Impact:**
- Empty groundings after refinement could cause issues in head processing
- Division by zero in later calculations
- Empty Cartesian products

**Current Safety Net:**
Line 950 (Section 4) has final satisfaction check:
```python
satisfaction = check_all_clause_satisfaction(...)
```

This should catch empty groundings, but it's late in the process.

**Fix:**
Add validation after refinement:
```python
refine_groundings(clause_variables, ...)

# Check if refinement emptied any groundings
for var in groundings:
    if len(groundings[var]) == 0:
        satisfaction = False
        break
```

---

**Key Insights:**

- **Comparison clauses:** Completely unimplemented - empty stub that silently does nothing
- **Refinement is critical:** Maintains consistency between `groundings` and `groundings_edges` after variable narrowing
- **Fixed-point iteration:** Refinement continues until no more changes occur (transitive closure)
- **Bidirectional propagation:** Changes flow both ways (forward via `dependency_graph_neighbors`, backward via `dependency_graph_reverse_neighbors`)
- **Early exit optimization:** Break immediately when `satisfaction=False` to avoid wasted work
- **Multi-hop propagation:** Refinement can cascade through long dependency chains (X → Y → Z → ...)

---

## Section 4: Head Processing - Node & Edge Rules (Lines 918-1221)
**Status:** 🔄 In Progress (Node Rules Complete)

**Theoretical Concepts:**
- **Head Instantiation**: Converting variable bindings into concrete rule instances ready for application
- **Ground Atoms in Head**: Variables that don't appear in body (new entities to create)
- **Provenance Collection**: Recording which entities satisfied each clause (atom trace)
- **Annotation Aggregation**: Collecting intervals for annotation function input
- **Dynamic Graph Mutation**: Adding new nodes/edges discovered during grounding
- **Instance-Specific Filtering**: For edge rules, each head edge must be validated separately

---

### Part A: Node Rule Head Processing (Lines 918-1017)

**High-Level Flow:**
1. Apply head functions (if present) to compute head variable binding
2. Handle ground atoms (head variable not in body)
3. Loop through each head grounding (one iteration = one rule instance)
4. For each head grounding:
   a. Recheck satisfaction (refinement might have invalidated)
   b. Build qualified_nodes and qualified_edges (provenance)
   c. Build annotations (for annotation function)
   d. Add new nodes to graph (if ground atom)
   e. Append rule instance to applicable_rules_node

---

#### Step 1: Head Function Application (Lines 928-931)

```python
# Apply any function in the head to determine the head grounding
head_var_groundings, is_func = _determine_node_head_vars(head_fns, head_fns_vars, groundings, head_functions)
if is_func:
    groundings[head_var_1] = head_var_groundings
```

**Purpose:** Allow head functions to compute derived entities.

**Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → cluster(hash(X,Y))

After body grounding:
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Dave]}

Head function application:
  head_fns = ['hash']
  head_fns_vars = [['X', 'Y']]
  
  Call _determine_node_head_vars(...)
  → hash function computes: [cluster_1, cluster_2, cluster_3, cluster_4]
     (one cluster ID for each X-Y combination)
  
  is_func = True
  groundings['cluster'] = [cluster_1, cluster_2, cluster_3, cluster_4]

Result: Head variable 'cluster' now has groundings computed by function
```

**Without head function:**
```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

is_func = False
groundings[head_var_1] not updated (already has groundings from body)
```

---

#### Step 2: Ground Atom Handling (Lines 933-941)

**What is a Ground Atom in Head?**
A head variable that doesn't appear in the rule body.

```python
head_var_1_in_nodes = head_var_1 in nodes
add_head_var_node_to_graph = False

if allow_ground_rules and head_var_1_in_nodes:
    groundings[head_var_1] = numba.typed.List([head_var_1])
elif head_var_1 not in groundings:
    if not head_var_1_in_nodes:
        add_head_var_node_to_graph = True
    groundings[head_var_1] = numba.typed.List([head_var_1])
```

**Three Cases:**

**Case 1: Normal variable (appears in body)**
```python
Rule: infected(X) → risk(X)

head_var_1 = 'X'
'X' in groundings? YES (from body clause)
→ Skip all lines 936-941
→ Use existing groundings['X'] = [Alice, Bob]
```

**Case 2: Ground atom that exists in graph**
```python
Rule: vaccinated(Y) → protected(Alice)  # Alice is constant in head

head_var_1 = 'Alice'
'Alice' in nodes? YES (Alice exists)
allow_ground_rules = True

Line 936-937:
  groundings['Alice'] = ['Alice']
  add_head_var_node_to_graph = False

Result: Update existing node Alice
```

**Case 3: Ground atom that doesn't exist (create new node)**
```python
Rule: infected(X) → spreads_to(NewNode)  # NewNode doesn't exist

head_var_1 = 'NewNode'
'NewNode' in nodes? NO
'NewNode' in groundings? NO

Line 938-941:
  'NewNode' not in groundings? YES
  'NewNode' in nodes? NO
  add_head_var_node_to_graph = True
  groundings['NewNode'] = ['NewNode']

Result: NewNode will be added to graph at line 1013-1014
```

---

#### Step 3: Loop Through Head Groundings (Lines 943-1017)

```python
for head_grounding in groundings[head_var_1]:
    # Process each head grounding as separate rule instance
    # ...
```

**Key Insight:** Each head grounding becomes ONE rule instance.

**Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

After body grounding:
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Dave, Eve]}
  groundings_edges = {('X','Y'): [(Alice,Bob), (Alice,Dave), (Carol,Eve)]}

Head variable: Y
groundings[head_var_1] = groundings['Y'] = [Bob, Dave, Eve]

Loop iterations:
  Iteration 1: head_grounding = 'Bob'
    → Create rule instance for risk(Bob)
  
  Iteration 2: head_grounding = 'Dave'
    → Create rule instance for risk(Dave)
  
  Iteration 3: head_grounding = 'Eve'
    → Create rule instance for risk(Eve)

Result: 3 rule instances appended to applicable_rules_node
```

---

#### Step 4: Initialize Instance Data Structures (Lines 944-947)

```python
qualified_nodes = numba.typed.List.empty_list(numba.typed.List.empty_list(node_type))
qualified_edges = numba.typed.List.empty_list(numba.typed.List.empty_list(edge_type))
annotations = numba.typed.List.empty_list(numba.typed.List.empty_list(interval.interval_type))
edges_to_be_added = (numba.typed.List.empty_list(node_type), numba.typed.List.empty_list(node_type), rule_edges[-1])
```

**Purpose:** Initialize containers for this specific rule instance.

**Structure:**
- `qualified_nodes`: List of lists - one sublist per clause
- `qualified_edges`: List of lists - one sublist per clause
- `annotations`: List of lists - one sublist per clause
- `edges_to_be_added`: Tuple (sources, targets, label) - for infer_edges (always empty for node rules)

---

#### Step 5: Final Satisfaction Check (Lines 949-952)

```python
# Check for satisfaction one more time in case the refining process has changed the groundings
satisfaction = check_all_clause_satisfaction(interpretations_node, interpretations_edge, clauses, thresholds, groundings, groundings_edges)
if not satisfaction:
    continue
```

**Why Recheck?**
- Earlier refinement might have invalidated groundings
- This is per-head-grounding check (specific to this iteration)
- Safety net: Ensures we don't create invalid rule instances

**Example Where Recheck Matters:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

After body grounding:
  groundings = {'X': [Alice], 'Y': [Bob, Carol]}
  groundings_edges = {('X','Y'): [(Alice, Bob), (Alice, Carol)]}

Head variable: Y
Loop through [Bob, Carol]:

Iteration 1: head_grounding = 'Bob'
  Recheck satisfaction:
    infected(X) with X=[Alice]? ✓
    neighbor(X,Y) with edges=[(Alice,Bob), (Alice,Carol)]? ✓
  satisfaction = True
  → Continue, create rule instance for risk(Bob)

Iteration 2: head_grounding = 'Carol'
  Suppose between iterations, Alice became uninfected (external update - unlikely but possible in parallel execution)
  Recheck satisfaction:
    infected(X) with X=[Alice]? ✗ (Alice no longer infected!)
  satisfaction = False
  → continue (skip this iteration)
  → No rule instance for risk(Carol)
```

**In Practice:**
This recheck is likely redundant for most cases since groundings don't change between loop iterations. But it's defensive programming for edge cases.

---

#### Step 6: Build Provenance and Annotations (Lines 954-1010)

**Purpose:** For each clause, collect:
1. **Qualified nodes/edges** (provenance for atom trace)
2. **Annotations** (intervals for annotation function)

```python
for i, clause in enumerate(clauses):
    clause_type = clause[0]
    clause_label = clause[1]
    clause_variables = clause[2]
    
    if clause_type == 'node':
        # Process node clause
    elif clause_type == 'edge':
        # Process edge clause
    else:
        # Comparison clause (skip)
        pass
```

---

##### Node Clause Provenance (Lines 959-977)

**Two Tasks:**
1. Build qualified_nodes (if atom_trace enabled)
2. Build annotations (if annotation function specified)

**Logic:**

```python
if clause_type == 'node':
    clause_var_1 = clause_variables[0]
    
    # 1. Qualified nodes (provenance)
    if atom_trace:
        if clause_var_1 == head_var_1:
            qualified_nodes.append([head_grounding])
        else:
            qualified_nodes.append(groundings[clause_var_1])
        qualified_edges.append([])  # Node clause has no edges
    
    # 2. Annotations (for annotation function)
    if ann_fn != '':
        a = []
        if clause_var_1 == head_var_1:
            a.append(interpretations_node[head_grounding].world[clause_label])
        else:
            for qn in groundings[clause_var_1]:
                a.append(interpretations_node[qn].world[clause_label])
        annotations.append(a)
```

**Concrete Example:**

```python
Rule: infected(X) ∧ vaccinated(X) ∧ neighbor(X,Y) → risk(Y)
Annotation function: 'max'
atom_trace = True

State:
  groundings = {'X': [Alice], 'Y': [Bob, Carol]}
  groundings_edges = {('X','Y'): [(Alice, Bob), (Alice, Carol)]}

Current head_grounding = 'Bob'

Clause 1: infected(X)
  clause_var_1 = 'X'
  'X' == head_var_1 ('Y')? NO
  
  Provenance:
    qualified_nodes.append(groundings['X'])
    → qualified_nodes = [[Alice]]
    qualified_edges.append([])
    → qualified_edges = [[]]
  
  Annotations:
    for qn in [Alice]:
      a.append(interpretations_node['Alice'].world[Label('infected')])
    → a = [Interval(0.9, 1.0)]
    annotations.append(a)
    → annotations = [[Interval(0.9, 1.0)]]

Clause 2: vaccinated(X)
  clause_var_1 = 'X'
  'X' == 'Y'? NO
  
  Provenance:
    qualified_nodes.append([Alice])
    → qualified_nodes = [[Alice], [Alice]]
    qualified_edges.append([])
    → qualified_edges = [[], []]
  
  Annotations:
    a = [Interval(0.7, 0.8)]  # Alice's vaccinated interval
    annotations.append(a)
    → annotations = [[Interval(0.9, 1.0)], [Interval(0.7, 0.8)]]

Clause 3: neighbor(X,Y)
  (Edge clause - see next section)

After all clauses:
  qualified_nodes = [[Alice], [Alice], []]
  qualified_edges = [[], [], [(Alice, Bob)]]
  annotations = [[Interval(0.9, 1.0)], [Interval(0.7, 0.8)], [Interval(1.0, 1.0)]]
```

**Special Case: clause_var == head_var**

```python
Rule: infected(X) → risk(X)

head_var_1 = 'X'
head_grounding = 'Alice'

Clause 1: infected(X)
  clause_var_1 = 'X'
  'X' == head_var_1? YES
  
  Provenance:
    qualified_nodes.append([head_grounding])
    → qualified_nodes = [['Alice']]  # Specific grounding, not all X values
  
  Annotations:
    a.append(interpretations_node['Alice'].world[Label('infected')])
    → annotations = [[Interval(0.9, 1.0)]]
    # Only Alice's interval, not all infected nodes
```

---

##### Edge Clause Provenance (Lines 979-1007)

**More Complex:** Must filter edges based on head variable.

**Logic:**

```python
elif clause_type == 'edge':
    clause_var_1, clause_var_2 = clause_variables[0], clause_variables[1]
    
    # 1. Qualified edges (provenance)
    if atom_trace:
        qualified_nodes.append([])  # Edge clause has no nodes
        
        if clause_var_1 == head_var_1:
            es = [e for e in groundings_edges[(clause_var_1, clause_var_2)] if e[0] == head_grounding]
            qualified_edges.append(es)
        elif clause_var_2 == head_var_1:
            es = [e for e in groundings_edges[(clause_var_1, clause_var_2)] if e[1] == head_grounding]
            qualified_edges.append(es)
        else:
            qualified_edges.append(groundings_edges[(clause_var_1, clause_var_2)])
    
    # 2. Annotations (similar filtering)
    if ann_fn != '':
        # ... similar logic
```

**Concrete Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)

State:
  groundings_edges = {('X','Y'): [(Alice, Bob), (Alice, Dave), (Carol, Eve)]}
  head_var_1 = 'Y'
  head_grounding = 'Bob'

Clause 2: neighbor(X,Y)
  clause_var_1 = 'X', clause_var_2 = 'Y'
  
  'X' == head_var_1 ('Y')? NO
  'Y' == head_var_1? YES → Filter edges where target == 'Bob'
  
  es = [e for e in [(Alice, Bob), (Alice, Dave), (Carol, Eve)] if e[1] == 'Bob']
  es = [(Alice, Bob)]
  
  qualified_edges.append([(Alice, Bob)])

Result: Only the edge that leads TO Bob is recorded in provenance
Why? This instance is updating risk(Bob), so we only care about edges involving Bob.
```

**Three Cases:**

**Case A: clause_var_1 == head_var (source matches)**
```python
Rule: neighbor(X,Y) → source_risk(X)

head_var_1 = 'X'
head_grounding = 'Alice'
clause_var_1 = 'X', clause_var_2 = 'Y'

Filter: e[0] == 'Alice'
→ Keep edges where Alice is source
```

**Case B: clause_var_2 == head_var (target matches)**
```python
Rule: neighbor(X,Y) → target_risk(Y)

head_var_1 = 'Y'
head_grounding = 'Bob'
clause_var_1 = 'X', clause_var_2 = 'Y'

Filter: e[1] == 'Bob'
→ Keep edges where Bob is target
```

**Case C: Neither matches**
```python
Rule: neighbor(X,Y) ∧ infected(Z) → complex(Z)

head_var_1 = 'Z'
head_grounding = 'Frank'
clause: neighbor(X,Y)

'X' == 'Z'? NO
'Y' == 'Z'? NO

No filter - include all edges
→ All (X,Y) edges that satisfied the clause
```

---

#### Step 7: Add Ground Atom to Graph (Lines 1012-1014)

```python
# Now that we're sure that the rule is satisfied, we add the head to the graph if needed (only for ground rules)
if add_head_var_node_to_graph:
    _add_node(head_var_1, neighbors, reverse_neighbors, nodes, interpretations_node)
```

**When Does This Happen?**
Only if `add_head_var_node_to_graph = True` (set at line 940).

**Example:**

```python
Rule: infected(X) → spreads_to(NewNode)

head_var_1 = 'NewNode'
'NewNode' not in graph initially

Line 940: add_head_var_node_to_graph = True

After satisfaction check passes:
  Line 1014: _add_node('NewNode', ...)
  → Creates new node 'NewNode' in graph
  → Initializes interpretations_node['NewNode']
  → Updates neighbors/reverse_neighbors
  → Adds to nodes list

Result: Dynamic graph expansion during reasoning!
```

---

#### Step 8: Append Rule Instance (Line 1017)

```python
# For each grounding add a rule to be applied
applicable_rules_node.append((head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_be_added))
```

**What Gets Appended:**

```python
Instance = (
    head_grounding,      # str - e.g., 'Bob'
    annotations,         # List[List[Interval]] - per clause
    qualified_nodes,     # List[List[str]] - per clause (provenance)
    qualified_edges,     # List[List[Tuple]] - per clause (provenance)
    edges_to_be_added    # Tuple ([], [], Label('')) - empty for node rules
)
```

**Complete Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
Annotation function: 'max'
atom_trace = True

Final state for head_grounding = 'Bob':

Instance = (
    'Bob',  # Update risk(Bob)
    
    [
        [Interval(0.9, 1.0)],     # Clause 1: infected(Alice)
        [Interval(1.0, 1.0)]      # Clause 2: neighbor(Alice, Bob)
    ],
    
    [
        ['Alice'],                # Clause 1: Alice satisfied infected
        []                        # Clause 2: edge clause has no nodes
    ],
    
    [
        [],                       # Clause 1: node clause has no edges
        [('Alice', 'Bob')]        # Clause 2: this edge satisfied neighbor
    ],
    
    ([], [], Label(''))           # No edges to add
)

applicable_rules_node.append(Instance)
```

---

### Complete Example: Node Rule End-to-End

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
Annotation function: 'max'
atom_trace = True

Graph:
  Nodes: Alice, Bob, Carol, Dave
  Edges: (Alice, Bob), (Alice, Dave), (Carol, Dave)
  
  infected(Alice) = [0.9, 1.0]
  infected(Carol) = [0.8, 0.9]

After body grounding (Sections 2-3):
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Dave]}
  groundings_edges = {('X', 'Y'): [(Alice, Bob), (Alice, Dave), (Carol, Dave)]}

Head Processing:

Step 1: Head function? NO (no function)

Step 2: Ground atom? NO (Y appears in body)

Step 3: Loop through groundings['Y'] = [Bob, Dave]

Iteration 1: head_grounding = 'Bob'
  Step 4: Initialize data structures
  Step 5: Recheck satisfaction → True
  Step 6: Build provenance and annotations
    Clause 1: infected(X)
      qualified_nodes = [['Alice', 'Carol']]
      annotations = [[Interval(0.9, 1.0), Interval(0.8, 0.9)]]
    
    Clause 2: neighbor(X,Y) where Y='Bob'
      Filter edges where target == 'Bob': [(Alice, Bob)]
      qualified_edges = [[], [('Alice', 'Bob')]]
      annotations = [[...], [Interval(1.0, 1.0)]]
  
  Step 7: Add ground atom? NO
  Step 8: Append instance
    applicable_rules_node.append((
        'Bob',
        [[Interval(0.9, 1.0), Interval(0.8, 0.9)], [Interval(1.0, 1.0)]],
        [['Alice', 'Carol'], []],
        [[], [('Alice', 'Bob')]],
        ([], [], Label(''))
    ))

Iteration 2: head_grounding = 'Dave'
  (Similar process)
  Filter edges where target == 'Dave': [(Alice, Dave), (Carol, Dave)]
  
  applicable_rules_node.append((
        'Dave',
        [[Interval(0.9, 1.0), Interval(0.8, 0.9)], [Interval(1.0, 1.0), Interval(1.0, 1.0)]],
        [['Alice', 'Carol'], []],
        [[], [('Alice', Dave), ('Carol', Dave)]],
        ([], [], Label(''))
    ))

Result: 2 rule instances ready for application
  1. Update risk(Bob) using max([0.9, 0.8], [1.0])
  2. Update risk(Dave) using max([0.9, 0.8], [1.0, 1.0])
```

---

### Bugs Found in Node Rule Processing

**BUG-155 (MEDIUM): Recheck Satisfaction Inside Loop is Expensive**
**Location:** Line 950
**Description:**
```python
for head_grounding in groundings[head_var_1]:
    # ...
    satisfaction = check_all_clause_satisfaction(...)
```

This rechecks ALL clauses for EVERY head grounding.

**Impact:**
- If head has 100 groundings, satisfaction is checked 100 times
- Each check iterates through all clauses
- Expensive: O(head_groundings × clauses × entities_per_clause)
- Redundant: Groundings don't change between loop iterations

**When Necessary:**
Only if groundings could change between iterations (not the case here).

**Fix:**
Move check outside loop:
```python
satisfaction = check_all_clause_satisfaction(...)
if not satisfaction:
    return ([], [])  # Exit early

for head_grounding in groundings[head_var_1]:
    # No recheck needed
```

---

**BUG-156 (LOW): Ground Atom Logic Inconsistency**
**Location:** Lines 936-941
**Description:**
```python
if allow_ground_rules and head_var_1_in_nodes:
    groundings[head_var_1] = [head_var_1]
elif head_var_1 not in groundings:
    if not head_var_1_in_nodes:
        add_head_var_node_to_graph = True
    groundings[head_var_1] = [head_var_1]
```

**Issue:** Both branches set `groundings[head_var_1] = [head_var_1]`, but with different conditions.

**Scenario:**
```python
allow_ground_rules = False
head_var_1 = 'Alice'
'Alice' in nodes? YES
'Alice' not in groundings? YES

Line 936: Condition False (allow_ground_rules is False)
Line 938: Condition True (Alice not in groundings)
Line 939: 'Alice' in nodes? YES → add_head_var_node_to_graph = False
Line 941: groundings['Alice'] = ['Alice']
```

**Problem:** Why check `allow_ground_rules` in first condition but not second?

**Impact:** Inconsistent semantics for ground atoms.

---

**BUG-157 (MEDIUM): No Validation of Empty Groundings Before Loop**
**Location:** Line 943
**Description:**
```python
for head_grounding in groundings[head_var_1]:
    # ...
```

If `groundings[head_var_1]` is empty, loop doesn't execute. No error or warning.

**Impact:**
- Rule silently doesn't fire
- No rule instances created
- Empty return: `applicable_rules_node = []`

**Should Detect:** Empty head groundings indicates earlier bug or unsatisfiable rule.

**Fix:**
```python
if len(groundings[head_var_1]) == 0:
    # This shouldn't happen if satisfaction checks work correctly
    # But defensive check is good
    return ([], [])

for head_grounding in groundings[head_var_1]:
    # ...
```

---

**Key Insights:**

- **One loop iteration = one rule instance:** Each head grounding becomes a separate applicable rule
- **Filtering by head variable:** Edge provenance is filtered to only include edges involving the specific head grounding
- **Dynamic graph expansion:** Ground atoms can create new nodes during reasoning
- **Provenance structure:** Parallel lists (qualified_nodes, qualified_edges, annotations) indexed by clause
- **Annotation aggregation:** All entities satisfying a clause contribute intervals to annotation function
- **Safety check overhead:** Recheck satisfaction for every head grounding (likely redundant)

---

### Part B: Edge Rule Head Processing (Lines 1019-1221)

**High-Level Flow:**
1. Apply head functions (if present) to compute head variable bindings for BOTH source and target
2. Handle ground atoms for BOTH head variables independently
3. Determine infer_edges mode (create new edges vs use existing)
4. Build valid_edge_groundings (Cartesian product or filtered existing edges)
5. **For EACH valid edge grounding** (critical difference from node rules):
   a. Create temp copies of groundings and groundings_edges
   b. Narrow temp structures to specific edge (7-way filtering)
   c. Refine temp structures through dependency graph
   d. Recheck satisfaction with temp structures
   e. Handle infer_edges case (prevent self-loops, accumulate edges)
   f. Build qualified_nodes and qualified_edges (7-way branching × 2 sections)
   g. Add new nodes/edges to graph (if ground atoms)
   h. Append rule instance to applicable_rules_edge

**Key Differences from Node Rules:**
- **Two head variables** instead of one (source, target)
- **Temp structure isolation** required for each edge validation
- **Seven-way branching** for matching clause variables to head variables
- **infer_edges mode** adds combinatorial complexity
- **Significantly more complex**: 203 lines vs 100 lines for node rules

---

#### Step 1: Head Function Application (Lines 1024-1028)

```python
# Apply any function in the head to determine the head grounding
head_var_groundings, is_func = _determine_edge_head_vars(head_fns, head_fns_vars, groundings, head_functions)
if is_func[0]:
    groundings[head_var_1] = head_var_groundings[0]
if is_func[1]:
    groundings[head_var_2] = head_var_groundings[1]
```

**Purpose:** Allow head functions to compute derived entities for BOTH source and target independently.

**Key Difference from Node Rules:**
- `_determine_edge_head_vars()` returns TWO lists: one for each head variable
- `is_func` is a 2-tuple indicating which variables were computed
- Each head variable can independently use a function or not

**Example 1: Functions for both variables**
```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(hash(X), hash(Y))

After body grounding:
  groundings = {'X': [Alice, Carol], 'Y': [Bob, Dave]}

Head function application:
  head_fns = ['hash', 'hash']
  head_fns_vars = [['X'], ['Y']]
  
  Call _determine_edge_head_vars(...)
  → Returns:
    head_var_groundings[0] = [hash(Alice), hash(Carol)]  # For source
    head_var_groundings[1] = [hash(Bob), hash(Dave)]     # For target
    is_func = [True, True]
  
  groundings['source'] = [hash(Alice), hash(Carol)]
  groundings['target'] = [hash(Bob), hash(Dave)]
```

**Example 2: Function for one variable only**
```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(cluster(X), Y)

is_func = [True, False]
groundings['source'] = [cluster_1, cluster_2]  # From function
groundings['target'] = [Bob, Dave]             # From body (unchanged)
```

---

#### Step 2: Ground Atom Handling (Lines 1030-1058)

**Complexity:** Edge rules must handle ground atoms for TWO variables, with interdependencies.

```python
1031-1032: Check if head variables exist in nodes
1033-1035: Initialize flags for graph additions
1036-1039: Handle allow_ground_rules case (both variables)
1041-1048: Handle missing groundings case (both variables)
1050-1052: Determine if edge should be added to graph
1054-1058: Extract groundings and determine infer_edges mode
```

**The Four Cases Per Variable:**

| Condition | Action | Lines | Flag Set |
|-----------|--------|-------|----------|
| `allow_ground_rules=True` AND `var in nodes` | Treat as ground atom (existing) | 1036-1039 | None |
| `var not in groundings` AND `var not in nodes` | Must add new node | 1041-1048 | `add_head_var_X_node_to_graph=True` |
| `var not in groundings` AND `var in nodes` | Add to groundings (existing) | 1041-1048 | Flag=False |
| `var in groundings` | Already grounded by body | N/A | None |

**Edge Addition Logic (Lines 1050-1052):**
```python
if not head_var_1_in_nodes and not head_var_2_in_nodes:
    add_head_edge_to_graph = True
```

**🐛 BUG-158 (HIGH):** Edge only added if BOTH nodes don't exist!

**COLTON NOTE: CHECK WITH DYUMAN**

---

#### Step 3: Determine infer_edges Mode & Build Valid Edge Groundings (Lines 1057-1071)

**infer_edges Mode Determination:**
```python
source, target, _ = rule_edges
infer_edges = True if source != '' and target != '' else False
```

**Two Distinct Modes:**

| Mode | Condition | Edge Construction | Example Size |
|------|-----------|-------------------|--------------|
| **infer_edges=True** | `source != ''` and `target != ''` | ALL combinations (Cartesian product) | 1000 × 800 = 800,000 |
| **infer_edges=False** | Either is `''` | Only existing edges in graph | Limited by graph topology |

**🐛 BUG-159 (MEDIUM):** No validation that `source`/`target` match `head_var_1`/`head_var_2`.

**Valid Edge Groundings Construction (Lines 1063-1071):**
```python
valid_edge_groundings = numba.typed.List.empty_list(edge_type)
for g1 in head_var_1_groundings:
    for g2 in head_var_2_groundings:
        if infer_edges:
            valid_edge_groundings.append((g1, g2))  # ALL combinations
        else:
            if (g1, g2) in edges_set:
                valid_edge_groundings.append((g1, g2))  # Only existing
```

**Example: infer_edges=True**
```python
Rule: infected(X) ∧ susceptible(Y) → risk(X,Y) [infer_edges]

head_var_1_groundings = [Alice, Bob, Carol]  # 3 infected
head_var_2_groundings = [Dave, Eve]          # 2 susceptible

valid_edge_groundings = [
    (Alice,Dave), (Alice,Eve),
    (Bob,Dave), (Bob,Eve),
    (Carol,Dave), (Carol,Eve)
]  # 6 combinations
```

**Example: infer_edges=False**
```python
Rule: property(X) ∧ property(Y) ∧ connected(X,Y) → strong(X,Y)

head_var_1_groundings = [Alice, Bob, Carol]
head_var_2_groundings = [Bob, Carol, Dave]

Graph edges: (Alice,Bob), (Bob,Carol)

valid_edge_groundings = [
    (Alice,Bob),   # Exists in graph ✓
    # (Alice,Carol) - Not in graph, skip
    # (Alice,Dave) - Not in graph, skip
    (Bob,Carol)    # Exists in graph ✓
    # (Bob,Dave) - Not in graph, skip
    # ... etc
]  # Only 2 edges
```

#### Step 4: Edge Grounding Loop & Temp Structure Creation (Lines 1073-1083)

**Critical Difference from Node Rules:**
Node rules can iterate `groundings` directly. Edge rules CANNOT because different edges need different grounding contexts.

```python
1073: for valid_e in valid_edge_groundings:
1074:     head_var_1_grounding, head_var_2_grounding = valid_e[0], valid_e[1]
1075-1078: Initialize empty qualified_nodes, qualified_edges, annotations, edges_to_be_added
1082-1083: Create temp copies
```

**Why Temp Structures?**

**Problem:** Edge rules have two head variables, creating complex dependencies.

```python
Rule: property(X) ∧ property(Y) ∧ connected(X,Y) → strong(X,Y)

Body groundings after clause processing:
  X = [Alice, Bob, Carol]
  Y = [Bob, Carol, Dave]
  connected_edges = [(Alice,Bob), (Bob,Carol), (Carol,Dave)]

Valid edge groundings (existing only):
  (Alice,Bob), (Bob,Carol), (Carol,Dave)
```

**For edge (Alice,Bob):**
- Must validate that body clauses are satisfied when X=Alice, Y=Bob
- Must filter `connected_edges` to only those involving Alice or Bob
- Cannot use shared `groundings` because next edge (Bob,Carol) needs different filtering

**For edge (Bob,Carol):**
- Must validate with X=Bob, Y=Carol
- Must filter `connected_edges` to only those involving Bob or Carol
- **Different filtering than (Alice,Bob)!**

**Solution:** Create temp copies for each edge:
```python
temp_groundings = groundings.copy()
temp_groundings_edges = groundings_edges.copy()

# Narrow to specific edge
temp_groundings[head_var_1] = [head_var_1_grounding]  # X = [Alice]
temp_groundings[head_var_2] = [head_var_2_grounding]  # Y = [Bob]
```

**Concrete Trace-Through: Why Shared Groundings Fail**

Let's trace through the exact same rule to see what happens WITH and WITHOUT temp structures:

**Rule:** `property(X) ∧ property(Y) ∧ connected(X,Y) → strong(X,Y)`

**After body grounding:**
```python
groundings = {
    'X': [Alice, Bob, Carol],
    'Y': [Bob, Carol, Dave]
}

groundings_edges = {
    ('X', 'Y'): [(Alice,Bob), (Bob,Carol), (Carol,Dave)]
}

valid_edge_groundings = [(Alice,Bob), (Bob,Carol), (Carol,Dave)]
```

---

**❌ WITHOUT Temp Structures (Shared groundings - WRONG):**

**Iteration 1: Processing edge (Alice, Bob)**
```python
# Line 1073: First iteration
valid_e = (Alice, Bob)
head_var_1_grounding = Alice
head_var_2_grounding = Bob

# NO temp copy - use shared groundings directly
# Lines 1089-1101: Filter groundings_edges for (Alice,Bob)
for c1, c2 in groundings_edges.keys():  # ('X','Y')
    # Branch 1 matches: c1==head_var_1 and c2==head_var_2
    groundings_edges[('X','Y')] = [e for e in groundings_edges[('X','Y')] 
                                    if e == (Alice, Bob)]
    # Result: groundings_edges[('X','Y')] = [(Alice,Bob)]

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([(Alice,Bob)])  # ✓ Correct for this iteration

# State after iteration 1:
groundings_edges = {
    ('X', 'Y'): [(Alice,Bob)]  # ⚠️ PERMANENTLY MODIFIED!
}
```

**Iteration 2: Processing edge (Bob, Carol)**
```python
# Line 1073: Second iteration
valid_e = (Bob, Carol)
head_var_1_grounding = Bob
head_var_2_grounding = Carol

# Lines 1089-1101: Filter groundings_edges for (Bob,Carol)
for c1, c2 in groundings_edges.keys():
    groundings_edges[('X','Y')] = [e for e in groundings_edges[('X','Y')] 
                                    if e == (Bob, Carol)]
    
    # Filter input: [(Alice,Bob)]  ← Already corrupted from iteration 1!
    # Filter condition: e == (Bob, Carol)
    # (Alice,Bob) == (Bob,Carol)? NO
    # Result: groundings_edges[('X','Y')] = []  ❌ EMPTY!

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([])  # ❌ WRONG! Should be [(Bob,Carol)]

# The rule instance for strong(Bob,Carol) has NO PROVENANCE!
```

**Iteration 3: Processing edge (Carol, Dave)**
```python
# Lines 1089-1101: Filter groundings_edges for (Carol,Dave)
# Filter input: []  ← Already empty!
# Result: groundings_edges[('X','Y')] = []  ❌ Still empty

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([])  # ❌ WRONG! Should be [(Carol,Dave)]
```

**Summary WITHOUT temp structures:**
- Iteration 1: qualified_edges = `[(Alice,Bob)]` ✓ Correct
- Iteration 2: qualified_edges = `[]` ❌ Missing provenance
- Iteration 3: qualified_edges = `[]` ❌ Missing provenance

---

**✅ WITH Temp Structures (Correct Approach):**

**Iteration 1: Processing edge (Alice, Bob)**
```python
# Line 1073: First iteration
valid_e = (Alice, Bob)
head_var_1_grounding = Alice
head_var_2_grounding = Bob

# Lines 1082-1083: Create FRESH temp copies
temp_groundings = groundings.copy()  
# → {'X': [Alice,Bob,Carol], 'Y': [Bob,Carol,Dave]}

temp_groundings_edges = groundings_edges.copy()
# → {('X','Y'): [(Alice,Bob), (Bob,Carol), (Carol,Dave)]}

# Lines 1087-1088: Narrow temp structures
temp_groundings['X'] = [Alice]
temp_groundings['Y'] = [Bob]

# Lines 1089-1101: Filter TEMP structures for (Alice,Bob)
temp_groundings_edges[('X','Y')] = [e for e in temp_groundings_edges[('X','Y')] 
                                     if e == (Alice, Bob)]
# Result: temp_groundings_edges[('X','Y')] = [(Alice,Bob)]

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([(Alice,Bob)])  # ✓ Correct

# State after iteration 1:
# ORIGINAL groundings_edges is UNTOUCHED!
groundings_edges = {
    ('X', 'Y'): [(Alice,Bob), (Bob,Carol), (Carol,Dave)]  # ✓ Still pristine
}
# temp structures are discarded (go out of scope)
```

**Iteration 2: Processing edge (Bob, Carol)**
```python
# Line 1073: Second iteration
valid_e = (Bob, Carol)
head_var_1_grounding = Bob
head_var_2_grounding = Carol

# Lines 1082-1083: Create NEW FRESH temp copies
temp_groundings = groundings.copy()
# → {'X': [Alice,Bob,Carol], 'Y': [Bob,Carol,Dave]}

temp_groundings_edges = groundings_edges.copy()
# → {('X','Y'): [(Alice,Bob), (Bob,Carol), (Carol,Dave)]}  ✓ FULL LIST!

# Lines 1087-1088: Narrow to specific edge
temp_groundings['X'] = [Bob]
temp_groundings['Y'] = [Carol]

# Lines 1089-1101: Filter TEMP structures for (Bob,Carol)
temp_groundings_edges[('X','Y')] = [e for e in temp_groundings_edges[('X','Y')] 
                                     if e == (Bob, Carol)]
    
# Filter input: [(Alice,Bob), (Bob,Carol), (Carol,Dave)]  ✓ FRESH!
# Filter condition: e == (Bob, Carol)
# Result: temp_groundings_edges[('X','Y')] = [(Bob,Carol)]  ✓ Correct!

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([(Bob,Carol)])  # ✓ Correct!
```

**Iteration 3: Processing edge (Carol, Dave)**
```python
# Lines 1082-1083: Create NEW FRESH temp copies AGAIN
temp_groundings_edges = groundings_edges.copy()
# → {('X','Y'): [(Alice,Bob), (Bob,Carol), (Carol,Dave)]}  ✓ FULL LIST AGAIN!

# Lines 1089-1101: Filter for (Carol,Dave)
temp_groundings_edges[('X','Y')] = [(Carol,Dave)]  ✓ Correct!

# Lines 1156-1158: Build qualified_edges
qualified_edges.append([(Carol,Dave)])  # ✓ Correct!
```

**Summary WITH temp structures:**
- Iteration 1: qualified_edges = `[(Alice,Bob)]` ✓ Correct
- Iteration 2: qualified_edges = `[(Bob,Carol)]` ✓ Correct
- Iteration 3: qualified_edges = `[(Carol,Dave)]` ✓ Correct

---

**Side-by-Side Comparison:**

| Iteration | Without Temp (WRONG) | With Temp (CORRECT) |
|-----------|---------------------|---------------------|
| **1: (Alice,Bob)** | qualified_edges = `[(Alice,Bob)]` ✓ | qualified_edges = `[(Alice,Bob)]` ✓ |
| **After 1** | `groundings_edges[('X','Y')]` = `[(Alice,Bob)]` ❌ | `groundings_edges[('X','Y')]` = `[(Alice,Bob), (Bob,Carol), (Carol,Dave)]` ✓ |
| **2: (Bob,Carol)** | qualified_edges = `[]` ❌ | qualified_edges = `[(Bob,Carol)]` ✓ |
| **After 2** | `groundings_edges[('X','Y')]` = `[]` ❌ | `groundings_edges[('X','Y')]` = `[(Alice,Bob), (Bob,Carol), (Carol,Dave)]` ✓ |
| **3: (Carol,Dave)** | qualified_edges = `[]` ❌ | qualified_edges = `[(Carol,Dave)]` ✓ |

---

**Why Node Rules Don't Need This:**

Node rules use a different approach that doesn't mutate shared structures:

```python
Rule: infected(X) ∧ neighbor(X,Y) → risk(X)

# Line 943: for head_grounding in groundings['X']:  # Alice, then Bob
# Line 945: qualified_edges = []  # NEW list each iteration!

# Iteration 1: head_grounding = Alice
# Lines 985-987: Build qualified_edges for neighbor(X,Y)
if clause_var_1 == head_var_1:  # 'X' == 'X'
    es = [e for e in groundings_edges[('X','Y')] if e[0] == head_grounding]
    # Filter at BUILD time, not MODIFY time
    # Result: [(Alice,Bob), (Alice,Carol)]
    qualified_edges.append(es)

# Iteration 2: head_grounding = Bob
# Line 945: qualified_edges = []  # FRESH list!
# Lines 985-987:
es = [e for e in groundings_edges[('X','Y')] if e[0] == head_grounding]
    # Uses ORIGINAL groundings_edges (never modified)
    # Result: [(Bob,Dave)]
    qualified_edges.append(es)
```

**Key difference:** 
- Node rules: Create NEW `qualified_edges` each iteration (line 945), filter at BUILD time using list comprehensions
- Edge rules (attempting without temp): Would MUTATE `groundings_edges`, corrupting it for subsequent iterations

---

#### Step 5: Seven-Way Filtering of temp_groundings_edges (Lines 1089-1101)

**Purpose:** Narrow temp_groundings_edges to only include edges that involve the current head grounding being processed.

**Why?** Because later code (lines 1156-1175 and 1180-1206) will use temp_groundings_edges to build provenance structures. We need those structures to only reference edges relevant to THIS specific rule instance.

**Compare to lines 985-992 for node rules.**

**The Seven Branches:**

```python
for c1, c2 in temp_groundings_edges.keys():
    if c1 == head_var_1 and c2 == head_var_2:
        # Branch 1: Both match, same order
        # Keep only edges where e == (hv1_grounding, hv2_grounding)
    elif c1 == head_var_2 and c2 == head_var_1:
        # Branch 2: Both match, reversed order
        # Keep only edges where e == (hv2_grounding, hv1_grounding)
    elif c1 == head_var_1:
        # Branch 3: First var matches hv1
        # Keep only edges where e[0] == hv1_grounding
    elif c2 == head_var_1:
        # Branch 4: Second var matches hv1
        # Keep only edges where e[1] == hv1_grounding
    elif c1 == head_var_2:
        # Branch 5: First var matches hv2
        # Keep only edges where e[0] == hv2_grounding
    elif c2 == head_var_2:
        # Branch 6: Second var matches hv2
        # Keep only edges where e[1] == hv2_grounding
    # Branch 7: MISSING else clause!
```

**Example:**
```python
Current head grounding: (Alice, Bob)
head_var_1 = 'X', head_var_2 = 'Y'
head_var_1_grounding = Alice, head_var_2_grounding = Bob

temp_groundings_edges = {
    ('X','Y'): [(Alice,Bob), (Alice,Carol), (Bob,Dave)],
    ('Y','Z'): [(Bob,Carol), (Carol,Dave)]
}

After filtering:
  ('X','Y'): Branch 1 matches
    → Filter: e == (Alice,Bob)
    → Result: [(Alice,Bob)]
    
  ('Y','Z'): Branch 6 matches (c2 == head_var_2)
    → Filter: e[1] == Bob (second element is Y which is head_var_2)
    → Result: [(Bob,Carol)] only (Carol,Dave) removed
```
---

#### Step 6: Refinement & Satisfaction Recheck (Lines 1103-1110)

```python
1103: refine_groundings(head_variables, temp_groundings, temp_groundings_edges, 
                        dependency_graph_neighbors, dependency_graph_reverse_neighbors)

1107: satisfaction = check_all_clause_satisfaction(interpretations_node, interpretations_edge, 
                                                    clauses, thresholds, temp_groundings, 
                                                    temp_groundings_edges)
1109-1110: if not satisfaction: continue
```

**Purpose:** 
1. **Refinement:** Propagate constraints through dependency graph to ensure consistency
2. **Recheck satisfaction:** Verify all clauses still satisfied after narrowing to specific edge

**Why Recheck?**

After narrowing temp structures to specific edge, some clauses might no longer be satisfied:

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ property(Y) → risk(X,Y)

Body groundings:
  X = [Alice, Bob]
  Y = [Carol, Dave]
  neighbor_edges = [(Alice,Carol), (Bob,Dave)]

Valid edge: (Alice,Carol)

After narrowing:
  temp_groundings['X'] = [Alice]
  temp_groundings['Y'] = [Carol]
  temp_groundings_edges[('X','Y')] = [(Alice,Carol)]

Recheck satisfaction:
  infected(Alice)? Check interpretations_node[Alice].world[infected]
  neighbor(Alice,Carol)? Check temp_groundings_edges
  property(Carol)? Check interpretations_node[Carol].world[property]

If any clause fails → continue (skip this edge)
```

---

#### Step 7: infer_edges Handling & Self-Loop Prevention (Lines 1112-1117)

```python
if infer_edges:
    # Prevent self loops while inferring edges if the clause variables are not the same
    if source != target and head_var_1_grounding == head_var_2_grounding:
        continue
    edges_to_be_added[0].append(head_var_1_grounding)
    edges_to_be_added[1].append(head_var_2_grounding)
```

**Purpose:** For inferred edges, accumulate source-target pairs to be added to graph later.

**Self-Loop Prevention Logic:**
```python
if source != target and head_var_1_grounding == head_var_2_grounding:
    continue
```

**Interpretation:**
- If `source != target` (different clause variables): Prevent self-loops when groundings are same
- If `source == target` (same clause variable): Allow self-loops

**Example:**
```python
Rule: infected(X) ∧ susceptible(Y) → risk(X,Y) [infer_edges]
source='X', target='Y'  # Different variables

If groundings produce (Alice,Alice):
  source != target → True ('X' != 'Y')
  head_var_1_grounding == head_var_2_grounding → True ('Alice' == 'Alice')
  Condition: True AND True → SKIP (continue)
  Result: Self-loop (Alice,Alice) NOT created ✓
```

---

#### Step 8: Building Qualified Nodes & Edges (Lines 1119-1207)

**Purpose:** For each body clause, record which entities satisfied it and collect their intervals.

**Structure:**
- **Lines 1119-1146:** Node clauses
- **Lines 1147-1207:** Edge clauses

**For Node Clauses (Lines 1124-1146):**

```python
if clause_type == 'node':
    clause_var_1 = clause_variables[0]
    
    # 1. Build qualified_nodes (if atom_trace)
    if atom_trace:
        if clause_var_1 == head_var_1:
            qualified_nodes.append([head_var_1_grounding])
        elif clause_var_1 == head_var_2:
            qualified_nodes.append([head_var_2_grounding])
        else:
            qualified_nodes.append(temp_groundings[clause_var_1])
        qualified_edges.append([])  # Empty for node clause
    
    # 2. Build annotations (if ann_fn != '')
    if ann_fn != '':
        a = []
        if clause_var_1 == head_var_1:
            a.append(interpretations_node[head_var_1_grounding].world[clause_label])
        elif clause_var_1 == head_var_2:
            a.append(interpretations_node[head_var_2_grounding].world[clause_label])
        else:
            for qn in temp_groundings[clause_var_1]:
                a.append(interpretations_node[qn].world[clause_label])
        annotations.append(a)
```

**Three Cases:**
1. **Clause var = head_var_1:** Use specific head_var_1_grounding
2. **Clause var = head_var_2:** Use specific head_var_2_grounding  
3. **Clause var is intermediate:** Use all from temp_groundings

**For Edge Clauses (Lines 1147-1207):**

**SEVEN-WAY BRANCHING × 2 SECTIONS = 14 BRANCHES TOTAL**

**Section 1: atom_trace (Lines 1156-1175) - Build qualified_edges**
```python
if atom_trace:
    qualified_nodes.append([])  # Empty for edge clause
    if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
        es = [e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] 
              if e == (head_var_1_grounding, head_var_2_grounding)]
        qualified_edges.append(es)
    elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
        es = [e for e in temp_groundings_edges[(clause_var_1, clause_var_2)] 
              if e == (head_var_2_grounding, head_var_1_grounding)]
        qualified_edges.append(es)
    # ... 5 more branches ...
```

**Section 2: ann_fn (Lines 1178-1206) - Build annotations**
```python
if ann_fn != '':
    a = []
    if clause_var_1 == head_var_1 and clause_var_2 == head_var_2:
        for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
            if e[0] == head_var_1_grounding and e[1] == head_var_2_grounding:
                a.append(interpretations_edge[e].world[clause_label])
    elif clause_var_1 == head_var_2 and clause_var_2 == head_var_1:
        for e in temp_groundings_edges[(clause_var_1, clause_var_2)]:
            if e[0] == head_var_2_grounding and e[1] == head_var_1_grounding:
                a.append(interpretations_edge[e].world[clause_label])
    # ... 5 more branches ...
    annotations.append(a)
```

---

#### Step 9: Graph Addition & Rule Application (Lines 1209-1221)

**Graph Addition (Lines 1210-1215):**
```python
if add_head_var_1_node_to_graph and head_var_1_grounding == head_var_1:
    _add_node(head_var_1, ...)
if add_head_var_2_node_to_graph and head_var_2_grounding == head_var_2:
    _add_node(head_var_2, ...)
if add_head_edge_to_graph and (head_var_1, head_var_2) == (head_var_1_grounding, head_var_2_grounding):
    _add_edge(head_var_1, head_var_2, ..., label.Label(''), ...)  # Empty label!
```


**Rule Application (Lines 1220-1221):**
```python
e = (head_var_1_grounding, head_var_2_grounding)
applicable_rules_edge.append((e, annotations, qualified_nodes, qualified_edges, edges_to_be_added))
```

**Data Structure:** 5-tuple per rule instance
1. **e:** Edge tuple (source, target)
2. **annotations:** List of interval lists (one per clause)
3. **qualified_nodes:** List of node lists (provenance for node clauses)
4. **qualified_edges:** List of edge lists (provenance for edge clauses)
5. **edges_to_be_added:** Tuple (sources, targets, label) for infer_edges mode

This tuple is consumed by `_update_edge()` to apply the rule and update interpretations.


### Key Insights: Edge Rules vs Node Rules

**Complexity Comparison:**

| Aspect | Node Rules | Edge Rules | Ratio |
|--------|-----------|-----------|-------|
| Lines of code | 100 | 203 | 2.0× |
| Head variables | 1 | 2 | 2× |
| Ground atom cases | 3 | 4 per var × 2 vars | ~3× |
| Filtering branches | 3 | 7 | 2.3× |
| Temp structures | None | Yes (2 dicts) | N/A |
| Bugs found | 5 | 14 | 2.8× |

**Architectural Patterns:**

1. **Isolation via Temp Copies:**
   - Node rules: Iterate `groundings` directly, filter inline with comprehensions
   - Edge rules: Create temp copies, narrow them, refine them, validate independently
   - **Rationale:** Two head variables create complex interdependencies

2. **Seven-Way Branching:**
   - Matching clause variables to head variables has 7 cases:
     - 2 exact matches (same order, reversed)
     - 4 partial matches (one var matches)
     - 1 no match (intermediate variables)
   - **Duplicated:** Between temp_groundings_edges filtering, atom_trace, and ann_fn sections
   - **Impact:** Maintenance burden, bug multiplication

3. **Mode Switching (infer_edges):**
   - **True:** Create new edges (Cartesian product) - O(n²) space
   - **False:** Use existing edges - O(edges in graph) space
   - **Critical difference:** Determines whether rule discovers new relationships or annotates existing ones

4. **Self-Loop Semantics:**
   - Different handling between modes
   - Ambiguous whether self-loops are valid
   - Depends on undocumented parser behavior

**Performance Characteristics:**

| Operation | Node Rules | Edge Rules | Notes |
|-----------|-----------|-----------|-------|
| Head grounding loop | O(N) | O(E) or O(N²) | E=existing edges, N²=inferred |
| Per-iteration work | Simple | Complex (temp copy + refine) | ~3× more work |
| Memory per iteration | None | 2 dict copies | Significant overhead |
| Total complexity | O(N × C) | O(E × C × F) | C=clauses, F=filtering work |

**Ground Rule Semantics:**

Both node and edge rules support ground atoms (head variables not in body), but:
- **Node rules:** Add single node to graph
- **Edge rules:** Add source node, target node, AND edge (broken by BUG-158, BUG-171)
- **Current state:** Ground edge rules are partially broken

**Provenance Collection:**

Both build parallel structures (qualified_nodes, qualified_edges, annotations) indexed by clause:
- **Purpose:** Track which entities satisfied each clause
- **Used by:** Annotation functions (aggregate intervals) and atom trace (explainability)
- **Structure:** One list per clause, containing entities that matched

**Safety Checks:**

- **Node rules:** Satisfaction rechecked once per head grounding (line 950)
- **Edge rules:** Satisfaction rechecked once per valid edge (line 1107)
- **Question:** Are these rechecks necessary? Refinement shouldn't invalidate satisfaction
- **Performance impact:** Potentially redundant O(clauses) work per iteration

