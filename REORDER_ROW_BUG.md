# Bug: `_reorder_row` IndexError on rules with non-appending clauses

## Summary

`pyreason.save_rule_trace(...)` raises `IndexError: index N is out of bounds for axis 0 with size N` from [`pyreason/scripts/utils/output.py:120`](pyreason/scripts/utils/output.py#L120) when a rule contains a clause that does **not** append anything to the per-row qualified-nodes / qualified-edges lists during the ground-rule pass — most notably **comparison clauses** (e.g. `score(x) >= 0.5`).

The bug is latent upstream and is exposed by any rule with at least one comparison clause that fires under `atom_trace=True`.

## Symptom

```
File ".../pyreason/scripts/utils/output.py", line 101, in save_rule_trace
    self._parse_internal_rule_trace(interpretation)
File ".../pyreason/scripts/utils/output.py", line 97, in _parse_internal_rule_trace
    self.rule_trace_edge = self.rule_trace_edge.apply(
        self._reorder_row, axis=1,
        map_dict=self.clause_map,
        columns_to_reorder=columns_to_reorder_edge,
    )
...
File ".../pyreason/scripts/utils/output.py", line 120, in _reorder_row
    new_values[target_pos] = original_values[orig_pos]
IndexError: index 3 is out of bounds for axis 0 with size 3
```

The same crash can occur on either `rule_trace_node` (line 96) or `rule_trace_edge` (line 97).

## Reproducer

A minimal script is included at [`examples/reorder_row_bug_ex.py`](examples/reorder_row_bug_ex.py). It uses a 2-node graph and a single 4-clause rule whose first clause is a comparison clause:

```python
pr.add_rule(pr.Rule(
    'result(x) <- score(x) >= 0.5, p1(x), friend(x, y), p2(x)',
    'reorder_row_bug_rule',
))
...
pr.save_rule_trace(interpretation, out_dir)  # <-- crashes here
```

Running it produces:

```
IndexError: index 2 is out of bounds for axis 0 with size 2
```

(The exact numbers depend on how many non-comparison clauses the rule has — the bug pattern is identical regardless.)

## Root Cause

There are two pieces of state that disagree about how many clauses a rule has:

1. **`__clause_maps[rule]`** is built in [`pyreason.py:1598`](pyreason/pyreason.py#L1598) as
   ```python
   {r.get_rule_name(): {i: i for i in range(len(r.get_clauses()))} for r in __rules}
   ```
   so it always has keys `0..len(clauses)-1` — i.e. one key per declared clause, comparison clauses included.

2. **The `Clause-N` columns in the rule-trace DataFrames** are appended per-row in [`output.py:32-40`](pyreason/scripts/utils/output.py#L32-L40) (and the edge counterpart at [`output.py:71-79`](pyreason/scripts/utils/output.py#L71-L79)):
   ```python
   for j in range(len(qn)):
       max_j = max(j, max_j)
       if len(qe[j]) == 0:
           row.append(list(qn[j]))     # node clause
       elif len(qn[j]) == 0:
           row.append(list(qe[j]))     # edge clause
   ```
   The loop iterates over `len(qn)`, **not** over the rule's full clause list, and only appends when exactly one of `qn[j]` / `qe[j]` is non-empty.

The mismatch shows up because the ground-rule pass in [`interpretation_parallel.py:1053-1055`](pyreason/scripts/interpretation/interpretation_parallel.py#L1053-L1055) — and the equivalent paths in `interpretation.py` and `interpretation_fp.py` — explicitly does **not** append to either list for comparison clauses:

```python
else:
    # Comparison clause (we do not handle for now)
    pass
```

So `qn` and `qe` are sized to `(# non-comparison clauses)`, while `__clause_maps[rule]` is sized to `(# total clauses)`. Any rule with at least one comparison clause produces rows with fewer `Clause-N` columns than the clause map references.

`_reorder_row` ([`output.py:114-123`](pyreason/scripts/utils/output.py#L114-L123)) then walks every key in the clause map and indexes into the row's columns blindly:

```python
@staticmethod
def _reorder_row(row, map_dict, columns_to_reorder):
    if row['Occurred Due To'] in map_dict:
        original_values = row[columns_to_reorder].values
        new_values = [None] * len(columns_to_reorder)
        for orig_pos, target_pos in map_dict[row['Occurred Due To']].items():
            new_values[target_pos] = original_values[orig_pos]  # <-- IndexError
        ...
```

When `orig_pos >= len(columns_to_reorder)`, indexing `original_values[orig_pos]` raises.

### Other shapes that can trigger the same bug

The diagnosis from the original incident also flags rules where a clause produces `qn[j]` and `qe[j]` that are both empty or both non-empty (certain negated-clause shapes, some closed-world `~stepFrom`/`future` pairs). In those cases the inner `if`/`elif` in `output.py` falls through without appending, leaving the same size mismatch.

## Why this is just now showing up

The crash is latent — any rule with a comparison clause and atom-trace enabled hits it. It happens to be surfacing now because of newer rules (e.g. `inputs/rules/bounded_label_rules.csv` and the May-14 beacon-mapping rules in the consuming project) that introduce more clause-shape variety. The local fork commit `2d55540` (gating `clause_labels_out`/`clause_variables_out` on `extended_ann_fn`) does **not** touch this code path and is unrelated.

## Repro Environment

- pyreason 3.x (bug reproduces against both the installed `~/.pyenv/.../site-packages/pyreason/` and this fork's `main`)
- Python 3.10
- Settings: `atom_trace=True`, `store_interpretation_changes=True` (the default for `save_rule_trace`)
- Graph size does not matter; the optimize-rules path (`len(edges) > len(nodes)`) is **not** required — the identity clause-map is constructed unconditionally.

## Proposed Fix

Bound-check the indexing inside `_reorder_row`. This is the smallest fix and keeps the existing semantics for any rule whose row width matches its clause map:

```python
@staticmethod
def _reorder_row(row, map_dict, columns_to_reorder):
    if row['Occurred Due To'] in map_dict:
        original_values = row[columns_to_reorder].values
        n = len(columns_to_reorder)
        new_values = [None] * n
        for orig_pos, target_pos in map_dict[row['Occurred Due To']].items():
            if orig_pos < n and target_pos < n:
                new_values[target_pos] = original_values[orig_pos]
        for i, col in enumerate(columns_to_reorder):
            row[col] = new_values[i]
    return row
```

### Longer-term cleanup (optional)

The mismatch is the real defect — the trace should know exactly which clause index each appended cell corresponds to. Two options worth considering:

1. **Always append a placeholder for comparison / non-appending clauses** in [`output.py:33-40`](pyreason/scripts/utils/output.py#L33-L40) so the row width matches `len(clauses)`. This also requires the ground-rule pass to surface comparison clauses into `qn`/`qe` (e.g. as empty lists) so the trace can distinguish "no clause appended at j" from "clause j had no groundings".
2. **Carry clause indices alongside the appended values** (e.g. `(j, payload)`) so `_reorder_row` looks up by clause index rather than positional offset.

Either of those removes the implicit positional contract that `_reorder_row` currently assumes.

## Files Touched by the Bug

- [pyreason/scripts/utils/output.py](pyreason/scripts/utils/output.py) — `_parse_internal_rule_trace`, `_reorder_row`
- [pyreason/pyreason.py:1598](pyreason/pyreason.py#L1598) — `__clause_maps` construction
- [pyreason/scripts/interpretation/interpretation_parallel.py:1053-1055](pyreason/scripts/interpretation/interpretation_parallel.py#L1053-L1055) (and parallel paths in `interpretation.py`, `interpretation_fp.py`) — comparison-clause skip
