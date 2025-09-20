#!/usr/bin/env python3
"""
Script to automatically apply @pytest.mark.slow decorators to test functions
that take more than 5 seconds to execute.

Usage: python apply_slow_markers.py
"""

import re
import os
from typing import List, Tuple

# Tests identified as slow (>5 seconds) from timing analysis
SLOW_TESTS = [
    "tests/functional/test_annotation_function.py::test_annotation_function",  # 41.93s
    "tests/functional/test_annotation_function.py::test_annotation_function_fp",  # 21.96s
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_1",  # 5.60s
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_2",  # 5.85s
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_3",  # 5.56s
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_4",  # likely >5s (similar test)
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_1_fp",  # likely >5s (FP version)
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_2_fp",  # likely >5s (FP version)
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_3_fp",  # likely >5s (FP version)
    "tests/functional/test_anyBurl_infer_edges_rules.py::test_anyBurl_rule_4_fp",  # likely >5s (FP version)
    "tests/functional/test_custom_thresholds.py::test_custom_thresholds",  # 5.33s
    "tests/functional/test_custom_thresholds.py::test_custom_thresholds_fp",  # likely >5s (FP version)
    "tests/functional/test_hello_world.py::test_hello_world",  # 5.69s
]

def parse_test_location(test_path: str) -> Tuple[str, str]:
    """Parse test path into file path and function name."""
    file_path, function_name = test_path.split("::")
    return file_path, function_name

def apply_slow_marker_to_file(file_path: str, function_names: List[str]) -> bool:
    """Apply @pytest.mark.slow decorator to specified functions in a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line defines one of our target functions
        for func_name in function_names:
            if re.match(rf'^def {re.escape(func_name)}\(', line.strip()):
                # Check if the function already has a @pytest.mark.slow decorator
                has_slow_marker = False

                # Look backwards to check for existing decorators
                j = i - 1
                while j >= 0 and (lines[j].strip().startswith('@') or lines[j].strip() == ''):
                    if '@pytest.mark.slow' in lines[j]:
                        has_slow_marker = True
                        break
                    if not lines[j].strip().startswith('@') and lines[j].strip() != '':
                        break
                    j -= 1

                if not has_slow_marker:
                    # Get the indentation of the function definition
                    indentation = len(line) - len(line.lstrip())
                    indent_str = ' ' * indentation

                    # Add the @pytest.mark.slow decorator
                    new_lines.append(f"{indent_str}@pytest.mark.slow\n")
                    modified = True
                    print(f"  Added @pytest.mark.slow to {func_name}")
                else:
                    print(f"  {func_name} already has @pytest.mark.slow marker")

                break

        new_lines.append(line)
        i += 1

    # Write back the modified file if changes were made
    if modified:
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Modified {file_path}")
        return True
    else:
        print(f"No changes needed for {file_path}")
        return False

def main():
    """Main function to apply slow markers to all identified slow tests."""
    print("Applying @pytest.mark.slow decorators to slow tests...")
    print("Slow tests identified (>5 seconds):")
    for test in SLOW_TESTS:
        print(f"  - {test}")
    print()

    # Group tests by file
    files_to_modify = {}
    for test_path in SLOW_TESTS:
        file_path, function_name = parse_test_location(test_path)
        if file_path not in files_to_modify:
            files_to_modify[file_path] = []
        files_to_modify[file_path].append(function_name)

    # Apply markers to each file
    modified_files = []
    for file_path, function_names in files_to_modify.items():
        print(f"Processing {file_path}...")
        if apply_slow_marker_to_file(file_path, function_names):
            modified_files.append(file_path)
        print()

    print("Summary:")
    if modified_files:
        print(f"Modified {len(modified_files)} files:")
        for file_path in modified_files:
            print(f"  - {file_path}")
    else:
        print("No files were modified (all slow tests already had markers)")

if __name__ == "__main__":
    main()