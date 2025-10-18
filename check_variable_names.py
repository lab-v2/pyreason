#!/usr/bin/env python3
"""
Script to check for occurrences of specific variable names in Python codebase.
Uses AST parsing to avoid false positives from comments and strings.
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import List, Tuple


class VariableNameVisitor(ast.NodeVisitor):
    """AST visitor that finds all occurrences of a specific variable name."""

    def __init__(self, target_name: str, filepath: str):
        self.target_name = target_name
        self.filepath = filepath
        self.occurrences: List[Tuple[int, int, str, str]] = []

    def visit_Name(self, node: ast.Name) -> None:
        """Visit Name nodes (variable references)."""
        if node.id == self.target_name:
            context = "reference"
            if isinstance(node.ctx, ast.Store):
                context = "assignment"
            elif isinstance(node.ctx, ast.Del):
                context = "deletion"
            self.occurrences.append((node.lineno, node.col_offset, context, node.id))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to check parameter names."""
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.arg == self.target_name:
                self.occurrences.append((arg.lineno, arg.col_offset, "function_parameter", arg.arg))
        if node.args.vararg and node.args.vararg.arg == self.target_name:
            self.occurrences.append((node.args.vararg.lineno, node.args.vararg.col_offset, "vararg", node.args.vararg.arg))
        if node.args.kwarg and node.args.kwarg.arg == self.target_name:
            self.occurrences.append((node.args.kwarg.lineno, node.args.kwarg.col_offset, "kwarg", node.args.kwarg.arg))
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Visit argument nodes."""
        if node.arg == self.target_name:
            self.occurrences.append((node.lineno, node.col_offset, "argument", node.arg))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Visit exception handler to check exception variable names."""
        if node.name == self.target_name:
            self.occurrences.append((node.lineno, node.col_offset, "exception_var", node.name))
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """Visit comprehension to check target variables."""
        if isinstance(node.target, ast.Name) and node.target.id == self.target_name:
            self.occurrences.append((node.target.lineno, node.target.col_offset, "comprehension_var", node.target.id))
        self.generic_visit(node)


def find_python_files(root_dir: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """Find all Python files in the directory tree."""
    if exclude_patterns is None:
        exclude_patterns = []

    python_files = []
    for py_file in root_dir.rglob("*.py"):
        # Check if file should be excluded
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(py_file):
                should_exclude = True
                break

        if not should_exclude:
            python_files.append(py_file)

    return python_files


def check_file_for_variable(filepath: Path, variable_name: str) -> List[Tuple[int, int, str, str]]:
    """Check a single file for occurrences of the variable name."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        visitor = VariableNameVisitor(variable_name, str(filepath))
        visitor.visit(tree)

        return visitor.occurrences
    except SyntaxError:
        print(f"Warning: Could not parse {filepath} (syntax error)", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Error processing {filepath}: {e}", file=sys.stderr)
        return []


def get_line_content(filepath: Path, lineno: int) -> str:
    """Get the content of a specific line from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if 0 < lineno <= len(lines):
                return lines[lineno - 1].rstrip()
    except Exception:
        pass
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Check for occurrences of specific variable names in Python codebase"
    )
    parser.add_argument(
        "variable_name",
        help="The variable name to search for"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Root directory to search (default: current directory)"
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[".venv", "__pycache__", ".git", "build", "dist", ".eggs"],
        help="Patterns to exclude from search"
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files (excluded by default)"
    )
    parser.add_argument(
        "--include-docs",
        action="store_true",
        help="Include documentation files (excluded by default)"
    )

    args = parser.parse_args()

    # Add default exclusions
    exclude_patterns = args.exclude.copy()
    if not args.include_tests:
        exclude_patterns.extend(["test_", "tests/"])
    if not args.include_docs:
        exclude_patterns.extend(["docs/", "examples/"])

    # Find all Python files
    print(f"Searching for variable '{args.variable_name}' in {args.path}")
    print(f"Excluding patterns: {exclude_patterns}\n")

    python_files = find_python_files(args.path, exclude_patterns)
    print(f"Found {len(python_files)} Python files to check\n")

    # Check each file
    total_occurrences = 0
    files_with_occurrences = 0

    for filepath in sorted(python_files):
        occurrences = check_file_for_variable(filepath, args.variable_name)

        if occurrences:
            files_with_occurrences += 1
            total_occurrences += len(occurrences)

            # Display relative path
            try:
                rel_path = filepath.relative_to(args.path)
            except ValueError:
                rel_path = filepath

            print(f"\n{rel_path}:")
            for lineno, col_offset, context, var_name in sorted(occurrences):
                line_content = get_line_content(filepath, lineno)
                print(f"  Line {lineno}, Col {col_offset} ({context}): {line_content.strip()}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Variable name: '{args.variable_name}'")
    print(f"  Files checked: {len(python_files)}")
    print(f"  Files with occurrences: {files_with_occurrences}")
    print(f"  Total occurrences: {total_occurrences}")
    print(f"{'=' * 60}")

    # Exit with non-zero if occurrences found
    if total_occurrences > 0:
        sys.exit(1)
    else:
        print("\nNo occurrences found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
