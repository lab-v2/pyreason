# Advanced feature tests for PyReason (annotation functions, custom thresholds, classifier integration)
import pyreason as pr
from pyreason import Threshold
try:
    import torch
    import torch.nn as nn
    torch_available = True
except ImportError:
    torch_available = False
import networkx as nx
import numba
import numpy as np
import pytest
from pyreason.scripts.numba_wrapper.numba_types.interval_type import closed


def setup_mode(mode):
    """Configure PyReason settings for the specified mode."""
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = True

    if mode == "fp":
        pr.settings.fp_version = True
    elif mode == "parallel":
        pr.settings.parallel_computing = True


@numba.njit
def probability_func(annotations, weights):
    prob_A = annotations[0][0].lower
    prob_B = annotations[1][0].lower
    union_prob = prob_A + prob_B
    union_prob = np.round(union_prob, 3)
    return union_prob, 1


@numba.njit
def identity_func(annotations):
    """Head function that returns the input node lists as-is."""
    result = numba.typed.List([annotations[0][0]])
    return result


@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_probability_func_consistency(mode):
    """Ensure annotation function behaves the same with and without JIT."""
    setup_mode(mode)
    annotations = numba.typed.List()
    annotations.append(numba.typed.List([closed(0.01, 1.0)]))
    annotations.append(numba.typed.List([closed(0.2, 1.0)]))
    weights = numba.typed.List([1.0, 1.0])
    jit_res = probability_func(annotations, weights)
    py_res = probability_func.py_func(annotations, weights)
    assert jit_res == py_res


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_head_functions(mode):
    """Test head function usage in rules for node and edge rules."""
    setup_mode(mode)

    pr.add_head_function(identity_func)

    graph = nx.DiGraph()
    graph.add_node("A", property=1)
    graph.add_node("B", property=1)
    graph.add_edge("A", "B", connected=1)
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('Processed(identity_func(X)) <- property(X), property(Y), connected(X, Y)', 'node_rule_with_func'))
    pr.add_rule(pr.Rule('Route(identity_func(A), B) <- property(X), property(Y), connected(X, Y)', 'edge_rule_func_first'))
    pr.add_rule(pr.Rule('Path(A, identity_func(B)) <- property(X), property(Y), connected(X, Y)', 'edge_rule_func_second'))
    pr.add_rule(pr.Rule('Link(identity_func(A), identity_func(B)) <- property(X), property(Y), connected(X, Y)', 'edge_rule_func_both'))

    interpretation = pr.reason(timesteps=1)

    assert interpretation.query(pr.Query('Processed(A)'), return_bool=True)
    assert interpretation.query(pr.Query('Route(A, B)'), return_bool=True)
    assert interpretation.query(pr.Query('Path(A, B)'), return_bool=True)
    assert interpretation.query(pr.Query('Link(A, B)'), return_bool=True)


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_annotation_function(mode):
    """Test annotation function usage in reasoning."""
    setup_mode(mode)

    pr.settings.allow_ground_rules = True

    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
    pr.add_annotation_function(probability_func)
    pr.add_rule(pr.Rule('union_probability(A, B):probability_func <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

    interpretation = pr.reason(timesteps=1)

    dataframes = pr.filter_and_sort_edges(interpretation, ['union_probability'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert interpretation.query(pr.Query('union_probability(A, B) : [0.21, 1]')), 'Union probability should be 0.21'


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_custom_thresholds(mode):
    """Test custom threshold functionality."""
    setup_mode(mode)

    # Modify the paths based on where you've stored the files we made above
    graph_path = "./tests/functional/group_chat_graph.graphml"

    # Modify pyreason settings to make verbose
    pr.settings.atom_trace = True

    # Load all the files into pyreason
    pr.load_graphml(graph_path)

    # add custom thresholds
    user_defined_thresholds = [
        Threshold("greater_equal", ("number", "total"), 1),
        Threshold("greater_equal", ("percent", "total"), 100),
    ]

    pr.add_rule(
        pr.Rule(
            "ViewedByAll(y) <- HaveAccess(x,y), Viewed(x)",
            "viewed_by_all_rule",
            custom_thresholds=user_defined_thresholds,
        )
    )

    pr.add_fact(pr.Fact("Viewed(Zach)", "seen-fact-zach", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Justin)", "seen-fact-justin", 0, 3))
    pr.add_fact(pr.Fact("Viewed(Michelle)", "seen-fact-michelle", 1, 3))
    pr.add_fact(pr.Fact("Viewed(Amy)", "seen-fact-amy", 2, 3))

    # Run the program for three timesteps to see the diffusion take place
    interpretation = pr.reason(timesteps=3)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ["ViewedByAll"])
    for t, df in enumerate(dataframes):
        print(f"TIMESTEP - {t}")
        print(df)
        print()

    assert (
        len(dataframes[0]) == 0
    ), "At t=0 the TextMessage should not have been ViewedByAll"
    assert (
        len(dataframes[2]) == 1
    ), "At t=2 the TextMessage should have been ViewedByAll"

    # TextMessage should be ViewedByAll in t=2
    assert "TextMessage" in dataframes[2]["component"].values and dataframes[2].iloc[
        0
    ].ViewedByAll == [
        1,
        1,
    ], "TextMessage should have ViewedByAll bounds [1,1] for t=2 timesteps"


@pytest.mark.skipif(not torch_available, reason="torch not installed")
@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_classifier_integration(mode):
    """Test classifier integration with PyReason."""
    setup_mode(mode)

    # Create a dummy PyTorch model: input size 10, output 3 classes.
    model = nn.Linear(10, 3)

    # Define class names for the output classes.
    class_names = ["cat", "dog", "rabbit"]

    # Create integration options.
    # Only probabilities exceeding 0.6 will be considered.
    # For those, if set_lower_bound is True, lower bound becomes 0.95; if set_upper_bound is False, upper bound is forced to 1.
    interface_options = pr.ModelInterfaceOptions(
        threshold=0.4,
        set_lower_bound=True,
        set_upper_bound=False,
        snap_value=0.95
    )

    # Create an instance of LogicIntegratedClassifier.
    logic_classifier = pr.LogicIntegratedClassifier(model, class_names, identifier="classifier",
                                                    interface_options=interface_options)

    # Create a dummy input tensor with 10 features.
    input_tensor = torch.rand(1, 10)

    # Set time bounds for the facts.
    t1 = 0
    t2 = 0

    # Run the forward pass to get the model output and the corresponding PyReason facts.
    output, probabilities, facts = logic_classifier(input_tensor, t1, t2)

    # Assert that the output is a tensor.
    assert isinstance(output, torch.Tensor), "The model output should be a torch.Tensor"
    # Assert that we have one fact per class.
    assert len(facts) == len(class_names), "Expected one fact per class"

    # Print results for visual inspection.
    print('Logits', output)
    print('Probabilities', probabilities)
    print("\nGenerated PyReason Facts:")
    for fact in facts:
        print(fact)


@pytest.mark.skipif(True, reason="Reason again functionality not implemented for FP version")
@pytest.mark.parametrize("mode", ["regular"])
def test_reason_again(mode):
    """Test reasoning continuation functionality."""
    setup_mode(mode)

    # Modify the paths based on where you've stored the files we made above
    graph_path = './tests/functional/friends_graph.graphml'

    # Load all the files into pyreason
    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)', 'popular_rule'))
    pr.add_fact(pr.Fact('popular(Mary)', 'popular_fact', 0, 1))

    # Run the program for two timesteps to see the diffusion take place
    faulthandler.enable()
    interpretation = pr.reason(timesteps=1)

    # Now reason again
    new_fact = pr.Fact('popular(Mary)', 'popular_fact2', 2, 4)
    pr.add_fact(new_fact)
    interpretation = pr.reason(timesteps=3, again=True, restart=False)

    # Display the changes in the interpretation for each timestep
    dataframes = pr.filter_and_sort_nodes(interpretation, ['popular'])
    for t, df in enumerate(dataframes):
        print(f'TIMESTEP - {t}')
        print(df)
        print()

    assert len(dataframes[2]) == 1, 'At t=0 there should be one popular person'
    assert len(dataframes[3]) == 2, 'At t=1 there should be two popular people'
    assert len(dataframes[4]) == 3, 'At t=2 there should be three popular people'

    # Mary should be popular in all three timesteps
    assert 'Mary' in dataframes[2]['component'].values and dataframes[2].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=0 timesteps'
    assert 'Mary' in dataframes[3]['component'].values and dataframes[3].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=1 timesteps'
    assert 'Mary' in dataframes[4]['component'].values and dataframes[4].iloc[0].popular == [1, 1], 'Mary should have popular bounds [1,1] for t=2 timesteps'

    # Justin should be popular in timesteps 1, 2
    assert 'Justin' in dataframes[3]['component'].values and dataframes[3].iloc[1].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=1 timesteps'
    assert 'Justin' in dataframes[4]['component'].values and dataframes[4].iloc[2].popular == [1, 1], 'Justin should have popular bounds [1,1] for t=2 timesteps'

    # John should be popular in timestep 3
    assert 'John' in dataframes[4]['component'].values and dataframes[4].iloc[1].popular == [1, 1], 'John should have popular bounds [1,1] for t=2 timesteps'


@pytest.mark.parametrize("mode", ["regular", "fp", "parallel"])
def test_reason_with_queries(mode):
    """Test reasoning with query-based rule filtering"""
    setup_mode(mode)
    # Set up test scenario
    graph = nx.DiGraph()
    graph.add_edges_from([("A", "B"), ("B", "C")])
    pr.load_graph(graph)

    pr.add_rule(pr.Rule('popular(x) <-1 friend(x, y)', 'rule1'))
    pr.add_rule(pr.Rule('friend(x, y) <-1 knows(x, y)', 'rule2'))
    pr.add_fact(pr.Fact('knows(A, B)', 'fact1'))

    # Create query to filter rules
    query = pr.Query('popular(A)')
    pr.settings.verbose = False  # Reduce output noise

    interpretation = pr.reason(timesteps=1, queries=[query])
    # Should complete and apply rule filtering logic
