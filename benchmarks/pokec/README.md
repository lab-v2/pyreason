# Pokec performance benchmarks

Cliff-tripwire benchmarks shaped like PyReason paper §4.2 (arXiv:2302.13482):
relevance diffusion on a SNAP soc-Pokec subgraph. Hosted GitHub Actions only —
no self-hosted runners.

## Layout

| Path | Role |
|------|------|
| `generate_fixtures.py` | Deterministic fixture builder from SNAP dumps |
| `run_bench.py` | Fresh-process runner; times import / setup / reason |
| `baselines.json` | Banked `relevance_rows` + `reason_s_max` thresholds |
| `fixtures/pokec-2k.*` | Generated in CI on cache miss; **not** committed |
| `fixtures/pokec-10k.*` | Generated in CI on cache miss; **not** committed |
| `data/` | Local SNAP downloads; gitignored |

## Dataset (do not commit)

Download once into `benchmarks/pokec/data/`:

- https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz
- https://snap.stanford.edu/data/soc-pokec-profiles.txt.gz

Integrity (gunzip line counts): relationships **30,622,564**; profiles **1,632,803**.

## Fixture generation

```bash
python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --size 2k --write

python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --size 10k --write
```

Spec (must match exactly for the verified 10k cross-check):

- Size = N smallest profile user ids; keep edges with both ends kept.
- `hasPet` from Slovak `pets` text (column 13) via the fixed stem→token map.
- Customers: paper proportion `2308/1632803`, every k-th sorted owner.
- GraphML: users then pet tokens; friend edges in SNAP order; hasPet by owner.

Reference **10k** counts (asserted): 10,000 users, **121,716** friend edges,
**6,204** hasPet edges, **14** customers. **2k** counts are banked in the
generator (`18,315` / `1,203` / `5`).

## Running the bench

```bash
# Per-PR type (3 fresh-process repeats, median)
python benchmarks/pokec/run_bench.py \
  --fixture benchmarks/pokec/fixtures/pokec-2k.graphml \
  --customers benchmarks/pokec/fixtures/pokec-2k-customers.json \
  --repeats 3 --type pokec-2k --out pokec-2k-report.json
```

Timed windows: `import_s`, `setup_s`, `reason_s`. Thresholds apply to
`reason_s` only. After `reason()`, `relevance_rows` at the final timestep must
**exactly** match `baselines.json` (semantics tripwire). First child is an
untimed warmup so Numba compilation stays out of measured windows.
`PYTHONHASHSEED=0` on every child.

Banked on `ubuntu-latest` (3 Actions medians per type; cap = 2× worst median):

| Type | `relevance_rows` | `reason_s_max` |
|------|------------------|----------------|
| 2k | **1573** | **20.6428** s |
| 10k | **8006** | **154.8286** s |

## CI (`.github/workflows/perf.yml`)

| Job | When | Notes |
|-----|------|-------|
| `pokec-2k` | every PR / push to main / manual | SNAP download only on cache miss; 45 min timeout |
| `pokec-10k` | every PR / push to main / nightly / manual | SNAP download only on cache miss; 300 min timeout |

Existing `python-package-version-test.yml` / `python-publish.yml` are untouched.

## Re-banking baselines

Caps above are already banked in `baselines.json`. Re-banking is a
**deliberate, reviewed** edit — never automatic.

1. Run the type 3× on Actions, collect median `reason_s` from each report.
2. Take the **worst** median, multiply by **2.0**, set `reason_s_max`.
3. `relevance_rows` must stay identical across those runs; change it only if
   the count is stable and the semantics change is intentional.
4. Cite the three report artifacts in the PR that edits `baselines.json`.

`relevance_rows` mismatches are hard failures. `reason_s` over threshold fails
with a message to re-run once before investigating (hosted-runner noise
±20–30% is expected; real historical regressions were ≥×4.4).
