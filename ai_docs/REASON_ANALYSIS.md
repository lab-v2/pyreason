# reason() Function Analysis

**Source File:** `pyreason/scripts/interpretation/interpretation.py`
**Location:** Lines 228-660 (434 lines)
**Complexity:** Very High (Orchestration function with nested loops and parallel execution)

---

## Function Overview

The `reason()` function is the **main orchestration engine** of PyReason. It implements the complete temporal reasoning loop that iteratively applies facts and rules until convergence or maximum timesteps are reached.

**Purpose:** Execute forward-chaining logic programming with temporal semantics:
1. Iterate through timesteps (t=0 to tmax)
2. Apply scheduled facts at each timestep
3. Ground all rules to find applicable instances
4. Apply rules and derive new facts
5. Repeat until fixed-point convergence or timeout

**Theoretical Foundation:**
- **Temporal Logic:** Reasoning evolves across discrete timesteps
- **Fixed-Point Semantics:** Iterate rule application until no more changes
- **Forward Chaining:** Apply all matching rules, derive consequences, repeat
- **Stratified Negation:** Immediate rules (delta_t=0) handled in inner loop
- **Non-monotonic Reasoning:** Supports both persistent and non-persistent modes

---

## Function Returns

**Return Type:** `Tuple[int, int]`

```python
return (t, fp_cnt)
```

**Components:**
1. **`t`** (int): Final timestep reached
   - If converged: timestep at which convergence detected + 1
   - If not converged: tmax + 1
   - Used for resumption: next call starts from this timestep

2. **`fp_cnt`** (int): Total fixed-point iterations performed
   - Counts how many times the inner rule application loop executed
   - Measure of reasoning effort (more iterations = more complex inference)

**Example:**
```python
# Run reasoning for 10 timesteps
t_final, fp_final = reason(..., tmax=10, ...)

# Result: (11, 47) means:
# - Reached timestep 11 (ran all 10 timesteps)
# - Performed 47 fixed-point iterations total
```

---

## Global State Modified

Unlike `_ground_rule()` which only reads state, **`reason()` modifies most of PyReason's state**:

### Primary Modifications (Updated by _update_node/_update_edge):

**1. `interpretations_node` and `interpretations_edge`**
- **Type:** `Dict[component, World]`
- **Modified:** Lines 302, 316, 431, 444, 478, 491, 505, 518
- **Purpose:** Core reasoning state - truth values for all predicates
- **Changes:** Intervals updated when facts/rules fire

**2. `rule_trace_node` and `rule_trace_edge`**
- **Type:** `List[Tuple[t, fp_cnt, component, label, interval]]`
- **Modified:** Lines 284, 289, 293 (facts), provenance in _update_node/_update_edge
- **Purpose:** Complete history of all interpretation changes
- **Changes:** Appended with (timestep, fp_count, entity, predicate, new_bound) on each update

**3. `rule_trace_node_atoms` and `rule_trace_edge_atoms`**
- **Type:** `List[Tuple[qualified_nodes, qualified_edges, bound, rule_name]]`
- **Modified:** Lines 286, 290, 294 (atom trace updates)
- **Purpose:** Detailed provenance showing which entities satisfied each clause
- **Changes:** Appended when atom_trace=True

**4. `predicate_map_node` and `predicate_map_edge`**
- **Type:** `Dict[Label, List[component]]`
- **Modified:** Indirectly via _update_node/_update_edge
- **Purpose:** Reverse index: predicate → entities that have it
- **Changes:** Updated when new predicates added to interpretations

**5. `num_ga` (Ground Atoms Count)**
- **Type:** `List[int]` (one entry per timestep)
- **Modified:** Line 658 (each timestep), indirectly in _update_node/_update_edge
- **Purpose:** Track total number of ground atoms (labeled entities) over time
- **Changes:** Appended with count at each timestep

### Graph Structure Modifications:

**6. `nodes` and `edges`**
- **Type:** `List[str]` and `List[Tuple[str, str]]`
- **Modified:** Lines 276 (node facts), 353 (edge facts), 468 (inferred edges)
- **Purpose:** Graph topology
- **Changes:** New nodes/edges added when facts reference missing entities or rules infer edges

**7. `neighbors` and `reverse_neighbors`**
- **Type:** `Dict[str, List[str]]`
- **Modified:** Same locations as nodes/edges (via _add_node, _add_edge, _add_edges)
- **Purpose:** Adjacency lists for efficient graph traversal
- **Changes:** Updated when edges added

### Scheduling State Modifications:

**8. `facts_to_be_applied_node` and `facts_to_be_applied_edge`**
- **Type:** `List[Tuple[time, comp, label, bound, static, graph_attribute]]`
- **Modified:** Lines 337, 411 (replace with unprocessed facts)
- **Purpose:** Queue of pending facts scheduled for future timesteps
- **Changes:** Consumed as facts applied, replenished with static facts

**9. `rules_to_be_applied_node` and `rules_to_be_applied_edge`**
- **Type:** `List[Tuple[time, comp, label, bound, static]]`
- **Modified:** Lines 457, 531 (remove applied), 608, 610 (add newly grounded)
- **Purpose:** Queue of pending rule instances
- **Changes:** Applied rules removed, newly grounded rules added

**10. `edges_to_be_added_node_rule` and `edges_to_be_added_edge_rule`**
- **Type:** `List[Tuple[sources, targets, label]]`
- **Modified:** Lines 458, 532 (remove applied), 617 (add newly grounded)
- **Purpose:** Edges to create for infer_edges rules
- **Changes:** Applied edges removed, new edges from grounding added

**11. Trace structures** (if atom_trace=True):
- `facts_to_be_applied_node_trace`, `facts_to_be_applied_edge_trace`
- `rules_to_be_applied_node_trace`, `rules_to_be_applied_edge_trace`
- **Modified:** Synchronized with main scheduling lists
- **Purpose:** Provenance for scheduled items

---
## Function Signature & Parameters (33 total)

```python
def reason(
    interpretations_node, interpretations_edge, predicate_map_node, predicate_map_edge,
    tmax, prev_reasoning_data, rules, nodes, edges, neighbors, reverse_neighbors,
    rules_to_be_applied_node, rules_to_be_applied_edge, edges_to_be_added_node_rule,
    edges_to_be_added_edge_rule, rules_to_be_applied_node_trace, rules_to_be_applied_edge_trace,
    facts_to_be_applied_node, facts_to_be_applied_edge, facts_to_be_applied_node_trace,
    facts_to_be_applied_edge_trace, ipl, rule_trace_node, rule_trace_edge,
    rule_trace_node_atoms, rule_trace_edge_atoms, reverse_graph, atom_trace,
    save_graph_attributes_to_rule_trace, persistent, inconsistency_check,
    store_interpretation_changes, update_mode, allow_ground_rules, max_facts_time,
    annotation_functions, head_functions, convergence_mode, convergence_delta,
    num_ga, verbose, again
):
```

**Parameter Count:** 33 (most in entire PyReason codebase)

---

### Parameter Table

| Parameter | Type | Definition |
|-----------|------|------------|
| **State: Core Reasoning** | | |
| `interpretations_node` | `Dict[str, World]` | Node interpretations mapping (node → World with predicate intervals) |
| `interpretations_edge` | `Dict[Tuple[str,str], World]` | Edge interpretations mapping (edge → World with predicate intervals) |
| `predicate_map_node` | `Dict[Label, List[str]]` | Reverse index: predicate → nodes that have it (for efficient lookup) |
| `predicate_map_edge` | `Dict[Label, List[Tuple]]` | Reverse index: predicate → edges that have it |
| **Temporal Control** | | |
| `tmax` | `int` | Maximum timesteps to execute (-1 for infinite, run until convergence) |
| `prev_reasoning_data` | `Tuple[int, int]` | Previous state: (start_timestep, start_fp_count) for resumption |
| **Rules** | | |
| `rules` | `List[Rule]` | All rules to apply during reasoning |
| **Graph Structure** | | |
| `nodes` | `List[str]` | All node identifiers in graph |
| `edges` | `List[Tuple[str,str]]` | All edges in graph as (source, target) tuples |
| `neighbors` | `Dict[str, List[str]]` | Forward adjacency: node → list of successors |
| `reverse_neighbors` | `Dict[str, List[str]]` | Backward adjacency: node → list of predecessors |
| **Scheduling: Rule Instances** | | |
| `rules_to_be_applied_node` | `List[Tuple]` | Queue of pending node rule instances: (time, node, label, bound, static) |
| `rules_to_be_applied_edge` | `List[Tuple]` | Queue of pending edge rule instances: (time, edge, label, bound, static) |
| `edges_to_be_added_node_rule` | `List[Tuple]` | Edges to create for node rules: (sources, targets, label) |
| `edges_to_be_added_edge_rule` | `List[Tuple]` | Edges to create for edge rules: (sources, targets, label) |
| `rules_to_be_applied_node_trace` | `List[Tuple]` | Provenance for scheduled node rules: (qualified_nodes, qualified_edges, rule_name) |
| `rules_to_be_applied_edge_trace` | `List[Tuple]` | Provenance for scheduled edge rules: (qualified_nodes, qualified_edges, rule_name) |
| **Scheduling: Facts** | | |
| `facts_to_be_applied_node` | `List[Tuple]` | Queue of pending node facts: (time, node, label, bound, static, graph_attribute) |
| `facts_to_be_applied_edge` | `List[Tuple]` | Queue of pending edge facts: (time, edge, label, bound, static, graph_attribute) |
| `facts_to_be_applied_node_trace` | `List[str]` | Provenance for node facts: name of fact source |
| `facts_to_be_applied_edge_trace` | `List[str]` | Provenance for edge facts: name of fact source |
| **Constraints** | | |
| `ipl` | `List[Tuple[Label, Label]]` | Inconsistent Predicate List: pairs of mutually exclusive predicates |
| **Provenance: Traces** | | |
| `rule_trace_node` | `List[Tuple]` | Complete history of node interpretation updates: (t, fp_cnt, node, label, bound) |
| `rule_trace_edge` | `List[Tuple]` | Complete history of edge interpretation updates: (t, fp_cnt, edge, label, bound) |
| `rule_trace_node_atoms` | `List[Tuple]` | Detailed node provenance: (qualified_nodes, qualified_edges, bound, rule_name) |
| `rule_trace_edge_atoms` | `List[Tuple]` | Detailed edge provenance: (qualified_nodes, qualified_edges, bound, rule_name) |
| **Configuration: Graph** | | |
| `reverse_graph` | `bool` | Whether reverse_neighbors is populated (enables backward edge traversal) |
| **Configuration: Provenance** | | |
| `atom_trace` | `bool` | Whether to record detailed atom-level provenance (qualified nodes/edges) |
| `save_graph_attributes_to_rule_trace` | `bool` | Whether to include initial graph facts in trace (vs only inferred facts) |
| **Configuration: Reasoning Semantics** | | |
| `persistent` | `bool` | True: monotonic (facts persist), False: non-monotonic (facts reset each timestep) |
| `inconsistency_check` | `bool` | True: resolve conflicting facts, False: override with newest fact |
| `store_interpretation_changes` | `bool` | Whether to record changes to traces (performance vs provenance tradeoff) |
| `update_mode` | `str` | 'override' (replace intervals) or 'intersection' (take minimum intersection) |
| `allow_ground_rules` | `bool` | Whether to permit rules with ground atoms (literal node/edge names as variables) |
| **Configuration: Temporal** | | |
| `max_facts_time` | `int` | Latest timestep with scheduled facts (for perfect_convergence detection) |
| **Configuration: Functions** | | |
| `annotation_functions` | `Tuple[Function]` | Registry of interval aggregation functions (max, min, avg, custom) |
| `head_functions` | `Tuple[Function]` | Registry of entity computation functions for rule heads |
| **Configuration: Convergence** | | |
| `convergence_mode` | `str` | 'delta_interpretation', 'delta_bound', 'perfect_convergence', or 'naive' |
| `convergence_delta` | `float` | Threshold for delta_interpretation/delta_bound modes |
| **Metrics** | | |
| `num_ga` | `List[int]` | Ground atoms per timestep (updated during reasoning) |
| **Debug** | | |
| `verbose` | `bool` | Whether to print timestep progress to console |
| `again` | `bool` | Resumption flag (allows rules to fire past tmax when resuming) |

**Returns:** `Tuple[int, int]` - (final_timestep, total_fp_iterations)


## High-Level Control Flow

```
reason():
    Initialize: t, fp_cnt, max_rules_time

    while timestep_loop (t < tmax):
        Print timestep (if verbose)

        # RESET (non-persistent mode)
        if not persistent and t > 0:
            Reset all non-static interpretations to [0,1]

        # FACT APPLICATION
        Apply node facts scheduled for time t
        Apply edge facts scheduled for time t

        # RULE APPLICATION & GROUNDING
        in_loop = True
        while in_loop:  # Inner fixed-point loop
            in_loop = False

            # Apply pending rules scheduled for time t
            Apply pending node rules
            Apply pending edge rules

            # If updates occurred, ground all rules again
            if update:
                fp_cnt += 1

                # PARALLEL GROUNDING
                for each rule (in parallel):
                    Ground rule → get applicable instances
                    Schedule instances for time t+delta_t
                    If delta_t == 0: set in_loop = True

        # CONVERGENCE CHECK
        if convergence detected:
            break

        t += 1

    return (t, fp_cnt)
```

---

## Execution Example: Simple Case

```python
# Setup
Graph:
  infected(Alice) = [0.9, 1.0]
  neighbor edges: (Alice, Bob), (Alice, Carol)

Rules:
  Rule 1: infected(X) → quarantine(X) [delta_t=0, immediate]
  Rule 2: infected(X) ∧ neighbor(X,Y) → risk(Y) [delta_t=1, delayed]

Facts:
  infected(Alice) = [0.9, 1.0] at t=0

# Execution Trace

t=0:
  Fact Application:
    - infected(Alice) = [0.9, 1.0] applied

  Rule Grounding (fp_cnt=0):
    - Rule 1 grounds: X = [Alice]
      → Schedule quarantine(Alice) for t=0 (delta_t=0)
    - Rule 2 grounds: X = [Alice], Y = [Bob, Carol]
      → Schedule risk(Bob) for t=1 (delta_t=1)
      → Schedule risk(Carol) for t=1 (delta_t=1)

  Inner Loop (delta_t=0 rules):
    - Apply quarantine(Alice) = [annotation result]
    - in_loop = True (delta_t=0 rule applied)
    - Re-ground all rules (fp_cnt=1):
      → Rule 1: Already has quarantine(Alice), no new instances
      → Rule 2: No change
    - in_loop = False (no new rules)

  Convergence Check: No convergence, continue

t=1:
  Fact Application: None

  Rule Application:
    - Apply risk(Bob) = [annotation result]
    - Apply risk(Carol) = [annotation result]

  Rule Grounding (fp_cnt=2):
    - Rule 1: infected(X) → quarantine(X)
      → X = [Alice] (only Alice is infected)
      → No new instances (Alice already has quarantine from t=0)
    - Rule 2: infected(X) ∧ neighbor(X,Y) → risk(Y)
      → X = [Alice], Y = [Bob, Carol]
      → No new instances (risk already applied to Bob and Carol)
    - No updates occurred, fixed-point reached

  Convergence Check:
    - No changes detected (fp_cnt=2 produced no new rule instances)
    - Converge at t=1

Final Result:
  interpretations_node = {
    'Alice': World(infected=[0.9,1.0], quarantine=[...]),
    'Bob': World(risk=[...]),
    'Carol': World(risk=[...])
  }

  return (2, 2)  # Converged at t=1, incremented to t=2; 2 fp iterations total
```

---

## Example: Non-Persistent Mode (Temporal Reset)

```python
# Configuration: persistent=False

t=0:
  Apply facts: infected(Alice) = [0.9, 1.0]
  Ground rules: quarantine(Alice) = [1.0, 1.0]
  State: infected(Alice)=[0.9,1.0], quarantine(Alice)=[1.0,1.0]

t=1:
  RESET (non-persistent):
    - infected(Alice).reset() → [0, 1] (if not static)
    - quarantine(Alice).reset() → [0, 1] (if not static)

  Apply facts: (none scheduled)
  Ground rules: Nothing satisfies infected(X) threshold anymore

  State: infected(Alice)=[0,1], quarantine(Alice)=[0,1]

Result: Facts don't persist across timesteps (temporal logic mode)
```

**Use Case:** Modeling time-varying phenomena where facts expire

---

## Example: Parallel Rule Grounding

```python
# 3 Rules in parallel (prange)

Rules:
  Rule 0: infected(X) → risk(X)
  Rule 1: risk(X) → quarantine(X)
  Rule 2: quarantine(X) ∧ neighbor(X,Y) → isolate(Y)

Parallel Execution (lines 555-603):
  Thread 0: Ground Rule 0 → adds to rules_to_be_applied_node_threadsafe[0]
  Thread 1: Ground Rule 1 → adds to rules_to_be_applied_node_threadsafe[1]
  Thread 2: Ground Rule 2 → adds to rules_to_be_applied_node_threadsafe[2]

Merge (lines 605-618):
  Combine all threadsafe lists into main lists
  rules_to_be_applied_node.extend(threadsafe[0])
  rules_to_be_applied_node.extend(threadsafe[1])
  rules_to_be_applied_node.extend(threadsafe[2])

Flag Merge (lines 619-626):
  in_loop = any(in_loop_threadsafe)     # OR: if ANY rule needs immediate application
  update = all(update_threadsafe)        # AND: if ALL rules had no updates (?)
```

**Note:** Flag merge logic at lines 619-626 is suspicious and will be analyzed in Section 6.

---

## Section-by-Section Analysis Plan

We will analyze `reason()` in 7 sections:

1. **Initialization & Setup** (Lines 228-239)
2. **Timestep Loop & Non-Persistent Reset** (Lines 239-265)
3. **Node Fact Application** (Lines 267-342)
4. **Edge Fact Application** (Lines 343-415)
5. **Rule Application Loop** (Lines 417-535)
6. **Rule Grounding & Scheduling** (Lines 536-627)
7. **Convergence Checking** (Lines 628-658)

Each section will include:
- Code walkthrough
- Logic flow diagrams
- Concrete examples
- Bug identification and logging

---

## Expected Bug Count

**Total Expected:** 15-25 bugs

**High-Risk Areas:**
1. Parallel rule grounding (Section 6) - race conditions, flag merging
2. Edge rule application (Section 5) - complex edge_l branching
3. Fact scheduling (Sections 3-4) - temporal logic, rescheduling
4. Mode interactions - combinatorial explosion of behaviors

---


---

## Section 1: Initialization & Setup (Lines 228-238)

**Purpose:** Extract resumption state and initialize temporary data structures for the reasoning loop.

---

### Code Walkthrough

**Line 229-230: Extract Resumption State**
```python
t = prev_reasoning_data[0]
fp_cnt = prev_reasoning_data[1]
```

**Purpose:** Enable reasoning to resume from a previous session.

**`prev_reasoning_data` Structure:**
- **Type:** `Tuple[int, int]`
- **Contents:** `(start_timestep, start_fp_count)`
- **Use Cases:**
  - **First run:** `(0, 0)` - start from t=0, fp_cnt=0
  - **Resumption:** `(5, 23)` - resume from t=5, continue from fp_cnt=23

**Example:**
```python
# Initial reasoning run
result = reason(..., prev_reasoning_data=(0, 0), tmax=10, ...)
# Returns: (11, 47) - reached t=11, did 47 fp iterations

# Resume reasoning from where we left off
result2 = reason(..., prev_reasoning_data=(11, 47), tmax=20, ...)
# Continues from t=11, fp_cnt starts at 47
```

---

**Line 231: Initialize Maximum Rule Time Tracker**
```python
max_rules_time = 0
```

**Purpose:** Track the latest timestep at which any rule is scheduled to fire.

**Updated:** Line 573 (node rules), Line 592 (edge rules)
```python
max_rules_time = max(max_rules_time, t + delta_t)
```

**Used:** Line 649 (perfect_convergence mode)
```python
if t >= max_facts_time and t >= max_rules_time:
    # No more facts or rules scheduled → converged
```

**Why Track This?**
- `perfect_convergence` mode needs to know if there's any future work scheduled
- If `t >= max_rules_time` AND `t >= max_facts_time`, nothing will fire in future → safe to terminate

---

**Line 232: Initialize Timestep Loop Flag**
```python
timestep_loop = True
```

**Purpose:** Control outer timestep loop (while timestep_loop).

**Set to False:** Line 241 when `t == tmax`
```python
if t == tmax:
    timestep_loop = False  # Exit after this iteration
```

**Why Use a Flag Instead of `while t < tmax`?**

Looking at line 239-241:
```python
while timestep_loop:
    if t == tmax:
        timestep_loop = False
```

This allows the loop to execute the final timestep (t=tmax) before exiting. If we used `while t < tmax`, timestep tmax would never execute.

**Execution with tmax=2:**
- Iteration 1: t=0, timestep_loop=True → execute t=0
- Iteration 2: t=1, timestep_loop=True → execute t=1
- Iteration 3: t=2, set timestep_loop=False → execute t=2, then exit

---

**Lines 233-236: Initialize Temporary Fact Lists**
```python
facts_to_be_applied_node_new = numba.typed.List.empty_list(facts_to_be_applied_node_type)
facts_to_be_applied_edge_new = numba.typed.List.empty_list(facts_to_be_applied_edge_type)
facts_to_be_applied_node_trace_new = numba.typed.List.empty_list(numba.types.string)
facts_to_be_applied_edge_trace_new = numba.typed.List.empty_list(numba.types.string)
```

**Purpose:** Temporary storage for facts that haven't been applied yet (scheduled for future timesteps).

**Why Separate `*_new` Lists?**

The algorithm processes `facts_to_be_applied_node` but some facts are scheduled for `t > current_t`:
```python
# Pseudocode from Section 3 (lines 271-337)
for fact in facts_to_be_applied_node:
    if fact.time == t:
        Apply fact now
        if static:
            Reschedule for t+1 (add to *_new)
    else:
        Add to *_new (apply later)

# After loop, replace main list with *_new
facts_to_be_applied_node = facts_to_be_applied_node_new.copy()
```

**Without `*_new` lists:** Can't modify `facts_to_be_applied_node` while iterating through it.

**With `*_new` lists:** Iterate through old list, accumulate unprocessed facts in new list, swap at end.

**Memory Overhead:** 4 additional lists, cleared and rebuilt each timestep.

---

**Lines 237-238: Initialize Rule Removal Set**
```python
rules_to_remove_idx = set()
rules_to_remove_idx.add(-1)
```

**Purpose:** Track which rule instances have been applied and should be removed from pending lists.

**Why Use a Set?**
- Fast O(1) membership testing: `if i not in rules_to_remove_idx`
- Used in list comprehension to filter out applied rules

**Why Initialize with `-1`?**

Looking at usage in line 457:
```python
rules_to_be_applied_node[:] = numba.typed.List([
    rules_to_be_applied_node[i] 
    for i in range(len(rules_to_be_applied_node)) 
    if i not in rules_to_remove_idx
])
```

The set is used for membership testing. Adding `-1` ensures the set is never empty, which might avoid some edge case or Numba typing issue.

**🐛 Potential Issue:** Is `-1` ever a valid index? No, since indices are `range(len(list))` which starts at 0. So `-1` is a harmless sentinel.

**Cleared:** Line 424 (node rules), Line 463 (edge rules)
```python
rules_to_remove_idx.clear()
```

**Populated:** Line 454 (node rules), Line 523 (edge rules)
```python
rules_to_remove_idx.add(idx)
```

---

### Initialization Pattern

This section follows a **minimal initialization** pattern:
1. Extract resumption state (t, fp_cnt)
2. Initialize tracking variables (max_rules_time, timestep_loop)
3. Create temporary data structures (facts_*_new, rules_to_remove_idx)
4. Begin main loop

**No bugs identified** in this section - initialization is straightforward and correct.

---



## Section 2: Timestep Loop & Non-Persistent Reset (Lines 239-265)

**Purpose:** Control timestep iteration and implement non-persistent (temporal) reasoning semantics.

---

### Code Walkthrough

**Lines 239-241: Timestep Loop Control**
```python
while timestep_loop:
    if t == tmax:
        timestep_loop = False
```

**Logic:** 
- Loop continues while `timestep_loop=True`
- When `t` reaches `tmax`, flag is set to `False`
- Current iteration completes, then loop exits

---

**Lines 246-259: Non-Persistent Reset**
```python
if t > 0 and not persistent:
    # Reset nodes (only if not static)
    for n in nodes:
        w = interpretations_node[n].world
        for l in w:
            if not w[l].is_static():
                w[l].reset()
    
    # Reset edges (only if not static)
    for e in edges:
        w = interpretations_edge[e].world
        for l in w:
            if not w[l].is_static():
                w[l].reset()
```

**Condition:** `t > 0 and not persistent`

**Why `t > 0`?**
- You would only reset after they have already been set at t=0.

**Why `not persistent`?**
- `persistent=True`: Monotonic reasoning (facts accumulate)
- `persistent=False`: Non-monotonic reasoning (facts reset each timestep)

**Reset Logic:**
1. Iterate through ALL nodes
2. For each node, iterate through ALL predicates in its world
3. If predicate is not static, call `reset()` (sets bound to [0, 1])
4. Repeat for edges

**What is `reset()`?**
Looking at the World/Bound implementation, `reset()` sets the interval back to [0, 1] (totally uncertain).

**Static Bounds:**
Static bounds (set via `static=True` in facts/rules) are NOT reset. They persist across timesteps regardless of `persistent` mode.

---

**Lines 261-264: Initialize Convergence Tracking**
```python
changes_cnt = 0
bound_delta = 0
update = False
```

**Purpose:** Track changes during this timestep to detect convergence.

**Variables:**
- `changes_cnt`: Number of interpretation changes (for `delta_interpretation` mode)
- `bound_delta`: Maximum bound change (for `delta_bound` mode)
- `update`: Whether any updates occurred (controls fixed-point loop)
---

### Key Observations

**1. Reset Happens BEFORE Fact Application**
The order is critical:
```
Reset interpretations (if non-persistent)
↓
Apply facts for current timestep
↓
Apply rules for current timestep
```

If reset happened AFTER facts, newly applied facts would be immediately erased.

**2. Static Bounds Persist Regardless of Mode**
Static bounds are never reset, acting as "permanent knowledge" even in non-persistent mode.

---

## Section 3: Node Fact Application (Lines 267-342)

**Purpose:** Apply all node facts scheduled for the current timestep, updating interpretations and handling consistency.

**Lines Covered:**
- 268-270: Clear temporary lists, create nodes_set
- 271-334: Main fact application loop
- 337-341: Update fact lists with unprocessed facts

---

### Code Structure

```python
# Lines 268-270: Setup
facts_to_be_applied_node_new.clear()
facts_to_be_applied_node_trace_new.clear()
nodes_set = set(nodes)

# Lines 271-334: Process each scheduled node fact
for i in range(len(facts_to_be_applied_node)):
    if facts_to_be_applied_node[i][0] == t:  # Time matches
        comp, l, bnd, static, graph_attribute = [extract tuple components]

        # Add node if missing
        if comp not in nodes_set:
            _add_node(...)

        # BRANCH 1: Bound already exists and is static
        if l in interpretations_node[comp].world and interpretations_node[comp].world[l].is_static():
            # Record in trace (skip _update_node)
            # Record IPL complements

        # BRANCH 2: Bound is non-static or doesn't exist
        else:
            if check_consistent_node(...):
                _update_node(...)  # Consistent: update normally
            else:
                # Inconsistent: resolve or override
                if inconsistency_check:
                    resolve_inconsistency_node(...)
                else:
                    _update_node(..., override=True)

        # Reschedule static facts for next timestep
        if static:
            facts_to_be_applied_node_new.append((t+1, comp, l, bnd, static, graph_attribute))

    else:  # Time doesn't match: keep for later
        facts_to_be_applied_node_new.append(facts_to_be_applied_node[i])

# Lines 337-341: Replace fact list with unprocessed facts
facts_to_be_applied_node[:] = facts_to_be_applied_node_new.copy()
```

---

### Execution Flow

```
For each fact in facts_to_be_applied_node:
    ├─ Time == t?
    │   ├─ NO → Keep in queue (lines 331-334)
    │   └─ YES → Process fact (lines 273-328)
    │       ├─ Add node to graph if missing (lines 275-277)
    │       ├─ Is bound static in interpretations? (line 280)
    │       │   ├─ YES → Record trace, skip update (lines 283-295)
    │       │   └─ NO → Check consistency (line 299)
    │       │       ├─ Consistent → _update_node (line 302)
    │       │       └─ Inconsistent (lines 311-323)
    │       │           ├─ inconsistency_check=True → resolve_inconsistency_node (line 314)
    │       │           └─ inconsistency_check=False → _update_node with override=True (line 316)
    │       └─ If static: reschedule for t+1 (lines 325-328)
    └─ Update facts_to_be_applied_node with unprocessed (line 337)
```

---

### Key Logic: Fact Rescheduling

**Lines 325-328:** Static facts are rescheduled for `t+1`:

```python
if static:
    facts_to_be_applied_node_new.append((t+1, comp, l, bnd, static, graph_attribute))
```

**Purpose:** Ensure static facts persist across all timesteps.

**Behavior:**
- Static fact applied at t=0 → rescheduled for t=1
- Applied at t=1 → rescheduled for t=2
- Continues until tmax reached

**Interaction with persistent mode:**
- **persistent=True:** Static facts ensure knowledge persists (redundant with persistent mode)
- **persistent=False:** Static facts persist despite reset (override non-persistent semantics)

---

### Key Logic: IPL Complement Recording

**Lines 287-295:** When static fact applied, record IPL complements:

```python
for p1, p2 in ipl:
    if p1 == l:
        rule_trace_node.append((t, fp_cnt, comp, p2, interpretations_node[comp].world[p2]))
    elif p2 == l:
        rule_trace_node.append((t, fp_cnt, comp, p1, interpretations_node[comp].world[p1]))
```

**Purpose:** Record constraint enforcement. If `ipl = [('healthy', 'infected')]`:
- When `infected(Alice) = [1, 1]` applied
- Record current value of `healthy(Alice)` in trace
- Shows that IPL constraint enforced (healthy and infected are mutually exclusive)

**Question:** Why only for static facts? Why not for non-static facts?

**Answer:** Non-static facts call `_update_node()`, which internally handles IPL updates. Static facts skip `_update_node()`, so IPL recording must happen manually.

---

### Convergence Tracking

**Lines 306-309, 320-323:** Update convergence parameters after `_update_node()`:

```python
if convergence_mode == 'delta_bound':
    bound_delta = max(bound_delta, changes)
else:
    changes_cnt += changes
```

**Two convergence modes:**
1. **delta_bound:** Track maximum bound change magnitude
2. **delta_interpretation:** Track total number of interpretation changes

**Purpose:** Detect when reasoning has reached fixed-point (no more changes).

---

### Key Observations

**1. Static Facts Create Permanent Knowledge**
Static facts:
- Are never overridden by new facts
- Persist across timesteps even in non-persistent mode
- Are rescheduled indefinitely

**2. Two Consistency Strategies**
- **inconsistency_check=True:** Attempt resolution (may fail/error)
- **inconsistency_check=False:** Override with newest fact (last-wins)

**3. Trace Recording Differs for Static vs Non-Static**
- **Static:** Manual trace recording (lines 284-295)
- **Non-static:** Trace recording handled by `_update_node()`

**4. graph_attribute Flag Controls Trace Inclusion**
When `save_graph_attributes_to_rule_trace=False` and `graph_attribute=True`:
- Skip trace recording (line 283)
- Purpose: Separate initial graph facts from inferred facts in provenance

---

## Section 4: Edge Fact Application (Lines 343-415)

**Purpose:** Apply all edge facts scheduled for the current timestep, updating edge interpretations and handling consistency.

**Lines Covered:**
- 344-346: Clear temporary lists, create edges_set
- 347-408: Main fact application loop
- 411-415: Update fact lists with unprocessed facts

---

### Code Structure

```python
# Lines 344-346: Setup
facts_to_be_applied_edge_new.clear()
facts_to_be_applied_edge_trace_new.clear()
edges_set = set(edges)

# Lines 347-408: Process each scheduled edge fact
for i in range(len(facts_to_be_applied_edge)):
    if facts_to_be_applied_edge[i][0] == t:  # Time matches
        comp, l, bnd, static, graph_attribute = [extract tuple components]

        # Add edge if missing
        if comp not in edges_set:
            _add_edge(comp[0], comp[1], ..., label.Label(''), ...)

        # BRANCH 1: Bound already exists and is static
        if l in interpretations_edge[comp].world and interpretations_edge[comp].world[l].is_static():
            # Record in trace (skip _update_edge)
            # Record IPL complements

        # BRANCH 2: Bound is non-static or doesn't exist
        else:
            if check_consistent_edge(...):
                _update_edge(...)  # Consistent: update normally
            else:
                # Inconsistent: resolve or override
                if inconsistency_check:
                    resolve_inconsistency_edge(...)
                else:
                    _update_edge(..., override=True)

        # Reschedule static facts for next timestep
        if static:
            facts_to_be_applied_edge_new.append((t+1, comp, l, bnd, static, graph_attribute))

    else:  # Time doesn't match: keep for later
        facts_to_be_applied_edge_new.append(facts_to_be_applied_edge[i])

# Lines 411-415: Replace fact list with unprocessed facts
facts_to_be_applied_edge[:] = facts_to_be_applied_edge_new.copy()
```

---

### Execution Flow

```
For each fact in facts_to_be_applied_edge:
    ├─ Time == t?
    │   ├─ NO → Keep in queue (lines 405-408)
    │   └─ YES → Process fact (lines 349-402)
    │       ├─ Add edge to graph if missing (lines 351-353)
    │       ├─ Is bound static in interpretations? (line 356)
    │       │   ├─ YES → Record trace, skip update (lines 358-370)
    │       │   └─ NO → Check consistency (line 373)
    │       │       ├─ Consistent → _update_edge (line 376)
    │       │       └─ Inconsistent (lines 385-397)
    │       │           ├─ inconsistency_check=True → resolve_inconsistency_edge (line 388)
    │       │           └─ inconsistency_check=False → _update_edge with override=True (line 390)
    │       └─ If static: reschedule for t+1 (lines 399-402)
    └─ Update facts_to_be_applied_edge with unprocessed (line 411)
```

---

### Comparison to Node Fact Application

Section 4 is structurally **nearly identical** to Section 3, with the following substitutions:

| Node Version (Section 3) | Edge Version (Section 4) |
|--------------------------|--------------------------|
| `facts_to_be_applied_node` | `facts_to_be_applied_edge` |
| `interpretations_node` | `interpretations_edge` |
| `nodes_set` | `edges_set` |
| `_add_node(comp, ...)` | `_add_edge(comp[0], comp[1], ..., label.Label(''), ...)` |
| `check_consistent_node(...)` | `check_consistent_edge(...)` |
| `_update_node(...)` | `_update_edge(...)` |
| `resolve_inconsistency_node(...)` | `resolve_inconsistency_edge(...)` |
| `rule_trace_node` | `rule_trace_edge` |

**Code Duplication:** ~70 lines of logic duplicated between Sections 3 and 4.

---

### Key Difference: _add_edge Parameters

**Line 352:**
```python
_add_edge(comp[0], comp[1], neighbors, reverse_neighbors, nodes, edges, 
          label.Label(''), interpretations_node, interpretations_edge, 
          predicate_map_edge, num_ga, t)
```

**Key observations:**
1. **comp[0], comp[1]:** Edge is a tuple `(source, target)`, so comp[0] = source, comp[1] = target
2. **label.Label(''):** Empty label passed to `_add_edge()`
   - Why empty? Because the edge may not have the predicate `l` yet
   - `_add_edge()` creates the edge structure without initializing predicates
   - The predicate `l` is added later via `_update_edge()` (if non-static)

**Contrast with _add_node:**
- `_add_node(comp, ...)` only needs the node identifier
- Nodes don't have source/target, so simpler signature

---

### Critical Difference: Trace Recording for Static Bounds

**Node version (line 284):**
```python
rule_trace_node.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, l, bnd))
```

**Edge version (line 359):**
```python
rule_trace_edge.append((numba.types.uint16(t), numba.types.uint16(fp_cnt), comp, l, interpretations_edge[comp].world[l]))
```

**Difference:** 
- Node version appends **`bnd`** (the fact's bound from the fact queue)
- Edge version appends **`interpretations_edge[comp].world[l]`** (the current bound in interpretations)

**Question:** Is this intentional or a bug?

**Possible interpretations:**
1. **Bug (inconsistency):** Should use `bnd` like node version
2. **Intentional:** Edge facts may need current interpretation value (e.g., if fact already applied earlier in same timestep)

**Impact:** If this is a bug, edge trace may record incorrect bounds for static facts.

---

### Execution Example: Edge Fact with Missing Edge

```python
# Setup
edges = [('Alice', 'Bob')]
facts_to_be_applied_edge = [
    (0, ('Alice', 'Carol'), 'friend', [0.9, 1.0], False, False),  # Edge doesn't exist yet
]

# t=0: Apply edge fact
comp = ('Alice', 'Carol')
Check: comp not in edges_set → True

# Add edge to graph (line 352)
_add_edge('Alice', 'Carol', neighbors, reverse_neighbors, nodes, edges, 
          label.Label(''), interpretations_node, interpretations_edge, 
          predicate_map_edge, num_ga, t)

Result after _add_edge:
  edges = [('Alice', 'Bob'), ('Alice', 'Carol')]
  neighbors['Alice'] = ['Bob', 'Carol']
  interpretations_edge[('Alice', 'Carol')] = World({})  # Empty world

# Check if static (line 356)
'friend' in interpretations_edge[('Alice', 'Carol')].world → False

# Not static, check consistency (line 373)
check_consistent_edge(...) → True (no existing bound)

# Call _update_edge (line 376)
_update_edge(interpretations_edge, predicate_map_edge, ('Alice', 'Carol'), 
             ('friend', [0.9, 1.0]), ...)

Result after _update_edge:
  interpretations_edge[('Alice', 'Carol')].world['friend'] = [0.9, 1.0]
```

---

### Key Observations

**1. Same Structure as Node Facts**
Edge fact application follows identical logic to node facts:
- Time-based scheduling
- Static vs non-static handling
- Consistency checking
- IPL complement recording
- Rescheduling for static facts

**2. Edge Creation On-Demand**
If an edge fact references a non-existent edge, it's created automatically via `_add_edge()`.

**3. Empty Label in _add_edge**
The `label.Label('')` parameter suggests edges are created without initial predicates, which are added later.

**4. All Section 3 Bugs Apply Here**
Same issues with tuple unpacking, rescheduling bounds checks, redundant copies, code duplication, and inefficient IPL iteration.

---

## Section 5: Rule Application Loop (Lines 417-535)

**Purpose:** Apply all pending rule instances scheduled for the current timestep, with an inner fixed-point loop for immediate rules (delta_t=0).

**Lines Covered:**
- 417-420: Inner loop setup (in_loop flag)
- 423-461: Node rule application
- 462-534: Edge rule application

---

### Code Structure

```python
# Lines 417-420: Inner fixed-point loop
in_loop = True
while in_loop:
    in_loop = False  # Will be set to True in Section 6 if delta_t=0 rules scheduled

    # Lines 423-461: APPLY NODE RULES
    rules_to_remove_idx.clear()
    for idx, i in enumerate(rules_to_be_applied_node):
        if i[0] == t:
            comp, l, bnd, set_static = i[1], i[2], i[3], i[4]
            
            if check_consistent_node(...):
                _update_node(..., mode='rule', override=override)
            else:
                if inconsistency_check:
                    resolve_inconsistency_node(..., mode='rule')
                else:
                    _update_node(..., mode='rule', override=True)
            
            rules_to_remove_idx.add(idx)
    
    # Remove applied rules
    rules_to_be_applied_node[:] = [filtered list]
    edges_to_be_added_node_rule[:] = [filtered list]
    
    # Lines 462-534: APPLY EDGE RULES
    rules_to_remove_idx.clear()
    for idx, i in enumerate(rules_to_be_applied_edge):
        if i[0] == t:
            comp, l, bnd, set_static = i[1], i[2], i[3], i[4]
            sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
            
            # Add inferred edges
            edges_added, changes = _add_edges(sources, targets, ..., edge_l, ...)
            
            # BRANCH 1: edge_l has a label (infer edges with label)
            if edge_l.value != '':
                for e in edges_added:
                    if interpretations_edge[e].world[edge_l].is_static():
                        continue  # Skip static bounds
                    
                    if check_consistent_edge(...):
                        _update_edge(e, (edge_l, bnd), ..., mode='rule')
                    else:
                        resolve or override
            
            # BRANCH 2: edge_l is empty (update existing edge)
            else:
                if check_consistent_edge(comp, (l, bnd), ...):
                    _update_edge(comp, (l, bnd), ..., mode='rule')
                else:
                    resolve or override
            
            rules_to_remove_idx.add(idx)
    
    # Remove applied rules
    rules_to_be_applied_edge[:] = [filtered list]
    edges_to_be_added_edge_rule[:] = [filtered list]
```

---

### Execution Flow

```
in_loop = True
while in_loop:
    in_loop = False
    
    Apply Node Rules:
        for each rule in rules_to_be_applied_node at time t:
            ├─ Check consistency
            ├─ Update or resolve
            ├─ Track convergence
            └─ Mark for removal
        Remove applied rules from lists
    
    Apply Edge Rules:
        for each rule in rules_to_be_applied_edge at time t:
            ├─ Extract sources, targets, edge_l from edges_to_be_added_edge_rule
            ├─ Call _add_edges() to create edges
            ├─ Branch on edge_l:
            │   ├─ edge_l != '' (infer edges with label):
            │   │   └─ For each newly added edge:
            │   │       ├─ Skip if static
            │   │       ├─ Check consistency
            │   │       └─ Update with (edge_l, bnd)
            │   └─ edge_l == '' (update existing edge):
            │       ├─ Check consistency for comp
            │       └─ Update with (l, bnd)
            └─ Mark for removal
        Remove applied rules from lists
    
    # If Section 6 schedules delta_t=0 rules, in_loop becomes True
    # → Loop repeats until fixed-point
```

---

### Key Logic: Inner Fixed-Point Loop

**Lines 417-420:**
```python
in_loop = True
while in_loop:
    in_loop = False
```

**Purpose:** Handle **immediate rules** with `delta_t=0`.

**Mechanism:**
1. Start with `in_loop = True` to enter loop
2. Set `in_loop = False` at beginning of iteration
3. Apply all pending rules for timestep `t`
4. In Section 6 (rule grounding), if any rule has `delta_t=0`, set `in_loop = True`
5. If `in_loop = True`, repeat loop (apply newly grounded rules immediately)
6. Continue until no delta_t=0 rules scheduled (fixed-point reached)

**Example:**
```python
# Rules:
#   R1: infected(X) → quarantine(X) [delta_t=0]
#   R2: quarantine(X) → isolated(X) [delta_t=0]

# t=0, fp_cnt=0:
Iteration 1:
  in_loop = False
  Apply rules: (none pending)
  Ground rules: R1 fires for Alice → schedule quarantine(Alice) at t=0
  → in_loop = True (delta_t=0)
  
Iteration 2:
  in_loop = False
  Apply rules: quarantine(Alice) applied
  Ground rules: R2 fires for Alice → schedule isolated(Alice) at t=0
  → in_loop = True (delta_t=0)
  
Iteration 3:
  in_loop = False
  Apply rules: isolated(Alice) applied
  Ground rules: No new rules fire
  → in_loop = False
  
Exit loop (fixed-point reached)
```

---

### Key Logic: Edge Rule Branching

**Lines 467-525:** Edge rules have two distinct paths based on `edge_l`:

**Path 1: edge_l != '' (Infer Edges with Label)**
```python
sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
edges_added, changes = _add_edges(sources, targets, ..., edge_l, ...)

if edge_l.value != '':
    for e in edges_added:
        if interpretations_edge[e].world[edge_l].is_static():
            continue
        _update_edge(e, (edge_l, bnd), ...)
```

**Use case:** Rules that **infer new edges** with a specific label.
- Example rule: `neighbor(X, Y) ∧ infected(X) → close_contact(X, Y)` with `infer_edges=True`
- `sources = [Alice]`, `targets = [Bob, Carol]`, `edge_l = 'close_contact'`
- Creates edges: `(Alice, Bob)`, `(Alice, Carol)` with label `close_contact`
- Updates all newly created edges with bound `bnd`

**Path 2: edge_l == '' (Update Existing Edge)**
```python
else:
    _update_edge(comp, (l, bnd), ...)
```

**Use case:** Rules that **update existing edges** without inferring new ones.
- Example rule: `edge(X, Y) ∧ infected(X) → risk(X, Y)`
- Updates the specific edge `comp = (X, Y)` with predicate `l = 'risk'` and bound `bnd`

---

### Key Logic: Static Bound Handling in Edge Rules

**Line 474:**
```python
if interpretations_edge[e].world[edge_l].is_static():
    continue
```

**Issue:** When `edge_l != ''` (inferring edges with label), the code skips updating static bounds.

**Question:** Why skip static bounds here but not in Path 2 (line 503)?

**Answer:** In Path 1, edges are newly created via `_add_edges()`. If the label `edge_l` is already static on the newly created edge, it was set during edge creation (from graph attributes). The rule should not override static graph attributes.

In Path 2, the edge already exists, and consistency checking handles static bounds.

**However:** This creates an asymmetry:
- Path 1: Skip static bounds silently (no trace update)
- Path 2: Check consistency (which may handle static bounds differently)

---

### Key Logic: Index Synchronization

**Critical invariant:** `rules_to_be_applied_edge[idx]` and `edges_to_be_added_edge_rule[idx]` must stay synchronized.

**Line 467:**
```python
sources, targets, edge_l = edges_to_be_added_edge_rule[idx]
```

**How synchronization maintained:**
- Section 6 (rule grounding) appends to both lists in parallel
- Section 5 (rule application) removes from both lists using same `rules_to_remove_idx`

**Lines 531-532:**
```python
rules_to_be_applied_edge[:] = numba.typed.List([rules_to_be_applied_edge[i] for i in range(len(rules_to_be_applied_edge)) if i not in rules_to_remove_idx])
edges_to_be_added_edge_rule[:] = numba.typed.List([edges_to_be_added_edge_rule[i] for i in range(len(edges_to_be_added_edge_rule)) if i not in rules_to_remove_idx])
```

**Risk:** If removal logic differs or lists get out of sync, wrong edge grounding applied to wrong rule.

---

### Key Difference: Rules vs Facts

| Aspect | Facts (Sections 3-4) | Rules (Section 5) |
|--------|---------------------|-------------------|
| **mode parameter** | `'fact'` or `'graph-attribute-fact'` | `'rule'` |
| **Rescheduling** | Static facts rescheduled for t+1 | Rules removed after application |
| **Static handling** | Skip `_update_node/edge()` | No special handling (except line 474) |
| **Trace source** | `facts_to_be_applied_*_trace` | `rules_to_be_applied_*_trace` |
| **Inner loop** | No inner loop | Fixed-point loop for delta_t=0 |

---

### Execution Example: Edge Rule with Inferred Edges

```python
# Rule: infected(X) ∧ neighbor(X, Y) → close_contact(X, Y) [delta_t=1, infer_edges=True]

# t=1: Rule instance scheduled
rules_to_be_applied_edge = [
    (1, ('Alice', 'Bob'), 'close_contact', [0.9, 1.0], False)
]
edges_to_be_added_edge_rule = [
    (['Alice'], ['Bob', 'Carol'], Label('close_contact'))
]

# Apply rule (line 464)
idx = 0
comp = ('Alice', 'Bob')  # Not actually used in this branch
l = 'close_contact'
bnd = [0.9, 1.0]
sources = ['Alice']
targets = ['Bob', 'Carol']
edge_l = Label('close_contact')

# Add edges (line 468)
edges_added = _add_edges(['Alice'], ['Bob', 'Carol'], ..., Label('close_contact'), ...)
# Returns: [('Alice', 'Bob'), ('Alice', 'Carol')]

# Branch 1: edge_l.value != '' (line 472)
for e in [('Alice', 'Bob'), ('Alice', 'Carol')]:
    # Check if static (line 474)
    if interpretations_edge[e].world['close_contact'].is_static():
        continue  # Skip if already static
    
    # Check consistency (line 476)
    if check_consistent_edge(interpretations_edge, e, ('close_contact', [0.9, 1.0])):
        # Update edge (line 478)
        _update_edge(interpretations_edge, ..., e, ('close_contact', [0.9, 1.0]), ...)

# Result:
#   ('Alice', 'Bob') has close_contact = [0.9, 1.0]
#   ('Alice', 'Carol') has close_contact = [0.9, 1.0]
```

---

### Key Observations

**1. Inner Loop Implements Stratified Negation**
The fixed-point loop ensures immediate rules (delta_t=0) are fully applied before advancing to the next timestep. This implements **stratified semantics** for logic programming.

**2. Edge Rules More Complex Than Node Rules**
Edge rules have two distinct execution paths based on `edge_l`, while node rules have a single path. This complexity increases bug surface area.

**3. Index Synchronization Critical**
The parallel lists `rules_to_be_applied_edge` and `edges_to_be_added_edge_rule` must remain perfectly synchronized. Any mismatch causes incorrect edge grounding.

**4. Static Bound Handling Inconsistent**
- Path 1 (edge_l != ''): Skip static bounds silently
- Path 2 (edge_l == ''): Let consistency check handle static bounds
- Facts (Sections 3-4): Skip `_update_*()` and record trace manually

**5. Massive Code Duplication**
Node rules and edge rules have nearly identical consistency checking and convergence tracking logic (duplicated 3+ times in this section alone).

---

## Section 6: Rule Grounding & Scheduling (Lines 536-627)

**Purpose:** Ground all rules in parallel to find applicable instances, schedule them for future timesteps, and manage the inner fixed-point loop.

**Lines Covered:**
- 536-540: Check update flag, increment fp_cnt
- 541-554: Initialize thread-safe lists and flags
- 555-603: Parallel rule grounding loop (prange)
- 605-618: Merge thread-safe lists to main lists
- 619-627: Merge thread-safe flags

---

### Code Structure

```python
# Lines 536-540: Entry guard
if update:  # Only ground rules if interpretations changed
    fp_cnt += 1
    
    # Lines 541-554: Initialize thread-safe structures (one per rule)
    rules_to_be_applied_node_threadsafe = List[List[...]] (len(rules) lists)
    rules_to_be_applied_edge_threadsafe = List[List[...]] (len(rules) lists)
    edges_to_be_added_edge_rule_threadsafe = List[List[...]] (len(rules) lists)
    in_loop_threadsafe = List[bool] (all False)
    update_threadsafe = List[bool] (all True)
    
    # Lines 555-603: PARALLEL GROUNDING
    for i in prange(len(rules)):  # PARALLEL
        rule = rules[i]
        delta_t = rule.get_delta()
        
        # Check timing constraint
        if t + delta_t <= tmax or tmax == -1 or again:
            # Ground rule
            applicable_node_rules, applicable_edge_rules = _ground_rule(...)
            
            # Process node rules
            for applicable_rule in applicable_node_rules:
                n, annotations, qualified_nodes, qualified_edges, _ = applicable_rule
                
                # Skip if static
                if rule.get_target() not in interpretations_node[n].world or 
                   not interpretations_node[n].world[rule.get_target()].is_static():
                    
                    bnd = annotate(...)
                    bnd = clamp(bnd, [0, 1])
                    
                    # Schedule rule for t + delta_t
                    rules_to_be_applied_node_threadsafe[i].append((t+delta_t, n, target, bnd, is_static))
                    
                    # If immediate rule, set flags
                    if delta_t == 0:
                        in_loop_threadsafe[i] = True
                        update_threadsafe[i] = False
            
            # Process edge rules (similar structure)
            for applicable_rule in applicable_edge_rules:
                # Similar logic...
    
    # Lines 605-618: Merge thread-safe lists
    for i in range(len(rules)):
        rules_to_be_applied_node.extend(rules_to_be_applied_node_threadsafe[i])
        rules_to_be_applied_edge.extend(rules_to_be_applied_edge_threadsafe[i])
        edges_to_be_added_edge_rule.extend(edges_to_be_added_edge_rule_threadsafe[i])
        # (Also merge trace lists if atom_trace)
    
    # Lines 619-627: Merge thread-safe flags
    in_loop = in_loop  # BUG: No-op
    update = update    # BUG: No-op
    for i in range(len(rules)):
        if in_loop_threadsafe[i]:
            in_loop = True
        if not update_threadsafe[i]:
            update = False
```

---

### Execution Flow

```
if update:  # Only if Section 5 caused changes
    fp_cnt += 1
    
    Initialize thread-safe structures:
        ├─ One list per rule for node rules
        ├─ One list per rule for edge rules
        ├─ One list per rule for edge groundings
        └─ Boolean flags: in_loop_threadsafe (all False), update_threadsafe (all True)
    
    PARALLEL: for each rule in rules:
        ├─ Check timing: t + delta_t <= tmax?
        ├─ Ground rule: _ground_rule() → (applicable_node_rules, applicable_edge_rules)
        ├─ For each applicable node rule:
        │   ├─ Skip if target predicate is static
        │   ├─ Annotate to get bound
        │   ├─ Clamp bound to [0, 1]
        │   ├─ Schedule for t + delta_t
        │   └─ If delta_t == 0: in_loop_threadsafe[i] = True, update_threadsafe[i] = False
        └─ For each applicable edge rule:
            └─ (Similar logic)
    
    Merge lists:
        Extend main lists with all thread-safe lists
    
    Merge flags:
        in_loop = OR(in_loop_threadsafe)
        update = AND(update_threadsafe)
```

---

### Key Logic: Thread-Safe Parallelization

**Why one list per rule?**

Each thread processes one rule in parallel. To avoid race conditions when appending to shared lists, each thread writes to its own dedicated list (`rules_to_be_applied_node_threadsafe[i]`).

After parallel execution completes, all thread-local lists are merged into the main lists (lines 605-618).

**Alternative approach (not used):** Use locks to synchronize access to shared lists. This approach avoids locks entirely by using separate lists.

---

### Key Logic: Bound Clamping

**Lines 570-572 (and 589-591):**
```python
bnd = annotate(annotation_functions, rule, annotations, rule.get_weights())
bnd_l = min(max(bnd[0], 0), 1)
bnd_u = min(max(bnd[1], 0), 1)
bnd = interval.closed(bnd_l, bnd_u)
```

**Purpose:** Ensure bounds are in valid range [0, 1].

**Question:** Why clamp here instead of in `annotate()` function?

**Answer:** `annotate()` may compute arbitrary values based on custom annotation functions. Clamping ensures the reasoning system only works with valid probability intervals.

**Issue:** This logic is duplicated (lines 570-572 and 589-591). Should be extracted to helper function.

---

### Key Logic: Static Bound Check

**Lines 567, 586:** Before scheduling a rule instance, check if the target predicate is static:

```python
# Node rules (line 567):
if rule.get_target() not in interpretations_node[n].world or 
   not interpretations_node[n].world[rule.get_target()].is_static():

# Edge rules (line 586):
if len(edges_to_add[0]) > 0 or 
   rule.get_target() not in interpretations_edge[e].world or 
   not interpretations_edge[e].world[rule.get_target()].is_static():
```

**Purpose:** Skip scheduling if:
1. **Node rules:** Target predicate already exists and is static
2. **Edge rules:** No new edges to add AND target predicate exists and is static

**Rationale:** Static bounds cannot be updated by rules, so don't waste time scheduling them.

**Edge rule special case:** If `len(edges_to_add[0]) > 0`, schedule the rule even if target is static. This handles the case where the rule infers new edges (which need to be added regardless of existing static bounds).

---

### Key Logic: Timing Constraint

**Line 560:**
```python
if t + delta_t <= tmax or tmax == -1 or again:
```

**Three cases:**
1. **t + delta_t <= tmax:** Rule would fire before/at maximum timestep → ground it
2. **tmax == -1:** Infinite mode → always ground rules
3. **again:** Resumption flag → allow rules to fire past original tmax

**Purpose:** Don't waste time grounding rules that will never be applied.

---

### Critical Bug: No-Op Flag Initialization

**Lines 620-621:**
```python
in_loop = in_loop
update = update
```

**Issue:** These lines do nothing. They assign variables to themselves.

**Likely intent:** Reset flags before merging? But this doesn't make sense.

**Possible explanations:**
1. **Copy-paste error:** Should be `in_loop = False` and `update = False`?
2. **Leftover code:** Debugging/placeholder code that was never removed
3. **Misunderstanding:** Developer thought this "resets" the variables

**Impact:** Variables are not reset, so they retain values from previous iterations. The merge loop (lines 622-626) then ORs/ANDs with existing values, which may not be the intended behavior.

---

### Critical Bug: Suspicious Flag Merge Logic

**Lines 622-626:**
```python
for i in range(len(rules)):
    if in_loop_threadsafe[i]:
        in_loop = True
    if not update_threadsafe[i]:
        update = False
```

**Analysis of `in_loop` merge:**
- `in_loop_threadsafe` initialized to all `False` (line 552)
- Set to `True` when `delta_t == 0` (lines 580, 602)
- Merge: If ANY thread has `in_loop_threadsafe[i] = True`, set `in_loop = True`
- **Logic:** OR across all threads ✓ (correct)

**Analysis of `update` merge:**
- `update_threadsafe` initialized to all `True` (line 553)
- Set to `False` when `delta_t == 0` (lines 581, 603)
- Merge: If ANY thread has `update_threadsafe[i] = False`, set `update = False`
- **Logic:** AND across all threads (via negation)

**Question:** Why is `update_threadsafe` initialized to `True` and set to `False` for delta_t=0 rules?

**Expected behavior:**
- `update` should be `True` if any rules were grounded (need to apply them in Section 5)
- `update` should be `False` if no rules were grounded (skip Section 5)

**Current behavior:**
- If ANY rule has `delta_t == 0`, set `update = False`
- This would prevent Section 5 from being entered again?

**This logic appears inverted or incorrect.** The flag management is confusing and likely buggy.

---

### Execution Example: Parallel Grounding

```python
# Rules:
#   R0: infected(X) → quarantine(X) [delta_t=0]
#   R1: quarantine(X) → isolated(X) [delta_t=1]
#   R2: isolated(X) → safe(X) [delta_t=2]

# t=0, fp_cnt=0, update=True
# Parallel grounding with 3 threads:

Thread 0 (R0):
  _ground_rule(R0) → applicable: [Alice]
  Schedule: (0, 'Alice', 'quarantine', [1,1], False)
  delta_t == 0 → in_loop_threadsafe[0] = True, update_threadsafe[0] = False
  rules_to_be_applied_node_threadsafe[0] = [(0, 'Alice', 'quarantine', [1,1], False)]

Thread 1 (R1):
  _ground_rule(R1) → applicable: (none, quarantine doesn't exist yet)
  rules_to_be_applied_node_threadsafe[1] = []

Thread 2 (R2):
  _ground_rule(R2) → applicable: (none, isolated doesn't exist yet)
  rules_to_be_applied_node_threadsafe[2] = []

# Merge lists:
rules_to_be_applied_node.extend([(0, 'Alice', 'quarantine', [1,1], False)])

# Merge flags:
in_loop = False  # (initial value retained due to lines 620-621)
for i in range(3):
    if in_loop_threadsafe[i]:  # i=0: True
        in_loop = True
    if not update_threadsafe[i]:  # i=0: True (not False)
        update = False

Result:
  in_loop = True (correct)
  update = False (suspicious)
```

---

### Key Observations

**1. Parallelization Strategy**
One list per rule avoids race conditions. Simple and effective, but uses O(R) space where R = number of rules.

**2. Flag Management Unclear**
The purpose and logic of `update_threadsafe` is not clear. The initialization to `True` and the merge logic don't align with expected behavior.

**3. No-Op Lines Are Red Flag**
Lines 620-621 suggest the code was not carefully reviewed or tested.

**4. Commented Code**
Line 593 has commented-out code, indicating incomplete refactoring or debugging artifacts.

**5. Bound Clamping Duplication**
Lines 570-572 and 589-591 duplicate the same bound clamping logic.

**6. Complex Conditions**
Lines 567 and 586 have complex boolean conditions that are hard to parse and maintain.

---

## Section 7: Convergence Checking (Lines 628-660)

**Purpose:** Detect when reasoning has reached a fixed-point and terminate the timestep loop.

**Lines Covered:**
- 628-644: delta_interpretation and delta_bound convergence modes
- 645-654: perfect_convergence mode
- 656-658: No convergence: increment t, update num_ga
- 660: Return (fp_cnt, t)

---

### Code Structure

```python
# Lines 631-637: delta_interpretation mode
if convergence_mode == 'delta_interpretation':
    if changes_cnt <= convergence_delta:
        if verbose:
            print(f'Converged at time: {t} with {int(changes_cnt)} changes')
        t += 1
        break

# Lines 638-644: delta_bound mode
elif convergence_mode == 'delta_bound':
    if bound_delta <= convergence_delta:
        if verbose:
            print(f'Converged at time: {t} with {float_to_str(bound_delta)} as max bound change')
        t += 1
        break

# Lines 648-654: perfect_convergence mode
elif convergence_mode == 'perfect_convergence':
    if t >= max_facts_time and t >= max_rules_time:
        if verbose:
            print(f'Converged at time: {t}')
        t += 1
        break

# Lines 656-658: No convergence this timestep
t += 1
num_ga.append(num_ga[-1])

# Line 660: Return
return fp_cnt, t
```

---

### Execution Flow

```
At end of each timestep:
    ├─ convergence_mode == 'delta_interpretation'?
    │   └─ If changes_cnt <= convergence_delta:
    │       ├─ Print convergence message (if verbose)
    │       ├─ t += 1
    │       └─ Break (exit timestep loop)
    │
    ├─ convergence_mode == 'delta_bound'?
    │   └─ If bound_delta <= convergence_delta:
    │       ├─ Print convergence message (if verbose)
    │       ├─ t += 1
    │       └─ Break (exit timestep loop)
    │
    ├─ convergence_mode == 'perfect_convergence'?
    │   └─ If t >= max_facts_time AND t >= max_rules_time:
    │       ├─ Print convergence message (if verbose)
    │       ├─ t += 1
    │       └─ Break (exit timestep loop)
    │
    └─ No convergence:
        ├─ t += 1
        └─ num_ga.append(num_ga[-1])

Return (fp_cnt, t)
```

---

### Convergence Mode 1: delta_interpretation

**Lines 631-637:**
```python
if convergence_mode == 'delta_interpretation':
    if changes_cnt <= convergence_delta:
        t += 1
        break
```

**Criterion:** Number of interpretation changes ≤ threshold

**How changes_cnt is tracked:**
- Initialized to 0 at start of each timestep (line 264)
- Incremented by `_update_node()` and `_update_edge()` (lines 309, 323, 383, 397, etc.)
- Each interpretation update increments by 1

**Use case:** Converge when "few enough" predicates changed.

**Example:**
```python
convergence_delta = 5
# If only 3 predicates changed this timestep → converge
# If 10 predicates changed → continue reasoning
```

---

### Convergence Mode 2: delta_bound

**Lines 638-644:**
```python
elif convergence_mode == 'delta_bound':
    if bound_delta <= convergence_delta:
        t += 1
        break
```

**Criterion:** Maximum bound change magnitude ≤ threshold

**How bound_delta is tracked:**
- Initialized to 0 at start of each timestep (line 264)
- Updated to max of all changes: `bound_delta = max(bound_delta, changes)` (lines 307, 321, 381, 395, etc.)
- `changes` from `_update_*()` represents magnitude of bound change

**Use case:** Converge when bounds are "stable enough" (small changes).

**Example:**
```python
convergence_delta = 0.01
# If max bound change is 0.005 → converge (stable)
# If max bound change is 0.1 → continue reasoning (still changing significantly)
```

---

### Convergence Mode 3: perfect_convergence

**Lines 648-654:**
```python
elif convergence_mode == 'perfect_convergence':
    if t >= max_facts_time and t >= max_rules_time:
        t += 1
        break
```

**Criterion:** No more facts or rules scheduled for future timesteps

**How max_*_time is tracked:**
- `max_facts_time`: Passed as parameter (computed when facts scheduled)
- `max_rules_time`: Updated in Section 6 when rules scheduled (lines 573, 592)

**Logic:** If current timestep `t` has reached or passed the latest scheduled fact/rule time, and no more facts/rules will be scheduled (because all rules have been grounded), then reasoning is complete.

**Use case:** Guaranteed complete convergence - all facts and rules fully applied.

**Example:**
```python
max_facts_time = 5  # Last fact scheduled for t=5
max_rules_time = 3  # Last rule scheduled for t=3

# t=5: Check t >= 5 and t >= 3 → True → Converge
```

---

### Convergence Mode 4: naive (implicit)

**Not explicitly handled in this section**

If `convergence_mode` is not one of the three modes above, no convergence check occurs. Reasoning continues until:
1. `t == tmax` (line 241)
2. All rules exhausted naturally

**Use case:** Run for exactly `tmax` timesteps without early convergence.

---

### Key Logic: Consistent Time Increment

**Lines 636, 643, 653:**
```python
t += 1
break
```

**Purpose:** Ensure consistent `t` value regardless of convergence.

**Rationale:**
- If convergence detected at timestep 5, return `t=6`
- If no convergence and loop exits at `t==tmax`, return `t=tmax+1` (line 657)
- This makes the returned timestep consistent: it's always "next timestep that would run"

**Use case for resumption:**
```python
# First run
t_final, fp_final = reason(..., tmax=10, ...)
# Returns (11, fp_cnt) - reasoning stopped after t=10

# Resume from where we left off
t_final2, fp_final2 = reason(..., tmax=20, prev_reasoning_data=(t_final, fp_final), ...)
# Continues from t=11
```

---

### Key Logic: num_ga Update

**Line 658:**
```python
num_ga.append(num_ga[-1])
```

**Purpose:** Append ground atom count for current timestep.

**Question:** Why `num_ga[-1]` (repeat previous count) instead of computing current count?

**Answer:** The actual count is updated incrementally during the timestep (in `_update_node()` and `_update_edge()`). Line 658 preserves the final count for this timestep.

**However:** This seems suspicious. If `num_ga` is updated during the timestep, why append the same value again?

**Possible interpretation:**
- `num_ga[-1]` contains count at end of timestep `t`
- Appending it again prepares for timestep `t+1`
- Next timestep will update `num_ga[-1]` in place?

**This logic is unclear and potentially buggy.**

---

### Critical Bug: Return Order

**Line 660:**
```python
return fp_cnt, t
```

**Issue:** Function signature indicates return type is `(t, fp_cnt)`, but this line returns `(fp_cnt, t)`.

**Evidence from function overview:**
- Documentation says: "Returns: Tuple[int, int] - (final_timestep, total_fp_iterations)"
- Variable names: `t` is timestep, `fp_cnt` is fixed-point count
- Caller likely expects `(timestep, fp_count)` order

**Impact:**
- **CRITICAL:** All callers of `reason()` will receive swapped values
- Timestep will be interpreted as fp_count and vice versa
- Resumption will break (wrong timestep used)
- Metrics will be wrong

**This is almost certainly a bug unless all calling code compensates for the swap.**

---

### Execution Example: delta_interpretation Convergence

```python
# Setup
convergence_mode = 'delta_interpretation'
convergence_delta = 5
tmax = 100

# t=0:
changes_cnt = 0
Apply facts → changes_cnt = 10
Apply rules → changes_cnt = 25
Check convergence: 25 <= 5? No
t += 1 (line 657)

# t=1:
changes_cnt = 0
Apply facts → changes_cnt = 2
Apply rules → changes_cnt = 8
Check convergence: 8 <= 5? No
t += 1

# t=2:
changes_cnt = 0
Apply facts → changes_cnt = 1
Apply rules → changes_cnt = 3
Check convergence: 3 <= 5? Yes!
Print: "Converged at time: 2 with 3 changes"
t += 1  # t = 3
break

Return (fp_cnt, 3)
```

---

### Execution Example: perfect_convergence

```python
# Setup
convergence_mode = 'perfect_convergence'
max_facts_time = 5  # Last fact scheduled for t=5
max_rules_time = 3  # Last rule scheduled for t=3

# t=0:
Check: 0 >= 5 and 0 >= 3? No
t += 1

# t=1:
Check: 1 >= 5 and 1 >= 3? No
t += 1

# t=2:
Check: 2 >= 5 and 2 >= 3? No
t += 1

# t=3:
Check: 3 >= 5 and 3 >= 3? No (3 < 5)
t += 1

# t=4:
Check: 4 >= 5 and 4 >= 3? No (4 < 5)
t += 1

# t=5:
Check: 5 >= 5 and 5 >= 3? Yes!
Print: "Converged at time: 5"
t += 1  # t = 6
break

Return (fp_cnt, 6)
```

---

### Key Observations

**1. Three Explicit Convergence Modes**
- delta_interpretation: Changes-based
- delta_bound: Magnitude-based
- perfect_convergence: Schedule-based

**2. Fourth Implicit Mode (naive)**
If no mode matches, reasoning continues until tmax.

**3. Consistent Time Handling**
All convergence paths increment `t` before breaking, ensuring consistent return value.

**4. Return Value Bug**
Returns `(fp_cnt, t)` but should return `(t, fp_cnt)` based on documentation and variable semantics.

**5. num_ga Logic Unclear**
Line 658 appends `num_ga[-1]` but the purpose and correctness of this is not obvious.

**6. No Validation**
No validation that convergence_mode is a valid value. Invalid mode silently uses naive convergence.

---


---

# Analysis Summary

## Statistics

**Function:** `reason()`  
**Location:** `interpretation.py:228-660`  
**Total Lines:** 434 lines  
**Sections Analyzed:** 7  
**Parameters:** 33 (most in entire PyReason codebase)  
**Return Type:** `Tuple[int, int]` - Should be `(t, fp_cnt)` but returns `(fp_cnt, t)` (BUG-204)

---

## Bug Summary

**Total Bugs Found:** 37 bugs (BUG-172 through BUG-208)

### By Severity:
- **CRITICAL:** 1 bug (BUG-204: Return values in wrong order)
- **HIGH:** 3 bugs (BUG-180, BUG-190, BUG-196, BUG-197)
- **MEDIUM:** 10 bugs
- **LOW:** 23 bugs

### By Section:
| Section | Lines | Bugs | Key Issues |
|---------|-------|------|------------|
| 1. Initialization | 228-238 | 0 | Clean |
| 2. Timestep Loop | 239-265 | 2 | Reset efficiency, static semantics |
| 3. Node Facts | 267-342 | 6 | KeyError risk, IPL iteration, code duplication |
| 4. Edge Facts | 343-415 | 8 | Trace inconsistency (HIGH), massive duplication |
| 5. Rule Application | 417-535 | 8 | Index sync (HIGH), edge_l branching complexity |
| 6. Rule Grounding | 536-627 | 8 | No-op flags (HIGH), inverted flag logic (HIGH) |
| 7. Convergence | 628-660 | 5 | Return order (CRITICAL), num_ga logic unclear |

---

## Critical Findings

### 1. Return Value Bug (CRITICAL)
**BUG-204:** Function returns `(fp_cnt, t)` but should return `(t, fp_cnt)`.
- **Impact:** All callers receive swapped values
- **Affects:** Resumption, metrics, user expectations
- **Fix:** Change line 660 to `return t, fp_cnt`

### 2. Parallel Flag Management (HIGH)
**BUG-196, BUG-197:** Flag merge logic is incorrect:
- Lines 620-621: No-op assignments (`in_loop = in_loop`)
- `update_threadsafe` initialization and merge logic inverted
- **Impact:** Fixed-point loop may not work correctly
- **Fix:** Complete redesign of flag management

### 3. Index Synchronization (HIGH)
**BUG-190:** No validation that `rules_to_be_applied_edge` and `edges_to_be_added_edge_rule` stay synchronized.
- **Impact:** Silent data corruption, wrong edges applied to wrong rules
- **Fix:** Add assertions or refactor to single list of tuples

### 4. Trace Recording Inconsistency (HIGH)
**BUG-180:** Node facts use `bnd`, edge facts use `interpretations_edge[comp].world[l]`.
- **Impact:** Edge trace may record incorrect bounds
- **Fix:** Standardize both to use `bnd`

---

## Major Patterns

### 1. Massive Code Duplication
**Sections affected:** 3-5  
**Duplications:**
- Node vs edge fact application: ~70 lines (Section 3 vs 4)
- Consistency checking pattern: Repeated 5+ times
- Convergence tracking: Duplicated in every branch
- Bound clamping: Lines 570-572 and 589-591

**Impact:**
- Bug fixes must be applied in multiple locations
- Already caused inconsistencies (BUG-180)
- 434-line function could be ~300 lines with proper extraction

**Recommendation:** Extract common logic to helper functions:
- `_apply_facts_for_component()`
- `_check_and_update_interpretation()`
- `_clamp_and_create_interval()`

---

### 2. Unclear Semantics
**Issues:**
- `persistent` vs `static` interaction (BUG-173)
- `update_threadsafe` initialization and merge (BUG-197, BUG-203)
- `num_ga.append(num_ga[-1])` purpose (BUG-205)
- Static bound handling differs between facts and rules (BUG-192)

**Impact:**
- Code is difficult to understand and maintain
- Likely incorrect behavior in edge cases
- New developers will be confused

**Recommendation:**
- Document intended semantics clearly
- Add comments explaining non-obvious logic
- Refactor to make behavior explicit

---

### 3. Fragile Parallel Lists
**Pattern:** Multiple lists must stay synchronized by index:
- `rules_to_be_applied_edge[i]` ↔ `edges_to_be_added_edge_rule[i]`
- `rules_to_be_applied_*[i]` ↔ `rules_to_be_applied_*_trace[i]`

**Risk:** No validation, easy to break, silent corruption

**Recommendation:** Use structured data:
```python
@dataclass
class RuleInstance:
    time: int
    component: Component
    label: Label
    bound: Interval
    is_static: bool
    trace: Optional[Trace]
    edge_grounding: Optional[EdgeGrounding]

rules_to_be_applied = List[RuleInstance]
```

---

### 4. Performance Issues
**Inefficiencies:**
- O(V+E) reset every timestep in non-persistent mode (BUG-172)
- O(N×M) IPL iteration for every static fact (BUG-175, BUG-183)
- Redundant list length checks before extend (BUG-200)
- No early exit from convergence checking

**Impact:** Performance degrades with large graphs or long IPL lists

**Recommendation:**
- Build IPL reverse index once
- Track which nodes/edges need reset (dirty flag)
- Remove unnecessary checks

---

## Recommendations

### Immediate Fixes (Critical/High Severity)
1. **BUG-204:** Fix return order to `return t, fp_cnt`
2. **BUG-196, BUG-197:** Fix flag merge logic in Section 6
3. **BUG-190:** Add assertions for list synchronization
4. **BUG-180:** Fix trace recording inconsistency

### Refactoring Priorities
1. **Extract fact application logic** to reduce duplication (Sections 3-4)
2. **Extract consistency checking pattern** to single function
3. **Replace parallel lists with structured data** for edge rules
4. **Document unclear semantics** (persistent, static, update_threadsafe, num_ga)

### Testing Priorities
1. **Test resumption** with various `prev_reasoning_data` values (catches BUG-204)
2. **Test delta_t=0 rules** in parallel (catches BUG-196, BUG-197)
3. **Test edge rule grounding** with infer_edges (catches BUG-190)
4. **Test trace correctness** for static edge facts (catches BUG-180)

---

## Comparison to _ground_rule()

| Aspect | _ground_rule() | reason() |
|--------|----------------|----------|
| **Lines** | 444 | 434 |
| **Parameters** | 15 | 33 |
| **Bugs Found** | ~70 | 37 |
| **Complexity** | High (complex clause evaluation) | Very High (orchestration) |
| **Main Issues** | Clause evaluation logic, variable handling | Duplication, flag management, synchronization |
| **Role** | Find applicable rules | Orchestrate entire reasoning process |

**Key difference:** `_ground_rule()` has more bugs due to complex logic, but `reason()` has higher-severity bugs due to orchestration complexity.

---

## Conclusion

The `reason()` function successfully implements temporal fixed-point reasoning with multiple convergence modes and parallel execution. However, it suffers from:

1. **Critical bugs:** Return value order, flag management
2. **Massive code duplication:** ~100+ lines could be extracted
3. **Unclear semantics:** Multiple poorly-documented behaviors
4. **Fragile design:** Parallel list synchronization without validation

**Overall assessment:** The function works for common cases but has serious bugs that will manifest in:
- Resumption scenarios (BUG-204)
- Parallel execution with delta_t=0 rules (BUG-196, BUG-197)
- Edge rule grounding (BUG-190)
- Provenance tracking (BUG-180)

**Recommended action:** Immediate fixes for critical bugs, then refactoring to reduce duplication and improve clarity.

---

**Analysis Complete**  
**Total Bugs Logged:** 37 (BUG-172 through BUG-208)  
**Date:** Layer 9 Analysis Complete

