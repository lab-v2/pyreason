# PyReason Theory Glossary

This glossary maintains definitions of logical and theoretical concepts encountered during the PyReason codebase analysis.

---

## L - Labels and Predicates

### Label (Predicate Identifier)
**Definition:** In annotated logic and knowledge graph systems, a label is a symbolic identifier that names a relationship or attribute. Labels form the basic vocabulary of the logical language—they define *what kinds* of facts can be expressed.

In graph-based reasoning:
- **Node labels** identify properties of entities (e.g., `"infected"`, `"vaccinated"`)
- **Edge labels** identify relationships between entities (e.g., `"friends"`, `"contacts"`)

Labels are distinct from the *truth values* attached to facts (which are Intervals). A fact like `Person(John) : [0.8, 1.0]` has:
- **Label**: `Person`
- **Subject**: `John`
- **Annotation**: `[0.8, 1.0]`

**PyReason Implementation:** The `Label` class (`scripts/components/label.py`) is a simple wrapper around a string value, providing equality, hashing, and string representation. Unlike `Interval`, it has no Numba integration—labels are resolved at graph-construction time, not during hot inference loops.

**References:** `scripts/components/label.py:1-21`

---

## I - Interval-Valued Logic & Annotated Logic

### Interval-Valued Truth
**Definition:** In classical propositional logic, truth values are binary: True (1) or False (0). Interval-valued logic extends this to represent partial knowledge or uncertainty about truth using closed intervals [lower, upper] where 0 ≤ lower ≤ upper ≤ 1.

- **[0, 0]**: Definitely false
- **[1, 1]**: Definitely true
- **[0, 1]**: Complete uncertainty (could be true or false)
- **[0.6, 0.8]**: Partial belief (truth value somewhere between 60% and 80%)

**PyReason Implementation:** The `Interval` class (`scripts/interval/interval.py`) stores bounds as `l` (lower) and `u` (upper) float64 fields.

**References:** `scripts/interval/interval.py:6-91`

---

### Annotated Logic
**Definition:** A generalization of classical logic where propositions carry additional semantic information (annotations) beyond just true/false. The annotations can represent confidence, source provenance, temporal validity, or uncertainty bounds.

**PyReason Implementation:** Uses interval annotations to track degrees of belief. The interval [lower, upper] is the annotation attached to each logical fact or predicate.

**Theoretical Foundation:** Related to Bilattice theory and Belnap's four-valued logic, extended to continuous intervals.

**References:** Entire PyReason system architecture

---

## T - Temporal & Non-Monotonic Reasoning

### Temporal Reasoning
**Definition:** Logical reasoning that explicitly models how truth values change over discrete timesteps. Facts that are true at time T may become false at time T+1 (non-monotonic).

**PyReason Implementation:**
- `prev_lower` and `prev_upper` fields track previous interval values
- `has_changed()` method detects temporal evolution
- `reset()` method advances timestep by saving current state

**References:** `scripts/interval/interval.py:27-33, 41-45, 56-60`

---

### Static vs. Dynamic Facts
**Definition:**
- **Static Facts**: Knowledge that remains constant across all timesteps (e.g., "Paris is in France")
- **Dynamic Facts**: Knowledge that can change over time (e.g., "Room temperature is 72°F")

**PyReason Implementation:** Boolean `static` field (`s`) in Interval class. Static intervals should not have their bounds modified during reasoning.

**References:** `scripts/interval/interval.py:22-23, 48-53`

---

## S - Set Operations on Intervals

### Interval Intersection
**Definition:** For intervals I₁ = [l₁, u₁] and I₂ = [l₂, u₂], the intersection is:
- I₁ ∩ I₂ = [max(l₁, l₂), min(u₁, u₂)] if this forms a valid interval
- Empty set (∅) if max(l₁, l₂) > min(u₁, u₂)

**Semantic Meaning:** Finding the most restrictive common bound when combining evidence from multiple sources. If two sources provide conflicting intervals, the intersection finds where they agree.

**PyReason Implementation:** `intersection()` method computes this, BUT returns [0,1] for empty intersections instead of signaling contradiction.

**References:** `scripts/interval/interval.py:63-69`

---

## N - Numba JIT Compilation

### Numba StructRef (Recommended Pattern)
**Definition:** Numba's newer mechanism (~0.51+) for creating JIT-compiled struct-like objects. The Python class inherits from `structref.StructRefProxy`, making the Python object and native struct share the same memory layout.

**Characteristics:**
- Python object IS the native struct (zero-copy)
- Mutations in JIT code are visible in Python
- Less boilerplate (~50 lines for a typical type)
- More "Pythonic" API

**PyReason Implementation:** `Interval` uses this pattern. The class inherits from `structref.StructRefProxy`, with JIT implementations provided via `@overload_method` and `@overload_attribute` in `interval_type.py`.

**References:** `scripts/interval/interval.py`, `scripts/numba_wrapper/numba_types/interval_type.py`

---

### Numba Classic Extension (Legacy Pattern)
**Definition:** Numba's older, more explicit mechanism for extending types. Requires manually defining a Type class, Model class, and boxing/unboxing routines.

**Characteristics:**
- Python object and native struct are SEPARATE memory
- Data is COPIED when entering/exiting JIT code (@unbox/@box)
- Mutations in JIT code create new Python objects on return
- More boilerplate (~100+ lines for a typical type)
- More control over memory layout

**Key Components:**
1. `class MyType(types.Type)` - Type identity
2. `class MyModel(models.StructModel)` - Memory layout
3. `@unbox(MyType)` - Python → native conversion
4. `@box(MyType)` - Native → Python conversion
5. `@overload`/`@overload_method` - JIT implementations

**PyReason Implementation:** `Label` uses this pattern. The Python class is plain (no Numba imports), with all JIT machinery in `label_type.py`.

**References:** `scripts/components/label.py`, `scripts/numba_wrapper/numba_types/label_type.py`

**Note:** See BUG-015 for discussion of why mixing patterns is problematic.

---

### Boxing and Unboxing
**Definition:** The process of converting between Python objects and native (C-level) representations in Numba.

- **Unboxing**: Python object → native struct (entering JIT code)
- **Boxing**: Native struct → Python object (exiting JIT code)

**Relevance:** In the Classic Extension pattern, boxing/unboxing involves copying data. In StructRef, the conversion is near-zero-cost because they share memory.

**References:** `scripts/numba_wrapper/numba_types/label_type.py:86-105`

---

### Performance Rationale
Logic programs may evaluate millions of interval operations per second during fixpoint computation. JIT compilation makes this feasible by:
- Eliminating Python interpreter overhead
- Enabling SIMD vectorization
- Reducing memory allocation (structs vs objects)

---

### Numba Constructor Overloading & Type System

**The Problem:** Numba compiles Python to LLVM machine code, but Python is dynamically typed. When Numba sees `World(labels)` in JIT code, it needs to answer two questions **at compile time**:
1. **Type Inference:** What type does this constructor return?
2. **Code Generation:** What machine code should I generate to build this object?

**The Solution:** Explicit type annotations and code generation functions.

#### Two-Phase Compilation

**Phase 1: Type Inference (`@type_callable`)**
```python
@type_callable(World)
def type_world(context):
    def typer(labels):
        if isinstance(labels, types.ListType):
            return world_type  # ← "World(labels) returns WorldType"
    return typer
```
- Runs during compilation, not execution
- Tells Numba: "When you see `World(labels)`, the result type is `WorldType`"
- Enables method lookup: `w.get_bound(...)` → look for `WorldType.get_bound()`

**Phase 2: Code Generation (`@lower_builtin`)**
```python
@lower_builtin(World, types.ListType(label.label_type))
def impl_world(context, builder, sig, args):
    def make_world(labels_arg):
        d = numba.typed.Dict.empty(...)
        for lab in labels_arg:
            d[lab] = interval.closed(0.0, 1.0)
        w = World(labels_arg, d)  # ← Calls 2-arg constructor
        return w

    w = context.compile_internal(builder, make_world, sig, args)
    return w
```
- Generates LLVM IR (machine code) to actually construct the object
- `context.compile_internal()` compiles the Python function `make_world` to native code
- Returns an LLVM value representing the constructed World struct

#### Why Two Constructors?

**1-arg: `World(labels)` - User-Facing API**
- Normal usage in Python or JIT code
- Creates empty dict, initializes all labels to [0, 1]
- Internally delegates to 2-arg constructor

**2-arg: `World(labels, world)` - Internal Optimization**
- Used during boxing (native → Python conversion)
- Accepts pre-built dict to avoid reconstruction
- Critical for performance: when returning World from JIT to Python, the dict already exists in memory

**Why not just rebuild the dict?**
```python
# Inefficient (what would happen without 2-arg constructor):
def box_world(native_world):
    labels = convert_to_python(native_world.labels)
    # Rebuild dict from scratch - SLOW!
    world_dict = {}
    for label in labels:
        world_dict[label] = native_world.world[label]  # Copy every entry
    return World(labels)  # Calls 1-arg, creates ANOTHER dict!

# Efficient (actual implementation with 2-arg):
def box_world(native_world):
    labels = convert_to_python(native_world.labels)
    world_dict = convert_to_python(native_world.world)  # Direct conversion
    return World(labels, world_dict)  # Reuse existing dict
```

#### Function Overloading Pattern

Numba supports multiple signatures for the same function via decorator stacking:

```python
@type_callable(World)
def type_world(context):
    def typer(labels, world):  # ← 2-arg signature
        if isinstance(labels, types.ListType) and isinstance(world, types.DictType):
            return world_type
    return typer

@type_callable(World)  # ← Same decorator, different signature
def type_world(context):  # ← Name collision (intentional but confusing)
    def typer(labels):  # ← 1-arg signature
        if isinstance(labels, types.ListType):
            return world_type
    return typer
```

When Numba sees `World(...)`:
1. Check argument count and types
2. Match against registered `typer` functions
3. Use the matching signature

**Note:** The function name collision (`type_world` defined twice) is intentional but non-Pythonic. Numba only cares about the decorator, not the function name. Many codebases use `# ruff: noqa: F811` to suppress redefinition warnings.

#### Complete Example: What Happens During Compilation

```python
@numba.njit
def create_world():
    labels = [Label("infected"), Label("healthy")]
    w = World(labels)  # ← Trace this line
    return w.get_bound(Label("infected"))
```

**Compile Time:**
1. **Type Inference Phase:**
   - See `World(labels)` where `labels : ListType(LabelType)`
   - Call `@type_callable(World)` → match 1-arg typer
   - Return `world_type`
   - Conclusion: `w : WorldType`

2. **Code Generation Phase:**
   - Need code for `World(labels)`
   - Call `@lower_builtin(World, ListType(...))` → match 1-arg implementation
   - Generate LLVM IR:
     ```llvm
     ; Pseudocode LLVM
     %dict = call @dict_empty()
     %len = call @list_length(%labels)
     for i in range(%len):
         %label = call @list_getitem(%labels, i)
         %interval = call @interval_closed(0.0, 1.0)
         call @dict_setitem(%dict, %label, %interval)
     %world = call @World_2arg_constructor(%labels, %dict)
     ```

3. **Method Lookup:**
   - See `w.get_bound(Label("infected"))`
   - Know `w : WorldType`
   - Look up `@overload_method(WorldType, 'get_bound')`
   - Generate code for method call

**Runtime:**
- CPU executes compiled machine code
- No Python interpreter overhead
- Direct memory access to struct fields

#### References
- Type System: `scripts/numba_wrapper/numba_types/world_type.py:33-46`
- Constructors: `scripts/numba_wrapper/numba_types/world_type.py:66-88`
- Boxing: `scripts/numba_wrapper/numba_types/world_type.py:134-144`

---

## Q - Quantified Logic & Thresholds

### Threshold (Quantified Rule Activation)
**Definition:** In first-order logic, quantifiers like ∀ (forall) and ∃ (exists) operate over entire domains. In threshold logic, we use **counting quantifiers** to specify that a rule activates only when a sufficient number or percentage of entities satisfy a condition.

**Classical Logic:**

- ∀ neighbors are infected → become infected (ALL must be infected)

**Threshold Logic:**

- ≥3 neighbors are infected → become infected (at least 3)
- ≥60% of neighbors are infected → become infected (percentage-based)

**PyReason Implementation:** The `Threshold` class (`scripts/threshold/threshold.py`) is a simple data container with three fields:

- `quantifier`: Comparison operator (`"greater_equal"`, `"less"`, `"equal"`, etc.)
- `quantifier_type`: 2-tuple `(count_mode, scope_mode)` where:
  - `count_mode`: `"number"` (absolute count) or `"percent"` (percentage)
  - `scope_mode`: `"total"` (all entities) or `"available"` (only entities with predicate defined)
- `thresh`: Numeric threshold value

**References:** `scripts/threshold/threshold.py:1-42`

---

### Threshold Lifecycle (Call Stack)

Thresholds flow through PyReason in two phases: **configuration** (Python objects) and **execution** (JIT-compiled tuples).

**Phase 1: Configuration (Python-land)**
```
User Code
  ↓
Threshold("greater_equal", ("percent", "total"), 60)  ← Object instantiation
  ↓
Rule(custom_thresholds=[threshold])
  ↓
rule_parser.parse_rule()  [scripts/utils/rule_parser.py:12]
  ↓
threshold.to_tuple() → ("greater_equal", ("percent", "total"), 60)  [line 163, 169]
  ↓
Store in numba.typed.List[Tuple]  [line 151]
```

**Phase 2: Execution (JIT-compiled hot loop)**
```
[Hot Loop] check_node_grounding_threshold_satisfaction(threshold=tuple)
           [scripts/interpretation/interpretation.py:1305]
  ↓
Extract: threshold[1][1] → "total" or "available"  [line 1306]
  ↓
Calculate denominator:
  - "total": len(grounding) = ALL entities
  - "available": len(get_qualified_node_groundings(...)) = entities with predicate defined
  ↓
[Hot Loop] _satisfies_threshold(neigh_len, qualified_neigh_len, threshold)  [line 1414]
  ↓
Extract: threshold[0] → quantifier, threshold[1][0] → count_mode, threshold[2] → thresh
  ↓
Boolean: Does this grounding satisfy the rule clause?
```

**Key Insight:** Threshold objects exist only during rule parsing. Once converted to tuples, they are evaluated millions of times per second in JIT-compiled code. This is why there's no `threshold_type.py` - thresholds are serialized before hitting performance-critical code.

**References:**
- Parsing: `scripts/utils/rule_parser.py:151-177`
- Evaluation: `scripts/interpretation/interpretation.py:1305-1440`

---

### "total" vs "available" Quantifier Types

The second element of `quantifier_type` determines which entities count toward the denominator in percentage/number calculations.

**"total" (Closed-World Assumption):**

- Denominator = ALL entities in the grounding (entire domain)
- Entities without the predicate defined count as failures
- Use when: Absence of information = false

**Example:**
```python
# Graph: Person A has neighbors B, C, D, E, F
# vaccinated(B): [1.0, 1.0], vaccinated(C): [0.0, 0.0]
# vaccinated(D, E, F): NOT DEFINED

Threshold("greater_equal", ("percent", "total"), 40)
# Denominator = 5 (all neighbors: B, C, D, E, F)
# Qualified = 1 (only B is vaccinated ≥ [0.8, 1.0])
# Result: 1/5 = 20% → Rule does NOT fire
```

**"available" (Open-World Assumption):**

- Denominator = Only entities where the predicate is defined with interval [0,1]
- Entities without the predicate are excluded from calculation
- Use when: Only count entities with known information

**Example:**
```python
# Same graph as above
Threshold("greater_equal", ("percent", "available"), 40)
# Denominator = 2 (only B, C have `vaccinated` defined)
# Qualified = 1 (only B is vaccinated ≥ [0.8, 1.0])
# Result: 1/2 = 50% → Rule FIRES
```

**Implementation:**
```python
# scripts/interpretation/interpretation.py:1306-1312
if threshold_quantifier_type == 'total':
    neigh_len = len(grounding)  # ALL entities
elif threshold_quantifier_type == 'available':
    neigh_len = len(get_qualified_node_groundings(
        interpretations_node, grounding, clause_label,
        interval.closed(0, 1)  # Filter for ANY defined interval
    ))
```

**Use Cases:**

- **"total"**: "If ≥50% of ALL students pass, class average is good" (students without grades = failures)
- **"available"**: "If ≥80% of TESTED patients are healthy, outbreak contained" (untested patients ignored)

**References:** `scripts/interpretation/interpretation.py:1305-1316, 1392-1399`

---

### Query (Knowledge Base Retrieval)
**Definition:** A query is a pattern specification for retrieving facts from the knowledge base. It combines a predicate, component (entity or entity pair), and optional bounds to filter which facts match.

**Theoretical Foundation:**

In formal logic and database theory, queries are **patterns** that match against stored data:

- **Prolog queries**: `?- infected(X), contact(X, alice)` (unification-based)
- **Database queries**: `SELECT * FROM facts WHERE predicate='infected' AND bounds ⊆ [0.8, 1.0]`
- **PyReason queries**: `Query("infected(alice) : [0.8, 1.0]")` (predicate + component + bounds filter)

**Query Semantics:**

A query specifies three dimensions of matching:
1. **Predicate filter**: Which predicate to match (`infected`, `vaccinated`, etc.)
2. **Component filter**: Which entities to match (node: `alice` or edge: `(alice, bob)`)
3. **Bounds filter**: Which interval range to accept ([0.8, 1.0] matches facts with bounds within this range)

**Example:**
```python
# Match: "Is Alice infected with high confidence?"
Query("infected(alice) : [0.8, 1.0]")

# Matches if knowledge base contains:
# infected(alice) : [0.9, 1.0]  ✓ Within bounds
# infected(alice) : [0.5, 0.7]  ✗ Outside bounds
```

---

### Query Negation
**Definition:** The `~` prefix in a query represents "absence of belief" or "explicitly false" knowledge. Negated queries match facts with bounds [0, 0], indicating certainty that the predicate is false.

**Syntax:**
```python
Query("~infected(alice)")  # Match if infected(alice) : [0, 0]
```

**Semantics:**
- **Positive query**: `infected(alice)` → defaults to [1, 1] (definitely true)
- **Negated query**: `~infected(alice)` → defaults to [0, 0] (definitely false)
- Negation changes the default bounds from "complete certainty true" to "complete certainty false"

**Logical Interpretation:**
- Classical logic: `¬infected(alice)` (boolean negation)
- PyReason: `infected(alice) : [0, 0]` (interval-valued negation)
- Represents **certain absence** of the property

**Implementation:**
- Detected by checking if `query[0] == '~'` (parser line 14-16)
- Sets bounds to `Interval(0, 0)`
- **BUG-090**: Only works without explicit bounds - `~pred(x) : [0.5, 0.7]` silently ignores negation

**Contrast with Uncertainty:**
```python
Query("infected(alice) : [0, 0]")     # Explicitly query for "definitely false"
Query("~infected(alice)")             # Same as above (negation sugar)
Query("infected(alice) : [0.4, 0.6]") # Query for "uncertain" (no negation needed)
```

---

### Component Type Classification
**Definition:** PyReason distinguishes between two types of graph components that predicates can apply to:

1. **Node (Unary Predicate)**: Property of a single entity
   - Example: `infected(alice)` - Alice has the property "infected"
   - Syntax: Single identifier in parentheses
   - Internal representation: String component

2. **Edge (Binary Predicate)**: Relationship between two entities
   - Example: `friend(alice, bob)` - Alice and Bob have the "friend" relationship
   - Syntax: Two identifiers separated by comma
   - Internal representation: Tuple component `(source, target)`

**Automatic Type Detection:**

The parser infers component type from syntax:
```python
# Node detection (no comma):
"infected(alice)"      → component = "alice", comp_type = "node"

# Edge detection (has comma):
"friend(alice, bob)"   → component = ("alice", "bob"), comp_type = "edge"
```

**Implementation:**
```python
# query_parser.py:28-32
if ',' in component:
    component = tuple(component.split(','))
    comp_type = 'edge'
else:
    comp_type = 'node'
```

**Theoretical Significance:**

This mirrors first-order logic arity:
- **Unary predicates**: P(x) - properties of individuals
- **Binary predicates**: R(x, y) - relations between individuals
- PyReason restricts to unary and binary (no ternary or higher-arity predicates)

**Graph Structure:**
- Nodes store unary facts: `infected(alice) : [0.8, 1.0]`
- Edges store binary facts: `friend(alice, bob) : [1.0, 1.0]`

**BUG-091**: Simple comma detection is fragile - node names with commas (e.g., `"Alice, Jr"`) are misclassified as edges.

---

### Query Default Bounds
**Definition:** When a query does not specify explicit bounds, the system uses default intervals based on whether the query is positive or negated.

**Default Bound Rules:**

1. **Positive query (no negation, no bounds)**:
   ```python
   Query("infected(alice)")
   # Defaults to: infected(alice) : [1, 1]
   # Matches facts with "complete certainty true"
   ```

2. **Negated query (has ~, no explicit bounds)**:
   ```python
   Query("~infected(alice)")
   # Defaults to: infected(alice) : [0, 0]
   # Matches facts with "complete certainty false"
   ```

3. **Explicit bounds (overrides defaults)**:
   ```python
   Query("infected(alice) : [0.6, 0.9]")
   # Uses specified bounds [0.6, 0.9]
   ```

**Rationale:**

Default [1, 1] for positive queries reflects **certainty semantics**:
- "Is Alice infected?" implicitly asks "Is Alice definitely infected?"
- Without bounds, user expects to match facts with high confidence
- Matches classical boolean queries where `infected(alice)` means "definitely infected"

**Semantic Subtlety:**

```python
# Different queries, different meanings:
Query("infected(alice)")           # Match if DEFINITELY infected [1,1]
Query("infected(alice) : [0, 1]")  # Match if ANY evidence of infection [0,1]
Query("infected(alice) : [0.5, 1]")# Match if LIKELY infected (≥50%)
```

**Implementation:**
```python
# query_parser.py:9-16
if query[0] == '~':
    lower, upper = 0, 0  # Negated default
else:
    lower, upper = 1, 1  # Positive default

# Lines 20-22: Override if explicit bounds provided
if ':' in pred_comp:
    # Parse and use explicit bounds
```

---

### Semantic Query Equivalence
**Definition:** Two queries are **semantically equivalent** if they match the same facts in the knowledge base, regardless of their string representation or internal parsing details.

**Current Limitation (BUG-094):**

PyReason's `Query` class does not implement semantic equality:
```python
q1 = Query("infected(alice) : [1.0, 1.0]")
q2 = Query("infected(alice)")  # Defaults to [1, 1] - semantically identical

q1 == q2  # False! Different objects, different query_text strings
```

**Semantic Equivalence Rules:**

Two queries should be equal if they have identical:
1. **Predicate**: Same `Label` value
2. **Component**: Same entity (node) or entity pair (edge)
3. **Component type**: Both node or both edge
4. **Bounds**: Same interval (accounting for defaults)

**Examples of Semantic Equivalence:**

```python
# These should all be equal (after space normalization):
Query("infected(alice)")
Query("infected( alice )")
Query("infected(alice) : [1, 1]")  # Explicit default bounds

# These should be equal (negation equivalence):
Query("~infected(alice)")
Query("infected(alice) : [0, 0]")

# These are NOT equal (different bounds):
Query("infected(alice) : [0.8, 1.0]")
Query("infected(alice) : [1.0, 1.0]")
```

**Why Semantic Equality Matters:**

1. **Caching**: Store query results without duplicate computation
   ```python
   query_cache = {q1: result}  # Need __hash__ and __eq__
   ```

2. **Deduplication**: Avoid processing identical queries
   ```python
   queries = {Query("infected(alice)"), Query("infected(alice)")}
   len(queries)  # Should be 1, but currently 2 without proper equality
   ```

3. **Testing**: Compare query objects in assertions
   ```python
   assert parsed_query == expected_query  # Currently fails
   ```

**Proper Implementation (Conceptual):**

```python
class Query:
    def __eq__(self, other):
        return (self.predicate == other.predicate and
                self.component == other.component and
                self.comp_type == other.comp_type and
                self.bounds == other.bounds)

    def __hash__(self):
        return hash((self.predicate, self.component,
                     self.comp_type, tuple(self.bounds)))
```

**References:**
- BUG-094: `BUG_LOG.md` (missing semantic equality)
- Current implementation: `scripts/query/query.py:4-36`

---

### Query API and Usage
**Definition:** The `Query` class is the user-facing API for specifying what facts to retrieve from the PyReason knowledge base during or after reasoning.

**Usage Pattern:**

```python
import pyreason as pr

# After reasoning completes:
query = pr.Query("infected(alice) : [0.8, 1.0]")
result = pr.query(query)  # Retrieve matching facts

# Result: List of facts matching the pattern
# [{'component': 'alice', 'predicate': 'infected', 'bounds': [0.9, 1.0], ...}]
```

**Constructor:**
```python
Query(query_text: str)
# Parses: predicate(component) : [lower, upper]
# Stores: predicate, component, comp_type, bounds
```

**Encapsulation (Over-engineered):**

The class uses Java-style getter methods instead of Pythonic attributes:
```python
# Current API (verbose):
query.get_predicate()     # Returns Label
query.get_component()     # Returns str or tuple
query.get_component_type()# Returns 'node' or 'edge'
query.get_bounds()        # Returns Interval

# More Pythonic (not implemented):
query.predicate
query.component
query.comp_type
query.bounds
```

**Design Inconsistency (BUG-093):**

Other PyReason classes use direct attribute access:
- `Interval.lower`, `Interval.upper` (not `get_lower()`)
- `Label.value` (not `get_value()`)
- `Threshold.quantifier` (not `get_quantifier()`)

But `Query` uses double-underscore name mangling (`__pred`) with getters, creating an inconsistent API.

**Immutability:**

Queries are effectively immutable (no setters):
- Good for caching and hashing
- Prevents accidental modification
- Reflects query as a **specification**, not mutable state

**Theoretical Role:**

Queries bridge the gap between:
1. **Symbolic specification**: User-friendly syntax `"infected(alice) : [0.8, 1.0]"`
2. **Internal representation**: Parsed components (Label, component, Interval)
3. **Knowledge base retrieval**: Pattern matching against stored facts

**References:**
- Implementation: `scripts/query/query.py:4-36`
- Parser: `scripts/utils/query_parser.py:5-34`
- BUG-093: Over-engineered encapsulation
- BUG-094: Missing semantic equality

---

### Query Lifecycle and Usage Patterns

The Query object has **two distinct usage patterns** in PyReason, serving different purposes at different stages of the reasoning process:

#### 1. Pre-Reasoning: Ruleset Filtering (Performance Optimization)

**Location:** `pyreason.py:678, 772-776` and `scripts/utils/filter_ruleset.py`

When you call `pr.reason(timesteps=10, queries=[...])`, the queries are used to **filter the ruleset before reasoning begins**:

```python
# pyreason.py:772-776
if queries is not None:
    __rules = ruleset_filter.filter_ruleset(queries, __rules)
```

**How Filtering Works:**

`filter_ruleset.py` implements a recursive dependency analysis:
1. Takes `List[Query]` and extracts predicates using `q.get_predicate()`
2. Finds all rules whose head matches the query predicate
3. Recursively finds rules that support those rules (transitive closure)
4. Returns a subset of rules, ignoring irrelevant ones

**Purpose:** Performance optimization - only reason about rules relevant to your queries. If you're only interested in `infected` predicates, ignore rules about `vaccinated`, `age`, etc.

**Example from tests:**
```python
queries = [Query('friend(A, B)')]
interpretation = pr.reason(timesteps=1, queries=queries)
# Only rules involving 'friend' predicate are evaluated
```

**Design Note:** The filtering only uses `get_predicate()`, suggesting it could have been simpler. Full query parsing (component, bounds) happens at construction time but is wasted if only filtering.

---

#### 2. Post-Reasoning: Result Validation (Query API)

**Location:** `scripts/interpretation/interpretation.py:741-780`

After reasoning completes, the `Interpretation` object has a `.query()` method that checks if a query is satisfied:

```python
# interpretation.py:741
def query(self, query, return_bool=True) -> Union[bool, Tuple[float, float]]:
```

**Implementation uses ALL Query getters:**
```python
comp_type = query.get_component_type()  # 'node' or 'edge'
component = query.get_component()       # 'A' or ('A', 'B')
pred = query.get_predicate()            # Label object
bnd = query.get_bounds()                # Interval object
```

**Query Evaluation Logic:**

1. **Check if component exists** in the graph (node or edge)
   ```python
   if comp_type == 'node':
       if component not in self.nodes:
           return False if return_bool else (0, 1)
   ```

2. **Check if predicate exists** in the interpretation for that component
   ```python
   if pred not in self.interpretations_node[component].world:
       return False if return_bool else (0, 1)
   ```

3. **Check if bounds satisfy the query** using Interval's `__contains__`
   ```python
   if self.interpretations_node[component].world[pred] in bnd:
       return True if return_bool else (actual_lower, actual_upper)
   ```

4. **Return result** (boolean or actual bounds)

**Example from tests:**
```python
interpretation = pr.reason(timesteps=1)
assert interpretation.query(Query('Processed(A)'), return_bool=True)
assert interpretation.query(Query('union_probability(A, B) : [0.21, 1]'))

# Can also return bounds instead of boolean:
bounds = interpretation.query(Query('infected(alice)'), return_bool=False)
# Returns: (0.9, 1.0) if satisfied, (0, 0) if not
```

---

#### Comparison of Two Usage Patterns

| Aspect | Pre-Reasoning Filtering | Post-Reasoning Validation |
|--------|------------------------|---------------------------|
| **When** | Before reasoning starts | After reasoning completes |
| **Purpose** | Optimize performance | Check results |
| **Parameter** | `pr.reason(queries=[...])` | `interpretation.query(...)` |
| **Location** | `pyreason.py:772-776`, `filter_ruleset.py` | `interpretation.py:741-780` |
| **Getters used** | Only `get_predicate()` | All getters (predicate, component, comp_type, bounds) |
| **Input** | `List[Query]` | Single `Query` |
| **Output** | Filtered ruleset | Boolean or bounds tuple |
| **Optimization** | Reduces rules to evaluate | N/A |
| **Validation** | N/A | Checks if fact exists with bounds |

---

#### Key Insights

**Why two different uses?**
- **Pre-reasoning filtering** is a performance optimization - reduces computational cost by eliminating irrelevant rules before expensive grounding
- **Post-reasoning querying** is the user-facing API for inspecting results and validating hypotheses

**Design implications:**
- The verbose getters (`get_predicate()`, etc.) are partially justified - `interpretation.query()` needs all query components
- However, `filter_ruleset.py` only uses `get_predicate()`, suggesting the design could be simplified
- Full query parsing happens at construction time, which is wasteful if only the predicate is needed for filtering

**Questions raised:**
1. Should pre-filtering use a simpler query representation (just predicate names as strings)?
2. Why parse the full query (component, bounds, etc.) if pre-filtering only uses the predicate?
3. Could `interpretation.query()` work directly with parsed tuples instead of a Query wrapper?

**Architectural observation:**
The Query class serves as a **unifying interface** for two completely different operations (filtering and validation), which explains its somewhat over-engineered design. It's trying to be general-purpose for multiple use cases.

**References:**
- Pre-reasoning filtering: `pyreason.py:772-776`, `scripts/utils/filter_ruleset.py:1-34`
- Post-reasoning validation: `scripts/interpretation/interpretation.py:741-780`
- Test examples: `tests/api_tests/test_pyreason_reasoning.py:189-196`, `tests/functional/test_advanced_features.py:80-107`

---

## I - Interpretation (Reasoning Engine)

### Interpretation Class
**Definition:** The core reasoning engine of PyReason. An `Interpretation` object encapsulates the entire state of a knowledge graph reasoning session, including the graph structure, current truth value assignments (worlds), provenance traces, and all configuration parameters that control reasoning behavior.

**Theoretical Role:**

In formal logic, an **interpretation** (or model) is a mapping from logical formulas to truth values in a specific domain. PyReason's `Interpretation` class extends this concept to:

1. **Temporal Logic**: Manages truth values across multiple timesteps
2. **Annotated Logic**: Truth values are intervals [lower, upper], not binary
3. **Dynamic Graphs**: Graph topology can change during reasoning
4. **Provenance**: Maintains complete audit trail of all inferences

**Architecture:**

The `Interpretation` class acts as the **reasoning context** that bridges:
- **Input**: Graph structure, facts, rules
- **Process**: Fixed-point iteration, rule grounding, interval updates
- **Output**: Final interpretation (truth assignments), provenance traces

**Location:** `scripts/interpretation/interpretation.py:54-114`

---

### Interpretation Constructor Parameters

The `__init__` method takes **12 configuration parameters** that control all aspects of reasoning behavior:

#### 1. `graph` (NetworkX Graph)
**Purpose:** The knowledge graph structure (nodes and edges) that reasoning operates over.

**Type:** NetworkX DiGraph or Graph object

**What it contains:**
- Nodes: Entities in the domain (e.g., `"Alice"`, `"Bob"`, `"Server1"`)
- Edges: Relationships between entities (e.g., `("Alice", "Bob")`)
- Node/edge attributes: Predicates attached to components (e.g., `graph.nodes["Alice"]["infected"] = [0.8, 1.0]`)

**Usage:**
- Extracted into Numba-typed lists: `self.nodes`, `self.edges` (lines 99-102)
- Neighbor structure built from graph: `self.neighbors` (lines 108-112)
- Specific labels extracted from graph attributes

**Why needed:** Defines the domain entities and relationships that rules operate over.

---

#### 2. `ipl` (Inconsistent Predicate List)
**Purpose:** List of predicate pairs that cannot both be true simultaneously. Enforces logical consistency constraints.

**Type:** List of tuples `[(Label, Label), ...]`

**Example:**
```python
ipl = [(Label("infected"), Label("healthy"))]
# If infected:[0.8,1.0], then healthy must be [0.0,0.2] (complement)
```

**Theoretical foundation:** **Inverse Predicate Law (IPL)** - if predicate P has interval [l, u], then its inverse ¬P must have interval [1-u, 1-l].

---

### IPL Enforcement Logic (Detailed Explanation)

The IPL enforces **logical consistency** between predicates that are **mutually exclusive and exhaustive** (complements). When you update one predicate in a complement pair, the system automatically updates the other to maintain the mathematical relationship between them.

#### The Complement Relationship

In interval-valued logic, if two predicates P1 and P2 are complements:
- **P2 = ¬P1** (P2 is the negation of P1)
- The negation of interval [a, b] is interval **[1-b, 1-a]**

**Why flip the bounds?**
- Lower certainty that P1 is true = Higher certainty that P1 is false (¬P1 is true)
- If P1 has *at least* 60% truth → ¬P1 has *at most* 40% truth (1 - 0.6)
- If P1 has *at most* 80% truth → ¬P1 has *at least* 20% truth (1 - 0.8)

#### Implementation in `_update_node()` / `_update_edge()`

**Code location:** `interpretation.py` lines 1493-1527 (node), 1599-1633 (edge)

```python
# Lines 1503-1505 (_update_node)
for p1, p2 in ipl:
    if p1 == l:  # If we just updated p1
        # Compute intersection of:
        # 1. What p2 currently is: [p2.lower, p2.upper]
        # 2. What p2 must be based on p1's negation: [1-p1.upper, 1-p1.lower]
        lower = max(world.world[p2].lower, 1 - world.world[p1].upper)
        upper = min(world.world[p2].upper, 1 - world.world[p1].lower)
        world.world[p2].set_lower_upper(lower, upper)
```

This computes the **intersection** of two constraints:
1. **What p2 currently is**: `[p2.lower, p2.upper]`
2. **What p2 must be based on p1's negation**: `[1 - p1.upper, 1 - p1.lower]`

The intersection maintains **both constraints** simultaneously.

#### Concrete Example

```
IPL: (infected, healthy)
Component: Alice

Initial state:
  infected(Alice) = [0.0, 1.0]  (completely unknown)
  healthy(Alice) = [0.0, 1.0]   (completely unknown)

Scenario 1: Update infected
  New: infected(Alice) = [0.6, 0.8]  (60-80% certain Alice is infected)

  IPL enforcement for healthy:
    Negation of infected: [1-0.8, 1-0.6] = [0.2, 0.4]

    Intersection with current healthy:
      lower = max(0.0, 0.2) = 0.2
      upper = min(1.0, 0.4) = 0.4

    Result: healthy(Alice) = [0.2, 0.4]  (20-40% certain Alice is healthy)

  Interpretation: If Alice is 60-80% infected, she must be 20-40% healthy.
                  These probabilities are complementary.
```

```
Scenario 2: Multiple updates (monotonic refinement)
  Step 1: infected(Alice) = [0.5, 0.9]
    → healthy(Alice) = [0.1, 0.5]  (via IPL)

  Step 2: healthy(Alice) = [0.2, 0.6]  (new fact)
    → IPL enforces: healthy ∈ [0.1, 0.5] ∩ [0.2, 0.6] = [0.2, 0.5]
    → Intersection narrows uncertainty

  Step 3: Update infected again: infected(Alice) = [0.6, 0.8]
    → IPL says: healthy ∈ [0.2, 0.4]
    → Current healthy: [0.2, 0.5]
    → Intersection: [max(0.2, 0.2), min(0.5, 0.4)] = [0.2, 0.4]

  Final: infected = [0.6, 0.8], healthy = [0.2, 0.4]
```

#### Why Use max/min (Intersection)?

We use **intersection** rather than **replacement** because:
1. **Monotonic refinement**: Knowledge only gets more specific, never contradicted
2. **Respect all constraints**: Both the current belief and the IPL constraint must hold
3. **Convergence**: Intervals can only narrow, ensuring the system reaches a fixed point

#### Real-World Intuition

Think of it like evidence accumulation:
- **Doctor's test says**: "60-80% chance of infection" → implies 20-40% healthy
- **Patient symptoms say**: "20-50% chance of being healthy"
- **Combined knowledge**: The overlap [0.2, 0.4] respects both pieces of evidence

The IPL ensures that when you learn something about one predicate, you automatically learn the corresponding fact about its complement. This is crucial for maintaining a **logically consistent knowledge base** where beliefs don't contradict each other.

**Key insight:** **Negation flips and reverses the interval**, and **intersection maintains all constraints**.

---

**Usage:**
- Automatically enforced in `_update_node()` / `_update_edge()` (lines 1493-1527, 1599-1633)
- Every update to a predicate triggers automatic updates to all its IPL complements
- Used in `resolve_inconsistency_node()` / `resolve_inconsistency_edge()` to reset complements during conflict resolution (lines 1816-1831, 1851-1866)

**Why needed:** Ensures logical coherence (e.g., can't be both infected AND healthy with high confidence).

---

#### 3. `annotation_functions` (Tuple of Functions)
**Purpose:** Registry of user-defined functions that compute rule head intervals from body clause intervals.

**Type:** Tuple of Numba-compiled functions with signature `(annotations, weights) -> (lower, upper)`

**Example:**
```python
annotation_functions = (max_fn, min_fn, average_fn, custom_fn)
```

**Usage:**
- Stored as tuple for Numba compatibility
- Looked up by name during rule application (line 1768-1771 in interpretation.py)
- Called via `numba.objmode` to compute dynamic intervals

**Why needed:** Enables flexible annotation aggregation strategies (max, min, weighted average, custom logic).

**See also:** Annotation Function glossary entry for detailed semantics.

---

#### 4. `head_functions` (Tuple of Functions)
**Purpose:** Registry of user-defined functions that compute rule head variables (entities) from body variable bindings.

**Type:** Tuple of Numba-compiled functions

**Example:**
```python
# Head function: cluster(hash(X,Y)) <- connected(X,Y)
head_functions = (hash_fn, identity_fn, concat_fn)
```

**Usage:**
- Stored as tuple for Numba compatibility
- Looked up by name during rule grounding
- Called to compute derived entity identifiers

**Why needed:** Enables dynamic entity creation and graph transformation during reasoning.

**See also:** Head Functions glossary entry for detailed semantics.

---

#### 5. `reverse_graph` (bool)
**Purpose:** If True, enables reverse graph traversal (successor → predecessor lookups).

**Type:** Boolean

**Usage:**
- Controls whether `reverse_neighbors` dictionary is populated and maintained
- Used for rules that require backward edge traversal

**Why needed:** Some reasoning patterns require traversing edges in reverse (e.g., "all parents of infected children").

---

#### 6. `atom_trace` (bool)
**Purpose:** If True, records detailed provenance of which ground atoms (variable bindings) satisfied each rule firing.

**Type:** Boolean

**Impact:**
- Enables: `rule_trace_node_atoms`, `rule_trace_edge_atoms` (lines 93-94)
- Records: For each rule firing, which specific entities matched each clause

**Example trace:**
```python
# Rule: infected(X) <- contact(X,Y), infected(Y)
# Fired with: X=Alice, Y=Bob
# Atom trace: ([['Alice']], [['Alice','Bob']], [0.9,1.0], "infection_rule")
```

**Tradeoff:**
- ✅ **Complete provenance**: Can explain every inference
- ❌ **Memory cost**: Significant overhead for large graphs
- ❌ **Performance cost**: Extra list operations per rule firing

**Why needed:** Debugging, explainability, audit trails, understanding why conclusions were reached.

---

#### 7. `save_graph_attributes_to_rule_trace` (bool)
**Purpose:** If True, includes graph attribute facts in provenance traces (not just rules).

**Type:** Boolean

**Impact:**
- Controls whether initial graph labels are recorded in `rule_trace_node/edge`
- Graph attributes are facts loaded from the graph structure itself

**Tradeoff:**
- ✅ **Complete trace**: Shows all truth value sources (facts + rules)
- ❌ **Noise**: Graph attributes often static and obvious

**Why needed:** Distinguish between inferred facts (from rules) vs. asserted facts (from graph).

---

#### 8. `persistent` (bool)
**Purpose:** If True, truth values persist across timesteps. If False, interpretations reset to initial state at each timestep.

**Type:** Boolean

**Semantics:**
- **persistent=True**: Monotonic reasoning - once derived, facts remain (classical logic programming)
- **persistent=False**: Non-monotonic reasoning - facts can disappear between timesteps (temporal logic)

**Implementation:** Lines 246-259 in `reason()` - resets all non-static intervals if `not persistent`

**Example:**
```python
# persistent=True:
# t=0: infected(Alice):[0.8,1.0]
# t=1: infected(Alice):[0.8,1.0] (persists)
# t=2: infected(Alice):[0.9,1.0] (can only increase)

# persistent=False:
# t=0: infected(Alice):[0.8,1.0]
# t=1: infected(Alice):[0.0,1.0] (reset to uncertain)
# t=2: infected(Alice) re-derived based on t=2 facts only
```

**Why needed:** Models different reasoning paradigms (persistent knowledge vs. episodic snapshots).

---

#### 9. `inconsistency_check` (bool)
**Purpose:** If True, detects and resolves inconsistent fact/rule applications (conflicting intervals). If False, uses override semantics.

**Type:** Boolean

**Behavior:**
- **True**: Calls `resolve_inconsistency_node/edge()` when multiple facts conflict
- **False**: Uses `override=True` in updates (later facts override earlier)

**Example conflict:**
```python
# Two facts fire at same timestep:
# Fact1: infected(Alice):[0.9,1.0]
# Fact2: infected(Alice):[0.0,0.2]

# inconsistency_check=True: Detects conflict, resolves (how?)
# inconsistency_check=False: Fact2 overrides Fact1 (last wins)
```

**Why needed:** Choose between strict consistency enforcement vs. pragmatic override semantics.

---

#### 10. `store_interpretation_changes` (bool)
**Purpose:** If True, records all interpretation changes to provenance traces. If False, skips trace updates (performance optimization).

**Type:** Boolean

**Impact:**
- Controls whether `rule_trace_node/edge` are populated
- Disabling saves memory and time for large-scale reasoning

**Tradeoff:**
- ✅ **Performance**: Significant speedup when disabled
- ❌ **No provenance**: Can't explain reasoning, no audit trail

**Why needed:** Production deployments may not need traces; development/debugging does.

---

#### 11. `update_mode` (str: 'override' | 'intersection')
**Purpose:** Controls how new intervals are combined with existing intervals during updates.

**Type:** String enum

**Semantics:**
- **'override'**: New interval replaces old (non-monotonic)
  ```python
  old: [0.5, 0.7]
  new: [0.8, 1.0]
  result: [0.8, 1.0]  # Replace
  ```

- **'intersection'**: New interval intersects with old (monotonic refinement)
  ```python
  old: [0.5, 0.9]
  new: [0.7, 1.0]
  result: [0.7, 0.9]  # Intersection
  ```

**Implementation:** Checked at lines 301, 375, 430, etc. in `reason()` to set `override` parameter for `_update_node/edge()`

**Why needed:** Different reasoning tasks require different update semantics (accumulation vs. replacement).

---

#### 12. `allow_ground_rules` (bool)
**Purpose:** If True, permits rules with no variables (ground facts in rule form). If False, such rules are errors.

**Type:** Boolean

**Example ground rule:**
```python
# No variables - always fires unconditionally
infected(Alice) <- vaccinated(Bob)
```

**Why needed:** Some use cases treat rules as conditional facts; others require true logical variables.

---

### Interpretation Instance Variables

The `__init__` method creates **16+ instance variables** organized by purpose:

#### Graph Structure (4 variables)
- `self.nodes` (List[str]): All node identifiers in the graph
- `self.edges` (List[Tuple[str,str]]): All edge tuples in the graph
- `self.neighbors` (Dict[str, List[str]]): Forward adjacency list (node → successors)
- `self.reverse_neighbors` (Dict[str, List[str]]): Reverse adjacency list (node → predecessors)

**Purpose:** Enable efficient graph traversal during rule grounding.

---

#### Interpretation State (2 variables)
- `self.interpretations_node` (Dict[str, World]): Maps each node to its World (predicate → interval)
- `self.interpretations_edge` (Dict[Tuple[str,str], World]): Maps each edge to its World

**Structure:**
```python
interpretations_node = {
    "Alice": World({Label("infected"): [0.8, 1.0], Label("vaccinated"): [1.0, 1.0]}),
    "Bob": World({Label("infected"): [0.0, 0.2], Label("vaccinated"): [0.0, 0.0]})
}
```

**Purpose:** The core reasoning state - current truth values for all predicates on all components.

---

#### Predicate Reverse Index (2 variables)
- `self.predicate_map_node` (Dict[Label, List[str]]): Maps each predicate to nodes that have it
- `self.predicate_map_edge` (Dict[Label, List[Tuple]]): Maps each predicate to edges that have it

**Structure:**
```python
predicate_map_node = {
    Label("infected"): ["Alice", "Bob", "Charlie"],
    Label("vaccinated"): ["Alice", "Dave"]
}

predicate_map_edge = {
    Label("infected"): [("Alice","Bob"), ("Carol","Dave")],
    Label("knows"): [("Alice","Carol")]
}
```

---

### Understanding predicate_map: The Reverse Index Explained

#### Primary Data Structure: interpretations

The **primary** way PyReason stores truth values is:

```python
interpretations[component].world[label] = interval

# Examples:
interpretations['Alice'].world[Label('infected')] = [0.6, 0.8]
interpretations['Bob'].world[Label('healthy')] = [0.2, 0.4]
interpretations[('Alice','Bob')].world[Label('knows')] = [0.9, 1.0]
```

**Query direction:** Given a **component**, find what **labels** it has.

```python
"What predicates does Alice have?"
→ Look up interpretations['Alice'].world.keys()
→ Returns: [Label('infected'), Label('age'), ...]
```

#### Reverse Index: predicate_map

The **reverse index** flips this around:

```python
predicate_map[label] = [list of components that have this label]

# Examples:
predicate_map[Label('infected')] = ['Alice', 'Bob', ('Carol','Dave')]
predicate_map[Label('healthy')] = ['Eve', 'Frank']
predicate_map[Label('knows')] = [('Alice','Bob'), ('Bob','Carol')]
```

**Query direction:** Given a **label**, find what **components** have it.

```python
"Which components have the 'infected' predicate?"
→ Look up predicate_map[Label('infected')]
→ Returns: ['Alice', 'Bob', ('Carol','Dave')]
```

#### Why "Reverse"?

It's the **reverse lookup** of the primary data structure:

| Data Structure | Question | Answer |
|----------------|----------|---------|
| **Primary (interpretations)** | "Given Alice, what predicates?" | infected, healthy, age |
| **Reverse (predicate_map)** | "Given infected, what components?" | Alice, Bob, (Carol,Dave) |

#### Concrete Example

```python
# State of the world:
interpretations = {
    'Alice': World({
        Label('infected'): [0.7, 0.9],
        Label('age'): [0.3, 0.3]
    }),
    'Bob': World({
        Label('infected'): [0.2, 0.4],
        Label('healthy'): [0.6, 0.8]
    }),
    ('Alice','Bob'): World({
        Label('infected'): [0.5, 0.7]
    })
}

# Reverse index:
predicate_map = {
    Label('infected'): ['Alice', 'Bob', ('Alice','Bob')],
    Label('healthy'): ['Bob'],
    Label('age'): ['Alice']
}
```

#### Why Is This Needed? Performance!

**Problem: Rule Grounding**

When applying a rule like:
```python
infected(X) ∧ neighbor(X,Y) → infected(Y)
```

We need to find **all X where infected(X) holds**.

**Without predicate_map (SLOW):**
```python
# Must iterate ALL components (could be millions!)
infected_components = []
for component in interpretations.keys():  # O(N) where N = all components
    if Label('infected') in interpretations[component].world:
        infected_components.append(component)
```

**With predicate_map (FAST):**
```python
# Direct lookup!
infected_components = predicate_map[Label('infected')]  # O(1) lookup
```

**Performance Impact:**
```
Scenario: 10,000 nodes, 50,000 edges, 100 predicates
Rule: infected(X) → process(X)

Without predicate_map:
  - Check all 60,000 components
  - Time: O(60,000) = 60,000 operations

With predicate_map:
  - Lookup predicate_map[Label('infected')]
  - Returns: [Alice, Bob, Carol]  (only 3 infected!)
  - Time: O(1) lookup + O(3) iteration = 4 operations

Speedup: 60,000 / 4 = 15,000x faster!
```

#### How It's Maintained

Every time we add or remove a label from a component, we update **both** structures:

**Adding a Label** (from `_add_edge` lines 1899-1902):
```python
# Update primary structure
interpretations_edge[edge].world[l] = interval.closed(0, 1)

# Update reverse index
if l in predicate_map:
    predicate_map[l].append(edge)  # Add edge to existing list
else:
    predicate_map[l] = numba.typed.List([edge])  # Create new list
```

**Removing a Label** (from `_delete_edge` lines 1937-1939):
```python
# Update primary structure
del interpretations_edge[edge]

# Update reverse index
for l in predicate_map:
    if edge in predicate_map[l]:
        predicate_map[l].remove(edge)  # Remove edge from list
```

#### Two Separate predicate_maps

PyReason maintains **two** reverse indexes:

```python
predicate_map_node[label] = [list of NODES with this label]
predicate_map_edge[label] = [list of EDGES with this label]
```

**Why separate?**
- Nodes and edges have different types (str vs tuple)
- Rules specify whether they're querying nodes or edges
- Keeps lookups type-safe and efficient

**Example:**
```python
predicate_map_node[Label('infected')] = ['Alice', 'Bob']
predicate_map_edge[Label('infected')] = [('Alice','Bob'), ('Carol','Dave')]
```

#### Visual Summary

```
PRIMARY DATA STRUCTURE (interpretations):
Component → Labels → Intervals

    Alice → infected: [0.7, 0.9]
         → age: [0.3, 0.3]

    Bob → infected: [0.2, 0.4]
        → healthy: [0.6, 0.8]

REVERSE INDEX (predicate_map):
Label → Components

    infected → [Alice, Bob, (Alice,Bob)]
    healthy → [Bob]
    age → [Alice]
```

#### Used In

- **`_ground_rule()`** (Layer 8, lines 784-1226): Primary use case - find components matching rule clauses
- **`get_rule_node_clause_grounding()`** (Layer 7A, lines 1335-1342): Lookup nodes with predicate
- **`get_rule_edge_clause_grounding()`** (Layer 7A, lines 1345-1389): Lookup edges with predicate
- **`_update_node()` / `_update_edge()`** (Layer 5): Update index when adding labels
- **`_delete_node()` / `_delete_edge()`** (Layer 6): Update index when removing components

**Key Insight:** "Reverse index" means it indexes the data in the **reverse direction** from the primary structure - instead of "component → labels", it's "label → components". This makes rule grounding extremely fast.

---

#### Scheduled Actions (6 variables)
- `self.rules_to_be_applied_node` (List[Tuple]): Rules that will fire for nodes at future timesteps
- `self.rules_to_be_applied_edge` (List[Tuple]): Rules that will fire for edges at future timesteps
- `self.facts_to_be_applied_node` (List[Tuple]): Facts to apply to nodes at future timesteps
- `self.facts_to_be_applied_edge` (List[Tuple]): Facts to apply to edges at future timesteps
- `self.edges_to_be_added_node_rule` (List[Tuple]): Edges to create from node rules (infer_edges)
- `self.edges_to_be_added_edge_rule` (List[Tuple]): Edges to create from edge rules (infer_edges)

**Purpose:** Implement temporal rules (delta_t) - schedule actions for future timesteps.

---

#### Provenance Traces (6 variables)
- `self.rule_trace_node` (List[Tuple]): Records every interval change for nodes (timestep, fp_cnt, component, predicate, interval)
- `self.rule_trace_edge` (List[Tuple]): Records every interval change for edges
- `self.rule_trace_node_atoms` (List[Tuple]): Records ground atoms that satisfied rules for nodes (if atom_trace=True)
- `self.rule_trace_edge_atoms` (List[Tuple]): Records ground atoms that satisfied rules for edges
- `self.rules_to_be_applied_node_trace` (List[Tuple]): Provenance for scheduled node rules
- `self.rules_to_be_applied_edge_trace` (List[Tuple]): Provenance for scheduled edge rules

**Purpose:** Complete audit trail - can reconstruct entire reasoning process step-by-step.

---

#### Reasoning Metadata (3 variables)
- `self.num_ga` (List[int]): Number of ground atoms at each timestep (for performance tracking)
- `self.time` (int): Current timestep (for resuming reasoning)
- `self.prev_reasoning_data` (List[int]): Previous timestep and fixed-point counter (for resuming)

**Purpose:** Support incremental reasoning (call `reason()` multiple times without resetting).

---

### Class Variables (2)
- `specific_node_labels` (Dict[Label, List[str]]): Global map of specific node labels (shared across all Interpretation instances)
- `specific_edge_labels` (Dict[Label, List[edge]]): Global map of specific edge labels

**Purpose:** Cache node/edge labels extracted from graph structure for efficient reuse.

**Note:** These are **class-level**, not instance-level - shared state across all Interpretation objects.

---

### Interpretation Lifecycle

**1. Construction:**
```
User → pr.reason() → Interpretation(graph, ipl, ...) → __init__
```

**2. Initialization:**
```
__init__ → Extract graph structure (nodes, edges, neighbors)
       → Initialize interpretations (World for each component)
       → Initialize predicate maps (reverse indexes)
       → Initialize empty trace lists
```

**3. Reasoning:**
```
start_fp() → reason() [main loop]
          → Apply facts
          → Ground rules
          → Apply rules
          → Check convergence
          → Repeat until converged or max timesteps
```

**4. Query:**
```
User → interpretation.query(Query(...))
    → Lookup component in interpretations
    → Return interval or boolean
```

**5. Export:**
```
User → interpretation.get_dict()
    → Convert Numba structures to Python dicts
    → Return serializable result
```

---

### References
- Constructor: `scripts/interpretation/interpretation.py:58-114`
- Initialization helpers: Lines 118-168 (_init_reverse_neighbors, _init_interpretations_node/edge)
- Main reasoning loop: Lines 228-660 (reason() function)
- Query interface: Lines 741-781 (query() method)

---

## W - World & Knowledge States

### World (Interpretation / Valuation)
**Definition:** In formal logic, a **world** (or **interpretation** / **valuation**) is a complete mapping from propositions to truth values. In modal and temporal logic, different "possible worlds" represent different states of knowledge or different points in time.

**Kripke Semantics:**
- Developed by Saul Kripke for modal logic
- A "world" represents a snapshot of all knowledge at a specific moment
- Relations between worlds define modalities (necessity, possibility, temporal succession)
- Formula truth is evaluated *relative to* a world

**In PyReason:**
A World maps predicates (Labels) to their current truth bounds (Intervals):
```
World = Dict[Label, Interval]

Example at timestep T=5:
{
  infected:    [0.8, 1.0],  # Highly likely infected
  vaccinated:  [1.0, 1.0],  # Definitely vaccinated
  healthy:     [0.0, 0.2]   # Unlikely healthy
}
```

**PyReason Implementation:** The `World` class (`scripts/components/world.py`) is a thin wrapper around `numba.typed.Dict[Label, Interval]`:

**Constructor:**
- Takes a list of `Label` objects
- Initializes all predicates to `[0.0, 1.0]` (complete uncertainty / "unknown")

**Core Operations:**
- `is_satisfied(label, interval)`: Check if `world[label]` ⊆ `interval`
- `update(label, interval)`: Refine bounds via intersection: `world[label] ∩= interval`
- `get_bound(label)`: Query current interval for a predicate

**Monotonicity:**
The `update()` method uses intersection, which means bounds can only **narrow** over time, never widen. This implements a monotonic refinement of knowledge - once you know something is at least [0.8, 1.0], you can't later decide it's [0.0, 1.0].

**Temporal Reasoning:**
In PyReason's fixpoint iteration:
- Each timestep operates on a World
- Rules fire and update intervals via `world.update()`
- Fixpoint convergence occurs when no more updates occur (all intervals stable)
- `Interval.reset()` advances to next timestep

**Two-Constructor Pattern:**
`World` has an unusual dual-constructor architecture:
1. **Python constructor**: `World(labels)` - creates dict internally
2. **Internal constructor**: `make_world(labels, world)` - accepts pre-built dict

The second constructor exists for **Numba boxing** (native → Python conversion). When JIT-compiled code returns a World to Python, the boxing machinery calls `make_world(labels, world)` to avoid rebuilding the dict.

**References:** `scripts/components/world.py:1-52`, `scripts/numba_wrapper/numba_types/world_type.py`

---

## H - Horn Clauses & Logic Programming

### Horn Clause
**Definition:** A logical formula in disjunctive form with at most one positive literal. In logic programming, Horn clauses take the form:
```
head ← body₁ ∧ body₂ ∧ ... ∧ bodyₙ
```
Where:
- **head**: Single positive literal (what we conclude)
- **body**: Conjunction of literals (conditions that must be satisfied)
- If all body conditions are true, the head becomes true

**Logical Equivalence:**
```
A ← B ∧ C   ≡   A ∨ ¬B ∨ ¬C   (disjunctive form)
```

**Special Cases:**
- **Fact**: Horn clause with empty body (always true): `infected(Alice) ←`
- **Query**: Horn clause with empty head: `← infected(X), contact(X,Y)`
- **Rule**: Horn clause with both head and body: `infected(X) ← contact(X,Y), infected(Y)`

**PyReason Implementation:**
Rules are parsed from text format `"head <- body1, body2, ..."` where:
- Head can have fixed interval: `infected(X):[0.6,0.9] <- ...`
- Head can have annotation function: `infected(X):max <- ...`
- Body clauses can have intervals: `contact(X,Y):[1,1], infected(Y):[0.8,1]`
- Commas represent conjunction (AND)

**Theoretical Foundation:**
Horn clauses are fundamental to:
- Prolog (entire language based on Horn logic)
- Datalog (Horn clauses without function symbols)
- Answer Set Programming (extends Horn logic with negation)
- Logic Programming (Horn clause resolution)

**References:** `scripts/utils/rule_parser.py:12-322`

---

### Rule Grounding
**Definition:** The process of substituting variables in a rule with concrete constants to produce specific fact instances. A rule with variables is called a **rule schema**, and each substitution creates a **ground instance**.

**Example:**
```
Rule schema:
  infected(X) ← contact(X,Y), infected(Y)

Groundings (given domain: {Alice, Bob, Charlie}):
  infected(Alice) ← contact(Alice,Bob), infected(Bob)
  infected(Alice) ← contact(Alice,Charlie), infected(Charlie)
  infected(Bob) ← contact(Bob,Alice), infected(Alice)
  infected(Bob) ← contact(Bob,Charlie), infected(Charlie)
  infected(Charlie) ← contact(Charlie,Alice), infected(Alice)
  infected(Charlie) ← contact(Charlie,Bob), infected(Bob)
```

**Grounding Space Complexity:**
For a rule with k variables over domain of size n:
- Maximum groundings: O(n^k)
- Example: 2 variables, 1000 entities = 1,000,000 ground instances

**PyReason Implementation:**
- Rules are stored as schemas with variables (strings like "X", "Y")
- During reasoning, the engine iterates over graph entities to find matching groundings
- Threshold logic determines how many groundings must satisfy conditions
- Ground instances are evaluated against current world state (interval annotations)

**References:**
- Rule structure: `scripts/utils/rule_parser.py:206-207` (head_variables)
- Clause variables: `scripts/utils/rule_parser.py:128-140` (body_variables)

---

### Head Functions (Computed Predicates)
**Definition:** In classical Datalog and Prolog, rule heads contain only variables or constants. Head functions extend this by allowing **function calls** in the head arguments, enabling derived predicates where the entities receiving conclusions are computed dynamically from body variables rather than directly bound.

**Theoretical Foundation:**

Classical logic programming (Prolog, Datalog) operates on **Herbrand interpretations** where predicates apply to ground terms (constants or function-free compound terms). Head functions extend this to **function-valued logic**, where:

1. **Body grounding** binds variables to constants as usual
2. **Head evaluation** applies user-defined functions to transform grounded values
3. **Derived terms** become the subjects of the head predicate

This bridges **symbolic reasoning** (predicate logic) with **computation** (arbitrary functions), similar to:
- **Functional logic programming** (e.g., Curry language)
- **Constraint logic programming** with computed domains
- **Prolog's findall/bagof** aggregation primitives

**Contrast with Standard Grounding:**

```
Standard rule (direct variable binding):
  infected(X) ← contact(X,Y), infected(Y)

  Body matches: contact(Alice, Bob), infected(Bob)
  Head fires for: infected(Alice)  ← X is directly bound to Alice

Head function rule (computed binding):
  cluster_infected(hash(X,Y)) ← contact(X,Y), infected(Y)

  Body matches: contact(Alice, Bob), infected(Bob)
  Head fires for: cluster_infected(hash(Alice, Bob))  ← Function computes entity
```

**PyReason Syntax:**

```python
# Node rule with head function
predicate(function_name(arg1, arg2, ...)) ← body

# Edge rule with head function in first position
predicate(function_name(arg1), Y) ← body

# Edge rule with head function in second position
predicate(X, function_name(arg1)) ← body

# Edge rule with functions in BOTH positions
predicate(f(arg1), g(arg2, arg3)) ← body
```

**Parsing and Representation:**

When the parser encounters a function call in the head (e.g., `f(X,Y)`), it creates:

- **head_variables**: `['__temp_var_N']` - Placeholder for function result
- **head_fns**: `['f']` - Function name to call during execution
- **head_fns_vars**: `[['X','Y']]` - Variables to pass as arguments

For mixed heads like `predicate(f(A), B)`:
- **head_variables**: `['__temp_var_0', 'B']`
- **head_fns**: `['f', '']` - Second position has no function (empty string)
- **head_fns_vars**: `[['A'], []]`

**Execution Flow:**

1. **Body grounding**: Variables bind to constants (standard unification)
2. **Function lookup**: Find registered user function by name in `head_fns[i]`
3. **Argument extraction**: Collect grounded values for variables in `head_fns_vars[i]`
4. **Function call**: Execute user function with arguments (via `numba.objmode`)
5. **Head instantiation**: Use function result as the entity for the head predicate

**Example: Identity Function**

```python
# Define head function (must be @numba.njit decorated)
@numba.njit
def identity_func(arg_lists):
    """Returns the first grounded value unchanged."""
    result = numba.typed.List([arg_lists[0][0]])
    return result

# Register with PyReason
pr.add_head_function(identity_func)

# Use in rule
pr.add_rule(pr.Rule(
    'Processed(identity_func(X)) ← property(X), connected(X,Y)',
    'node_rule'
))

# Execution:
# Body matches: property(Alice), connected(Alice, Bob)
# Function called: identity_func([['Alice']])
# Returns: ['Alice']
# Head fires: Processed(Alice)
```

**Example: Edge Rule with Dual Functions**

```python
@numba.njit
def first_char(arg_lists):
    """Extract first character of node name."""
    node = arg_lists[0][0]
    return numba.typed.List([node[0]])

pr.add_head_function(first_char)

pr.add_rule(pr.Rule(
    'Route(first_char(X), first_char(Y)) ← connected(X,Y)',
    'edge_route'
))

# Execution:
# Body matches: connected(Alice, Bob)
# first_char([['Alice']]) → ['A']
# first_char([['Bob']]) → ['B']
# Head fires: Route(A, B)
```

**Use Cases:**

1. **Aggregation**: Group entities into clusters
   ```python
   cluster(hash(X,Y,Z)) ← related(X,Y), related(Y,Z)
   ```

2. **Derived identifiers**: Compute new entity names
   ```python
   meeting(concat(person1, person2)) ← schedules_overlap(person1, person2)
   ```

3. **Graph transformations**: Map nodes to abstract structures
   ```python
   layer(compute_layer(X)) ← in_network(X), depth(X,D)
   ```

4. **Type conversions**: Transform entity representations
   ```python
   normalized(to_lowercase(X)) ← entity(X)
   ```

**Critical Distinction: Head Functions vs Annotation Functions**

These are **completely orthogonal** concepts:

| Aspect | Head Functions | Annotation Functions |
|--------|---------------|---------------------|
| **What they compute** | Which entities get the predicate | What interval those entities receive |
| **When they execute** | During grounding (determines targets) | After grounding (determines bounds) |
| **Syntax** | `pred(f(X))` | `pred(X):max` |
| **Input** | Variable groundings | Clause intervals |
| **Output** | Node/edge identifiers | Interval bounds |
| **Field** | `head_fns`, `head_fns_vars` | `ann_fn` |

**Example combining both:**

```python
# Rule with BOTH head function AND annotation function
cluster_risk(hash(X,Y)):max ← contact(X,Y), infected(X), infected(Y)

# Execution:
# 1. Body grounds: X=Alice, Y=Bob
# 2. Head function: hash(Alice, Bob) → "cluster_42"
# 3. Annotation function: max(infected(Alice), infected(Y)) → [0.9, 1.0]
# 4. Result: cluster_risk(cluster_42) gets interval [0.9, 1.0]
```

**Theoretical Significance:**

Head functions elevate PyReason beyond traditional Datalog by enabling:
- **Computed domains**: Entities can be generated, not just selected
- **Non-monotonic entity creation**: New nodes/edges emerge from reasoning
- **Functional abstraction**: Logic rules can construct abstract representations
- **Hybrid reasoning**: Seamless integration of symbolic logic with procedural computation

This makes PyReason closer to **functional logic programming** languages while maintaining the declarative semantics of Horn clause reasoning.

**Implementation References:**
- Parsing: `scripts/utils/rule_parser.py:119-120, 221-287` (head argument parsing)
- Grounding: `scripts/interpretation/interpretation.py:2000-2037` (node head vars)
- Grounding: `scripts/interpretation/interpretation.py:2041-2082` (edge head vars)
- Execution: `scripts/interpretation/interpretation.py:2085-2107` (function calls)
- Storage: `scripts/rules/rule_internal.py:34-35` (head_fns, head_fns_vars fields)
- Examples: `tests/functional/test_advanced_features.py:60-79`

---

## A - Annotation Functions (Extended)

### Annotation Function (Rule Heads)
**Definition:** Instead of assigning a fixed interval to the rule head, an annotation function computes the output interval based on the intervals of satisfied body clauses. This enables dynamic, data-driven inference.

#### Theoretical Foundations

**Annotation Aggregation (Belief Revision):**

In annotated logic, when multiple rules fire and infer the same predicate with different truth values, we need a principled way to combine them. This is the **belief revision** or **annotation aggregation** problem:

```
Example: If Rule₁ says infected(X): [0.6, 0.8]
         and Rule₂ says infected(X): [0.7, 0.9]
         What's the final annotation for infected(X)?
```

**Fuzzy Logic Operators:**

Annotation functions implement classical fuzzy logic operators for combining evidence:

1. **S-norm (Maximum) - Optimistic Disjunction**
   - **Semantics**: "Take the strongest evidence"
   - **Use case**: Rules represent alternative explanations
   - **Example**: `infected(X) ← contact(X,Y), infected(Y)` OR `infected(X) ← sneeze(X)`
   - **Logic**: If either fires strongly, take max
   - **Mathematical**: `μ_A∪B(x) = max(μ_A(x), μ_B(x))`

2. **T-norm (Minimum) - Pessimistic Conjunction**
   - **Semantics**: "Only as strong as the weakest link"
   - **Use case**: All evidence must align (conservative)
   - **Example**: Diagnosis requires multiple confirming tests
   - **Logic**: Take minimum to handle conflicting evidence
   - **Mathematical**: `μ_A∩B(x) = min(μ_A(x), μ_B(x))`

3. **Average - Compromise Aggregation**
   - **Semantics**: "Balance all evidence equally"
   - **Use case**: Rules are equally trustworthy, smooth out extremes
   - **Example**: Risk assessment from multiple independent factors
   - **Mathematical**: `μ_avg(x) = (1/n) Σ μ_i(x)`

4. **Weighted Average - Trust-Based Aggregation**
   - **Semantics**: "More reliable rules have more influence"
   - **Use case**: Rules have different confidence levels
   - **Example**: `0.8 : infected(X) ← ...` means 80% confidence in rule
   - **Mathematical**: `μ_weighted(x) = Σ(w_i · μ_i(x)) / Σ w_i`

**Interval Arithmetic:**

Operations must preserve the `[lower, upper]` structure while maintaining the invariant:
- `lower ≤ upper`
- Both bounds in `[0, 1]`
- Lower and upper bounds often processed separately
- Result intervals must remain valid (non-inverted, in range)

**Theoretical Context:**

These operators originate from:
- **Fuzzy Set Theory** (Zadeh, 1965): T-norms and S-norms as generalized AND/OR
- **Bilattice Theory** (Ginsberg, 1988): Lattice structures for truth values with knowledge/information ordering
- **Annotated Logic Programming** (Subrahmanian, 1987): Logic programs with annotations from complete lattices
- **Belief Revision** (Alchourrón, Gärdenfors, Makinson, 1985): Updating belief states with new information

**Syntax in PyReason:**
```
predicate(vars):function_name <- body1, body2, ...
```

**Contrast with Fixed Intervals:**
```
# Fixed interval (static conclusion):
infected(X):[0.7,0.9] <- contact(X,Y), infected(Y):[0.8,1]
# Always assigns [0.7,0.9] when rule fires

# Annotation function (dynamic conclusion):
infected(X):max <- contact(X,Y), infected(Y):[0.8,1]
# Assigns max([0.8,1]) when rule fires - adapts to data
```

**Common Annotation Functions:**
- `max`: Take maximum interval from body clauses
- `min`: Take minimum interval
- `mean_weight`: Weighted average based on rule weights
- Custom functions: User-defined interval computations

**Use Cases:**
- Propagating maximum confidence: "Infected if ANY contact is infected" → use `max`
- Combining evidence: "Risk level based on weighted factors" → use `mean_weight`
- Conservative reasoning: "Only conclude if ALL evidence agrees" → use `min`

**PyReason Implementation:**
- Parsed from rule head (line 100-108 in rule_parser.py)
- Stored as string in `ann_fn` field
- Default target_bound is `[0,1]` when annotation function is used
- Actual function execution happens during reasoning (not in parser)

**References:**
- Parsing: `scripts/utils/rule_parser.py:100-108`
- Storage: `rule_internal.py:12` (`_ann_fn` field)

---

### Annotation Function Registration and Execution

**CRITICAL ARCHITECTURAL FINDING:** PyReason does NOT distinguish between "built-in" and "custom" annotation functions. The functions in `scripts/annotation_functions/annotation_functions.py` (`average`, `maximum`, `minimum`, `average_lower`) are **reference implementations**, not pre-registered built-ins. ALL annotation functions—whether provided by PyReason or user-defined—follow the **identical registration and lookup flow**.

#### Registration Flow (Identical for All Functions)

**Step 1: User Registration**
```python
# For "built-in" functions (must manually import and register!):
import pyreason.scripts.annotation_functions.annotation_functions as af
pr.add_annotation_function(af.average)  # NOT automatic!

# For custom functions (same API):
@numba.njit
def custom_fn(annotations, weights):
    # ... compute interval ...
    return lower, upper
pr.add_annotation_function(custom_fn)
```

Both calls append to the same module-level list: `pyreason.py:472`:
```python
__annotation_functions = []  # Empty by default!
```

**Step 2: Rule Parsing**
```python
pr.add_rule(pr.Rule('infected(X):average <- body'))
#                              ^^^^^^^^ Stored as string
```
Parser extracts `"average"` as a string identifier and stores in `rule.ann_fn` field (rule_parser.py:100-108).

**Step 3: Preparation for Reasoning**
```python
# pyreason.py:769 - Convert list to tuple for Numba
annotation_functions = tuple(__annotation_functions)
```
Passed to interpretation engine constructor.

**Step 4: Function Lookup During Reasoning**

When a rule fires, the annotation function is looked up **dynamically by name** (interpretation.py:1768-1771):

```python
# Inside Numba JIT function
func_name = rule.get_annotation_function()  # Returns "average" or "custom_fn"

with numba.objmode(annotation='Tuple((float64, float64))'):
    for func in annotation_functions:  # ← O(n) linear search!
        if func.__name__ == func_name:  # ← String comparison
            annotation = func(annotations, weights)
            break
return annotation
```

**Why `numba.objmode`?**
- Numba JIT cannot do dynamic function lookups by name
- Must temporarily exit JIT compilation to execute Python introspection
- Compares function's `__name__` attribute with stored string
- Calls matched function, returns result back to JIT context

#### Comparison: "Built-in" vs Custom Functions

| Aspect | Built-in Functions | Custom Functions |
|--------|-------------------|------------------|
| **Implementation** | `scripts/annotation_functions/annotation_functions.py` | User-defined Python functions |
| **Registration** | Manual via `add_annotation_function()` | Manual via `add_annotation_function()` |
| **Auto-available?** | ❌ NO - must explicitly add | ❌ NO - must explicitly add |
| **Lookup mechanism** | O(n) linear search by `__name__` | O(n) linear search by `__name__` |
| **Performance** | `numba.objmode` overhead | `numba.objmode` overhead |
| **Requirements** | Must be `@numba.njit` decorated | Must be `@numba.njit` decorated |
| **Signature** | `func(annotations, weights) -> (lower, upper)` | `func(annotations, weights) -> (lower, upper)` |

**Conclusion:** The "built-in" annotation functions are merely **example implementations** shipped with PyReason. They have **zero special status** in the runtime architecture. Users must import and register them just like custom functions.

#### Performance Characteristics

**O(n) Lookup Overhead:**
- With 10 registered annotation functions, every rule firing checks up to 10 name comparisons
- No caching or dictionary-based O(1) lookup
- Multiplied by every rule invocation at every timestep

**`objmode` Overhead:**
- Exiting JIT compilation for name lookup adds latency
- Function call itself is fast (Numba-compiled), but lookup is slow

**Potential Optimization:**
```python
# Current: O(n) list scan
annotation_functions = tuple([func1, func2, func3, ...])

# Better: O(1) dict lookup
annotation_functions = {
    'average': average_func,
    'maximum': maximum_func,
    'custom_fn': custom_func
}
# Lookup: annotation_functions[func_name](annotations, weights)
```

#### Design Implications

**1. No "Built-in" Privilege:**
The functions in `annotation_functions.py` are **not imported anywhere** in the main codebase:
```bash
$ grep -r "import.*annotation_functions" /workdir/pyreason/pyreason --include="*.py"
# No results outside of tests!
```

**2. User Responsibility:**
Documentation examples show users implementing their own `average` function instead of using the provided one:
```python
# From docs/examples_rst/annF_average_example.rst
@numba.njit
def avg_ann_fn(annotations, weights):
    # User re-implements average from scratch!
    sum_lower_bounds = 0
    sum_upper_bounds = 0
    num_atoms = 0
    for clause in annotations:
        for atom in clause:
            sum_lower_bounds += atom.lower
            sum_upper_bounds += atom.upper
            num_atoms += 1
    return sum_lower_bounds / num_atoms, sum_upper_bounds / num_atoms
```

**3. Validation Gap:**
If function name doesn't match any registered function, lookup **silently fails**:
- No error raised
- Returns default interval `[0, 1]`
- User gets unexpected behavior with no diagnostic

#### Theoretical Significance

This architecture reflects a **plugin-based design philosophy**:
- Annotation functions are **user-extensible primitives**, not fixed operations
- PyReason provides reference implementations as **guidance**, not requirements
- System remains open for domain-specific aggregation logic (e.g., probabilistic independence for Bayesian networks, custom fuzzy operators)

However, this creates usability friction:
- Users expect `"average"` to work automatically (it doesn't)
- No discovery mechanism for available functions
- No compile-time validation of function names

#### References
- Registration API: `pyreason.py:651-662`
- Module-level storage: `pyreason.py:472`
- Lookup implementation: `scripts/interpretation/interpretation.py:1762-1771`
- Built-in implementations: `scripts/annotation_functions/annotation_functions.py:8-101`
- Example usage: `examples/annotation_function_ex.py`
- Bug report: BUG-081 through BUG-088 (annotation_functions.py analysis)

---

## C - Convergence & Fixed-Point Semantics

### Fixed-Point Reasoning
**Definition:** The iterative process of applying rules until the knowledge base reaches a stable state where no further changes occur. This implements the **least fixed-point semantics** of logic programming.

**Theoretical Foundation:**

In logic programming (Prolog, Datalog), the semantics of a program is defined as the **least fixed-point** of a consequence operator T_P:

1. **Start with empty knowledge base**: KB₀ = ∅
2. **Apply all rules once**: KB₁ = T_P(KB₀) = {all facts derivable in one step}
3. **Repeat**: KB_{i+1} = T_P(KB_i) = KB_i ∪ {newly derived facts}
4. **Fixed point reached**: KB_n = T_P(KB_n) (no new facts can be derived)

**PyReason Adaptation:**

Classical fixed-point semantics assume **monotonic** reasoning (facts, once derived, remain true forever). PyReason extends this to **temporal, non-monotonic** reasoning:

- Facts can have different intervals at different timesteps
- Fixed-point is computed **per timestep**
- Non-persistent mode resets interpretations between timesteps

**References:** Core concept underlying `Interpretation.reason()` main loop

---

### Convergence Modes
**Definition:** PyReason supports three distinct strategies for determining when fixed-point reasoning should terminate at a given timestep. Each mode trades off between computational cost and precision guarantees.

**API Parameters:**
```python
pr.reason(
    timesteps=10,
    convergence_threshold=N,           # Delta interpretation count
    convergence_bound_threshold=epsilon # Delta bound epsilon
)
```

**Mode Selection Logic** (interpretation.py:172-182):
```python
if convergence_bound_threshold == -1 and convergence_threshold == -1:
    mode = 'perfect_convergence'
elif convergence_bound_threshold == -1:
    mode = 'delta_interpretation'  # Use convergence_threshold
else:
    mode = 'delta_bound'  # Use convergence_bound_threshold
```

---

### Mode 1: Perfect Convergence
**Theory:** True mathematical fixed-point - reasoning stops **only when** no more rules or facts can possibly fire.

**Activation:**
```python
pr.reason(
    timesteps=10,
    convergence_threshold=-1,       # Both set to -1
    convergence_bound_threshold=-1
)
```

**Convergence Criterion** (interpretation.py:648-654):
```python
if t >= max_facts_time and t >= max_rules_time:
    break  # No more facts/rules scheduled to fire
```

**Semantics:**
- `max_facts_time`: Latest timestep where any fact is scheduled to apply
- `max_rules_time`: Latest timestep where any rule (via delta_t) is scheduled to fire
- If current timestep exceeds both, **no future changes are possible**

**Guarantees:**
- ✅ **Complete**: All derivable facts are computed
- ✅ **Sound**: No spurious conclusions
- ⚠️ **Expensive**: May iterate many times even after practical convergence

**Example:**
```python
# Fact: infected(Alice) at t=0
# Rule: infected(X) <- 2 contact(X,Y), infected(Y)  # Delta_t = 2
# max_facts_time = 0
# max_rules_time = 2 (last possible rule firing)
# Convergence at t=3 (after t=2 rule fires)
```

**Use Cases:**
- Safety-critical reasoning: Must guarantee all conclusions reached
- Small knowledge bases: Overhead is minimal
- Debugging: Verify complete rule firing
- Theoretical correctness: Match formal semantics

---

### Mode 2: Delta Interpretation (Change Count)
**Theory:** Approximate convergence by monitoring **how many** interpretations changed during the timestep. If changes drop below threshold, assume near-convergence.

**Activation:**
```python
pr.reason(
    timesteps=10,
    convergence_threshold=5,        # Stop if ≤5 changes
    convergence_bound_threshold=-1  # Disable bound delta
)
```

**Convergence Criterion** (interpretation.py:631-637):
```python
if changes_cnt <= convergence_delta:
    print(f'Converged with {int(changes_cnt)} changes')
    break
```

**Changes Tracked:**
- `changes_cnt` increments by 1 for **each** interpretation (node or edge predicate) that had its interval modified
- Updated after every `_update_node()` / `_update_edge()` call (lines 306-309, 320-323, etc.)

**Example:**
```python
# Timestep t=5:
# - infected(Alice): [0.7,0.9] → [0.8,1.0]  (changed, changes_cnt += 1)
# - infected(Bob):   [0.5,0.7] → [0.6,0.8]  (changed, changes_cnt += 1)
# - healthy(Alice):  [0.0,0.3] → [0.0,0.3]  (unchanged, no increment)
# - vaccinated(Bob): [1.0,1.0] → [1.0,1.0]  (unchanged, no increment)
# Total: changes_cnt = 2

# If convergence_threshold = 5:
#   2 ≤ 5 → Converged!
```

**Semantics:**
- **Changes count** = number of (component, predicate) pairs whose intervals were refined
- Does NOT measure magnitude of change, only binary "changed vs unchanged"
- Setting threshold=0 requires **zero** changes (equivalent to perfect convergence in practical terms)

**Tradeoffs:**
- ✅ **Fast**: Stops early if activity slows down
- ✅ **Practical**: Works well when most inferences converge quickly
- ⚠️ **Incomplete**: May miss inferences that would occur in later iterations
- ⚠️ **Parameter tuning**: Threshold value is domain-dependent (need to experiment)

**Use Cases:**
- Large knowledge bases: Can't afford perfect convergence
- Approximate reasoning: "Close enough" results acceptable
- Iterative refinement: Multiple reasoning calls with increasing thresholds
- Performance-critical: Real-time systems, need bounded latency

**Parameter Guidance:**
- `threshold=0`: Strictest (near-perfect convergence)
- `threshold=1-10`: Tight (most inferences likely complete)
- `threshold=50-100`: Loose (early termination, may miss conclusions)

---

### Mode 3: Delta Bound (Maximum Epsilon Change)
**Theory:** Approximate convergence by monitoring the **magnitude** of interval changes. If the largest interval change drops below epsilon, assume numerical stability.

**Activation:**
```python
pr.reason(
    timesteps=10,
    convergence_threshold=-1,          # Disable change count
    convergence_bound_threshold=0.01   # Stop if max change ≤ 0.01
)
```

**Convergence Criterion** (interpretation.py:638-644):
```python
if bound_delta <= convergence_delta:
    print(f'Converged with {float_to_str(bound_delta)} max change')
    break
```

**Bound Delta Tracked:**
- `bound_delta` = max(all interval changes during timestep)
- Updated as `bound_delta = max(bound_delta, changes)` after each update (lines 307, 321, etc.)
- `changes` returned by `_update_node()` / `_update_edge()` is the **maximum** of lower and upper bound changes

**Example:**
```python
# Timestep t=8:
# - infected(Alice): [0.80,0.90] → [0.82,0.91]
#     lower_change = |0.82 - 0.80| = 0.02
#     upper_change = |0.91 - 0.90| = 0.01
#     changes = max(0.02, 0.01) = 0.02
#     bound_delta = max(bound_delta, 0.02)
#
# - infected(Bob): [0.60,0.75] → [0.605,0.755]
#     lower_change = |0.605 - 0.60| = 0.005
#     upper_change = |0.755 - 0.75| = 0.005
#     changes = max(0.005, 0.005) = 0.005
#     bound_delta = max(bound_delta, 0.005) = 0.02 (no update)
#
# Total: bound_delta = 0.02

# If convergence_bound_threshold = 0.01:
#   0.02 > 0.01 → Continue reasoning
# If convergence_bound_threshold = 0.05:
#   0.02 ≤ 0.05 → Converged!
```

**Semantics:**
- **Bound delta** = max over all interval changes: max(|new_lower - old_lower|, |new_upper - old_upper|)
- Measures **numerical stability** rather than logical completeness
- Epsilon must be chosen based on domain (scales with interval magnitudes)

**Tradeoffs:**
- ✅ **Numerically stable**: Good for scientific computing, probabilistic reasoning
- ✅ **Insensitive to count**: Doesn't matter if 1 or 1000 predicates changed, only magnitude
- ⚠️ **Incomplete**: Small changes may still be logically significant
- ⚠️ **Scale-dependent**: Epsilon choice depends on interval ranges (0-1 vs 0-100)

**Use Cases:**
- Probabilistic reasoning: Convergence when probabilities stabilize
- Continuous domains: Sensor data, physical simulations
- Iterative approximation: Numerical methods where epsilon-convergence is standard
- Gradient-based learning: Similar to gradient descent stopping criterion

**Parameter Guidance:**
- `threshold=0.001`: Tight (high precision)
- `threshold=0.01`: Standard (1% change tolerance)
- `threshold=0.1`: Loose (10% change tolerance, fast but imprecise)

---

### Convergence Mode Comparison

| Aspect | Perfect | Delta Interpretation | Delta Bound |
|--------|---------|---------------------|-------------|
| **Criterion** | No more rules/facts to fire | ≤N interpretations changed | Max interval change ≤ε |
| **Measures** | Logical completeness | Change count | Change magnitude |
| **Parameters** | Both = -1 | `convergence_threshold` | `convergence_bound_threshold` |
| **Completeness** | ✅ Guaranteed | ⚠️ Approximate | ⚠️ Approximate |
| **Performance** | ❌ Slowest | ✅ Fast | ✅ Fast |
| **Use case** | Small KBs, debugging | Large KBs, logical reasoning | Probabilistic, numerical |
| **Stops when** | t ≥ max(fact_time, rule_time) | changes_cnt ≤ threshold | bound_delta ≤ epsilon |

---

### Implementation Details

**Convergence Check Frequency:**
- Performed **once per timestep** after all facts and rules applied (lines 628-654)
- Not checked during inner loop (delta_t=0 immediate rule effects)

**Reset Between Timesteps:**
- `changes_cnt = 0` at start of each timestep (line 262)
- `bound_delta = 0` at start of each timestep (line 263)
- Convergence is **per-timestep**, not global

**Timestep Increment on Convergence:**
```python
# Consistency: Return t+1 when converged, same as non-convergence case
t += 1
break
```
This ensures returned timestep is "next timestep that would have been processed", not "last processed timestep".

**Interactions with Other Features:**
- **Non-persistent mode**: Convergence resets each timestep (interpretations reset)
- **Static facts**: Do NOT count toward changes (already immutable)
- **Graph attributes**: Counted in changes if `save_graph_attributes_to_rule_trace=True`

---

### Practical Recommendations

**When to use each mode:**

1. **Perfect Convergence**:
   - Graph has <1000 nodes/edges
   - Rules have small delta_t values (<5)
   - Correctness is more important than speed
   - Debugging rule interactions

2. **Delta Interpretation**:
   - Large graphs (>10,000 nodes/edges)
   - Complex rulesets (>100 rules)
   - Logical reasoning where "most conclusions" is sufficient
   - Set threshold to 1-5% of total predicates

3. **Delta Bound**:
   - Probabilistic reasoning (Bayesian networks, fuzzy logic)
   - Interval bounds represent measurements or confidences
   - Numerical optimization (similar to gradient descent convergence)
   - Set epsilon to acceptable precision (e.g., 0.01 = 1% error tolerance)

**Combining with timestep limit:**
- Always set `timesteps` parameter as safety bound
- Convergence acts as **early stopping** condition
- Without convergence criteria, reasoning runs for full `timesteps` iterations

---

### References
- Mode selection: `scripts/interpretation/interpretation.py:172-182`
- Perfect convergence check: `scripts/interpretation/interpretation.py:648-654`
- Delta interpretation check: `scripts/interpretation/interpretation.py:631-637`
- Delta bound check: `scripts/interpretation/interpretation.py:638-644`
- Change tracking: Throughout `reason()` function at lines 306-309, 320-323, 380-383, 394-397, etc.

---

## C - Comparison Clauses

### Comparison Clause
**Definition:** A body clause in a rule that evaluates a numeric comparison instead of a symbolic predicate. This bridges symbolic logic with arithmetic reasoning.

**Syntax:**
```
predicate(var1, var2) operator value
```

**Supported Operators** (from rule_parser.py:315):
- `<=`, `>=`, `<`, `>`, `==`, `!=`

**Example Rules:**
```
# Eligible to vote if age >= 18
eligible_voter(X) <- age(X,Y), Y >= 18

# High temperature alert
alert(Sensor) <- temperature(Sensor,T), T > 100

# Exact match
calibrated(Device) <- reading(Device,R), R == 0
```

**PyReason Implementation:**
- Comparison operators detected via `_get_operator_from_clause()` (line 314-321)
- Clause type set to `'comparison'` instead of `'node'` or `'edge'` (line 182-185)
- Operator stored in clause tuple (5th element)
- Numeric evaluation happens during grounding (outside parser scope)

**Theoretical Significance:**
Comparison clauses enable **constraint logic programming** - combining:
- Symbolic reasoning (predicates over entities)
- Numeric reasoning (arithmetic constraints)

This is essential for:
- Temporal reasoning (time > threshold)
- Sensor data analysis (temperature > limit)
- Threshold-based rules (count >= minimum)

**References:**
- Detection: `scripts/utils/rule_parser.py:183-186, 314-321`
- Clause structure: `scripts/utils/rule_parser.py:190` (op field)

---

## E - Edge Inference

### Edge Inference
**Definition:** A rule mechanism that creates new graph edges as a side effect when the rule fires. This enables **dynamic graph construction** during reasoning, where the graph topology itself evolves based on logical conclusions.

**Syntax in PyReason:**
```python
Rule(rule_text, infer_edges=True)
```

**Example:**
```python
# Rule: If X and Y are both in same group, create "colleague" edge
Rule("colleague(X,Y) <- group_member(X,G), group_member(Y,G)", 
     infer_edges=True)

# Before reasoning:
#   Nodes: Alice, Bob, Charlie
#   Edges: None
#   Facts: group_member(Alice, Engineering)
#          group_member(Bob, Engineering)
#
# After reasoning:
#   New edge created: colleague(Alice, Bob)
```

**PyReason Implementation:**
- Controlled by `infer_edges` parameter in Rule constructor (rule.py:15)
- Parser checks if rule is node or edge type (line 123)
- For edge rules with `infer_edges=True`, creates edge tuple (line 194-199):
  ```python
  edges = (head_variables[0], head_variables[1], target)
  # (source_var, target_var, edge_label)
  ```
- For node rules or `infer_edges=False`: `edges = ('', '', Label(''))`
- Edge creation happens during rule evaluation in reasoning engine

**Use Cases:**
- Social network evolution: Friendships based on shared interests
- Knowledge graph completion: Inferring missing relationships
- Dynamic routing: Creating network paths based on conditions
- Temporal graphs: Edges that appear/disappear over time

**Constraints:**
- Only applicable to edge rules (2 variables in head)
- Node rules automatically set `infer_edges=False` (line 143-144)
- Edge type stored in tuple: `(var1, var2, label)` format

**References:**
- Parameter: `scripts/rules/rule.py:15` (infer_edges)
- Parsing: `scripts/utils/rule_parser.py:143-144, 194-199`
- Storage: `rule_internal.py:16` (_edges field)

---

## T - Temporal Logic (Extended)

### Temporal Rules with Delta-t
**Definition:** Rules where the body is evaluated at time t, but the head fires at time t + Δt (temporal offset). This enables reasoning about future states based on current conditions.

**Syntax in PyReason:**
```
head <- delta body1, body2, ...
       ^^^^^ Leading integer specifies temporal offset
```

**Examples:**
```
# Disease incubation: Infected 2 timesteps after exposure
infected(X) <- 2 contact(X,Y), infected(Y)
# Evaluates contact and infection at time t
# Fires infected(X) at time t+2

# Immediate rule (delta=0, default):
infected(X) <- contact(X,Y), infected(Y)
# Evaluates and fires at same timestep

# Delayed notification:
notified(X) <- 5 alert(X)
# Notification occurs 5 timesteps after alert
```

**Parsing Implementation:**
```python
# rule_parser.py lines 19-32:
t = ''
while body[0].isdigit():  # Extract leading digits
    t += body[0]
    body = body[1:]
if t == '':
    t = 0  # Default to immediate
else:
    t = int(t)
```

**Storage:**
- Stored as `delta` field (uint16) in rule structures
- Line 217: `numba.types.uint16(t)`
- BUG-067: Limited to 65,535 timesteps (uint16 overflow)

**Theoretical Use Cases:**
- **Disease modeling**: Incubation periods
- **Event causality**: Delayed effects
- **Temporal dependencies**: "X causes Y after delay"
- **Scheduling**: "Action triggers response at future time"

**References:**
- Parsing: `scripts/utils/rule_parser.py:19-32`
- Type: `scripts/numba_wrapper/numba_types/rule_type.py:50` (delta field)

---

## R - Rules & Rule Structure

### Rule (Internal Representation)
**Definition:** A PyReason rule is a Horn clause with interval annotations, temporal offsets, thresholds, and optional annotation functions. The internal representation (`rule_internal.Rule`) stores all components needed for rule evaluation during reasoning.

**General Form:**
```
target(head_vars):[bound] <- delta clauses with thresholds
```

**Example:**
```python
Rule("infected(X):[0.8,1.0] <- 2 contact(X,Y), infected(Y):[0.7,1.0]",
     name="infection_spread",
     custom_thresholds=[Threshold("greater_equal", ("number", "total"), 1)])
```

---

### Rule Fields (14 Total)

#### 1. `_rule_name` (str)
**Purpose:** Human-readable identifier for the rule, used in rule traces and debugging.

**Example:** `"infection_spread"`, `"eligibility_check"`

**Usage:** Appears in execution traces to show which rule fired at each timestep.

---

#### 2. `_type` (str: 'node' | 'edge')
**Purpose:** Specifies whether the rule head is a node predicate (1 variable) or edge predicate (2 variables).

**Determination:**
- `'node'`: Head has 1 variable → `infected(X)`
- `'edge'`: Head has 2 variables → `friend(X,Y)`

**Implementation:** Set by parser at line 123 based on `len(head_variables)`

---

#### 3. `_target` (Label)
**Purpose:** The predicate name in the rule head (what the rule concludes about).

**Example:**
```python
# Rule: infected(X) <- contact(X,Y), infected(Y)
# target = Label("infected")

# Rule: friend(X,Y) <- knows(X,Y), likes(Y,X)
# target = Label("friend")
```

**Type:** `Label` object (wraps a string predicate name)

---

#### 4. `_head_variables` (List[str])
**Purpose:** Variable names in the rule head, determining what entities the rule applies to.

**Examples:**
```python
# Node rule: infected(X)
head_variables = ['X']

# Edge rule: friend(X,Y)
head_variables = ['X', 'Y']

# Function in head: distance(f(X,Y))
head_variables = ['__temp_var_0']  # Temp variable for function result
```

**Type:** Numba-typed list of strings

---

#### 5. `_delta` (uint16)
**Purpose:** Temporal offset - number of timesteps between body evaluation and head firing.

**Examples:**
```python
# Immediate rule (delta=0, default):
infected(X) <- contact(X,Y), infected(Y)
# Body evaluated at t, head fires at t

# Delayed rule (delta=2):
infected(X) <- 2 contact(X,Y), infected(Y)
# Body evaluated at t, head fires at t+2
```

**Type:** `uint16` (0 to 65,535)
**Warning:** BUG-067 - Limited to 65,535 timesteps

---

#### 6. `_clauses` (List[Tuple])
**Purpose:** The body conditions that must be satisfied for the rule to fire.

**Structure:** Each clause is a 5-tuple:
```python
(clause_type, label, variables, interval, operator)
```

**Clause Types:**
- `'node'`: Node predicate with 1 variable
- `'edge'`: Edge predicate with 2 variables  
- `'comparison'`: Arithmetic comparison (e.g., `age(X) >= 18`)

**Example:**
```python
# Rule: infected(X) <- contact(X,Y), infected(Y):[0.8,1]
clauses = [
    ('edge', Label('contact'), ['X','Y'], Interval(0,1), ''),
    ('node', Label('infected'), ['Y'], Interval(0.8,1), '')
]

# Rule: eligible(X) <- age(X,Y), Y >= 18
clauses = [
    ('edge', Label('age'), ['X','Y'], Interval(0,1), ''),
    ('comparison', Label(''), ['Y'], Interval(18,18), '>=')
]
```

**Type:** Numba-typed list of tuples

---

#### 7. `_bnd` (Interval)
**Purpose:** The interval bound to assign to the head when the rule fires (used when no annotation function is specified).

**Examples:**
```python
# Fixed interval:
infected(X):[0.7,0.9] <- ...
# bnd = Interval(0.7, 0.9)

# Default (no bound specified):
infected(X) <- ...
# bnd = Interval(1, 1)  # Certain true

# With annotation function:
infected(X):max <- ...
# bnd = Interval(0, 1)  # Placeholder, function computes actual bound
```

**Type:** `Interval` object

---

#### 8. `_thresholds` (List[Tuple])
**Purpose:** Specifies how many body clauses must be satisfied for the rule to fire. One threshold per clause.

**Structure:** Each threshold is a 3-tuple:
```python
(quantifier, (count_mode, scope_mode), value)
```

**Default:** `("greater_equal", ("number", "total"), 1.0)` - ANY clause satisfies

**Examples:**
```python
# Default (ANY): At least 1 clause must be satisfied
[("greater_equal", ("number", "total"), 1.0)]

# ALL: All clauses must be satisfied
[("greater_equal", ("percent", "total"), 100.0)]

# Custom: At least 3 neighbors must be infected
[("greater_equal", ("number", "total"), 3.0)]

# Percentage: At least 60% must be satisfied
[("greater_equal", ("percent", "available"), 60.0)]
```

**Type:** Numba-typed list of tuples
**See also:** Threshold section in glossary for detailed semantics

---

#### 9. `_ann_fn` (str)
**Purpose:** Name of the annotation function to compute the head interval from body clause intervals. Empty string if using fixed bound.

**Common Values:**
- `''` (empty): Use fixed `_bnd` value
- `'max'`: Take maximum interval from satisfied clauses
- `'min'`: Take minimum interval
- `'mean_weight'`: Weighted average using `_weights`

**Example:**
```python
# Fixed bound:
infected(X):[0.8,1] <- ...
# ann_fn = ''

# Annotation function:
infected(X):max <- ...
# ann_fn = 'max'
```

**Type:** String (function name or empty)

---

#### 10. `_weights` (numpy.ndarray[float64])
**Purpose:** Weight for each body clause, used by weighted annotation functions to compute the head interval.

**Example:**
```python
# Rule with 3 clauses, equal weights:
weights = np.array([1.0, 1.0, 1.0])

# Custom weights (first clause more important):
Rule(..., weights=np.array([2.0, 1.0, 1.0]))

# Weighted average annotation function uses these weights
# to compute: sum(weight_i * interval_i) / sum(weights)
```

**Default:** Array of 1.0s (equal weight) with length = number of clauses
**Type:** Numpy array of float64, length = number of clauses

---

#### 11. `_head_fns` (List[str])
**Purpose:** Function names for each head variable position. Empty string if variable is not a function call.

**Example:**
```python
# Simple head: infected(X)
head_fns = ['']  # No functions

# Function in head: distance(f(X,Y), Z)
head_fns = ['f', '']  # First arg is function f, second is variable Z

# Multiple functions: relation(f(X), g(Y))
head_fns = ['f', 'g']
```

**Purpose:** Enables derived predicates where head arguments are computed from variables.

**Type:** Numba-typed list of strings

---

#### 12. `_head_fns_vars` (List[List[str]])
**Purpose:** For each function in `_head_fns`, the list of variables passed as arguments.

**Example:**
```python
# Head: distance(f(X,Y), Z)
head_fns = ['f', '']
head_fns_vars = [['X','Y'], []]  # f takes X,Y; Z takes no args (is variable)

# Head: relation(f(A,B), g(C))
head_fns = ['f', 'g']
head_fns_vars = [['A','B'], ['C']]  # f(A,B), g(C)
```

**Parsing:** Creates temporary variables `__temp_var_N` in `head_variables` for function results

**Type:** Numba-typed list of lists of strings

---

#### 13. `_edges` (Tuple[str, str, Label])
**Purpose:** Specifies edge to create when rule fires (if `infer_edges=True`). Used for dynamic graph construction.

**Structure:** 3-tuple `(source_var, target_var, edge_label)`

**Examples:**
```python
# Edge inference enabled:
Rule("friend(X,Y) <- knows(X,Y)", infer_edges=True)
# edges = ('X', 'Y', Label('friend'))
# Creates friend edge from X to Y when rule fires

# Edge inference disabled (default):
# edges = ('', '', Label(''))
```

**Constraints:**
- Only applicable to edge rules (2 variables in head)
- Node rules always have `('', '', Label(''))`

**Type:** 3-tuple of (string, string, Label)

---

#### 14. `_static` (bool)
**Purpose:** If True, atoms in the head become immutable after the rule fires once. Bounds no longer change.

**Example:**
```python
# Static rule: Once infected, always infected
Rule("infected(X) <- contact(X,Y), infected(Y)", set_static=True)
# After first firing: infected(Alice) = [0.8, 1.0] (immutable)

# Dynamic rule (default): Bounds can change over time
Rule("infected(X) <- contact(X,Y), infected(Y)")
# infected(Alice) can be updated in subsequent timesteps
```

**Use Cases:**
- Permanent properties: "Once graduated, always a graduate"
- One-shot conclusions: "Diagnosis made, cannot be unmade"
- Performance optimization: Skip re-evaluation of static facts

**Type:** Boolean
**Default:** False

---

### Rule Lifecycle

**Construction:**
```
User Code → rule.Rule(rule_text, ...) 
         → rule_parser.parse_rule(...)
         → rule_type.Rule (Numba native struct)
```

**Execution:**
```
Reasoning Engine:
  1. Ground rule variables over domain entities
  2. For each grounding, evaluate body clauses against current world
  3. Check thresholds: do enough clauses satisfy?
  4. If yes:
     - Compute head interval (fixed bound or annotation function)
     - Fire rule: update world state at timestep t + delta
     - If infer_edges: create edge
     - If static: mark head atom as immutable
```

**Boxing (Native → Python):**
```
JIT returns native rule → Numba boxing 
                       → rule_internal.Rule (Python object)
```

---

### References
- Parser: `scripts/utils/rule_parser.py:12-322`
- Python representation: `scripts/rules/rule_internal.py:1-91`
- Numba wrapper: `scripts/numba_wrapper/numba_types/rule_type.py:1-301`
- User API: `scripts/rules/rule.py:1-23`

---
