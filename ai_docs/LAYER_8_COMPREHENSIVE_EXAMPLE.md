# Layer 8: _ground_rule() - Comprehensive Execution Example

This example traces through the complete execution of `_ground_rule()` for four different rules, demonstrating all critical branches including ground atoms, multi-hop dependency graphs, refinement propagation, and both edge rule modes.

**Reference:** For detailed line-by-line analysis, see `GROUND_RULE_ANALYSIS.md`.

---

## Scenario: Disease Outbreak Simulation

### Graph Structure

```
Nodes: Alice, Bob, Carol, Dave
Edges: (Alice, Bob), (Alice, Carol), (Bob, Dave)

     Alice
      / \
     v   v
   Bob   Carol
    |
    v
   Dave
```

### Initial Interpretations

```python
interpretations_node = {
    'Alice': World({'infected': [0.9, 1.0]}),      # Infected (static)
    'Bob':   World({'susceptible': [0.8, 1.0]}),   # Susceptible
    'Carol': World({'susceptible': [0.7, 0.9]}),   # Susceptible
    'Dave':  World({'susceptible': [0.6, 0.8]})    # Susceptible (for R2)
}

interpretations_edge = {
    ('Alice', 'Bob'):   World({'neighbor': [1.0, 1.0]}),
    ('Alice', 'Carol'): World({'neighbor': [1.0, 1.0]}),
    ('Bob', 'Dave'):    World({'neighbor': [1.0, 1.0]})
}
```

### Rules

| ID | Rule | Type | Key Features |
|----|------|------|--------------|
| R1 | `infected(Alice) → patient_zero(Alice)` | Node | Ground atom (allow_ground_rules) |
| R2 | `infected(X) ∧ neighbor(X,Y) ∧ neighbor(Y,Z) ∧ susceptible(Z) → at_risk(Z)` | Node | Multi-hop dependency, refinement |
| R3 | `infected(X) ∧ neighbor(X,Y) → exposure(X,Y)` | Edge | infer_edges=True |
| R4 | `neighbor(X,Y) ∧ infected(X) → alert(X,Y)` | Edge | infer_edges=False |

---

## Output Structure Reference

Each rule produces **applicable rule instances** - complete data packages for rule application.

**Node Rule Instance:** `(head_grounding, annotations, qualified_nodes, qualified_edges, edges_to_be_added)`
- `head_grounding`: Node to update (e.g., `'Dave'`)
- `annotations`: `List[List[Interval]]` - intervals from each clause for annotation function
- `qualified_nodes`: `List[List[str]]` - nodes that satisfied each clause (provenance)
- `qualified_edges`: `List[List[Tuple]]` - edges that satisfied each clause (provenance)
- `edges_to_be_added`: `([], [], Label(''))` - empty for node rules

**Edge Rule Instance:** `(edge, annotations, qualified_nodes, qualified_edges, edges_to_be_added)`
- `edge`: Edge tuple to update (e.g., `('Alice', 'Bob')`)
- Other fields same as node rules
- `edges_to_be_added`: Contains source/target lists for infer_edges mode

For detailed explanation, see GROUND_RULE_ANALYSIS.md section "What is an Applicable Rule Instance?"

---

## Part 1: Rule R1 - Ground Atom Node Rule

### `infected(Alice) → patient_zero(Alice)` [allow_ground_rules=True]

This rule uses **ground atoms** - literal constants instead of variables. Both `Alice` in the body and head are the actual node name, not variables to be grounded.

#### Section 1: Initialization

```python
# Rule parameters extracted
rule_type = 'node'
head_var_1 = 'Alice'  # Note: This is the literal string 'Alice'
clauses = [('node', Label('infected'), ['Alice'], [0.7, 1.0], '')]

# Data structures initialized
groundings = {}
groundings_edges = {}
dependency_graph_neighbors = {}
dependency_graph_reverse_neighbors = {}
satisfaction = True
```

#### Section 2: Clause Processing - Ground Atom Branch

**Clause 1: `infected(Alice)`**

```python
clause_var_1 = 'Alice'

# Line 835-836: Ground atom detection
allow_ground_rules = True
'Alice' in nodes_set?  →  YES (Alice is a node in the graph)

# BRANCH: Ground atom path (not variable grounding)
grounding = ['Alice']  # Use literal node name directly
```

**Contrast with variable-based grounding:**
- Normal rule `infected(X)`: Would call `get_rule_node_clause_grounding()` to find all nodes with `infected` predicate
- Ground atom rule `infected(Alice)`: Directly uses `['Alice']` as the only candidate

```python
# Line 841: Filter by satisfaction
qualified_groundings = get_qualified_node_groundings(
    interpretations_node, ['Alice'], Label('infected'), [0.7, 1.0]
)
# Check: infected(Alice) = [0.9, 1.0] ⊇ [0.7, 1.0]? YES
qualified_groundings = ['Alice']

# Line 842: Update groundings
groundings['Alice'] = ['Alice']

# Line 854: Threshold check
satisfaction = True
```

**State after clause processing:**
```python
groundings = {'Alice': ['Alice']}
groundings_edges = {}
dependency_graph_neighbors = {}  # No edge clauses, no dependencies
```

#### Section 4: Head Processing - Ground Atom in Head

```python
# Line 934-937: Ground atom handling for head
head_var_1 = 'Alice'
head_var_1_in_nodes = 'Alice' in nodes  →  YES

# Line 936-937: allow_ground_rules branch
allow_ground_rules = True AND head_var_1_in_nodes = True
groundings['Alice'] = ['Alice']  # Already set, but confirmed
add_head_var_node_to_graph = False  # Node exists
```

**Head grounding loop:** Single iteration with `head_grounding = 'Alice'`

```python
# Line 950: Satisfaction recheck
satisfaction = check_all_clause_satisfaction(...)  →  True

# Lines 959-977: Build provenance (clause 1 is node clause)
# clause_var_1 ('Alice') == head_var_1 ('Alice')? YES
qualified_nodes = [['Alice']]  # Specific grounding
qualified_edges = [[]]
annotations = [[Interval(0.9, 1.0)]]  # Alice's infected interval
```

#### Output

```python
applicable_rules_node.append((
    'Alice',                              # head_grounding
    [[Interval(0.9, 1.0)]],              # annotations
    [['Alice']],                          # qualified_nodes
    [[]],                                 # qualified_edges
    ([], [], Label(''))                   # edges_to_be_added (empty)
))
```

**Result:** 1 rule instance - update `patient_zero(Alice)`

---

## Part 2: Rule R2 - Multi-Clause Node Rule with Refinement

### `infected(X) ∧ neighbor(X,Y) ∧ neighbor(Y,Z) ∧ susceptible(Z) → at_risk(Z)`

This rule demonstrates the core grounding algorithm: dependency graph construction, implicit variable narrowing, and refinement propagation.

#### Section 1: Initialization

```python
rule_type = 'node'
head_var_1 = 'Z'
clauses = [
    ('node', Label('infected'), ['X'], [0.7, 1.0], ''),
    ('edge', Label('neighbor'), ['X', 'Y'], [0.9, 1.0], ''),
    ('edge', Label('neighbor'), ['Y', 'Z'], [0.9, 1.0], ''),
    ('node', Label('susceptible'), ['Z'], [0.5, 1.0], '')
]

groundings = {}
groundings_edges = {}
dependency_graph_neighbors = {}
dependency_graph_reverse_neighbors = {}
```

#### Section 2a: Clause 1 - `infected(X)`

```python
clause_var_1 = 'X'

# 'X' not in nodes_set (X is a variable, not literal 'X')
# Normal grounding path
grounding = get_rule_node_clause_grounding('X', {}, predicate_map_node, Label('infected'), nodes)
# predicate_map_node[Label('infected')] = ['Alice']
grounding = ['Alice']

# Filter by satisfaction
qualified_groundings = ['Alice']  # infected(Alice) = [0.9, 1.0] satisfies

groundings['X'] = ['Alice']
```

**State after clause 1:**
```python
groundings = {'X': ['Alice']}
groundings_edges = {}
dependency_graph_neighbors = {}
```

#### Section 2b: Clause 2 - `neighbor(X,Y)`

```python
clause_var_1, clause_var_2 = 'X', 'Y'

# Get candidate edges
# X already grounded to [Alice], Y ungrounded
# → Find edges where source is Alice
grounding = [(Alice, Bob), (Alice, Carol)]

# Filter by satisfaction (all neighbor edges satisfy)
qualified_groundings = [(Alice, Bob), (Alice, Carol)]

# Lines 877-887: Extract unique nodes from edges
groundings['X'] = ['Alice']           # From e[0]
groundings['Y'] = ['Bob', 'Carol']    # From e[1]

# Line 890: Store edge groundings
groundings_edges[('X', 'Y')] = [(Alice, Bob), (Alice, Carol)]

# Lines 892-901: Build dependency graph
dependency_graph_neighbors['X'] = ['Y']           # X → Y
dependency_graph_reverse_neighbors['Y'] = ['X']   # Y ← X
```

**State after clause 2:**
```python
groundings = {'X': ['Alice'], 'Y': ['Bob', 'Carol']}
groundings_edges = {('X', 'Y'): [(Alice, Bob), (Alice, Carol)]}
dependency_graph_neighbors = {'X': ['Y']}
dependency_graph_reverse_neighbors = {'Y': ['X']}
```

#### Section 2c: Clause 3 - `neighbor(Y,Z)` (Implicit Narrowing)

```python
clause_var_1, clause_var_2 = 'Y', 'Z'

# Get candidate edges where source is in groundings['Y'] = [Bob, Carol]
# Bob's neighbors: [Dave] → edge (Bob, Dave)
# Carol's neighbors: [] → NO EDGES (Carol has no outgoing edges!)
grounding = [(Bob, Dave)]
qualified_groundings = [(Bob, Dave)]

# Lines 877-887: Extract unique nodes - THIS IS KEY!
groundings['Y'] = ['Bob']    # Overwritten! Was [Bob, Carol], now [Bob]
groundings['Z'] = ['Dave']

groundings_edges[('Y', 'Z')] = [(Bob, Dave)]

# Build dependency graph
dependency_graph_neighbors['Y'] = ['Z']           # Y → Z (added)
dependency_graph_reverse_neighbors['Z'] = ['Y']   # Z ← Y (added)
```

**Critical observation:** `groundings['Y']` was **implicitly narrowed** from `[Bob, Carol]` to `[Bob]` because Carol has no outgoing neighbor edges.

**State after clause 3 (before refinement):**
```python
groundings = {'X': ['Alice'], 'Y': ['Bob'], 'Z': ['Dave']}
groundings_edges = {
    ('X', 'Y'): [(Alice, Bob), (Alice, Carol)],  # Still has Carol edge!
    ('Y', 'Z'): [(Bob, Dave)]
}
dependency_graph_neighbors = {'X': ['Y'], 'Y': ['Z']}
dependency_graph_reverse_neighbors = {'Y': ['X'], 'Z': ['Y']}
```

**Problem:** `groundings_edges[('X', 'Y')]` still contains `(Alice, Carol)`, but `Carol` is no longer in `groundings['Y']`!

#### Section 3: Refinement - `refine_groundings(['Y', 'Z'], ...)`

This is where refinement fixes the inconsistency. See GROUND_RULE_ANALYSIS.md Section 3 for the full algorithm.

```python
# clause_variables = ['Y', 'Z'] - both just processed
variables_just_refined = ['Y', 'Z']

# Iteration 1: Process Y
# Y in dependency_graph_reverse_neighbors? YES → ['X']
# Propagate Y's narrowing back to edges involving X

old_edge_groundings = groundings_edges[('X', 'Y')]  # [(Alice,Bob), (Alice,Carol)]
new_node_groundings = groundings['Y']  # [Bob]

# Filter: Keep edges where e[1] (target) is in [Bob]
# (Alice, Bob): Bob in [Bob]? YES ✓
# (Alice, Carol): Carol in [Bob]? NO ✗

groundings_edges[('X', 'Y')] = [(Alice, Bob)]  # (Alice, Carol) REMOVED!

# Extract X groundings from filtered edges
groundings['X'] = ['Alice']  # Unchanged (Alice still valid)
```

**State after refinement:**
```python
groundings = {'X': ['Alice'], 'Y': ['Bob'], 'Z': ['Dave']}
groundings_edges = {
    ('X', 'Y'): [(Alice, Bob)],      # (Alice, Carol) removed by refinement!
    ('Y', 'Z'): [(Bob, Dave)]
}
```

**Consistency restored:** All edges have endpoints in their respective groundings.

#### Section 2d: Clause 4 - `susceptible(Z)`

```python
clause_var_1 = 'Z'

# Z already grounded to [Dave]
grounding = ['Dave']

# Check: susceptible(Dave) = [0.6, 0.8] ⊇ [0.5, 1.0]? YES
qualified_groundings = ['Dave']

groundings['Z'] = ['Dave']  # Unchanged
satisfaction = True
```

#### Section 4: Head Processing

```python
head_var_1 = 'Z'
groundings['Z'] = ['Dave']  # Already grounded from body

# Single head grounding: Dave
for head_grounding in ['Dave']:

    # Line 950: Satisfaction recheck
    satisfaction = check_all_clause_satisfaction(...)  →  True

    # Build provenance for each clause:
    # Clause 1 (infected(X)): X != Z, use all groundings['X']
    #   qualified_nodes[0] = ['Alice']
    # Clause 2 (neighbor(X,Y)): edge clause
    #   qualified_edges[1] = [(Alice, Bob)]
    # Clause 3 (neighbor(Y,Z)): Z == head_var, filter by Z=Dave
    #   qualified_edges[2] = [(Bob, Dave)]
    # Clause 4 (susceptible(Z)): Z == head_var
    #   qualified_nodes[3] = ['Dave']
```

#### Output

```python
applicable_rules_node.append((
    'Dave',                                      # head_grounding
    [[Interval(0.9,1.0)], [Interval(1.0,1.0)],  # annotations per clause
     [Interval(1.0,1.0)], [Interval(0.6,0.8)]],
    [['Alice'], [], [], ['Dave']],              # qualified_nodes
    [[], [(Alice,Bob)], [(Bob,Dave)], []],      # qualified_edges
    ([], [], Label(''))                          # edges_to_be_added
))
```

**Result:** 1 rule instance - update `at_risk(Dave)`

**Key takeaways from R2:**
- Dependency chain X → Y → Z constructed from edge clauses
- Carol eliminated because she has no path to Z
- Refinement propagated the narrowing back to clean up stale edge groundings

---

## Part 3: Rule R3 - Edge Rule with infer_edges=True

### `infected(X) ∧ neighbor(X,Y) → exposure(X,Y)` [infer_edges=True]

This rule creates **new edges** between infected nodes and their neighbors. It demonstrates temp_groundings isolation, Cartesian product construction, and the seven-way filtering logic.

#### Section 2: Clause Processing (Summary)

The first two clauses are processed identically to R2:

```python
# After clause 1: infected(X)
groundings = {'X': ['Alice']}

# After clause 2: neighbor(X,Y)
groundings = {'X': ['Alice'], 'Y': ['Bob', 'Carol']}
groundings_edges = {('X', 'Y'): [(Alice, Bob), (Alice, Carol)]}
dependency_graph_neighbors = {'X': ['Y']}
```

#### Section 4: Edge Rule Head Processing

```python
rule_type = 'edge'
head_var_1, head_var_2 = 'X', 'Y'

# Lines 1057-1058: Determine infer_edges mode
source, target, _ = rule_edges  # ('X', 'Y', Label('exposure'))
infer_edges = (source != '' and target != '')  →  True
```

#### Building valid_edge_groundings (Cartesian Product)

```python
head_var_1_groundings = groundings['X'] = ['Alice']
head_var_2_groundings = groundings['Y'] = ['Bob', 'Carol']

# Lines 1063-1070: Build Cartesian product (infer_edges=True)
valid_edge_groundings = []
for g1 in ['Alice']:
    for g2 in ['Bob', 'Carol']:
        # infer_edges=True → add ALL combinations
        valid_edge_groundings.append((g1, g2))

valid_edge_groundings = [(Alice, Bob), (Alice, Carol)]
# Note: These edges already exist, but infer_edges mode doesn't check
```

#### Loop Iteration 1: Processing (Alice, Bob)

**Step 1: Create temp copies (Lines 1082-1083)**

```python
temp_groundings = groundings.copy()
# {'X': ['Alice'], 'Y': ['Bob', 'Carol']}

temp_groundings_edges = groundings_edges.copy()
# {('X', 'Y'): [(Alice, Bob), (Alice, Carol)]}
```

**Why temp copies?** Each edge needs isolated validation. Without copies, filtering for (Alice, Bob) would corrupt data needed for (Alice, Carol). See GROUND_RULE_ANALYSIS.md "Why Temp Structures?" for detailed explanation.

**Step 2: Narrow to specific edge (Lines 1087-1088)**

```python
head_var_1_grounding, head_var_2_grounding = 'Alice', 'Bob'

temp_groundings['X'] = ['Alice']  # Already single
temp_groundings['Y'] = ['Bob']    # Narrowed from [Bob, Carol]
```

**Step 3: Seven-way filtering of temp_groundings_edges (Lines 1089-1101)**

```python
for c1, c2 in temp_groundings_edges.keys():  # ('X', 'Y')
    # Check: c1 == head_var_1 AND c2 == head_var_2?
    # 'X' == 'X' AND 'Y' == 'Y'? YES → Branch 1

    temp_groundings_edges[('X', 'Y')] = [
        e for e in [(Alice,Bob), (Alice,Carol)]
        if e == (Alice, Bob)  # Exact match required
    ]
    # Result: [(Alice, Bob)]
```

**Step 4: Refinement & Satisfaction Check (Lines 1103-1110)**

```python
refine_groundings(['X', 'Y'], temp_groundings, temp_groundings_edges, ...)
satisfaction = check_all_clause_satisfaction(...)  →  True
```

**Step 5: Self-loop prevention (Lines 1112-1117)**

```python
if infer_edges:
    # source='X', target='Y' → different variables
    if source != target and head_var_1_grounding == head_var_2_grounding:
        continue  # Skip self-loops
    # 'Alice' == 'Bob'? NO → Not a self-loop, continue

    edges_to_be_added[0].append('Alice')  # sources
    edges_to_be_added[1].append('Bob')    # targets
```

**Step 6: Build provenance (Lines 1119-1207)**

Uses temp_groundings (narrowed to this specific edge) for provenance collection.

#### Loop Iteration 2: Processing (Alice, Carol)

Same process with `head_var_2_grounding = 'Carol'`:
- temp_groundings['Y'] = ['Carol']
- temp_groundings_edges[('X', 'Y')] = [(Alice, Carol)]
- edges_to_be_added accumulates: sources=['Alice','Alice'], targets=['Bob','Carol']

#### Output

```python
# Two rule instances created
applicable_rules_edge.append((
    ('Alice', 'Bob'),                    # edge
    [[Interval(0.9,1.0)], [Interval(1.0,1.0)]],  # annotations
    [['Alice'], []],                     # qualified_nodes
    [[], [(Alice, Bob)]],                # qualified_edges
    (['Alice'], ['Bob'], Label('exposure'))  # edges_to_be_added
))

applicable_rules_edge.append((
    ('Alice', 'Carol'),
    [[Interval(0.9,1.0)], [Interval(1.0,1.0)]],
    [['Alice'], []],
    [[], [(Alice, Carol)]],
    (['Alice'], ['Carol'], Label('exposure'))
))
```

**Result:** 2 rule instances - create/update `exposure(Alice,Bob)` and `exposure(Alice,Carol)`

---

## Part 4: Rule R4 - Edge Rule with infer_edges=False

### `neighbor(X,Y) ∧ infected(X) → alert(X,Y)` [infer_edges=False]

This rule updates **existing edges** only. It contrasts with R3 by filtering based on actual graph topology.

#### Section 2: Clause Processing

```python
# Clause 1: neighbor(X,Y)
# Get ALL neighbor edges in graph
grounding = [(Alice, Bob), (Alice, Carol), (Bob, Dave)]
qualified_groundings = [(Alice, Bob), (Alice, Carol), (Bob, Dave)]

groundings['X'] = ['Alice', 'Bob']
groundings['Y'] = ['Bob', 'Carol', 'Dave']
groundings_edges[('X', 'Y')] = [(Alice,Bob), (Alice,Carol), (Bob,Dave)]

# Clause 2: infected(X)
# Filter X to only infected nodes
grounding = groundings['X'] = ['Alice', 'Bob']
# Check infected predicate:
#   Alice: infected = [0.9, 1.0] ✓
#   Bob: infected = ? (not in world) ✗
qualified_groundings = ['Alice']
groundings['X'] = ['Alice']

# Lines 844-848: Filter edge groundings (node clause after edge clause)
qualified_groundings_set = {'Alice'}
for c1, c2 in groundings_edges:
    if c1 == 'X':  # Source variable matches
        groundings_edges[('X','Y')] = [
            e for e in groundings_edges[('X','Y')]
            if e[0] in {'Alice'}
        ]
# (Alice,Bob) ✓, (Alice,Carol) ✓, (Bob,Dave) ✗
groundings_edges[('X', 'Y')] = [(Alice, Bob), (Alice, Carol)]
```

**State after clause processing:**
```python
groundings = {'X': ['Alice'], 'Y': ['Bob', 'Carol', 'Dave']}
groundings_edges = {('X', 'Y'): [(Alice, Bob), (Alice, Carol)]}
```

#### Section 4: Edge Rule Head Processing (infer_edges=False)

```python
head_var_1, head_var_2 = 'X', 'Y'

# Lines 1057-1058: Determine infer_edges mode
source, target, _ = rule_edges  # ('', '', Label(''))
infer_edges = (source != '' and target != '')  →  False
```

#### Building valid_edge_groundings (Existing Edges Only)

```python
head_var_1_groundings = ['Alice']
head_var_2_groundings = ['Bob', 'Carol', 'Dave']

# Lines 1063-1070: Filter by edges_set (infer_edges=False)
valid_edge_groundings = []
for g1 in ['Alice']:
    for g2 in ['Bob', 'Carol', 'Dave']:
        # infer_edges=False → check if edge exists
        if (g1, g2) in edges_set:
            valid_edge_groundings.append((g1, g2))

# (Alice, Bob) in edges_set? YES ✓
# (Alice, Carol) in edges_set? YES ✓
# (Alice, Dave) in edges_set? NO ✗

valid_edge_groundings = [(Alice, Bob), (Alice, Carol)]
```

**Contrast with R3:**
- R3 (infer_edges=True): Would include (Alice, Dave) if Dave were in Y groundings
- R4 (infer_edges=False): Only edges that exist in the graph

#### Loop Processing

Same temp_groundings pattern as R3, but with fewer iterations since only existing edges qualify.

Each iteration:
1. Create temp copies
2. Narrow temp_groundings to specific edge
3. Apply seven-way filtering
4. Refine and check satisfaction
5. Build provenance

#### Output

```python
applicable_rules_edge.append((
    ('Alice', 'Bob'),
    [[Interval(1.0,1.0)], [Interval(0.9,1.0)]],  # neighbor, infected
    [[], ['Alice']],                              # qualified_nodes
    [[(Alice, Bob)], []],                         # qualified_edges
    ([], [], Label(''))                           # No edges to add
))

applicable_rules_edge.append((
    ('Alice', 'Carol'),
    [[Interval(1.0,1.0)], [Interval(0.9,1.0)]],
    [[], ['Alice']],
    [[(Alice, Carol)], []],
    ([], [], Label(''))
))
```

**Result:** 2 rule instances - update `alert(Alice,Bob)` and `alert(Alice,Carol)`

**Key difference from R3:** `edges_to_be_added` is empty because we're updating existing edges, not creating new ones.

---

## Final Output Summary

### applicable_rules_node

| Rule | head_grounding | Description |
|------|----------------|-------------|
| R1 | `'Alice'` | patient_zero(Alice) |
| R2 | `'Dave'` | at_risk(Dave) |

**Total node rule instances:** 2

### applicable_rules_edge

| Rule | edge | edges_to_be_added | Description |
|------|------|-------------------|-------------|
| R3 | `('Alice', 'Bob')` | `(['Alice'], ['Bob'], 'exposure')` | Create exposure edge |
| R3 | `('Alice', 'Carol')` | `(['Alice'], ['Carol'], 'exposure')` | Create exposure edge |
| R4 | `('Alice', 'Bob')` | `([], [], '')` | Update existing with alert |
| R4 | `('Alice', 'Carol')` | `([], [], '')` | Update existing with alert |

**Total edge rule instances:** 4

---

## Branch Coverage Matrix

| Branch | R1 | R2 | R3 | R4 | Lines |
|--------|:--:|:--:|:--:|:--:|-------|
| Ground atom in body | ✓ | | | | 835-836 |
| Ground atom in head | ✓ | | | | 936-937 |
| Node clause (first) | ✓ | ✓ | ✓ | | 830-854 |
| Node clause (narrows existing) | | | | ✓ | 844-848 |
| Edge clause processing | | ✓ | ✓ | ✓ | 856-901 |
| Dependency graph construction | | ✓ | ✓ | ✓ | 892-901 |
| Multi-hop dependency (X→Y→Z) | | ✓ | | | 892-901 |
| refine_groundings() | | ✓ | ✓ | ✓ | 907-909 |
| Refinement propagation (reverse) | | ✓ | | | 1277-1297 |
| Node rule head processing | ✓ | ✓ | | | 924-1017 |
| Edge rule head processing | | | ✓ | ✓ | 1019-1221 |
| infer_edges=True (Cartesian) | | | ✓ | | 1066-1067 |
| infer_edges=False (existing) | | | | ✓ | 1068-1070 |
| temp_groundings isolation | | | ✓ | ✓ | 1082-1083 |
| Seven-way edge filtering | | | ✓ | ✓ | 1089-1101 |
| Self-loop prevention | | | ✓ | | 1112-1117 |
| edges_to_be_added accumulation | | | ✓ | | 1116-1117 |
| Multiple head groundings | | | ✓ | ✓ | 1073 loop |

---

## Key Takeaways

1. **Ground atoms** (R1): When `allow_ground_rules=True`, literal node/edge names in clauses are used directly instead of being treated as variables.

2. **Dependency graph** (R2): Edge clauses create dependencies between variables. When `neighbor(X,Y)` is processed, X→Y is added to the dependency graph.

3. **Implicit narrowing** (R2): Edge clause extraction can narrow a variable if some bindings have no valid edges. Carol was removed from Y because she has no outgoing neighbors.

4. **Refinement propagation** (R2): `refine_groundings()` propagates variable narrowing through the dependency graph, cleaning up stale edge groundings.

5. **temp_groundings isolation** (R3, R4): Edge rules create temp copies for each edge iteration to prevent corruption across iterations.

6. **infer_edges modes** (R3 vs R4):
   - `True`: Cartesian product of head groundings (creates new edges)
   - `False`: Only edges existing in graph (updates existing edges)

7. **Output structure**: Each rule instance is a complete, self-contained package ready for `_update_node()` or `_update_edge()` to apply.
