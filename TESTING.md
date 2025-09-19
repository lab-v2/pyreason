# PyReason Test Suite Documentation

This document describes the enhanced test suite structure for PyReason, which provides unified testing across multiple configurations while maintaining clear separation of concerns.

## Overview

The test suite is organized into three distinct directories, each serving a specific purpose:

- **`tests/unit/api_tests/`** - Tests for the main pyreason.py API functions
- **`tests/unit/disable_jit/`** - Tests for internal interpretation logic with JIT compilation disabled
- **`tests/unit/dont_disable_jit/`** - Tests for components that benefit from JIT compilation

## Quick Start

### Using Make (Recommended)

```bash
# Run all test suites with coverage
make test

# Run only fast test suites
make test-fast

# Run specific test suite
make test-api

# Run tests in parallel where possible
make test-parallel

# Generate HTML coverage report
make coverage-html

# Clean up generated files
make clean
```

### Using the Test Runner Directly

```bash
# Run all test suites
python run_tests.py

# Run specific suite
python run_tests.py --suite api_tests

# Run multiple suites
python run_tests.py --suite api_tests --suite dont_disable_jit

# Run fast suites only
python run_tests.py --fast

# Run without coverage collection
python run_tests.py --no-coverage

# Run in parallel
python run_tests.py --parallel
```

### Traditional Pytest (Per Suite)

```bash
# API tests (JIT enabled, real pyreason)
pytest tests/unit/api_tests/ -v

# JIT disabled tests (stubbed environment)
NUMBA_DISABLE_JIT=1 pytest tests/unit/disable_jit/ -v

# JIT enabled tests (stubbed pyreason)
pytest tests/unit/dont_disable_jit/ -v
```

## Test Suite Details

### API Tests (`tests/unit/api_tests/`)

**Purpose:** Test the public API of pyreason.py
- **JIT:** Enabled
- **Environment:** Real pyreason module
- **Coverage:** `pyreason` package
- **Use Case:** Integration testing of main API functions

**Example Tests:**
- `test_pyreason_reasoning.py` - Tests for the reasoning engine
- `test_pyreason_file_loading.py` - Tests for file loading operations
- `test_pyreason_settings.py` - Tests for settings management

### JIT Disabled Tests (`tests/unit/disable_jit/`)

**Purpose:** Test internal interpretation logic with JIT disabled for easier debugging
- **JIT:** Disabled (`NUMBA_DISABLE_JIT=1`)
- **Environment:** Stubbed pyreason module with sophisticated test fixtures
- **Coverage:** `pyreason.scripts` package
- **Use Case:** Unit testing of complex interpretation algorithms

**Key Features:**
- Parametrized tests for both `interpretation_fp.py` and `interpretation.py`
- Sophisticated `reason_env` fixture for testing reasoning logic
- Mocked numba types for faster test execution

**Example Tests:**
- `test_annotation_functions.py` - Tests for annotation function logic
- `test_reason_core.py` - Core reasoning algorithm tests
- `test_interpretation_init.py` - Interpretation initialization tests

### JIT Enabled Tests (`tests/unit/dont_disable_jit/`)

**Purpose:** Test components that benefit from JIT compilation
- **JIT:** Enabled
- **Environment:** Lightweight stubbed pyreason module
- **Coverage:** `pyreason.scripts` package
- **Use Case:** Testing numba-compiled components and consistency checks

**Example Tests:**
- `test_world.py` - Tests for world/graph structures
- `test_numba_consistency.py` - Consistency between JIT and non-JIT versions

## Configuration

### `test_config.json`

The test runner uses a JSON configuration file that defines:

- Test suite paths and descriptions
- Coverage settings and source packages
- Environment variables for each suite
- Execution policies (parallel/sequential)
- Output and reporting options

### `pytest.ini`

Global pytest configuration providing:
- Test discovery patterns
- Markers for categorizing tests
- Warning filters
- Logging configuration
- Default options

## Coverage Reporting

The test runner automatically combines coverage from all suites and generates:

- **Terminal Report:** Summary displayed after test execution
- **HTML Report:** Interactive coverage browser at `test_reports/htmlcov/index.html`
- **XML Report:** Machine-readable coverage data at `test_reports/coverage.xml`

### Viewing Coverage

```bash
# Generate and open HTML report
make coverage-html

# Show terminal coverage summary
make coverage-report

# Get path to XML report (for CI/CD)
make coverage-xml
```

## Development Workflow

### Adding New Tests

1. **For API tests:** Add to `tests/unit/api_tests/`
   - Use real pyreason imports
   - Test high-level functionality
   - Focus on user-facing behavior

2. **For algorithm tests:** Add to `tests/unit/disable_jit/`
   - Use parametrized helpers for testing both interpretation modules
   - Leverage the `reason_env` fixture for complex scenarios
   - Test internal logic and edge cases

3. **For performance tests:** Add to `tests/unit/dont_disable_jit/`
   - Use numba-compiled code
   - Test consistency between JIT and non-JIT versions
   - Focus on numerical accuracy and performance

### Running Tests During Development

```bash
# Quick feedback loop - fast tests only
make test-fast

# Full validation before commit
make test

# Debug specific suite
make test-api  # or test-jit, test-no-jit

# Check test configuration
make debug-config
make debug-suites
```

### Continuous Integration

```bash
# CI-optimized test run
make ci-test

# Fast CI validation
make ci-fast
```

## Troubleshooting

### Common Issues

1. **pytest not found**
   ```bash
   make install-deps
   # or
   pip install pytest coverage pytest-cov pytest-timeout
   ```

2. **pyreason import errors**
   - Ensure pyreason is installed: `pip install -e .`
   - Check PYTHONPATH is set correctly

3. **Coverage combination fails**
   - Install coverage: `pip install coverage`
   - Clean old coverage files: `make clean-coverage`

4. **Tests timeout**
   - Individual test timeout: 60s (configurable in pytest.ini)
   - Suite timeout: 300s-600s (configurable in test_config.json)

### Debug Commands

```bash
# Check dependencies
make check-deps

# Show project info
make info

# List available test suites
make debug-suites

# Show full configuration
make debug-config

# Clean everything and start fresh
make clean
```

## Architecture Benefits

This structure provides:

1. **Clear Separation:** Each directory has a distinct purpose and configuration
2. **Unified Execution:** Single command to run all tests with combined coverage
3. **Flexible Execution:** Run individual suites, fast tests, or parallel execution
4. **Comprehensive Coverage:** Automatic aggregation across all test types
5. **Developer Friendly:** Convenient make targets and clear error messages
6. **CI/CD Ready:** XML reports and configurable execution modes

## Migration from Old Structure

If you have existing test commands, here are the equivalents:

```bash
# Old: pytest tests/unit/api_tests/ -v
# New: make test-api

# Old: NUMBA_DISABLE_JIT=1 pytest tests/unit/disable_jit/ -v
# New: make test-jit

# Old: pytest tests/unit/dont_disable_jit/ -v
# New: make test-no-jit

# Old: Multiple commands for coverage combination
# New: make test (automatic coverage combination)
```

The new system is fully backward compatible - you can still run pytest directly on individual directories if needed.