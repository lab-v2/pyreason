# PyReason Public API Reference

This document covers the public-facing API exposed by [pyreason/pyreason.py](../pyreason/pyreason.py). It is the primary entry point users interact with after `import pyreason as pr`.

The API has three parts:

1. **Settings** — global flags on `pr.settings` that control how the reasoner behaves.
2. **Loader / builder functions** — load graphs, rules, facts, and custom functions into the reasoner.
3. **Reasoning and inspection functions** — run the reasoner and explore its output.

---

## 1. Settings

All settings are exposed as properties on the singleton `pr.settings` object (an instance of `_Settings`). Each is read via `pr.settings.<name>` and written via `pr.settings.<name> = value`. All boolean setters raise `TypeError` if a non-bool is supplied; the `update_mode` and `output_file_name` setters require strings.

Call `pr.reset_settings()` (or `pr.settings.reset()`) to restore every setting to its default.

### `verbose` — `bool` (default `True`)
Controls whether PyReason prints progress and diagnostic messages (rule filtering, optimization, the empty-graph warning, etc.) to stdout during reasoning. Set to `False` for silent runs.

### `output_to_file` — `bool` (default `False`)
When `True`, stdout is reassigned to a text file at the start of `reason()` (and again inside `_reason`). The file is created in the current working directory and named `<output_file_name>_<timestamp>.txt`, where the timestamp is generated at the top of `reason()`.

### `output_file_name` — `str` (default `'pyreason_output'`)
Base name used for the log file. It is interpolated into the open call only when `output_to_file` is `True`, so it has no effect otherwise. A timestamp is appended automatically.

### `graph_attribute_parsing` — `bool` (default `True`)
When `True`, node and edge attributes from the loaded graph (GraphML or NetworkX) are converted into PyReason facts at load time via `GraphmlParser.parse_graph_attributes`. When `False`, all four attribute structures are initialized as empty Numba containers, so only the topology survives.

### `abort_on_inconsistency` — `bool` (default `False`)
If `True`, the reasoner will raise/abort the moment it detects an inconsistency in the interpretation. If `False`, inconsistencies are resolved by setting the bounds of the inconsistent groundings to `[0,1]` and applying the `static` property to the grounding. Has no effect unless `inconsistency_check` is also `True`. The setting itself is declared on `_Settings` but is consumed inside the interpretation engines, not in `pyreason.py`.

### `memory_profile` — `bool` (default `False`)
When `True`, both branches of `reason()` wrap their inner call (`_reason` or `_reason_again`) in `memory_profiler.memory_usage(..., max_usage=True)` and print the peak memory delta against a baseline taken just before the call. Adds overhead — leave off for production runs.

### `reverse_digraph` — `bool` (default `False`)
When `True`, every edge `a -> b` in the loaded graph is reversed to `b -> a`. The flag is honored at load time (passed into `GraphmlParser.parse_graph`).

### `atom_trace` — `bool` (default `False`)
When `True`, PyReason records every atom (ground fact) responsible for each rule firing, enabling full explainability via `get_rule_trace` / `save_rule_trace`. **Memory-intensive** on large programs. Automatically forced to `False` if `store_interpretation_changes` is `False` because there is no trace storage to write into.

### `save_graph_attributes_to_trace` — `bool` (default `False`)
When `True`, graph attribute facts are also written into the rule trace. Because graphs can be large, this can dramatically inflate trace size and memory use. Off by default even when `atom_trace` is on.

### `canonical` — `bool` (default `False`) — **DEPRECATED**
Deprecated alias for `persistent`. Both the getter and setter delegate to the underlying `__persistent` field, so reading or writing `canonical` is identical to reading or writing `persistent`. Prefer `persistent` in new code.

### `persistent` — `bool` (default `False`)
Controls whether interpretations carry bounds forward across timesteps:
- `False` (non-persistent): bounds are reset at each timestep unless explicitly re-derived.
- `True` (persistent): bounds derived in earlier timesteps remain in force unless overridden.

The flag is consumed inside the interpretation engine selected by `Program.__init__`.


### `inconsistency_check` — `bool` (default `True`)
When `True`, the reasoner detects two kinds of inconsistencies at each update: (1) **IPL conflicts**, where the atom being updated is paired with another predicate in the inconsistent predicate list, and (2) **bound conflicts**, where the incoming bound cannot be reconciled with the existing bound under the current `update_mode` (e.g. an `'intersection'` update whose new interval does not intersect the old one). In both cases the reasoner calls `resolve_inconsistency_node` / `resolve_inconsistency_edge`, which clamps the offending grounding (and any IPL-paired groundings) to `[0,1]` and marks them `static=True` for the rest of the run. Set to `False` to skip the check entirely for a small speedup when you trust your rules.

### `static_graph_facts` — `bool` (default `True`)
When `True`, facts derived from graph attributes are marked **static** — they hold for all time and never expire. When `False`, they obey normal start/end times. The flag is consumed by `GraphmlParser.parse_graph_attributes` during graph loading, so it is only meaningful when `graph_attribute_parsing` is also `True`.


### `store_interpretation_changes` — `bool` (default `True`)
When `True`, every change made to the interpretation is recorded so it can be queried after reasoning. When `False`, the reasoner runs faster and uses less memory, but post-hoc inspection is unavailable — `atom_trace` is forced off, and every inspection helper asserts on this flag.

### `parallel_computing` — `bool` (default `False`)
When `True`, the `Program` selects the parallel `InterpretationParallel` engine instead of the single-threaded `Interpretation`, allowing the reasoner to use multiple CPU cores during inference. Whether Numba's JIT cache takes effect for the parallel engine depends on Numba's restrictions around caching `parallel=True` functions, so startup time after the first run may be slower than the single-threaded engine.

### `update_mode` — `str` (default `'intersection'`)
How newly derived bounds combine with existing bounds for the same atom:
- `'intersection'`: take the intersection of the old and new bounds (the default, "tighten only" semantics). This enforces **monotonic reasoning**, meaning that once a bound has been derived it can only ever be tightened, never loosened or retracted — the set of derivable conclusions only grows over time. Any update whose new interval does not intersect the old one is treated as an inconsistency (see `inconsistency_check`).
- `'override'`: replace the old bound with the new one. This permits non-monotonic updates, allowing previously derived conclusions to be loosened or contradicted by later updates.

The string is consumed inside the interpretation engine when applying updates. Note that the setter only checks that the value is a `str`, not that it is one of the two recognized modes.

### `allow_ground_rules` — `bool` (default `False`)
When `True`, rules may contain ground (constant) atoms in their bodies/heads. When `False`, rules must use only variables. Off by default for performance. Consumed by the interpretation engine when matching rule clauses against the graph.

### `fp_version` — `bool` (default `False`)
Selects the reasoning engine. `Program.__init__` branches on this flag:
- `False`: the optimized engine (`Interpretation`, timestep-driven, generally faster).
- `True`: the fixed-point engine (`InterpretationFP`, iterates clauses until a fixed point at each step). Useful for certain rule patterns that benefit from fixed-point semantics.

Note that `parallel_computing=True` overrides this — the parallel engine is selected first regardless of `fp_version`.

---

## 2. Reset Functions

### `reset() -> None`
Clears node facts, edge facts, the loaded graph, the duplicate-fact-name tracker, and the registered closed-world predicates so the next call to `reason()` starts fresh. Calls `reset_rules()` and resets the underlying `Program` object's facts and graph if it exists. Use this between independent runs in a single Python process to keep memory bounded.

### `reset_rules() -> None`
Clears all loaded rules, the duplicate-rule-name tracker, annotation functions, and head functions. Also resets the rules in the underlying `Program` if one exists.

### `reset_settings() -> None`
Restores every entry on `pr.settings` to its default value.

### `get_rules()`
Returns the internal Numba typed list of currently loaded rules. Mostly useful for debugging.

---

## 3. Loading Graphs

### `load_graphml(path: str) -> None`
Parses a GraphML file from disk and loads it as the reasoning graph.

**Parameters**
- `path` (`str`, required): filesystem path to a `.graphml` file.

**Behavior**
- Honors `settings.reverse_digraph` (reverses edges if set).
- If `settings.graph_attribute_parsing` is `True`, node/edge attributes become facts (subject to `settings.static_graph_facts`).
- Replaces any previously loaded graph.

### `load_graph(graph: networkx.DiGraph) -> None`
Loads an in-memory NetworkX `DiGraph` as the reasoning graph. Same attribute-parsing behavior as `load_graphml`.

**Parameters**
- `graph` (`nx.DiGraph`, required): the graph to use.

---

## 4. Loading Rules

Rules are constructed with the `pr.Rule(...)` class and added to the program via the functions below.

### `add_rule(pr_rule: Rule) -> None`
Adds a single `pr.Rule` to the program. Auto-generates a name if the rule has none, and emits a warning (via `warnings.warn`) if the resolved name has already been used — duplicate names produce ambiguous rule traces.

**Parameters**
- `pr_rule` (`pyreason.Rule`, required): a rule object. If the rule has no name, one is auto-generated as `rule_<index>`.

#### `pr.Rule(rule_text, name=None, infer_edges=False, set_static=False, custom_thresholds=None, weights=None)`
Constructor for the rule object passed to `add_rule`.

**Parameters**
- `rule_text` (`str`, required): the rule in text format, e.g. `'pred1(x,y) : [0.2, 1] <- pred2(a, b) : [1,1], pred3(b, c)'`. The head and body are separated by `<-`, and clauses in the body are comma-separated. Bound annotations like `: [0.2, 1]` are optional.
- `name` (`str`, optional, default `None`): a unique name for the rule. Appears in the rule trace and makes traces easier to read. If omitted, `add_rule` will auto-generate one as `rule_<index>`.
- `infer_edges` (`bool`, optional, default `False`): if `True`, when the body of an edge rule is satisfied between two nodes that are not yet connected, the reasoner creates a new edge between them. Useful for link-prediction style rules.
- `set_static` (`bool`, optional, default `False`): if `True`, when the rule fires, the head atom's bounds are frozen — they will no longer change for the rest of the run.
- `custom_thresholds` (optional, default `None`): per-clause thresholds overriding the default `ANY` quantifier. Either a list of `pr.Threshold` objects with one entry per clause, or a dict mapping clause-index to `pr.Threshold` (unspecified clauses fall back to the default).
- `weights` (optional, default `None`): a list of numeric weights, one per clause, passed to the rule's annotation function. If omitted, all weights default to `1`.

### `add_rules_from_file(file_path: str, infer_edges: bool = False, raise_errors: bool = False) -> None`
Reads a text file of rules (one rule per line, `#` for comments, blank lines ignored) and adds each as a `pr.Rule`. Per-line parsing failures are either raised or warned-and-skipped depending on `raise_errors`. When `settings.verbose` is on, a summary of loaded/failed counts is printed at the end.

**Parameters**
- `file_path` (`str`, required): path to the rules file.
- `infer_edges` (`bool`, optional, default `False`): if `True`, the reasoner will create an edge between the head's variables when the body is satisfied but no such edge exists. Useful for link-prediction style rules. Applied uniformly to every rule in the file.
- `raise_errors` (`bool`, optional, default `False`): if `True`, raise `ValueError` on the first invalid rule line. If `False` (the default), invalid rules are skipped with a warning and the rest of the file is loaded.

**Raises**
- `FileNotFoundError`: if `file_path` does not exist.
- `ValueError`: if `raise_errors=True` and a rule line fails to parse.

### `add_rule_from_csv(csv_path: str, raise_errors: bool = True) -> None`
Bulk-loads rules from a CSV file. Each row has up to four columns: `rule_text, name, infer_edges, set_static`. A header row matching exactly `rule_text,name,infer_edges,set_static` is optional and auto-detected; any other first row is treated as data. Each successfully parsed row is forwarded to `add_rule`. Duplicate `name` values within the same CSV are rejected. Boolean columns accept `True/False`, `1/0`, `yes/no`, etc. (case-insensitive).

**Parameters**
- `csv_path` (`str`, required): path to the CSV file.
- `raise_errors` (`bool`, optional, default `True`): if `True`, the first malformed row aborts the load with an exception. If `False`, malformed rows are skipped with a warning.

**Columns**
- `rule_text` (required): the rule in text format, e.g. `friend(A, B) <- knows(A, B)`. Quote rule text containing commas.
- `name` (optional): unique rule name. Empty allowed.
- `infer_edges` (optional, default `False`): see `add_rules_from_file`.
- `set_static` (optional, default `False`): mark the head atom as static when the rule fires.

**Raises**
- `FileNotFoundError`: if `csv_path` does not exist.
- `ValueError`: on parsing failures when `raise_errors=True`, including duplicate names.

### `add_rule_from_json(json_path: str, raise_errors: bool = True) -> None`
Bulk-loads rules from a JSON file containing an array of rule objects. Supports the same fields as `add_rule_from_csv`, plus two JSON-only advanced fields: `custom_thresholds` and `weights`. Each successfully parsed item is forwarded to `add_rule`. Duplicate `name` values within the same file are rejected.

**Parameters**
- `json_path` (`str`, required): path to the JSON file. Must contain a top-level array.
- `raise_errors` (`bool`, optional, default `True`): if `True`, the first malformed item aborts the load with an exception. If `False`, malformed items are skipped with a warning.

**Per-item fields**
- `rule_text` (required, `str`): the rule in text format.
- `name` (optional, `str`): unique rule name.
- `infer_edges` (optional, `bool`, default `False`).
- `set_static` (optional, `bool`, default `False`).
- `custom_thresholds` (optional): either a list of threshold objects (one per clause) or a dict mapping clause-index strings to threshold objects. Each threshold object must have `quantifier`, `quantifier_type` (a 2-tuple), and `thresh` fields. Forwarded to `pr.Threshold`.
- `weights` (optional, list of numbers): per-clause weights handed to the rule's annotation function.

**Raises**
- `FileNotFoundError`: if `json_path` does not exist.
- `ValueError`: on JSON-decode failures, on a non-array root, or on parsing failures when `raise_errors=True`.

---

## 5. Loading Facts

### `add_fact(pyreason_fact: Fact) -> None`
Adds a node fact or edge fact (constructed via `pr.Fact(...)`) to the program. The fact's `type` (`'node'` or `'edge'`) determines which internal list it goes into. If the fact has no name, one is auto-generated as `fact_<index>`. Emits a warning if the resolved name has already been used — duplicate names produce ambiguous node and atom traces.

**Parameters**
- `pyreason_fact` (`pyreason.Fact`, required): the fact object.

> Facts added between consecutive `reason()` calls are consumed by the next call. After `reason()`, the internal node/edge fact lists are cleared so additional facts can be added before `reason(again=True)`. The duplicate-name tracker is *not* cleared by `reason()` — only `reset()` clears it.

#### `pr.Fact(fact_text, name=None, start_time=0, end_time=0, static=False)`
Constructor for the fact object passed to `add_fact`. Whether the resulting fact is a node fact or an edge fact is inferred automatically from the number of components in `fact_text`.

**Parameters**
- `fact_text` (`str`, required): the fact in text format. Format is `Predicate(component)` or `Predicate(component):bound`.
  - **Predicate** must start with a letter or underscore and may contain letters, digits, and underscores (e.g. `Viewed`, `Has_access`, `_Internal`).
  - **Component** is one node identifier for a node fact (`Pred(node1)`) or two comma-separated identifiers for an edge fact (`Pred(node1,node2)`). Components cannot contain parentheses, colons, or nested structures.
  - **Bound** is optional. If omitted, defaults to `True` (`1.0`). Accepts `True`/`False` (case-insensitive), an interval `[lower,upper]` with both values in `[0,1]`, or a leading `~` for negation (e.g. `~Viewed(zach)` or `~Pred(node):[0.2,0.8]`). Negating an explicit bound rounds to 10 decimal places before negation to avoid floating-point drift.
  - Examples: `'Viewed(zach)'`, `'Viewed(zach):False'`, `'Viewed(zach):[0.5,0.8]'`, `'Connected(alice,bob):[0.7,0.9]'`, `'~Viewed(zach)'`.
- `name` (`str`, optional, default `None`): a unique name for the fact. Appears in the rule trace so you can tell when it was applied. If omitted, `add_fact` will auto-generate one as `fact_<index>`.
- `start_time` (`int`, optional, default `0`): the first timestep at which this fact is active.
- `end_time` (`int`, optional, default `0`): the last timestep at which this fact is active.
- `static` (`bool`, optional, default `False`): if `True`, the fact is active for the entire program and `start_time` / `end_time` are ignored.

### `add_fact_from_json(json_path: str, raise_errors: bool = True) -> None`
Bulk-loads facts from a JSON file containing an array of fact objects. Each successfully parsed item is forwarded to `add_fact`. Duplicate `name` values within the same file are rejected.

**Parameters**
- `json_path` (`str`, required): path to the JSON file. Must contain a top-level array.
- `raise_errors` (`bool`, optional, default `True`): if `True`, the first malformed item aborts the load with an exception. If `False`, malformed items are skipped with a warning.

**Per-item fields**
- `fact_text` (required, `str`): the fact in text format, e.g. `"pred(x,y) : [0.2, 1]"` or `"pred(x) : True"`.
- `name` (optional, `str`): unique fact name.
- `start_time` (optional, `int`, default `0`): first timestep at which the fact is active.
- `end_time` (optional, `int`, default `0`): last timestep at which the fact is active.
- `static` (optional, `bool`, default `False`): mark the fact as static for the entire program.

**Raises**
- `FileNotFoundError`: if `json_path` does not exist.
- `ValueError`: on JSON-decode failures, on a non-array root, or on parsing failures when `raise_errors=True`.

### `add_fact_from_csv(csv_path: str, raise_errors: bool = True) -> None`
Bulk-loads facts from a CSV file. Each row has up to five columns: `fact_text, name, start_time, end_time, static`. A header row matching exactly `fact_text,name,start_time,end_time,static` is optional and auto-detected; any other first row is treated as data. Each successfully parsed row is forwarded to `add_fact`. Duplicate `name` values within the same CSV are rejected. The `static` column accepts `True/False`, `1/0`, `yes/no`, etc. (case-insensitive).

**Parameters**
- `csv_path` (`str`, required): path to the CSV file.
- `raise_errors` (`bool`, optional, default `True`): if `True`, the first malformed row aborts the load with an exception. If `False`, malformed rows are skipped with a warning.

**Columns**
- `fact_text` (required): the fact in text format. Quote fact text containing commas (e.g. `"HaveAccess(Zach,TextMessage)"`) or interval bounds (e.g. `"Processed(Node1):[0.5,0.8]"`).
- `name` (optional): unique fact name.
- `start_time` (optional, default `0`).
- `end_time` (optional, default `0`).
- `static` (optional, default `False`).

**Raises**
- `FileNotFoundError`: if `csv_path` does not exist.
- `ValueError`: on parsing failures when `raise_errors=True`, including duplicate names.

---

## 6. Loading Inconsistent Predicates (IPL)

The IPL is a set of predicate pairs that must never both hold. PyReason uses it to detect and resolve contradictions.

### `load_inconsistent_predicate_list(path: str) -> None`
Loads an IPL from a YAML file.

**Parameters**
- `path` (`str`, required): filesystem path to a YAML IPL file.

### `add_inconsistent_predicate(pred1: str, pred2: str) -> None`
Adds a single inconsistent pair programmatically. Can be called multiple times to build up the IPL.

**Parameters**
- `pred1` (`str`, required): first predicate name.
- `pred2` (`str`, required): second predicate name.

---

## 7. Closed-World Predicates (Circumscription)

### `add_closed_world_predicate(predicate_name: str) -> None`
Registers a predicate as **closed-world** (a form of circumscription). For any node or edge where a closed-world predicate has bounds `[0,1]` (unknown), the reasoner treats it as `[0,0]` (false) during rule satisfaction checks. This lets you assume "absence of evidence is evidence of absence" for specific predicates without having to assert negative facts.

The set of registered predicates is stored module-level and converted into a Numba-compatible list at the start of each `reason()` call, then attached to the `Program` as `closed_world_predicates`. Cleared by `reset()`.

**Parameters**
- `predicate_name` (`str`, required): the predicate to treat as closed-world.

---

## 8. Custom Functions

PyReason supports user-defined functions that can be referenced from inside rules. Both must be JIT-compiled with `@numba.njit` so they can be called from the reasoner's compiled kernels.

### `add_annotation_function(function: Callable) -> None`
Registers an **annotation function** — a function that combines body annotations and weights into a head annotation.

**Parameters**
- `function` (`Callable`, required): a `@numba.njit` function with signature `(annotations, weights) -> annotation`.

### `add_head_function(function: Callable) -> None`
Registers a **head function** — a function called on the head's annotations.

**Parameters**
- `function` (`Callable`, required): a `@numba.njit` function with signature `(annotations) -> annotation`.

---

## 9. Running the Reasoner

### `reason(timesteps=-1, convergence_threshold=-1, convergence_bound_threshold=-1, queries=None, again=False, restart=True)`
The main entry point. Builds (or reuses) the underlying `Program` and runs inference, returning the final `Interpretation` object.

**Parameters**
- `timesteps` (`int`, optional, default `-1`): maximum number of timesteps. `-1` means run until convergence. When `again=True`, this is the *additional* timesteps to run beyond the previous run.
- `convergence_threshold` (`int`, optional, default `-1`): maximum number of interpretation changes between timesteps for the run to be considered converged. `-1` means require zero changes (perfect convergence).
- `convergence_bound_threshold` (`float`, optional, default `-1`): maximum bound delta for any interpretation between timesteps to be considered converged. `-1` disables bound-based convergence.
- `queries` (`List[pr.Query]`, optional, default `None`): a list of `pr.Query` objects used to filter the ruleset down to only the rules that can affect the queried atoms. When supplied, irrelevant rules are pruned before reasoning for a substantial speedup.
- `again` (`bool`, optional, default `False`): if `True` and a previous run exists, continue from the existing interpretation rather than rebuilding the program. Newly added facts are appended.
- `restart` (`bool`, optional, default `True`): when `again=True`, controls whether the time counter resets to 0. If `False`, time continues from where the previous run ended.

**Returns**
- `Interpretation`: the final interpretation. Pass this to `get_rule_trace`, `save_rule_trace`, `filter_and_sort_nodes`, or `filter_and_sort_edges` for inspection.

**Side effects**
- Sets an internal timestamp used for any output files.
- If `settings.output_to_file` is `True`, redirects stdout to the configured log file.
- If `settings.memory_profile` is `True`, prints peak memory delta after the run.
- If `settings.graph_attribute_parsing` is on but no graph was loaded, uses an empty `nx.DiGraph` and emits a warning when `verbose` is `True`.
- Requires that at least one rule has been loaded; otherwise raises an exception.
- After a successful run, internal node/edge fact lists are cleared so additional facts can be added before calling `reason(again=True)`.

---

## 10. Inspecting Results

All four inspection functions require `settings.store_interpretation_changes` to have been `True` during the run; otherwise they assert.

### `save_rule_trace(interpretation, folder: str = './') -> None`
Writes the full rule trace (every interpretation change) to CSV files in `folder`. With `settings.atom_trace = True`, the trace also lists the atoms that triggered each change, providing complete explainability.

**Parameters**
- `interpretation` (required): the value returned by `reason()`.
- `folder` (`str`, optional, default `'./'`): directory to write the trace files into.

### `get_rule_trace(interpretation) -> Tuple[pandas.DataFrame, pandas.DataFrame]`
Returns the rule trace in memory as two `pandas.DataFrame`s: `(nodes_df, edges_df)`. Same content as `save_rule_trace`, but accessible programmatically.

**Parameters**
- `interpretation` (required): the value returned by `reason()`.

**Returns**
- `(nodes_df, edges_df)`: pandas DataFrames of the per-change rule trace for nodes and edges.

### `filter_and_sort_nodes(interpretation, labels, bound=interval.closed(0,1), sort_by='lower', descending=True)`
Returns one DataFrame per timestep of the node-level interpretation, filtered to the requested labels and bound, then sorted.

**Parameters**
- `interpretation` (required): the value returned by `reason()`.
- `labels` (`List[str]`, required): label names to keep in the output.
- `bound` (`interval.Interval`, optional, default `interval.closed(0, 1)`): only rows whose bounds fall within this interval are kept. The default keeps everything.
- `sort_by` (`str`, optional, default `'lower'`): `'lower'` or `'upper'` — which end of the bound to sort on.
- `descending` (`bool`, optional, default `True`): sort order.

**Returns**
- A list of pandas DataFrames, one per timestep.

### `filter_and_sort_edges(interpretation, labels, bound=interval.closed(0,1), sort_by='lower', descending=True)`
Identical to `filter_and_sort_nodes` but operates on edge-level interpretations.

---

## 11. Module-Level Re-Exports

For convenience, the module also re-exports several construction classes used to build inputs:

| Symbol | Purpose |
| --- | --- |
| `pr.Rule` | Construct a rule from text. |
| `pr.Fact` | Construct a node or edge fact. |
| `pr.Threshold` | Construct a threshold for a rule clause. |
| `pr.Query` | Construct a query for ruleset filtering. |
| `pr.LogicIntegratedClassifier` | (Optional, requires `torch`) wrap a PyTorch model as a logic-integrated classifier. |
| `pr.ModelInterfaceOptions` | (Optional, requires `torch`) options object for the classifier wrapper. |

If `torch` is not installed, `LogicIntegratedClassifier` and `ModelInterfaceOptions` are `None` and a notice is printed at import time.

---

## Typical Workflow

```python
import pyreason as pr

# 1. Configure
pr.settings.verbose = True
pr.settings.atom_trace = True

# 2. Load inputs
pr.load_graphml('graph.graphml')
pr.add_rules_from_file('rules.txt')
pr.add_fact(pr.Fact('pred(node_a)', name='seed', start_time=0, end_time=0))

# 3. Reason
interpretation = pr.reason(timesteps=10)

# 4. Inspect
nodes_df, edges_df = pr.get_rule_trace(interpretation)
pr.save_rule_trace(interpretation, folder='./out')
```
