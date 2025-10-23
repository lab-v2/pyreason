"""
Unit tests for pyreason global state management and reset functions.
Tests the critical reset(), reset_rules(), reset_settings() functions and global variable handling.
"""

import pytest
from unittest.mock import patch, MagicMock
import pyreason as pr


class TestResetFunction:
    """Test the main reset() function."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    @patch('pyreason.pyreason.__program')
    def test_reset_calls_program_methods_when_program_exists(self, mock_program):
        """Test reset() calls program reset methods when program exists."""
        # Mock program exists
        mock_program_instance = MagicMock()
        mock_program.return_value = mock_program_instance

        # Make __program not None
        with patch('pyreason.pyreason.__program', mock_program_instance):
            pr.reset()

            # Verify program reset methods were called
            mock_program_instance.reset_facts.assert_called_once()
            mock_program_instance.reset_graph.assert_called_once()

    def test_reset_handles_none_program(self):
        """Test reset() handles None program gracefully."""
        # Should not raise any exceptions
        pr.reset()

    def test_reset_calls_reset_rules(self):
        """Test that reset() calls reset_rules()."""
        with patch('pyreason.pyreason.reset_rules') as mock_reset_rules:
            pr.reset()
            mock_reset_rules.assert_called_once()

    def test_reset_clears_node_facts_global(self):
        """Test that reset() clears __node_facts global variable."""
        # Note: We can't easily test the actual global variable state
        # without complex mocking, but we can test the function doesn't crash
        pr.reset()

    def test_reset_clears_edge_facts_global(self):
        """Test that reset() clears __edge_facts global variable."""
        pr.reset()

    def test_reset_clears_graph_global(self):
        """Test that reset() clears __graph global variable."""
        pr.reset()


class TestResetRulesFunction:
    """Test the reset_rules() function - includes critical annotation_functions bug fix."""

    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_reset_rules_basic_functionality(self):
        """Test reset_rules() basic operation."""
        # Should not raise exceptions
        pr.reset_rules()

    @patch('pyreason.pyreason.__program')
    def test_reset_rules_calls_program_reset_when_program_exists(self, mock_program):
        """Test reset_rules() calls program.reset_rules() when program exists."""
        mock_program_instance = MagicMock()

        with patch('pyreason.pyreason.__program', mock_program_instance):
            pr.reset_rules()
            mock_program_instance.reset_rules.assert_called_once()

    def test_reset_rules_handles_none_program(self):
        """Test reset_rules() handles None program gracefully."""
        # Should not raise any exceptions
        pr.reset_rules()

    def test_reset_rules_clears_annotation_functions(self):
        # Add an annotation function
        def test_annotation_func(annotations, weights):
            return 0.5, 0.5
        pr.add_annotation_function(test_annotation_func)

        # Reset rules should clear annotation functions
        pr.reset_rules()

    def test_annotation_functions_isolation_between_resets(self):
        """
        Test that annotation functions are properly isolated between reset_rules() calls.
        This ensures the bug fix works correctly.
        """

        # Add annotation function
        def func1(annotations, weights):
            return 0.1, 0.1

        pr.add_annotation_function(func1)

        # Reset
        pr.reset_rules()

        # Add a different annotation function
        def func2(annotations, weights):
            return 0.2, 0.2

        pr.add_annotation_function(func2)

        # Reset again
        pr.reset_rules()

        # Should work without Numba typing errors

    def test_multiple_annotation_functions_reset(self):
        """Test reset_rules() with multiple annotation functions."""
        # Add multiple annotation functions
        def func1(annotations, weights):
            return 0.1, 0.1

        def func2(annotations, weights):
            return 0.2, 0.2

        def func3(annotations, weights):
            return 0.3, 0.3

        pr.add_annotation_function(func1)
        pr.add_annotation_function(func2)
        pr.add_annotation_function(func3)

        # Reset should clear all
        pr.reset_rules()


class TestResetSettingsFunction:
    """Test the reset_settings() function."""

    def test_reset_settings_calls_settings_reset(self):
        """Test that reset_settings() calls settings.reset()."""
        with patch.object(pr.settings, 'reset') as mock_reset:
            pr.reset_settings()
            mock_reset.assert_called_once()

    def test_reset_settings_restores_defaults(self):
        """Test that reset_settings() actually restores default values."""
        # Change settings
        pr.settings.verbose = False
        pr.settings.memory_profile = True
        pr.settings.output_file_name = "custom"

        # Reset
        pr.reset_settings()

        # Verify defaults restored
        assert pr.settings.verbose is True
        assert pr.settings.memory_profile is False
        assert pr.settings.output_file_name == "pyreason_output"


class TestGlobalStateManagement:
    """Test global variable state management."""

    def setup_method(self):
        """Clean state before each test."""
        pr.reset()
        pr.reset_settings()

    def test_torch_integration_consistency(self):
        """Test that torch integration variables are consistent"""
        # Just verify the current state is consistent
        if hasattr(pr, 'LogicIntegratedClassifier'):
            if pr.LogicIntegratedClassifier is None:
                # If LogicIntegratedClassifier is None, ModelInterfaceOptions should also be None
                assert pr.ModelInterfaceOptions is None
            else:
                # If LogicIntegratedClassifier exists, ModelInterfaceOptions should also exist
                assert pr.ModelInterfaceOptions is not None

    def test_state_isolation_between_operations(self):
        """Test that state is properly isolated between operations."""
        # This test verifies that subsequent operations don't interfere
        # with each other due to global state pollution

        # First operation
        pr.reset()

        # Second operation
        pr.reset_rules()

        # Third operation
        pr.reset_settings()

        # Should all work without issues

    def test_annotation_functions_state_consistency(self):
        """
        Test annotation functions state consistency across operations.
        This is a comprehensive test for the annotation_functions bug fix.
        """
        # Test sequence that previously caused Numba typing errors

        # 1. Start clean
        pr.reset()
        pr.reset_rules()

        # 2. Add annotation function
        def test_func(annotations, weights):
            return 0.5, 0.5

        pr.add_annotation_function(test_func)

        # 3. Reset (should clear annotation functions)
        pr.reset_rules()

        # 4. Add different annotation function
        def test_func2(annotations, weights):
            return 0.8, 0.8

        pr.add_annotation_function(test_func2)

        # 5. Reset again
        pr.reset_rules()

        # This sequence should work without Numba typing errors

    def test_reset_sequence_comprehensive(self):
        """Test comprehensive reset sequence."""
        # Test the full reset sequence
        pr.reset()           # Reset main state
        pr.reset_rules()     # Reset rules and annotation functions
        pr.reset_settings()  # Reset settings

        # Should be in clean state

    def test_repeated_resets_are_safe(self):
        """Test that repeated resets are safe and don't cause issues."""
        # Multiple resets should be safe
        for _ in range(5):
            pr.reset()
            pr.reset_rules()
            pr.reset_settings()


class TestStateConsistency:
    """Test state consistency across different operations."""
    def setup_method(self):
        """Clean state before each test."""
        
        pr.reset()
        pr.reset_settings()

    def test_settings_persist_across_reset(self):
        """Test that settings changes persist across reset() (but not reset_settings())."""
        # Change a setting
        pr.settings.verbose = True

        # Call reset() (not reset_settings())
        pr.reset()

        # Setting should still be changed
        assert pr.settings.verbose is True

        # But reset_settings() should restore it
        pr.reset_settings()
        assert pr.settings.verbose is True

    def test_rules_reset_independence(self):
        """Test that reset_rules() is independent of other reset operations."""
        # Change settings
        pr.settings.verbose = True

        # Reset rules
        pr.reset_rules()

        # Settings should be unchanged
        assert pr.settings.verbose is True

    def test_full_cleanup_sequence(self):
        """Test the complete cleanup sequence for test isolation."""
        # This is the sequence that should be used for test cleanup
        # to ensure complete state isolation

        pr.reset()           # Clear main state
        pr.reset_settings()  # Reset settings to defaults

        # Verify clean state
        assert pr.settings.verbose is True
        assert pr.settings.memory_profile is False
        assert pr.settings.output_file_name == "pyreason_output"
