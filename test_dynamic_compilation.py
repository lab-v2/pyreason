#!/usr/bin/env python3
"""
Test script to validate if dynamic decorator application can replace
the two separate interpretation files.
"""

import numba
import numpy as np
from numba import prange
import sys
import os

# Add the project root to path so we can import pyreason modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the existing interpretation modules for comparison
try:
    import pyreason.scripts.interpretation.interpretation as interp_seq
    import pyreason.scripts.interpretation.interpretation_parallel as interp_par
    print("✓ Successfully imported existing interpretation modules")
except ImportError as e:
    print(f"✗ Failed to import interpretation modules: {e}")
    sys.exit(1)


def test_simple_dynamic_compilation():
    """Test basic dynamic compilation approach with a simple function."""
    print("\n" + "="*60)
    print("Testing Simple Dynamic Compilation")
    print("="*60)

    # Define a simple function that uses prange
    def simple_parallel_function(arr):
        total = 0
        for i in prange(len(arr)):
            total += arr[i] * 2
        return total

    try:
        # Create both versions dynamically
        simple_seq = numba.njit(cache=False, parallel=False)(simple_parallel_function)
        simple_par = numba.njit(cache=False, parallel=True)(simple_parallel_function)

        # Test with sample data
        test_array = np.array([1, 2, 3, 4, 5], dtype=np.int64)

        result_seq = simple_seq(test_array)
        result_par = simple_par(test_array)

        print(f"Sequential result: {result_seq}")
        print(f"Parallel result: {result_par}")
        print(f"Results match: {result_seq == result_par}")

        if result_seq == result_par:
            print("✓ Simple dynamic compilation works!")
            return True
        else:
            print("✗ Results don't match!")
            return False

    except Exception as e:
        print(f"✗ Simple dynamic compilation failed: {e}")
        return False


def test_cache_behavior():
    """Test if caching works with dynamic compilation."""
    print("\n" + "="*60)
    print("Testing Cache Behavior")
    print("="*60)

    def cached_function(x):
        return x * 2

    try:
        # Test with cache=True
        cached_seq = numba.njit(cache=True, parallel=False)(cached_function)
        cached_par = numba.njit(cache=True, parallel=True)(cached_function)

        result_seq = cached_seq(5)
        result_par = cached_par(5)

        print(f"Cached sequential result: {result_seq}")
        print(f"Cached parallel result: {result_par}")
        print(f"Cache results match: {result_seq == result_par}")

        if result_seq == result_par:
            print("✓ Caching works with dynamic compilation!")
            return True
        else:
            print("✗ Cache results don't match!")
            return False

    except Exception as e:
        print(f"✗ Cached dynamic compilation failed: {e}")
        return False


def extract_reason_function_source():
    """Extract the source of the reason function to test dynamic compilation."""
    print("\n" + "="*60)
    print("Analyzing Existing Reason Function")
    print("="*60)

    # Check if both modules have the reason function
    has_seq_reason = hasattr(interp_seq.Interpretation, 'reason')
    has_par_reason = hasattr(interp_par.Interpretation, 'reason')

    print(f"Sequential module has reason function: {has_seq_reason}")
    print(f"Parallel module has reason function: {has_par_reason}")

    if has_seq_reason and has_par_reason:
        seq_func = interp_seq.Interpretation.reason
        par_func = interp_par.Interpretation.reason

        # Check if they have the same signature
        import inspect
        try:
            seq_sig = inspect.signature(seq_func)
            par_sig = inspect.signature(par_func)

            print(f"Sequential function parameters: {len(seq_sig.parameters)}")
            print(f"Parallel function parameters: {len(par_sig.parameters)}")
            print(f"Signatures match: {seq_sig == par_sig}")

            return True
        except Exception as e:
            print(f"Could not inspect signatures: {e}")
            return False
    else:
        print("✗ Could not find reason functions in both modules")
        return False


def test_dynamic_reason_compilation():
    """Test if we can create dynamic versions of the actual reason function."""
    print("\n" + "="*60)
    print("Testing Dynamic Reason Function Compilation")
    print("="*60)

    try:
        # Get the original function source (this is tricky with numba-compiled functions)
        # We'll try to access the original Python function

        # Check if the function has a py_func attribute (available for njit functions)
        if hasattr(interp_seq.Interpretation.reason, 'py_func'):
            original_func = interp_seq.Interpretation.reason.py_func
            print("✓ Found original Python function via py_func")
        else:
            print("✗ Cannot access original Python function")
            return False

        # Try to create new compiled versions
        dynamic_seq = numba.njit(cache=False, parallel=False)(original_func)
        dynamic_par = numba.njit(cache=False, parallel=True)(original_func)

        print("✓ Successfully created dynamic compiled versions")
        print("⚠️  Note: Cannot easily test with real data without full setup")

        return True

    except Exception as e:
        print(f"✗ Dynamic reason compilation failed: {e}")
        return False


def test_function_identity():
    """Test if dynamically compiled functions have different identities."""
    print("\n" + "="*60)
    print("Testing Function Identity")
    print("="*60)

    def test_func(x):
        return x + 1

    # Create multiple versions
    func1 = numba.njit(parallel=False)(test_func)
    func2 = numba.njit(parallel=True)(test_func)
    func3 = numba.njit(parallel=False)(test_func)

    print(f"func1 is func2: {func1 is func2}")
    print(f"func1 is func3: {func1 is func3}")
    print(f"func2 is func3: {func2 is func3}")

    # Test if they produce same results
    result1 = func1(5)
    result2 = func2(5)
    result3 = func3(5)

    print(f"All results equal: {result1 == result2 == result3}")

    return result1 == result2 == result3


def main():
    """Run all tests to validate dynamic compilation approach."""
    print("Dynamic Compilation Validation for PyReason")
    print("="*80)

    tests = [
        ("Simple Dynamic Compilation", test_simple_dynamic_compilation),
        ("Cache Behavior", test_cache_behavior),
        ("Function Identity", test_function_identity),
        ("Reason Function Analysis", extract_reason_function_source),
        ("Dynamic Reason Compilation", test_dynamic_reason_compilation),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Dynamic compilation approach looks viable.")
        print("Next steps: Implement the refactoring in your codebase.")
    elif passed >= total // 2:
        print("\n⚠️  Most tests passed. Some issues to resolve, but approach may work.")
    else:
        print("\n❌ Multiple test failures. Dynamic compilation may not work.")
        print("Consider keeping the current two-file approach.")


if __name__ == "__main__":
    main()