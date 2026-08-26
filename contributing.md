
## Getting Started

Install the project requirements and the pre-commit framework:

```bash
pip install -r requirements.txt
```

## Setting up Pre-Commit Hooks

To ensure code quality and consistency, enable the pre-commit hooks:

```bash
pre-commit install
```

That writes `.git/hooks/pre-commit`. It is per-clone and not tracked, so a
fresh clone has no hooks until you run it. Confirm it took:

```bash
ls .git/hooks/pre-commit
```

If that file is missing, the hooks are silently not running on your commits —
`pre-commit run --all-files` will still work by hand, which makes the gap easy
to miss.

On every commit the hooks run `ruff check pyreason/scripts` and both unit
suites — `tests/unit/disable_jit` and `tests/unit/dont_disable_jit` — as two
separate hook entries, so the JIT settings of one never leak into the other.

The functional suite is **not** wired into any hook; every entry in
`.pre-commit-config.yaml` is `stages: [pre-commit]`. Run
`pytest tests/functional` yourself before opening a PR, or rely on CI, which
does run it.

Trigger all checks manually with `pre-commit run --all-files`.

## Linting

We are working to update the codebase to comply with `ruff` linting rules. Run
this command to view linting results:

```bash
ruff check pyreason/scripts
```

## Running Tests

### Prerequisites

Installing the requirements is required before running tests, not optional:

```bash
pip install -r requirements.txt
```

Two entries in that file are easy to overlook, and both fail in confusing ways:

- **`torch`** — `tests/unit/dont_disable_jit/test_classifiers.py` imports it at
  module scope. Without it, that entire suite aborts during collection with
  `ModuleNotFoundError: No module named 'torch'` and pytest exits 2. No tests
  run, including the ones unrelated to classifiers.
- **`pytest-cov`** — every coverage-enabled command below passes `--cov` to
  pytest. Without the plugin, pytest exits 4 with
  `unrecognized arguments: --cov`, and `run_tests.py` reports this as a *failing
  test suite* rather than a missing dependency.

Check what is present with `make check-deps`.

### Test layout

The test suite is organized into four directories:

- **`tests/api_tests/`** - Tests for main pyreason.py API functions (JIT enabled, real pyreason)
- **`tests/unit/disable_jit/`** - Tests for internal interpretation logic (JIT disabled, stubbed environment)
- **`tests/unit/dont_disable_jit/`** - Tests for components that benefit from JIT (JIT enabled, lightweight stubs)
- **`tests/functional/`** - End-to-end functional tests (JIT enabled, real pyreason, longer running)

### Important: never collect both unit directories in one process

`tests/unit/disable_jit/conftest.py` sets `NUMBA_DISABLE_JIT=1` and
`numba.config.DISABLE_JIT = True` at **import** time. Those settings are
process-global, so any single pytest process that collects both unit
directories leaves JIT disabled for the suite that requires it enabled:

```bash
pytest tests/unit     # DON'T — over a hundred spurious failures
pytest                # DON'T — pytest.ini sets testpaths = tests, so this is the same thing
```

The resulting failures are not real. They land in
`tests/unit/dont_disable_jit/test_rule_parser.py` and `test_world.py` with the
signature:

```
TypeError: Interval.__new__() takes from 3 to 4 positional arguments but 6 were given
```

Every one of those tests passes when its directory is run on its own. If you
see that error, check how you invoked pytest before investigating the code.

Give each suite its own process instead. `run_tests.py` does this for you (one
subprocess per suite), and so do the pre-commit hooks (`disable_jit` and
`dont_disable_jit` are two separate hook entries).

### Running suites directly with pytest

Run one directory at a time.

```bash
# Unit tests, JIT disabled — fastest, good inner-loop check
pytest tests/unit/disable_jit -v

# Unit tests, JIT enabled
pytest tests/unit/dont_disable_jit -v

# API tests
pytest tests/api_tests -v

# Functional, end-to-end tests
pytest tests/functional -v

# A single functional file (~15 s)
pytest tests/functional/test_basic_reasoning.py -v

# A single functional test, all three reasoner variants (~14 s)
pytest tests/functional/test_basic_reasoning.py::test_hello_world -v
```

Note that most functional tests are parameterized over three reasoner
variants (`regular`, `fp`, `parallel`), so naming one test runs three.

#### Why the same command can take 20 seconds or 7 minutes

Numba caches compiled functions on disk under `pyreason/cache/<source-hash>/`.
The hash covers the engine source, so **any edit to the compiled modules (e.g.
`interpretation.py`) invalidates the cache** and the next run re-compiles from
scratch. Timings measured on a developer laptop:

| Suite | Cold cache | Warm cache |
|-------|-----------|-----------|
| `tests/unit/disable_jit` | ~1 s | ~1 s (JIT off, unaffected) |
| `tests/unit/dont_disable_jit` | ~13 s | ~10 s |
| `tests/api_tests` | ~6 min 40 s | ~22 s |
| `tests/functional` | ~11 min 15 s | ~9 min 35 s – 10 min 10 s |

Only the suites that exercise the real engine care about the cache.
`disable_jit` runs with JIT off, and `dont_disable_jit` runs against
lightweight stubs, so both are nearly cold-proof.

`pyreason/cache/` is gitignored, so a fresh clone always starts cold. Note that
`make clean` does **not** clear it — it only removes `__pycache__`,
`.pytest_cache`, and the coverage reports. To force a cold run, delete the
directory yourself:

```bash
rm -rf pyreason/cache
```

If a suite that "used to take 20 seconds" suddenly runs for minutes, the cache
was invalidated — that is expected, not a hang.

Separately, the *first* `import pyreason` in a fresh clone runs a small warmup
reasoning job and prints:

```
Imported PyReason for the first time. Initializing caches for faster runtimes ... this will take a minute
```

That flips `initialized` in the tracked file `pyreason/.cache_status.yaml`, so
after your first non-test run `git status` shows it modified. This is expected;
leave it out of your commits. Test runners are exempt — `pyreason/__init__.py`
skips the write-back when `pytest` or `unittest` is loaded — so running the
suites never dirties it.

#### Almost all of the functional runtime is nine tests

The cost is not spread evenly across the suite. In a measured warm-cache run
(`pytest tests/functional --cov pyreason --durations=20`, 610 s total), nine
tests accounted for 596 s — **98% of the wall clock** — and the remaining 76
tests finished in about 14 seconds combined:

```
117.19s  test_advanced_features.py::test_head_functions[regular]
105.14s  test_advanced_features.py::test_head_functions[parallel]
 69.95s  test_advanced_features.py::test_negated_annotation_function[parallel]
 69.35s  test_advanced_features.py::test_annotation_function[parallel]
 60.64s  test_advanced_features.py::test_head_functions[fp]
 51.82s  test_advanced_features.py::test_annotation_function[regular]
 48.76s  test_advanced_features.py::test_negated_annotation_function[regular]
 39.27s  test_advanced_features.py::test_annotation_function[fp]
 33.67s  test_advanced_features.py::test_negated_annotation_function[fp]
```

These are the annotation- and head-function tests, which compile new Numba
signatures for each of the three reasoner variants. Two consequences worth
knowing:

- pytest collects `test_advanced_features.py` first, so a `-v` run appears to
  stall on its first handful of tests and then race through the rest. That is
  normal.
- Deselecting that one file gives you a fast end-to-end check:

  ```bash
  pytest tests/functional --deselect tests/functional/test_advanced_features.py -v
  ```

  That covers 59 of the 85 functional tests in about 16 s warm, versus roughly
  10 minutes for the whole suite. Run the full suite before you open a PR.

Add `--durations=20` to any suite to see where its own time goes.

### Using the test runner

`run_tests.py` runs each suite in its own subprocess with the right environment
and combines coverage across all of them.

Which suites share a machine is set in `test_config.json` under `execution`:

| Group | Suites |
|-------|--------|
| `parallel_suites` | `api_tests`, `dont_disable_jit` |
| `sequential_suites` | `disable_jit`, `functional` |

`disable_jit` is sequential because it sets `NUMBA_DISABLE_JIT` process-wide
(see the warning above), and `functional` because it is long and CPU-hungry.
Moving either into the parallel group will produce the spurious `Interval`
failures or badly skewed timings.

```bash
# All suites, parallel where safe, then open the HTML coverage report
make test

# All suites, no browser
make test-only

# All suites, one at a time
make test-sequential

# Only the fast suites (api_tests + dont_disable_jit)
make test-fast

# Only the functional suite
make test-functional

# Skip coverage entirely — useful if pytest-cov is unavailable
make test-no-coverage
```

`make test` opens the HTML report with `open`, falls back to `xdg-open`, and
if neither exists just prints the path — so it is safe over SSH or in a
container. Use `make test-only` if you want to skip the attempt entirely.

Single suites have their own targets:

```bash
make test-api     # tests/api_tests
make test-jit     # tests/unit/dont_disable_jit  (JIT enabled)
make test-no-jit  # tests/unit/disable_jit       (JIT disabled)
```

`make help` lists every target.

The same runner can be driven directly, which is the easiest way to pick an
arbitrary combination of suites:

```bash
# One or more named suites: api_tests, disable_jit, dont_disable_jit, functional
python run_tests.py --suite api_tests --suite dont_disable_jit

# Without coverage instrumentation
python run_tests.py --suite disable_jit --no-coverage
```

#### The runner chooses its own interpreter

`run_tests.py` does **not** run the suites under the interpreter you invoked it
with. `_find_python_command()` re-resolves one, in this order:

1. `$VIRTUAL_ENV/bin/python`, if `VIRTUAL_ENV` is set
2. `./.venv/bin/python`, `./venv/bin/python`, `./env/bin/python`
3. the first of `python3.9`, `/usr/bin/python3`, `python3`, `python`,
   `python3.11` that answers `--version`

An active `VIRTUAL_ENV` therefore wins over both `sys.executable` and `PATH`.
If it points at an environment without `pytest-cov`, every coverage-enabled
suite dies instantly with `error: unrecognized arguments: --cov` and pytest
exit code 4 — which the runner reports as a *failing test suite*, not a missing
dependency. Prepending the right environment to `PATH` does not fix this;
`VIRTUAL_ENV` is read first.

The runner prints its choice as the first line of each suite:

```
Running command with Python: /path/to/python
```

Check that line before debugging a suite that failed in under a second.

#### Each suite has a wall-clock timeout

`run_tests.py` kills any suite that overruns the `timeout` set for it in
`test_config.json`. The summary reports the kill as a plain `FAIL` and does not
say it was a timeout, so read the suite's own output before you start looking
for a test that broke.

| Suite | Timeout | Longest measured (cold) |
|-------|---------|-------------------------|
| `api_tests` | 900 s | ~6 min 40 s |
| `disable_jit` | 600 s | ~1 s |
| `dont_disable_jit` | 300 s | ~13 s |
| `functional` | 1800 s | ~11 min 15 s |

Compare against the cold-cache column in the table above when you change one.
A fresh clone is always cold, so a limit that only clears the *warm* number
will kill the suite on a new contributor's first run.

The limits are wall clock, not CPU time, so anything that stops the clock while
a suite runs counts against it. Suspending a laptop mid-run is the common case:
the suite resumes fine, but the elapsed time already exceeds the limit.

### Coverage Reports

The test runner automatically combines coverage from all suites:

- **Terminal Report:** Summary shown after test execution
- **HTML Report:** `test_reports/htmlcov/index.html`
- **XML Report:** `test_reports/coverage.xml`

Coverage is reported but **not enforced**. `test_config.json` contains
`"fail_under": 80` under `coverage`, but `run_tests.py` never reads that key
and never passes it to `coverage`, so a run well under 80% still exits 0 — a
single suite on its own typically reports 22–60%. Do not rely on the test
runner to gate coverage; read the number yourself.

### Troubleshooting

```bash
# Check system status and dependencies
make info
make check-deps

# List every available make target
make help

# Test pytest configuration
python -c "import configparser; c=configparser.ConfigParser(); c.read('pytest.ini'); print('pytest.ini is valid')"

# Clean up generated files
make clean
```
