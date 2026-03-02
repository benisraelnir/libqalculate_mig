"""
CLI integration tests for the qalc command.

Tests the command-line interface by invoking qalc via subprocess
and checking outputs for --help, --version, and basic expressions.
"""

from __future__ import annotations

import subprocess
import sys
import os

import pytest


# Path to the python package directory
_PYTHON_DIR = os.path.join(os.path.dirname(__file__), '..', 'python')


def run_qalc(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
    """
    Run the qalc CLI as a subprocess.

    Uses `python -m qalculate.cli.qalc` to invoke the CLI,
    ensuring the package is on the path.
    """
    cmd = [sys.executable, "-m", "qalculate.cli.qalc"] + list(args)
    env = os.environ.copy()
    # Ensure the python package is importable
    env["PYTHONPATH"] = os.path.abspath(_PYTHON_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        input=input_text,
    )
    return result


class TestCLIHelp:
    """Test --help flag."""

    def test_help_flag(self):
        result = run_qalc("--help")
        assert result.returncode == 0
        assert "usage: qalc" in result.stdout.lower()

    def test_help_short_flag(self):
        result = run_qalc("-h")
        assert result.returncode == 0
        assert "usage: qalc" in result.stdout.lower()

    def test_help_contains_options(self):
        result = run_qalc("--help")
        assert "-v" in result.stdout
        assert "-version" in result.stdout
        assert "-t" in result.stdout or "-terse" in result.stdout
        assert "-base" in result.stdout or "-b" in result.stdout


class TestCLIVersion:
    """Test --version flag."""

    def test_version_flag(self):
        result = run_qalc("--version")
        assert result.returncode == 0
        # Should output version string
        version_output = result.stdout.strip()
        assert version_output  # Not empty
        # Should be a version-like string (digits and dots)
        assert any(c.isdigit() for c in version_output)

    def test_version_short_flag(self):
        result = run_qalc("-v")
        assert result.returncode == 0
        version_output = result.stdout.strip()
        assert version_output

    def test_version_matches_package(self):
        """Version from CLI should match package __version__."""
        result = run_qalc("--version")
        from qalculate import __version__
        assert result.stdout.strip() == __version__


class TestCLIExpressionEvaluation:
    """Test basic expression evaluation via CLI (Milestone 1 stub)."""

    def test_simple_addition(self):
        result = run_qalc("1+1")
        assert result.returncode == 0
        # Output should contain "2"
        assert "2" in result.stdout

    def test_simple_multiplication(self):
        result = run_qalc("3*4")
        assert result.returncode == 0
        assert "12" in result.stdout

    def test_terse_mode(self):
        result = run_qalc("-t", "2+3")
        assert result.returncode == 0
        assert "5" in result.stdout


class TestCLIInteractiveStub:
    """Test the interactive mode stub."""

    def test_interactive_quit(self):
        """Interactive mode should exit cleanly on 'quit'."""
        result = run_qalc("-i", input_text="quit\n")
        assert result.returncode == 0

    def test_interactive_exit(self):
        """Interactive mode should exit cleanly on 'exit'."""
        result = run_qalc("-i", input_text="exit\n")
        assert result.returncode == 0

    def test_interactive_eof(self):
        """Interactive mode should exit cleanly on EOF."""
        result = run_qalc("-i", input_text="")
        assert result.returncode == 0
