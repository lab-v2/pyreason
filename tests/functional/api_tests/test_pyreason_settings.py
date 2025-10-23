"""
Comprehensive unit tests for the pyreason._Settings class.
Tests all property getters/setters, type validation, and reset functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import pyreason as pr


def test_settings_import():
    """Test that we can import pyreason settings without expensive initialization."""
    
    assert hasattr(pr, 'settings')
    assert pr.settings is not None


class TestSettingsDefaults:
    """Test default values for all settings properties."""

    def setup_method(self):
        """Reset settings before each test."""
        
        pr.reset_settings()

    def test_verbose_default(self):
        """Test verbose default value."""
        
        assert pr.settings.verbose is True

    def test_output_to_file_default(self):
        """Test output_to_file default value."""
        
        assert pr.settings.output_to_file is False

    def test_output_file_name_default(self):
        """Test output_file_name default value."""
        
        assert pr.settings.output_file_name == 'pyreason_output'

    def test_graph_attribute_parsing_default(self):
        """Test graph_attribute_parsing default value."""
        
        assert pr.settings.graph_attribute_parsing is True

    def test_abort_on_inconsistency_default(self):
        """Test abort_on_inconsistency default value."""
        
        assert pr.settings.abort_on_inconsistency is False

    def test_memory_profile_default(self):
        """Test memory_profile default value."""
        
        assert pr.settings.memory_profile is False

    def test_reverse_digraph_default(self):
        """Test reverse_digraph default value."""
        
        assert pr.settings.reverse_digraph is False

    def test_atom_trace_default(self):
        """Test atom_trace default value."""
        
        assert pr.settings.atom_trace is False

    def test_save_graph_attributes_to_trace_default(self):
        """Test save_graph_attributes_to_trace default value."""
        
        assert pr.settings.save_graph_attributes_to_trace is False

    def test_canonical_default(self):
        """Test canonical default value."""
        
        assert pr.settings.canonical is False

    def test_persistent_default(self):
        """Test persistent default value."""
        
        assert pr.settings.persistent is False

    def test_inconsistency_check_default(self):
        """Test inconsistency_check default value."""
        
        assert pr.settings.inconsistency_check is True

    def test_static_graph_facts_default(self):
        """Test static_graph_facts default value."""
        
        assert pr.settings.static_graph_facts is True

    def test_store_interpretation_changes_default(self):
        """Test store_interpretation_changes default value."""
        
        assert pr.settings.store_interpretation_changes is True

    def test_parallel_computing_default(self):
        """Test parallel_computing default value."""
        
        assert pr.settings.parallel_computing is False

    def test_update_mode_default(self):
        """Test update_mode default value."""
        
        assert pr.settings.update_mode == 'intersection'

    def test_allow_ground_rules_default(self):
        """Test allow_ground_rules default value."""
        
        assert pr.settings.allow_ground_rules is False

    def test_fp_version_default(self):
        """Test fp_version default value."""
        
        assert pr.settings.fp_version is False


class TestSettingsValidSetters:
    """Test setting valid values for all properties."""

    def setup_method(self):
        """Reset settings before each test."""
        
        pr.reset_settings()

    def test_verbose_setter_true(self):
        """Test setting verbose to True."""
        
        pr.settings.verbose = True
        assert pr.settings.verbose is True

    def test_verbose_setter_false(self):
        """Test setting verbose to False."""
        
        pr.settings.verbose = False
        assert pr.settings.verbose is False

    def test_output_to_file_setter_true(self):
        """Test setting output_to_file to True."""
        
        pr.settings.output_to_file = True
        assert pr.settings.output_to_file is True

    def test_output_to_file_setter_false(self):
        """Test setting output_to_file to False."""
        
        pr.settings.output_to_file = False
        assert pr.settings.output_to_file is False

    def test_output_file_name_setter_valid_string(self):
        """Test setting output_file_name to valid string."""
        
        pr.settings.output_file_name = "test_output"
        assert pr.settings.output_file_name == "test_output"

    def test_output_file_name_setter_empty_string(self):
        """Test setting output_file_name to empty string."""
        
        pr.settings.output_file_name = ""
        assert pr.settings.output_file_name == ""

    def test_graph_attribute_parsing_setter_true(self):
        """Test setting graph_attribute_parsing to True."""
        
        pr.settings.graph_attribute_parsing = True
        assert pr.settings.graph_attribute_parsing is True

    def test_graph_attribute_parsing_setter_false(self):
        """Test setting graph_attribute_parsing to False."""
        
        pr.settings.graph_attribute_parsing = False
        assert pr.settings.graph_attribute_parsing is False

    def test_abort_on_inconsistency_setter_true(self):
        """Test setting abort_on_inconsistency to True."""
        
        pr.settings.abort_on_inconsistency = True
        assert pr.settings.abort_on_inconsistency is True

    def test_memory_profile_setter_true(self):
        """Test setting memory_profile to True."""
        
        pr.settings.memory_profile = True
        assert pr.settings.memory_profile is True

    def test_reverse_digraph_setter_true(self):
        """Test setting reverse_digraph to True."""
        
        pr.settings.reverse_digraph = True
        assert pr.settings.reverse_digraph is True

    def test_atom_trace_setter_true(self):
        """Test setting atom_trace to True."""
        
        pr.settings.atom_trace = True
        assert pr.settings.atom_trace is True

    def test_save_graph_attributes_to_trace_setter_true(self):
        """Test setting save_graph_attributes_to_trace to True."""
        
        pr.settings.save_graph_attributes_to_trace = True
        assert pr.settings.save_graph_attributes_to_trace is True

    def test_canonical_setter_false(self):
        """Test setting canonical to False."""
        
        pr.settings.canonical = False
        assert pr.settings.canonical is False

    def test_persistent_setter_false(self):
        """Test setting persistent to False."""
        
        pr.settings.persistent = False
        assert pr.settings.persistent is False

    def test_inconsistency_check_setter_true(self):
        """Test setting inconsistency_check to True."""
        
        pr.settings.inconsistency_check = True
        assert pr.settings.inconsistency_check is True

    def test_static_graph_facts_setter_false(self):
        """Test setting static_graph_facts to False."""
        
        pr.settings.static_graph_facts = False
        assert pr.settings.static_graph_facts is False

    def test_store_interpretation_changes_setter_true(self):
        """Test setting store_interpretation_changes to True."""
        
        pr.settings.store_interpretation_changes = True
        assert pr.settings.store_interpretation_changes is True

    def test_parallel_computing_setter_true(self):
        """Test setting parallel_computing to True."""
        
        pr.settings.parallel_computing = True
        assert pr.settings.parallel_computing is True

    def test_update_mode_setter_valid_string(self):
        """Test setting update_mode to valid string."""
        
        pr.settings.update_mode = "parallel"
        assert pr.settings.update_mode == "parallel"

    def test_allow_ground_rules_setter_false(self):
        """Test setting allow_ground_rules to False."""
        
        pr.settings.allow_ground_rules = False
        assert pr.settings.allow_ground_rules is False

    def test_fp_version_setter_true(self):
        """Test setting fp_version to True."""
        
        pr.settings.fp_version = True
        assert pr.settings.fp_version is True


class TestSettingsInvalidSetters:
    """Test type validation for all property setters."""

    def setup_method(self):
        """Reset settings before each test."""
        
        pr.reset_settings()

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_verbose_setter_invalid_type(self, invalid_value):
        """Test verbose setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.verbose = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_output_to_file_setter_invalid_type(self, invalid_value):
        """Test output_to_file setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.output_to_file = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        True, False, 123, 3.14, [], {}, None, object()
    ])
    def test_output_file_name_setter_invalid_type(self, invalid_value):
        """Test output_file_name setter with invalid types."""
        
        with pytest.raises(TypeError, match='file_name has to be a string'):
            pr.settings.output_file_name = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_graph_attribute_parsing_setter_invalid_type(self, invalid_value):
        """Test graph_attribute_parsing setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.graph_attribute_parsing = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_abort_on_inconsistency_setter_invalid_type(self, invalid_value):
        """Test abort_on_inconsistency setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.abort_on_inconsistency = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_memory_profile_setter_invalid_type(self, invalid_value):
        """Test memory_profile setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.memory_profile = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_reverse_digraph_setter_invalid_type(self, invalid_value):
        """Test reverse_digraph setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.reverse_digraph = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_atom_trace_setter_invalid_type(self, invalid_value):
        """Test atom_trace setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.atom_trace = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_save_graph_attributes_to_trace_setter_invalid_type(self, invalid_value):
        """Test save_graph_attributes_to_trace setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.save_graph_attributes_to_trace = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_canonical_setter_invalid_type(self, invalid_value):
        """Test canonical setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.canonical = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_persistent_setter_invalid_type(self, invalid_value):
        """Test persistent setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.persistent = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_inconsistency_check_setter_invalid_type(self, invalid_value):
        """Test inconsistency_check setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.inconsistency_check = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_static_graph_facts_setter_invalid_type(self, invalid_value):
        """Test static_graph_facts setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.static_graph_facts = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_store_interpretation_changes_setter_invalid_type(self, invalid_value):
        """Test store_interpretation_changes setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.store_interpretation_changes = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_parallel_computing_setter_invalid_type(self, invalid_value):
        """Test parallel_computing setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.parallel_computing = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        True, False, 123, 3.14, [], {}, None, object()
    ])
    def test_update_mode_setter_invalid_type(self, invalid_value):
        """Test update_mode setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a str'):
            pr.settings.update_mode = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_allow_ground_rules_setter_invalid_type(self, invalid_value):
        """Test allow_ground_rules setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.allow_ground_rules = invalid_value

    @pytest.mark.parametrize("invalid_value", [
        "not_bool", 123, 3.14, [], {}, None, object()
    ])
    def test_fp_version_setter_invalid_type(self, invalid_value):
        """Test fp_version setter with invalid types."""
        
        with pytest.raises(TypeError, match='value has to be a bool'):
            pr.settings.fp_version = invalid_value


class TestSettingsReset:
    """Test settings reset functionality."""

    def test_reset_settings_restores_all_defaults(self):
        """Test that reset_settings restores all properties to defaults."""
        

        # Change all settings to non-default values
        pr.settings.verbose = False
        pr.settings.output_to_file = True
        pr.settings.output_file_name = "custom_output"
        pr.settings.graph_attribute_parsing = False
        pr.settings.abort_on_inconsistency = True
        pr.settings.memory_profile = True
        pr.settings.reverse_digraph = True
        pr.settings.atom_trace = True
        pr.settings.save_graph_attributes_to_trace = True
        pr.settings.canonical = True
        pr.settings.persistent = True
        pr.settings.inconsistency_check = False
        pr.settings.static_graph_facts = False
        pr.settings.store_interpretation_changes = False
        pr.settings.parallel_computing = True
        pr.settings.update_mode = "custom_mode"
        pr.settings.allow_ground_rules = True
        pr.settings.fp_version = True

        # Reset settings
        pr.reset_settings()

        # Verify all are back to defaults
        assert pr.settings.verbose is True
        assert pr.settings.output_to_file is False
        assert pr.settings.output_file_name == 'pyreason_output'
        assert pr.settings.graph_attribute_parsing is True
        assert pr.settings.abort_on_inconsistency is False
        assert pr.settings.memory_profile is False
        assert pr.settings.reverse_digraph is False
        assert pr.settings.atom_trace is False
        assert pr.settings.save_graph_attributes_to_trace is False
        assert pr.settings.canonical is False
        assert pr.settings.persistent is False
        assert pr.settings.inconsistency_check is True
        assert pr.settings.static_graph_facts is True
        assert pr.settings.store_interpretation_changes is True
        assert pr.settings.parallel_computing is False
        assert pr.settings.update_mode == 'intersection'
        assert pr.settings.allow_ground_rules is False
        assert pr.settings.fp_version is False

    def test_settings_reset_method(self):
        """Test the Settings.reset() method directly."""
        

        # Change some settings
        pr.settings.verbose = False
        pr.settings.memory_profile = True
        pr.settings.canonical = True

        # Call reset method directly
        pr.settings.reset()

        # Verify settings are reset
        assert pr.settings.verbose is True
        assert pr.settings.memory_profile is False
        assert pr.settings.canonical is False


class TestSettingsState:
    """Test settings state management and isolation."""

    def test_settings_modification_persists(self):
        """Test that settings modifications persist until reset."""
        
        pr.reset_settings()

        # Modify a setting
        pr.settings.verbose = True
        assert pr.settings.verbose is True

        # Should still be True
        assert pr.settings.verbose is True

    def test_multiple_settings_modifications(self):
        """Test modifying multiple settings in sequence."""
        
        pr.reset_settings()

        # Modify multiple settings
        pr.settings.verbose = True
        pr.settings.memory_profile = True
        pr.settings.output_file_name = "test"

        # All should be set correctly
        assert pr.settings.verbose is True
        assert pr.settings.memory_profile is True
        assert pr.settings.output_file_name == "test"
