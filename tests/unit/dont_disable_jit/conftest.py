import sys
import types

# Provide lightweight stubs for pyreason.pyreason to avoid expensive init.
sys.modules.setdefault('pyreason.pyreason', types.ModuleType('pyreason.pyreason'))
stub = sys.modules['pyreason.pyreason']

stub.settings = types.SimpleNamespace()

def _noop(*args, **kwargs):
    return None

stub.load_graphml = _noop
stub.add_rule = _noop
stub.add_fact = _noop
stub.reason = _noop
stub.reset = _noop
stub.reset_rules = _noop


class Rule:
    def __init__(self, *args, **kwargs):
        pass


class Fact:
    def __init__(self, *args, **kwargs):
        pass


stub.Rule = Rule
stub.Fact = Fact
