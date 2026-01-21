# PyReason Bug Log

This log tracks all code quality issues discovered during analysis. Issues are categorized by severity:

- **CRITICAL**: Must be fixed - causes incorrect behavior, type errors, or crashes
- **HIGH**: Should be fixed - significant logic errors or performance issues
- **MEDIUM**: Should be documented - questionable design choices or potential edge case bugs
- **LOW**: Nice to fix - code smell, tech debt, or minor inefficiencies

---

## `scripts/interval/interval.py`

### BUG-001: Type Inconsistency in Intersection Default Values
**Severity:** CRITICAL
**Location:** `interval.py:67-68`
**Description:**
```python
if lower > upper:
    lower = np.float32(0)  # ← Uses float32
    upper = np.float32(1)  # ← Uses float32
```
The Interval struct fields are defined as `float64` (see `interval_type.py:19-20`), but the intersection method returns `float32` values when intervals are disjoint. This causes type coercion.

**Impact:**
- Potential Numba compilation errors or warnings
- Silent type promotion overhead in tight loops
- Precision loss (float32 has ~7 decimal digits vs float64's ~15)

**Fix:**
```python
lower = np.float64(0)
upper = np.float64(1)
```

---

### BUG-002: Floating-Point Equality Comparisons
**Severity:** MEDIUM
**Location:** `interval.py:57-58, 75`
**Description:**
```python
# In has_changed():
if self.lower==self.prev_lower and self.upper==self.prev_upper:

# In __eq__():
if interval.lower==self.lower and interval.upper==self.upper:
```
Direct equality comparison on floating-point numbers is fragile due to rounding errors. Example:
```python
0.1 + 0.2 == 0.3  # May be False due to binary representation
```

**Impact:**
- `has_changed()` may incorrectly report changes when values are numerically identical but have minor rounding differences
- Could prevent fixpoint convergence in the reasoning loop
- Equality checks may fail for intervals that are semantically equal

**Fix:**
Use epsilon-based comparison:
```python
def _float_eq(a, b, epsilon=1e-9):
    return abs(a - b) < epsilon

if _float_eq(self.lower, self.prev_lower) and _float_eq(self.upper, self.prev_upper):
```

---

### BUG-003: Non-Functional `@property @njit` Decorators
**Severity:** MEDIUM
**Location:** `interval.py:10-33` (all property methods)
**Description:**
```python
@property
@njit
def lower(self):
    return self.l
```
The combination of `@property` and `@njit` is misleading:
- In JIT-compiled contexts, Numba ignores these decorators and uses the `@overload_attribute` definitions from `interval_type.py`
- In pure Python contexts, `@njit` on a property is redundant (properties aren't JIT-compiled individually)
- The `@property` decorator only works in uncompiled Python usage

**Impact:**
- Code maintainability: misleading decorators suggest functionality that doesn't exist
- Developers may incorrectly assume these are the compiled implementations
- Inconsistent behavior between Python and JIT contexts

**Fix:**
Remove `@njit` decorators from all properties in `interval.py`. The properties should remain for Python-mode usage, but the JIT implementations are correctly defined via overloads in `interval_type.py`.

---

### BUG-004: Missing Invariant Validation
**Severity:** MEDIUM
**Location:** `interval.py:7-8` (constructor)
**Description:**
The `__new__` method and `set_lower_upper()` do not validate:
- `lower <= upper` (interval validity)
- `0 <= lower, upper <= 1` (probability/truth bounds)

**Impact:**
- Invalid intervals (e.g., `[0.8, 0.2]`) can be created and propagate silently
- Out-of-range values (e.g., `[-0.5, 1.5]`) could corrupt reasoning
- Debugging becomes harder when garbage data is accepted

**Fix:**
Add validation in constructor and setters:
```python
def __new__(cls, lower, upper, s=False):
    if lower > upper:
        raise ValueError(f"Invalid interval: lower ({lower}) > upper ({upper})")
    if not (0 <= lower <= 1 and 0 <= upper <= 1):
        raise ValueError(f"Bounds must be in [0,1]: got [{lower}, {upper}]")
    ...
```

**Note:** Validation may be intentionally omitted for performance in tight loops. Consider adding a debug mode or assertion flag.

---

### BUG-005: Static Flag Ignored in Intersection
**Severity:** MEDIUM
**Location:** `interval.py:69`
**Description:**
```python
return Interval(lower, upper, False, self.lower, self.upper)
                              ^^^^^
```
The intersection result is always marked as non-static (`False`), even if both input intervals are static.

**Impact:**
- Loss of static flag information when combining static facts
- May cause unnecessary recomputation in temporal reasoning
- Semantic incorrectness: intersection of two static facts should be static

**Expected Behavior:**
```python
return Interval(lower, upper, self.static and interval.static, ...)
```

---

### BUG-006: Redundant `to_str()` Method
**Severity:** LOW
**Location:** `interval.py:71-72`
**Description:**
```python
def to_str(self):
    return self.__repr__()
```
Unnecessary indirection. Python's `str()` built-in already calls `__repr__()` if `__str__()` is not defined.

**Impact:**
- Code bloat
- Unclear intent: why have a separate method that does nothing different?

**Fix:**
Remove `to_str()`. Clients should use `str(interval)` or `repr(interval)` directly.

---

## `scripts/numba_wrapper/numba_types/interval_type.py`

### BUG-007: Duplicate Type Inconsistency in Overloaded Intersection
**Severity:** CRITICAL
**Location:** `interval_type.py:61-62`
**Description:**
```python
if lower > upper:
    lower = np.float32(0)  # ← Same bug as BUG-001
    upper = np.float32(1)
```
The overloaded intersection method has the same type inconsistency as `interval.py`. This is the version actually used in JIT-compiled code, making it more critical.

**Impact:** Same as BUG-001, but affects all compiled reasoning code.

**Fix:**
```python
lower = np.float64(0)
upper = np.float64(1)
```

---

### BUG-008: Floating-Point Equality in Overloaded Methods
**Severity:** MEDIUM
**Location:** `interval_type.py:100, 117, 127`
**Description:**
The overloaded implementations of `has_changed()` and operator overloads (`==`, `!=`) use direct floating-point equality comparisons.

**Impact:** Same as BUG-002, but affects JIT-compiled code paths.

**Fix:** Use epsilon-based comparison in all overloaded methods.

---

### BUG-009: Questionable Intersection Semantics for Disjoint Intervals
**Severity:** MEDIUM (Design Decision - Document Intent)
**Location:** `interval.py:66-69`, `interval_type.py:60-63`
**Description:**
When two intervals don't overlap (e.g., `[0.8, 0.9] ∩ [0.1, 0.2]`), the intersection returns `[0, 1]` (maximum uncertainty) instead of signaling a contradiction or returning an empty interval.

```python
if lower > upper:  # Disjoint intervals
    lower = np.float32(0)
    upper = np.float32(1)
```

**Theoretical Question:**
In annotated logic, contradictory evidence typically needs special handling:
- **Option 1 (Current):** Default to uncertainty `[0,1]` (Open World Assumption)
- **Option 2:** Signal contradiction (raise exception or return special marker)
- **Option 3:** Return empty interval representation

**Impact:**
- May hide logical inconsistencies in rule sets
- Conflicting evidence is masked as "unknown" rather than "contradiction"
- Difficult to debug rule conflicts

**Recommendation:**
This may be intentional design (paraconsistent logic or Open World Assumption). Should be:
1. Explicitly documented in code comments
2. Made configurable (e.g., `inconsistency_handling` setting)
3. Logged/traced when contradictions occur

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 2 | interval.py, interval_type.py |
| HIGH | 0 | - |
| MEDIUM | 4 | interval.py, interval_type.py |
| LOW | 3 | interval.py |
| **TOTAL** | **9** | **2** |

---

## `scripts/components/label.py`

### BUG-010: `__eq__` Crashes on Non-Label Comparisons
**Severity:** MEDIUM
**Location:** `label.py:9-11`
**Description:**
```python
def __eq__(self, label):
    result = (self._value == label.get_value()) and isinstance(label, type(self))
    return result
```
The equality method calls `label.get_value()` before checking if `label` is a `Label` instance. Comparing `Label("x") == "x"` raises `AttributeError: 'str' object has no attribute 'get_value'`.

**Impact:**
- Crashes when Labels are compared to non-Label objects (strings, None, etc.)
- Breaks standard Python equality semantics (should return False for incompatible types)
- Can cause unexpected failures in set operations or dict lookups with mixed types

**Fix:**
```python
def __eq__(self, other):
    if not isinstance(other, Label):
        return False
    return self._value == other._value
```

---

### BUG-011: Missing Input Validation in Constructor
**Severity:** LOW
**Location:** `label.py:3-4`
**Description:**
```python
def __init__(self, value):
    self._value = value
```
No validation that `value` is a string. Passing `Label(123)`, `Label(None)`, or `Label([])` will create invalid labels that may fail silently or produce cryptic errors later.

**Impact:**
- Garbage-in-garbage-out: invalid data propagates silently
- Debugging becomes harder when type errors surface far from the source
- Inconsistent behavior: `Label(123)` would have `__str__` return `123` (int), not `"123"` (string)

**Fix:**
```python
def __init__(self, value):
    if not isinstance(value, str):
        raise TypeError(f"Label value must be a string, got {type(value).__name__}")
    self._value = value
```

**Note:** May be intentionally permissive if labels are expected to hold non-string identifiers in some contexts.

---

### BUG-012: Inefficient `__hash__` Implementation
**Severity:** LOW
**Location:** `label.py:16-17`
**Description:**
```python
def __hash__(self):
    return hash(str(self))  # Calls __str__ which returns self._value
```
Unnecessary indirection: `str(self)` calls `__str__()` which just returns `self._value`. The hash should directly hash the value.

**Impact:**
- Minor performance overhead (extra function call per hash)
- Code clarity: obscures what's actually being hashed

**Fix:**
```python
def __hash__(self):
    return hash(self._value)
```

---

### BUG-013: Non-Standard `__repr__` Implementation
**Severity:** LOW
**Location:** `label.py:19-20`
**Description:**
```python
def __repr__(self):
    return self.get_value()
```
By Python convention, `__repr__` should return a string that could recreate the object. Current implementation returns the bare value, making it indistinguishable from a plain string in debugging output.

**Impact:**
- Debugging difficulty: `print(repr(label))` shows `foo` instead of `Label('foo')`
- In collections: `[Label('a'), Label('b')]` displays as `[a, b]` instead of `[Label('a'), Label('b')]`
- Cannot distinguish Label from its underlying value in logs/traces

**Fix:**
```python
def __repr__(self):
    return f"Label({self._value!r})"
```

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 2 | interval.py, interval_type.py |
| HIGH | 0 | - |
| MEDIUM | 5 | interval.py, interval_type.py, label.py |
| LOW | 6 | interval.py, label.py |
| **TOTAL** | **13** | **3** |

---

## `scripts/numba_wrapper/numba_types/label_type.py`

### BUG-014: Missing Type Guard in Hash Overload
**Severity:** MEDIUM
**Location:** `label_type.py:77-81`
**Description:**
```python
@overload(hash)
def label_hash(label):
    def impl(label):
        return hash(label.value)
    return impl
```
Unlike `label_eq` (line 69), this overload doesn't check `isinstance(label, LabelType)` before returning the implementation. The overload will be attempted for *any* `hash()` call, potentially causing compilation errors when Numba tries to access `.value` on non-Label types.

**Impact:**
- May cause cryptic compilation errors when hashing non-Label types
- Inconsistent with the pattern used in `label_eq`

**Fix:**
```python
@overload(hash)
def label_hash(label):
    if isinstance(label, LabelType):
        def impl(label):
            return hash(label.value)
        return impl
```

---

### BUG-015: Architectural Inconsistency - Mixed Numba Extension Patterns
**Severity:** LOW (Technical Debt)
**Location:** `interval.py` + `interval_type.py` vs `label.py` + `label_type.py`
**Description:**
The codebase uses two different Numba extension patterns for similar domain objects:

| Pattern | Used By | API Style |
|---------|---------|-----------|
| **StructRef** | Interval | `structref.StructRefProxy` inheritance |
| **Classic Extension** | Label | Separate Type/Model + boxing/unboxing |

**StructRef (Interval):**
- Python object IS the native struct (shared memory)
- Minimal conversion overhead
- Newer API (~Numba 0.51+)

**Classic Extension (Label):**
- Python object and native struct are separate
- Requires explicit `@box`/`@unbox` with data copying
- Older, more verbose API

**Impact:**
- Maintenance burden: developers must understand two patterns
- Potential for subtle bugs: mutation semantics differ between patterns
- Code review complexity: no single "correct way" to extend types

**Recommendation:**
For the rewrite, standardize on **StructRef** for all domain objects unless there's a specific reason to use classic extension (e.g., wrapping immutable third-party classes).

**Note:** This may be historical accident (different authors/timeframes) rather than intentional design. Not a functional bug, but worth unifying in clean-room rewrite.

---

### BUG-016: Verbose Equality Implementation
**Severity:** LOW
**Location:** `label_type.py:70-74`
**Description:**
```python
def impl(label_1, label_2):
    if label_1.value == label_2.value:
        return True
    else:
        return False
```
Unnecessary verbosity. Could be a single `return` statement.

**Fix:**
```python
def impl(label_1, label_2):
    return label_1.value == label_2.value
```

---

### BUG-017: Inconsistent Type Naming
**Severity:** LOW
**Location:** `label_type.py:33, 43`
**Description:**
```python
# Line 33 (constructor type check)
if isinstance(value, types.UnicodeType):

# Line 43 (model field definition)
('value', types.string)
```
`types.UnicodeType` and `types.string` are aliases in Numba, but inconsistent usage can confuse maintainers.

**Fix:**
Pick one and use consistently. `types.unicode_type` is the canonical name in modern Numba.

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 2 | interval.py, interval_type.py |
| HIGH | 0 | - |
| MEDIUM | 9 | interval.py, interval_type.py, label.py, label_type.py, threshold.py, rule_parser.py |
| LOW | 11 | interval.py, label.py, label_type.py, threshold.py |
| **TOTAL** | **22** | **6** |

---

## `scripts/threshold/threshold.py`

### BUG-018: Missing Type Validation for Threshold Value
**Severity:** MEDIUM
**Location:** `threshold.py:32`
**Description:**
```python
def __init__(self, quantifier, quantifier_type, thresh):
    # ... validation for quantifier and quantifier_type
    self.thresh = thresh  # ← No type checking
```
The docstring claims `thresh` is an `int` (line 8, 21), but there's no runtime validation. Users can pass strings, None, lists, or any other type.

**Impact:**
- `Threshold("greater_equal", ("number", "total"), "not a number")` silently creates invalid object
- Errors surface later during tuple conversion or threshold evaluation (confusing stack trace)
- Type errors propagate into Numba-compiled code, causing cryptic compilation failures

**Fix:**
```python
def __init__(self, quantifier, quantifier_type, thresh):
    if not isinstance(thresh, (int, float)):
        raise TypeError(f"thresh must be numeric, got {type(thresh).__name__}")
    # ... rest of validation
    self.thresh = thresh
```

---

### BUG-019: Missing Structural Validation for quantifier_type
**Severity:** MEDIUM
**Location:** `threshold.py:27-28`
**Description:**
```python
if quantifier_type[0] not in ("number", "percent") or quantifier_type[1] not in ("total", "available"):
    raise ValueError("Invalid quantifier type")
```
The code accesses `quantifier_type[0]` and `quantifier_type[1]` without checking if it's actually a tuple/list with 2 elements.

**Impact:**
- Passing `quantifier_type="number"` (string instead of tuple) raises `IndexError: string index out of range`
- Passing `quantifier_type=["number"]` (1-element list) raises `IndexError: list index out of range`
- Error message is cryptic (IndexError instead of meaningful validation error)

**Fix:**
```python
if not isinstance(quantifier_type, (tuple, list)) or len(quantifier_type) != 2:
    raise TypeError("quantifier_type must be a 2-element tuple/list")
if quantifier_type[0] not in ("number", "percent") or quantifier_type[1] not in ("total", "available"):
    raise ValueError("Invalid quantifier type")
```

---

### BUG-020: No Range Validation for Threshold Values
**Severity:** LOW
**Location:** `threshold.py:32`
**Description:**
No validation that threshold values make sense:
- Negative numbers: `Threshold("greater_equal", ("number", "total"), -5)`
- Zero for percentages: `Threshold("greater_equal", ("percent", "total"), 0)`
- Nonsensical large values: `Threshold("greater_equal", ("number", "total"), 999999)` on a 10-node graph
- Percentages > 100: `Threshold("greater_equal", ("percent", "total"), 150)`

**Impact:**
- Logical errors that silently produce wrong results
- Rules that never fire or always fire unexpectedly
- Difficult to debug (no error, just unexpected behavior)

**Fix:**
```python
def __init__(self, quantifier, quantifier_type, thresh):
    # ... type/structure validation

    # Validate range for percentages
    if quantifier_type[0] == "percent":
        if not (0 <= thresh <= 100):
            raise ValueError(f"Percentage threshold must be in [0, 100], got {thresh}")

    # Validate non-negative for absolute counts
    if quantifier_type[0] == "number" and thresh < 0:
        raise ValueError(f"Absolute threshold cannot be negative, got {thresh}")

    self.thresh = thresh
```

**Note:** May be intentional to allow flexible values for advanced use cases. Consider adding a `strict=True` parameter.

---

### BUG-021: Missing Standard Python Methods
**Severity:** LOW
**Location:** Entire `threshold.py` class
**Description:**
Unlike `Label`, the `Threshold` class lacks standard Python methods:
- No `__eq__`: Can't compare two Threshold objects
- No `__hash__`: Can't use in sets or as dict keys
- No `__repr__`: Debugging output is `<threshold.Threshold object at 0x...>` instead of meaningful representation

**Impact:**
- Debugging difficulty: `print(threshold)` shows memory address, not contents
- Can't test equality: `thresh1 == thresh2` uses object identity, not value equality
- Can't deduplicate thresholds in sets

**Fix:**
```python
def __eq__(self, other):
    if not isinstance(other, Threshold):
        return False
    return (self.quantifier == other.quantifier and
            self.quantifier_type == other.quantifier_type and
            self.thresh == other.thresh)

def __hash__(self):
    return hash((self.quantifier, self.quantifier_type, self.thresh))

def __repr__(self):
    return f"Threshold({self.quantifier!r}, {self.quantifier_type!r}, {self.thresh!r})"
```

---

### BUG-022: Architectural Inconsistency - No Numba Integration
**Severity:** LOW (Design Decision)
**Location:** `threshold.py` (no corresponding `threshold_type.py`)
**Description:**
`Interval` and `Label` both have Numba type wrappers (`interval_type.py`, `label_type.py`) for JIT compilation, but `Threshold` does not.

**Impact:**
- **Likely negligible** - thresholds are serialized to tuples before entering hot loops
- If thresholds were passed as objects to JIT code, lack of Numba wrapper would cause errors
- Inconsistent architecture could confuse developers

**Observation:**
This appears **intentional** - thresholds are configuration objects converted via `to_tuple()` before execution. The tuple format is the ABI boundary between Python setup and compiled evaluation.

**Recommendation:**
Document this design decision in code comments or architecture docs. The current implementation is correct, but the rationale should be explicit.

---

### BUG-023: Type Mismatch Between Documentation and Implementation
**Severity:** MEDIUM
**Location:** `threshold.py:8, 21, 32` vs `rule_parser.py:151`
**Description:**
The docstring claims `thresh` is an `int`, but the Numba type signature expects `float64`:

```python
# threshold.py:8 (docstring)
thresh (int): The numerical threshold value

# threshold.py:21 (docstring)
thresh (int): The numerical value for the threshold.

# rule_parser.py:151 (Numba type definition)
numba.types.Tuple((
    numba.types.string,
    numba.types.UniTuple(numba.types.string, 2),
    numba.types.float64  # ← Expected type is float64, not int64
))
```

**Impact:**
- **Semantic inconsistency**: Percentages should logically be floats (`60.5%`), absolute counts should be ints (`3 neighbors`)
- Python ints auto-convert to float64, so no runtime error occurs
- Misleading documentation: developers expect `Threshold(..., 3)` but `Threshold(..., 3.0)` would be more accurate
- Line 171 uses `1.0` (float literal) for default, confirming floats are intended

**Fix:**
Update docstrings to reflect actual type:
```python
"""
Attributes:
    thresh (float): The numerical threshold value to compare against.
"""
```

Or add explicit conversion in `to_tuple()`:
```python
def to_tuple(self):
    return self.quantifier, self.quantifier_type, float(self.thresh)
```

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 2 | interval.py, interval_type.py |
| HIGH | 1 | world.py |
| MEDIUM | 10 | interval.py, interval_type.py, label.py, label_type.py, threshold.py, rule_parser.py, world.py |
| LOW | 16 | interval.py, label.py, label_type.py, threshold.py, world.py |
| **TOTAL** | **29** | **7** |

---

## `scripts/components/world.py`

### BUG-024: Missing @staticmethod Decorator on make_world
**Severity:** HIGH
**Location:** `world.py:18-21`
**Description:**
```python
def make_world(labels, world):  # ← No @staticmethod decorator
    w = World(labels)
    w._world = world
    return w
```
The `make_world` function is defined without `self` and without `@staticmethod`. This creates a method that:
- **Works from Numba**: The boxing function (`world_type.py:137`) serializes and calls it as a function object
- **Fails in pure Python**: Calling `World.make_world(labels, world)` would implicitly pass `self` as first arg, causing `TypeError: make_world() takes 2 positional arguments but 3 were given`

**Impact:**
- Any pure Python code calling `World.make_world(labels, world)` will crash
- Non-idiomatic code confuses developers (looks like it should work but doesn't)
- Testing in Python (without Numba) would reveal the bug immediately

**Fix:**
```python
@staticmethod
def make_world(labels, world):
    w = World(labels)
    w._world = world
    return w
```

**Note:** This function exists specifically for Numba's boxing machinery (native → Python conversion), not for general use.

---

### BUG-025: Redundant Variable Initializations
**Severity:** LOW
**Location:** `world.py:24, 37`
**Description:**
Multiple methods initialize variables unnecessarily before immediate reassignment:

```python
# is_satisfied (line 23-29)
def is_satisfied(self, label, interval):
    result = False  # ← Unnecessary
    bnd = self._world[label]
    result = bnd in interval  # ← Immediately reassigned
    return result

# get_bound (line 36-40)
def get_bound(self, label):
    result = None  # ← Unnecessary
    result = self._world[label]  # ← Immediately reassigned
    return result
```

**Impact:**
- Code bloat
- Misleading: suggests `result` might be used uninitialized
- Minor performance overhead (negligible in Python, eliminated in JIT)

**Fix:**
```python
def is_satisfied(self, label, interval):
    bnd = self._world[label]
    return bnd in interval

def get_bound(self, label):
    return self._world[label]
```

---

### BUG-026: Redundant get_world() Method
**Severity:** LOW
**Location:** `world.py:42-43`
**Description:**
```python
@property
def world(self):
    return self._world

def get_world(self):  # ← Redundant
    return self._world
```
The `get_world()` method duplicates the `world` property. Python convention favors properties over getters.

**Impact:**
- API inconsistency: two ways to do the same thing
- Maintenance burden: both must be kept in sync

**Fix:**
Remove `get_world()` and use the `world` property consistently.

---

### BUG-027: Missing __repr__ Method
**Severity:** LOW
**Location:** Entire `world.py` class
**Description:**
The class has `__str__` but no `__repr__`. By Python convention, `__repr__` should return a string that could recreate the object (or at least identify it uniquely).

**Impact:**
- Debugging difficulty: `repr(world)` shows `<world.World object at 0x...>` instead of meaningful content
- In collections: `[world1, world2]` displays as memory addresses instead of readable representation

**Fix:**
```python
def __repr__(self):
    labels_str = ', '.join(str(lbl) for lbl in self._labels)
    return f"World(labels=[{labels_str}])"
```

---

### BUG-028: __str__ Uses Deprecated Methods
**Severity:** LOW
**Location:** `world.py:46-51`
**Description:**
```python
def __str__(self):
    result = ''
    for lbl in self._world.keys():
        result = result + lbl.get_value() + ',' + self._world[lbl].to_str() + '\n'
    return result
```
Uses `get_value()` and `to_str()` methods which are:
- Non-idiomatic (Python favors direct access or `str()`)
- Flagged as redundant in BUG-006, BUG-013

**Impact:**
- Coupling to deprecated API
- When Label/Interval are refactored, this breaks

**Fix:**
```python
def __str__(self):
    lines = [f"{str(lbl)},{str(interval)}" for lbl, interval in self._world.items()]
    return '\n'.join(lines)
```

---

### BUG-029: No Input Validation in Constructor
**Severity:** LOW
**Location:** `world.py:8-12`
**Description:**
```python
def __init__(self, labels):
    self._labels = labels  # ← No validation
    self._world = numba.typed.Dict.empty(key_type=label.label_type, value_type=interval.interval_type)
    for lbl in labels:  # ← Crashes if labels is not iterable
        self._world[lbl] = interval.closed(0.0, 1.0)
```
No checks that:
- `labels` is iterable
- `labels` contains `Label` objects
- `labels` is non-empty

**Impact:**
- `World(None)` → `TypeError: 'NoneType' object is not iterable`
- `World([1, 2, 3])` → Numba type error (int is not Label)
- `World("string")` → Iterates over characters
- Cryptic error messages far from source

**Fix:**
```python
def __init__(self, labels):
    if not hasattr(labels, '__iter__'):
        raise TypeError("labels must be iterable")
    labels_list = list(labels)
    if not labels_list:
        raise ValueError("labels cannot be empty")
    # Optional: validate all are Label instances
    self._labels = labels_list
    # ... rest of constructor
```

---

### BUG-030: No KeyError Handling in Dictionary Access
**Severity:** MEDIUM
**Location:** `world.py:26, 32, 39`
**Description:**
Methods directly access `self._world[label]` without checking if the label exists:

```python
# is_satisfied (line 26)
bnd = self._world[label]  # ← KeyError if label not in world

# update (line 32)
current_bnd = self._world[label]  # ← KeyError if label not in world

# get_bound (line 39)
result = self._world[label]  # ← KeyError if label not in world
```

**Impact:**
- Cryptic errors: `KeyError: Label('unknown_predicate')` instead of meaningful message
- Difficult to debug: caller doesn't know if it's a typo or logic error
- No way to gracefully handle missing predicates

**Fix (Option 1 - Fail fast):**
```python
def get_bound(self, label):
    if label not in self._world:
        raise ValueError(f"Label {label} not defined in world. Available: {list(self._world.keys())}")
    return self._world[label]
```

**Fix (Option 2 - Default behavior):**
```python
def get_bound(self, label):
    return self._world.get(label, interval.closed(0.0, 1.0))  # Return unknown if missing
```

**Recommendation:** Option 1 for debugging, Option 2 for flexibility. Consider making it configurable.

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 2 | interval.py, interval_type.py |
| HIGH | 1 | world.py |
| MEDIUM | 13 | interval.py, interval_type.py, label.py, label_type.py, threshold.py, rule_parser.py, world.py, world_type.py |
| LOW | 20 | interval.py, label.py, label_type.py, threshold.py, world.py, world_type.py |
| **TOTAL** | **36** | **8** |

---

## `scripts/numba_wrapper/numba_types/world_type.py`

### BUG-031: Function Redefinition Anti-Pattern for Constructor Overloading
**Severity:** MEDIUM
**Location:** `world_type.py:33-46`
**Description:**
```python
@type_callable(World)
def type_world(context):  # ← First definition
    def typer(labels, world):
        if isinstance(labels, types.ListType) and isinstance(world, types.DictType):
            return world_type
    return typer

@type_callable(World)
# ruff: noqa: F811  # ← Suppress "redefined function" warning
def type_world(context):  # ← Second definition (same name)
    def typer(labels):
        if isinstance(labels, types.ListType):
            return world_type
    return typer
```

Two functions with identical names for constructor overloading. Numba supports this via decorator stacking, but reusing the function name is confusing and requires linter suppression.

**Impact:**
- Code smell: appears broken to unfamiliar readers
- Requires `# noqa: F811` to suppress linting errors
- Harder to debug: which `type_world` is being invoked?
- Non-Pythonic: function name collisions are normally errors

**Fix (Better Pattern):**
```python
@type_callable(World)
def type_world_constructor(context):
    def typer(*args):
        if len(args) == 2:
            labels, world = args
            if isinstance(labels, types.ListType) and isinstance(world, types.DictType):
                return world_type
        elif len(args) == 1:
            labels = args[0]
            if isinstance(labels, types.ListType):
                return world_type
    return typer
```

**Note:** The pattern is intentional (Numba only cares about decorators, not names), but BUG-015 established that architectural inconsistency is worth flagging. The same pattern exists in `label_type.py`.

---

### BUG-032: Redundant Variable Initializations in Overloaded Methods
**Severity:** LOW
**Location:** `world_type.py:95, 113`
**Description:**
Same issue as BUG-025 (world.py) - the JIT-compiled method implementations have unnecessary initialization:

```python
@overload_method(WorldType, 'is_satisfied')
def is_satisfied(world, label, interval):
    def impl(world, label, interval):
        result = False  # ← Unnecessary
        bnd = world.world[label]
        result = bnd in interval  # ← Immediately reassigned
        return result
    return impl

@overload_method(WorldType, 'get_bound')
def get_bound(world, label):
    def impl(world, label):
        result = None  # ← Unnecessary
        result = world.world[label]  # ← Immediately reassigned
        return result
    return impl
```

**Impact:**
- Code bloat (minor in JIT, but still present in source)
- Misleading: suggests result might be used uninitialized
- Inconsistent with best practices

**Fix:**
```python
def impl(world, label, interval):
    bnd = world.world[label]
    return bnd in interval

def impl(world, label):
    return world.world[label]
```

---

### BUG-033: No KeyError Handling in Overloaded Methods
**Severity:** LOW
**Location:** `world_type.py:96, 105, 114`
**Description:**
Same issue as BUG-030 (world.py) - the JIT implementations directly access `world.world[label]` without validation:

```python
bnd = world.world[label]  # ← KeyError if label not in dict
```

**Impact:**
- Same as BUG-030, but in JIT-compiled code paths
- Cryptic errors during JIT execution

**Fix:** Same options as BUG-030 (fail-fast validation or default value).

---

### BUG-034: update() Method Has No Return Statement
**Severity:** MEDIUM
**Location:** `world_type.py:102-108`
**Description:**
```python
@overload_method(WorldType, 'update')
def update(w, label, interval):
    def impl(w, label, interval):
        current_bnd = w.world[label]
        new_bnd = current_bnd.intersection(interval)
        w.world[label] = new_bnd
        # ← No return statement
    return impl
```

The method mutates `w.world[label]` but doesn't return anything. Python version (`world.py:31-34`) also has no return, so this is consistent.

**Impact:**
- Semantic ambiguity: Is this a mutating operation or does it return the new world?
- In Classic Extension pattern (separate Python/native memory), mutations in JIT may not persist to Python
- No documentation clarifying mutation semantics

**Investigation Needed:**
Does the mutation persist when the World is returned to Python? In Classic Extension:
- Unboxing creates a NEW native struct from Python
- Boxing creates a NEW Python object from native
- Mutations might be lost during round-trip

**Fix:**
1. Add explicit `return None` for clarity
2. Document mutation semantics in docstring
3. Test round-trip behavior: Python → JIT (mutate) → Python

---

### BUG-035: Commented-Out Dead Code
**Severity:** LOW
**Location:** `world_type.py:68`
**Description:**
```python
@lower_builtin(World, types.ListType(...), types.DictType(...))
def impl_world(context, builder, sig, args):
    # context.build_map(builder, )  # ← Incomplete/dead code
    typ = sig.return_type
    ...
```

Commented-out code with incomplete syntax suggests:
- Leftover debugging code
- Incomplete implementation
- Copy-paste artifact

**Impact:**
- Code clutter
- Confusing to maintainers (why is this here?)
- Suggests code might not be finished

**Fix:** Remove the comment or explain why it's preserved.

---

### BUG-036: Manual Reference Counting May Cause Memory Issues
**Severity:** MEDIUM
**Location:** `world_type.py:71-72`
**Description:**
```python
@lower_builtin(World, types.ListType(...), types.DictType(...))
def impl_world(context, builder, sig, args):
    labels_arg, wo = args
    context.nrt.incref(builder, types.DictType(...), wo)      # ← Manual incref
    context.nrt.incref(builder, types.ListType(...), labels_arg)  # ← Manual incref
    w = cgutils.create_struct_proxy(typ)(context, builder)
    w.labels = labels_arg
    w.world = wo
    return w._getvalue()
```

The 2-arg constructor manually increments reference counts for both arguments. However:

**Inconsistency:**
- 1-arg constructor (lines 78-88) does NOT manually incref
- Unboxing (lines 125-126) uses `.value` which may already manage refcounts
- Boxing (lines 138-139) uses `c.box()` which may have different refcount expectations

**Potential Issues:**
- **Memory leak**: If Numba already increments refcounts automatically, this double-increments
- **Double-free**: If refcounts aren't properly balanced on struct destruction
- **Inconsistent semantics**: Why does 2-arg incref but 1-arg doesn't?

**Impact:**
- Hard-to-debug memory leaks (gradual growth over time)
- Rare crashes (double-free when struct is destroyed)
- Only manifests under specific usage patterns

**Investigation Needed:**
Compare with `label_type.py` (similar Classic Extension pattern) to see if manual incref is standard.

**Fix:**
Audit reference counting throughout:
1. Check if `create_struct_proxy` automatically manages refcounts
2. Verify consistency between 1-arg and 2-arg constructors
3. Test for memory leaks with long-running programs

---

### BUG-037: Nested Attribute Access Pattern (Confusing Naming)
**Severity:** LOW
**Location:** `world_type.py:96, 105, 114`
**Description:**
```python
bnd = world.world[label]  # ← world.world looks strange
```

The native struct has a field named `world` (the dict), so accessing dict entries requires `world.world[...]`. This is technically correct but visually confusing.

**Impact:**
- Code readability: `world.world` looks like a typo or stuttering
- No functional issue, just awkward naming
- Consistent with the data model (line 55: `('world', types.DictType(...))`)

**Fix (for rewrite):**
Rename the struct field to avoid collision:
```python
# In WorldModel (line 52-56):
members = [
    ('labels', types.ListType(label.label_type)),
    ('_data', types.DictType(...))  # ← Rename 'world' → '_data'
]

# In method overloads:
bnd = world._data[label]  # ← Clearer
```

**Note:** This is purely cosmetic. The current implementation is functionally correct.

---

## `scripts/utils/fact_parser.py`

### BUG-038: Missing Parenthesis Validation - Causes Silent Data Corruption
**Severity:** CRITICAL
**Location:** `fact_parser.py:29-31`
**Description:**
```python
idx = pred_comp.find('(')  # Returns -1 if '(' not found
pred = pred_comp[:idx]      # pred_comp[:-1] when idx=-1
component = pred_comp[idx + 1:-1]  # pred_comp[0:-1] when idx=-1
```
If the input lacks a `(`, `find()` returns -1. Slicing `[:idx]` with idx=-1 produces `pred_comp[:-1]` (all but last character), and `component` becomes `pred_comp[0:-1]` (also all but last character). **This silently corrupts data instead of raising an error.**

**Impact:**
- Input `"infected"` → `pred="infecte"`, `component="infected"` (both wrong)
- No error raised - invalid facts enter the knowledge base
- Debugging nightmare: facts appear to parse successfully but contain garbage data
- Violates fail-fast principle - corruption discovered much later in the pipeline

**Fix:**
```python
idx = pred_comp.find('(')
if idx == -1:
    raise ValueError(f"Missing '(' in fact: {fact_text}")
if not pred_comp.endswith(')'):
    raise ValueError(f"Missing ')' in fact: {fact_text}")
pred = pred_comp[:idx]
component = pred_comp[idx + 1:-1]
```

---

### BUG-039: No Validation for Interval Bound Format - Crashes on Malformed Input
**Severity:** CRITICAL
**Location:** `fact_parser.py:25-26`
**Description:**
```python
bound = [float(b) for b in bound[1:-1].split(',')]  # Assumes format "[x,y]"
bound = interval.closed(*bound)
```
Assumes interval bounds are formatted as `"[x,y]"` with no validation:
- Crashes if bound doesn't start/end with brackets: `bound[1:-1]` produces wrong substring
- Crashes if split produces != 2 elements: `interval.closed(*bound)` requires exactly 2 args
- Crashes on non-numeric values: `float(b)` raises ValueError

**Impact:**
- Input `"pred(x):0.5,0.8"` → crashes (missing brackets, slices to `.5,0.`)
- Input `"pred(x):[0.5,0.8,0.9]"` → crashes (3 values, `closed()` expects 2)
- Input `"pred(x):[low,high]"` → crashes (non-numeric)
- No error message indicates what format is expected

**Fix:**
```python
import re
if bound not in ('true', 'false'):
    match = re.match(r'\[([\d.]+),([\d.]+)\]', bound)
    if not match:
        raise ValueError(f"Invalid interval format: {bound}. Expected [lower,upper]")
    lower, upper = match.groups()
    bound = interval.closed(float(lower), float(upper))
```

---

### BUG-040: No Validation of Interval Bound Values
**Severity:** HIGH
**Location:** `fact_parser.py:25-26`
**Description:**
```python
bound = [float(b) for b in bound[1:-1].split(',')]
bound = interval.closed(*bound)
```
The parser accepts any float values without validating:
- Bounds should be in [0, 1] range for probability/truth semantics
- Lower bound should be ≤ upper bound
- No checks for NaN, infinity, negative values, or values > 1

**Impact:**
- Input `"pred(x):[-0.5,2.0]"` → accepted (invalid probability range)
- Input `"pred(x):[0.9,0.1]"` → accepted (inverted bounds, semantically invalid)
- Input `"pred(x):[nan,inf]"` → accepted (may cause undefined behavior in interval arithmetic)
- Violates invariants expected by downstream interval operations

**Fix:**
```python
lower, upper = float(bound[0]), float(bound[1])
if not (0 <= lower <= 1 and 0 <= upper <= 1):
    raise ValueError(f"Interval bounds must be in [0,1]: [{lower},{upper}]")
if lower > upper:
    raise ValueError(f"Lower bound {lower} exceeds upper bound {upper}")
bound = interval.closed(lower, upper)
```

---

### BUG-041: Multiple Colons Cause Incorrect Parsing
**Severity:** MEDIUM
**Location:** `fact_parser.py:8-9`
**Description:**
```python
if ':' in f:
    pred_comp, bound = f.split(':')  # Only splits on FIRST colon
```
If the fact contains multiple colons, `split(':')` without a limit splits only on the first occurrence. This could happen with:
- Malformed input: `"pred(x):0.5:extra"`
- Future syntax extensions: `"pred(x):source:value"`

The code splits into only 2 parts, putting everything after the first `:` into `bound`, which may not be the intended behavior.

**Impact:**
- Input `"pred(x):0.5:garbage"` → `bound="0.5:garbage"`, crashes on float conversion
- No validation that exactly one `:` exists
- Error message doesn't indicate the problem

**Fix:**
```python
if ':' in f:
    parts = f.split(':')
    if len(parts) != 2:
        raise ValueError(f"Fact must contain exactly one ':' separator: {fact_text}")
    pred_comp, bound = parts
```

---

### BUG-042: Whitespace Removal Breaks Facts with Spaces in String Arguments
**Severity:** MEDIUM
**Location:** `fact_parser.py:5`
**Description:**
```python
f = fact_text.replace(' ', '')  # Removes ALL whitespace
```
The parser unconditionally strips all spaces from the input. This breaks any facts where components contain legitimate spaces, such as:
- Multi-word entity names: `"person(John Smith)"`
- Quoted strings: `"name(x, 'New York')"`

While PyReason may not currently support quoted strings, this design choice prevents future extensibility.

**Impact:**
- Input `"person(John Smith)"` → component becomes `"JohnSmith"` (data corruption)
- No way to represent entities with spaces in their identifiers
- Future-proofing issue: adding string literal support requires rewriting parser

**Fix:**
Only strip whitespace outside of parentheses and brackets, or use a proper tokenizer:
```python
# Option 1: Strip only around delimiters
f = re.sub(r'\s*([():,\[\]])\s*', r'\1', fact_text)

# Option 2: Better - use a proper parser/lexer
```

**Note:** If the current PyReason design intentionally disallows spaces in identifiers, this should be validated with a clear error message rather than silently removing them.

---

### BUG-043: Edge Component Not Validated for Correct Tuple Structure
**Severity:** MEDIUM
**Location:** `fact_parser.py:34-36`
**Description:**
```python
if ',' in component:
    fact_type = 'edge'
    component = tuple(component.split(','))  # Assumes exactly 2 elements
```
The code assumes edge facts have exactly 2 nodes (source, target) but doesn't validate:
- Could have 1 element with trailing comma: `"edge(a,)"` → `('a', '')`
- Could have 3+ elements: `"edge(a,b,c)"` → `('a', 'b', 'c')`
- Empty elements: `"edge(,)"` → `('', '')`

Downstream code may assume `len(component) == 2` for edges, causing crashes or incorrect behavior.

**Impact:**
- Malformed edge facts enter knowledge base
- Graph construction may crash when expecting 2-tuples
- No error message guides user to correct format

**Fix:**
```python
if ',' in component:
    fact_type = 'edge'
    component = tuple(component.split(','))
    if len(component) != 2:
        raise ValueError(f"Edge fact must have exactly 2 components: {fact_text}")
    if any(c == '' for c in component):
        raise ValueError(f"Edge components cannot be empty: {fact_text}")
else:
    fact_type = 'node'
    if component == '':
        raise ValueError(f"Node component cannot be empty: {fact_text}")
```

---

### BUG-044: No Validation of Predicate Name
**Severity:** LOW
**Location:** `fact_parser.py:29-30`
**Description:**
```python
idx = pred_comp.find('(')
pred = pred_comp[:idx]  # Could be empty string
```
The parser doesn't validate that the predicate name is non-empty or follows identifier rules. This allows:
- Empty predicate: `"(node1):[0,1]"` → `pred=""`
- Invalid identifiers: `"123pred(node)"`
- Special characters: `"@#$(node)"`

**Impact:**
- Invalid predicates enter the knowledge base
- May cause issues in rule matching or graph lookups
- Poor user experience: no guidance on valid predicate syntax

**Fix:**
```python
import re
if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', pred):
    raise ValueError(f"Invalid predicate name '{pred}'. Must be valid identifier.")
```

---

### BUG-045: Case-Insensitive Bound Parsing Not Documented
**Severity:** LOW
**Location:** `fact_parser.py:19-23`
**Description:**
```python
bound = bound.lower()  # Silently converts to lowercase
if bound == 'true':
    ...
elif bound == 'false':
    ...
```
The parser converts bounds to lowercase before comparison, making `"True"`, `"TRUE"`, `"tRuE"` all equivalent. This behavior is not documented and may surprise users expecting case-sensitive parsing.

**Impact:**
- Implicit behavior not documented in API
- Inconsistent with typical case-sensitive language parsers
- Minor: unlikely to cause real bugs

**Fix:**
Add docstring explaining case-insensitive boolean handling:
```python
def parse_fact(fact_text):
    """
    Parse a fact string into components.

    Bounds are case-insensitive: 'True', 'TRUE', 'true' all map to [1,1].
    ...
    """
```

---

### BUG-046: No Error Messages - Silent Failures and Cryptic Crashes
**Severity:** LOW
**Location:** `fact_parser.py:1-40` (entire file)
**Description:**
The parser has zero error handling. All failures produce Python runtime exceptions with cryptic messages:
- IndexError: list index out of range
- ValueError: could not convert string to float
- TypeError: closed() takes 2 positional arguments but 3 were given

Users get no guidance on:
- What syntax is expected
- Which part of their input is malformed
- How to fix the error

**Impact:**
- Poor developer experience
- Difficult debugging for users unfamiliar with PyReason syntax
- No validation feedback during rule/fact authoring

**Fix:**
Wrap the parsing logic in try-except and provide contextual errors:
```python
def parse_fact(fact_text):
    try:
        # ... parsing logic ...
    except Exception as e:
        raise ValueError(
            f"Failed to parse fact: {fact_text}\n"
            f"Expected format: predicate(component):[lower,upper]\n"
            f"Error: {e}"
        ) from e
```

---

## `scripts/facts/fact.py`, `scripts/facts/fact_node.py`, `scripts/facts/fact_edge.py`

### BUG-047: Massive Code Duplication - fact_node.py and fact_edge.py Are 98% Identical
**Severity:** HIGH
**Location:** `fact_node.py:1-43`, `fact_edge.py:1-43`
**Description:**
The `fact_node.py` and `fact_edge.py` files contain **identical code** - 42 out of 43 lines are duplicates. The ONLY difference is line 35:
```python
# fact_node.py:35
"type": 'pyreason node fact'

# fact_edge.py:35
"type": 'pyreason edge fact'
```

Both files define a `Fact` class with:
- Identical `__init__` signature (7 parameters)
- Identical getter methods (get_name, set_name, get_component, etc.)
- Identical field names (_name, _component, _label, _interval, _t_lower, _t_upper, _static)
- Nearly identical `__str__` method

**Impact:**
- Violates DRY principle catastrophically
- Bug fixes must be manually synchronized across both files
- Maintenance nightmare: any change requires duplicate edits
- Risk of divergence: files may drift apart over time as bugs are fixed in only one
- Code bloat: unnecessary duplication

**Fix:**
Create a base `InternalFact` class and use inheritance:
```python
# fact_internal.py
class InternalFact:
    def __init__(self, name, component, label, interval, t_lower, t_upper, static=False):
        self._name = name
        self._t_upper = t_upper
        self._t_lower = t_lower
        self._component = component
        self._label = label
        self._interval = interval
        self._static = static

    # ... all shared methods ...

    def _get_fact_type(self):
        raise NotImplementedError("Subclass must implement")

    def __str__(self):
        return {
            "type": self._get_fact_type(),
            # ... rest of dict ...
        }

# fact_node.py
class Fact(InternalFact):
    def _get_fact_type(self):
        return 'pyreason node fact'

# fact_edge.py
class Fact(InternalFact):
    def _get_fact_type(self):
        return 'pyreason edge fact'
```

---

### BUG-048: No Inheritance Hierarchy Despite Identical Interfaces
**Severity:** HIGH
**Location:** `fact.py:5`, `fact_node.py:1`, `fact_edge.py:1`
**Description:**
Three separate classes named `Fact` exist with no inheritance relationship:
- `fact.Fact` - user-facing API (parses text strings)
- `fact_node.Fact` - internal runtime representation for nodes
- `fact_edge.Fact` - internal runtime representation for edges

Despite `fact_node.Fact` and `fact_edge.Fact` having identical signatures and nearly identical implementations, neither inherits from a common base class. This makes polymorphic code impossible:
```python
# Cannot write:
if isinstance(f, BaseFact):  # No BaseFact exists
    ...

# Cannot use:
facts: List[BaseFact] = [...]  # No common type
```

**Impact:**
- No type hierarchy for facts
- Cannot write polymorphic functions that work on "any fact"
- `isinstance()` checks don't work across fact types
- Type hints become module-specific: `fact_node.Fact` vs `fact_edge.Fact`
- Violates Liskov Substitution Principle

**Fix:**
Establish proper inheritance:
```python
# Base class for runtime facts
class InternalFact:
    ...

# Subclasses for node/edge specialization
class NodeFact(InternalFact):
    ...

class EdgeFact(InternalFact):
    ...
```

**Note:** The user-facing `fact.Fact` serves a different purpose (parsing/construction) and may not need to inherit from InternalFact.

---

### BUG-049: Name Collision Across Modules - Three Classes Named "Fact"
**Severity:** MEDIUM
**Location:** `fact.py:5`, `fact_node.py:1`, `fact_edge.py:1`
**Description:**
All three modules define a class named `Fact`, creating namespace-dependent polymorphism:
```python
from pyreason.scripts.facts.fact import Fact  # User API
from pyreason.scripts.facts.fact_node import Fact  # Internal node
from pyreason.scripts.facts.fact_edge import Fact  # Internal edge
```

This requires explicit module qualification and makes code harder to read:
```python
import pyreason.scripts.facts.fact as user_fact
import pyreason.scripts.facts.fact_node as node_fact

f1 = user_fact.Fact("pred(x):True")  # Verbose
f2 = node_fact.Fact(...)  # Confusing - same name, different classes
```

**Impact:**
- Confusing for developers: "Fact" means different things in different contexts
- Import ambiguity: `from ... import Fact` is unclear without module context
- No IDE autocomplete help to distinguish them
- Harder to read code reviews and trace execution

**Fix:**
Use distinct, descriptive class names:
```python
# fact.py
class UserFact:  # or FactDefinition, FactSpec, etc.
    ...

# fact_node.py
class NodeFact:
    ...

# fact_edge.py
class EdgeFact:
    ...
```

**Note:** This is a minor issue compared to BUG-047/048, but improves code clarity.

---

### BUG-050: fact.py Constructor Does Not Validate Parsed Components
**Severity:** MEDIUM
**Location:** `fact.py:20-28`
**Description:**
```python
pred, component, bound, fact_type = fact_parser.parse_fact(fact_text)
self.name = name
# ... directly assigns parsed values with no validation
self.pred = label.Label(pred)
self.component = component
self.bound = bound
self.type = fact_type
```

The constructor blindly trusts the output of `fact_parser.parse_fact()`, which we know is critically fragile (BUG-038, BUG-039). If the parser returns corrupted data:
- `component` could be an empty string or malformed
- `fact_type` could be wrong
- No validation that `bound` is a valid Interval
- No validation that `pred` is a valid identifier

**Impact:**
- Invalid facts can be constructed and added to the knowledge base
- No second line of defense after the fragile parser
- Errors discovered much later during reasoning
- Violates fail-fast principle

**Fix:**
Add validation after parsing:
```python
pred, component, bound, fact_type = fact_parser.parse_fact(fact_text)

# Validate parsed results
if not pred:
    raise ValueError(f"Empty predicate in fact: {fact_text}")
if fact_type == 'node' and not component:
    raise ValueError(f"Empty component in node fact: {fact_text}")
if fact_type == 'edge':
    if not isinstance(component, tuple) or len(component) != 2:
        raise ValueError(f"Edge fact must have 2 components: {fact_text}")
    if any(c == '' for c in component):
        raise ValueError(f"Empty component in edge fact: {fact_text}")
# Validate interval bounds
if not (0 <= bound.lower <= 1 and 0 <= bound.upper <= 1):
    raise ValueError(f"Interval bounds must be in [0,1]: {fact_text}")

self.pred = label.Label(pred)
# ... rest of assignments
```

---

### BUG-051: Java-Style Getters Instead of Python Properties
**Severity:** LOW
**Location:** `fact_node.py:12-31`, `fact_edge.py:12-31`
**Description:**
```python
def get_name(self):
    return self._name

def get_component(self):
    return self._component
# ... etc
```

The internal fact classes use Java-style getter methods instead of Python properties or direct attribute access. This is un-Pythonic and verbose:
```python
# Current (verbose):
name = fact.get_name()
component = fact.get_component()

# Pythonic (preferred):
name = fact.name
component = fact.component
```

**Impact:**
- Unnecessarily verbose code
- Inconsistent with Python idioms
- No actual encapsulation benefit (fields are still accessible as _name)
- More typing, less readable

**Fix:**
Use `@property` decorators:
```python
@property
def name(self):
    return self._name

@name.setter
def name(self, value):
    self._name = value

@property
def component(self):
    return self._component
# etc.
```

**Note:** Even better - just make them public attributes unless you need validation/computation.

---

### BUG-052: __str__ Returns Dict Instead of String
**Severity:** LOW
**Location:** `fact_node.py:33-42`, `fact_edge.py:33-42`
**Description:**
```python
def __str__(self):
    fact = {
        "type": 'pyreason node fact',
        ...
    }
    return fact  # ← Returns dict, not string!
```

The `__str__` method is supposed to return a string, but this returns a dict. When Python calls `str(fact_obj)`, it will call `dict.__str__()` on the returned dict, producing output like:
```
{'type': 'pyreason node fact', 'name': ..., ...}
```

This works but is semantically wrong and confusing.

**Impact:**
- Violates `__str__` contract (should return str, not dict)
- Misleading for developers reading the code
- Prevents customized string formatting

**Fix:**
```python
def __str__(self):
    fact = {
        "type": 'pyreason node fact',
        "name": self._name,
        "component": self._component,
        "label": self._label,
        "confidence": self._interval,
        "time": f'[{self._t_lower},{self._t_upper}]'
    }
    return str(fact)  # Or use json.dumps for prettier formatting
```

---

### BUG-053: Missing __repr__ Method in All Fact Classes
**Severity:** LOW
**Location:** `fact.py`, `fact_node.py`, `fact_edge.py`
**Description:**
None of the three `Fact` classes define `__repr__`, so they use the default implementation which shows memory address:
```python
>>> f = Fact("pred(x):True")
>>> f
<pyreason.scripts.facts.fact.Fact object at 0x7f8b3c4d5e80>
```

This provides no useful debugging information.

**Impact:**
- Poor REPL/debugging experience
- No way to recreate object from repr
- Harder to diagnose issues in logs

**Fix:**
Add `__repr__` to each class:
```python
# fact.py
def __repr__(self):
    return f"Fact(fact_text='{self.pred}({self.component}):{self.bound}', name={self.name!r}, start_time={self.start_time}, end_time={self.end_time}, static={self.static})"

# fact_node.py
def __repr__(self):
    return f"NodeFact(name={self._name!r}, component={self._component!r}, label={self._label!r}, interval={self._interval!r}, t_lower={self._t_lower}, t_upper={self._t_upper}, static={self._static})"
```

---

### BUG-054: Missing __eq__ and __hash__ - Cannot Use Facts in Sets/Dicts Reliably
**Severity:** LOW
**Location:** `fact.py`, `fact_node.py`, `fact_edge.py`
**Description:**
None of the `Fact` classes define `__eq__` or `__hash__`, so they use identity-based equality:
```python
f1 = Fact("pred(x):True")
f2 = Fact("pred(x):True")
f1 == f2  # False! Different objects
{f1, f2}  # Set with 2 elements (should be 1 if semantically equal)
```

This means:
- Cannot deduplicate facts based on content
- Cannot use facts as dict keys reliably
- Set operations don't work as expected

**Impact:**
- Duplicate facts may be added to knowledge base
- Cannot efficiently check "does this fact already exist?"
- Set-based reasoning operations don't work

**Fix:**
Implement `__eq__` and `__hash__`:
```python
# fact.py
def __eq__(self, other):
    if not isinstance(other, Fact):
        return False
    return (self.pred == other.pred and
            self.component == other.component and
            self.bound == other.bound and
            self.start_time == other.start_time and
            self.end_time == other.end_time and
            self.static == other.static)

def __hash__(self):
    return hash((self.pred, self.component, self.bound, self.start_time, self.end_time, self.static))
```

**Note:** Only implement `__hash__` if objects are immutable. If facts can be mutated, they should not be hashable.

---

### BUG-055: fact.py Has No Setters - Immutable After Construction
**Severity:** LOW
**Location:** `fact.py:5-36`
**Description:**
The user-facing `Fact` class provides no methods to modify fact attributes after construction. All fields are read-only:
```python
f = Fact("pred(x):True", start_time=5)
# No way to change start_time
# No f.start_time = 10  (would work but bypasses any validation)
```

In contrast, `fact_node.Fact` has `set_name()`, suggesting mutability is needed.

**Impact:**
- Cannot adjust fact parameters after construction
- Users must create new Fact objects for any changes
- Unclear if facts are meant to be immutable or mutable

**Fix:**
**Option 1**: Make facts explicitly immutable (use frozen dataclass or named tuple)
**Option 2**: Add setter methods/properties for mutable fields
**Option 3**: Document the intended mutability semantics

**Note:** This may be intentional design. If facts should be immutable after construction, add `@dataclass(frozen=True)` to enforce it.

---

## `scripts/numba_wrapper/numba_types/fact_node_type.py`, `scripts/numba_wrapper/numba_types/fact_edge_type.py`

### BUG-056: Massive Code Duplication in Numba Fact Wrappers - 99% Identical
**Severity:** HIGH
**Location:** `fact_node_type.py:1-177`, `fact_edge_type.py:1-176`
**Description:**
The Numba wrapper files for node and edge facts are **virtually identical** - 175 out of 177 lines are exact duplicates. The ONLY meaningful difference is the component type:

```python
# fact_node_type.py:36
isinstance(component, types.UnicodeType)  # Node: single string

# fact_edge_type.py:36
isinstance(component, types.Tuple)  # Edge: tuple of two strings

# fact_node_type.py:47
('component', numba.types.string)

# fact_edge_type.py:47
('component', numba.types.Tuple((numba.types.string, numba.types.string)))
```

Everything else is identical:
- Same type registration boilerplate (lines 18-29)
- Same constructor overload logic (lines 33-38)
- Same StructModel definition (lines 42-54, except component type)
- Same attribute wrappers (lines 57-64)
- Same constructor implementation (lines 68-80)
- Same 6 getter method overloads (lines 84-123)
- Same unboxing logic (lines 127-152)
- Same boxing logic (lines 156-176)

**Impact:**
- Even worse than BUG-047 (Python class duplication) - 177 lines vs 43 lines
- Numba extension code is complex and error-prone - duplication multiplies risk
- Bug fixes must be manually synchronized across both files
- Already observed divergence: fact_node_type.py has 177 lines, fact_edge_type.py has 176
- Maintenance nightmare for any type system changes
- High coupling - changes to Numba API require duplicate updates

**Fix:**
Use Numba's type parameterization or metaprogramming to generate both types:

**Option 1: Generic factory function**
```python
# fact_type_factory.py
def create_fact_type(name, component_type):
    class FactType(types.Type):
        def __init__(self):
            super(FactType, self).__init__(name=name)

    fact_type = FactType()

    @register_model(FactType)
    class FactModel(models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [
                ('name', numba.types.string),
                ('component', component_type),  # ← Parameterized
                ('l', label.label_type),
                # ... rest of fields
            ]
            models.StructModel.__init__(self, dmm, fe_type, members)

    # ... rest of registration logic using component_type parameter
    return fact_type

# fact_node_type.py
fact_type = create_fact_type('FactNode', numba.types.string)

# fact_edge_type.py
fact_type = create_fact_type('FactEdge',
    numba.types.Tuple((numba.types.string, numba.types.string)))
```

**Option 2: Single unified Fact type with component discrimination**
```python
# Use a single FactType with runtime component type checking
# Discriminate node vs edge based on component value type
```

**Note:** This is the same root cause as BUG-047 - lack of abstraction over the node/edge distinction. The entire fact system should be refactored with a common base.

---

### BUG-057: Timestep Range Limited to 65,535 Steps
**Severity:** MEDIUM
**Location:** `fact_node_type.py:50-51`, `fact_edge_type.py:50-51`
**Description:**
```python
('t_lower', numba.types.uint16),  # Maximum value: 65,535
('t_upper', numba.types.uint16),
```

Timesteps are stored as `uint16`, limiting temporal reasoning to a maximum of 65,535 timesteps. For long-running simulations or fine-grained temporal models, this is insufficient:
- Hourly timesteps for a year = 8,760 steps (OK)
- Minutely timesteps for a week = 10,080 steps (OK)
- Secondly timesteps for a day = 86,400 steps (**OVERFLOW**)
- Millisecond-resolution simulations immediately overflow

**Impact:**
- Programs requiring more than 65,535 timesteps will overflow
- Silent wraparound: timestep 65,536 becomes 0 (modulo arithmetic)
- Temporal logic breaks: facts may become active/inactive incorrectly
- No error message or warning on overflow
- Limits scalability of temporal reasoning applications

**Fix:**
Change to `uint32` (4.29 billion steps) or `uint64` (virtually unlimited):
```python
('t_lower', numba.types.uint32),  # Maximum: 4,294,967,295
('t_upper', numba.types.uint32),
```

**Cost analysis:**
- Memory increase: 4 bytes per fact (2 bytes × 2 fields)
- For 10,000 facts: 40KB additional memory (negligible)
- Performance: No impact (uint32 is native word size on modern CPUs)

**Note:** Check if any serialization formats or database schemas also assume uint16 for timesteps.

---

### BUG-058: Manual Reference Counting - Memory Leak Risk
**Severity:** LOW
**Location:** `fact_node_type.py:144-150, 168-175`, `fact_edge_type.py:144-150, 168-175`
**Description:**
```python
# Unboxing (lines 144-150):
c.pyapi.decref(name_obj)
c.pyapi.decref(component_obj)
c.pyapi.decref(l_obj)
c.pyapi.decref(bnd_obj)
c.pyapi.decref(t_lower_obj)
c.pyapi.decref(t_upper_obj)
c.pyapi.decref(static_obj)

# Boxing (lines 168-175):
c.pyapi.decref(name_obj)
c.pyapi.decref(component_obj)
c.pyapi.decref(l_obj)
c.pyapi.decref(bnd_obj)
c.pyapi.decref(t_lower_obj)
c.pyapi.decref(t_upper_obj)
c.pyapi.decref(static_obj)
c.pyapi.decref(class_obj)
```

**14 manual `decref()` calls** (7 in unboxing, 8 in boxing) are required to prevent memory leaks. This is error-prone:
- If a field is added, must remember to add corresponding `decref()`
- If a `decref()` is missed, memory leak occurs
- If a `decref()` is duplicated, use-after-free crash occurs
- No compiler enforcement of correctness

**Impact:**
- Maintenance burden during code modifications
- Memory leaks if reference counting is incorrect
- Same issue as BUG-036 in world_type.py
- Code duplication (BUG-056) means this fragility exists in two places

**Fix:**
Use RAII pattern or context manager for automatic cleanup:
```python
from contextlib import contextmanager

@contextmanager
def managed_pyobject(c, obj):
    try:
        yield obj
    finally:
        c.pyapi.decref(obj)

# Usage:
with managed_pyobject(c, name_obj) as name:
    fact.name = c.unbox(numba.types.string, name).value
# Automatic decref when exiting context
```

Alternatively, Numba may provide utilities for automatic reference management that should be investigated.

**Note:** This is a general pattern in all Classic Extension API types. Consider standardizing across all wrappers.

---

### BUG-059: Inconsistent Naming Between Python and Native Representations
**Severity:** LOW
**Location:** `fact_node_type.py:129-135`, `fact_edge_type.py:129-135`
**Description:**
```python
# Python class (fact_node.py):
def __init__(self, name, component, label, interval, ...):
    self._name = name         # ← Underscore prefix (private convention)
    self._component = component
    self._label = label
    self._interval = interval
    # ... etc

# Numba unboxing (fact_node_type.py:129-135):
name_obj = c.pyapi.object_getattr_string(obj, "_name")  # ← Must use underscore
component_obj = c.pyapi.object_getattr_string(obj, "_component")
l_obj = c.pyapi.object_getattr_string(obj, "_label")
bnd_obj = c.pyapi.object_getattr_string(obj, "_interval")

# Native struct (fact_node_type.py:46-52):
members = [
    ('name', numba.types.string),      # ← No underscore (public)
    ('component', ...),
    ('l', label.label_type),           # ← Different name! (label → l)
    ('bnd', interval.interval_type),   # ← Different name! (interval → bnd)
]
```

There are **naming inconsistencies** across the Python/native boundary:
- Python uses `_label`, native uses `l`
- Python uses `_interval`, native uses `bnd`
- Python uses underscore prefix (private), native doesn't

**Impact:**
- Confusing for developers working across boundaries
- Name `l` is cryptic (single letter) - unclear what it represents
- Inconsistent with Python naming conventions
- Makes code harder to read and maintain

**Fix:**
Use consistent names across both representations:
```python
# Option 1: Match Python names
members = [
    ('name', numba.types.string),
    ('component', ...),
    ('label', label.label_type),      # ← Full name
    ('interval', interval.interval_type),  # ← Full name
    ('t_lower', numba.types.uint32),
    ('t_upper', numba.types.uint32),
    ('static', numba.types.boolean)
]

# Option 2: Use full descriptive names everywhere
self.name = name  # Remove underscore if not truly private
self.component = component
self.label = label
self.interval = interval
```

**Note:** The abbreviations `l` and `bnd` may be historical - check if they're used extensively in reasoning engine code before renaming.

---

## `scripts/numba_wrapper/numba_types/rule_type.py`

### BUG-076: Broken Constructor Implementation - Dead Code
**Severity:** HIGH
**Location:** `scripts/numba_wrapper/numba_types/rule_type.py:16, 32-38, 82-107`

**Description:**
The file has explicit warning comments stating the constructor doesn't work:
```python
# Line 16:
# WARNING: problem with constructing inside jit function (not needed for now)

# Line 32:
# Construct object from Numba functions (Doesn't work. We don't need this currently)
@type_callable(Rule)
def type_rule(context):
    def typer(rule_name, type, target, head_variables, delta, clauses, bnd, thresholds, ann_fn, weights, head_fns, head_fns_vars, edges, static):
        # ... 14 argument type checking
```

The `@lower_builtin` implementation (lines 82-107) includes ~80 lines of manual reference counting and struct construction that never executes successfully.

**Impact:**
- ~80 lines of dead code that must be maintained
- Misleading API - developers might assume the constructor works
- No clear documentation of WHY it's broken
- Wastes compilation time registering broken lowering code
- If someone tries to use it, fails with cryptic Numba errors

**Fix:**
Remove the broken `@lower_builtin` implementation entirely:
```python
# KEEP @type_callable - needed for type system registration
@type_callable(Rule)
def type_rule(context):
    def typer(rule_name, type, target, ...):
        if isinstance(rule_name, types.UnicodeType) and ...:
            return rule_type
    return typer

# REMOVE @lower_builtin - broken implementation
# Delete lines 82-107

# Add clear documentation:
# NOTE: Rule objects CANNOT be constructed inside JIT code.
# Rules must be created in Python via rule_parser.parse_rule()
# and passed to JIT functions. This limitation exists due to:
# - 14 complex fields including nested typed collections
# - Circular dependencies with Label and Interval types
# - List-of-lists type complexity (head_fns_vars)
```

**Note:** The `@type_callable` registration is still necessary for Numba to recognize Rule as a valid type. Only the constructor implementation (`@lower_builtin`) should be removed. Any future need to construct Rules in JIT code would be a feature request, not a bug fix.

**Comparison with other types:**
- **World**: Classic pattern, constructor WORKS, heavily used in JIT
- **Label**: Classic pattern, constructor WORKS, used in JIT
- **Interval**: StructRef pattern, constructor WORKS automatically
- **Fact**: Classic pattern, constructor defined but never used
- **Rule**: Classic pattern, constructor BROKEN, explicitly marked non-functional

---

### BUG-077: Incomplete Mutability - Missing Setters
**Severity:** HIGH
**Location:** `scripts/numba_wrapper/numba_types/rule_type.py:153-157`

**Description:**
Only ONE setter is implemented in the Numba wrapper:
```python
@overload_method(RuleType, "set_clauses")
def set_clauses(rule):
    def setter(rule, clauses):
        rule.clauses = clauses
    return setter
```

But `rule_internal.py:73-88` has THREE setters:
- `set_rule_name()` - NOT in Numba wrapper
- `set_clauses()` - Present
- `set_thresholds()` - NOT in Numba wrapper

**Impact:**
- JIT code cannot modify `rule_name` even though Python API allows it
- JIT code cannot modify `thresholds` even though Python API allows it
- Inconsistent mutation semantics across Python/JIT boundary
- If JIT code receives a rule and tries to use Python setters, changes might not persist

**Fix:**
Either complete the API by adding missing setters:
```python
@overload_method(RuleType, "set_rule_name")
def set_rule_name(rule):
    def setter(rule, rule_name):
        rule.rule_name = rule_name
    return setter

@overload_method(RuleType, "set_thresholds")
def set_thresholds(rule):
    def setter(rule, thresholds):
        rule.thresholds = thresholds
    return setter
```

Or remove ALL setters if rules should be immutable:
```python
# Remove set_clauses from both rule_type.py and rule_internal.py
# Document that rules are immutable after construction
```

**Note:** Decision depends on whether rule mutation is intentional design or technical debt.

---

### BUG-078: Pattern Mixing Creates Architectural Inconsistency
**Severity:** MEDIUM
**Location:** `scripts/numba_wrapper/numba_types/rule_type.py:1-301` (entire file)

**Description:**
PyReason uses TWO different Numba extension patterns inconsistently:
- **Classic Extension**: Label, Fact, Rule - separate memory, boxing/unboxing copies data
- **StructRef**: Interval, World - shared memory, zero-copy mutations

This creates confusing mutation semantics:
```python
# In JIT code:
rule.bnd.lower = 0.5  # Mutates in place (bnd is Interval, uses StructRef)
rule.target.value = "new"  # NO - target field immutable (Label uses Classic)
rule.set_clauses(new_clauses)  # Must use setter (Rule uses Classic)
```

**Impact:**
- Confusing API: Some nested fields mutable, some not
- Performance inconsistency: Classic pattern copies data, StructRef doesn't
- Maintenance burden: Two patterns to understand and debug
- Future migration: Moving to StructRef breaks compatibility

**Fix:**
For PyReason 2.0 rewrite, unify on StructRef pattern for ALL types:
- Consistent mutation semantics
- Better performance (no boxing/unboxing overhead)
- Less boilerplate (~50 lines vs ~300 lines per type)
- Easier to understand and maintain

**Note:** This is an architectural design decision, not strictly a bug. But consistency is valuable.

---

### BUG-079: Getter Naming Inconsistency - Singular vs Plural
**Severity:** LOW
**Location:** `scripts/numba_wrapper/numba_types/rule_type.py:188-199`

**Description:**
Method names don't match field plurality:
```python
@overload_method(RuleType, "get_head_function")  # Singular
def get_head_function(rule):
    def impl(rule):
        return rule.head_fns  # Returns list (plural)
    return impl

@overload_method(RuleType, "get_head_function_vars")  # Singular "function"
def get_head_function_vars(rule):
    def impl(rule):
        return rule.head_fns_vars  # Plural "fns"
    return impl
```

**Impact:**
- Minor naming confusion
- Misleads developers expecting single value
- Inherited from `rule_internal.py:61-65` which has same naming

**Fix:**
Rename to match plurality:
```python
@overload_method(RuleType, "get_head_functions")  # Plural
@overload_method(RuleType, "get_head_functions_vars")  # Plural
```

Or document clearly: "Despite singular name, returns list of functions."

---

### BUG-080: Inconsistent Inner Function Naming
**Severity:** LOW
**Location:** `scripts/numba_wrapper/numba_types/rule_type.py:111-213` (all getters)

**Description:**
Getters use inconsistent inner function names:
```python
@overload_method(RuleType, "get_name")
def get_name(rule):
    def getter(rule):  # Named "getter"
        return rule.rule_name
    return getter

@overload_method(RuleType, "get_bnd")
def get_bnd(rule):
    def impl(rule):  # Named "impl"
        return rule.bnd
    return impl

@overload_method(RuleType, "set_clauses")
def set_clauses(rule):
    def setter(rule, clauses):  # Named "setter"
        rule.clauses = clauses
    return setter
```

Some use `getter`, some use `impl`, some use `setter`.

**Impact:**
- Minor: Harder to skim code
- No functional impact (inner functions are anonymous to Numba)

**Fix:**
Standardize on `impl` (matches Numba conventions):
```python
def getter(rule):  →  def impl(rule):
def setter(rule, x):  →  def impl(rule, x):
```

---

## Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| CRITICAL | 6 | interval.py, interval_type.py, fact_parser.py, fact_node.py, fact_edge.py, fact_node_type.py, fact_edge_type.py |
| HIGH | 3 | world.py, fact_parser.py, fact.py/fact_node.py/fact_edge.py |
| MEDIUM | 21 | interval.py, interval_type.py, label.py, label_type.py, threshold.py, rule_parser.py, world.py, world_type.py, fact_parser.py, fact.py/fact_node.py/fact_edge.py, fact_node_type.py, fact_edge_type.py |
| LOW | 30 | interval.py, label.py, label_type.py, threshold.py, world.py, world_type.py, fact_parser.py, fact.py, fact_node.py, fact_edge.py, fact_node_type.py, fact_edge_type.py |
| **TOTAL** | **60** | **14** |

---

## `scripts/annotation_functions/annotation_functions.py`

### BUG-081: O(n²) Performance - np.append in Loop
**Severity:** HIGH
**Location:** `annotation_functions.py:14, 24`
**Description:**
```python
weighted_sum = np.arange(0, dtype=np.float64)  # Empty array
for i, clause in enumerate(annotations):
    s = 0
    for annotation in clause:
        annotation_cnt += 1
        if mode=='lower':
            s += annotation.lower * weights[i]
        elif mode=='upper':
            s += annotation.upper * weights[i]
    weighted_sum = np.append(weighted_sum, s)  # ← O(n) copy each iteration
```
NumPy arrays are immutable. `np.append()` allocates a new array, copies all existing elements, then adds the new element. With `n` clauses, this performs `1 + 2 + 3 + ... + n = O(n²)` operations.

**Impact:**
- With 100 clauses: ~5,000 array allocations and copies
- With 1,000 clauses: ~500,000 array allocations → severe performance degradation
- Completely defeats the purpose of Numba JIT compilation
- Memory thrashing in inner reasoning loops (annotations computed every timestep)
- All 4 public functions (`average`, `average_lower`, `maximum`, `minimum`) affected

**Fix:**
Preallocate array with known size:
```python
@numba.njit
def _get_weighted_sum(annotations, weights, mode='lower'):
    n_clauses = len(annotations)
    weighted_sum = np.zeros(n_clauses, dtype=np.float64)
    annotation_cnt = 0

    for i, clause in enumerate(annotations):
        s = 0
        for annotation in clause:
            annotation_cnt += 1
            if mode == 'lower':
                s += annotation.lower * weights[i]
            elif mode == 'upper':
                s += annotation.upper * weights[i]
        weighted_sum[i] = s  # ← O(1) assignment

    return weighted_sum, annotation_cnt
```

**Note:**
This is one of the most severe performance bugs in the entire codebase, as annotation functions are called repeatedly during reasoning over large graphs. The O(n²) behavior makes the system unusable for rules with many clauses.

---

### BUG-082: Unused Return Value - Wasted Computation
**Severity:** MEDIUM
**Location:** `annotation_functions.py:78, 94`
**Description:**
```python
# In maximum():
weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')
weighted_sum_upper, n = _get_weighted_sum(annotations, weights, mode='upper')
#                    ↑ 'n' computed but never used

# In minimum():
weighted_sum_lower, n = _get_weighted_sum(annotations, weights, mode='lower')
weighted_sum_upper, n = _get_weighted_sum(annotations, weights, mode='upper')
#                    ↑ 'n' computed but never used
```
The `_get_weighted_sum` helper counts all annotations across all clauses, but `maximum()` and `minimum()` don't need this value. They only use the weighted sums for max/min operations.

**Impact:**
- Wasted computation iterating through all annotations just to count them
- Inner loop overhead accumulates when annotation functions called repeatedly
- Code confusion - why return a value that's not used?

**Fix:**
Either:
1. **Option A**: Make annotation count optional (use -1 sentinel when not needed)
2. **Option B**: Split into two functions - `_get_weighted_sum_with_count()` and `_get_weighted_sum()`
3. **Option C**: Accept the minor overhead as cleaner than having two versions

**Note:**
Less severe than BUG-081 (O(n) overhead vs O(n²)), but still wasteful in hot paths.

---

### BUG-083: Inconsistent Semantics - Weighted Sum vs Annotation Count
**Severity:** LOW
**Location:** `annotation_functions.py:39-52, 55-70`
**Description:**
The `average()` and `average_lower()` functions have semantically confused aggregation logic:
NOTE: This assumes a clause can have multiple annotations, which it cannot.  Logic is fine but could be written in more consistenly. Read the rest of the AI slop with this in mind.
```python
# Weights are per-clause (outer loop):
for i, clause in enumerate(annotations):
    s = 0
    for annotation in clause:
        annotation_cnt += 1  # ← Counting individual annotations
        s += annotation.lower * weights[i]  # ← But multiplying by clause weight
    weighted_sum = np.append(weighted_sum, s)

# Then dividing by annotation count, not clause count:
avg_lower = np.sum(weighted_sum) / n  # ← n is total annotation count
```

**Problem**: The math combines two different levels of aggregation inconsistently:
1. **Inner level**: Weights apply to clauses, so `weights[i]` multiplies each annotation in clause `i`
2. **Outer level**: Division by `annotation_cnt` (total across all clauses) instead of sum of weights

**Example showing the inconsistency:**
```
Rule: infected(X) ← contact(X,Y), infected(Y)
Clause 1 weight: 0.5
Clause 2 weight: 1.0

Clause 1 has 3 matching bindings: [0.8, 0.8], [0.9, 0.9], [0.7, 0.7] # This doesn't make sense, every clause only has one interval
Clause 2 has 1 matching binding: [0.6, 0.6]

Current computation:
  weighted_sum[0] = (0.8 + 0.9 + 0.7) * 0.5 = 1.2
  weighted_sum[1] = 0.6 * 1.0 = 0.6
  avg = (1.2 + 0.6) / 4 annotations = 0.45

But what does this mean? The weight 0.5 reduced clause 1's contribution, but then we divided by the number of annotations, which doesn't account for weights at all.
```

**Impact:**
- Unclear semantics - what does the "average" actually represent?
- Weights don't behave as expected - not a true weighted average
- Results depend on how many bindings each clause has, not just their weighted values
- Mathematical inconsistency makes rewrite correctness verification difficult

**Fix:**
Need to decide on clear semantics. Options:
1. **Weighted average of clause contributions** (divide by sum of weights, not annotation count):
   ```python
   avg_lower = np.sum(weighted_sum) / np.sum(weights)
   ```
2. **Average of weighted annotations** (weight each individual annotation, not clauses):
   ```python
   # Apply weights at annotation level, not clause level
   # Requires restructuring the loop
   ```
3. **Two-stage aggregation** (average within clauses, then weighted average across clauses):
   ```python
   # First average annotations within each clause, then weighted combine
   ```

**Note:**
This is a design-level bug that requires clarifying the intended semantics before fixing.

---

### BUG-084: No Input Validation
**Severity:** MEDIUM
**Location:** `annotation_functions.py:9-101` (all functions)
**Description:**
None of the annotation functions validate their inputs. No checks for:
1. **Weights array length matches annotations length**:
   ```python
   annotations = [[...], [...], [...]]  # 3 clauses
   weights = [0.5, 1.0]                  # Only 2 weights → IndexError on weights[2]
   ```
2. **Weights are non-negative**: Negative weights could produce nonsensical intervals
3. **Annotations list is non-empty**: Division by zero if no annotations (line 47)
4. **Annotations are valid intervals**: Could pass malformed intervals with `lower > upper` or out of `[0,1]` range

**Impact:**
- **IndexError** if weights array is shorter than annotations (will crash JIT function)
- **Division by zero** if annotations list is empty (line 47: `/ n` when `n=0`)
- **Silent garbage output** if weights are negative or intervals are malformed
- Hard-to-debug crashes because Numba error messages are cryptic

**Fix:**
Add validation at function entry:
```python
@numba.njit
def average(annotations, weights):
    # Validate inputs
    if len(annotations) == 0:
        return interval.closed(0, 1)  # Or raise error
    if len(weights) != len(annotations):
        return interval.closed(0, 1)  # Or raise error

    # ... rest of function
```

**Note:**
Validation has small performance cost, but prevents crashes. Could be optional (debug mode only) if performance is critical.

---

### BUG-085: Questionable _check_bound Logic
**Severity:** MEDIUM
**Location:** `annotation_functions.py:29-35`
**Description:**
```python
@numba.njit
def _check_bound(lower, upper):
    if lower > upper:
        return (0, 1)  # ← Returns maximally uncertain interval
    else:
        lower_bound = min(lower, 1)  # ← Clamps upper end but not lower
        upper_bound = min(upper, 1)
        return (lower_bound, upper_bound)
```

**Problems:**
1. **If `lower > upper`**: Returns `[0, 1]` (maximally uncertain), throwing away all information
   - This can hide bugs in annotation function logic
   - Why not swap them or raise an error?
2. **Only clamps to 1, not to 0**: Uses `min(x, 1)` but doesn't ensure `x >= 0`
   - Negative values will pass through: `_check_bound(-0.5, 0.5)` returns `(-0.5, 0.5)`
3. **Asymmetric handling**: Upper bounds get clamped but lower bounds don't
   - If `lower = 1.5`, returns `(1, 1)` ← valid but information loss
   - If `lower = -0.5`, returns `(-0.5, 1)` ← invalid interval!

**Impact:**
- Invalid intervals can silently propagate through the system
- `[0, 1]` fallback masks bugs instead of failing fast
- Negative intervals will cause downstream errors in interval operations

**Fix:**
```python
@numba.njit
def _check_bound(lower, upper):
    # Clamp to [0, 1] first
    lower = max(0.0, min(lower, 1.0))
    upper = max(0.0, min(upper, 1.0))

    # Ensure lower <= upper
    if lower > upper:
        # Option 1: Swap them
        return (upper, lower)
        # Option 2: Take midpoint
        # mid = (lower + upper) / 2
        # return (mid, mid)
        # Option 3: Return [0,1] but log a warning

    return (lower, upper)
```

**Note:**
The current behavior (return `[0,1]` on invalid) might be intentional as a "safe fallback," but it hides bugs and should at least log a warning.

---

### BUG-086: Missing Annotation Functions
**Severity:** LOW
**Location:** `annotation_functions.py:1` (comment), entire file
**Description:**
```python
# Line 1:
# List of annotation functions will come here. All functions to be numba decorated and compatible
```
The comment suggests more functions are planned, but only 4 are implemented:
- `average` - Weighted average of both bounds
- `average_lower` - Weighted average of lower, max of upper
- `maximum` - Max of both bounds
- `minimum` - Min of both bounds

**Missing common annotation functions:**
1. **`average_upper`** - Max of lower, weighted average of upper (dual of `average_lower`)
2. **`pessimistic_average`** - Min of lower, average of upper (cautious)
3. **`optimistic_average`** - Average of lower, max of upper (same as `average_lower`?)
4. **`product`** - Probabilistic independence: `lower1 * lower2`, used in Bayesian reasoning
5. **`bounded_sum`** - Lukasiewicz T-conorm: `min(1, sum(...))`
6. **`identity`** - Return first annotation unchanged (for rules with single clause)
7. **`threshold`** - Return 1 if average > threshold, else 0 (binarization)

**Impact:**
- Limited expressiveness for complex reasoning scenarios
- Users may need to implement custom functions
- Some rule semantics cannot be expressed (e.g., probabilistic independence)

**Fix:**
Implement missing functions or document that current set is complete and sufficient for PyReason's use cases.

**Note:**
This might be intentional minimalism. Without seeing how annotation functions are used in the reasoning engine, hard to judge if this is a real gap or YAGNI.

---

### BUG-087: Redundant Manual Max Computation
**Severity:** LOW
**Location:** `annotation_functions.py:63-66`
**Description:**
```python
# In average_lower():
max_upper = 0
for clause in annotations:
    for annotation in clause:
        max_upper = annotation.upper if annotation.upper > max_upper else max_upper
```
This manually finds the maximum upper bound, but could use NumPy's vectorized `np.max()` for clarity and potential performance.

**Impact:**
- Minor: Manual loop is clear and Numba will optimize it well
- Readability: Inconsistent with `maximum()` which uses `np.max(weighted_sum_upper)`

**Fix:**
```python
# Collect all upper bounds
uppers = np.array([annotation.upper for clause in annotations for annotation in clause])
max_upper = np.max(uppers)
```
Or build array in loop then take max.

**Note:**
Very minor issue. Current code is fine, just inconsistent with other functions' style.

---

### BUG-088: String Mode Parameter Should Be Boolean
**Severity:** LOW
**Location:** `annotation_functions.py:9, 20-23`
**Description:**
```python
def _get_weighted_sum(annotations, weights, mode='lower'):
    # ...
    if mode=='lower':
        s += annotation.lower * weights[i]
    elif mode=='upper':
        s += annotation.upper * weights[i]
```
The `mode` parameter is a string with only two values: `'lower'` or `'upper'`. String comparisons are slower than boolean checks, and the API is less type-safe.

**Impact:**
- Typo like `mode='Lower'` will silently fail (neither branch executes, `s` stays 0)
- String comparison overhead (minor, but in inner loop)
- Less clear API - booleans are self-documenting: `use_lower=True`

**Fix:**
```python
def _get_weighted_sum(annotations, weights, use_lower=True):
    # ...
    if use_lower:
        s += annotation.lower * weights[i]
    else:
        s += annotation.upper * weights[i]
```

**Note:**
Extremely minor. Current approach is readable enough. Only worth changing if doing major refactor.

---

## `scripts/utils/query_parser.py`

### BUG-089: No Input Validation in parse_query
**Severity:** HIGH
**Location:** `query_parser.py:5-34`
**Description:**
The parser has ZERO validation and will crash on any malformed input:
```python
# Examples that crash:
parse_query("infected")              # IndexError: line 24, no '('
parse_query("infected(")             # ValueError: line 26, no closing ')'
parse_query("(alice)")               # Creates Label('') - empty predicate
parse_query("infected() : [1, x]")   # ValueError: float conversion fails
parse_query("infected(alice) : [1.0, 0.0]")  # Creates inverted interval
```

All parsing errors produce Python stack traces instead of user-friendly error messages.

**Impact:**
- Crashes instead of graceful error handling
- No validation of semantic correctness (inverted intervals, empty strings)
- Silent bugs with edge cases (empty predicates, invalid bounds)
- Users cannot distinguish syntax errors from semantic errors

**Fix:**
Add comprehensive validation:
1. Check for empty/whitespace-only queries
2. Validate parentheses structure: `'(' in query and ')' in query`
3. Validate bounds format: `[lower,upper]` with exactly 2 numeric values
4. Validate interval constraints: `0 <= lower <= upper <= 1`
5. Validate predicate and component are non-empty
6. For edges, validate exactly 2 components

---

### BUG-090: Query Negation Only Works for Default Bounds
**Severity:** CRITICAL
**Location:** `query_parser.py:14-16`
**Description:**
The negation logic (`~` prefix) only applies when no explicit bounds are provided:
```python
if query[0] == '~':
    pred_comp = query[1:]
    lower, upper = 0, 0
```

This means:
- `~infected(alice)` → [0, 0] ✓ Works as expected
- `~infected(alice) : [0.5, 0.7]` → Tilde treated as part of predicate name!
  - Becomes `Label("~infected")` with bounds [0.5, 0.7]
  - Negation is silently ignored

**Impact:**
- Confusing semantics: negation only works without explicit bounds
- Users might write `~pred(x) : [0.8, 1.0]` expecting negation to apply
- Silent bug: tilde becomes part of predicate name, won't match any facts
- No error or warning when negation is ignored

**Fix:**
Either:
1. Raise error if tilde used with explicit bounds: `"Cannot use negation (~) with explicit bounds"`
2. Apply negation to explicit bounds (e.g., invert interval semantically)
3. Document clearly that `~` only works for default bounds

---

### BUG-091: Component Type Detection Is Fragile
**Severity:** MEDIUM
**Location:** `query_parser.py:28-32`
**Description:**
Edge detection uses simple comma check:
```python
if ',' in component:
    component = tuple(component.split(','))
    comp_type = 'edge'
else:
    comp_type = 'node'
```

**Problems:**
- Node name with comma: `infected(Alice,Jr)` → Misclassified as edge with components `('Alice', 'Jr')`
- Extra commas: `friend(alice,,bob)` → Creates tuple `('alice', '', 'bob')` (3 elements!)
- More than 2 components: `predicate(a,b,c)` → 3-tuple, but edges require exactly 2
- No validation that edges have exactly 2 components

**Impact:**
- Node names containing commas are misclassified as edges
- Invalid edge queries (with 1 or 3+ components) pass through without error
- Downstream code may crash or behave unexpectedly with wrong component types

**Fix:**
```python
if ',' in component:
    parts = component.split(',')
    if len(parts) != 2:
        raise ValueError(f"Edge queries must have exactly 2 components, got {len(parts)}: {component}")
    if not all(p.strip() for p in parts):
        raise ValueError(f"Edge components cannot be empty: {component}")
    component = tuple(parts)
    comp_type = 'edge'
else:
    comp_type = 'node'
```

---

### BUG-092: No Validation of Predicate Name Format
**Severity:** MEDIUM
**Location:** `query_parser.py:25`
**Description:**
Predicate names are extracted without validation:
```python
pred = label.Label(pred_comp[:idx])
```

**Problems:**
- Special characters: `pred!@#(alice)` → Label("pred!@#")
- Numeric names: `123(alice)` → Label("123")
- Reserved keywords: `if(alice)` → Label("if")
- Empty predicate: `(alice)` → Label("") (if no validation added for BUG-089)
- Leading/trailing whitespace in weird edge cases

**Impact:**
- May create predicates that don't match any facts/rules in the knowledge base
- Debugging confusion: "Why doesn't my query match my fact?"
- Inconsistency: PyReason likely expects identifier-style predicate names

**Fix:**
Add validation:
```python
pred_str = pred_comp[:idx].strip()
if not pred_str:
    raise ValueError("Predicate name cannot be empty")
if not pred_str.replace('_', '').isalnum():  # Allow underscores
    raise ValueError(f"Predicate name must be alphanumeric, got: {pred_str}")
pred = label.Label(pred_str)
```

**Note:** Could use `str.isidentifier()` for Python identifier rules, but may be too restrictive.

---

## `scripts/query/query.py`

### BUG-093: Query Class Over-Engineers Encapsulation
**Severity:** LOW
**Location:** `query.py:17-30`
**Description:**
The `Query` class stores parsed components as "private" fields with double underscore prefix:
```python
self.__pred, self.__component, self.__comp_type, self.__bnd = parse_query(query_text)
```

And provides verbose getter methods:
```python
def get_predicate(self):
    return self.__pred

def get_component(self):
    return self.__component
```

**Issues:**
- **Over-engineering**: Simple data container doesn't need private fields with name mangling
- **Verbosity**: `query.get_predicate()` vs cleaner `query.predicate`
- **Inconsistency**: Other PyReason classes use direct attribute access:
  - `Interval.lower` and `Interval.upper` (not `get_lower()`)
  - `Label.value` is accessible directly
  - `Threshold.quantifier` is accessible

**Impact:**
- Minimal - getter methods work fine
- Slightly more verbose API than necessary
- Inconsistent with codebase patterns
- Python name mangling (`_Query__pred`) serves no purpose here

**Fix:**
Simplify to direct attribute access:
```python
class Query:
    def __init__(self, query_text: str):
        self.pred, self.component, self.comp_type, self.bnd = parse_query(query_text)
        self.query_text = query_text

    # Keep __str__ and __repr__
```

---

### BUG-094: No Semantic Equality for Queries
**Severity:** LOW
**Location:** `query.py:4-36` (entire class)
**Description:**
The `Query` class does not implement `__eq__` or `__hash__`, relying on default identity comparison:
```python
q1 = Query("infected(alice) : [1.0, 1.0]")
q2 = Query("infected(alice)")  # Semantically identical (defaults to [1,1])

q1 == q2  # False! Different objects, different query_text strings
```

**Impact:**
- Queries with identical semantics but different string representations are not equal
- Cannot use queries reliably in sets or as dictionary keys
- Confusing behavior: semantically identical queries test as unequal
- Comparison is by identity, not by parsed components

**Examples:**
```python
Query("infected(alice)") != Query("infected( alice )")  # Same after space removal
Query("infected(alice) : [1, 1]") != Query("infected(alice)")  # Semantically identical
```

**Fix:**
Implement semantic equality:
```python
def __eq__(self, other):
    if not isinstance(other, Query):
        return False
    return (self.__pred == other.__pred and
            self.__component == other.__component and
            self.__comp_type == other.__comp_type and
            self.__bnd == other.__bnd)

def __hash__(self):
    # Make hashable for use in sets/dicts
    comp_hash = self.__component if isinstance(self.__component, str) else tuple(self.__component)
    return hash((self.__pred, comp_hash, self.__comp_type,
                 self.__bnd.lower, self.__bnd.upper))
```

---

### BUG-095: Inconsistent Space Handling Behavior
**Severity:** LOW
**Location:** `query_parser.py:6`
**Description:**
All spaces are stripped globally at the start:
```python
query = query.replace(' ', '')
```

This means:
- `infected( alice )` → `infected(alice)` ✓ Works as intended
- `infected(New York)` → `infected(NewYork)` ✗ Removes spaces in entity names
- Edge whitespace: `friend( alice , bob )` → `friend(alice,bob)` ✓ Works

**Impact:**
- Entity names cannot contain spaces (e.g., "New York", "Alice Jr")
- May be intentional if PyReason doesn't support spaces in entity names
- No clear documentation of this limitation
- Could surprise users expecting standard identifier parsing

**Note:**
This is likely **intentional design** matching PyReason's entity naming conventions. Entity names probably should not contain spaces for graph consistency. However, it should be documented.

**Fix (if spaces should be allowed):**
Strip spaces more selectively:
```python
# Remove spaces outside of component names
query = re.sub(r'\s+(?![^()]*\))', '', query)
# Remove spaces around colons and brackets
query = query.replace(' :', ':').replace(': ', ':')
query = query.replace(' [', '[').replace('[ ', '[')
```

Or document clearly: "Entity names in queries cannot contain spaces."

---

## Next Review Target
According to analysis flow, continue with Layer 3 utilities or Layer 5 domain objects:
- `scripts/utils/yaml_parser.py`
- `scripts/utils/graphml_parser.py`

### BUG-096: Deprecated File with 85% Dead Code
**Severity:** MEDIUM  
**Location:** `scripts/utils/yaml_parser.py` (entire file)

**Description:**
The file contains 196 lines but only 9 lines (5%) are actually used. Three of four functions are dead code from a deprecated YAML-based loading system:

**Dead Code (167 lines, never called):**
- `parse_rules()` - 96 lines (lines 12-107)
- `parse_facts()` - 38 lines (lines 110-148)
- `parse_labels()` - 33 lines (lines 151-184)

**Active Code (9 lines):**
- `parse_ipl()` - 9 lines (lines 187-196) - called once at `pyreason.py:578`

**Evidence of deprecation:**
1. Line 95 comment: `# Dummy rule type. this file is deprecated`
2. Excluded from test coverage in `run_tests.py:267`: `*/yaml_parser.py`
3. Zero imports of the three dead functions anywhere in codebase

**Impact:**
- **Code maintenance burden**: Developers must read/understand 167 lines of unused code
- **Confusion**: New contributors may think YAML-based rule loading is supported
- **Bitrot risk**: Dead code not tested or maintained, may break dependencies
- **Misleading documentation**: Functions exist but don't work with current system

**Fix:**
Option 1 (Recommended): Delete dead code, keep only `parse_ipl()`:
```python
# yaml_parser.py - only 20 lines after cleanup
import yaml
import numba
import pyreason.scripts.numba_wrapper.numba_types.label_type as label

def parse_ipl(path):
    """Load inconsistent predicate list from YAML file."""
    with open(path, 'r') as file:
        ipl_yaml = yaml.safe_load(file)
    
    ipl = numba.typed.List.empty_list(numba.types.Tuple((label.label_type, label.label_type)))
    if ipl_yaml['ipl'] is not None:
        for labels in ipl_yaml['ipl']:
            ipl.append((label.Label(labels[0]), label.Label(labels[1])))
    
    return ipl
```

Option 2: Move `parse_ipl()` to a new `ipl_parser.py` and delete entire file

Option 3: Add deprecation warnings and comments directing users to new parsers

**Note:**
The modern system uses `rule_parser.py` and `fact_parser.py` (already analyzed) for loading rules and facts programmatically. This represents a major architectural shift from YAML-based configuration to Python-based rule definition.

---

### BUG-097: O(n) Duplicate Check in Reverse Neighbor Construction
**Severity:** MEDIUM  
**Location:** `scripts/interpretation/interpretation.py:122`

**Description:**
The `_init_reverse_neighbors` function checks for duplicates using `n not in reverse_neighbors[neighbor_node]`, which performs a linear search through the list on every append operation.

```python
for neighbor_node in neighbor_nodes:
    if neighbor_node in reverse_neighbors and n not in reverse_neighbors[neighbor_node]:
        reverse_neighbors[neighbor_node].append(n)
```

For a graph with E edges and average degree D, this becomes O(E × D) instead of O(E).

**Impact:**
- Initialization time scales quadratically with graph connectivity
- For dense graphs (high D), this becomes a significant bottleneck
- Example: Graph with 1000 nodes, average degree 50 → 50,000 O(50) operations = 2.5M list scans

**Fix:**
Use a set for duplicate detection, then convert to list:
```python
reverse_neighbors_sets = {}
for n, neighbor_nodes in neighbors.items():
    for neighbor_node in neighbor_nodes:
        if neighbor_node not in reverse_neighbors_sets:
            reverse_neighbors_sets[neighbor_node] = set()
        reverse_neighbors_sets[neighbor_node].add(n)
    if n not in reverse_neighbors_sets:
        reverse_neighbors_sets[n] = set()

# Convert to numba typed lists
reverse_neighbors = numba.typed.Dict.empty(...)
for node, neighbor_set in reverse_neighbors_sets.items():
    reverse_neighbors[node] = numba.typed.List(neighbor_set)
```

**Note:**
Numba may not support sets in njit mode, requiring this to be done outside njit or with alternative approach.

---

### BUG-098: Unnecessary Reverse Neighbor Entry Check
**Severity:** LOW  
**Location:** `scripts/interpretation/interpretation.py:122`

**Description:**
The condition checks both `neighbor_node in reverse_neighbors` AND `n not in reverse_neighbors[neighbor_node]`:

```python
if neighbor_node in reverse_neighbors and n not in reverse_neighbors[neighbor_node]:
    reverse_neighbors[neighbor_node].append(n)
else:
    reverse_neighbors[neighbor_node] = numba.typed.List([n])
```

The `else` branch unconditionally creates a new list, which will overwrite any existing entry. If `neighbor_node in reverse_neighbors` is true, the `else` shouldn't execute.

**Impact:**
- Logic error: existing reverse neighbors can be overwritten
- May cause incorrect neighbor relationships

**Fix:**
Restructure logic:
```python
if neighbor_node not in reverse_neighbors:
    reverse_neighbors[neighbor_node] = numba.typed.List.empty_list(node_type)
if n not in reverse_neighbors[neighbor_node]:
    reverse_neighbors[neighbor_node].append(n)
```

---

### BUG-099: Massive Parameter List Anti-Pattern
**Severity:** MEDIUM  
**Location:** `scripts/interpretation/interpretation.py:218`

**Description:**
The `reason()` method is called with **38 positional arguments**:
```python
fp_cnt, t = self.reason(self.interpretations_node, self.interpretations_edge, 
    self.predicate_map_node, self.predicate_map_edge, self.tmax, 
    self.prev_reasoning_data, rules, self.nodes, self.edges, 
    # ... 29 more arguments ...
    self._convergence_delta, self.num_ga, verbose, again)
```

**Impact:**
- **Unmaintainable**: Impossible to remember parameter order
- **Error-prone**: Easy to swap arguments of same type
- **Numba limitation**: All state must be passed as arguments since it's a static method
- **Refactoring nightmare**: Adding/removing parameters requires updating all call sites

**Fix:**
Since this is a Numba-compiled static method, options are limited:
1. Group related parameters into Numba-compatible struct types
2. Make `reason()` an instance method (if Numba allows)
3. Document parameter groups with clear comments
4. Consider if all 38 parameters are actually necessary

**Note:**
This is a fundamental tension between Numba's JIT compilation (requiring staticmethod + explicit parameters) and good OOP design. Likely intentional tradeoff for performance.

---

### BUG-100: String-Based Graph Attribute Detection
**Severity:** MEDIUM  
**Location:** `scripts/interpretation/interpretation.py:198, 206`

**Description:**
Graph attribute facts are detected by checking if the fact name equals the magic string `'graph-attribute-fact'`:

```python
graph_attribute = True if name=='graph-attribute-fact' else False
```

**Impact:**
- **Fragile**: Typos or case mismatches silently break functionality
- **Unclear contract**: Nothing enforces this naming convention
- **Implicit coupling**: Fact naming logic spread across codebase
- **No validation**: Invalid names accepted without error

**Fix:**
1. Define constant: `GRAPH_ATTRIBUTE_FACT_NAME = 'graph-attribute-fact'`
2. Or use enum/flag in Fact class: `fact.is_graph_attribute()`
3. Or check fact type directly: `isinstance(fact, GraphAttributeFact)`

Better approach:
```python
# In fact.py
class Fact:
    def is_graph_attribute(self):
        return self.is_graph_attr  # Explicit boolean flag

# In interpretation.py
graph_attribute = fact.is_graph_attribute()
```

---

### BUG-101: Initial Specific Label Intervals Always [0, 1]
**Severity:** LOW  
**Location:** `scripts/interpretation/interpretation.py:146, 165`

**Description:**
When specific labels are initialized (e.g., "Person(John)"), they're always set to interval [0.0, 1.0]:

```python
interpretations[n].world[l] = interval.closed(0.0, 1.0)
```

This represents "completely uncertain" - we don't know if John is a Person or not.

**Impact:**
- **Counterintuitive**: Specific labels from graph usually indicate known facts (e.g., node has attribute "Person")
- **Requires explicit fact**: User must add fact "Person(John): [1, 1]" even though node is labeled "Person"
- **Inconsistent semantics**: Why specify label if it means nothing initially?

**Fix:**
Initialize specific labels to [1.0, 1.0] (certain true) or make it configurable:

```python
# Option 1: Always certain
interpretations[n].world[l] = interval.closed(1.0, 1.0)

# Option 2: Configurable
initial_bound = settings.specific_label_initial_bound  # Default [1, 1]
interpretations[n].world[l] = interval.closed(initial_bound[0], initial_bound[1])
```

**Note:**
This may be intentional if specific labels just define "vocabulary" (possible predicates) rather than initial truth. Requires clarification of intended semantics.

---

!!!!!! THIS IS THE END OF BUG_LOG.md, as adding any more will exceed the context window.  Please see BUG_LOG_2.md for a continuation of this log.