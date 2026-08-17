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
| `fixtures/pokec-2k.*` | Committed per-PR fixture (~1.6 MB GraphML) |
| `fixtures/pokec-10k.*` | Generated in nightly CI; **not** committed |
| `data/` | Local SNAP downloads; gitignored |

## Dataset (do not commit)

Download once into `benchmarks/pokec/data/`:

- https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz
- https://snap.stanford.edu/data/soc-pokec-profiles.txt.gz

Integrity (gunzip line counts): relationships **30,622,564**; profiles **1,632,803**.

## Fixture generation

```bash
python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --rungs 2k --write

python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --rungs 10k --write
```

Spec (must match exactly for the verified 10k cross-check):

- Rung = N smallest profile user ids; keep edges with both ends kept.
- `hasPet` from Slovak `pets` text (column 13) via the fixed stem→token map.
- Customers: paper proportion `2308/1632803`, every k-th sorted owner.
- GraphML: users then pet tokens; friend edges in SNAP order; hasPet by owner.

Reference **10k** counts (asserted): 10,000 users, **121,716** friend edges,
**6,204** hasPet edges, **14** customers. **2k** counts are banked in the
generator (`18,315` / `1,203` / `5`).

## Running the bench

```bash
# Per-PR band (3 fresh-process repeats, median)
python benchmarks/pokec/run_bench.py \
  --fixture benchmarks/pokec/fixtures/pokec-2k.graphml \
  --customers benchmarks/pokec/fixtures/pokec-2k-customers.json \
  --repeats 3 --band pokec-2k --out pokec-2k-report.json
```

Timed windows: `import_s`, `setup_s`, `reason_s`. Thresholds apply to
`reason_s` only. After `reason()`, `relevance_rows` at the final timestep must
**exactly** match `baselines.json` (semantics tripwire). First child is an
untimed warmup so Numba compilation stays out of measured windows.
`PYTHONHASHSEED=0` on every child.

Verified **10k** `relevance_rows` on current-main / PR #160 semantics: **8006**.
Banked **2k** `relevance_rows`: **1573**. `reason_s_max` stays `null` until
banked from Actions (see below).

## CI (`.github/workflows/perf.yml`)

| Job | When | Notes |
|-----|------|-------|
| `pokec-2k` | every PR / push to main / manual | committed fixture; 45 min timeout |
| `pokec-10k` | nightly + manual, or PR labeled `pokec-10k` | SNAP download only on cache miss; not on every PR |

Existing `python-package-version-test.yml` / `python-publish.yml` are untouched.

## Re-banking baselines

Re-banking is a **deliberate, reviewed** edit to `baselines.json` — never
automatic.

1. Run the band 3× on Actions (`workflow_dispatch`), collect median `reason_s`
   from each report artifact.
2. Take the **worst** median, multiply by **2.0**, set `reason_s_max`.
3. Set `relevance_rows` to the observed count (must be identical across runs).
4. Open a PR whose description cites the three report artifacts.

`relevance_rows` mismatches are hard failures. `reason_s` over threshold fails
with a message to re-run once before investigating (hosted-runner noise
±20–30% is expected; real historical regressions were ≥×4.4).
