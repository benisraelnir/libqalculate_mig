#!/usr/bin/env python3
"""
BE Testing - CLI Contract Validation Tests

Generated pytest script to validate the CLI spec against the running application.
Each command is tested as a parameterized test case using pytest.

This script supports two modes:
1. SRC Validation: Tests commands and captures outputs (no expected_stdout/stderr)
2. DST Contract Validation: Tests commands and validates outputs match expected

Generated at: 2026-03-06T22:11:39.676477+00:00
Project: libqalculate-mig
Milestone: 1
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
        "name": "test_help_short_flag",
        "category": "HELP_OUTPUT",
        "description": "Verify -h shows usage information and exits with code 0",
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
        "name": "test_help_long_flag",
        "category": "HELP_OUTPUT",
        "description": "Verify --help shows usage information and exits with code 0",
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
        "name": "test_help_single_dash",
        "category": "HELP_OUTPUT",
        "description": "Verify -help (single-dash long form) also shows help",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "usage: qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_options",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes key option descriptions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-b, -base",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_version_option",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes the version option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-v, -version",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_set_option",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes the set option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-s, -set",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_terse_option",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes the terse option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-t, -terse",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_nodefs_option",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes the nodefs option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-n, -nodefs",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_lists_interactive_option",
        "category": "HELP_OUTPUT",
        "description": "Verify help output includes the interactive option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-i, -interactive",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_short_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify -v shows version string and exits with code 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_long_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version shows version string and exits with code 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_single_dash_long",
        "category": "VERSION_OUTPUT",
        "description": "Verify -version (single-dash long form) shows version",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nodefs_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --nodefs flag is accepted and Calculator initializes without loading global definitions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--nodefs",
            "-t",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_nodefs_short_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify -n short flag for nodefs is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-n",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_nounits_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --nounits flag is accepted and does not cause an error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--nounits",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_nofunctions_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --nofunctions flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--nofunctions",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_novariables_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --novariables flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--novariables",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_nocurrencies_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --nocurrencies flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--nocurrencies",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_nodatasets_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --nodatasets flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--nodatasets",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_defaults_flag_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify --defaults flag is accepted and loads default settings",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--defaults",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_terse_flag_short",
        "category": "HAPPY_PATH",
        "description": "Verify -t terse flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_terse_flag_long",
        "category": "HAPPY_PATH",
        "description": "Verify --terse flag is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--terse",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_option_with_value",
        "category": "HAPPY_PATH",
        "description": "Verify -s/--set option with a value is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s",
            "base 10",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_set_option_equals_syntax",
        "category": "HAPPY_PATH",
        "description": "Verify --set=VALUE syntax is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--set",
            "base 16",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_base_option_short",
        "category": "HAPPY_PATH",
        "description": "Verify -b flag with base value is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-b",
            "16",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_base_option_long",
        "category": "HAPPY_PATH",
        "description": "Verify --base flag with base value is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--base",
            "2",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_color_option_no_value",
        "category": "HAPPY_PATH",
        "description": "Verify -c color flag without value defaults to enabling color",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-c",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_color_option_with_value",
        "category": "HAPPY_PATH",
        "description": "Verify --color with explicit value is accepted (value must be inline, e.g. -c2)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-c2",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_time_option_short",
        "category": "HAPPY_PATH",
        "description": "Verify -m time limit option is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-m",
            "5000",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_time_option_long",
        "category": "HAPPY_PATH",
        "description": "Verify --time time limit option is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--time",
            "3000",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_unicode_on_flag",
        "category": "HAPPY_PATH",
        "description": "Verify -u8 enables Unicode signs",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-u8",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_unicode_off_flag",
        "category": "HAPPY_PATH",
        "description": "Verify +u8 disables Unicode signs",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "+u8",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_double_dash_separator",
        "category": "HAPPY_PATH",
        "description": "Verify -- separates options from expression, treating everything after as expression text",
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
        "timeout_seconds": 15
    },
    {
        "name": "test_programming_mode_flag",
        "category": "HAPPY_PATH",
        "description": "Verify -p programming mode flag with base value is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-p",
            "16",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_file_option_short",
        "category": "HAPPY_PATH",
        "description": "Verify -f flag with a file argument is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "/tmp/qalc_test_commands.txt",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_test_commands.txt",
                "content": ""
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_test_commands.txt"
            ]
        }
    },
    {
        "name": "test_file_option_long",
        "category": "HAPPY_PATH",
        "description": "Verify --file flag with a file argument is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--file",
            "/tmp/qalc_test_commands.txt",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_test_commands.txt",
                "content": ""
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_test_commands.txt"
            ]
        }
    },
    {
        "name": "test_test_file_option",
        "category": "HAPPY_PATH",
        "description": "Verify --test-file activates unit-test mode with defaults, terse, and locale-ignore",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "/tmp/qalc_test_batch.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_test_batch.txt",
                "content": ""
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_test_batch.txt"
            ]
        }
    },
    {
        "name": "test_list_flag_no_search",
        "category": "HAPPY_PATH",
        "description": "Verify -l/--list flag without a search term lists user-defined items",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-l"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_list_flag_with_search",
        "category": "HAPPY_PATH",
        "description": "Verify --list with a search term filters results",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list",
            "meter"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_list_functions_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --list-functions lists available functions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-functions"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_list_units_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --list-units lists available units",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-units"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_list_variables_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --list-variables lists available variables",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-variables"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_list_prefixes_flag",
        "category": "HAPPY_PATH",
        "description": "Verify --list-prefixes lists available prefixes",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--list-prefixes"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_multiple_flags_combined",
        "category": "HAPPY_PATH",
        "description": "Verify multiple flags can be combined (nodefs + terse + version)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-n",
            "-t",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_multiple_options_semicolon",
        "category": "HAPPY_PATH",
        "description": "Verify -s supports semicolon-separated multiple options",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s",
            "base 16;precision 20",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_expression_argument_accepted",
        "category": "HAPPY_PATH",
        "description": "Verify a positional expression argument is accepted without error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_expression_after_double_dash",
        "category": "HAPPY_PATH",
        "description": "Verify expression after -- is treated as expression even if it looks like a flag",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--",
            "-5+3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_invalid_unknown_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown option should produce a warning message",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--unknown-option",
            "--",
            "1+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Unrecognized option",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_invalid_single_dash_unknown",
        "category": "INVALID_OPTIONS",
        "description": "Unknown single-dash option before -- should produce a warning",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-z",
            "--",
            "1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Unrecognized option",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_set_option_no_value",
        "category": "INVALID_ARGS",
        "description": "Using -s without a value should produce an error message about missing option/value",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "No option and value specified",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_file_option_no_file",
        "category": "INVALID_ARGS",
        "description": "Using -f without a filename should produce an error about missing file",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "No file specified",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_boundary_empty_expression",
        "category": "BOUNDARY",
        "description": "Empty expression (no args, no file, non-interactive forced) should handle gracefully",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--",
            ""
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_boundary_very_long_expression",
        "category": "BOUNDARY",
        "description": "Very long expression string should be accepted without crashing",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_base_zero",
        "category": "BOUNDARY",
        "description": "Setting base to 0 should be handled without crash",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-b",
            "0",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_boundary_base_negative",
        "category": "BOUNDARY",
        "description": "Setting base to a negative number should be handled",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-b",
            "-1",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_boundary_time_zero",
        "category": "BOUNDARY",
        "description": "Setting time limit to 0 should be handled (no timeout)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-m",
            "0",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_time_negative",
        "category": "BOUNDARY",
        "description": "Setting time limit to negative value should clamp to 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-m",
            "-100",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_color_zero",
        "category": "BOUNDARY",
        "description": "Setting color to 0 should disable color output (value must be inline, e.g. -c0)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-c0",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_file_input_with_commands",
        "category": "FILE_INPUT",
        "description": "Verify -f reads and processes commands from a file",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "/tmp/qalc_file_test.txt",
            "-t"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_file_test.txt",
                "content": "1+1\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_file_test.txt"
            ]
        }
    },
    {
        "name": "test_file_input_nonexistent",
        "category": "FILE_INPUT",
        "description": "Verify that specifying a non-existent file is handled gracefully",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "/tmp/qalc_nonexistent_file_12345.txt",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_file_input_empty_file",
        "category": "FILE_INPUT",
        "description": "Verify that an empty command file is handled gracefully",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "/tmp/qalc_empty_test.txt",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_empty_test.txt",
                "content": ""
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_empty_test.txt"
            ]
        }
    },
    {
        "name": "test_test_file_with_batch",
        "category": "FILE_INPUT",
        "description": "Verify --test-file processes batch test expressions in unit-test mode",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "/tmp/qalc_batch_test.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "/tmp/qalc_batch_test.txt",
                "content": "1+1\n\t2\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "/tmp/qalc_batch_test.txt"
            ]
        }
    },
    {
        "name": "test_pipe_expression_via_stdin",
        "category": "PIPE_INPUT",
        "description": "Verify the CLI can accept expression input via stdin pipe",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-n"
        ],
        "stdin": "1+1\n",
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_pipe_empty_stdin",
        "category": "PIPE_INPUT",
        "description": "Verify empty stdin input is handled gracefully",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-n"
        ],
        "stdin": "",
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_env_qalculate_user_dir",
        "category": "HAPPY_PATH",
        "description": "Verify QALCULATE_USER_DIR environment variable is respected for user data path",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-v"
        ],
        "env": {
            "QALCULATE_USER_DIR": "/tmp/qalc_test_user_dir"
        },
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_env_xdg_config_home",
        "category": "HAPPY_PATH",
        "description": "Verify XDG_CONFIG_HOME environment variable is respected",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-v"
        ],
        "env": {
            "XDG_CONFIG_HOME": "/tmp/qalc_test_xdg_config"
        },
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_set_ignore_locale",
        "category": "HAPPY_PATH",
        "description": "Verify -s 'ignore locale' option is accepted and affects locale handling",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s",
            "ignore locale 1",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_set_language",
        "category": "HAPPY_PATH",
        "description": "Verify -s 'language' option is accepted",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-s",
            "language en",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 15
    },
    {
        "name": "test_exrates_flag",
        "category": "HAPPY_PATH",
        "description": "Verify -e/--exrates flag is accepted for exchange rate fetching",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-e",
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_help_exits_immediately",
        "category": "HELP_OUTPUT",
        "description": "Verify --help exits immediately without initializing Calculator or loading definitions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "options",
        "expected_stderr": null,
        "timeout_seconds": 5
    },
    {
        "name": "test_version_exits_immediately",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version exits immediately without loading definitions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.9.0",
        "expected_stderr": null,
        "timeout_seconds": 5
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
