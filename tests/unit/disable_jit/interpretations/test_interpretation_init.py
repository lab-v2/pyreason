import pytest
import networkx as nx
from types import MethodType
from tests.unit.disable_jit.interpretations.test_interpretation_common import get_interpretation_helpers

# Preload defaults so decorators resolve
_default = get_interpretation_helpers("interpretation_fp")
for _name in dir(_default):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_default, _name)


@pytest.fixture(params=["interpretation_fp", "interpretation"], autouse=True)
def helpers_fixture(request):
    h = get_interpretation_helpers(request.param)
    g = globals()
    for name in dir(h):
        if not name.startswith("_"):
            g[name] = getattr(h, name)
    yield


@pytest.fixture
def shim_types(monkeypatch):
    class ListShim:
        def __call__(self, iterable=()):
            return list(iterable)

        def empty_list(self, *args, **kwargs):
            return []

    class DictShim:
        def empty(self, *args, **kwargs):
            return {}

    monkeypatch.setattr(interpretation.numba.typed, "List", ListShim())
    monkeypatch.setattr(interpretation.numba.typed, "Dict", DictShim())

    class World:
        def __init__(self, labels=None):
            self.world = {}

    monkeypatch.setattr(interpretation.world, "World", World)
    monkeypatch.setattr(interpretation.interval, "closed", lambda lo, up: (lo, up))


# ---- _init_reverse_neighbors tests ----

def test_init_reverse_neighbors_branches(shim_types):
    neighbors = {
        "n1": ["n2", "n2"],
        "n2": ["n3"],
        "n3": ["n2"],
        "n4": [],
    }
    rev = init_reverse_neighbors(neighbors)
    assert rev == {"n2": ["n1", "n3"], "n1": [], "n3": ["n2"], "n4": []}


def test_init_reverse_neighbors_empty(shim_types):
    assert init_reverse_neighbors({}) == {}


# ---- Interpretation __init__ neighbor tests ----

def test_interpretation_init_neighbors(shim_types):
    g = nx.Graph()
    g.add_edge("n1", "n2")
    interp = interpretation.Interpretation(
        g,
        {},
        {},
        (),
        False,
        False,
        False,
        False,
        False,
        False,
        "",
        True,
    )
    assert set(interp.neighbors["n1"]) == {"n2"}
    assert set(interp.neighbors["n2"]) == {"n1"}
    assert set(interp.reverse_neighbors["n1"]) == {"n2"}
    assert set(interp.reverse_neighbors["n2"]) == {"n1"}


# ---- _init_interpretations_node tests ----

def test_init_interpretations_node_populates(shim_types):
    nodes = ["a", "b"]
    specific = {"L": ["a"], "M": []}
    interps, pmap = init_interpretations_node(nodes, specific)
    assert pmap["L"] == ["a"] and pmap["M"] == []
    if interpretation.__name__.endswith("interpretation"):
        assert set(interps.keys()) == {"a", "b"}
        assert interps["a"].world["L"] == (0.0, 1.0)
        assert interps["b"].world == {}
    else:
        assert set(interps.keys()) == {0}


def test_init_interpretations_node_empty(shim_types):
    interps, pmap = init_interpretations_node([], {})
    assert pmap == {}
    if interpretation.__name__.endswith("interpretation"):
        assert interps == {}
    else:
        assert interps == {0: {}}


# ---- _init_interpretations_edge tests ----

def test_init_interpretations_edge_populates(shim_types):
    edges = [("a", "b"), ("b", "c")]
    specific = {"L": [("a", "b")], "M": []}
    interps, pmap = init_interpretations_edge(edges, specific)
    assert pmap["L"] == [("a", "b")] and pmap["M"] == []
    if interpretation.__name__.endswith("interpretation"):
        assert set(interps.keys()) == set(edges)
        assert interps[("a", "b")].world["L"] == (0.0, 1.0)
        assert interps[("b", "c")].world == {}
    else:
        assert set(interps.keys()) == {0}


def test_init_interpretations_edge_empty(shim_types):
    interps, pmap = init_interpretations_edge([], {})
    assert pmap == {}
    if interpretation.__name__.endswith("interpretation"):
        assert interps == {}
    else:
        assert interps == {0: {}}


# ---- _init_convergence tests ----

def test_init_convergence_branches():
    assert init_convergence(-1, -1) == ("perfect_convergence", 0)
    assert init_convergence(-1, 0.5) == ("delta_interpretation", 0.5)
    assert init_convergence(0.7, 0.2) == ("delta_bound", 0.7)


# ---- _init_facts tests ----

class Fact:
    def __init__(self, name, component, label, bound, static, lo, hi):
        self._name = name
        self._component = component
        self._label = label
        self._bound = bound
        self.static = static
        self._lo = lo
        self._hi = hi

    def get_time_lower(self):
        return self._lo

    def get_time_upper(self):
        return self._hi

    def get_component(self):
        return self._component

    def get_label(self):
        return self._label

    def get_bound(self):
        return self._bound

    def get_name(self):
        return self._name


def test_init_facts_branches(shim_types):
    n_fact = Fact("graph-attribute-fact", "n1", "L", (0.0, 1.0), True, 0, 0)
    e_fact = Fact("other", ("a", "b"), "M", (0.0, 1.0), False, 0, 1)
    ftn, fte = [], []
    ftn_trace, fte_trace = [], []
    max_t = init_facts([n_fact], [e_fact], ftn, fte, ftn_trace, fte_trace, True)
    assert max_t == 1
    assert ftn == [(0, "n1", "L", (0.0, 1.0), True, True)]
    assert fte == [
        (0, ("a", "b"), "M", (0.0, 1.0), False, False),
        (1, ("a", "b"), "M", (0.0, 1.0), False, False),
    ]
    assert ftn_trace == ["graph-attribute-fact"]
    assert fte_trace == ["other", "other"]


def test_init_facts_no_trace(shim_types):
    fact = Fact("other", "n1", "L", (0.0, 1.0), False, 0, 0)
    ftn, fte = [], []
    ftn_trace, fte_trace = [], []
    max_t = init_facts([fact], [fact], ftn, fte, ftn_trace, fte_trace, False)
    assert max_t == 0
    assert ftn_trace == [] and fte_trace == []


# ---- _start_fp tests ----

def build_interp():
    g = nx.Graph()
    interp = interpretation.Interpretation(
        g,
        {},
        {},
        (),
        False,
        False,
        False,
        False,
        False,
        False,
        "",
        True,
    )
    interp.time = 5
    interp.prev_reasoning_data = [2, 0]
    interp.tmax = 10
    interp._convergence_mode = "perfect_convergence"
    interp._convergence_delta = 0
    interp.num_ga = [1]

    def reason_stub(self, *args):
        self.recorded_prev = list(args[5])
        return (7, 3)

    interp.reason = MethodType(reason_stub, interp)
    return interp


def test_start_fp_no_again(shim_types):
    interp = build_interp()
    interp._start_fp([], 0, False, False, False)
    assert interp.prev_reasoning_data == [3, 7]
    assert interp.num_ga == [1]


def test_start_fp_again_no_restart(shim_types):
    interp = build_interp()
    interp._start_fp([], 0, False, True, False)
    assert interp.recorded_prev[0] == 2
    if interpretation.__name__.endswith("interpretation"):
        assert interp.num_ga == [1, 1]
    else:
        assert interp.num_ga == [1]


def test_start_fp_restart_resets_verbose(shim_types, capsys):
    interp = build_interp()
    interp._start_fp([], 0, True, True, True)
    captured = capsys.readouterr().out.strip()
    assert interp.recorded_prev[0] == 0
    assert captured.endswith("7")
    if interpretation.__name__.endswith("interpretation"):
        assert interp.num_ga == [1, 1]
    else:
        assert interp.num_ga == [1]


def test_start_fp_no_again_verbose(shim_types, capsys):
    interp = build_interp()
    interp._start_fp([], 0, True, False, False)
    captured = capsys.readouterr().out.strip()
    assert interp.prev_reasoning_data == [3, 7]
    assert captured.endswith("7")
    assert interp.num_ga == [1]


def test_start_fp_again_no_restart_verbose(shim_types, capsys):
    interp = build_interp()
    interp._start_fp([], 0, True, True, False)
    captured = capsys.readouterr().out.strip()
    assert interp.recorded_prev[0] == 2
    assert captured.endswith("7")
    if interpretation.__name__.endswith("interpretation"):
        assert interp.num_ga == [1, 1]
    else:
        assert interp.num_ga == [1]


def test_start_fp_restart_no_verbose(shim_types, capsys):
    interp = build_interp()
    interp._start_fp([], 0, False, True, True)
    captured = capsys.readouterr().out.strip()
    assert interp.recorded_prev[0] == 0
    assert captured == ""
    if interpretation.__name__.endswith("interpretation"):
        assert interp.num_ga == [1, 1]
    else:
        assert interp.num_ga == [1]


# ---- start_fp wrapper tests ----

def test_start_fp_invokes_private(shim_types):
    interp = build_interp()
    called = {}

    def stub(self, rules, max_facts_time, verbose, again, restart):
        called["args"] = (rules, max_facts_time, verbose, again, restart)

    interp._start_fp = MethodType(stub, interp)
    fact = Fact("other", "n1", "L", (0.0, 1.0), False, 0, 1)
    interp.start_fp(3, [fact], [], ["r"], True, 0.2, -1, again=True, restart=False)
    assert interp.tmax == 3
    assert interp._convergence_mode == "delta_interpretation"
    assert interp._convergence_delta == 0.2
    assert called["args"] == (["r"], 1, True, True, False)
