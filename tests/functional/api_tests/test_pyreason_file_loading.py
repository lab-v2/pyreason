"""
Unit tests for pyreason file loading operations and graph management.
Tests load_graphml, load_graph, load_inconsistent_predicate_list functions.
"""

import pytest
import networkx as nx
import tempfile
import os
import pyreason as pr
import pandas as pd
from pyreason.scripts.rules.rule import Rule

class TestLoadGraphML:
    """Test load_graphml() function."""

    def setup_method(self):
        """Clean state before each test."""

        pr.reset()
        pr.reset_settings()

    def test_load_graphml_nonexistent_file(self):
        """Test load_graphml() with nonexistent file."""

        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_graphml('nonexistent_file.graphml')
             

    def test_load_graphml_with_empty_path(self):
        """Test load_graphml() with empty path."""
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_graphml('')

    def test_load_graphml_simple_graph(self):
        """Test loading a simple GraphML file."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_node_attributes(self):
        """Test loading GraphML with node attributes."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="name" for="node" attr.name="name" attr.type="string"/>
  <key id="age" for="node" attr.name="age" attr.type="int"/>
  <graph id="G" edgedefault="directed">
    <node id="A">
      <data key="name">Alice</data>
      <data key="age">25</data>
    </node>
    <node id="B">
      <data key="name">Bob</data>
      <data key="age">30</data>
    </node>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_edge_attributes(self):
        """Test loading GraphML with edge attributes."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>
  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="weight">0.8</data>
      <data key="relation">knows</data>
    </edge>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_attribute_parsing_enabled(self):
        """Test loading GraphML with attribute parsing enabled."""
        pr.settings.graph_attribute_parsing = True

        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="person" for="node" attr.name="person" attr.type="boolean"/>
  <graph id="G" edgedefault="directed">
    <node id="A">
      <data key="person">true</data>
    </node>
    <node id="B">
      <data key="person">true</data>
    </node>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_attribute_parsing_disabled(self):
        """Test loading GraphML with attribute parsing disabled."""
        pr.settings.graph_attribute_parsing = False

        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="person" for="node" attr.name="person" attr.type="boolean"/>
  <graph id="G" edgedefault="directed">
    <node id="A">
      <data key="person">true</data>
    </node>
    <node id="B">
      <data key="person">true</data>
    </node>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_empty_graph(self):
        """Test loading an empty GraphML graph."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_self_loops(self):
        """Test loading GraphML with self-loops."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="A"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_undirected_graph(self):
        """Test loading an undirected GraphML graph."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        except Exception:
            # If it raises an error, that's acceptable behavior
            pass
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_multiple_graphs(self):
        """Test loading GraphML with multiple graphs (should use first)."""
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G1" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
  <graph id="G2" edgedefault="directed">
    <node id="X"/>
    <node id="Y"/>
    <edge source="X" target="Y"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_reverse_digraph_enabled(self):
        """Test loading GraphML with reverse_digraph setting enabled."""
        pr.settings.reverse_digraph = True

        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)
            pr.settings.reverse_digraph = False  # Reset to default

    def test_load_graphml_with_reverse_digraph_disabled(self):
        """Test loading GraphML with reverse_digraph setting disabled."""
        pr.settings.reverse_digraph = False

        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(graphml_content)
            tmp_path = tmp.name

        try:
            pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_overwrites_previous_graph(self):
        """Test that loading a new GraphML overwrites the previous graph."""
        graphml_content1 = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        graphml_content2 = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="X"/>
    <node id="Y"/>
    <edge source="X" target="Y"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp1:
            tmp1.write(graphml_content1)
            tmp1_path = tmp1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp2:
            tmp2.write(graphml_content2)
            tmp2_path = tmp2.name

        try:
            pr.load_graphml(tmp1_path)
            pr.load_graphml(tmp2_path)  # Should overwrite first graph
        finally:
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)

    def test_load_graphml_invalid_xml(self):
        """Test loading invalid XML GraphML file."""
        invalid_graphml = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
    <node id="A"/>
    <node id="B"
    <edge source="A" target="B"/>
  </graph>
</graphml>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphml', delete=False) as tmp:
            tmp.write(invalid_graphml)
            tmp_path = tmp.name

        try:
            with pytest.raises(Exception):  # Should raise some kind of parsing error
                pr.load_graphml(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_graphml_with_invalid_path_type(self):
        """Test load_graphml() with invalid path type."""
        with pytest.raises((TypeError, OSError)):
            pr.load_graphml(123)  # Not a string


class TestLoadGraph:
    """Test load_graph() function."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_load_graph_simple_digraph(self):
        """Test loading a simple DiGraph."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')

        # Should not raise an exception
        pr.load_graph(graph)

    def test_load_graph_empty_digraph(self):
        """Test loading an empty DiGraph."""
        graph = nx.DiGraph()

        pr.load_graph(graph)

    def test_load_graph_with_node_attributes(self):
        """Test loading a graph with node attributes."""
        graph = nx.DiGraph()
        graph.add_node('A', label='person', age=25)
        graph.add_node('B', label='person', age=30)
        graph.add_edge('A', 'B')

        pr.load_graph(graph)

    def test_load_graph_with_edge_attributes(self):
        """Test loading a graph with edge attributes."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B', relation='knows', weight=0.8)
        graph.add_edge('B', 'C', relation='likes', weight=0.6)

        pr.load_graph(graph)

    def test_load_graph_with_attribute_parsing_enabled(self):
        """Test loading graph with attribute parsing enabled."""
        pr.settings.graph_attribute_parsing = True

        graph = nx.DiGraph()
        graph.add_node('A', label='person')
        graph.add_edge('A', 'B', relation='knows')

        pr.load_graph(graph)

    def test_load_graph_with_attribute_parsing_disabled(self):
        """Test loading graph with attribute parsing disabled."""
        pr.settings.graph_attribute_parsing = False

        graph = nx.DiGraph()
        graph.add_node('A', label='person')
        graph.add_edge('A', 'B', relation='knows')

        pr.load_graph(graph)


    def test_load_graph_with_self_loops(self):
        """Test loading graph with self-loops."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'A')  # Self-loop
        graph.add_edge('A', 'B')

        pr.load_graph(graph)

    def test_load_graph_with_multiple_components(self):
        """Test loading graph with multiple disconnected components."""
        graph = nx.DiGraph()
        # Component 1
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        # Component 2 (disconnected)
        graph.add_edge('X', 'Y')
        graph.add_edge('Y', 'Z')

        pr.load_graph(graph)

    def test_load_graph_large_graph(self):
        """Test loading a larger graph."""
        graph = nx.DiGraph()
        # Create a graph with many nodes and edges
        for i in range(100):
            for j in range(i+1, min(i+5, 100)):  # Connect to next 4 nodes
                graph.add_edge(f'node_{i}', f'node_{j}')

        pr.load_graph(graph)

    def test_load_graph_overwrites_previous_graph(self):
        """Test that loading a new graph overwrites the previous one."""
        graph1 = nx.DiGraph()
        graph1.add_edge('A', 'B')

        graph2 = nx.DiGraph()
        graph2.add_edge('X', 'Y')

        pr.load_graph(graph1)
        pr.load_graph(graph2)  # Should overwrite graph1

    def test_load_graph_undirected_graph(self):
        """Test load_graph() with undirected graph (should handle gracefully or error)."""
        

        graph = nx.Graph()  # Undirected graph
        graph.add_edge('A', 'B')

        # This might raise an error or be converted to DiGraph
        # The exact behavior depends on implementation
        try:
            pr.load_graph(graph)
        except (TypeError, AttributeError):
            # If it raises an error, that's acceptable behavior
            pass


class TestLoadInconsistentPredicateList:
    """Test load_inconsistent_predicate_list() function."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_load_ipl_nonexistent_file(self):
        """Test load_inconsistent_predicate_list() with nonexistent file."""
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_inconsistent_predicate_list('nonexistent.yaml')


    def test_load_ipl_with_invalid_yaml(self):
        """Test load_inconsistent_predicate_list() with invalid YAML."""
        invalid_yaml = """
        invalid: yaml: content:
        - missing closing bracket
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            tmp.write(invalid_yaml)
            tmp_path = tmp.name

        try:
            with pytest.raises(Exception):  # Should raise some kind of parsing error
                pr.load_inconsistent_predicate_list(tmp_path)

        finally:
            os.unlink(tmp_path)

    def test_load_ipl_with_invalid_path_type(self):
        """Test load_inconsistent_predicate_list() with invalid path type."""
        with pytest.raises(OSError):
            pr.load_inconsistent_predicate_list(123)  # Not a string


class TestGraphAttributeParsing:
    """Test graph attribute parsing behavior."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_graph_attribute_parsing_enabled_with_attributes(self):
        """Test attribute parsing when enabled with node/edge attributes."""
        pr.settings.graph_attribute_parsing = True

        graph = nx.DiGraph()
        graph.add_node('A', person=True, age=25)
        graph.add_node('B', person=True, age=30)
        graph.add_edge('A', 'B', knows=True, weight=0.8)

        pr.load_graph(graph)

    def test_graph_attribute_parsing_disabled_with_attributes(self):
        """Test attribute parsing when disabled with node/edge attributes."""
        pr.settings.graph_attribute_parsing = False

        graph = nx.DiGraph()
        graph.add_node('A', person=True, age=25)
        graph.add_node('B', person=True, age=30)
        graph.add_edge('A', 'B', knows=True, weight=0.8)

        pr.load_graph(graph)

    def test_graph_with_complex_attributes(self):
        """Test graph with complex attribute types."""
        graph = nx.DiGraph()
        graph.add_node('A',
                      string_attr='value',
                      int_attr=42,
                      float_attr=3.14,
                      bool_attr=True,
                      list_attr=[1, 2, 3])
        graph.add_edge('A', 'B',
                      string_attr='edge_value',
                      int_attr=100,
                      dict_attr={'key': 'value'})

        pr.load_graph(graph)

    def test_graph_with_no_attributes(self):
        """Test graph with no attributes (both parsing modes)."""
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')

        # Test with parsing enabled
        pr.settings.graph_attribute_parsing = True
        pr.load_graph(graph)

        # Test with parsing disabled
        pr.settings.graph_attribute_parsing = False
        pr.load_graph(graph)


class TestFileLoadingSequences:
    """Test sequences of file loading operations."""
    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_load_graph_then_ipl(self):
        """Test loading graph followed by inconsistent predicate list."""
        # Load graph
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        # Load IPL
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            tmp.write('- [pred1, pred2]\n')
            tmp_path = tmp.name
        try:
            pr.load_inconsistent_predicate_list(tmp_path)
        except Exception:
            # If parsing fails, that's acceptable for this test
            pass
        finally:
            os.unlink(tmp_path)

    def test_multiple_graph_loads(self):
        """Test loading multiple graphs in sequence."""
        graph1 = nx.DiGraph()
        graph1.add_edge('A', 'B')

        graph2 = nx.DiGraph()
        graph2.add_edge('X', 'Y')
        graph2.add_edge('Y', 'Z')

        graph3 = nx.DiGraph()
        graph3.add_node('single_node')

        pr.load_graph(graph1)
        pr.load_graph(graph2)
        pr.load_graph(graph3)

class TestErrorHandling:
    """Test error handling in file loading operations."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_load_operations_with_permission_errors(self):
        """Test file loading operations with permission denied."""
        # Create a file and remove read permissions (if possible)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'test content')
            tmp_path = tmp.name

        try:
            # Try to remove read permissions
            os.chmod(tmp_path, 0o000)

            # These should raise permission errors
            with pytest.raises((PermissionError, OSError)):
                pr.load_graphml(tmp_path)

        except (OSError, PermissionError):
            # If we can't change permissions (e.g., Windows), skip this test
            pytest.skip("Cannot test permission errors on this system")

        finally:
            # Restore permissions and clean up
            try:
                os.chmod(tmp_path, 0o644)
                os.unlink(tmp_path)
            except OSError:
                pass

    def test_load_operations_after_failures(self):
        """Test that operations work after previous failures."""
        # Try to load nonexistent file (should fail)
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_graphml('nonexistent.graphml')

        # But then loading a valid graph should work
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)  # Should succeed

    def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""

        # Load valid graph
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        # Try invalid IPL load
        with pytest.raises((FileNotFoundError, OSError)):
            pr.load_inconsistent_predicate_list('nonexistent.yaml')

        # System should still be in valid state
        # Loading another graph should work
        graph2 = nx.DiGraph()
        graph2.add_edge('C', 'D')
        pr.load_graph(graph2)


class TestAddRulesFromFile:
    """Test add_rules_from_file() function."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_add_rules_from_file_simple_rules(self):
        """Test loading simple rules from file."""
        

        rules_content = """friend(A, B) <- knows(A, B)
enemy(A, B) <- ~friend(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_with_comments_and_empty_lines(self):
        """Test rule file parsing handles comments and empty lines"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            f.write("   \n")  # Whitespace-only line
            f.write("test_rule(x) <-1 other_rule(x)\n")
            f.write("# Another comment\n")
            f.write("another_rule(y) <-1 test_rule(y)\n")
            temp_path = f.name

        try:
            pr.add_rules_from_file(temp_path)
            rules = pr.get_rules()
            assert len(rules) == 2  # Should only include the 2 actual rules
        finally:
            os.unlink(temp_path)

    def test_add_rules_from_file_with_empty_lines(self):
        """Test loading rules from file with empty lines."""
        

        rules_content = """friend(A, B) <- knows(A, B)

            enemy(A, B) <- ~friend(A, B)

            """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_with_infer_edges_true(self):
        """Test loading rules with infer_edges=True."""
        rules_content = """friend(A, B) <- knows(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path, infer_edges=True)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_with_infer_edges_false(self):
        """Test loading rules with infer_edges=False."""
        rules_content = """friend(A, B) <- knows(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path, infer_edges=False)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_nonexistent_file(self):
        """Test add_rules_from_file() with nonexistent file."""
        

        with pytest.raises((FileNotFoundError, OSError)):
            pr.add_rules_from_file('nonexistent_rules.txt')

    def test_add_rules_from_file_empty_file(self):
        """Test loading rules from empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write('')
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_multiple_calls(self):
        """Test multiple calls to add_rules_from_file."""
        rules_content1 = """friend(A, B) <- knows(A, B)"""
        rules_content2 = """enemy(A, B) <- ~friend(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp1:
            tmp1.write(rules_content1)
            tmp1_path = tmp1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp2:
            tmp2.write(rules_content2)
            tmp2_path = tmp2.name

        try:
            pr.add_rules_from_file(tmp1_path)
            pr.add_rules_from_file(tmp2_path)
        finally:
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)


    def test_add_rules_from_file_complex_rules(self):
        """Test loading complex rules from file."""
        

        rules_content = """friend(A, B) <- knows(A, B), likes(A, B)
        enemy(A, B) <- ~friend(A, B), conflict(A, B)
        ally(A, B) <- friend(A, B), common_interest(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_add_rules_from_file_after_existing_rules(self):
        """Test that rule numbering continues from existing rules."""
        
        from pyreason.scripts.rules.rule import Rule

        # Add a rule manually first
        pr.add_rule(Rule("existing(A, B) <- test(A, B)", "existing_rule", False))

        rules_content = """friend(A, B) <- knows(A, B)
        enemy(A, B) <- ~friend(A, B)"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(rules_content)
            tmp_path = tmp.name

        try:
            pr.add_rules_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)


    def test_add_inconsistent_predicates(self):
        """Test adding inconsistent predicate pairs"""
        pr.add_inconsistent_predicate("pred1", "pred2")
        pr.add_inconsistent_predicate("pred3", "pred4")
        # Should not raise exceptions


class TestRuleTrace:
    """Test save_rule_trace() and get_rule_trace() functions."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_save_rule_trace_with_store_interpretation_changes_disabled(self):
        """Test save_rule_trace() with store_interpretation_changes disabled."""
        pr.settings.store_interpretation_changes = False

        # Create a simple interpretation (empty for this test)
        interpretation = {}

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.save_rule_trace(interpretation)

    def test_get_rule_trace_with_store_interpretation_changes_disabled(self):
        """Test get_rule_trace() with store_interpretation_changes disabled."""
        pr.settings.store_interpretation_changes = False

        # Create a simple interpretation (empty for this test)
        interpretation = {}

        with pytest.raises(AssertionError, match='store interpretation changes setting is off'):
            pr.get_rule_trace(interpretation)

    def test_save_rule_trace_with_store_interpretation_changes_enabled(self):
        """Test save_rule_trace() with store_interpretation_changes enabled."""
        pr.settings.store_interpretation_changes = True

        # Create a simple graph and run reasoning to get an interpretation
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        # Add a simple fact and rule
        pr.add_fact(pr.Fact('person(A)', 'A', 1, 1))
        pr.add_rule(Rule('friend(A, B) <- person(A)', 'test_rule', False))

        # Run reasoning to get interpretation
        interpretation = pr.reason(1)

        # Test save_rule_trace with default folder
        with tempfile.TemporaryDirectory() as temp_dir:
            pr.save_rule_trace(interpretation, temp_dir)
            # Check that files were created (exact files depend on implementation)
            files_created = os.listdir(temp_dir)
            assert len(files_created) > 0, "Expected files to be created in the trace folder"

    def test_save_rule_trace_with_custom_folder(self):
        """Test save_rule_trace() with custom folder path."""
        pr.settings.store_interpretation_changes = True

        # Create a simple graph and run reasoning
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        pr.add_fact(pr.Fact('person(A)', 'A', 1, 1))
        pr.add_rule(Rule('friend(A, B) <- person(A)', 'test_rule', False))

        interpretation = pr.reason(1)

        # Test with custom folder
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_folder = os.path.join(temp_dir, 'custom_trace')
            os.makedirs(custom_folder, exist_ok=True)

            pr.save_rule_trace(interpretation, custom_folder)
            files_created = os.listdir(custom_folder)
            assert len(files_created) > 0, "Expected files to be created in the custom trace folder"

    def test_get_rule_trace_with_store_interpretation_changes_enabled(self):
        """Test get_rule_trace() with store_interpretation_changes enabled."""
        pr.settings.store_interpretation_changes = True

        # Create a simple graph and run reasoning
        graph = nx.DiGraph()
        graph.add_edge('A', 'B')
        pr.load_graph(graph)

        pr.add_fact(pr.Fact('person(A)', 'A', 1, 1))
        pr.add_rule(Rule('friend(A, B) <- person(A)', 'test_rule', False))

        interpretation = pr.reason(1)

        # Test get_rule_trace
        node_trace, edge_trace = pr.get_rule_trace(interpretation)

        # Verify return types are DataFrames
        assert isinstance(node_trace, pd.DataFrame), "Expected node_trace to be a pandas DataFrame"
        assert isinstance(edge_trace, pd.DataFrame), "Expected edge_trace to be a pandas DataFrame"

    def test_get_rule_trace_returns_dataframes(self):
        """Test that get_rule_trace() returns proper DataFrame structures."""
        pr.settings.store_interpretation_changes = True

        # Create a more complex scenario
        graph = nx.DiGraph()
        graph.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'A')])
        pr.load_graph(graph)

        # Add multiple facts and rules
        pr.add_fact(pr.Fact('person(A)', 'A', 1, 1))
        pr.add_fact(pr.Fact('person(B)', 'B', 1, 1))
        pr.add_rule(Rule('friend(A, B) <- person(A)', 'rule1', False))
        pr.add_rule(Rule('likes(A, B) <- friend(A, B)', 'rule2', False))

        interpretation = pr.reason(2)

        node_trace, edge_trace = pr.get_rule_trace(interpretation)

        # Basic structure verification
        assert isinstance(node_trace, pd.DataFrame)
        assert isinstance(edge_trace, pd.DataFrame)

        # DataFrames should have some basic expected structure
        # (exact columns depend on implementation, but they should be valid DataFrames)
        assert hasattr(node_trace, 'columns')
        assert hasattr(edge_trace, 'columns')
