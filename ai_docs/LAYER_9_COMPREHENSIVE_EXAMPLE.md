# Layer 9: reason() - Comprehensive Execution Example

This example traces through the complete execution of `reason()`, demonstrating all critical branches and the fixed-point reasoning loop.

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
    'Alice': World({'infected': [0.9, 1.0]}),  # Will be marked static
    'Bob':   World({'susceptible': [0.8, 1.0]}),
    'Carol': World({'susceptible': [0.7, 0.9]}),
    'Dave':  World({})  # No initial predicates
}

interpretations_edge = {
    ('Alice', 'Bob'):   World({'neighbor': [1.0, 1.0]}),
    ('Alice', 'Carol'): World({'neighbor': [1.0, 1.0]}),
    ('Bob', 'Dave'):    World({'neighbor': [1.0, 1.0]})
}
```

### Rules

| ID | Rule | delta_t | Notes |
|----|------|---------|-------|
| R1 | `infected(X) → quarantine(X)` | 0 | Immediate rule |
| R2 | `infected(X) ∧ neighbor(X,Y) ∧ susceptible(Y) → at_risk(Y)` | 1 | Delayed rule |
| R3 | `at_risk(X) → monitor(X)` | 0 | Immediate rule |
| R4 | `infected(X) ∧ neighbor(X,Y) → exposure(X,Y)` | 1 | Infers new edges |

### Scheduled Facts

```python
facts_to_be_applied_node = [
    (0, 'Alice', 'infected', [0.9, 1.0], True, True),   # t=0, static, graph_attribute
    (0, 'Bob', 'susceptible', [0.8, 1.0], False, True), # t=0, non-static
    (0, 'Carol', 'susceptible', [0.7, 0.9], False, True),
    (2, 'Dave', 'vaccinated', [0.5, 0.6], False, False) # t=2, non-static, not graph_attribute
]
```

### Configuration

```python
tmax = 10
persistent = True
convergence_mode = 'perfect_convergence'
inconsistency_check = False
update_mode = 'override'
```

---

## Execution Trace

### Initialization (Lines 228-238)

```python
# Extract previous reasoning data (for resumption)
t = 0           # Starting timestep
fp_cnt = 0      # Fixed-point iteration counter
max_rules_time = 0

# Initialize temporary storage
facts_to_be_applied_node_new = []
facts_to_be_applied_edge_new = []
rules_to_remove_idx = {-1}  # Sentinel value
```

**State after initialization:**
- Ready to begin timestep loop
- No previous reasoning data (fresh start)

---

### Timestep t=0

#### Step 1: Timestep Loop Entry (Lines 239-265)

```
Check: t < tmax? → 0 < 10 → YES, enter loop
Check: persistent=True → Skip non-persistent reset
Initialize: changes_cnt=0, bound_delta=0, update=False
```

#### Step 2: Node Fact Application (Lines 267-342)

**Processing fact: `infected(Alice) = [0.9, 1.0]` (static)**

```
Time matches: 0 == 0 → YES
Node exists: 'Alice' in nodes → YES
Check static: 'infected' in Alice.world? → YES, is_static? → YES

BRANCH: Static bound already exists
  → Skip _update_node() (bound cannot change)
  → Record in rule_trace_node: (t=0, fp_cnt=0, 'Alice', 'infected', [0.9,1.0])
  → Check IPL complements (none in this example)
  → Reschedule for t+1: (1, 'Alice', 'infected', [0.9,1.0], True, True)
```

**Processing fact: `susceptible(Bob) = [0.8, 1.0]` (non-static)**

```
Time matches: 0 == 0 → YES
Node exists: 'Bob' in nodes → YES
Check static: 'susceptible' in Bob.world? → YES, is_static? → NO

BRANCH: Non-static bound
  → check_consistent_node() → YES (no conflict)
  → _update_node(Bob, susceptible, [0.8,1.0])
    - Update Bob.world['susceptible'] = [0.8, 1.0]
    - Update predicate_map_node['susceptible'].add('Bob')
    - Record in rule_trace_node
    - Returns: (update=True, changes=1)
  → update = True, changes_cnt = 1
```

**Processing fact: `susceptible(Carol) = [0.7, 0.9]`**
- Same flow as Bob
- `changes_cnt = 2`

**Processing fact: `vaccinated(Dave)` at t=2**
```
Time matches: 0 == 2 → NO
→ Add to facts_to_be_applied_node_new (process later)
```

**State after node facts:**
```python
interpretations_node = {
    'Alice': {'infected': [0.9, 1.0]},      # Static
    'Bob':   {'susceptible': [0.8, 1.0]},   # Updated
    'Carol': {'susceptible': [0.7, 0.9]},   # Updated
    'Dave':  {}
}
update = True
changes_cnt = 2
```

#### Step 3: Edge Fact Application (Lines 343-415)

No edge facts scheduled for t=0. Skip to rule application.

#### Step 4: Rule Application Loop Entry (Lines 417-420)

```python
in_loop = True
while in_loop:
    in_loop = False  # Will be set True if delta_t=0 rules scheduled
```

**First iteration of inner loop:**

No rules in `rules_to_be_applied_node` or `rules_to_be_applied_edge` yet (haven't grounded).

#### Step 5: Rule Grounding (Lines 536-627)

```
Check: update == True → YES, enter grounding phase
fp_cnt += 1  → fp_cnt = 1
```

**Initialize thread-safe lists (one per rule):**
```python
rules_to_be_applied_node_threadsafe = [[], [], [], []]  # 4 rules
rules_to_be_applied_edge_threadsafe = [[], [], [], []]
in_loop_threadsafe = [False, False, False, False]
update_threadsafe = [True, True, True, True]
```

**Parallel grounding (conceptually 4 threads):**

**Thread 0 - Rule R1: `infected(X) → quarantine(X)` [delta_t=0]**
```
_ground_rule(R1) called:
  - Find nodes where infected(X) satisfies threshold
  - Alice.infected = [0.9, 1.0] → satisfies
  - Returns: applicable_node_rules = [(Alice, annotations, ...)]

Process applicable rules:
  - Target 'quarantine' not in Alice.world → schedule rule
  - bnd = annotate(...) → [1.0, 1.0]
  - Clamp to [0,1] → [1.0, 1.0]
  - Schedule: (t=0, 'Alice', 'quarantine', [1.0,1.0], False)
  - delta_t == 0 → in_loop_threadsafe[0] = True
```

**Thread 1 - Rule R2: `infected(X) ∧ neighbor(X,Y) ∧ susceptible(Y) → at_risk(Y)` [delta_t=1]**
```
_ground_rule(R2) called:
  - infected(X): X = [Alice]
  - neighbor(X,Y): (Alice,Bob), (Alice,Carol)
  - susceptible(Y): Bob, Carol satisfy
  - Returns: applicable_node_rules = [(Bob, ...), (Carol, ...)]

Process applicable rules:
  - Schedule: (t=1, 'Bob', 'at_risk', [0.8,1.0], False)
  - Schedule: (t=1, 'Carol', 'at_risk', [0.7,0.9], False)
  - delta_t == 1 → in_loop_threadsafe[1] stays False
  - max_rules_time = max(0, 1) = 1
```

**Thread 2 - Rule R3: `at_risk(X) → monitor(X)` [delta_t=0]**
```
_ground_rule(R3) called:
  - No nodes have at_risk predicate yet
  - Returns: applicable_node_rules = []

Nothing to schedule.
```

**Thread 3 - Rule R4: `infected(X) ∧ neighbor(X,Y) → exposure(X,Y)` [delta_t=1, infer_edges]**
```
_ground_rule(R4) called:
  - infected(X): X = [Alice]
  - neighbor(X,Y): (Alice,Bob), (Alice,Carol)
  - Returns: applicable_edge_rules with edges_to_add

Process applicable rules:
  - Schedule edge rules for (Alice,Bob) and (Alice,Carol)
  - edges_to_be_added_edge_rule_threadsafe[3] = [(['Alice'],['Bob','Carol'],'exposure')]
  - Schedule: (t=1, (Alice,Bob), 'exposure', [0.9,1.0], False)
  - max_rules_time = max(1, 1) = 1
```

**Merge thread-safe lists (Lines 605-618):**
```python
rules_to_be_applied_node = [
    (0, 'Alice', 'quarantine', [1.0,1.0], False),  # From R1
    (1, 'Bob', 'at_risk', [0.8,1.0], False),       # From R2
    (1, 'Carol', 'at_risk', [0.7,0.9], False)      # From R2
]
rules_to_be_applied_edge = [
    (1, ('Alice','Bob'), 'exposure', [0.9,1.0], False),
    (1, ('Alice','Carol'), 'exposure', [0.9,1.0], False)
]
edges_to_be_added_edge_rule = [
    (['Alice'], ['Bob','Carol'], Label('exposure'))
]
```

**Merge flags (Lines 619-627):**
```
in_loop = in_loop_threadsafe[0] = True  (R1 has delta_t=0)
```

#### Step 6: Inner Loop Continues (delta_t=0)

```
in_loop == True → Continue inner loop
in_loop = False  (reset for this iteration)
```

**Apply pending node rules at t=0:**

**Rule: `quarantine(Alice) = [1.0, 1.0]`**
```
Time matches: 0 == 0 → YES
check_consistent_node() → YES
_update_node(Alice, quarantine, [1.0,1.0])
  - Update Alice.world['quarantine'] = [1.0, 1.0]
  - update = True, changes_cnt = 3
Mark rule for removal
```

**Remove applied rules:**
```python
rules_to_be_applied_node = [
    (1, 'Bob', 'at_risk', ...),      # Still pending (t=1)
    (1, 'Carol', 'at_risk', ...)     # Still pending (t=1)
]
```

**State after applying delta_t=0 rules:**
```python
interpretations_node['Alice'] = {
    'infected': [0.9, 1.0],
    'quarantine': [1.0, 1.0]  # NEW
}
```

#### Step 7: Re-ground Rules (update=True)

```
update == True → Ground rules again
fp_cnt += 1 → fp_cnt = 2
```

**Ground R1 again:**
```
infected(Alice) → quarantine(Alice)
But quarantine(Alice) already exists → is_static? → NO
→ Schedule again? Check condition:
  rule.get_target() not in world OR not is_static()
  'quarantine' in Alice.world → YES
  is_static() → NO
→ Still schedule (could update bound)
→ in_loop_threadsafe[0] = True
```

**Ground R3 (at_risk → monitor):**
```
Still no nodes with at_risk → nothing to schedule
```

**Merge flags:**
```
in_loop = True (R1 scheduled again)
```

#### Step 8: Apply delta_t=0 Rules Again

**Apply quarantine(Alice) again:**
```
_update_node(Alice, quarantine, [1.0,1.0])
  - Bound unchanged (already [1.0,1.0])
  - Returns: update=False, changes=0
```

**State:** No changes this iteration.

#### Step 9: Re-ground Rules (update=False)

```
update == False → Skip grounding phase
in_loop = False (no delta_t=0 rules fired)
```

**Exit inner loop.**

#### Step 10: Convergence Check (Lines 628-658)

```
convergence_mode == 'perfect_convergence'
Check: t >= max_facts_time (0 >= 2?) → NO
→ No convergence yet

t += 1 → t = 1
num_ga.append(num_ga[-1])
```

---

### Timestep t=1

#### Step 1: Loop Entry

```
t < tmax? → 1 < 10 → YES
persistent=True → Skip reset
changes_cnt = 0, update = False
```

#### Step 2: Node Fact Application

**Rescheduled static fact: `infected(Alice)`**
```
Time matches: 1 == 1 → YES
Check static: 'infected' already static in Alice.world → YES

BRANCH: Static bound
  → Record in trace only
  → Reschedule for t=2
```

No other facts at t=1. `update = False` (static facts don't trigger update).

#### Step 3: Edge Fact Application

No edge facts. Skip.

#### Step 4: Rule Application

**Apply pending node rules at t=1:**

**Rule: `at_risk(Bob) = [0.8, 1.0]`**
```
Time matches: 1 == 1 → YES
check_consistent_node() → YES
_update_node(Bob, at_risk, [0.8,1.0])
  - Update Bob.world['at_risk'] = [0.8, 1.0]
  - update = True, changes_cnt = 1
```

**Rule: `at_risk(Carol) = [0.7, 0.9]`**
```
_update_node(Carol, at_risk, [0.7,0.9])
  - update = True, changes_cnt = 2
```

**Apply pending edge rules at t=1:**

**Rule: `exposure(Alice,Bob) = [0.9, 1.0]` with infer_edges**
```
Extract from edges_to_be_added_edge_rule:
  sources = ['Alice'], targets = ['Bob', 'Carol'], edge_l = 'exposure'

Call _add_edges(['Alice'], ['Bob','Carol'], ..., 'exposure'):
  - Creates edges: (Alice,Bob), (Alice,Carol) if they don't exist
  - These edges exist but 'exposure' label is new
  - Returns: edges_added = [(Alice,Bob), (Alice,Carol)]

BRANCH: edge_l.value != '' (has label)
  For each edge in edges_added:
    - Check if exposure is static → NO
    - check_consistent_edge() → YES
    - _update_edge(edge, ('exposure', [0.9,1.0]))
```

**State after edge rules:**
```python
interpretations_edge = {
    ('Alice', 'Bob'):   {'neighbor': [1.0,1.0], 'exposure': [0.9,1.0]},
    ('Alice', 'Carol'): {'neighbor': [1.0,1.0], 'exposure': [0.9,1.0]},
    ('Bob', 'Dave'):    {'neighbor': [1.0,1.0]}
}
```

#### Step 5: Rule Grounding

```
update == True → Ground all rules
fp_cnt += 1 → fp_cnt = 3
```

**Ground R3: `at_risk(X) → monitor(X)` [delta_t=0]**
```
Now Bob and Carol have at_risk!
_ground_rule(R3):
  - at_risk(Bob) satisfies threshold
  - at_risk(Carol) satisfies threshold
  - Returns: [(Bob, ...), (Carol, ...)]

Schedule:
  - (t=1, 'Bob', 'monitor', [0.8,1.0], False)
  - (t=1, 'Carol', 'monitor', [0.7,0.9], False)
  - delta_t == 0 → in_loop_threadsafe = True
```

**Merge:** `in_loop = True`

#### Step 6: Apply delta_t=0 Rules

```python
# Apply monitor(Bob) and monitor(Carol)
_update_node(Bob, monitor, [0.8,1.0]) → changes_cnt = 3
_update_node(Carol, monitor, [0.7,0.9]) → changes_cnt = 4
```

**State:**
```python
interpretations_node = {
    'Alice': {'infected': [0.9,1.0], 'quarantine': [1.0,1.0]},
    'Bob':   {'susceptible': [0.8,1.0], 'at_risk': [0.8,1.0], 'monitor': [0.8,1.0]},
    'Carol': {'susceptible': [0.7,0.9], 'at_risk': [0.7,0.9], 'monitor': [0.7,0.9]},
    'Dave':  {}
}
```

#### Step 7: Re-ground (update=True)

```
fp_cnt += 1 → fp_cnt = 4
```

No new rules fire (R3 already applied to Bob and Carol).

**Merge:** `in_loop = False`, `update = False`

**Exit inner loop.**

#### Step 8: Convergence Check

```
convergence_mode == 'perfect_convergence'
Check: t >= max_facts_time (1 >= 2?) → NO
→ No convergence

t += 1 → t = 2
```

---

### Timestep t=2

#### Step 1: Loop Entry

```
t < tmax? → 2 < 10 → YES
Initialize: changes_cnt = 0, update = False
```

#### Step 2: Node Fact Application

**Rescheduled static fact: `infected(Alice)` at t=2**
```
Static bound → trace only, reschedule for t=3
```

**New fact: `vaccinated(Dave) = [0.5, 0.6]`**
```
Time matches: 2 == 2 → YES
Check: 'vaccinated' in Dave.world? → NO

BRANCH: Predicate doesn't exist (non-static path)
  check_consistent_node() → YES (no existing bound)
  _update_node(Dave, vaccinated, [0.5,0.6])
    - Create Dave.world['vaccinated'] = [0.5, 0.6]
    - update = True, changes_cnt = 1
```

#### Step 3: Rule Application

No pending rules at t=2.

#### Step 4: Rule Grounding

```
update == True → Ground all rules
fp_cnt += 1 → fp_cnt = 5
```

No new applicable rules found.

**Merge:** `in_loop = False`, `update = False`

#### Step 5: Convergence Check

```
convergence_mode == 'perfect_convergence'
Check: t >= max_facts_time AND t >= max_rules_time
       2 >= 2 AND 2 >= 1 → YES!

CONVERGED!
Print: "Converged at time: 2"
t += 1 → t = 3
break
```

---

### Function Return

```python
return fp_cnt, t  # Returns (5, 3)

# Note: This is actually swapped (BUG-204)
# Should return (t, fp_cnt) = (3, 5)
```

---

## Final State Summary

### Interpretations

```python
interpretations_node = {
    'Alice': {
        'infected': [0.9, 1.0],      # Static, from t=0 fact
        'quarantine': [1.0, 1.0]     # From R1 at t=0
    },
    'Bob': {
        'susceptible': [0.8, 1.0],   # From t=0 fact
        'at_risk': [0.8, 1.0],       # From R2 at t=1
        'monitor': [0.8, 1.0]        # From R3 at t=1
    },
    'Carol': {
        'susceptible': [0.7, 0.9],   # From t=0 fact
        'at_risk': [0.7, 0.9],       # From R2 at t=1
        'monitor': [0.7, 0.9]        # From R3 at t=1
    },
    'Dave': {
        'vaccinated': [0.5, 0.6]     # From t=2 fact
    }
}

interpretations_edge = {
    ('Alice', 'Bob'):   {'neighbor': [1.0,1.0], 'exposure': [0.9,1.0]},
    ('Alice', 'Carol'): {'neighbor': [1.0,1.0], 'exposure': [0.9,1.0]},
    ('Bob', 'Dave'):    {'neighbor': [1.0,1.0]}
}
```

### Execution Metrics

| Metric | Value |
|--------|-------|
| Final timestep | 3 |
| Fixed-point iterations | 5 |
| Total interpretation changes | ~8 |
| Rules fired | R1 (x1), R2 (x2), R3 (x2), R4 (x2) |

---

## Branch Coverage Summary

| Section | Branch | Demonstrated At |
|---------|--------|-----------------|
| **Section 2** | Non-persistent reset | Not shown (persistent=True) |
| **Section 3** | Static node fact | t=0: infected(Alice) |
| **Section 3** | Non-static node fact | t=0: susceptible(Bob/Carol) |
| **Section 3** | Fact rescheduling | t=0→t=1: infected(Alice) |
| **Section 4** | Edge fact application | Not shown (no edge facts) |
| **Section 5** | Node rule application | t=0: quarantine(Alice) |
| **Section 5** | Edge rule - edge_l != '' | t=1: exposure edges (R4) |
| **Section 5** | Edge rule - edge_l == '' | Not shown |
| **Section 6** | delta_t=0 inner loop | t=0: R1, t=1: R3 |
| **Section 6** | Parallel grounding | All rules grounded in parallel |
| **Section 7** | perfect_convergence | t=2: max times reached |

---

## Key Takeaways

1. **Fixed-point loop**: Rules with `delta_t=0` cause immediate re-grounding within the same timestep until no new rules fire.

2. **Static facts**: Persist across timesteps (rescheduled) but never update interpretations - only recorded in trace.

3. **Rule scheduling**: Rules are grounded → scheduled for `t + delta_t` → applied at that timestep.

4. **Edge inference**: Rules with `infer_edges=True` and a head label create new edges via `_add_edges()`, then update all created edges with the bound.

5. **Convergence**: `perfect_convergence` waits until `t >= max(max_facts_time, max_rules_time)` to ensure all scheduled work is complete.

6. **Parallelization**: Rules are grounded in parallel using thread-safe lists, then merged after the parallel loop completes.
