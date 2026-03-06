#!/usr/bin/env python3
"""
BE Testing - CLI Contract Validation Tests

Generated pytest script to validate the CLI spec against the running application.
Each command is tested as a parameterized test case using pytest.

This script supports two modes:
1. SRC Validation: Tests commands and captures outputs (no expected_stdout/stderr)
2. DST Contract Validation: Tests commands and validates outputs match expected

Generated at: 2026-03-06T22:33:49.102345+00:00
Project: libqalculate-mig
Milestone: 5
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

# =============================================================================
# Test Configuration (embedded from spec validation)
# =============================================================================

_ENV_PLACEHOLDER = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


def resolve_env_placeholders(obj: Any) -> Any:
    """Recursively resolve ${VAR_NAME} environment variable placeholders in test data.

    Only resolves braced ${VAR} syntax to avoid unintentional expansion of
    unrelated $VAR patterns (e.g. $HOME, $stored.KEY).
    """
    if isinstance(obj, str):
        return _ENV_PLACEHOLDER.sub(lambda m: os.environ.get(m.group(1), m.group(0)), obj)
    if isinstance(obj, dict):
        return {k: resolve_env_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_env_placeholders(item) for item in obj]
    return obj


# Parse JSON at runtime, then resolve any ${VAR_NAME} env var placeholders
# that the agent may have substituted for detected secrets.
TEST_CASES = resolve_env_placeholders(json.loads(r'''[
    {
        "name": "test_help_output",
        "category": "HELP_OUTPUT",
        "description": "Verify --help shows usage information and exits with 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "usage: qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_short_flag",
        "category": "HELP_OUTPUT",
        "description": "Verify -h shows usage information and exits with 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-h"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "usage: qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_output",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version shows version string and exits with 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": ".",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_short_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify -v shows version string and exits with 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": ".",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_simple_addition",
        "category": "HAPPY_PATH",
        "description": "Evaluate a simple addition expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_simple_multiplication",
        "category": "HAPPY_PATH",
        "description": "Evaluate a simple multiplication expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3*7"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "21",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_simple_division",
        "category": "HAPPY_PATH",
        "description": "Evaluate a simple division expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10/2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_subtraction",
        "category": "HAPPY_PATH",
        "description": "Evaluate a subtraction expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100-37"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "63",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_power",
        "category": "HAPPY_PATH",
        "description": "Evaluate an exponentiation expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "2^10"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1024",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_parentheses",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with parentheses for correct precedence",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(2+3)*4"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "20",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_negative_number",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with negative numbers",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--",
            "-5+3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_decimal_arithmetic",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with decimal numbers",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3.14*2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6.28",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nested_parentheses",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with nested parentheses",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "((2+3)*(4-1))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "15",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_terse_mode",
        "category": "HAPPY_PATH",
        "description": "Verify terse mode outputs only the result",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5+5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_terse_long_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --terse flag works like -t",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--terse",
            "5+5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_base_hex",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with hexadecimal output base",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "16",
            "255"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "FF",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_base_bin",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with binary output base",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "2",
            "10"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1010",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_base_oct",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with octal output base",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "8",
            "8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_option_via_s",
        "category": "HAPPY_PATH",
        "description": "Use -s flag to set precision",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "precision 20",
            "pi"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.14159265358979323846",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_option_long_flag",
        "category": "HAPPY_PATH",
        "description": "Use --set flag to set precision",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--set",
            "precision 20",
            "pi"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.14159265358979323846",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_multiple_options_semicolon",
        "category": "HAPPY_PATH",
        "description": "Use -s with semicolon-separated multiple options",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "base 16;precision 10",
            "255"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "FF",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_unit_conversion",
        "category": "HAPPY_PATH",
        "description": "Evaluate expression with unit conversion using 'to'",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 km to m"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5000 m",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_function_sqrt",
        "category": "HAPPY_PATH",
        "description": "Evaluate sqrt function",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sqrt(144)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_function_sin",
        "category": "HAPPY_PATH",
        "description": "Evaluate sin function in radians mode",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "sin(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_programming_mode",
        "category": "HAPPY_PATH",
        "description": "Start in programming mode with -p flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-p",
            "16",
            "255"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "FF",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_expression_with_double_dash",
        "category": "HAPPY_PATH",
        "description": "Expression after -- separator is treated as expression not options",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_expression_with_spaces",
        "category": "HAPPY_PATH",
        "description": "Multiple positional args joined as expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "2",
            "+",
            "2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nodefs_flag",
        "category": "HAPPY_PATH",
        "description": "Verify -n/--nodefs prevents loading global definitions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-n",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_defaults_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --defaults loads default settings",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--defaults",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_time_limit",
        "category": "HAPPY_PATH",
        "description": "Verify -m timeout flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-m",
            "5000",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_list_all",
        "category": "HAPPY_PATH",
        "description": "List user-defined items with -l flag and exit",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-l"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_functions",
        "category": "HAPPY_PATH",
        "description": "List all functions with --list-functions flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-functions"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_units",
        "category": "HAPPY_PATH",
        "description": "List all units with --list-units flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-units"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_variables",
        "category": "HAPPY_PATH",
        "description": "List all variables with --list-variables flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-variables"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_prefixes",
        "category": "HAPPY_PATH",
        "description": "List all prefixes with --list-prefixes flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-prefixes"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_search_term",
        "category": "HAPPY_PATH",
        "description": "Search for matching items with -l and a search term",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-l",
            "meter"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "meter",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_list_functions_search",
        "category": "HAPPY_PATH",
        "description": "Search functions with --list-functions and a search term",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-functions",
            "sin"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "sin",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_file_execution",
        "category": "FILE_INPUT",
        "description": "Execute commands from a file with -f flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_commands.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_commands.txt",
                "content": "2+2\n3*3\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_commands.txt"
            ]
        }
    },
    {
        "name": "test_file_from_stdin",
        "category": "PIPE_INPUT",
        "description": "Execute commands from stdin with -f -",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "-"
        ],
        "stdin": "2+2\n",
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_pipe_expression",
        "category": "PIPE_INPUT",
        "description": "Pipe an expression to qalc via stdin file mode",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "-"
        ],
        "stdin": "10*10\n",
        "expected_exit_code": 0,
        "expected_stdout": "100",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_test_file_pass",
        "category": "HAPPY_PATH",
        "description": "Run batch test file with --test-file that should pass",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "test_batch.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "tests passed",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "test_batch.txt",
                "content": "2+2\n\t4\n3*3\n\t9\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_batch.txt"
            ]
        }
    },
    {
        "name": "test_test_file_fail",
        "category": "HAPPY_PATH",
        "description": "Run batch test file with --test-file that should fail on mismatch",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "test_batch_fail.txt"
        ],
        "expected_exit_code": 1,
        "expected_stdout": "Mismatch detected",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "test_batch_fail.txt",
                "content": "2+2\n\t5\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_batch_fail.txt"
            ]
        }
    },
    {
        "name": "test_test_file_empty",
        "category": "BOUNDARY",
        "description": "Run batch test file with --test-file that has no test lines (0 tests warning)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "test_batch_empty.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "WARNING: 0 tests were run",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_batch_empty.txt",
                "content": "\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_batch_empty.txt"
            ]
        }
    },
    {
        "name": "test_invalid_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown option should produce unrecognized option message",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--unknown-option",
            "--",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Unrecognized option",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_short_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown short option should produce unrecognized option message",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-z",
            "--",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Unrecognized option",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_no_value",
        "category": "INVALID_ARGS",
        "description": "Using -s without a value should produce error message",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "No option and value specified",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_file_nonexistent",
        "category": "INVALID_ARGS",
        "description": "Specifying a nonexistent file with -f should produce error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "nonexistent_file_xyz.txt"
        ],
        "expected_exit_code": 1,
        "expected_stdout": "Could not open",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_file_no_path",
        "category": "INVALID_ARGS",
        "description": "Using -f without a file path should produce error message",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "No file specified",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_empty_expression",
        "category": "BOUNDARY",
        "description": "Empty expression with terse mode should produce no output and enter interactive mode if no -i",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "-"
        ],
        "stdin": "\n",
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_large_number",
        "category": "BOUNDARY",
        "description": "Evaluate expression with very large numbers",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "999999999999999999+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1000000000000000000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_zero_division",
        "category": "BOUNDARY",
        "description": "Division by zero should produce a result (infinity or error message)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1/0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_complex_expression",
        "category": "HAPPY_PATH",
        "description": "Evaluate a complex arithmetic expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(2+3)*(4-1)/5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_pi_constant",
        "category": "HAPPY_PATH",
        "description": "Evaluate pi constant",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "pi"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.14159",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_euler_constant",
        "category": "HAPPY_PATH",
        "description": "Evaluate e (Euler's number) constant",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "e"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2.71828",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_color_flag_on",
        "category": "HAPPY_PATH",
        "description": "Verify -c flag is accepted for enabling color output",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-c",
            "1",
            "-t",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_color_flag_off",
        "category": "HAPPY_PATH",
        "description": "Verify -c 0 disables color output",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-c",
            "0",
            "-t",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nounits_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --nounits flag prevents loading units but basic arithmetic still works",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--nounits",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nofunctions_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --nofunctions flag prevents loading functions but basic arithmetic still works",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--nofunctions",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_novariables_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --novariables flag prevents loading variables but basic arithmetic still works",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--novariables",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nocurrencies_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --nocurrencies flag prevents loading currencies but basic arithmetic still works",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--nocurrencies",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nodatasets_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --nodatasets flag prevents loading datasets but basic arithmetic still works",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--nodatasets",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_expression_quoted",
        "category": "HAPPY_PATH",
        "description": "Evaluate a quoted expression (quotes stripped by shell)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"2+2\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_modulo_operation",
        "category": "HAPPY_PATH",
        "description": "Evaluate modulo operation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "mod(17,5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_abs_function",
        "category": "HAPPY_PATH",
        "description": "Evaluate abs function",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "abs(-5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_factorial",
        "category": "HAPPY_PATH",
        "description": "Evaluate factorial expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5!"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "120",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_long_expression",
        "category": "BOUNDARY",
        "description": "Evaluate a very long expression with many operations",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "50",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_batch_file_multiple_tests",
        "category": "FILE_INPUT",
        "description": "Run a batch test file with multiple expression/result pairs",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "test_multi_batch.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "tests passed",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "test_multi_batch.txt",
                "content": "2+2\n\t4\n10/2\n\t5\n3^3\n\t27\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_multi_batch.txt"
            ]
        }
    },
    {
        "name": "test_file_with_multiple_commands",
        "category": "FILE_INPUT",
        "description": "Execute a file with multiple expressions via -f",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_multi_cmds.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_multi_cmds.txt",
                "content": "2+2\n5*5\n10-3\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_multi_cmds.txt"
            ]
        }
    },
    {
        "name": "test_unicode_on",
        "category": "HAPPY_PATH",
        "description": "Enable unicode with -u8 flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-u8",
            "-t",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_unicode_off",
        "category": "HAPPY_PATH",
        "description": "Disable unicode with +u8 flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "+u8",
            "-t",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_settings_persistence_save_mode",
        "category": "FILE_INPUT",
        "description": "Verify 'save mode' command in file mode produces confirmation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_save_mode.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "mode saved",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_save_mode.txt",
                "content": "save mode\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_save_mode.txt"
            ]
        }
    },
    {
        "name": "test_interactive_help_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'help' command via file input produces help text",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_help_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "Available commands",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_help_cmd.txt",
                "content": "help\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_help_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_mode_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'mode' command via file input shows settings",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_mode_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "precision",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_mode_cmd.txt",
                "content": "mode\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_mode_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_set_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'set' command via file sets option and subsequent expression uses it",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_set_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "FF",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_set_cmd.txt",
                "content": "set base 16\n255\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_set_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_exact_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'exact' command sets approximation to exact mode",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_exact_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_exact_cmd.txt",
                "content": "exact\nsqrt(2)\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_exact_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_variable_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'variable' command creates a variable and it can be used",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_var_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_var_cmd.txt",
                "content": "variable myvar 5\nmyvar*2\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_var_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_function_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'function' command creates a user function and it can be called",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_func_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "50",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_func_cmd.txt",
                "content": "function double 2*\\x\ndouble(25)\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_func_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_delete_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'delete' command removes a variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_delete_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_delete_cmd.txt",
                "content": "variable tmpvar 42\ndelete tmpvar\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_delete_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_info_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'info' command displays information about sin function",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_info_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "sin",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_info_cmd.txt",
                "content": "info sin\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_info_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_find_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'find' command searches for matching items",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_find_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_find_cmd.txt",
                "content": "find meter\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_find_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_convert_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'convert' command converts last result",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_convert_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_convert_cmd.txt",
                "content": "255\nconvert hex\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_convert_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_base_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'base' command sets the output base",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_base_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_base_cmd.txt",
                "content": "base 16\n255\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_base_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_factor_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'factor' command factorizes the last result",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_factor_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_factor_cmd.txt",
                "content": "12\nfactor\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_factor_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_quit_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'quit' command causes graceful exit",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-i",
            "-f",
            "test_quit_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10,
        "setup": {
            "create_file": {
                "path": "test_quit_cmd.txt",
                "content": "quit\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_quit_cmd.txt"
            ]
        }
    },
    {
        "name": "test_interactive_exit_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'exit' command causes graceful exit",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-i",
            "-f",
            "test_exit_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10,
        "setup": {
            "create_file": {
                "path": "test_exit_cmd.txt",
                "content": "exit\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_exit_cmd.txt"
            ]
        }
    },
    {
        "name": "test_answer_variable",
        "category": "FILE_INPUT",
        "description": "Verify ans variable holds the previous result",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "test_ans.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": "20",
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_ans.txt",
                "content": "10\nans*2\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_ans.txt"
            ]
        }
    },
    {
        "name": "test_interactive_rpn_via_file",
        "category": "FILE_INPUT",
        "description": "Verify 'rpn on' command enables RPN mode",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "test_rpn_cmd.txt"
        ],
        "stdin": null,
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "test_rpn_cmd.txt",
                "content": "rpn on\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_rpn_cmd.txt"
            ]
        }
    },
    {
        "name": "test_defs2doc_basic",
        "category": "HAPPY_PATH",
        "description": "Run defs2doc utility to generate documentation files (produces appendixa.xml, appendixb.xml, appendixc.xml)",
        "command": "defs2doc",
        "subcommand": "",
        "args": [],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_examples2doc_missing_readme",
        "category": "INVALID_ARGS",
        "description": "Run examples2doc without README.md present should fail with exit code 1",
        "command": "examples2doc",
        "subcommand": "",
        "args": [],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_examples2doc_with_readme",
        "category": "FILE_INPUT",
        "description": "Run examples2doc with a README.md present to generate examples.xml",
        "command": "examples2doc",
        "subcommand": "",
        "args": [],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "README.md",
                "content": "# Test\n## Examples\n### Basic\n2+2 _4_\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "README.md",
                "examples.xml"
            ]
        }
    }
]'''))

# CLI binary/entry point
CLI_COMMAND = "./src/qalc"

# Working directory for CLI execution
WORKING_DIR = "."

# Default command timeout in seconds
DEFAULT_TIMEOUT = 30

# Response validation mode: when True, validates output against expected
VALIDATE_OUTPUT = any(
    tc.get("actual_stdout") is not None or tc.get("actual_stderr") is not None
    for tc in TEST_CASES
)

# =============================================================================
# Output Validation Utilities
# =============================================================================



def normalize_output(output: str) -> str:
    """Normalize output for comparison (strip whitespace, normalize newlines)."""
    if output is None:
        return ""
    return output.strip().replace("\r\n", "\n")


def matches_pattern(actual: str, pattern: str | None) -> bool:
    """
    Check if actual output matches the expected pattern.

    Pattern matching rules:
    - If pattern is None, always matches (no validation)
    - If pattern starts with 'regex:', use regex matching
    - Otherwise, check if pattern is contained in actual output (case-insensitive)
    """
    if pattern is None:
        return True

    actual_normalized = normalize_output(actual)

    if pattern.startswith("regex:"):
        regex_pattern = pattern[6:]  # Remove 'regex:' prefix
        return bool(re.search(regex_pattern, actual_normalized, re.IGNORECASE | re.MULTILINE))

    # Default: substring match (case-insensitive)
    pattern_normalized = normalize_output(pattern)
    return pattern_normalized.lower() in actual_normalized.lower()


def validate_cli_output(
    actual_stdout: str,
    actual_stderr: str,
    expected_stdout: str | None,
    expected_stderr: str | None,
) -> tuple[bool, list[str]]:
    """
    Validate CLI output against expected patterns.

    Args:
        actual_stdout: Actual stdout from command
        actual_stderr: Actual stderr from command
        expected_stdout: Expected stdout pattern (or None)
        expected_stderr: Expected stderr pattern (or None)

    Returns:
        tuple: (is_valid, list of violations)
    """
    violations: list[str] = []

    if expected_stdout is not None and not matches_pattern(actual_stdout, expected_stdout):
        violations.append(
            f"stdout mismatch: expected pattern '{expected_stdout}' not found in output"
        )

    if expected_stderr is not None and not matches_pattern(actual_stderr, expected_stderr):
        violations.append(
            f"stderr mismatch: expected pattern '{expected_stderr}' not found in output"
        )

    return len(violations) == 0, violations


def format_output_diff(violations: list[str]) -> str:
    """Format output differences for error message."""
    if not violations:
        return "No differences"

    output = []
    for i, diff in enumerate(violations):
        output.append(f"  - {diff}")

    return "\n".join(output)


# =============================================================================
# Output Store (cross-test-case value sharing)
# =============================================================================

# In-memory store for values extracted from command outputs and shared across test cases.
# Test cases with a "store" field extract values from their stdout/stderr and save them here.
# Later test cases reference stored values via "$stored.KEY" placeholders.
_output_store: dict[str, Any] = {}


def extract_by_json_path(data: Any, json_path: str) -> Any:
    """Extract a value from nested data using a dot-separated JSON path.

    Supports dict key access and integer list indexing.
    E.g. "data.users.0.id" -> data["data"]["users"][0]["id"]
    """
    current = data
    for key in json_path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def store_output_values(test_case: dict[str, Any], stdout: str, stderr: str) -> None:
    """Extract values from command output and save them in the output store.

    The test case's "store" field maps placeholder names to extraction rules:
    - "stdout.json.<json_path>": Parse stdout as JSON and extract by path
    - "stderr.json.<json_path>": Parse stderr as JSON and extract by path
    - "stdout.regex.<pattern>": Match regex against stdout, store first capture group
    - "stderr.regex.<pattern>": Match regex against stderr, store first capture group
    - "stdout": Store the full stdout string (stripped)
    - "stderr": Store the full stderr string (stripped)
    """
    store_config = test_case.get("store")
    if not store_config or not isinstance(store_config, dict):
        return

    for placeholder_name, extraction_rule in store_config.items():
        if not isinstance(extraction_rule, str):
            continue

        value: Any = None

        if extraction_rule == "stdout":
            value = stdout.strip()
        elif extraction_rule == "stderr":
            value = stderr.strip()
        elif extraction_rule.startswith("stdout.json."):
            json_path = extraction_rule[len("stdout.json."):]
            try:
                parsed = json.loads(stdout)
                value = extract_by_json_path(parsed, json_path)
            except (json.JSONDecodeError, TypeError):
                print(f"  Warning: stdout is not valid JSON for store rule '{extraction_rule}'")
        elif extraction_rule.startswith("stderr.json."):
            json_path = extraction_rule[len("stderr.json."):]
            try:
                parsed = json.loads(stderr)
                value = extract_by_json_path(parsed, json_path)
            except (json.JSONDecodeError, TypeError):
                print(f"  Warning: stderr is not valid JSON for store rule '{extraction_rule}'")
        elif extraction_rule.startswith("stdout.regex."):
            pattern = extraction_rule[len("stdout.regex."):]
            match = re.search(pattern, stdout)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)
        elif extraction_rule.startswith("stderr.regex."):
            pattern = extraction_rule[len("stderr.regex."):]
            match = re.search(pattern, stderr)
            if match:
                value = match.group(1) if match.lastindex else match.group(0)

        if value is not None:
            _output_store[placeholder_name] = value
            print(f"  Stored: ${placeholder_name} = <{len(str(value))} chars>")
        else:
            print(f"  Warning: store rule '{extraction_rule}' resolved to None for '{placeholder_name}'")


def resolve_stored_placeholders(obj: Any) -> Any:
    """Replace $stored.KEY placeholders with values from the output store.

    Handles three cases:
    1. Exact match: value is "$stored.key" -> replaced with stored value (preserves type)
    2. Embedded match: value is "Bearer $stored.token" -> string interpolation
    3. Recursive: dicts and lists are traversed recursively
    """
    if not _output_store:
        return obj

    if isinstance(obj, str):
        # Exact match - preserves original type (e.g. int, dict) instead of stringifying
        if obj.startswith("$stored."):
            key = obj[len("$stored."):]
            if key in _output_store:
                return _output_store[key]
        # Embedded string interpolation (handles "Bearer $stored.token" and partial matches)
        if "$stored." in obj:
            result = obj
            for key, value in _output_store.items():
                result = result.replace(f"$stored.{key}", str(value))
            return result
        return obj

    if isinstance(obj, dict):
        return {k: resolve_stored_placeholders(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [resolve_stored_placeholders(item) for item in obj]

    return obj


# =============================================================================
# Test Results Collection
# =============================================================================

test_results: list[dict[str, Any]] = []


def record_result(
    name: str,
    command: str,
    subcommand: str | None,
    args: list[str],
    expected_exit_code: int,
    actual_exit_code: int,
    passed: bool,
    duration_ms: float,
    category: str | None = None,
    description: str | None = None,
    error: str | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
    output_match: bool | None = None,
    output_diff: list[str] | None = None,
) -> None:
    """Record a test result for final output."""
    result: dict[str, Any] = {
        "name": name,
        "command": command,
        "subcommand": subcommand,
        "args": args,
        "expected_exit_code": expected_exit_code,
        "actual_exit_code": actual_exit_code,
        "passed": passed,
        "duration_ms": duration_ms,
        "category": category,
        "description": description,
    }
    if error:
        result["error"] = error

    # Track output validation results (for DST contract testing)
    if output_match is not None:
        result["output_match"] = output_match
    if output_diff:
        result["output_diff"] = output_diff

    # Capture outputs for validation
    if stdout:
        if passed:
            result["actual_stdout"] = stdout  # Capture more for passed tests
        else:
            result["stdout"] = stdout

    if stderr:
        if passed:
            result["actual_stderr"] = stderr
        else:
            result["stderr"] = stderr

    test_results.append(result)


# =============================================================================
# Setup and Cleanup Helpers
# =============================================================================


def run_setup(setup_config: dict[str, Any], work_dir: Path) -> bool:
    """Run setup actions before a test."""
    if not setup_config:
        return True

    try:
        # Create file
        if "create_file" in setup_config:
            file_config = setup_config["create_file"]
            file_path = work_dir / file_config["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_config.get("content", ""))
            print(f"Setup: Created file {file_path}")

        # Create directory
        if "create_dir" in setup_config:
            dir_path = work_dir / setup_config["create_dir"]
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Setup: Created directory {dir_path}")

        # Run command
        if "run_command" in setup_config:
            cmd = setup_config["run_command"]
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )
            if result.returncode != 0:
                print(f"Setup command failed: {result.stderr}")
                return False

        return True

    except Exception as e:
        print(f"Setup error: {e}")
        return False


def run_cleanup(cleanup_config: dict[str, Any], work_dir: Path) -> None:
    """Run cleanup actions after a test (best effort)."""
    if not cleanup_config:
        return

    try:
        # Delete files
        if "delete_files" in cleanup_config:
            for file_path in cleanup_config["delete_files"]:
                full_path = work_dir / file_path
                if full_path.exists():
                    full_path.unlink()
                    print(f"Cleanup: Deleted file {full_path}")

        # Delete directories
        if "delete_dirs" in cleanup_config:
            for dir_path in cleanup_config["delete_dirs"]:
                full_path = work_dir / dir_path
                if full_path.exists():
                    shutil.rmtree(full_path)
                    print(f"Cleanup: Deleted directory {full_path}")

        # Run command
        if "run_command" in cleanup_config:
            cmd = cleanup_config["run_command"]
            subprocess.run(
                cmd,
                shell=True,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

    except Exception as e:
        print(f"Cleanup warning: {e}")


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def cli_work_dir() -> Path:
    """Get the CLI working directory."""
    return Path(WORKING_DIR)


@pytest.fixture(scope="session", autouse=True)
def verify_cli_exists() -> None:
    """Verify the CLI command exists before running tests."""
    print(f"\nVerifying CLI command exists: {CLI_COMMAND}...")

    # Check if it's a direct path
    if os.path.isfile(CLI_COMMAND):
        print(f"CLI found at: {CLI_COMMAND}")
        return

    # Check if it's in PATH
    result = shutil.which(CLI_COMMAND)
    if result:
        print(f"CLI found in PATH: {result}")
        return

    # Try common locations
    work_dir = Path(WORKING_DIR)
    common_paths = [
        work_dir / CLI_COMMAND,
        work_dir / "dist" / CLI_COMMAND,
        work_dir / "target" / "release" / CLI_COMMAND,
        work_dir / "bin" / CLI_COMMAND,
    ]

    for path in common_paths:
        if path.exists():
            print(f"CLI found at: {path}")
            return

    pytest.fail(f"CLI command '{CLI_COMMAND}' not found. Please ensure the app is built.")


# =============================================================================
# Test Cases
# =============================================================================


def get_test_ids() -> list[str]:
    """Generate test IDs for parametrization."""
    return [tc.get("name", f"test_{i}") for i, tc in enumerate(TEST_CASES)]


@pytest.mark.parametrize("test_case", TEST_CASES, ids=get_test_ids())
def test_cli_command(test_case: dict[str, Any], cli_work_dir: Path) -> None:
    """Test a single CLI command based on test case configuration."""
    # Extract test case info
    name = test_case.get("name", "unnamed")
    command = CLI_COMMAND
    raw_args = test_case.get("args", [])
    args = (
        [str(arg) for arg in raw_args]
        if isinstance(raw_args, list)
        else ([str(raw_args)] if raw_args is not None else [])
    )
    subcommand = test_case.get("subcommand", "")
    subcommand_parts = (
        [part for part in subcommand.strip().split(" ") if part]
        if isinstance(subcommand, str) and subcommand.strip()
        else []
    )
    execution_args = subcommand_parts + args
    stdin_input = test_case.get("stdin")
    env_vars = test_case.get("env", {})
    expected_exit_code = test_case.get("expected_exit_code", 0)
    expected_stdout = test_case.get("expected_stdout")
    expected_stderr = test_case.get("expected_stderr")
    category = test_case.get("category")
    description = test_case.get("description")
    setup_config = test_case.get("setup")
    cleanup_config = test_case.get("cleanup")
    timeout = test_case.get("timeout_seconds", DEFAULT_TIMEOUT)

    # Expected outputs for DST contract validation (from SRC validation)
    actual_stdout_expected = test_case.get("actual_stdout")
    actual_stderr_expected = test_case.get("actual_stderr")

    try:
        # Run setup if configured
        if setup_config:
            if not run_setup(setup_config, cli_work_dir):
                record_result(
                    name=name,
                    command=command,
                    subcommand=subcommand if isinstance(subcommand, str) and subcommand.strip() else None,
                    args=execution_args,
                    expected_exit_code=expected_exit_code,
                    actual_exit_code=-1,
                    passed=False,
                    duration_ms=0,
                    category=category,
                    description=description,
                    error="Setup failed",
                )
                pytest.fail(f"Setup failed for test '{name}'")

        # Resolve $stored.* placeholders from previous test outputs
        args = resolve_stored_placeholders(args)
        env_vars = resolve_stored_placeholders(env_vars)
        if stdin_input is not None:
            stdin_input = resolve_stored_placeholders(stdin_input)

        # Build full command
        full_cmd = [command] + execution_args

        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars)

        # Execute command
        start_time = time.time()
        try:
            result = subprocess.run(
                full_cmd,
                input=stdin_input,
                cwd=str(cli_work_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration_ms = (time.time() - start_time) * 1000
            actual_exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr

            # Check exit code first
            exit_code_passed = actual_exit_code == expected_exit_code
            error_msg = None if exit_code_passed else (
                f"Expected exit code {expected_exit_code}, got {actual_exit_code}"
            )

            # Store output values for cross-test-case sharing (before any assertions)
            if exit_code_passed:
                store_output_values(test_case, stdout, stderr)

            # Check output patterns
            output_match: bool | None = None
            output_diff: list[str] | None = None

            # For DST validation, compare against captured SRC output
            if actual_stdout_expected is not None or actual_stderr_expected is not None:
                output_match, output_diff = validate_cli_output(
                    stdout,
                    stderr,
                    actual_stdout_expected,
                    actual_stderr_expected,
                )
                if not output_match:
                    error_msg = f"Output contract violation:\n{format_output_diff(output_diff)}"
            # For SRC validation or basic validation, check expected patterns
            elif expected_stdout is not None or expected_stderr is not None:
                output_match, output_diff = validate_cli_output(
                    stdout,
                    stderr,
                    expected_stdout,
                    expected_stderr,
                )
                if not output_match:
                    error_msg = f"Output pattern mismatch:\n{format_output_diff(output_diff)}"

            # Overall pass
            passed = exit_code_passed and (output_match is None or output_match)

            record_result(
                name=name,
                command=command,
                subcommand=subcommand if isinstance(subcommand, str) and subcommand.strip() else None,
                args=execution_args,
                expected_exit_code=expected_exit_code,
                actual_exit_code=actual_exit_code,
                passed=passed,
                duration_ms=duration_ms,
                category=category,
                description=description,
                error=error_msg,
                stdout=stdout,
                stderr=stderr,
                output_match=output_match,
                output_diff=output_diff,
            )

            # pytest assertions
            if not exit_code_passed:
                pytest.fail(
                    f"Test '{name}': Expected exit code {expected_exit_code}, got {actual_exit_code}.\n"
                    f"stdout: {stdout if stdout else 'empty'}\n"
                    f"stderr: {stderr if stderr else 'empty'}"
                )

            if output_match is False:
                pytest.fail(
                    f"Test '{name}': Output validation failed.\n"
                    f"Violations:\n{format_output_diff(output_diff or [])}"
                )

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start_time) * 1000
            record_result(
                name=name,
                command=command,
                subcommand=subcommand if isinstance(subcommand, str) and subcommand.strip() else None,
                args=execution_args,
                expected_exit_code=expected_exit_code,
                actual_exit_code=-1,
                passed=False,
                duration_ms=duration_ms,
                category=category,
                description=description,
                error=f"Command timed out after {timeout}s",
                stdout=e.stdout if hasattr(e, 'stdout') else None,
                stderr=e.stderr if hasattr(e, 'stderr') else None,
            )
            pytest.fail(f"Test '{name}': Command timed out after {timeout}s")

    except Exception as e:
        record_result(
            name=name,
            command=command,
            subcommand=subcommand if isinstance(subcommand, str) and subcommand.strip() else None,
            args=execution_args,
            expected_exit_code=expected_exit_code,
            actual_exit_code=-1,
            passed=False,
            duration_ms=0,
            category=category,
            description=description,
            error=f"Test error: {type(e).__name__}: {e}",
        )
        raise

    finally:
        # Always run cleanup
        if cleanup_config:
            run_cleanup(cleanup_config, cli_work_dir)


# =============================================================================
# Test Results Output
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def output_test_results(request: pytest.FixtureRequest) -> Any:
    """Output test results in JSON format after all tests complete."""
    yield  # Wait for all tests to complete

    # Calculate final results
    passed_count = sum(1 for r in test_results if r["passed"])
    failed_count = len([r for r in test_results if not r["passed"]])
    total_count = len(test_results)
    all_passed = failed_count == 0 and total_count > 0

    failures = [r for r in test_results if not r["passed"]]

    # Count output validation results (for DST contract testing)
    output_validated_count = sum(1 for r in test_results if r.get("output_match") is not None)
    output_match_count = sum(1 for r in test_results if r.get("output_match") is True)

    output = {
        "all_passed": all_passed,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total_count": total_count,
        "results": test_results,
        "failures": failures,
    }

    # Add contract validation summary if any tests had expected outputs
    if output_validated_count > 0:
        output["contract_validation"] = {
            "tests_with_expected_output": output_validated_count,
            "output_matches": output_match_count,
            "output_mismatches": output_validated_count - output_match_count,
        }

    print("\n" + "=" * 60)
    print(f"Results: {passed_count}/{total_count} passed")
    if output_validated_count > 0:
        print(f"Contract validation: {output_match_count}/{output_validated_count} outputs matched")
    print("=" * 60)
    print(json.dumps(output))
    sys.stdout.flush()
