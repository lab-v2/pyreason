# PyReason Test Suite Makefile
# Provides convenient shortcuts for running different test configurations

.PHONY: help test test-all test-fast test-api test-jit test-no-jit test-consistency \
        test-parallel test-sequential test-no-coverage coverage-report coverage-html coverage-xml \
        clean clean-coverage clean-reports install-deps lint check-deps

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
RUN_TESTS := $(PYTHON) run_tests.py
PIP := $(PYTHON) -m pip

# Auto-detect python if python3 doesn't work
PYTHON_CHECK := $(shell $(PYTHON) --version 2>/dev/null || echo "failed")
ifeq ($(PYTHON_CHECK),failed)
    PYTHON := python
    RUN_TESTS := $(PYTHON) run_tests.py
    PIP := $(PYTHON) -m pip
endif

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BOLD := \033[1m
RESET := \033[0m

# Help target
help: ## Show this help message
	@echo "$(BOLD)PyReason Test Suite$(RESET)"
	@echo "$(BLUE)Available targets:$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Examples:$(RESET)"
	@echo "  make test                 # Run all test suites in parallel with coverage"
	@echo "  make test-sequential      # Run all test suites sequentially (slower)"
	@echo "  make test-fast            # Run only fast test suites"
	@echo "  make test-api             # Run only API tests"
	@echo "  make coverage-html        # Generate HTML coverage report"

# Main test targets
test: ## Run all test suites with coverage and open report (in parallel)
	@echo "$(BOLD)$(BLUE)Running all test suites in parallel...$(RESET)"
	$(RUN_TESTS) --parallel
	@echo "$(BOLD)$(GREEN)Opening coverage report in browser...$(RESET)"
	@if [ -f test_reports/htmlcov/index.html ]; then \
		open test_reports/htmlcov/index.html 2>/dev/null || \
		xdg-open test_reports/htmlcov/index.html 2>/dev/null || \
		echo "$(GREEN)HTML report available at: test_reports/htmlcov/index.html$(RESET)"; \
	else \
		echo "$(YELLOW)No HTML coverage report found$(RESET)"; \
	fi

test-all: test ## Alias for 'test' target

test-only: ## Run all test suites with coverage (no browser, in parallel)
	@echo "$(BOLD)$(BLUE)Running all test suites in parallel...$(RESET)"
	$(RUN_TESTS) --parallel

test-sequential: ## Run all test suites sequentially (no parallelization)
	@echo "$(BOLD)$(BLUE)Running all test suites sequentially...$(RESET)"
	$(RUN_TESTS)

test-fast: ## Run only fast test suites (api_tests, dont_disable_jit)
	@echo "$(BOLD)$(BLUE)Running fast test suites...$(RESET)"
	$(RUN_TESTS) --fast

test-parallel: ## Run test suites in parallel where possible
	@echo "$(BOLD)$(BLUE)Running test suites in parallel...$(RESET)"
	$(RUN_TESTS) --parallel

test-no-coverage: ## Run all tests without coverage collection
	@echo "$(BOLD)$(BLUE)Running tests without coverage...$(RESET)"
	$(RUN_TESTS) --no-coverage

# Individual test suite targets
test-api: ## Run only API tests (tests/api_tests)
	@echo "$(BOLD)$(BLUE)Running API tests...$(RESET)"
	$(RUN_TESTS) --suite api_tests

test-jit: ## Run only JIT-disabled tests (tests/unit/disable_jit)
	@echo "$(BOLD)$(BLUE)Running JIT-disabled tests...$(RESET)"
	$(RUN_TESTS) --suite don_disable_jit

test-no-jit: ## Run only JIT-enabled tests (tests/unit/dont_disable_jit)
	@echo "$(BOLD)$(BLUE)Running JIT-enabled tests...$(RESET)"
	$(RUN_TESTS) --suite disable_jit

test-consistency: ## Run numba consistency tests
	@echo "$(BOLD)$(BLUE)Running consistency tests...$(RESET)"
	$(PYTHON) -m pytest tests/unit/dont_disable_jit/test_numba_consistency.py -v

test-functional: ## Run functional/end-to-end tests
	@echo "$(BOLD)$(BLUE)Running functional tests...$(RESET)"
	$(RUN_TESTS) --suite functional


test-all-suites: ## Run all test suites including functional tests (in parallel)
	@echo "$(BOLD)$(BLUE)Running all test suites including functional in parallel...$(RESET)"
	$(RUN_TESTS) --parallel

# Coverage targets
coverage-report: ## Show coverage report in terminal
	@echo "$(BOLD)$(BLUE)Generating coverage report...$(RESET)"
	@if [ -f test_reports/coverage.xml ]; then \
		coverage report --rcfile=test_reports/.coveragerc 2>/dev/null || \
		echo "$(YELLOW)Run 'make test' first to generate coverage data$(RESET)"; \
	else \
		echo "$(YELLOW)No coverage data found. Run 'make test' first$(RESET)"; \
	fi

coverage-html: ## Generate HTML coverage report
	@echo "$(BOLD)$(BLUE)Opening HTML coverage report...$(RESET)"
	@if [ -f test_reports/htmlcov/index.html ]; then \
		open test_reports/htmlcov/index.html 2>/dev/null || \
		xdg-open test_reports/htmlcov/index.html 2>/dev/null || \
		echo "$(GREEN)HTML report available at: test_reports/htmlcov/index.html$(RESET)"; \
	else \
		echo "$(YELLOW)No HTML coverage report found. Run 'make test' first$(RESET)"; \
	fi

coverage-xml: ## Show path to XML coverage report
	@echo "$(BOLD)$(BLUE)XML Coverage Report:$(RESET)"
	@if [ -f test_reports/coverage.xml ]; then \
		echo "$(GREEN)XML report available at: test_reports/coverage.xml$(RESET)"; \
	else \
		echo "$(YELLOW)No XML coverage report found. Run 'make test' first$(RESET)"; \
	fi

# Development targets
lint: ## Run linting checks
	@echo "$(BOLD)$(BLUE)Running linting checks...$(RESET)"
	@echo "Fixing end of files..."
	@pre-commit run end-of-file-fixer --all-files || true
	@echo "Running ruff..."
	./.venv/bin/python -m ruff check pyreason/scripts

check-deps: ## Check if required dependencies are installed
	@echo "$(BOLD)$(BLUE)Checking dependencies...$(RESET)"
	@$(PYTHON) -c "import pytest; print('✓ pytest installed')" 2>/dev/null || \
		(echo "$(RED)✗ pytest not installed$(RESET)" && exit 1)
	@$(PYTHON) -c "import coverage; print('✓ coverage installed')" 2>/dev/null || \
		(echo "$(RED)✗ coverage not installed$(RESET)" && exit 1)
	@$(PYTHON) -c "import pyreason; print('✓ pyreason importable')" 2>/dev/null || \
		(echo "$(YELLOW)⚠ pyreason not importable (may need installation)$(RESET)")
	@echo "$(GREEN)Dependencies check complete$(RESET)"

install-deps: ## Install testing dependencies
	@echo "$(BOLD)$(BLUE)Installing testing dependencies...$(RESET)"
	$(PIP) install pytest coverage pytest-cov pytest-timeout
	@echo "$(GREEN)Testing dependencies installed$(RESET)"

# Cleanup targets
clean: clean-coverage clean-reports ## Clean all generated files
	@echo "$(BOLD)$(BLUE)Cleaning all generated files...$(RESET)"
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(RESET)"

clean-coverage: ## Clean coverage files
	@echo "$(BOLD)$(BLUE)Cleaning coverage files...$(RESET)"
	@rm -f .coverage .coverage.* 2>/dev/null || true
	@rm -rf test_reports/htmlcov 2>/dev/null || true
	@rm -f test_reports/coverage.xml 2>/dev/null || true

clean-reports: ## Clean test report files
	@echo "$(BOLD)$(BLUE)Cleaning test reports...$(RESET)"
	@rm -rf test_reports 2>/dev/null || true

# Version and info
info: ## Show project and tool versions
	@echo "$(BOLD)$(BLUE)Project Information:$(RESET)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Pytest: $$($(PYTHON) -c 'import pytest; print(pytest.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "Coverage: $$($(PYTHON) -c 'import coverage; print(coverage.__version__)' 2>/dev/null || echo 'Not installed')"
	@echo "Working Directory: $$(pwd)"
	@echo "Test Runner: $$(ls -la run_tests.py 2>/dev/null || echo 'Not found')"
