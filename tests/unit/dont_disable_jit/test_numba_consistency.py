import pyreason.scripts.interpretation.interpretation as interpretation
import pyreason.scripts.numba_wrapper.numba_types.label_type as label


def test_satisfies_threshold_expected_result():
    """Ensure the helper matches the original PyReason result."""
    threshold = ("greater_equal", ("number", "total"), 4)

    # Changed from JIT comparison to the verified original PyReason result.
    result = interpretation._satisfies_threshold(
        10,
        5,
        threshold,
    )

    assert result is True


def test_get_rule_node_clause_grounding_expected_result():
    """Ensure node grounding matches original PyReason."""
    nodes = ["n1", "n2", "n3"]
    groundings = {}
    predicateMap = {}

    nodeLabel = label.Label("L")
    predicateMap[nodeLabel] = ["n1", "n2"]

    # Changed from JIT comparison to the verified original PyReason result.
    result = interpretation.get_rule_node_clause_grounding(
        "X",
        groundings,
        predicateMap,
        nodeLabel,
        nodes,
    )

    assert list(result) == ["n1", "n2"]


def test_get_rule_edge_clause_grounding_expected_result():
    """Ensure edge grounding matches original PyReason."""
    nodes = ["n1", "n2"]

    edges = [
        ("n1", "n2"),
        ("n2", "n1"),
    ]

    neighbors = {
        "n1": ["n2"],
        "n2": ["n1"],
    }

    reverseNeighbors = {
        "n1": ["n2"],
        "n2": ["n1"],
    }

    groundings = {}
    groundingEdges = {}
    predicateMap = {}
    edgeLabel = label.Label("L")

    # Changed from JIT comparison to the verified original PyReason result.
    result = interpretation.get_rule_edge_clause_grounding(
        "X",
        "Y",
        groundings,
        groundingEdges,
        neighbors,
        reverseNeighbors,
        predicateMap,
        edgeLabel,
        edges,
    )

    assert list(result) == [("n1", "n2"), ("n2", "n1")]
