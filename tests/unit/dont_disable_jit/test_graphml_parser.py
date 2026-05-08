import pytest
from pyreason.scripts.utils.graphml_parser import GraphmlParser
import networkx as nx
import warnings

def _parse(graph):
    p = GraphmlParser()
    p.load_graph(graph)
    return p.parse_graph_attributes(static_facts=False)

class TestValidGraphmlParsing:
    def test_node_attribute_with_valid_interval_string(self):
        g = nx.DiGraph()
        g.add_node("A", confidence="0.3,0.8")
        facts_node, facts_edge, node_labels, edge_labels = _parse(g)
        # one node fact, no edge facts
        assert len(facts_node) == 1
        assert len(facts_edge) == 0

        fact = facts_node[0]
        assert fact.get_component() == "A"
        assert str(fact.get_label()) == "confidence"      # NOT "confidence-0.3,0.8"
        assert fact.get_bound().lower == 0.3              # NOT 1
        assert fact.get_bound().upper == 0.8              # NOT 1

    def test_node_attribute_with_valid_single_string_interval(self):
        g = nx.DiGraph()
        g.add_node("B", strong="0.5")
        facts_node, facts_edge, node_labels, edge_labels = _parse(g)
        assert len(facts_node) == 1
        fact = facts_node[0]
        assert fact.get_bound().lower == 0.5
        assert fact.get_bound().upper == 1
        assert str(fact.get_label()) == "strong"
        assert fact.get_component() == "B"

    def test_node_with_direct_numeric_attribute(self):
        g = nx.DiGraph()
        g.add_node("B", popular=0.8)
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        fact = facts_node[0]
        assert fact.get_component() == "B"
        assert str(fact.get_label()) == "popular"
        assert fact.get_bound().lower == 0.8
        assert fact.get_bound().upper == 1.0

    def test_edge_attribute_with_valid_interval_string(self):
        g = nx.DiGraph()
        g.add_edge("A", "B", trust="0.2,0.9")
        facts_node, facts_edge, node_labels, edge_labels = _parse(g)
        assert len(facts_edge) == 1
        fact = facts_edge[0]
        assert fact.get_component() == ("A", "B")
        assert str(fact.get_label()) == "trust"
        assert fact.get_bound().lower == 0.2
        assert fact.get_bound().upper == 0.9

    def test_edge_with_direct_numeric_attribute(self):
        g = nx.DiGraph()
        g.add_edge("Z", "F", knows=0.7)
        facts_node, facts_edge, _, _ = _parse(g)
        assert len(facts_node) == 0
        assert len(facts_edge) == 1
        fact = facts_edge[0]
        assert fact.get_component() == ("Z", "F")
        assert str(fact.get_label()) == "knows"
        assert fact.get_bound().lower == 0.7
        assert fact.get_bound().upper == 1.0


    def test_non_numeric_value_produces_categorical_label(self):
        g = nx.DiGraph()
        g.add_node("Ben", pet="cat")
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        fact = facts_node[0]
        assert str(fact.get_label()) == "pet-cat"
        assert fact.get_bound().lower == 1.0
        assert fact.get_bound().upper == 1.0


    def test_boundary_value_zero(self):
        g = nx.DiGraph()
        g.add_node("A", popular=0)
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        fact = facts_node[0]
        assert fact.get_bound().lower == 0.0
        assert fact.get_bound().upper == 1.0


    def test_boundary_value_one(self):
        g = nx.DiGraph()
        g.add_node("B", popular=1)
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        fact = facts_node[0]
        assert fact.get_bound().lower == 1.0
        assert fact.get_bound().upper == 1.0


    def test_boundary_float_zero_and_one(self):
        g = nx.DiGraph()
        g.add_node("C", a=0.0, b=1.0)
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 2
        bounds = {str(f.get_label()): (f.get_bound().lower, f.get_bound().upper) for f in facts_node}
        assert bounds["a"] == (0.0, 1.0)
        assert bounds["b"] == (1.0, 1.0)

    def test_multiple_valid_attributes_on_one_node(self):
        g = nx.DiGraph()
        g.add_node("Alice", popular=0.5, happy=0.7, pet="dog")
        facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 3
        labels = sorted(str(f.get_label()) for f in facts_node)
        assert labels == ["happy", "pet-dog", "popular"]    # sorted


class TestInvalidGraphmlParsing:
    def test_invalid_attribute_key_is_skipped(self):
        g = nx.DiGraph()
        g.add_node("A", **{"bad key": 0.5, "good_key": 0.7})
        with pytest.warns(UserWarning, match="bad key"):
            facts_node, _, _, _ = _parse(g)
        # only good_key produced a fact
        assert len(facts_node) == 1

    def test_invalid_empty_key_values(self):
        g = nx.DiGraph()
        g.add_node("B", **{"": 0.5, "good_key": 0.7})
        with pytest.warns(UserWarning, match="empty"):
            facts_node, _, _, _ = _parse(g)
        # only good_key produced a fact
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "good_key"
        assert facts_node[0].get_bound().lower == 0.7
        assert facts_node[0].get_bound().upper == 1.0

    def test_invalid_string_bound_values(self):
        g = nx.DiGraph()
        g.add_node("C", bad_attr="1.5", good_attr=0.7)
        with pytest.warns(UserWarning, match="out of range"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "good_attr"
        assert facts_node[0].get_bound().lower == 0.7

    def test_invalid_node_id_skips_all_attributes(self):
        g = nx.DiGraph()
        g.add_node("bad node", popular=0.5, happy=0.3)      # 2 attrs on bad node (need to be skipped)
        g.add_node("Bob", happy=0.7)                        # 1 attr on good node 
        with pytest.warns(UserWarning, match="Skipping all attributes"):
            facts_node, _, _, _ = _parse(g)
        # all of bad_node's attrs skipped; only Bob's fact produced
        assert len(facts_node) == 1
        assert facts_node[0].get_component() == "Bob"

    def test_bad_node_id(self):
        g = nx.DiGraph()
        g.add_node("bad node", a=0.1, b=0.2, c=0.3, d=0.4)
        with pytest.warns() as recorded:
            facts_node, _, _, _ = _parse(g)
        node_warnings = [w for w in recorded if "Skipping all attributes" in str(w.message)]
        assert len(node_warnings) == 1
        assert len(facts_node) == 0

    def test_bad_edge_id(self):
        g = nx.DiGraph()
        g.add_edge("bad node", "Bob", knows=1.0, trusts=0.5)
        g.add_edge("X", "Y", friends=0.8)
        with pytest.warns(UserWarning, match="Skipping all attributes on Edge"):
            facts_node, facts_edge, _, _ = _parse(g)
        assert len(facts_edge) == 1
        assert facts_edge[0].get_component() == ("X", "Y")

    def test_invalid_interval_string_format(self):
        g = nx.DiGraph()
        g.add_node("A", confidence="0.9,0.1", happy=0.5)
        with pytest.warns(UserWarning, match="lower <= upper"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "happy"

    def test_invalid_nonnumeric_interval_string_values(self):
        g = nx.DiGraph()
        g.add_node("A", confidence="abc,def", happy=0.5)
        with pytest.warns(UserWarning, match="not parseable"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "happy"

    def test_interval_out_of_range(self):
        g = nx.DiGraph()
        g.add_node("E", confidence="1.5,2.0", happy=0.5)
        with pytest.warns(UserWarning, match="must be in"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "happy"

    def test_numeric_out_of_range(self):
        g = nx.DiGraph()
        g.add_node("V", popular=1.5, happy=0.5)
        with pytest.warns(UserWarning, match="not a valid bound"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "happy"

    def test_invalid_label_composition(self):
        g = nx.DiGraph()
        g.add_node("B", pet="two words", happy=0.5)
        with pytest.warns(UserWarning, match="combined label"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "happy"

    def test_whitespace(self):
        g = nx.DiGraph()
        g.add_node("C", attr="   ", good_attr=0.7)
        with pytest.warns(UserWarning, match="non-empty"):
            facts_node, _, _, _ = _parse(g)
        assert len(facts_node) == 1
        assert str(facts_node[0].get_label()) == "good_attr"


class TestEdgeCasesConditions:
    '''
    - Node with no attributes : produces no facts, no warnings, no errors. 
    - Empty graph — same. 
    - The same label key appearing on multiple nodes: specific_node_labels[label] should accumulate all of them. 
    - Mixed case keys are preserved. ETC
    '''
    def test_node_with_no_attributes_produces_no_facts(self):
        g = nx.DiGraph()
        g.add_node("Brandon")   # no attributes
        facts_node, facts_edge, node_labels, edge_labels = _parse(g)
        assert len(facts_node) == 0
        assert len(facts_edge) == 0
        assert len(node_labels) == 0
        assert len(edge_labels) == 0

    def test_empty_graph_produces_no_facts(self):
        g = nx.DiGraph()
        facts_node, facts_edge, node_labels, edge_labels = _parse(g)
        assert len(facts_node) == 0
        assert len(facts_edge) == 0
        assert len(node_labels) == 0
        assert len(edge_labels) == 0

    def test_label_key_appearing_on_multiple_nodes(self):
        g = nx.DiGraph()
        g.add_node("A", popular=0.6)
        g.add_node("B", popular=0.7)
        facts_node, _, node_labels, _ = _parse(g)
        assert len(facts_node) == 2
        assert len(node_labels) == 1
        label_strs = [str(k) for k in node_labels]
        assert "popular" in label_strs
        for i in node_labels:
            if str(i) == "popular":
                assert sorted(list(node_labels[i])) == ["A", "B"]

    def test_mixed_case_keys_are_preserved(self):
        g = nx.DiGraph()
        g.add_node("N", Popular=0.6, popular=0.7)
        facts_node, _, node_labels, _ = _parse(g)
        assert len(facts_node) == 2
        assert len(node_labels) == 2
        label_strs = [str(k) for k in node_labels]
        assert "Popular" in label_strs
        assert "popular" in label_strs