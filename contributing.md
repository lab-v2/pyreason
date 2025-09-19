
## Getting Started

Install the project requirements and the pre-commit framework:

```bash
pip install -r requirements.txt
pip install pre-commit
```

## Setting up Pre-Commit Hooks

To ensure code quality and consistency, enable the pre-commit hooks:

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
```

On every commit, the hooks will run the unit tests located in
`tests/unit/disable_jit` and `tests/unit/dont_disable_jit`. Functional tests in
`tests/functional` execute on every push. You can trigger all checks manually
with `pre-commit run --all-files`.

## Linting

We are working to update the codebase to comply with `ruff` linting rules. Run
this command to view linting results:

```bash
ruff check .
```

## Running Tests

### Enhanced Test Suite

PyReason uses a unified test runner that handles multiple test configurations automatically. The test suite is organized into three directories:

- **`tests/unit/api_tests/`** - Tests for main pyreason.py API functions (JIT enabled, real pyreason)
- **`tests/unit/disable_jit/`** - Tests for internal interpretation logic (JIT disabled, stubbed environment)
- **`tests/unit/dont_disable_jit/`** - Tests for components that benefit from JIT (JIT enabled, lightweight stubs)

### Quick Start

```bash
# Install testing dependencies
make install-deps

# Run all test suites with unified coverage
make test

# Run only fast test suites
make test-fast

# Generate HTML coverage report
make coverage-html
```

### Individual Test Suites

```bash
# API tests (real pyreason, JIT enabled)
make test-api

# JIT disabled tests (stubbed environment)
make test-jit

# JIT enabled tests (lightweight stubs)
make test-no-jit

# Consistency tests
make test-consistency
```

### Advanced Options

```bash
# Run with parallel execution where possible
make test-parallel

# Run without coverage collection (faster)
python run_tests.py --no-coverage

# Run specific suites
python run_tests.py --suite api_tests --suite dont_disable_jit

# Run functional tests
pytest tests/functional
```

### Traditional Pytest (Per Suite)

You can still run pytest directly on individual directories:

```bash
# API tests
pytest tests/unit/api_tests/ -v

# JIT disabled tests
NUMBA_DISABLE_JIT=1 pytest tests/unit/disable_jit/ -v

# JIT enabled tests
pytest tests/unit/dont_disable_jit/ -v
```

### Coverage Reports

The test runner automatically combines coverage from all suites:

- **Terminal Report:** Summary shown after test execution
- **HTML Report:** `test_reports/htmlcov/index.html`
- **XML Report:** `test_reports/coverage.xml`

### Troubleshooting

```bash
# Check system status and dependencies
make info
make check-deps

# Validate test runner setup
python test_runner_validation.py

# Clean up generated files
make clean
```

Running tests locally before committing or pushing helps catch issues early and speeds up code review. The unified test runner ensures consistent behavior across different development environments.
