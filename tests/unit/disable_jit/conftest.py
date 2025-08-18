# # tests/conftest.py
import os; os.environ["NUMBA_DISABLE_JIT"] = "1"
import numba; numba.config.DISABLE_JIT = True
import sys, types; sys.modules.setdefault("pyreason.pyreason", types.ModuleType("pyreason.pyreason"))
