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
| `fixtures/pokec-2k.graphml.gz` | Committed fixture, gzipped (75 KB) |
| `fixtures/pokec-10k.graphml.gz` | Committed fixture, gzipped (509 KB) |
| `fixtures/pokec-*-customers.json` | Committed customer id lists |
| `data/` | Local SNAP dumps, needed only to regenerate; gitignored |

## Dataset (do not commit)

The fixtures are committed gzipped, so **neither CI nor a normal checkout needs
the SNAP dumps** — CI just gunzips them. Both archives together are under
600 KB, small enough to live in git directly; Git LFS would be the wrong tool
at this size and would bill clone bandwidth to the repo owner.

You only need the raw dumps to *regenerate* a fixture (spec change, new size).
Download once into `benchmarks/pokec/data/` (~570 MB, gitignored):

- https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz
- https://snap.stanford.edu/data/soc-pokec-profiles.txt.gz

Integrity (gunzip line counts): relationships **30,622,564**; profiles **1,632,803**.

## Fixture generation

```bash
python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --size 2k --write

python benchmarks/pokec/generate_fixtures.py \
  --data-dir benchmarks/pokec/data --size 10k --write

# Re-compress for commit. -n omits the timestamp so the archive is
# byte-reproducible from identical GraphML.
gzip -9 -n -kf benchmarks/pokec/fixtures/pokec-{2k,10k}.graphml
```

The generator asserts the reference counts below, so a run that completes
without an AssertionError has produced a correct fixture. The unpacked
`.graphml` is gitignored; commit only the `.gz`.

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
| `pokec-2k` | every PR / push to main / nightly / manual | 3 repeats; ~7 min; 20 min timeout |
| `pokec-10k` | every PR / push to main / nightly / manual | 3 repeats; ~11 min; 30 min timeout |

**Both sizes gate every PR, by design.** They run as two parallel jobs, so the
gate costs the longer of the two (~11 min) rather than their sum — and the
existing `python-package-version-test.yml` suite takes 29–35 min on the same
PR. Perf therefore adds **zero** PR latency: it is never the critical path.
Runner minutes are free on public repos, so wall clock is the only budget that
matters here, and 2k is effectively free alongside 10k.

Roughly 320 s of each job is size-independent Numba compilation in the warmup
child. That is why 2k is not much cheaper than 10k, and why merging the two
jobs to share one warmup would *raise* wall clock by serializing them.

`workflow_dispatch` takes a `type` input (`2k` / `10k` / `both`) to run a
single size manually; every other trigger runs both. The nightly cron is kept
as a drift check against runner-image and dependency changes that no PR would
surface.

Fixtures are unpacked from the committed `.gz` files, so CI never contacts
`snap.stanford.edu` — no cache step, no cold-miss download, and fork PRs
(which cannot write to the Actions cache) behave identically to branch PRs.

There is deliberately **no `paths:` filter**. A perf number depends on more
than it looks like it does — the engine, the benchmark harness, the fixtures,
the workflow, and the pinned dependencies in `setup.py` — and a filter that
misses one of those turns a real regression into a job that silently never
ran. Since perf is off the critical path and runner minutes are free, a filter
would buy no wall clock and no money in exchange for that gap. A docs-only PR
running the bench is the cheap side of the trade.

The jobs install the package **editable**. `run_bench.py` prepends the repo
root to each child's `PYTHONPATH`, so the checkout is what gets imported and
measured regardless; `-e` makes that explicit instead of leaving an unused
copy in `site-packages`.

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
