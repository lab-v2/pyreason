#!/usr/bin/env python3
"""
Unified test runner for PyReason test suites.

This script handles running multiple test suites with different configurations
(JIT enabled/disabled, stubbed environments) and aggregates coverage reports.

Usage:
    python run_tests.py                    # Run all test suites
    python run_tests.py --suite api_tests  # Run specific suite
    python run_tests.py --fast             # Run fast suites only
    python run_tests.py --no-coverage      # Skip coverage collection
    python run_tests.py --parallel         # Run compatible suites in parallel
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
# from pathlib import Path  # Not used
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


class TestSuite:
    """Represents a test suite configuration."""

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.display_name = config['name']
        self.description = config['description']
        self.path = config['path']
        self.coverage_source = config['coverage_source']
        self.jit_disabled = config['jit_disabled']
        self.uses_real_pyreason = config['uses_real_pyreason']
        self.environment_vars = config['environment_vars']
        self.pytest_args = config['pytest_args']
        self.timeout = config['timeout']

    def __str__(self):
        return f"{self.display_name} ({self.name})"


class TestRunner:
    """Main test runner class."""

    def __init__(self, config_file: str = "test_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.suites = self._create_suites()
        self.temp_dir = None
        self.coverage_files = []

    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self._error(f"Configuration file {self.config_file} not found")
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON in {self.config_file}: {e}")

    def _create_suites(self) -> Dict[str, TestSuite]:
        """Create TestSuite objects from configuration."""
        suites = {}
        for name, config in self.config['test_suites'].items():
            suites[name] = TestSuite(name, config)
        return suites

    def _print(self, message: str, color: str = "", bold: bool = False):
        """Print colored message."""
        prefix = ""
        if bold:
            prefix += Colors.BOLD
        if color:
            prefix += color

        suffix = Colors.END if (color or bold) else ""
        print(f"{prefix}{message}{suffix}")

    def _error(self, message: str):
        """Print error message and exit."""
        self._print(f"ERROR: {message}", Colors.RED, bold=True)
        sys.exit(1)

    def _success(self, message: str):
        """Print success message."""
        self._print(message, Colors.GREEN, bold=True)

    def _info(self, message: str):
        """Print info message."""
        self._print(message, Colors.BLUE)

    def _warning(self, message: str):
        """Print warning message."""
        self._print(message, Colors.YELLOW)

    def _find_python_command(self) -> str:
        """Find the best available Python command."""
        # First check if we're in a virtual environment
        if 'VIRTUAL_ENV' in os.environ:
            venv_python = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'python')
            if os.path.exists(venv_python):
                return venv_python

        # Look for common venv patterns in current directory
        venv_patterns = ['./.venv/bin/python', './venv/bin/python', './env/bin/python']
        for venv_path in venv_patterns:
            if os.path.exists(venv_path):
                return venv_path

        # Try different python commands in order of preference
        # Prioritize Python 3.9 as PyReason doesn't support 3.13+
        candidates = [
            'python3.9',
            '/usr/bin/python3',      # System Python (often 3.9 on macOS)
            'python3',
            'python',
            'python3.11'
        ]

        for cmd in candidates:
            try:
                result = subprocess.run([cmd, '--version'],
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Fallback to python3 if nothing else works
        return 'python3'

    def run_suite(self, suite: TestSuite, coverage: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Run a single test suite.

        Returns:
            Tuple of (success: bool, coverage_file_path: Optional[str])
        """
        self._info(f"\\n{'='*60}")
        self._info(f"Running {suite.display_name}")
        self._info(f"Path: {suite.path}")
        self._info(f"JIT Disabled: {suite.jit_disabled}")
        self._info(f"Uses Real PyReason: {suite.uses_real_pyreason}")
        self._info(f"{'='*60}")

        # Prepare environment
        env = os.environ.copy()
        env.update(suite.environment_vars)

        # Prepare pytest command - try to find python/pytest
        python_cmd = self._find_python_command()
        cmd = [python_cmd, '-m', 'pytest']
        print("Running command with Python:", python_cmd)

        coverage_file_path = None
        if coverage:
            # Create coverage config if it doesn't exist
            self._create_coverage_config()

            # Create unique coverage file for this suite
            coverage_file_path = os.path.join(self.temp_dir, f".coverage.{suite.name}")
            cmd.extend([
                '--cov', suite.coverage_source,
                '--cov-report', 'term-missing',
                '--cov-append',
                f'--cov-config={self.temp_dir}/.coveragerc'
            ])
            env['COVERAGE_FILE'] = coverage_file_path

        cmd.extend(suite.pytest_args)
        cmd.append(suite.path)

        self._info(f"Command: {' '.join(cmd)}")

        # Run the test
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                env=env,
                timeout=suite.timeout,
                capture_output=False,  # Show output in real-time
                cwd=os.getcwd()
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            if success:
                self._success(f"✓ {suite.display_name} completed in {duration:.1f}s")
            else:
                self._warning(f"✗ {suite.display_name} failed after {duration:.1f}s (exit code: {result.returncode})")

            # Check if coverage file was actually created
            if coverage and coverage_file_path and os.path.exists(coverage_file_path):
                return success, coverage_file_path
            else:
                return success, None

        except subprocess.TimeoutExpired:
            self._warning(f"✗ {suite.display_name} timed out after {suite.timeout}s")
            return False, None
        except Exception as e:
            self._warning(f"✗ {suite.display_name} failed with error: {e}")
            return False, None

    def run_suites_parallel(self, suites: List[TestSuite], coverage: bool = True) -> List[Tuple[TestSuite, bool, Optional[str]]]:
        """Run multiple suites in parallel."""
        self._info(f"\\nRunning {len(suites)} suites in parallel...")

        results = []
        with ThreadPoolExecutor(max_workers=len(suites)) as executor:
            # Submit all suites
            future_to_suite = {
                executor.submit(self.run_suite, suite, coverage): suite
                for suite in suites
            }

            # Collect results as they complete
            for future in as_completed(future_to_suite):
                suite = future_to_suite[future]
                try:
                    success, coverage_file = future.result()
                    results.append((suite, success, coverage_file))
                except Exception as e:
                    self._warning(f"Suite {suite.name} failed with exception: {e}")
                    results.append((suite, False, None))

        return results

    def run_suites_sequential(self, suites: List[TestSuite], coverage: bool = True) -> List[Tuple[TestSuite, bool, Optional[str]]]:
        """Run multiple suites sequentially."""
        results = []
        for suite in suites:
            success, coverage_file = self.run_suite(suite, coverage)
            results.append((suite, success, coverage_file))
        return results

    def _create_coverage_config(self):
        """Create coverage configuration file."""
        coverage_config = f"""
[run]
source = pyreason
omit =
    */tests/*
    */conftest.py
    */__pycache__/*
    */setup.py
    */interpretation_parallel.py
    */yaml_parser.py
    

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod

[html]
directory = {self.config['output']['combined_report_dir']}/htmlcov

[xml]
output = {self.config['output']['combined_report_dir']}/coverage.xml
"""

        coverage_rc = os.path.join(self.temp_dir, '.coveragerc')
        with open(coverage_rc, 'w') as f:
            f.write(coverage_config)
        return coverage_rc

    def combine_coverage(self, coverage_files: List[str]):
        """Combine coverage files and generate reports."""
        if not coverage_files:
            self._warning("No coverage files to combine")
            return

        self._info(f"\\nCombining coverage from {len(coverage_files)} suites...")

        # Create output directory in project root
        report_dir = self.config['output']['combined_report_dir']
        project_report_dir = os.path.abspath(report_dir)
        os.makedirs(project_report_dir, exist_ok=True)

        # Combine coverage files
        combined_coverage = os.path.join(self.temp_dir, '.coverage.combined')
        cmd = ['coverage', 'combine'] + coverage_files

        env = os.environ.copy()
        env['COVERAGE_FILE'] = combined_coverage

        try:
            subprocess.run(cmd, check=True, env=env, cwd=self.temp_dir)

            # Copy combined coverage file to project directory
            project_coverage_file = os.path.join(os.getcwd(), '.coverage')
            shutil.copy2(combined_coverage, project_coverage_file)

            # Generate reports - run from project directory so reports go to correct location
            coverage_config = self._create_coverage_config()

            # Set environment to use the copied coverage file
            project_env = os.environ.copy()
            project_env['COVERAGE_FILE'] = project_coverage_file

            if self.config['coverage']['html_report']:
                self._info("Generating HTML coverage report...")
                self._info(f"Working directory: {os.getcwd()}")
                self._info(f"Target directory: {project_report_dir}/htmlcov/")
                subprocess.run([
                    'coverage', 'html',
                    f'--rcfile={coverage_config}'
                ], check=True, env=project_env, cwd=os.getcwd())

                # Verify the report was created
                html_report_path = os.path.join(project_report_dir, 'htmlcov', 'index.html')
                if os.path.exists(html_report_path):
                    self._success(f"HTML report: {html_report_path}")
                else:
                    self._warning(f"HTML report not found at expected location: {html_report_path}")
                    # List what was actually created
                    if os.path.exists(project_report_dir):
                        contents = os.listdir(project_report_dir)
                        self._info(f"Contents of {project_report_dir}: {contents}")

            if self.config['coverage']['xml_report']:
                self._info("Generating XML coverage report...")
                subprocess.run([
                    'coverage', 'xml',
                    f'--rcfile={coverage_config}'
                ], check=True, env=project_env, cwd=os.getcwd())
                self._success(f"XML report: {project_report_dir}/coverage.xml")

            # Show coverage summary
            self._info("\\nCoverage Summary:")
            subprocess.run([
                'coverage', 'report',
                f'--rcfile={coverage_config}'
            ], env=project_env, cwd=os.getcwd())

        except subprocess.CalledProcessError as e:
            self._warning(f"Coverage combination failed: {e}")
        except FileNotFoundError:
            self._warning("Coverage tool not found. Install with: pip install coverage")

    def run(self, suite_names: Optional[List[str]] = None,
            coverage: bool = True,
            parallel: bool = False,
            continue_on_failure: bool = True) -> bool:
        """
        Run test suites.

        Args:
            suite_names: List of suite names to run. If None, run all suites.
            coverage: Whether to collect coverage
            parallel: Whether to run compatible suites in parallel
            continue_on_failure: Whether to continue after suite failures

        Returns:
            True if all suites passed, False otherwise
        """

        # Determine which suites to run
        if suite_names:
            suites_to_run = []
            for name in suite_names:
                if name not in self.suites:
                    self._error(f"Unknown test suite: {name}")
                suites_to_run.append(self.suites[name])
        else:
            suites_to_run = list(self.suites.values())

        self._info(f"Running {len(suites_to_run)} test suite(s): {[s.name for s in suites_to_run]}")

        # Create temporary directory for coverage files
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir

            all_results = []

            if parallel and len(suites_to_run) > 1:
                # Determine which suites can run in parallel
                parallel_suites = [s for s in suites_to_run if s.name in self.config['execution']['parallel_suites']]
                sequential_suites = [s for s in suites_to_run if s.name in self.config['execution']['sequential_suites']]

                if parallel_suites:
                    results = self.run_suites_parallel(parallel_suites, coverage)
                    all_results.extend(results)

                if sequential_suites:
                    results = self.run_suites_sequential(sequential_suites, coverage)
                    all_results.extend(results)
            else:
                # Run all sequentially
                results = self.run_suites_sequential(suites_to_run, coverage)
                all_results.extend(results)

            # Collect coverage files
            coverage_files = [cf for _, _, cf in all_results if cf]

            # Combine coverage if requested
            if coverage and coverage_files:
                self.combine_coverage(coverage_files)

            # Print summary
            self._print_summary(all_results)

            # Return overall success
            all_passed = all(success for _, success, _ in all_results)
            if not continue_on_failure and not all_passed:
                return False

            return all_passed

    def _print_summary(self, results: List[Tuple[TestSuite, bool, Optional[str]]]):
        """Print test execution summary."""
        total = len(results)
        passed = sum(1 for _, success, _ in results if success)
        failed = total - passed

        self._print("\\n" + "="*60, bold=True)
        self._print("TEST EXECUTION SUMMARY", bold=True)
        self._print("="*60, bold=True)

        for suite, success, _ in results:  # coverage_file not used in summary
            status = "PASS" if success else "FAIL"
            color = Colors.GREEN if success else Colors.RED
            self._print(f"{suite.display_name:30} {status}", color, bold=True)

        self._print("="*60, bold=True)
        self._print(f"Total: {total}, Passed: {passed}, Failed: {failed}", bold=True)

        if failed == 0:
            self._success("🎉 All test suites passed!")
        else:
            self._warning(f"⚠️  {failed} test suite(s) failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified test runner for PyReason test suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                      # Run all test suites
  python run_tests.py --suite api_tests    # Run specific suite
  python run_tests.py --fast               # Run fast suites only
  python run_tests.py --no-coverage        # Skip coverage
  python run_tests.py --parallel           # Run in parallel where possible
        """
    )

    parser.add_argument(
        '--suite',
        action='append',
        help='Run specific test suite(s). Can be used multiple times.'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run only fast test suites (api_tests, dont_disable_jit)'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Skip coverage collection'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run compatible suites in parallel'
    )
    parser.add_argument(
        '--continue-on-failure',
        action='store_true',
        default=True,
        help='Continue running remaining suites after a failure (default: True)'
    )
    parser.add_argument(
        '--config',
        default='test_config.json',
        help='Path to test configuration file'
    )

    args = parser.parse_args()

    # Determine suites to run
    suite_names = None
    if args.suite:
        suite_names = args.suite
    elif args.fast:
        suite_names = ['api_tests', 'dont_disable_jit']

    # Create and run test runner
    runner = TestRunner(args.config)

    success = runner.run(
        suite_names=suite_names,
        coverage=not args.no_coverage,
        parallel=args.parallel,
        continue_on_failure=args.continue_on_failure
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
