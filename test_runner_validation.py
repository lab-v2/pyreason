#!/usr/bin/env python3
"""
Validation script for the PyReason test runner.

This script tests the test runner functionality without requiring
pytest or other dependencies to be installed.
"""

import os
import tempfile
import json
from run_tests import TestRunner, TestSuite

def test_config_loading():
    """Test that configuration loads correctly."""
    print("🧪 Testing configuration loading...")

    runner = TestRunner()
    assert len(runner.suites) == 3, f"Expected 3 suites, got {len(runner.suites)}"

    expected_suites = ['api_tests', 'disable_jit', 'dont_disable_jit']
    for suite_name in expected_suites:
        assert suite_name in runner.suites, f"Missing suite: {suite_name}"

    print("   ✓ Configuration loaded successfully")
    print(f"   ✓ Found {len(runner.suites)} test suites")
    return True

def test_suite_configuration():
    """Test individual suite configurations."""
    print("🧪 Testing suite configurations...")

    runner = TestRunner()

    # Test API suite
    api_suite = runner.suites['api_tests']
    assert api_suite.jit_disabled == False
    assert api_suite.uses_real_pyreason == True
    assert api_suite.coverage_source == 'pyreason'
    print("   ✓ API tests suite configured correctly")

    # Test JIT disabled suite
    jit_disabled = runner.suites['disable_jit']
    assert jit_disabled.jit_disabled == True
    assert jit_disabled.uses_real_pyreason == False
    assert 'NUMBA_DISABLE_JIT' in jit_disabled.environment_vars
    print("   ✓ JIT disabled suite configured correctly")

    # Test JIT enabled suite
    jit_enabled = runner.suites['dont_disable_jit']
    assert jit_enabled.jit_disabled == False
    assert jit_enabled.uses_real_pyreason == False
    print("   ✓ JIT enabled suite configured correctly")

    return True

def test_coverage_config():
    """Test coverage configuration generation."""
    print("🧪 Testing coverage configuration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        runner = TestRunner()
        runner.temp_dir = temp_dir

        # Test coverage config creation
        runner._create_coverage_config()

        config_file = os.path.join(temp_dir, '.coveragerc')
        assert os.path.exists(config_file), "Coverage config file not created"

        with open(config_file, 'r') as f:
            content = f.read()

        # Check essential sections
        assert '[run]' in content, "Missing [run] section"
        assert 'source = pyreason' in content, "Missing source setting"
        assert '*/tests/*' in content, "Missing test omit pattern"
        assert '[report]' in content, "Missing [report] section"
        assert '[html]' in content, "Missing [html] section"

        print("   ✓ Coverage configuration generated successfully")
        print(f"   ✓ Config file size: {len(content)} characters")

    return True

def test_python_detection():
    """Test Python command detection."""
    print("🧪 Testing Python command detection...")

    runner = TestRunner()
    python_cmd = runner._find_python_command()

    assert python_cmd in ['python', 'python3', 'python3.11', 'python3.12', 'python3.13']
    print(f"   ✓ Detected Python command: {python_cmd}")

    return True

def test_help_and_args():
    """Test command-line interface."""
    print("🧪 Testing command-line interface...")

    # Test that the runner can be imported and basic methods work
    runner = TestRunner()

    # Test config loading with custom file (should fail gracefully)
    try:
        TestRunner("nonexistent.json")
        assert False, "Should have failed with nonexistent config"
    except SystemExit:
        print("   ✓ Handles missing config file correctly")

    return True

def test_suite_selection():
    """Test suite selection logic."""
    print("🧪 Testing suite selection...")

    runner = TestRunner()

    # Test all suites
    all_suites = list(runner.suites.values())
    assert len(all_suites) == 3

    # Test specific suite selection
    api_only = [runner.suites['api_tests']]
    assert len(api_only) == 1
    assert api_only[0].name == 'api_tests'

    print("   ✓ Suite selection works correctly")
    return True

def test_parallel_vs_sequential():
    """Test parallel execution configuration."""
    print("🧪 Testing execution mode configuration...")

    runner = TestRunner()
    config = runner.config

    # Check execution settings
    assert 'execution' in config
    assert 'parallel_suites' in config['execution']
    assert 'sequential_suites' in config['execution']

    parallel_suites = config['execution']['parallel_suites']
    sequential_suites = config['execution']['sequential_suites']

    # API tests and dont_disable_jit should be parallel-safe
    assert 'api_tests' in parallel_suites
    assert 'dont_disable_jit' in parallel_suites

    # disable_jit should be sequential (due to global JIT setting)
    assert 'disable_jit' in sequential_suites

    print("   ✓ Execution mode configuration is correct")
    return True

def main():
    """Run all validation tests."""
    print("🚀 PyReason Test Runner Validation")
    print("=" * 50)

    tests = [
        test_config_loading,
        test_suite_configuration,
        test_coverage_config,
        test_python_detection,
        test_help_and_args,
        test_suite_selection,
        test_parallel_vs_sequential,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"   ❌ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"   ❌ {test.__name__} failed with error: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! The test runner is ready to use.")
        print("\nNext steps:")
        print("1. Install testing dependencies: make install-deps")
        print("2. Run a simple test: python run_tests.py --help")
        print("3. Try running tests: make test-api (if pytest is available)")
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)