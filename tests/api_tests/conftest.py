"""
Conftest for API tests - allows importing real pyreason module for API testing.
We don't disable JIT since we're testing the high-level API, not the internal numba functions.
"""

# No special setup needed - let pyreason import normally with JIT enabled
# This allows us to test the actual API behavior
