# Interpretation.py Section-by-Section Analysis

**Companion to:** [INTERPRETATION_ANALYSIS.md](INTERPRETATION_ANALYSIS.md)
**Source File:** `pyreason/scripts/interpretation/interpretation.py`

---

## Overview

This document contains the **detailed function-by-function analysis** of `interpretation.py`. For each layer defined in the analysis plan, this file documents:

- **Theoretical concepts** underlying each function
- **Implementation details** with parameter tables and type definitions
- **Bugs logged** during analysis (cross-referenced to BUG_LOG.md)
- **Key insights** discovered during the deep dive

The parent document ([INTERPRETATION_ANALYSIS.md](INTERPRETATION_ANALYSIS.md)) contains:
- High-level architecture and data flow
- The 12-layer analysis plan with line numbers and function inventories
- Cross-cutting concerns (performance, error handling, Numba strategy)
- Summary statistics and rewrite priorities

---

## Section-by-Section Analysis

### Layer 0/1: Initialization (Lines 54-225)
**Status:** ✅ Complete

---

#### 1.1: Interpretation Class Overview

**Purpose:** The `Interpretation` class is the core reasoning engine of PyReason. It encapsulates the complete state of a knowledge graph reasoning session.

**Theoretical Role:**
- **Temporal Logic**: Manages truth values across multiple timesteps
- **Annotated Logic**: Truth values are intervals [lower, upper], not binary
- **Dynamic Graphs**: Graph topology can change during reasoning
- **Provenance**: Maintains complete audit trail of all inferences

**Architecture:**
```
Input (graph, facts, rules) → Interpretation → Fixed-Point Iteration → Output (truth assignments, traces)
```

---

#### 1.2: Constructor Parameters (12 total)

The `__init__` method (lines 58-114) accepts 12 configuration parameters:

1. **`graph`** (NetworkX Graph): Knowledge graph structure (nodes, edges, attributes)
   - Defines domain entities and relationships that rules operate over
   - Extracted to: `self.nodes`, `self.edges`, `self.neighbors`

2. **`ipl`** (List[Tuple[Label, Label]]): Inconsistent Predicate List
   - Predicate pairs that cannot both be true (e.g., infected/healthy)
   - Enforces Inverse Predicate Law: if P=[l,u], then ¬P=[1-u, 1-l]

3. **`annotation_functions`** (Tuple[Function]): Registry of interval aggregation functions
   - Compute rule head intervals from body clause intervals
   - Examples: max, min, average, weighted_average, custom

4. **`head_functions`** (Tuple[Function]): Registry of entity computation functions
   - Compute rule head variables (entities) from body variable bindings
   - Enables derived predicates (e.g., cluster(hash(X,Y)))

5. **`reverse_graph`** (bool): Enable reverse graph traversal
   - If True, populates `reverse_neighbors` (predecessor lookups)

6. **`atom_trace`** (bool): Record detailed provenance
   - If True, records which ground atoms (variable bindings) satisfied each rule
   - Tradeoff: Complete explainability vs. memory/performance overhead

7. **`save_graph_attributes_to_rule_trace`** (bool): Include graph attributes in traces
   - If True, initial graph labels recorded in provenance
   - Distinguishes inferred facts (rules) from asserted facts (graph)

8. **`persistent`** (bool): Truth value persistence across timesteps
   - True: Monotonic reasoning (facts persist, classical logic programming)
   - False: Non-monotonic reasoning (facts reset each timestep, temporal logic)

9. **`inconsistency_check`** (bool): Detect and resolve conflicting facts
   - True: Calls `resolve_inconsistency_node/edge()` on conflicts
   - False: Uses override semantics (later facts override earlier)

10. **`store_interpretation_changes`** (bool): Record all changes to traces
    - If False, skips trace updates (performance optimization)
    - Tradeoff: Speed vs. provenance

11. **`update_mode`** (str: 'override' | 'intersection'): Interval combination strategy
    - 'override': New interval replaces old (non-monotonic)
    - 'intersection': New interval intersects with old (monotonic refinement)

12. **`allow_ground_rules`** (bool): Permit rules with no variables
    - If True, allows ground facts in rule form (e.g., `infected(Alice) <- vaccinated(Bob)`)

---

#### 1.3: Instance Variables (16+ total)

**Graph Structure (4 variables):**
- `self.nodes` (List[str]): All node identifiers
- `self.edges` (List[Tuple[str,str]]): All edge tuples
- `self.neighbors` (Dict[str, List[str]]): Forward adjacency (node → successors)
- `self.reverse_neighbors` (Dict[str, List[str]]): Reverse adjacency (node → predecessors)

**Interpretation State (2 variables):**
- `self.interpretations_node` (Dict[str, World]): Node → World (predicate → interval)
- `self.interpretations_edge` (Dict[Tuple, World]): Edge → World

**Predicate Reverse Index (2 variables):**
- `self.predicate_map_node` (Dict[Label, List[str]]): Predicate → nodes with that predicate
- `self.predicate_map_edge` (Dict[Label, List[Tuple]]): Predicate → edges with that predicate
- **Purpose**: O(1) lookup optimization vs O(n) scan

**Scheduled Actions (6 variables):**
- `self.rules_to_be_applied_node` (List[Tuple]): Node rules scheduled for future timesteps
- `self.rules_to_be_applied_edge` (List[Tuple]): Edge rules scheduled for future timesteps
- `self.facts_to_be_applied_node` (List[Tuple]): Node facts scheduled for future timesteps
- `self.facts_to_be_applied_edge` (List[Tuple]): Edge facts scheduled for future timesteps
- `self.edges_to_be_added_node_rule` (List[Tuple]): Edges to create from node rules
- `self.edges_to_be_added_edge_rule` (List[Tuple]): Edges to create from edge rules
- **Purpose**: Implement temporal rules (delta_t)

**Provenance Traces (6 variables):**
- `self.rule_trace_node` (List[Tuple]): Every interval change for nodes
- `self.rule_trace_edge` (List[Tuple]): Every interval change for edges
- `self.rule_trace_node_atoms` (List[Tuple]): Ground atoms for node rules (if atom_trace)
- `self.rule_trace_edge_atoms` (List[Tuple]): Ground atoms for edge rules (if atom_trace)
- `self.rules_to_be_applied_node_trace` (List[Tuple]): Provenance for scheduled node rules
- `self.rules_to_be_applied_edge_trace` (List[Tuple]): Provenance for scheduled edge rules

**Reasoning Metadata (3 variables):**
- `self.num_ga` (List[int]): Ground atoms count per timestep (performance tracking)
- `self.time` (int): Current timestep (for resuming)
- `self.prev_reasoning_data` (List[int]): [previous_timestep, fp_counter] (for resuming)

**Class Variables (2, shared across all instances):**
- `specific_node_labels` (Dict[Label, List[str]]): Global node label cache
- `specific_edge_labels` (Dict[Label, List[edge]]): Global edge label cache

---

#### 1.4: Initialization Functions

**Theoretical Concepts:**
- **Knowledge Graph Representation**: Dual node/edge structure with World states
- **Interpretation State**: Maps components to predicate→interval truth values
- **Predicate Map**: Reverse index from predicate to components (optimization for rule grounding)
- **Neighbor Structures**: Forward (successors) and reverse (predecessors) for graph traversal
- **Inverse Predicate Law (IPL)**: Mutually exclusive predicate pairs with complement bounds
- **Convergence Modes**: Perfect (no changes), Delta interpretation (change count), Delta bound (epsilon threshold)
- **Fact Expansion**: Temporal facts [t_lower, t_upper] expanded to individual timestep applications
- **Provenance Tracking**: Rule trace (what modified components) + Atom trace (which ground atoms satisfied rules)

**Implementation Details:**
- `__init__` (lines 58-114): Stores 12 config parameters, initializes 16+ numba typed collections
- `_init_reverse_neighbors` (lines 118-130): Inverts neighbor dict, ensures all nodes present
- `_init_interpretations_node/edge` (lines 134-168): Creates empty Worlds, processes specific_labels with [0,1] bounds
- `_init_convergence` (lines 172-182): Parses -1 sentinels into mode + delta
- `_init_facts` (lines 192-210): Expands temporal facts, detects graph-attributes via string matching
- `start_fp` → `_start_fp` (lines 184-224): Entry point, passes 38 arguments to reason()

**Bugs Logged:**
- BUG-097 (HIGH): O(n) duplicate check in reverse neighbor construction - O(E×D) complexity
- BUG-098 (LOW): Logic error in reverse neighbor else branch can overwrite existing entries
- BUG-099 (MEDIUM): 38-parameter function call - unmaintainable parameter list anti-pattern
- BUG-100 (MEDIUM): String-based graph attribute detection - fragile magic string 'graph-attribute-fact'
- BUG-101 (LOW): Specific labels initialized to [0,1] (uncertain) instead of [1,1] (certain) - semantic ambiguity

**Key Insights:**
- **Numba constraints drive design**: Static methods + explicit parameters required for JIT compilation
- **Performance-critical initialization**: Reverse neighbor construction has quadratic complexity bug (BUG-097)
- **Dual data structures**: Interpretations (forward lookup) + predicate_map (reverse lookup) enable efficient queries
- **Provenance is first-class**: Complete audit trail maintained from initialization
- **Specific labels semantic ambiguity**: Unclear if graph labels mean "possible predicate" vs "initial truth"
- **Convergence is configurable**: Three distinct modes support different reasoning requirements

---

### Layer 1: Utility Functions (Lines 1965-1998)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Numba String Manipulation Limitations**: Numba's JIT compiler has limited support for Python's native string operations
- **Manual String↔Number Conversion**: Custom implementations to work within Numba's constraints
- **ASCII Arithmetic**: `ord(v) - 48` converts characters '0'-'9' to integers 0-9
- **Fixed-Point Decimal Arithmetic**: Using integer operations + power-of-10 scaling

**Implementation Details:**
1. **`float_to_str(value)`** (1965-1970): Converts float to string with 3 decimal places
   - Extracts integer part via truncation: `int(value)`
   - Extracts fractional part: `int(value % 1 * 1000)`
   - Concatenates with f-string formatting

2. **`str_to_float(value)`** (1973-1983): Parses string to float
   - Finds decimal point position
   - Counts digits after decimal
   - Removes decimal point, parses as integer
   - Divides by 10^(decimal_places) to restore floating point

3. **`str_to_int(value)`** (1986-1997): Parses string to integer using manual ASCII arithmetic
   - Detects negative sign, removes if present
   - For each character: converts ASCII to digit (`ord(v) - 48`)
   - Applies positional notation: `digit × 10^position`
   - Negates result if negative flag set

**Bugs Logged:**
- BUG-102 (CRITICAL): Negative float conversion produces incorrect output due to Python modulo behavior
- BUG-103 (CRITICAL): Zero-padding missing causes loss of significant digits
- BUG-104 (MEDIUM): No input validation in str_to_float
- BUG-105 (MEDIUM): Non-numeric characters not validated in str_to_int
- BUG-106 (MEDIUM): Multiple minus signs incorrectly handled
- BUG-107 (MEDIUM): Precision loss without rounding (truncation instead of rounding)
- BUG-108 (LOW): Floating-point arithmetic precision errors (IEEE 754 limitations)
- BUG-109 (LOW): Multiple decimal points not detected

**Key Insights:**
- These utility functions exist to work around Numba's string manipulation limitations
- Bug density is extremely high (23.5% - 8 bugs in 34 lines)
- Two CRITICAL bugs make these functions mathematically incorrect for common cases
- Functions likely not heavily used (otherwise bugs would have been discovered)
- Usage analysis needed to determine real-world impact
- Modern Numba versions may support native Python string operations, making these obsolete

---

### Layer 2: Threshold & Trace Functions (Lines 1414-1443, 1657-1659)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Threshold Logic**: Counting quantifiers that specify rule activation when sufficient entities satisfy a condition (e.g., "≥3 neighbors" or "≥60% of neighbors")
- **Provenance Tracking**: Recording the complete history of interpretation changes for explainability and debugging

**Implementation Details:**

**`_satisfies_threshold(num_neigh, num_qualified_component, threshold)`** (1414-1443)
Evaluates whether a threshold condition is satisfied during rule grounding.

| Parameter | Type | Definition |
|-----------|------|------------|
| `num_neigh` | `int` | Denominator for percentage calculations. If `threshold[1][1]=='total'`: count of all entities in grounding. If `'available'`: count of entities with predicate defined. |
| `num_qualified_component` | `int` | Count of entities whose interval satisfies the clause's required bounds. Computed by `get_qualified_node/edge_groundings()`. |
| `threshold` | `Tuple` | 3-tuple: `(quantifier, (count_mode, scope_mode), value)` where: |
| | | • `threshold[0]`: quantifier (`'greater_equal'`, `'greater'`, `'less_equal'`, `'less'`, `'equal'`) |
| | | • `threshold[1][0]`: count_mode (`'number'` or `'percent'`) |
| | | • `threshold[1][1]`: scope_mode (`'total'` or `'available'`) |
| | | • `threshold[2]`: numeric value (absolute count or percentage) |

**`_update_rule_trace(rule_trace, qn, qe, prev_bnd, name)`** (1657-1659)
Appends a provenance entry recording an interpretation change.

| Parameter | Type | Definition |
|-----------|------|------------|
| `rule_trace` | `numba.typed.List` | Accumulator list of all interpretation changes. Modified in-place. |
| `qn` | `List[List[str]]` | Qualified nodes - nested list where each inner list contains nodes satisfying a body clause. |
| `qe` | `List[List[Tuple]]` | Qualified edges - nested list where each inner list contains `(source, target)` tuples satisfying a body clause. |
| `prev_bnd` | `Interval` | The interval **before** this update. `.copy()` called to prevent aliasing. |
| `name` | `str` | Rule/fact identifier that caused the change (e.g., `"infection_rule"`). |

**Bugs Logged:**
- BUG-110 (MEDIUM): `_satisfies_threshold` missing `@numba.njit` decorator
- BUG-111 (MEDIUM): `result` variable not initialized - UnboundLocalError if no branch taken
- BUG-112 (MEDIUM): Floating-point equality (`==`) without epsilon tolerance
- BUG-113 (LOW): Redundant ternary expressions (`True if x else False`)
- BUG-114 (LOW): `_update_rule_trace` JIT overhead may exceed benefit for trivial function
- BUG-115 (MEDIUM): `prev_bnd.copy()` assumes Numba-compatible `.copy()` method

**Key Insights:**
- Threshold evaluation is O(1) but missing JIT decorator causes mode-switching overhead
- Trace accumulation can cause OOM for long reasoning sessions (unbounded growth)
- Both functions duplicated identically across 3 interpretation files

---

## Layer 2: Threshold & Trace Functions (Detailed)

### `_satisfies_threshold` - Threshold Evaluation

#### Direct Call Sites (2 locations)
Both calls occur in Layer 7A (Grounding Helper Functions):

1. **Line 1315**: `check_node_grounding_threshold_satisfaction()`
   - **Purpose**: Validate that enough nodes satisfy a clause's threshold condition
   - **Context**: During rule grounding, after finding all nodes matching a clause predicate
   - **Parameters passed**:
     - `neigh_len`: Total nodes (if `'total'`) or available nodes with predicate (if `'available'`)
     - `qualified_neigh_len`: Count of nodes with intervals satisfying the clause bounds
     - `threshold`: Rule-defined threshold structure

2. **Line 1330**: `check_edge_grounding_threshold_satisfaction()`
   - **Purpose**: Validate that enough edges satisfy a clause's threshold condition
   - **Context**: During rule grounding, after finding all edges matching a clause predicate
   - **Parameters passed**: Same structure as node version, but for edges

#### Indirect Usage (Rule Grounding Pipeline)
```
reason() [Layer 9]
  ↓
_ground_rule() [Layer 8]
  ↓
check_node/edge_grounding_threshold_satisfaction() [Layer 7A]
  ↓
_satisfies_threshold() [Layer 2] ← YOU ARE HERE
```

**Call Frequency**: 
- Once per rule per clause with threshold per timestep
- Worst case: `O(T × R × C)` where T=timesteps, R=rules, C=clauses with thresholds

#### Example Use Case (from rule syntax)
See Glossary for example


### Function 2: `_update_rule_trace` - Provenance Recording


**Trace Entry Structure**:
```python
(
    qualified_nodes,      # List[List[node]] - which nodes satisfied rule body
    qualified_edges,      # List[List[edge]] - which edges satisfied rule body  
    previous_bound.copy(), # Interval - old value before update
    name                  # str - rule/fact name that caused change
)
```

**Downstream Consumers**:
1. **Interpretation.get_dict()** - Exports traces to dictionary format for user analysis
2. **Debugging/visualization tools** - Explain why a fact has a particular value
3. **Learning systems** - Analyze which rules fire frequently
4. **Audit trails** - Regulatory compliance, explainability requirements

---

### Layer 3: Satisfaction Checking (Lines 1662-1772)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Interval Containment**: A world bound `[w_l, w_u]` satisfies a required interval `[r_l, r_u]` iff `r_l ≤ w_l` AND `r_u ≥ w_u` (world is at least as specific as required)
- **Annotation Functions**: User-defined functions that compute rule head intervals from body clause intervals (e.g., `max`, `min`, `average`)
- **Comparison Clauses**: Special clauses with numeric suffix labels (e.g., `age_25`) for arithmetic comparisons

**Implementation Details:**

**`are_satisfied_node(interpretations, comp, nas)`** (1662-1666) - ⚠️ DEAD CODE

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations mapping node → World |
| `comp` | `str` | Node identifier to check |
| `nas` | `List[Tuple[Label, Interval]]` | List of (label, required_bound) pairs to check |

**Returns:** `bool` - True if ALL annotations are satisfied

---

**`is_satisfied_node(interpretations, comp, na)`** (1670-1681)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations |
| `comp` | `str` | Node identifier |
| `na` | `Tuple[Label, Interval]` | Single (label, required_bound) pair. `na[0]` = label, `na[1]` = interval |

**Returns:** `bool` - True if world's bound for label is contained within required interval

**Logic:**
1. If label or bound is None → return True (wildcard)
2. Get world for component
3. Call `world.is_satisfied(label, interval)` → checks `world_bound in required_interval`

---

**`is_satisfied_node_comparison(interpretations, comp, na)`** (1685-1708) - ⚠️ DEAD CODE

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations |
| `comp` | `str` | Node identifier |
| `na` | `Tuple[Label, Interval]` | (label_prefix, required_bound) - label has numeric suffix |

**Returns:** `Tuple[bool, float]` - (satisfied, extracted_number)

**Purpose:** Enables rules like `age(X) > 21` by finding `age_25` in world and extracting `25`.

---

**`are_satisfied_edge(interpretations, comp, nas)`** (1712-1716) - ⚠️ DEAD CODE
Same as `are_satisfied_node` but for edges. `comp` is `Tuple[str, str]`.

---

**`is_satisfied_edge(interpretations, comp, na)`** (1720-1731)
Same as `is_satisfied_node` but for edges. `comp` is `Tuple[str, str]`.

---

**`is_satisfied_edge_comparison(interpretations, comp, na)`** (1735-1758) - ⚠️ DEAD CODE
Same as `is_satisfied_node_comparison` but for edges.

---

**`annotate(annotation_functions, rule, annotations, weights)`** (1762-1771)

| Parameter | Type | Definition |
|-----------|------|------------|
| `annotation_functions` | `Tuple[Function]` | Registry of user-defined annotation functions |
| `rule` | `Rule` | Rule object being evaluated |
| `annotations` | `List[Interval]` | Body clause intervals to aggregate |
| `weights` | `List[float]` | Weights for weighted aggregation |

**Returns:** `Tuple[float, float]` - (lower, upper) bounds for rule head

**Logic:**
1. Get function name from rule (`rule.get_annotation_function()`)
2. If empty → return rule's static bound
3. Otherwise, find matching function in registry and call it

---

**Bugs Logged:**
- BUG-116 (MEDIUM): No short-circuit evaluation in `are_satisfied_node/edge`
- BUG-117 (LOW): Silent exception swallowing hides real errors
- BUG-118 (HIGH): Comparison functions use broken `str_to_float` (inherits BUG-102, BUG-103)
- BUG-119 (MEDIUM): Comparison functions may be dead code
- BUG-120 (HIGH): `annotate()` returns undefined variable if no function matches
- BUG-121 (LOW): `annotate()` loop doesn't break after finding match
- BUG-122 (MEDIUM): `are_satisfied_*` and `*_comparison` functions never called - dead code

**Key Insights:**
- 58 lines (53%) are dead code - functions defined but never called
- Only `is_satisfied_node`, `is_satisfied_edge`, and `annotate` are actually used
- Comparison functions inherit critical bugs from `str_to_float`
- `annotate()` can crash if annotation function name not found in registry

---

#### Call Sites & Integration

**`is_satisfied_node` Call Sites (1 location):**
- Line 1396: `get_qualified_node_groundings()` [Layer 7A]
  - Filters node groundings to only those satisfying clause bounds
  - Called during rule grounding to find qualified components

**`is_satisfied_edge` Call Sites (1 location):**
- Line 1407: `get_qualified_edge_groundings()` [Layer 7A]
  - Filters edge groundings to only those satisfying clause bounds

**`annotate` Call Sites (2 locations):**
- Line 568: `reason()` [Layer 9] - Node rule application
- Line 587: `reason()` [Layer 9] - Edge rule application
  - Computes rule head interval from body clause intervals
  - Called after rule grounding succeeds, before applying update

**Integration Pipeline:**
```
reason() [Layer 9]
  ↓
_ground_rule() [Layer 8] - Find variable bindings
  ↓
get_qualified_node/edge_groundings() [Layer 7A]
  ↓
is_satisfied_node/edge() [Layer 3] ← Filters by bounds
  ↓
annotate() [Layer 3] ← Computes head interval
  ↓
_update_node/edge() [Layer 5] - Apply changes
```

**Satisfaction Semantics (from World.is_satisfied):**
```python
def is_satisfied(self, label, interval):
    bnd = self._world[label]      # Get current world bound
    return bnd in interval        # Check containment

# Interval.__contains__ semantics:
# interval contains bnd iff:
#   interval.lower <= bnd.lower AND interval.upper >= bnd.upper
```

**Example:**
```
World: infected(Alice) = [0.8, 0.9]  (80-90% certain infected)
Clause requires: infected(Alice):[0.7, 1.0]  (at least 70% certain)
Check: 0.7 <= 0.8 AND 1.0 >= 0.9 → True (satisfied)
```

---

#### Code Variants

All Layer 3 functions exist identically in **3 interpretation implementations**:
1. `interpretation.py` (lines 1662-1772)
2. `interpretation_fp.py` (lines 1774-1884)
3. `interpretation_parallel.py` (lines 1662-1772)

**Dead code total across all variants:** 174 lines (58 × 3 files)

---

### Layer 4: Consistency Checking (Lines 1775-1798)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Interval Consistency (Overlap)**: Two intervals are consistent iff they can both be true simultaneously—i.e., they share at least one point (overlap)
- **Conflict Detection**: Before applying a new bound, check if it contradicts existing knowledge
- **Monotonic vs Non-Monotonic**: Consistency enables monotonic refinement; inconsistency triggers resolution

**Distinction from Satisfaction:**
| Concept | Question | Check | Use Case |
|---------|----------|-------|----------|
| **Satisfaction** | "Does the world meet the rule's requirements?" | Containment: `required ⊆ world` | Rule triggering |
| **Consistency** | "Can new info coexist with existing info?" | Overlap: `world ∩ new ≠ ∅` | Update validation |

**Implementation Details:**

**`check_consistent_node(interpretations, comp, na)`** (1775-1785)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations mapping node → World |
| `comp` | `str` | Node identifier to check |
| `na` | `Tuple[Label, Interval]` | (label, proposed_bound) - the new annotation to check |

**Returns:** `bool` - True if proposed bound overlaps with existing bound (consistent)

**Logic:**
1. Get world for component
2. If label exists in world → get existing bound; else → assume `[0, 1]` (unknown)
3. Check overlap: `NOT (proposed.lower > existing.upper OR existing.lower > proposed.upper)`

---

**`check_consistent_edge(interpretations, comp, na)`** (1788-1798)
Same as `check_consistent_node` but for edges. `comp` is `Tuple[str, str]`.

---

**Bugs Logged:**
- BUG-123 (LOW): 100% code duplication between node and edge versions
- BUG-124 (LOW): Redundant conditional pattern (`if ... return False else return True`)

**Key Insights:**
- **Lowest bug density**: Simple, mathematically correct logic
- **Clear semantics**: Overlap check is straightforward interval arithmetic
- **Used in update pipeline**: Called from `_update_node/edge()` when `inconsistency_check=True`
- **Enables monotonic refinement**: Only accepts updates that don't contradict existing knowledge

---

#### Call Sites & Integration

**`check_consistent_node` Call Sites (2 locations):**
- Line 1476: `_update_node()` [Layer 5] - Before applying rule update
- Line 1509: `_update_node()` [Layer 5] - Before applying fact update

**`check_consistent_edge` Call Sites (2 locations):**
- Line 1582: `_update_edge()` [Layer 5] - Before applying rule update
- Line 1615: `_update_edge()` [Layer 5] - Before applying fact update

**Integration Pipeline:**
```
reason() [Layer 9]
  ↓
_update_node/edge() [Layer 5]
  ↓
check_consistent_node/edge() [Layer 4] ← Validates update won't cause contradiction
  ↓
If inconsistent → resolve_inconsistency_node/edge() [Layer 5]
If consistent → Apply update
```

**Consistency Example:**
```
Existing: infected(Alice) = [0.3, 0.7]  (30-70% certain)
Proposed: infected(Alice) = [0.6, 0.9]  (60-90% certain)

Check overlap:
  proposed.lower (0.6) <= existing.upper (0.7)? YES
  existing.lower (0.3) <= proposed.upper (0.9)? YES
→ CONSISTENT (overlap at [0.6, 0.7])

After monotonic refinement: infected(Alice) = [0.6, 0.7]
  (intersection narrows uncertainty)
```

**Inconsistency Example:**
```
Existing: infected(Alice) = [0.8, 0.9]  (80-90% certain infected)
Proposed: infected(Alice) = [0.1, 0.2]  (10-20% certain infected)

Check overlap:
  proposed.lower (0.1) <= existing.upper (0.9)? YES
  existing.lower (0.8) <= proposed.upper (0.2)? NO
→ INCONSISTENT (no overlap - contradictory information)

→ Triggers resolve_inconsistency_node() [Layer 5]
```

---

#### How Consistency Relates to Monotonic Reasoning

**Three-layer architecture for safe interval refinement:**

1. **Layer 3 (Satisfaction)**: Gates rule activation
   - "Is the world specific enough to trigger this rule?"
   - Prevents premature conclusions from uncertain data

2. **Layer 4 (Consistency)**: Gates update acceptance
   - "Is this new bound compatible with what we know?"
   - Prevents contradictory updates from corrupting state

3. **Layer 5 (Update)**: Applies the refinement
   - If update_mode='intersection': narrow interval (monotonic)
   - If update_mode='override': replace interval (non-monotonic)

**Monotonic Progress Emerges From:**
- Satisfaction ensuring rules only fire when premises are sufficiently certain
- Consistency blocking contradictory conclusions
- Intersection-mode updates that only narrow (never widen) intervals

**Non-Monotonic Mode:**
- When `inconsistency_check=False` and `update_mode='override'`
- New values replace old without checking overlap
- Enables temporal reasoning where beliefs can change over time


---

### Layer 5: Interpretation Updates (Lines 1446-1654, 1801-1868)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Core State Mutation**: These functions handle ALL interpretation updates in PyReason
- **Interval Update Modes**:
  - `override=True`: Direct replacement (non-monotonic)
  - `override=False`: Intersection with existing bound (monotonic refinement)
- **IPL Enforcement**: Automatically maintains Inverse Predicate Law constraints
- **Convergence Tracking**: Monitors change magnitude for fixed-point detection
- **Provenance Recording**: Complete audit trail of all updates

**Implementation Details:**

#### `_update_node(interpretations, predicate_map, comp, na, ipl, rule_trace, fp_cnt, t_cnt, static, convergence_mode, atom_trace, save_graph_attributes_to_rule_trace, rules_to_be_applied_trace, idx, facts_to_be_applied_trace, rule_trace_atoms, store_interpretation_changes, num_ga, mode, override=False)` (1446-1549)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations mapping |
| `predicate_map` | `Dict[Label, List[str]]` | Reverse index: predicate → components |
| `comp` | `str` | Node identifier to update |
| `na` | `Tuple[Label, Interval]` | (label, new_bound) to apply |
| `ipl` | `List[Tuple[Label, Label]]` | Inconsistent Predicate List (complement pairs) |
| `rule_trace` | `List` | Provenance trace storage |
| `fp_cnt` | `int` | Fixed-point iteration counter |
| `t_cnt` | `int` | Timestep counter |
| `static` | `bool` | Whether bound should be marked unchangeable |
| `convergence_mode` | `str` | 'delta_bound' or 'delta_interpretation' |
| `atom_trace` | `bool` | Whether to record detailed atom-level provenance |
| `save_graph_attributes_to_rule_trace` | `bool` | Include graph attributes in trace |
| `rules_to_be_applied_trace` | `List` | Trace of rules being applied |
| `idx` | `int` | Index into trace arrays |
| `facts_to_be_applied_trace` | `List` | Trace of facts being applied |
| `rule_trace_atoms` | `List` | Atom-level trace storage |
| `store_interpretation_changes` | `bool` | Whether to record changes |
| `num_ga` | `List[int]` | Ground atom count per timestep |
| `mode` | `str` | 'fact', 'rule', or 'graph-attribute-fact' |
| `override` | `bool` | If True, use direct update; if False, use intersection |

**Returns:** `Tuple[bool, float]` - (was_updated, change_magnitude)

**Logic Flow:**
1. Get world for component
2. Extract label and bound from na tuple
3. Add label to world if doesn't exist (initialize to [0,1])
4. Store previous bound for comparison
5. Apply update:
   - If override=True: `set_lower_upper()` (direct replacement)
   - If override=False: `world.update()` (intersection)
6. Set static flag
7. Check if value changed
8. Record trace if enabled
9. **IPL Enforcement**: For each (p1, p2) in ipl:
   - If updated label == p1: update p2 to [max(p2.lower, 1-p1.upper), min(p2.upper, 1-p1.lower)]
   - If updated label == p2: update p1 to [max(p1.lower, 1-p2.upper), min(p1.upper, 1-p2.lower)]
10. Calculate convergence metric:
    - If delta_bound mode: max delta across all updated bounds
    - If delta_interpretation mode: 1 + number of IPL updates
11. Return (updated, change)

---

#### `_update_edge(...)` (1552-1654)
**Identical to _update_node** except component type is `Tuple[str, str]` instead of `str`.

**Critical Difference:** Line 1631 contains BUG-125 (appends wrong variable)

---

#### `resolve_inconsistency_node(interpretations, comp, na, ipl, t_cnt, fp_cnt, idx, atom_trace, rule_trace, rule_trace_atoms, rules_to_be_applied_trace, facts_to_be_applied_trace, store_interpretation_changes, mode)` (1801-1833)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations` | `Dict[str, World]` | Node interpretations mapping |
| `comp` | `str` | Node identifier |
| `na` | `Tuple[Label, Interval]` | (label, proposed_bound) that was inconsistent |
| `ipl` | `List[Tuple[Label, Label]]` | Inconsistent Predicate List |
| `t_cnt` | `int` | Timestep counter |
| `fp_cnt` | `int` | Fixed-point iteration counter |
| `idx` | `int` | Index into trace arrays |
| `atom_trace` | `bool` | Whether to record atom-level trace |
| `rule_trace` | `List` | Provenance trace storage |
| `rule_trace_atoms` | `List` | Atom-level trace storage |
| `rules_to_be_applied_trace` | `List` | Trace of rules being applied |
| `facts_to_be_applied_trace` | `List` | Trace of facts being applied |
| `store_interpretation_changes` | `bool` | Whether to record changes |
| `mode` | `str` | 'fact', 'rule', or 'graph-attribute-fact' |

**Returns:** None (modifies world in-place)

**Logic Flow:**
1. Record inconsistency in trace (bound set to [0,1])
2. Get name of causing fact/rule for trace
3. Set inconsistent label to [0,1] (totally uncertain)
4. Set label as static (prevent future updates)
5. For each IPL complement of the inconsistent label:
   - Also set complement to [0,1] and mark static
   - Record in trace

**Semantics:**
When contradictory bounds are detected (non-overlapping intervals), the system cannot determine truth value. It:
1. Resets both the label and its complements to [0,1] (complete uncertainty)
2. Marks them as static to prevent oscillation
3. Records the inconsistency in provenance for debugging

**Example:**
```
IPL: (infected, healthy)
Component: Alice

Facts at t=0:
1. infected(Alice) = [0.8, 0.9]  (80-90% certain)
2. infected(Alice) = [0.1, 0.2]  (10-20% certain) ← CONTRADICTS!

Resolution:
1. check_consistent returns False (no overlap)
2. resolve_inconsistency_node called
3. Set: infected(Alice) = [0,1], healthy(Alice) = [0,1]
4. Mark both as static=True
5. Record: "Inconsistency due to <fact name>"

Result: System acknowledges it doesn't know the truth
```

---

#### `resolve_inconsistency_edge(...)` (1836-1868)
**Identical to resolve_inconsistency_node** except component type and variable name (`w` instead of `world`).

---

**Bugs Logged:**
- BUG-125 (CRITICAL): Wrong variable in convergence tracking (_update_edge line 1631)
- BUG-126 (HIGH): Silent exception swallowing
- BUG-127 (HIGH): Convergence calculation uses wrong previous bound for IPL complements
- BUG-128 (MEDIUM): num_ga not incremented when adding IPL predicates
- BUG-129 (MEDIUM): Missing existence check for IPL complements in resolve_inconsistency
- BUG-130 (LOW): 100% code duplication (273 lines)
- BUG-131 (LOW): Operator precedence bug in resolve_inconsistency
- BUG-132 (LOW): Inconsistent variable naming (world vs w)

**Key Insights:**
- **Most complex state mutation**: Handles 6 concurrent concerns (updates, IPL, trace, convergence, predicate_map, num_ga)
- **Bug asymmetry proves duplication risk**: BUG-125 exists in edge version but not node version
- **Convergence broken for IPL**: Combination of BUG-125 and BUG-127 makes edge convergence unreliable when IPL constraints active
- **Silent failures deadly**: BUG-126 swallows all errors, making debugging impossible
- **IPL enforcement automatic**: Every update triggers complement updates, maintaining logical consistency

---

#### Call Sites & Integration

**`_update_node` / `_update_edge` called from:**
- `reason()` [Layer 9] - Main reasoning loop
  - Line ~302: Apply node facts
  - Line ~431: Apply node rules  
  - Line ~372: Apply edge facts
  - Line ~562: Apply edge rules

**`resolve_inconsistency_node` / `resolve_inconsistency_edge` called from:**
- `reason()` [Layer 9] - When `inconsistency_check=True` and bounds don't overlap
  - Line ~314: Resolve node fact inconsistency
  - Line ~442: Resolve node rule inconsistency
  - Similar for edges

**Integration Pipeline:**
```
reason() [Layer 9]
  ↓
For each fact/rule:
  check_consistent_node/edge() [Layer 4]
    ↓
  If consistent → _update_node/edge() [Layer 5]
    ↓
    - Update world.world[label]
    - Update predicate_map (reverse index)
    - Enforce IPL (update complements)
    - Record provenance (rule_trace, atom_trace)
    - Calculate convergence (delta)
    - Increment num_ga if new label
    ↓
  If inconsistent → resolve_inconsistency_node/edge() [Layer 5]
    ↓
    - Set label and complements to [0,1]
    - Mark as static (unchangeable)
    - Record inconsistency in trace
```

---

#### IPL (Inverse Predicate Law) Enforcement Details

**Rule:** If (P1, P2) are inverse predicates, then P2 ∈ [1-P1.upper, 1-P1.lower]

**Example:**
```
IPL: (infected, healthy)

Update: infected(Alice) = [0.6, 0.8]

IPL Enforcement:
  healthy must satisfy: healthy ∈ [1-0.8, 1-0.6] = [0.2, 0.4]
  
  If healthy currently = [0.0, 1.0]:
    New healthy = [max(0.0, 0.2), min(1.0, 0.4)] = [0.2, 0.4]
  
  If healthy currently = [0.3, 0.5]:
    New healthy = [max(0.3, 0.2), min(0.5, 0.4)] = [0.3, 0.4]
    (intersection: tightens upper bound)
```

**Code Implementation (lines 1503-1505):**
```python
lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
world.world[p2].set_lower_upper(lower, upper)
```

This ensures logical consistency: if we're 60-80% certain of infection, we're 20-40% certain of health.

---

#### Update Mode Semantics

**Override Mode (`override=True`):**
```python
world.world[l].set_lower_upper(bnd.lower, bnd.upper)
```
- Direct replacement, no intersection
- Non-monotonic: can widen intervals
- Used for: graph-attribute-facts, facts in override mode

**Intersection Mode (`override=False`):**
```python
world.update(l, bnd)  # Calls World.update() which does intersection
```
- Monotonic refinement: narrows intervals
- Used for: rules, facts in intersection mode
- Implements: `new = current ∩ proposed`

**Example:**
```
Current: infected(Alice) = [0.3, 0.7]

Proposed update: [0.5, 0.9]

Override mode:
  Result: [0.5, 0.9]  (complete replacement)

Intersection mode:
  Result: [0.5, 0.7]  (overlap of [0.3,0.7] and [0.5,0.9])
```

---

#### Convergence Tracking Semantics

**delta_bound mode:**
Measures maximum change in any interval bound:
```python
for i in updated_bnds:
    lower_delta = abs(i.lower - prev_t_bnd.lower)
    upper_delta = abs(i.upper - prev_t_bnd.upper)
    max_delta = max(lower_delta, upper_delta)
    change = max(change, max_delta)
```

Example:
```
Previous: [0.3, 0.7]
Current:  [0.5, 0.8]
Delta: max(|0.5-0.3|, |0.8-0.7|) = max(0.2, 0.1) = 0.2
```

**delta_interpretation mode:**
Counts number of predicates updated:
```python
change = 1 + ip_update_cnt
```

Example:
```
Update infected → change = 1
IPL updates healthy → ip_update_cnt = 1
Total change = 1 + 1 = 2
```

**Note:** delta_bound mode is BROKEN by BUG-127 when IPL constraints active!

---

#### Code Variants
Functions exist in **3 interpretation implementations** (identical):
1. **interpretation.py**
2. **interpretation_fp.py**
3. **interpretation_parallel.py**

Total duplicated code: 273 lines × 3 = 819 lines across project

---


---

### Layer 6: Graph Mutation Operations (Lines 1869-1962)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Dynamic Graph Topology**: Graph structure can change during reasoning (add/remove nodes and edges)
- **Referential Integrity**: Must maintain consistency across multiple data structures (nodes, edges, neighbors, reverse_neighbors, interpretations, predicate_map)
- **Cascade Deletion**: Deleting a node should cascade to delete incident edges
- **Index Synchronization**: All reverse indexes must be kept in sync with primary data structures

**Implementation Details:**

#### `_add_node(node, neighbors, reverse_neighbors, nodes, interpretations_node)` (1869-1875)

| Parameter | Type | Definition |
|-----------|------|------------|
| `node` | `str` | Node identifier to add |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency: node → [targets] |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency: node → [sources] |
| `nodes` | `List[str]` | List of all nodes in graph |
| `interpretations_node` | `Dict[str, World]` | Node interpretations mapping |

**Returns:** None (modifies structures in-place)

**Logic:**
1. Append node to nodes list
2. Initialize empty neighbor lists for node
3. Initialize empty reverse_neighbor lists for node
4. Create empty World for node (no initial labels)

**Note:** Simple helper function, only called from `_add_edge()` when adding edges with new nodes.

---

#### `_add_edge(source, target, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge, predicate_map, num_ga, t)` (1878-1917)

| Parameter | Type | Definition |
|-----------|------|------------|
| `source` | `str` | Source node identifier |
| `target` | `str` | Target node identifier |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency mapping |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency mapping |
| `nodes` | `List[str]` | List of all nodes |
| `edges` | `List[Tuple[str, str]]` | List of all edges |
| `l` | `Label` | Label to add to edge (can be empty Label('')) |
| `interpretations_node` | `Dict[str, World]` | Node interpretations |
| `interpretations_edge` | `Dict[Tuple[str, str], World]` | Edge interpretations |
| `predicate_map` | `Dict[Label, List[component]]` | Reverse index: label → components |
| `num_ga` | `List[int]` | Ground atom count per timestep |
| `t` | `int` | Timestep index for num_ga |

**Returns:** `Tuple[edge, bool]` - (edge tuple, new_edge flag)

**Logic:**
1. If source not in nodes → call `_add_node()` to add it
2. If target not in nodes → call `_add_node()` to add it
3. Create edge tuple `(source, target)`
4. **If edge doesn't exist:**
   - Add to edges list
   - Add to neighbors[source] and reverse_neighbors[target]
   - If label not empty: create World with label, increment num_ga, update predicate_map
   - If label empty: create empty World
   - Set new_edge = True
5. **If edge exists:**
   - If label not in edge's world and not empty:
     - Add label to existing World
     - Increment num_ga
     - Update predicate_map
     - Set new_edge = True
6. Return (edge, new_edge)

**Edge Cases:**
- Empty label (Label('')): Creates edge without initial labels
- Duplicate additions: Second call with same edge returns new_edge=False (unless new label)
- Auto-creates nodes: If source/target don't exist, adds them automatically

---

#### `_add_edges(sources, targets, neighbors, reverse_neighbors, nodes, edges, l, interpretations_node, interpretations_edge, predicate_map, num_ga, t)` (1920-1929)

**Batch version of _add_edge**. Creates Cartesian product of sources × targets.

| Parameter | Type | Definition |
|-----------|------|------------|
| `sources` | `List[str]` | List of source nodes |
| `targets` | `List[str]` | List of target nodes |
| Other params | Same as _add_edge | Same as _add_edge |

**Returns:** `Tuple[List[edge], int]` - (edges_added list, change count)

**Logic:**
```python
for source in sources:
    for target in targets:
        edge, new_edge = _add_edge(source, target, ...)
        edges_added.append(edge)  # Always appends (BUG-136)
        changes += 1 if new_edge else 0
```

**Use Case:**
Called from `reason()` main loop (line 468) when applying rules that add multiple edges.

---

#### `_delete_edge(edge, neighbors, reverse_neighbors, edges, interpretations_edge, predicate_map, num_ga)` (1932-1942)

| Parameter | Type | Definition |
|-----------|------|------------|
| `edge` | `Tuple[str, str]` | Edge to delete |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency |
| `edges` | `List[Tuple[str, str]]` | List of all edges |
| `interpretations_edge` | `Dict[Tuple[str, str], World]` | Edge interpretations |
| `predicate_map` | `Dict[Label, List[component]]` | Reverse index |
| `num_ga` | `List[int]` | Ground atom count per timestep |

**Returns:** None (modifies structures in-place)

**Logic:**
1. Unpack edge into (source, target)
2. Remove edge from edges list
3. Decrement num_ga[-1] by number of labels on edge
4. Delete edge from interpretations_edge
5. Remove edge from predicate_map for all predicates (BUG-137: inefficient)
6. Remove target from neighbors[source]
7. Remove source from reverse_neighbors[target]

**Note:** Does NOT delete nodes, even if they become isolated.

---

#### `_delete_node(node, neighbors, reverse_neighbors, nodes, interpretations_node, predicate_map, num_ga)` (1945-1962)

| Parameter | Type | Definition |
|-----------|------|------------|
| `node` | `str` | Node to delete |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency |
| `nodes` | `List[str]` | List of all nodes |
| `interpretations_node` | `Dict[str, World]` | Node interpretations |
| `predicate_map` | `Dict[Label, List[component]]` | Reverse index |
| `num_ga` | `List[int]` | Ground atom count per timestep |

**Returns:** None (modifies structures in-place)

**Logic:**
1. Remove node from nodes list
2. Decrement num_ga[-1] by number of labels on node
3. Delete node from interpretations_node
4. Delete node's neighbor lists
5. Remove node from predicate_map for all predicates (BUG-137: inefficient)
6. Remove node from all other nodes' neighbor lists (cleanup dangling references)
7. Remove node from all other nodes' reverse_neighbor lists

**CRITICAL BUG:** Does NOT delete edges involving this node (BUG-133)!

---

**Bugs Logged:**
- BUG-133 (CRITICAL): Missing edge cleanup when deleting nodes
- BUG-134 (MEDIUM): Misleading new_edge semantics (returns True for new label on existing edge)
- BUG-135 (MEDIUM): No IPL enforcement in _add_edge (no ipl parameter)
- BUG-136 (LOW): Duplicate edges in _add_edges return value
- BUG-137 (LOW): Inefficient predicate_map iteration (O(P) instead of O(L))

**Key Insights:**
- **Graph mutation is dangerous**: BUG-133 can corrupt graph structure with orphaned edges
- **Inconsistent IPL enforcement**: Updates enforce IPL (Layer 5), but additions don't (Layer 6)
- **Missing parameters**: _add_edge lacks `ipl` parameter, preventing proper enforcement
- **No transaction semantics**: Operations can fail partway through, leaving inconsistent state
- **Design feels incomplete**: Less polished than interpretation update functions (Layer 5)

---

#### Call Sites & Integration

**`_add_node` called from:**
- `_add_edge()` (lines 1881, 1884): Auto-creates nodes when adding edges

**`_add_edge` called from:**
- Public API `add_edge()` (line 664): User-facing graph modification
- `reason()` main loop (line 352): Add edges during fact application
- `_ground_rule()` (line 1215): Add edges-to-be-added from rule heads

**`_add_edges` called from:**
- `reason()` main loop (line 468): Batch add edges from rule application

**`_delete_edge` called from:**
- Public API `delete_edge()` (line 675): For pyreason gym (RL environment)

**`_delete_node` called from:**
- Public API `delete_node()` (line 679): For pyreason gym (RL environment)

**Integration Pipeline:**
```
User / Reasoning Engine
  ↓
add_edge() / delete_edge() / delete_node()  [Public API - Layer 10]
  ↓
_add_edge() / _delete_edge() / _delete_node()  [Layer 6]
  ↓
Updates: nodes, edges, neighbors, reverse_neighbors
         interpretations_node, interpretations_edge
         predicate_map, num_ga
```

**Usage Context:**
- **Static graphs**: Most users don't modify graph during reasoning
- **Dynamic graphs**: pyreason gym uses deletion for RL environments
- **Rule-driven additions**: Rules can add new edges via head functions

---

#### Referential Integrity Requirements

For graph to be consistent, the following invariants must hold:

**Invariant 1: Node existence**
```
∀ edge (s, t) ∈ edges: s ∈ nodes AND t ∈ nodes
```
Violated by: BUG-133 (deleting node doesn't delete edges)

**Invariant 2: Edge interpretations**
```
∀ edge ∈ edges: edge ∈ interpretations_edge.keys()
∀ edge ∈ interpretations_edge.keys(): edge ∈ edges
```
Violated by: BUG-133 (interpretations_edge has orphaned entries)

**Invariant 3: Neighbor symmetry**
```
∀ edge (s, t) ∈ edges: 
  t ∈ neighbors[s] AND s ∈ reverse_neighbors[t]
```
Maintained correctly (even after deletions)

**Invariant 4: Predicate map accuracy**
```
∀ label l, ∀ component c ∈ predicate_map[l]:
  l ∈ interpretations[c].world.keys()
```
Could be violated by: BUG-133 (predicate_map_edge references deleted edges)

**Invariant 5: Ground atom count**
```
num_ga[t] = Σ_c len(interpretations[c].world)
```
Violated by: BUG-128 (IPL predicates not counted)
Maintained by: deletions (correctly decrement)

---

#### Design Patterns & Tradeoffs

**Pattern 1: Auto-create nodes**
- `_add_edge()` automatically creates source/target if they don't exist
- **Pro:** Convenient for users, no need to pre-create nodes
- **Con:** Can hide bugs (typos in node names silently create new nodes)

**Pattern 2: No cascade deletion**
- `_delete_edge()` doesn't delete isolated nodes
- **Pro:** Explicit control over node lifetime
- **Con:** Can leave orphaned nodes in graph (though interpretations preserved)

**Pattern 3: In-place mutation**
- All functions modify structures directly, no return values (except _add_edge/edges)
- **Pro:** Efficient, no copying
- **Con:** No rollback if operation fails partway through

**Pattern 4: Missing IPL enforcement**
- Graph mutations don't enforce IPL, updates do
- **Pro:** Simpler implementation
- **Con:** Inconsistent behavior, can violate logical constraints

**Recommendation:** Add IPL parameter to _add_edge and enforce complements for consistency with Layer 5.

---

#### Code Variants
Functions exist in **3 interpretation implementations** (identical):
1. **interpretation.py**
2. **interpretation_fp.py**
3. **interpretation_parallel.py**

Total duplicated code: 94 lines × 3 = 282 lines across project

---


---

### Layer 7A: Grounding Helpers (Lines 1228-1411)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Rule Grounding**: Process of finding all variable bindings that satisfy a rule's body clauses
- **Threshold Quantification**: Rules can require "at least 50% of neighbors" to satisfy a condition
- **Dependency Graph**: Variables in a rule form a graph showing which variables constrain others
- **Refinement**: After binding one variable, propagate constraints to narrow other variables' possible values
- **Qualified vs Total**: Distinguish between all possible components and those satisfying a predicate

**Implementation Details:**

#### `check_all_clause_satisfaction(interpretations_node, interpretations_edge, clauses, thresholds, groundings, groundings_edges)` (1228-1244)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations_node` | `Dict[str, World]` | Node interpretations |
| `interpretations_edge` | `Dict[Tuple, World]` | Edge interpretations |
| `clauses` | `List[Tuple]` | Rule body clauses to check |
| `thresholds` | `List[Tuple]` | Threshold for each clause |
| `groundings` | `Dict[str, List]` | Variable → possible node bindings |
| `groundings_edges` | `Dict[Tuple, List]` | Variable pair → possible edge bindings |

**Returns:** `bool` - True if all clause thresholds satisfied

**Logic:**
1. Initialize satisfaction = True
2. For each clause with its threshold:
   - If node clause: check node threshold satisfaction
   - If edge clause: check edge threshold satisfaction
   - AND result with current satisfaction
3. Return overall satisfaction

**CRITICAL BUG:** Passes same grounding twice (BUG-138) - breaks threshold checking!

---

#### `refine_groundings(clause_variables, groundings, groundings_edges, dependency_graph_neighbors, dependency_graph_reverse_neighbors)` (1247-1302)

| Parameter | Type | Definition |
|-----------|------|------------|
| `clause_variables` | `List[str]` | Variables that have been bound so far |
| `groundings` | `Dict[str, List]` | Current variable bindings |
| `groundings_edges` | `Dict[Tuple, List]` | Current edge bindings |
| `dependency_graph_neighbors` | `Dict[str, List[str]]` | Variable dependency graph (forward) |
| `dependency_graph_reverse_neighbors` | `Dict[str, List[str]]` | Variable dependency graph (backward) |

**Returns:** None (modifies groundings in-place)

**Logic:**
This function propagates variable binding constraints through the dependency graph.

**When Called:**
`refine_groundings` is called **after processing some clauses** but **before processing all of them**. It ensures that variable bindings remain consistent as more constraints are added.

**Complete Example:**
```
Rule: infected(X) ∧ neighbor(X,Y) ∧ age(Y,Z) → risk(Z)

Dependency graph (built from clause structure):
  X → Y  (X constrains Y through neighbor(X,Y) clause)
  Y → Z  (Y constrains Z through age(Y,Z) clause)

Processing Timeline:
  Step 1: Process infected(X) → X is bound to [Alice, Bob, Carol]
  Step 2: Process neighbor(X,Y) → Y is bound to [Dave, Eve, Frank, George, Henry]
  Step 3: CALL refine_groundings ← We are here!
  Step 4: Process age(Y,Z) → Z will be bound
  Step 5: CALL refine_groundings again

Initial state (BEFORE refine_groundings is called):
  clause_variables = ['X', 'Y']  # Both variables have been bound so far

  groundings = {
    'X': [Alice, Bob, Carol],
    'Y': [Dave, Eve, Frank, George, Henry]  # Henry is the problem!
  }

  groundings_edges = {
    ('X', 'Y'): [(Alice,Dave), (Alice,Eve), (Bob,Frank), (Carol,George)]
  }

  # Why is Henry in groundings[Y]?
  # When processing neighbor(X,Y), we:
  # 1. Called get_rule_edge_clause_grounding() which returned edges
  # 2. Extracted Y values: [Dave, Eve, Frank, George]
  # 3. But Y might have been added from other sources:
  #    - Y could appear in the predicate_map
  #    - Y could be from an earlier clause in a different order
  #    - Initial grounding might include all nodes with certain predicates
  # 4. Result: Y has extra values that don't actually connect to any X value!

Call to refine_groundings:
  refine_groundings(
    clause_variables=['X', 'Y'],  # All variables bound so far
    groundings={...},
    groundings_edges={...},
    dependency_graph_neighbors={'X': ['Y'], 'Y': ['Z']},
    dependency_graph_reverse_neighbors={'Y': ['X'], 'Z': ['Y']}
  )

Refinement process:

Iteration 1:
  variables_just_refined = ['X', 'Y']  # Start with all clause_variables

  Processing X (has forward neighbor Y):
    - old_edge_groundings = groundings_edges[('X','Y')]
      = [(Alice,Dave), (Alice,Eve), (Bob,Frank), (Carol,George)]
    - new_node_groundings = groundings['X'] = [Alice, Bob, Carol]
    - Filter edges: keep only edges where source ∈ [Alice, Bob, Carol]
      qualified = [(Alice,Dave), (Alice,Eve), (Bob,Frank), (Carol,George)]
      (All edges have valid X values, so all kept)
    - Extract Y values from filtered edges: [Dave, Eve, Frank, George]
    - UPDATE groundings['Y'] = [Dave, Eve, Frank, George]
      ← Henry REMOVED! He wasn't in any edge with X

  Processing Y (has forward neighbor Z, but Z not bound yet):
    - Y has no forward neighbor that's been bound yet
    - Skip for now (will refine Z when we process age(Y,Z) clause)

Iteration 2:
  variables_just_refined = []  # No new variables refined
  Loop exits

Final state (AFTER refine_groundings):
  groundings = {
    'X': [Alice, Bob, Carol],
    'Y': [Dave, Eve, Frank, George]  # ✓ Henry removed!
  }

  groundings_edges = {
    ('X', 'Y'): [(Alice,Dave), (Alice,Eve), (Bob,Frank), (Carol,George)]
  }

Later (after processing age(Y,Z)):
  clause_variables = ['X', 'Y', 'Z']
  refine_groundings(['X', 'Y', 'Z'], ...)
  # Now refines Z based on Y's final values
```

**Algorithm:**
1. Start with variables just refined (initially: all clause variables)
2. For each refined variable:
   - Find forward neighbors in dependency graph
   - For each neighbor:
     - Filter edge groundings to only include refined variable's bindings
     - Extract target values and update neighbor's groundings
     - Mark neighbor as refined
   - Find reverse neighbors (same process, opposite direction)
3. Repeat until no new variables refined

**Key Insight:** This prevents invalid combinations where a variable takes a value that can't connect to other variables' values.

---

#### `check_node_grounding_threshold_satisfaction(interpretations_node, grounding, qualified_grounding, clause_label, threshold)` (1305-1317)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations_node` | `Dict[str, World]` | Node interpretations |
| `grounding` | `List[str]` | Total possible node bindings |
| `qualified_grounding` | `List[str]` | Bindings satisfying clause predicate/bound |
| `clause_label` | `Label` | Predicate to check |
| `threshold` | `Tuple` | Threshold structure: (operator, (mode, quantifier_type), value) |

**Returns:** `bool` - True if threshold satisfied

**Logic:**
1. Extract threshold_quantifier_type from threshold
2. If 'total': neigh_len = total bindings
3. If 'available': neigh_len = available bindings (those with predicate in [0,1])
4. Calculate qualified_neigh_len
5. Check if qualified/total satisfies threshold (e.g., >= 50%)

**Threshold Modes:**
- **'total'**: Denominator is all possible components
  - Example: "At least 50% of all neighbors"
- **'available'**: Denominator is components that have the predicate
  - Example: "At least 50% of neighbors with 'infected' label"

**Example:**
```
Threshold: [available, >=, 50%]
Clause: infected(X) with bound [0.7, 1.0]

grounding = [Alice, Bob, Carol, Dave]  # All neighbors
qualified_grounding = [Bob, Carol]      # Neighbors with infected >= 0.7

If threshold_quantifier_type == 'available':
  # How many neighbors have 'infected' label at all?
  available = get_qualified_node_groundings(..., interval.closed(0, 1))
  # = [Alice, Bob, Carol]  (Dave doesn't have infected label)
  neigh_len = 3

qualified_neigh_len = 2  (Bob, Carol)

Check: 2/3 = 66.7% >= 50%? YES ✓
```

---

#### `check_edge_grounding_threshold_satisfaction(...)` (1320-1332)
Identical to node version, operates on edges instead. See BUG-142.

---

#### `get_rule_node_clause_grounding(clause_var_1, groundings, predicate_map, l, nodes)` (1335-1342)

| Parameter | Type | Definition |
|-----------|------|------------|
| `clause_var_1` | `str` | Variable name (e.g., 'X') |
| `groundings` | `Dict[str, List]` | Existing variable bindings |
| `predicate_map` | `Dict[Label, List]` | Reverse index: label → components |
| `l` | `Label` | Predicate being queried |
| `nodes` | `List[str]` | All nodes in graph |

**Returns:** `List[str]` - Possible bindings for variable

**Logic:**
```
If variable already bound:
    Return existing bindings
Else if predicate exists in predicate_map:
    Return components with that predicate
Else:
    Return all nodes (predicate doesn't exist on any node)
```

**Concrete Examples Using Consistent Graph:**

First, let's establish the graph structure (same as used for edge grounding):

```
Graph Structure:
  Nodes: [Alice, Bob, Carol, Dave, Eve, Frank, George, Henry]

  Edges:
    Alice → Dave, Eve
    Bob → Frank
    Carol → George
    Dave → Henry
    Eve → Henry

Node Predicates (example interpretations):
  Alice: infected=[0.8, 0.9]
  Bob: infected=[0.6, 0.7], vaccinated=[0.9, 1.0]
  Carol: infected=[0.9, 1.0]
  Dave: vaccinated=[0.8, 0.9]
  Eve: vaccinated=[0.7, 0.8]
  Frank: (no predicates yet)
  George: (no predicates yet)
  Henry: (no predicates yet)

predicate_map (reverse index):
  Label('infected'): [Alice, Bob, Carol]
  Label('vaccinated'): [Bob, Dave, Eve]
```

---

**Case 1: Variable not bound, predicate EXISTS** (Most common - first clause in rule)

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ ...
Clause: infected(X)  # First clause

Input:
  clause_var_1 = 'X'  (not in groundings)
  groundings = {}  # Empty - no variables bound yet
  predicate_map = {
    Label('infected'): [Alice, Bob, Carol],
    Label('vaccinated'): [Bob, Dave, Eve]
  }
  l = Label('infected')
  nodes = [Alice, Bob, Carol, Dave, Eve, Frank, George, Henry]

Code path (lines 1335-1342):
  if clause_var_1 in groundings:
      # Not taken - X not in groundings yet
  else:
      if l in predicate_map:
          node_groundings = predicate_map[l]  # ← THIS PATH
      else:
          node_groundings = nodes

Execution:
  Label('infected') in predicate_map? YES
  Return: predicate_map[Label('infected')]

Return: [Alice, Bob, Carol]

Why this is efficient:
  - O(1) lookup in predicate_map dictionary
  - Avoids scanning all nodes in the graph
  - Only returns nodes that actually have this predicate
  - This is why PyReason maintains the predicate_map reverse index!

Next steps in rule grounding:
  - These 3 candidates will be filtered by get_qualified_node_groundings()
  - Only nodes with infected >= threshold will remain
  - Example: if clause requires infected:[0.7,1.0]
    → Alice: [0.8,0.9] ✓ satisfies
    → Bob: [0.6,0.7] ✗ too low (0.6 < 0.7)
    → Carol: [0.9,1.0] ✓ satisfies
  - Final: groundings[X] = [Alice, Carol]
```

---

**Case 2: Variable not bound, predicate DOES NOT EXIST**

```python
Rule: admin(X) ∧ neighbor(X,Y) ∧ ...
Clause: admin(X)  # First clause

Input:
  clause_var_1 = 'X'  (not in groundings)
  groundings = {}
  predicate_map = {
    Label('infected'): [Alice, Bob, Carol],
    Label('vaccinated'): [Bob, Dave, Eve]
    # 'admin' is NOT in predicate_map!
  }
  l = Label('admin')
  nodes = [Alice, Bob, Carol, Dave, Eve, Frank, George, Henry]

Code path:
  if clause_var_1 in groundings:
      # Not taken - X not in groundings yet
  else:
      if l in predicate_map:
          # Not taken - 'admin' not in predicate_map
      else:
          node_groundings = nodes  # ← THIS PATH

Execution:
  Label('admin') in predicate_map? NO
  Return: nodes

Return: [Alice, Bob, Carol, Dave, Eve, Frank, George, Henry]

Why return ALL nodes?
  - The predicate doesn't exist on ANY node yet
  - Rule might be adding this predicate for the first time
  - All nodes are potential candidates
  - Later filtering (get_qualified_node_groundings) will handle satisfaction

Example rule that adds new predicates:
  neighbor(X,Y) ∧ infected(Y) → risk(X)
  # 'risk' might not exist initially
  # Return all nodes for X, filter by neighbor relationship later

Warning:
  - This can be expensive if graph has many nodes
  - O(n) where n = number of nodes
  - Later clauses must filter aggressively to avoid combinatorial explosion
```

---

**Case 3: Variable ALREADY BOUND** (Later clauses in rule)

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ infected(Y) ∧ vaccinated(X) ∧ ...
                                      ↑              ↑
                                   2nd clause    4th clause
Clause: vaccinated(X)  # Fourth clause - X already bound from infected(X)

Input:
  clause_var_1 = 'X'  (ALREADY in groundings)
  groundings = {
    'X': [Alice, Carol],  # From infected(X) clause earlier
    'Y': [Dave, Eve]      # From neighbor and infected(Y) clauses
  }
  predicate_map = {
    Label('infected'): [Alice, Bob, Carol],
    Label('vaccinated'): [Bob, Dave, Eve]
  }
  l = Label('vaccinated')
  nodes = [Alice, Bob, Carol, Dave, Eve, Frank, George, Henry]

Code path:
  if clause_var_1 in groundings:
      node_groundings = groundings[clause_var_1]  # ← THIS PATH
  else:
      # Not taken - X is already bound

Execution:
  'X' in groundings? YES
  Return: groundings['X']

Return: [Alice, Carol]

Why respect existing bindings?
  - X has already been constrained by earlier clauses
  - infected(X) filtered X to [Alice, Carol]
  - neighbor(X,Y) further validated these bindings
  - We must honor this constraint - can't introduce new X values!

What happens next?
  - get_qualified_node_groundings will check:
    Does Alice have vaccinated predicate with correct bounds?
    Does Carol have vaccinated predicate with correct bounds?

  Looking at our graph:
    Alice: infected=[0.8,0.9], NO vaccinated ✗
    Carol: infected=[0.9,1.0], NO vaccinated ✗

  Result: groundings[X] becomes EMPTY []
  Rule will NOT fire - no X satisfies all clauses!

Alternative outcome:
  If Alice had vaccinated=[0.5,0.6]:
    infected(X): Alice ✓
    neighbor(X,Y): Alice→Dave ✓, Alice→Eve ✓
    infected(Y): Dave ✗, Eve ✗ (neither infected)
    # Rule still won't fire due to Y clause failure

Key insight:
  - Clauses progressively narrow the binding set
  - Order matters for performance but not correctness
  - Once a variable is bound, that binding is reused (not recomputed)
```

---

**Summary: Three Cases Comparison**

| Case | Condition | Return Value | Time Complexity | Use Case |
|------|-----------|--------------|-----------------|----------|
| **1** | Variable new, predicate exists | `predicate_map[l]` | O(1) | First clause with common predicate |
| **2** | Variable new, predicate missing | `nodes` (all) | O(1) reference | First clause with new/rare predicate |
| **3** | Variable already bound | `groundings[var]` | O(1) | Later clauses re-checking same variable |

**Performance Characteristics:**

Case 1 (predicate_map lookup):
- **Best case**: Predicate exists on few nodes → small candidate set
- Example: `admin` might only apply to 2-3 nodes out of 10,000
- Avoids iterating through entire graph

Case 2 (return all nodes):
- **Worst case**: Must consider entire graph
- Example: 10,000 nodes → 10,000 candidates
- Later clauses MUST filter aggressively
- This is why predicate_map is so important for performance!

Case 3 (reuse binding):
- **Always optimal**: Respects prior constraints
- No redundant computation
- Ensures logical consistency

**Use Case:** First clause in rule determines initial bindings using predicate_map (fast!).

---

#### `get_rule_edge_clause_grounding(clause_var_1, clause_var_2, groundings, groundings_edges, neighbors, reverse_neighbors, predicate_map, l, edges)` (1345-1389)

Handles edge clauses like `neighbor(X,Y)` with 4 different cases based on which variables are already bound.

| Parameter | Type | Definition |
|-----------|------|------------|
| `clause_var_1` | `str` | Source variable (X) |
| `clause_var_2` | `str` | Target variable (Y) |
| `groundings` | `Dict` | Node variable bindings |
| `groundings_edges` | `Dict` | Edge variable bindings |
| `neighbors` | `Dict` | Forward adjacency |
| `reverse_neighbors` | `Dict` | Backward adjacency |
| `predicate_map` | `Dict` | Label → edges mapping |
| `l` | `Label` | Edge predicate |
| `edges` | `List[Tuple]` | All edges |

**Returns:** `List[Tuple[str, str]]` - Possible edge bindings

**Concrete Example Using Consistent Graph:**

First, let's establish the graph structure we'll use for all 4 cases:

```
Graph Structure:
  Alice → Dave
  Alice → Eve
  Bob → Frank
  Carol → George
  Dave → Henry
  Eve → Henry

Adjacency structures:
  neighbors = {
    'Alice': [Dave, Eve],
    'Bob': [Frank],
    'Carol': [George],
    'Dave': [Henry],
    'Eve': [Henry],
    'Frank': [],
    'George': [],
    'Henry': []
  }

  reverse_neighbors = {
    'Alice': [],
    'Bob': [],
    'Carol': [],
    'Dave': [Alice],
    'Eve': [Alice],
    'Frank': [Bob],
    'George': [Carol],
    'Henry': [Dave, Eve]
  }

  edges = [
    (Alice,Dave), (Alice,Eve), (Bob,Frank),
    (Carol,George), (Dave,Henry), (Eve,Henry)
  ]
```

---

**Case 1: Neither variable bound** (`X` and `Y` both new)

```python
Rule: neighbor(X,Y) ∧ infected(X) ∧ ...
Clause: neighbor(X,Y)  # First clause

Input:
  clause_var_1 = 'X'  (not in groundings)
  clause_var_2 = 'Y'  (not in groundings)
  groundings = {}  # Empty - no variables bound yet
  l = Label('neighbor')

Code path (lines 1355-1359):
  if clause_var_1 not in groundings and clause_var_2 not in groundings:
      if l in predicate_map:
          edge_groundings = predicate_map[l]
      else:
          edge_groundings = edges

If 'neighbor' in predicate_map:
  Return: predicate_map[Label('neighbor')]
  # All edges with 'neighbor' label

Else (predicate doesn't exist or has no label):
  Return: edges = [
    (Alice,Dave), (Alice,Eve), (Bob,Frank),
    (Carol,George), (Dave,Henry), (Eve,Henry)
  ]

Result: All edges in the graph
Why: We haven't narrowed down either variable yet, so all edges are possible
```

---

**Case 2: Target bound, source unbound** (`Y` known, find `X`)

```python
Rule: infected(Y) ∧ neighbor(X,Y) ∧ ...
Clause: neighbor(X,Y)  # Second clause, Y already bound

Input:
  clause_var_1 = 'X'  (not in groundings)
  clause_var_2 = 'Y'  (in groundings = [Dave, Frank])
  groundings = {
    'Y': [Dave, Frank]  # From infected(Y) clause
  }

Code path (lines 1363-1366):
  elif clause_var_1 not in groundings and clause_var_2 in groundings:
      for n in groundings[clause_var_2]:
          es = numba.typed.List([(nn, n) for nn in reverse_neighbors[n]])
          edge_groundings.extend(es)

Execution:
  edge_groundings = []

  For n = Dave:
    reverse_neighbors[Dave] = [Alice]
    Create edges: [(nn, Dave) for nn in [Alice]]
    → [(Alice, Dave)]
    edge_groundings = [(Alice, Dave)]

  For n = Frank:
    reverse_neighbors[Frank] = [Bob]
    Create edges: [(nn, Frank) for nn in [Bob]]
    → [(Bob, Frank)]
    edge_groundings = [(Alice,Dave), (Bob,Frank)]

Return: [(Alice,Dave), (Bob,Frank)]

Why reverse_neighbors?
  - We know the TARGET (Y = Dave, Frank)
  - We need to find the SOURCE (X = ?)
  - reverse_neighbors[Dave] tells us "who points TO Dave"
  - Answer: Alice points to Dave → edge (Alice,Dave)
  - reverse_neighbors[Frank] tells us "who points TO Frank"
  - Answer: Bob points to Frank → edge (Bob,Frank)
```

---

**Case 3: Source bound, target unbound** (`X` known, find `Y`)

```python
Rule: infected(X) ∧ neighbor(X,Y) ∧ ...
Clause: neighbor(X,Y)  # Second clause, X already bound

Input:
  clause_var_1 = 'X'  (in groundings = [Alice, Carol])
  clause_var_2 = 'Y'  (not in groundings)
  groundings = {
    'X': [Alice, Carol]  # From infected(X) clause
  }

Code path (lines 1370-1373):
  elif clause_var_1 in groundings and clause_var_2 not in groundings:
      for n in groundings[clause_var_1]:
          es = numba.typed.List([(n, nn) for nn in neighbors[n]])
          edge_groundings.extend(es)

Execution:
  edge_groundings = []

  For n = Alice:
    neighbors[Alice] = [Dave, Eve]
    Create edges: [(Alice, nn) for nn in [Dave, Eve]]
    → [(Alice,Dave), (Alice,Eve)]
    edge_groundings = [(Alice,Dave), (Alice,Eve)]

  For n = Carol:
    neighbors[Carol] = [George]
    Create edges: [(Carol, nn) for nn in [George]]
    → [(Carol,George)]
    edge_groundings = [(Alice,Dave), (Alice,Eve), (Carol,George)]

Return: [(Alice,Dave), (Alice,Eve), (Carol,George)]

Why neighbors (not reverse_neighbors)?
  - We know the SOURCE (X = Alice, Carol)
  - We need to find the TARGET (Y = ?)
  - neighbors[Alice] tells us "who does Alice point TO"
  - Answer: Alice points to [Dave, Eve] → edges (Alice,Dave), (Alice,Eve)
  - neighbors[Carol] tells us "who does Carol point TO"
  - Answer: Carol points to [George] → edge (Carol,George)
```

---

**Case 4: Both variables bound** (`X` and `Y` both known)

```python
Rule: infected(X) ∧ status(Y) ∧ neighbor(X,Y) ∧ ...
Clause: neighbor(X,Y)  # Third clause, both X and Y already bound

Input:
  clause_var_1 = 'X'  (in groundings = [Alice, Bob, Dave])
  clause_var_2 = 'Y'  (in groundings = [Dave, Eve, Frank])
  groundings = {
    'X': [Alice, Bob, Dave],  # From infected(X) clause
    'Y': [Dave, Eve, Frank]   # From status(Y) clause
  }
  groundings_edges = {}  # No (X,Y) edge clause processed yet

Code path (lines 1377-1386):
  else:
      # We have seen both variables before
      if (clause_var_1, clause_var_2) in groundings_edges:
          edge_groundings = groundings_edges[(clause_var_1, clause_var_2)]
      else:
          groundings_clause_var_2_set = set(groundings[clause_var_2])
          for n in groundings[clause_var_1]:
              es = numba.typed.List([(n, nn) for nn in neighbors[n]
                                      if nn in groundings_clause_var_2_set])
              edge_groundings.extend(es)

Sub-case 4a: (X,Y) already in groundings_edges
  # If we've processed an edge clause with these variables before
  Return: groundings_edges[(X,Y)]  # Reuse cached result

Sub-case 4b: Both variables bound separately (first time seeing them together)
  Execution:
    edge_groundings = []
    groundings_clause_var_2_set = {Dave, Eve, Frank}  # Y values as set

    For n = Alice (X value):
      neighbors[Alice] = [Dave, Eve]
      Filter: keep only if in Y values
        Dave in {Dave, Eve, Frank}? YES → (Alice,Dave)
        Eve in {Dave, Eve, Frank}? YES → (Alice,Eve)
      edge_groundings = [(Alice,Dave), (Alice,Eve)]

    For n = Bob (X value):
      neighbors[Bob] = [Frank]
      Filter: keep only if in Y values
        Frank in {Dave, Eve, Frank}? YES → (Bob,Frank)
      edge_groundings = [(Alice,Dave), (Alice,Eve), (Bob,Frank)]

    For n = Dave (X value):
      neighbors[Dave] = [Henry]
      Filter: keep only if in Y values
        Henry in {Dave, Eve, Frank}? NO → Skip
      edge_groundings = [(Alice,Dave), (Alice,Eve), (Bob,Frank)]

  Return: [(Alice,Dave), (Alice,Eve), (Bob,Frank)]

Why the filter?
  - We need edges where BOTH endpoints are in our bindings
  - X must be in [Alice, Bob, Dave]
  - Y must be in [Dave, Eve, Frank]
  - (Alice,Dave): Alice ✓ in X, Dave ✓ in Y → Include
  - (Alice,Eve): Alice ✓ in X, Eve ✓ in Y → Include
  - (Alice,George): Alice ✓ in X, George ✗ not in Y → Exclude
  - (Bob,Frank): Bob ✓ in X, Frank ✓ in Y → Include
  - (Dave,Henry): Dave ✓ in X, Henry ✗ not in Y → Exclude
```

---

**Summary: When to use neighbors vs reverse_neighbors**

| Case | Known | Unknown | Use | Why |
|------|-------|---------|-----|-----|
| 1 | Neither | Both | `edges` or `predicate_map` | No constraints yet |
| 2 | Target (Y) | Source (X) | `reverse_neighbors[Y]` | "Who points TO Y?" |
| 3 | Source (X) | Target (Y) | `neighbors[X]` | "Who does X point TO?" |
| 4 | Both | None | `neighbors[X]` + filter | "Does X→Y exist and both valid?" |

**Key Insight:** `reverse_neighbors` is used when we know the TARGET and need to find the SOURCE. `neighbors` is used when we know the SOURCE and need to find the TARGET.

---

#### `get_qualified_node_groundings(interpretations_node, grounding, clause_l, clause_bnd)` (1392-1400)

| Parameter | Type | Definition |
|-----------|------|------------|
| `interpretations_node` | `Dict` | Node interpretations |
| `grounding` | `List[str]` | Candidate node bindings |
| `clause_l` | `Label` | Predicate to check |
| `clause_bnd` | `Interval` | Required bound |

**Returns:** `List[str]` - Nodes satisfying predicate with bound

**Logic:**
```python
qualified = []
for node in grounding:
    if is_satisfied_node(interpretations_node, node, (clause_l, clause_bnd)):
        qualified.append(node)
return qualified
```

**Example:**
```
grounding = [Alice, Bob, Carol, Dave]
clause: infected with bound [0.7, 1.0]

Check each:
  Alice: infected=[0.8,0.9] ⊆ [0.7,1.0]? NO (lower bound 0.8 > 0.7, but contained)
  Wait, let me recalculate...
  
  Alice: infected=[0.8,0.9], required=[0.7,1.0]
    is_satisfied checks if required contains world bound
    [0.7,1.0] contains [0.8,0.9]? YES ✓
  
  Bob: infected=[0.6,0.75], required=[0.7,1.0]  
    [0.7,1.0] contains [0.6,0.75]? NO (0.6 < 0.7)
  
  Carol: infected=[0.9,1.0], required=[0.7,1.0]
    [0.7,1.0] contains [0.9,1.0]? YES ✓

qualified = [Alice, Carol]
```

**Use Case:** Filter variable bindings to only those satisfying clause requirements.

---

#### `get_qualified_edge_groundings(...)` (1403-1411)
Identical to node version, operates on edges. Calls `is_satisfied_edge()` instead.

---

**Bugs Logged:**
- BUG-138 (HIGH): Broken threshold checking - passes same argument twice
- BUG-139 (MEDIUM): Missing @numba.njit decorator on check_all_clause_satisfaction
- BUG-140 (MEDIUM): No short-circuit evaluation
- BUG-141 (MEDIUM): Undefined variable risk with invalid threshold types
- BUG-142 (LOW): Code duplication in threshold functions

**Key Insights:**
- **BUG-138 is critical**: Threshold checks completely broken, causes massive over-firing of rules
- **Complex edge pattern matching**: `get_rule_edge_clause_grounding` must handle 4 cases based on variable binding order
- **Refinement is sophisticated**: Propagates constraints through dependency graph to eliminate invalid bindings
- **Performance critical**: Called in tight loop during rule grounding (most expensive reasoning phase)
- **Predicate map is key**: Fast O(1) lookup of components with specific predicates

---

#### Call Sites & Integration

All Layer 7A functions are called from `_ground_rule()` [Layer 8, lines 784-1226]:

**`get_rule_node_clause_grounding`:**
- Line ~850: Get initial node bindings for node clauses

**`get_rule_edge_clause_grounding`:**
- Line ~1000: Get edge bindings for edge clauses

**`get_qualified_node_groundings`:**
- Line ~896: Filter nodes by predicate/bound satisfaction
- Line 1312: Used by check_node_grounding_threshold_satisfaction

**`get_qualified_edge_groundings`:**
- Line ~1032: Filter edges by predicate/bound satisfaction
- Line 1327: Used by check_edge_grounding_threshold_satisfaction

**`check_node_grounding_threshold_satisfaction`:**
- Line ~892: Validate threshold for node clauses

**`check_edge_grounding_threshold_satisfaction`:**
- Line ~1029: Validate threshold for edge clauses

**`refine_groundings`:**
- Line 944: After initial grounding, propagate constraints
- Line 1098: After handling special clauses, re-refine

**`check_all_clause_satisfaction`:**
- Line 950: Final validation before rule fires
- Line 1107: Validation after refinement

**Integration Pipeline:**
```
_ground_rule() [Layer 8]
  ↓
For each clause:
  1. Get initial groundings
     - get_rule_node_clause_grounding() or get_rule_edge_clause_grounding()
  2. Filter by satisfaction
     - get_qualified_node_groundings() or get_qualified_edge_groundings()
  3. Check thresholds
     - check_node/edge_grounding_threshold_satisfaction()
  4. Refine through dependency graph
     - refine_groundings()
  5. Final validation
     - check_all_clause_satisfaction()
  
If all pass → Rule fires with these bindings
```

---

#### Rule Grounding Example (Complete Flow)

```
Rule: infected(X) ∧ [available, >=50%] neighbor(X,Y) ∧ age(Y,Z) → infected(Z)

Graph:
  Nodes: Alice, Bob, Carol, Dave, Eve
  Edges: (Alice,Bob), (Alice,Carol), (Bob,Dave), (Carol,Eve)
  
  infected(Alice) = [0.8, 0.9]
  infected(Bob) = [0.6, 0.7]
  infected(Carol) = [0.9, 1.0]

Step 1: Ground infected(X)
  get_rule_node_clause_grounding('X', ..., Label('infected'), ...)
  → Returns predicate_map[infected] = [Alice, Bob, Carol]
  
  get_qualified_node_groundings(..., [Alice,Bob,Carol], infected, [0.7,1.0])
  → Filters to [Alice, Carol]  (Bob's 0.6 < 0.7)
  
  groundings[X] = [Alice, Carol]

Step 2: Ground neighbor(X,Y) with threshold
  get_rule_edge_clause_grounding('X', 'Y', ..., Label('neighbor'), ...)
  → Case 3: X bound, Y unbound
  → For Alice: neighbors[Alice] = [Bob, Carol]
  → For Carol: neighbors[Carol] = [Eve]
  → Returns [(Alice,Bob), (Alice,Carol), (Carol,Eve)]
  
  groundings_edges[(X,Y)] = [(Alice,Bob), (Alice,Carol), (Carol,Eve)]
  groundings[Y] = [Bob, Carol, Eve]
  
  Check threshold: [available, >=50%]
  check_edge_grounding_threshold_satisfaction(...)
    → For X=Alice: has 2 neighbors (Bob, Carol), threshold requires >= 50%
    → For X=Carol: has 1 neighbor (Eve), threshold requires >= 50%
    → Both satisfy (100% >= 50%)

Step 3: Ground age(Y,Z)
  get_rule_edge_clause_grounding('Y', 'Z', ..., Label('age'), ...)
  → Case 3: Y bound to [Bob, Carol, Eve], Z unbound
  → Look up neighbors for each Y...
  → Returns age edges
  
Step 4: Refine groundings
  refine_groundings([X, Y], groundings, groundings_edges, ...)
  → Propagate X constraints to Y through neighbor edges
  → Propagate Y constraints to Z through age edges
  → Remove any invalid combinations

Step 5: Final validation
  check_all_clause_satisfaction(...)
  → Verify all clauses still satisfied after refinement
  
Result: Rule fires for valid (X,Y,Z) combinations
```

---

#### Code Variants
Functions exist in **3 interpretation implementations** (identical):
1. **interpretation.py**
2. **interpretation_fp.py**
3. **interpretation_parallel.py**

Total duplicated code: 184 lines × 3 = 552 lines across project

---

### Layer 7B: Head Variable Determination (Lines 2000-2107)
**Status:** ✅ Complete

**Theoretical Concepts:**
- **Head Functions**: User-defined functions that compute derived entities in rule heads
- **Entity Computation**: Ability to create new entities from existing variable bindings
- **Function Dispatch**: Runtime lookup and invocation of registered head functions
- **Cartesian Product Application**: Functions can operate over multiple variable groundings

**Distinction from Annotation Functions:**
| Aspect | Annotation Functions | Head Functions |
|--------|---------------------|----------------|
| **Purpose** | Compute interval bounds | Compute entities (nodes/edges) |
| **Input** | Clause intervals + weights | Variable groundings |
| **Output** | `(lower, upper)` float tuple | List of node/edge identifiers |
| **When called** | After rule grounding succeeds | During rule grounding (before head is known) |
| **Example** | `max`, `min`, `average` | `identity_func`, `hash`, `concat` |

---

#### Function 1: `_determine_node_head_vars(head_fns, head_fns_vars, groundings, head_functions)` (2000-2037)

| Parameter | Type | Definition |
|-----------|------|------------|
| `head_fns` | `List[str]` | Function names for each head variable. Empty string `''` if no function. For node rules: single-element list. |
| `head_fns_vars` | `List[List[str]]` | Nested list of variable names used as arguments to each function. For node rules: `[[var1, var2, ...]]`. |
| `groundings` | `Dict[str, List[str]]` | Current variable bindings from rule body grounding. |
| `head_functions` | `Tuple[Function]` | Registry of user-registered head functions. |

**Returns:** `Tuple[List[str], bool]` - (head_groundings, is_func)
- `head_groundings`: List of node identifiers for rule head
- `is_func`: True if function was applied, False if using existing grounding

**Logic Flow:**
```
1. Initialize empty head_groundings list
2. Extract first element from head_fns (node rules have only one head variable)
3. Extract corresponding function variables from head_fns_vars[0]
4. If function name is non-empty and has variables:
   a. Create fn_arg_values list
   b. For each function variable:
      - If variable in groundings: add its grounded values
      - Else: treat variable name as literal string (add [variable_name])
   c. Call _call_head_function(fn_name, fn_arg_values, head_functions)
   d. Set is_func = True
   e. Return (head_groundings, is_func)
5. Else: return (empty list, False)
```

**Concrete Example:**

```python
Rule: infected(X) ∧ neighbor(X,Y) → processed(identity_func(Y))
                                     ↑                      ↑
                                  head predicate      head function

After grounding body clauses:
  groundings = {
    'X': [Alice, Carol],
    'Y': [Dave, Eve, Frank]
  }

Input to _determine_node_head_vars:
  head_fns = ['identity_func']  # One function for the single head var
  head_fns_vars = [['Y']]        # Function takes Y as argument
  groundings = {'X': [Alice, Carol], 'Y': [Dave, Eve, Frank]}
  head_functions = (identity_func, hash_func, ...)

Execution:
  Line 2018: fn_name = 'identity_func'
  Line 2019: fn_vars = ['Y']
  Line 2022: fn_name != '' and len(fn_vars) > 0? YES → enter if block

  Line 2025: fn_arg_values = []
  Line 2026-2031: For fn_var = 'Y':
    'Y' in groundings? YES
    fn_arg_values.append([Dave, Eve, Frank])

  Result: fn_arg_values = [[Dave, Eve, Frank]]

  Line 2034: head_groundings = _call_head_function('identity_func',
                                                    [[Dave, Eve, Frank]],
                                                    head_functions)

  identity_func receives: [[Dave, Eve, Frank]]
  identity_func returns: [Dave, Eve, Frank]  # Identity function returns as-is

  Line 2035: is_func = True

Return: ([Dave, Eve, Frank], True)

What happens next in _ground_rule:
  Line 931: groundings['processed'] = [Dave, Eve, Frank]

  Result: Rule will fire 3 times:
    1. processed(Dave) gets new bounds
    2. processed(Eve) gets new bounds
    3. processed(Frank) gets new bounds
```

**Example with Ungrounded Variable:**

```python
Rule: property(X) → new_node(concat(X, 'suffix'))
                              ↑
                    Function uses X (grounded) and literal 'suffix'

After grounding:
  groundings = {'X': [Alice, Bob]}

Input:
  head_fns = ['concat']
  head_fns_vars = [['X', 'suffix']]  # Two arguments
  groundings = {'X': [Alice, Bob]}

Execution:
  fn_vars = ['X', 'suffix']

  For 'X':
    'X' in groundings? YES → append [Alice, Bob]

  For 'suffix':
    'suffix' in groundings? NO → append ['suffix']  # Literal string!

  fn_arg_values = [[Alice, Bob], ['suffix']]

  concat receives: [[Alice, Bob], ['suffix']]
  concat might compute: [Alice_suffix, Bob_suffix]

Return: ([Alice_suffix, Bob_suffix], True)
```

**Missing Decorator Bug:**
Line 2000: Function is NOT decorated with `@numba.njit` (unlike edge version on line 2040).

---

#### Function 2: `_determine_edge_head_vars(head_fns, head_fns_vars, groundings, head_functions)` (2041-2081)

| Parameter | Type | Definition |
|-----------|------|------------|
| Same as node version | Same | Same |

**Returns:** `Tuple[List[List[str]], List[bool]]` - (head_groundings, is_func)
- `head_groundings`: Two-element list `[sources, targets]` where each is a list of node identifiers
- `is_func`: Two-element list `[source_is_func, target_is_func]`

**Key Difference from Node Version:**
- Handles TWO head variables (source and target of edge)
- Loops twice (i=0 for source, i=1 for target)
- Returns nested structure: `[[source_nodes], [target_nodes]]`

**Logic Flow:**
```
1. Initialize head_groundings = [[], []]  # Two empty lists
2. Initialize is_func = [False, False]
3. For i in range(2):  # Process source (0) and target (1)
   a. Extract fn_name and fn_vars for position i
   b. If function exists:
      - Build fn_arg_values from groundings
      - Call _call_head_function
      - Set head_groundings[i] = result
      - Set is_func[i] = True
4. Return (head_groundings, is_func)
```

**Concrete Example:**

```python
Rule: property(A) ∧ property(B) → route(identity_func(A), B)
                                         ↑                ↑
                                    source function    target var

After grounding:
  groundings = {
    'A': [Alice, Bob],
    'B': [Carol, Dave]
  }

Input:
  head_fns = ['identity_func', '']  # Function for source, no function for target
  head_fns_vars = [['A'], []]       # A is arg to function, target has no vars
  groundings = {'A': [Alice, Bob], 'B': [Carol, Dave]}

Execution:
  Line 2055-2056: head_groundings = [[], []]
  Line 2057: is_func = [False, False]

  Iteration i=0 (source):
    Line 2061: fn_name = 'identity_func'
    Line 2062: fn_vars = ['A']
    Line 2065: fn_name != '' and len(fn_vars) > 0? YES

    Build fn_arg_values:
      'A' in groundings? YES → append [Alice, Bob]
    fn_arg_values = [[Alice, Bob]]

    Line 2077: head_grounding = _call_head_function(...)
               → returns [Alice, Bob]
    Line 2078: head_groundings[0] = [Alice, Bob]
    Line 2079: is_func[0] = True

  Iteration i=1 (target):
    Line 2061: fn_name = ''  # Empty string
    Line 2062: fn_vars = []
    Line 2065: fn_name != '' and len(fn_vars) > 0? NO → skip

    head_groundings[1] remains []
    is_func[1] remains False

Return: ([[Alice, Bob], []], [True, False])

What happens next in _ground_rule:
  - Source uses function result: [Alice, Bob]
  - Target uses existing grounding: groundings['B'] = [Carol, Dave]

  Cartesian product:
    (Alice, Carol)
    (Alice, Dave)
    (Bob, Carol)
    (Bob, Dave)

  Result: Rule fires 4 times, one for each edge combination
```

**Has Decorator:**
Line 2040: Correctly decorated with `@numba.njit(cache=True)` ✓

---

#### Function 3: `_call_head_function(fn_name, fn_arg_values, head_functions)` (2085-2107)

| Parameter | Type | Definition |
|-----------|------|------------|
| `fn_name` | `str` | Name of the function to call (e.g., `'identity_func'`) |
| `fn_arg_values` | `List[List[str]]` | Nested list where each element is a list of node identifiers. Structure: `[[arg1_values], [arg2_values], ...]` |
| `head_functions` | `Tuple[Function]` | Registry of all available head functions |

**Returns:** `List[str]` - Flattened list of node identifiers computed by the function

**Logic Flow:**
```
1. Initialize empty func_result list
2. Enter objmode context (escape Numba to call Python functions)
3. Linear search through head_functions tuple:
   a. Check if function has __name__ attribute
   b. Check if func.__name__ == fn_name
   c. If match: call func(fn_arg_values) and break
4. Exit objmode, return func_result
```

**Why objmode?**
- Head functions are user-defined Python functions
- Numba can't JIT-compile arbitrary user code at runtime
- `objmode` allows calling regular Python from within Numba code
- Type annotation `'types.ListType(types.unicode_type)'` ensures correct Numba type on return

**Concrete Example:**

```python
# User registers this function
@numba.njit
def identity_func(annotations):
    """Head function that returns the input node lists as-is."""
    result = numba.typed.List([annotations[0][0]])
    return result

# Registration
pr.add_head_function(identity_func)

# Call from _determine_node_head_vars
Input:
  fn_name = 'identity_func'
  fn_arg_values = [[Dave, Eve, Frank]]
  head_functions = (identity_func, hash_func, concat_func)

Execution:
  Line 2099: func_result = []

  Line 2101: Enter objmode

  Line 2102-2105: Linear search
    Iteration 1: func = identity_func
      hasattr(identity_func, '__name__')? YES
      identity_func.__name__ == 'identity_func'? YES → MATCH
      Line 2104: func_result = identity_func([[Dave, Eve, Frank]])
      Line 2105: break

  Exit objmode

Return: [Dave, Eve, Frank]
```

**Head Function Contract:**

User-defined head functions must follow this interface:
```python
@numba.njit
def my_head_function(arg_values: List[List[str]]) -> List[str]:
    """
    Args:
        arg_values: Nested list where each element is groundings for one variable
                    Example: [[Alice, Bob], [Carol]] means:
                      - First arg variable has groundings [Alice, Bob]
                      - Second arg variable has groundings [Carol]

    Returns:
        Flat list of node identifiers (strings)
        These become the head variable groundings
    """
    # Example: Cartesian product
    result = numba.typed.List.empty_list(numba.types.unicode_type)
    for v1 in arg_values[0]:
        for v2 in arg_values[1]:
            result.append(f"{v1}_{v2}")
    return result
```

---

**Bugs Logged:**

- **BUG-143 (MEDIUM)**: `_determine_node_head_vars` missing `@numba.njit` decorator
  - **Location:** `interpretation.py:2000`
  - **Impact:** Mode switching overhead every time function called for node rules with head functions
  - **Fix:** Add `@numba.njit(cache=True)` decorator to line 2000

- **BUG-144 (HIGH)**: No error handling in `_call_head_function` if function not found
  - **Location:** `interpretation.py:2085-2107`
  - **Impact:** Silent failure - returns empty list if function name doesn't match any registered function. Rule silently won't fire.
  - **Fix:** Raise error or log warning if function not found after search

- **BUG-145 (MEDIUM)**: Linear search through head_functions is O(n)
  - **Location:** `interpretation.py:2102-2105`
  - **Impact:** Inefficient for large function registries. Called once per rule grounding.
  - **Fix:** Use dictionary mapping `fn_name -> function` for O(1) lookup

- **BUG-146 (LOW)**: Ungrounded variables treated as literal strings
  - **Location:** `interpretation.py:2031, 2074`
  - **Impact:** Questionable semantics. If user writes `f(X, Y)` but Y not bound, system passes string 'Y' to function. May cause confusion.
  - **Note:** Might be intentional design to support literal constants, but undocumented

- **BUG-147 (LOW)**: Code duplication between node and edge versions
  - **Location:** Lines 2000-2037 vs 2041-2081
  - **Impact:** 90% identical logic, maintenance burden
  - **Fix:** Extract common logic to shared helper function

---

**Key Insights:**

- **Head functions enable derived entities**: Unlike annotation functions (which compute bounds), head functions compute which entities exist
- **Asymmetric decorator usage**: Edge version has `@numba.njit`, node version doesn't (likely a copy-paste bug)
- **objmode boundary**: Necessary escape hatch to call user Python code from Numba
- **Silent failures possible**: If function name typo, rule won't fire with no error
- **Literal string fallback**: Ungrounded variables become string literals (undocumented feature?)

---

#### Call Sites & Integration

**`_determine_node_head_vars` called from:**
- Line 929: `_ground_rule()` [Layer 8] - For node rules after body grounding

**`_determine_edge_head_vars` called from:**
- Line 1024: `_ground_rule()` [Layer 8] - For edge rules after body grounding

**`_call_head_function` called from:**
- Line 2034: `_determine_node_head_vars()` [Layer 7B]
- Line 2077: `_determine_edge_head_vars()` [Layer 7B]

**Integration Pipeline:**
```
_ground_rule() [Layer 8]
  ↓
Ground all body clauses → groundings = {X: [...], Y: [...]}
  ↓
If rule head has function:
  _determine_node_head_vars() OR _determine_edge_head_vars() [Layer 7B]
    ↓
  _call_head_function() [Layer 7B]
    ↓
  User function executes: my_func(arg_values) → [computed_nodes]
    ↓
  Return to _ground_rule
    ↓
  Update groundings with computed head variable
    ↓
Continue rule application with new head grounding
```

**Example End-to-End:**

```
Rule: infected(X) ∧ neighbor(X,Y) → cluster(hash(X,Y))

Step 1: Ground body clauses
  infected(X) → X = [Alice, Carol]
  neighbor(X,Y) → Y = [Dave, Eve]

Step 2: Call _determine_node_head_vars
  head_fns = ['hash']
  head_fns_vars = [['X', 'Y']]

Step 3: Build function arguments
  fn_arg_values = [[Alice, Carol], [Dave, Eve]]

Step 4: Call _call_head_function('hash', ...)
  Searches head_functions for 'hash'
  Calls: hash([[Alice, Carol], [Dave, Eve]])

Step 5: hash function computes
  Might return: ['cluster_1', 'cluster_2', 'cluster_3', 'cluster_4']
  (One for each X-Y combination)

Step 6: Update groundings
  groundings['cluster'] = ['cluster_1', 'cluster_2', 'cluster_3', 'cluster_4']

Step 7: Apply rule
  cluster(cluster_1) gets new bounds
  cluster(cluster_2) gets new bounds
  ...
```

---

### Layer 8: Rule Grounding - ANALYSIS PLAN
**Status:** 📋 Planning Phase
**Location:** `interpretation.py:784-1226` (444 lines)
**Function:** `_ground_rule(rule, ...)`

---

## Analysis Plan Overview

This is the most complex single function in PyReason. It orchestrates the entire rule grounding process: finding all variable bindings that satisfy a rule's body clauses, then preparing the data structures needed to apply the rule's head.

**Complexity Factors:**
- 444 lines (10x larger than typical function)
- Handles 3 distinct rule types (node, edge, edge-with-infer)
- Processes 4 clause types (node, edge, comparison, binder)
- Manages 7 interconnected data structures
- Contains 2 nested loops with 8+ conditional branches each
- Mixes imperative logic with functional filtering

**Analysis Strategy:**
Break the function into 6 logical sections, analyze each separately, then examine interactions.

---

## Section 1: Initialization & Setup (Lines 784-820)
**Goal:** Understand data structure initialization and rule parameter extraction

**Lines:**
- 784-793: Extract rule parameters from rule object
- 794-798: Unpack head variables based on rule type
- 800-802: Initialize return containers (applicable_rules_node/edge)
- 804-815: Initialize grounding data structures
- 817-820: Create helper sets and satisfaction flag

**Key Questions:**
1. What is the purpose of each data structure?
2. Why use both `groundings` (dict) and `groundings_edges` (dict)?
3. What is the dependency graph used for?
4. Why create `nodes_set` and `edges_set`?

**Analysis Tasks:**
- [ ] Document each data structure's purpose and lifetime
- [ ] Identify any missing initializations
- [ ] Check for type consistency issues
- [ ] Create parameter table with all 14 input parameters

**Expected Bugs:** 0-1 (initialization is typically straightforward)

---

## Section 2: Clause Loop - Node & Edge Clause Processing (Lines 821-901)
**Goal:** Understand how both node and edge clauses are grounded, validated, and how the dependency graph is built

**Lines:**
- 821-828: Loop setup and clause unpacking
- 830-855: Node clause processing branch
- 856-901: Edge clause processing branch (grounding + dependency graph construction)

**Node Clause Logic Flow:**
1. Check if clause variable is ground atom (allow_ground_rules)
2. Get candidate nodes from predicate_map or all nodes
3. Filter candidates by satisfaction (qualified_groundings)
4. Update groundings dict
5. Filter existing edge groundings to maintain consistency
6. Check threshold satisfaction

**Edge Clause Logic Flow:**
1. Get candidate edges (handle ground atom case)
2. Filter by satisfaction
3. Check threshold
4. Extract unique source/target nodes from qualified edges
5. Update groundings_edges dict
6. Update dependency graph (forward and reverse)

**Key Questions:**
1. Why filter edge groundings after updating node groundings (lines 844-848)?
2. What happens if qualified_groundings is empty?
3. Why initialize groundings[var] to empty list then populate (lines 877-887)?
4. How does dependency graph differ from neighbor graph?
5. Why update both forward and reverse dependency graphs?
6. What is the allow_ground_rules feature for?

**Analysis Tasks:**
- [ ] Trace through concrete example: `infected(X)` node clause
- [ ] Trace through concrete example: `neighbor(X,Y)` edge clause
- [ ] Document the edge filtering logic (lines 844-848)
- [ ] Document dependency graph construction logic
- [ ] Verify duplicate prevention in lines 882-887
- [ ] Identify potential KeyError conditions
- [ ] Check for inconsistent state if edge has no valid endpoints

**Expected Bugs:** 5-7 (complex filtering logic, state management, dependency graph)

---

## Section 3: Clause Loop - Comparison & Refinement (Lines 903-914)
**Goal:** Understand comparison clause handling and refinement process

**Lines:**
- 903-905: Comparison clause stub (pass statement)
- 907-910: Refinement call
- 912-914: Early exit on unsatisfied clauses

**Key Questions:**
1. Why is comparison clause empty? Is this dead code or unimplemented feature?
2. Why refine only if satisfaction is true?
3. What does refine_groundings actually do?
4. What state is left behind if we break early?

**Analysis Tasks:**
- [ ] Document comparison clause status (dead code vs TODO)
- [ ] Explain refinement's role in maintaining grounding consistency
- [ ] Identify any cleanup needed for early exit
- [ ] Check if early exit can leave inconsistent state

**Expected Bugs:** 1-2 (unimplemented feature, cleanup issues)

---

## Section 4: Head Processing - Node & Edge Rules (Lines 918-1221)
**Goal:** Understand how both node and edge rule heads are instantiated and prepared for application

**Lines:**
- **Node Rules** (918-1017):
  - 924-941: Head variable determination and ground atom handling
  - 943-953: Loop setup with satisfaction recheck
  - 954-1010: Building qualified nodes/edges and annotations per clause
  - 1012-1017: Add node to graph if needed, append to applicable_rules
- **Edge Rules** (1019-1221):
  - 1019-1058: Head variable determination, ground atom handling, infer_edges setup
  - 1060-1071: Build valid_edge_groundings (Cartesian product or existing edges)
  - 1073-1117: Loop through valid edges, build temp groundings, refine
  - 1107-1110: Recheck satisfaction, continue if false
  - 1112-1117: Handle infer_edges case
  - 1119-1207: Build qualified nodes/edges and annotations per clause
  - 1209-1221: Add nodes/edges to graph if needed, append to applicable_rules

**Node Rule Logic Flow:**
1. Apply head functions if present
2. Handle ground atoms (variables not in body)
3. Loop through each head grounding
4. Recheck satisfaction after refinement
5. For each clause, build qualified_nodes/edges and annotations
6. Add ground nodes to graph if needed
7. Append to applicable_rules_node

**Edge Rule Logic Flow:**
1. Apply head functions for source and target independently
2. Handle ground atoms for both variables
3. Determine if inferring edges or using existing
4. Build valid edge groundings (filtered by infer_edges flag)
5. For each valid edge:
   a. Create temp copies of groundings and groundings_edges
   b. Narrow temp structures to specific head grounding
   c. Refine temp structures
   d. Recheck satisfaction with temp structures
   e. Handle self-loop prevention for infer_edges
   f. Build qualified nodes/edges and annotations
   g. Add ground nodes/edges to graph
   h. Append to applicable_rules_edge

**Key Questions:**
1. Why recheck satisfaction for each head grounding?
2. Why different logic for clause_var == head_var vs not?
3. Why copy groundings to temp_groundings for each edge (line 1082-1083)?
4. Why refine with head_variables instead of clause_variables (line 1103)?
5. What is the purpose of lines 1089-1101 (filtering temp_groundings_edges)?
6. Why check `head_var_1_grounding == head_var_1` when adding to graph (line 1210)?
7. Why prevent self-loops only when `source != target` (line 1114)?

**Analysis Tasks:**
- [ ] Trace concrete example: `infected(X) ∧ neighbor(X,Y) → processed(Y)` (node rule)
- [ ] Trace concrete example without infer_edges: `property(X) ∧ property(Y) ∧ connected(X,Y) → strong_connected(X,Y)`
- [ ] Trace concrete example WITH infer_edges: `infected(X) ∧ neighbor(X,Y) ∧ susceptible(Y) → risk(X,Y)`
- [ ] Document the qualified_nodes/edges structures
- [ ] Document the annotations structure
- [ ] Document temp_groundings purpose and lifetime
- [ ] Document all 7 filtering branches in lines 1089-1101
- [ ] Verify self-loop prevention logic
- [ ] Compare node vs edge processing to find duplication
- [ ] Check for consistent handling of atom_trace and ann_fn flags

**Expected Bugs:** 8-13 (extreme complexity, many edge cases, temp state management, duplication)

---

## Section 5: Cross-Cutting Analysis
**Goal:** Identify bugs arising from interactions between sections

**Analysis Tasks:**
- [ ] Compare node vs edge rule processing for inconsistencies
- [ ] Verify data structure invariants maintained throughout function
- [ ] Check for resource leaks (temp structures not cleaned up)
- [ ] Identify duplicate code between node and edge branches
- [ ] Verify early exit paths leave consistent state
- [ ] Check for missing error handling

**Expected Bugs:** 2-4 (interaction bugs, inconsistencies)

---

## Analysis Execution Order

**Phase 1: Foundation (Sections 1-2)**
→ Understand data structures and clause processing (both node and edge)
→ Build concrete examples for node and edge clauses

**Phase 2: Refinement (Section 3)**
→ Understand how groundings are refined after each clause
→ Document comparison clause status

**Phase 3: Head Processing (Section 4)**
→ Trace node and edge rule head instantiation
→ Compare infer_edges vs existing edges for edge rules

**Phase 4: Integration (Section 5)**
→ Look for interaction bugs
→ Summarize findings

---

## Concrete Examples to Build

**Example 1: Simple Node Rule**
```
Rule: infected(X) → quarantine(X)
Graph: infected(Alice)=[0.8,0.9], infected(Bob)=[0.6,0.7]
Trace through: Section 1 → Section 2 (node clause) → Section 3 → Section 4 (node rule)
```

**Example 2: Node Rule with Edge Clause**
```
Rule: infected(X) ∧ neighbor(X,Y) → risk(Y)
Graph: infected(Alice)=[0.9,1.0], edges: (Alice,Bob), (Alice,Carol)
Trace through: Sections 1-4 (node rule path)
```

**Example 3: Edge Rule WITHOUT infer_edges**
```
Rule: property(X) ∧ property(Y) ∧ connected(X,Y) → strong_connected(X,Y)
Graph: All predicates exist, edge (Alice,Bob) exists
Trace through: Sections 1-4 (edge rule, infer_edges=False path)
```

**Example 4: Edge Rule WITH infer_edges**
```
Rule: infected(X) ∧ neighbor(X,Y) ∧ susceptible(Y) → risk(X,Y) [infer_edges]
Graph: Predicates exist, but risk edges don't exist yet
Trace through: Sections 1-4 (edge rule, infer_edges=True path)
```

---

## Summary Statistics

**Total Expected Bugs:** 16-27
- Initialization: 0-1
- Node & edge clause processing: 5-7
- Comparison & refinement: 1-2
- Node & edge rule heads: 8-13
- Cross-cutting: 2-4

**Lines of Code:** 444 (21% of entire interpretation.py file)

**Cyclomatic Complexity:** ~40-50 (extremely high)

**Code Duplication:** High (node vs edge branches, qualified nodes/edges building)

---

## Next Steps

Proceed through each section sequentially:
1. Read section code
2. Build concrete examples
3. Document logic flow
4. Identify bugs
5. Log bugs to BUG_LOG_2.md
6. Mark section complete
7. Request user input before proceeding to next section

---
