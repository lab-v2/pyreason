import networkx as nx
import pyreason as pr
import pytest


@pytest.mark.parametrize("mode", ["regular", "parallel"])
@pytest.mark.parametrize("atom_trace", [False, True])
@pytest.mark.parametrize(
    "delay, immediate_rule",
    [(2, False), (1, True)],
    ids=["two-timestep-delay", "mixed-zero-and-one-timestep-delays"],
)
def test_pending_node_rules_keep_their_schedule(mode, atom_trace, delay, immediate_rule):
    """Pending node rules survive both a timestep and an extra fixed-point pass."""
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = False
    pr.settings.parallel_computing = mode == "parallel"
    pr.settings.atom_trace = atom_trace

    graph = nx.DiGraph()
    graph.add_node("a")
    pr.load_graph(graph)
    pr.add_fact(pr.Fact("seed(a)", "seed_fact", 0, 3))
    pr.add_rule(pr.Rule(f"result(x) <-{delay} seed(x)", "delayed_rule"))
    if immediate_rule:
        pr.add_rule(pr.Rule("immediate(x) <-0 seed(x)", "immediate_rule"))

    interpretation = pr.reason(timesteps=3)
    frames = pr.filter_and_sort_nodes(interpretation, ["result"])
    assert len(frames) == 4
    for timestep, frame in enumerate(frames):
        if timestep < delay:
            assert frame.empty
        else:
            assert frame.to_dict("records") == [{"component": "a", "result": [1, 1]}]

    if immediate_rule:
        immediate_frames = pr.filter_and_sort_nodes(interpretation, ["immediate"])
        assert immediate_frames[0].to_dict("records") == [
            {"component": "a", "immediate": [1, 1]}
        ]

    if atom_trace:
        trace, _ = pr.get_rule_trace(interpretation)
        delayed_trace = trace[trace["Label"] == "result"]
        assert set(delayed_trace["Time"]) == set(range(delay, 4))
        assert set(delayed_trace["Occurred Due To"]) == {"delayed_rule"}
        assert all(nodes == ["a"] for nodes in delayed_trace["Clause-1"])
