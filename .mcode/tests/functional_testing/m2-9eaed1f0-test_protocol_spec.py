#!/usr/bin/env python3
"""
BE Testing - CLI Contract Validation Tests

Generated pytest script to validate the CLI spec against the running application.
Each command is tested as a parameterized test case using pytest.

This script supports two modes:
1. SRC Validation: Tests commands and captures outputs (no expected_stdout/stderr)
2. DST Contract Validation: Tests commands and validates outputs match expected

Generated at: 2026-03-06T22:07:14.439201+00:00
Project: libqalculate-mig
Milestone: 2
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
        "description": "Verify --help shows usage information",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--help"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Usage:",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_help_short_flag",
        "category": "HELP_OUTPUT",
        "description": "Verify -h shows usage information",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-h"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Usage:",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_output",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version shows version string",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_short_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify -v shows version string",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-v"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_add_integers",
        "category": "HAPPY_PATH",
        "description": "Basic integer addition: 1 + 2 = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1 + 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_add_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language addition: 1 plus 2 = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1 plus 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_subtract_unicode_minus",
        "category": "HAPPY_PATH",
        "description": "Unicode minus sign subtraction: 5\u22122 = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5\u22122"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_subtract_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language subtraction: 5 minus 3 = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 minus 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_double_negation",
        "category": "HAPPY_PATH",
        "description": "Double negation: 5--2 = 7",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5--2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "7",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_triple_negation",
        "category": "HAPPY_PATH",
        "description": "Triple negation: 5---2 = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5---2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_negative_minus",
        "category": "HAPPY_PATH",
        "description": "Negative number minus: -5-2 = -7",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-5-2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-7",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_minus_minus_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language double negation: 5 minus minus 3 = 8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 minus minus 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_minus_negative_natural",
        "category": "HAPPY_PATH",
        "description": "Natural language minus negative: 5 minus - 3 = 8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 minus - 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_multiply_asterisk",
        "category": "HAPPY_PATH",
        "description": "Multiplication with asterisk: 2*3 = 6",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "2*3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_multiply_unicode_times",
        "category": "HAPPY_PATH",
        "description": "Unicode multiplication sign: 3 \u00d7 4 = 12",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3 \u00d7 4"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_multiply_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language multiplication: 4 times 5 = 20",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "4 times 5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "20",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_multiply_unicode_dot",
        "category": "HAPPY_PATH",
        "description": "Unicode middle dot multiplication: 5 \u22c5 6 = 30",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 \u22c5 6"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "30",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_divide_slash",
        "category": "HAPPY_PATH",
        "description": "Division with slash: 6/2 = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "6/2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_divide_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language division: 12 per 3 = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "12 per 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_divide_fraction",
        "category": "HAPPY_PATH",
        "description": "Division producing decimal: 1/2 = 0.5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1/2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.5",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_remainder_percent",
        "category": "HAPPY_PATH",
        "description": "Remainder with percent sign: 6%2 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "6%2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_remainder_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language remainder: 7 rem 2 = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "7 rem 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_remainder_negative",
        "category": "HAPPY_PATH",
        "description": "Negative remainder: -8%3 = -2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-8%3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_modulo_double_percent",
        "category": "HAPPY_PATH",
        "description": "Modulo with double percent: 3 %% 2 = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3 %% 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_modulo_double_percent_negative",
        "category": "HAPPY_PATH",
        "description": "Modulo with negative divisor: 3 %% -2 = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3 %% -2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_modulo_natural_language",
        "category": "HAPPY_PATH",
        "description": "Natural language modulo: 3 mod -2 = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "3 mod -2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_integer_division_double_slash",
        "category": "HAPPY_PATH",
        "description": "Integer division with //: 5//2 = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5//2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_integer_division_backslash",
        "category": "HAPPY_PATH",
        "description": "Integer division with backslash: 5\\2 = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5\\2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_integer_division_natural",
        "category": "HAPPY_PATH",
        "description": "Natural language integer division: 5 div 2 = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 div 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_power_caret",
        "category": "HAPPY_PATH",
        "description": "Exponentiation with caret: 5 ^ 2 = 25",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 ^ 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "25",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_power_double_star",
        "category": "HAPPY_PATH",
        "description": "Exponentiation with **: 5 ** 3 = 125",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 ** 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "125",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_power_right_associative",
        "category": "HAPPY_PATH",
        "description": "Exponentiation is right-associative: 4 ** 3 ** 2 = 4^(3^2) = 262144",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "4 ** 3 ** 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "262144",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_factorial_one",
        "category": "HAPPY_PATH",
        "description": "Factorial of 1: 1! = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1!"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_factorial_five",
        "category": "HAPPY_PATH",
        "description": "Factorial of 5: 5! = 120",
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
        "name": "test_to_bin",
        "category": "HAPPY_PATH",
        "description": "Convert 52 to binary",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52 to bin"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0011 0100",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_bin16",
        "category": "HAPPY_PATH",
        "description": "Convert 52 to 16-bit binary",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52 to bin16"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0000 0000 0011 0100",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_oct",
        "category": "HAPPY_PATH",
        "description": "Convert 52 to octal",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52 to oct"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "064",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_hex",
        "category": "HAPPY_PATH",
        "description": "Convert 52 to hexadecimal",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52 to hex"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0x34",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_hex_input",
        "category": "HAPPY_PATH",
        "description": "Parse hexadecimal input: 0x34 = 52",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0x34"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "52",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_hex_function",
        "category": "HAPPY_PATH",
        "description": "hex() function: hex(34) = 52 (interpret 34 as hex)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "hex(34)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "52",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_shift_and_to_bin",
        "category": "HAPPY_PATH",
        "description": "Bitwise shift and AND with binary output: 523<<2&250 to bin",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "523<<2&250 to bin"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0010 1000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_float",
        "category": "HAPPY_PATH",
        "description": "Convert 52.345 to IEEE 754 float binary",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52.345 to float"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0100 0010 0101 0001 0110 0001 0100 1000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_float_function",
        "category": "HAPPY_PATH",
        "description": "Parse IEEE 754 float binary back to decimal",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "float(01000010010100010110000101001000)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "52.34500122",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_floatError",
        "category": "HAPPY_PATH",
        "description": "IEEE 754 float representation error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "floatError(52.345)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.000001220703125",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_roman",
        "category": "HAPPY_PATH",
        "description": "Convert 1978 to Roman numerals",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1978 to roman"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "MCMLXXVIII",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_base32",
        "category": "HAPPY_PATH",
        "description": "Convert 52 to base 32",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "52 to base 32"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1K",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_sqrt_to_irrational_base",
        "category": "HAPPY_PATH",
        "description": "sqrt(32) to base sqrt(2) = 100000",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sqrt(32) to base sqrt(2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_hex_input_base_set",
        "category": "HAPPY_PATH",
        "description": "Hex exponent notation with input base 16",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "input base 16",
            "5p10+AEp-2*p23"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "364909568",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_to_sexa_unicode",
        "category": "HAPPY_PATH",
        "description": "Convert decimal to sexagesimal with Unicode symbols",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "52.34 to sexa"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "52\u00b020\u203224\u2033",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_not_one",
        "category": "HAPPY_PATH",
        "description": "Bitwise NOT of 1: \u00ac1 = -2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\u00ac1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_not_tilde_zero",
        "category": "HAPPY_PATH",
        "description": "Bitwise NOT of 0: ~0 = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "~0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_not_tilde_neg1",
        "category": "HAPPY_PATH",
        "description": "Bitwise NOT of -1: ~-1 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "~-1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_not_large_negative",
        "category": "HAPPY_PATH",
        "description": "Bitwise NOT of -812: ~ -812 = 811",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "~ -812"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "811",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_zero",
        "category": "HAPPY_PATH",
        "description": "Right shift: 0 >> 0 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0 >> 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_zero_by_one",
        "category": "HAPPY_PATH",
        "description": "Right shift: 0 >> 1 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0 >> 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_18_by_2",
        "category": "HAPPY_PATH",
        "description": "Right shift: 18 >> 2 = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "18 >> 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_identity",
        "category": "HAPPY_PATH",
        "description": "Right shift by 0 is identity: 11 >> 0 = 11",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "11 >> 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "11",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_negative_identity",
        "category": "HAPPY_PATH",
        "description": "Right shift negative by 0: -11 >> 0 = -11",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-11 >> 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-11",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_right_shift_negative",
        "category": "HAPPY_PATH",
        "description": "Right shift negative: -18 >> 1 = -9",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-18 >> 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-9",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_left_shift_zero",
        "category": "HAPPY_PATH",
        "description": "Left shift: 0 << 0 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0 << 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_left_shift_zero_by_one",
        "category": "HAPPY_PATH",
        "description": "Left shift: 0 << 1 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0 << 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_left_shift_identity",
        "category": "HAPPY_PATH",
        "description": "Left shift by 0 is identity: 18 << 0 = 18",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "18 << 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "18",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_left_shift_18_by_1",
        "category": "HAPPY_PATH",
        "description": "Left shift: 18 << 1 = 36",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "18 << 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "36",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_left_shift_negative",
        "category": "HAPPY_PATH",
        "description": "Left shift negative: -18 << 2 = -72",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-18 << 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-72",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_or_unicode",
        "category": "HAPPY_PATH",
        "description": "Bitwise OR with Unicode symbol and binary output",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b1011 0010 \u2228 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1111 0011",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_or_pipe",
        "category": "HAPPY_PATH",
        "description": "Bitwise OR with pipe operator: 0b0101 | 0b1001 to bin4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b0101 | 0b1001 to bin4"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1101",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_and_unicode",
        "category": "HAPPY_PATH",
        "description": "Bitwise AND with Unicode symbol: 0b1011 0010 \u2227 0b0111 0001 to bin8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b1011 0010 \u2227 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0011 0000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_and_ampersand",
        "category": "HAPPY_PATH",
        "description": "Bitwise AND with ampersand: 0b1011 0010 & 0b0111 0001 to bin8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b1011 0010 & 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0011 0000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_xor_keyword",
        "category": "HAPPY_PATH",
        "description": "Bitwise XOR with 'xor' keyword: 0b1011 0010 xor 0b0111 0001 to bin8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b1011 0010 xor 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1100 0011",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_xor_double_caret",
        "category": "HAPPY_PATH",
        "description": "Bitwise XOR with ^^: 0b1011 0010 ^^ 0b0111 0001 to bin8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b1011 0010 ^^ 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1100 0011",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_xor_unicode",
        "category": "HAPPY_PATH",
        "description": "Bitwise XOR with Unicode \u22bb: 0b0101 \u22bb 0b0111 0001 to bin8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b0101 \u22bb 0b0111 0001 to bin8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1100 0011",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_precedence_1",
        "category": "HAPPY_PATH",
        "description": "Bitwise operator precedence: 0b0101 | 0b1001 xor 0b0101 & 0b0111 = 13",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b0101 | 0b1001 xor 0b0101 & 0b0111"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "13",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_bitwise_precedence_2",
        "category": "HAPPY_PATH",
        "description": "Bitwise operator precedence (reversed): 0b0101 & 0b0111 xor 0b1001 | 0b0101 = 13",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0b0101 & 0b0111 xor 0b1001 | 0b0101"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "13",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_zero",
        "category": "HAPPY_PATH",
        "description": "Percentage literal: 0% = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_one",
        "category": "HAPPY_PATH",
        "description": "Percentage literal: 1% = 0.01",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.01",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_small_decimal",
        "category": "HAPPY_PATH",
        "description": "Percentage with small decimal: .000123 % = 0.00000123",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            ".000123 %"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.00000123",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_negative",
        "category": "HAPPY_PATH",
        "description": "Negative percentage: -15% = -0.15",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-15%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-0.15",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_large",
        "category": "HAPPY_PATH",
        "description": "Large percentage: 1234% = 12.34",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1234%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12.34",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_scientific",
        "category": "HAPPY_PATH",
        "description": "Scientific notation percentage: 1e-3% = 0.00001",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1e-3%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.00001",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_add_percents",
        "category": "HAPPY_PATH",
        "description": "Adding two percentages: 10% + 5% = 0.15",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% + 5%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.15",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_percents",
        "category": "HAPPY_PATH",
        "description": "Subtracting percentages: 10%-6% = 0.04",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10%-6%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.04",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_chain",
        "category": "HAPPY_PATH",
        "description": "Chained percentage operations: 123% - 3% + 10% = 1.3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "123% - 3% + 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_equal",
        "category": "HAPPY_PATH",
        "description": "Equal percentages cancel: 10% - 10% = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% - 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_larger",
        "category": "HAPPY_PATH",
        "description": "Subtract larger percentage: 10% - 20% = -0.1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% - 20%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-0.1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_multiply",
        "category": "HAPPY_PATH",
        "description": "Multiply percentages: 10% * 2% = 0.002",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% * 2%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.002",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_divide",
        "category": "HAPPY_PATH",
        "description": "Divide percentages: 10% / 2% = 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% / 2%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_mixed_ops",
        "category": "HAPPY_PATH",
        "description": "Mixed percentage operations: 10%*20%-30%/15% = -1.98",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10%*20%-30%/15%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1.98",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_add_to_number",
        "category": "HAPPY_PATH",
        "description": "Context-sensitive: 100 + 10% = 110 (10% of 100)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 + 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "110",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_add_chain",
        "category": "HAPPY_PATH",
        "description": "Chained percentage on number: 100 + 10% + 10% = 121",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 + 10% + 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "121",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_add_compound",
        "category": "HAPPY_PATH",
        "description": "Compound percentage: 100 + (10 + 10)% = 120",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 + (10 + 10)%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "120",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_from_number",
        "category": "HAPPY_PATH",
        "description": "Subtract percentage from number: 100 - 10% = 90",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 - 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "90",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_chain",
        "category": "HAPPY_PATH",
        "description": "Chained percentage subtraction: 100 - 10% - 10% = 81",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 - 10% - 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "81",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_subtract_compound",
        "category": "HAPPY_PATH",
        "description": "Compound percentage subtraction: 100 - (10-5) % = 95",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 - (10-5) %"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "95",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_before_number_add",
        "category": "HAPPY_PATH",
        "description": "Percentage before number: 10% + 100 = 100.1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% + 100"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100.1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_before_number_subtract",
        "category": "HAPPY_PATH",
        "description": "Percentage before number: 10% - 100 = -99.9",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10% - 100"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-99.9",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_multiply_by_number",
        "category": "HAPPY_PATH",
        "description": "Number times percentage: 100 * 10% = 10",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 * 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_divide_by_number",
        "category": "HAPPY_PATH",
        "description": "Number divided by percentage: 100 / 10% = 1000",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 / 10%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_with_units",
        "category": "HAPPY_PATH",
        "description": "Percentage with units: 10 meters + 20% = 12 m",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10 meters + 20%"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12 m",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_percent_equation_solve",
        "category": "HAPPY_PATH",
        "description": "Solve percentage equation: 10 - x% = 8 => x = 20",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10 - x% = 8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 20",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_complex_power",
        "category": "HAPPY_PATH",
        "description": "Complex exponentiation: (2i - 3)^(3.2i + 3)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(2i - 3)^(3.2i + 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.009212545193 - 0.009517560625i",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_powertower",
        "category": "HAPPY_PATH",
        "description": "Power tower (tetration): powertower(2, 4) = 65536",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "powertower(2, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "65536",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_allroots",
        "category": "HAPPY_PATH",
        "description": "All 7th roots of 4: allroots(4, 7)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "allroots(4, 7)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1.219013654  (0.7600425817 + 0.9530632524i)  (-0.2712560568 + 1.188450437i)  (-1.098293352 + 0.5289102023i)  (-1.098293352 - 0.5289102023i)  (-0.2712560568 - 1.188450437i)  (0.7600425817 - 0.9530632524i)]",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_lambertw_complex_uncertainty",
        "category": "HAPPY_PATH",
        "description": "Lambert W function with complex argument and uncertainty",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "lambertw(5i + 2+/-0.002, -1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.389008\u00b10.000043 - 3.62889\u00b10.00035i",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_uncertainty_power",
        "category": "HAPPY_PATH",
        "description": "Power with uncertainty: (2+/-3)^3.2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(2+/-3)^3.2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "9.18958684\u00b144.11001683",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ln_complex_uncertainty",
        "category": "HAPPY_PATH",
        "description": "Natural log with complex argument and uncertainty",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "ln((5+/-0.003)i - 0+/-0.2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.60944\u00b10.00060 + 1.571\u00b10.040i",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ei_uncertainty",
        "category": "HAPPY_PATH",
        "description": "Exponential integral with uncertainty: Ei(3+/-0.3)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "Ei(3+/-0.3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "9.9\u00b12.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_uncertainty_power_ic2",
        "category": "HAPPY_PATH",
        "description": "Power with uncertainty using interval calculation mode 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "ic 2",
            "(2+/-3)^3.2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "86\u00b187 - 0.29\u00b10.30i",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ln_complex_uncertainty_ic2",
        "category": "HAPPY_PATH",
        "description": "Natural log with complex uncertainty using interval calculation mode 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "ic 2",
            "ln((5+/-0.003)i - 0+/-0.2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.60984\u00b10.00100 + 1.571\u00b10.040i",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ei_uncertainty_ic2",
        "category": "HAPPY_PATH",
        "description": "Exponential integral with uncertainty using interval calculation mode 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "ic 2",
            "Ei(3+/-0.3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10.1\u00b12.1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_empty",
        "category": "HAPPY_PATH",
        "description": "Empty string literal: \"\" = \"\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_single_char_double_quote",
        "category": "HAPPY_PATH",
        "description": "Single char string: \"x\" = 'x'",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"x\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "'x'",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_multi_char",
        "category": "HAPPY_PATH",
        "description": "Multi-char string: \"xx\" = \"xx\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"xx\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"xx\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_word",
        "category": "HAPPY_PATH",
        "description": "String word: \"meters\" = \"meters\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"meters\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"meters\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_single_quote_num",
        "category": "HAPPY_PATH",
        "description": "Single-quoted number string: '12' = \"12\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "'12'"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"12\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_string_double_quote_num",
        "category": "HAPPY_PATH",
        "description": "Double-quoted number string: \"12\" = \"12\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"12\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"12\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_concatenate_strings",
        "category": "HAPPY_PATH",
        "description": "Concatenate strings: concatenate(\"a\", \"bc\", 'defg') = \"abcdefg\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "concatenate(\"a\", \"bc\", 'defg')"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"abcdefg\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_concatenate_empty",
        "category": "HAPPY_PATH",
        "description": "Concatenate with empty strings: concatenate(\"\", \"c\", '', 'd') = \"cd\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "concatenate(\"\", \"c\", '', 'd')"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"cd\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_concatenate_numbers",
        "category": "HAPPY_PATH",
        "description": "Concatenate numbers as strings: concatenate(1,2) = \"12\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "concatenate(1,2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"12\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_concatenate_expression",
        "category": "HAPPY_PATH",
        "description": "Concatenate unevaluated expression: concatenate(1*2, 5) = \"1*25\"",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "concatenate(1*2, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\"1*25\"",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_dec_concatenate",
        "category": "HAPPY_PATH",
        "description": "Evaluate concatenated expression: dec(concatenate(4*2, 5)) = 100",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dec(concatenate(4*2, 5))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_len_empty",
        "category": "HAPPY_PATH",
        "description": "String length of empty string: len(\"\") = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "len(\"\")"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_len_space",
        "category": "HAPPY_PATH",
        "description": "String length of space: len(\" \") = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "len(\" \")"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_len_number",
        "category": "HAPPY_PATH",
        "description": "String length of number: len(5) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "len(5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_len_fraction",
        "category": "HAPPY_PATH",
        "description": "String length of fraction: len(5/6) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "len(5/6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_len_concatenate",
        "category": "HAPPY_PATH",
        "description": "String length of concatenation: len(concatenate(\"a\", \"bc\")) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "len(concatenate(\"a\", \"bc\"))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_unicode_to_char",
        "category": "HAPPY_PATH",
        "description": "Unicode code point to character: char(0xD8) = '\u00d8'",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "char(0xD8)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "'\u00d8'",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_char_to_hex",
        "category": "HAPPY_PATH",
        "description": "Character to Unicode code point in hex: code(\u00d8) to hex = 0xD8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "code(\u00d8) to hex"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0xD8",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_code_string_array",
        "category": "HAPPY_PATH",
        "description": "Character codes of string as array: code(abc) = [97 98 99]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "code(abc)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[97  98  99]",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_hex_to_unicode",
        "category": "HAPPY_PATH",
        "description": "Convert hex code to Unicode character: 0xD8 to unicode = \u00d8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "0xD8 to unicode"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u00d8",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_char_vector",
        "category": "HAPPY_PATH",
        "description": "Character from vector of code points: char([0xD8, 0x61])",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "char([0xD8, 0x61])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "['\u00d8'  'a']",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_emoji_code_hex",
        "category": "HAPPY_PATH",
        "description": "Emoji Unicode code point in hex: code(\ud83d\ude00) to hex = 0x1F600",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "code(\ud83d\ude00) to hex"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0x1F600",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_emoji_utf8_code",
        "category": "HAPPY_PATH",
        "description": "Emoji UTF-8 encoding: code(\ud83c\udf49, utf-8, 0) to hex",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "unicode 1",
            "code(\ud83c\udf49, utf-8, 0) to hex"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0xF09F8D89",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_missing_expression",
        "category": "INVALID_ARGS",
        "description": "Running qalc with no arguments should enter interactive mode or show help (non-interactive context exits with error or starts REPL)",
        "command": "qalc",
        "subcommand": "",
        "args": [],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown option --foobar should fail",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--foobar"
        ],
        "expected_exit_code": 2,
        "expected_stdout": null,
        "expected_stderr": "unknown option",
        "timeout_seconds": 10
    },
    {
        "name": "test_base_missing_value",
        "category": "INVALID_ARGS",
        "description": "Missing value for --base option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--base"
        ],
        "expected_exit_code": 2,
        "expected_stdout": null,
        "expected_stderr": "argument",
        "timeout_seconds": 10
    },
    {
        "name": "test_set_missing_value",
        "category": "INVALID_ARGS",
        "description": "Missing value for --set option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--set"
        ],
        "expected_exit_code": 2,
        "expected_stdout": null,
        "expected_stderr": "argument",
        "timeout_seconds": 10
    },
    {
        "name": "test_file_not_found",
        "category": "INVALID_ARGS",
        "description": "Specifying a non-existent file with --file should fail",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--file",
            "/nonexistent/path/expr.txt"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_zero",
        "category": "BOUNDARY",
        "description": "Evaluate literal zero: 0 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_negative_zero",
        "category": "BOUNDARY",
        "description": "Evaluate negative zero: -0 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_large_number",
        "category": "BOUNDARY",
        "description": "Large number arithmetic",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "999999999999999999 + 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1000000000000000000",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_large_factorial",
        "category": "BOUNDARY",
        "description": "Large factorial: 20!",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "20!"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2432902008176640000",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_division_by_zero",
        "category": "BOUNDARY",
        "description": "Division by zero should not crash",
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
        "name": "test_boundary_deeply_nested_parens",
        "category": "BOUNDARY",
        "description": "Deeply nested parentheses: ((((1+2)))) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "((((1+2))))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_empty_string_expression",
        "category": "BOUNDARY",
        "description": "Empty expression string",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            ""
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_many_operators",
        "category": "BOUNDARY",
        "description": "Long chain of additions: 1+1+1+1+1+1+1+1+1+1 = 10",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1+1+1+1+1+1+1+1+1+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_zero_power_zero",
        "category": "BOUNDARY",
        "description": "0^0 edge case",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0^0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_negative_power",
        "category": "BOUNDARY",
        "description": "Negative exponent: 2^-3 = 0.125",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "2^-3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.125",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_imaginary_unit",
        "category": "BOUNDARY",
        "description": "Imaginary unit: i^2 = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "i^2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_pipe_simple_expression",
        "category": "PIPE_INPUT",
        "description": "Pipe a simple expression to stdin",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "2 + 3",
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_pipe_multiline",
        "category": "PIPE_INPUT",
        "description": "Pipe multiple expressions to stdin",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "1+1\n2+2\n3+3\n",
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_file_input_batch",
        "category": "FILE_INPUT",
        "description": "Execute expressions from a file using --file",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--file",
            "test_input.txt"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10,
        "setup": {
            "create_file": {
                "path": "test_input.txt",
                "content": "1+1\n2*3\n5^2\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "test_input.txt"
            ]
        }
    },
    {
        "name": "test_test_file_pass",
        "category": "FILE_INPUT",
        "description": "Execute a batch test file that should pass",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "passing_test.batch"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10,
        "setup": {
            "create_file": {
                "path": "passing_test.batch",
                "content": "1 + 2\n\t3\n5 * 3\n\t15\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "passing_test.batch"
            ]
        }
    },
    {
        "name": "test_test_file_fail",
        "category": "FILE_INPUT",
        "description": "Execute a batch test file with a wrong expected result should fail",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "failing_test.batch"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10,
        "setup": {
            "create_file": {
                "path": "failing_test.batch",
                "content": "1 + 2\n\t999\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "failing_test.batch"
            ]
        }
    },
    {
        "name": "test_base_hex_output",
        "category": "HAPPY_PATH",
        "description": "Use -b flag to set output base to hex: 255 in hex = 0xFF",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "hex",
            "255"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0xFF",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_base_bin_output",
        "category": "HAPPY_PATH",
        "description": "Use -b flag to set output base to binary: 10 in binary",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "bin",
            "10"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0000 1010",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_base_oct_output",
        "category": "HAPPY_PATH",
        "description": "Use -b flag to set output base to octal: 100 in octal",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-b",
            "oct",
            "100"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0144",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_set_precision",
        "category": "HAPPY_PATH",
        "description": "Set precision via -s flag: 1/3 with precision 20",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "precision 20",
            "1/3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.33333333333333333333",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_sqrt_function",
        "category": "HAPPY_PATH",
        "description": "Square root: sqrt(144) = 12",
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
        "name": "test_cbrt_function",
        "category": "HAPPY_PATH",
        "description": "Cube root: cbrt(27) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cbrt(27)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_exp_function",
        "category": "HAPPY_PATH",
        "description": "Exponential: exp(0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "exp(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ln_function",
        "category": "HAPPY_PATH",
        "description": "Natural logarithm: ln(1) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "ln(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_abs_function",
        "category": "HAPPY_PATH",
        "description": "Absolute value: abs(-42) = 42",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "abs(-42)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "42",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_gcd_function",
        "category": "HAPPY_PATH",
        "description": "Greatest common divisor: gcd(12, 18) = 6",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "gcd(12, 18)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_lcm_function",
        "category": "HAPPY_PATH",
        "description": "Least common multiple: lcm(4, 6) = 12",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "lcm(4, 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_round_function",
        "category": "HAPPY_PATH",
        "description": "Round: round(3.7) = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "round(3.7)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_floor_function",
        "category": "HAPPY_PATH",
        "description": "Floor: floor(3.7) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "floor(3.7)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_ceil_function",
        "category": "HAPPY_PATH",
        "description": "Ceiling: ceil(3.2) = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "ceil(3.2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_trunc_function",
        "category": "HAPPY_PATH",
        "description": "Truncate: trunc(3.9) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "trunc(3.9)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_sign_function",
        "category": "HAPPY_PATH",
        "description": "Sign function: sign(-5) = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sign(-5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_isprime_true",
        "category": "HAPPY_PATH",
        "description": "Primality test: isprime(17) = 1 (true)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "isprime(17)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_isprime_false",
        "category": "HAPPY_PATH",
        "description": "Primality test: isprime(15) = 0 (false)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "isprime(15)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_nextprime",
        "category": "HAPPY_PATH",
        "description": "Next prime: nextprime(10) = 11",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "nextprime(10)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "11",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_totient",
        "category": "HAPPY_PATH",
        "description": "Euler's totient: totient(12) = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "totient(12)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_binomial",
        "category": "HAPPY_PATH",
        "description": "Binomial coefficient: binomial(10, 3) = 120",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "binomial(10, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "120",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_if_function",
        "category": "HAPPY_PATH",
        "description": "Conditional function: if(1 > 0, 42, 0) = 42",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "if(1 > 0, 42, 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "42",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_if_function_false",
        "category": "HAPPY_PATH",
        "description": "Conditional function false branch: if(1 < 0, 42, 99) = 99",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "if(1 < 0, 42, 99)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "99",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_double_factorial",
        "category": "HAPPY_PATH",
        "description": "Double factorial: 7!! = 7*5*3*1 = 105",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "7!!"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "105",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_root_function",
        "category": "HAPPY_PATH",
        "description": "Nth root: root(81, 4) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "root(81, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_mod_function",
        "category": "HAPPY_PATH",
        "description": "Modulo function: mod(17, 5) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "mod(17, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_frac_function",
        "category": "HAPPY_PATH",
        "description": "Fractional part: frac(3.75) = 0.75",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "frac(3.75)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.75",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_int_function",
        "category": "HAPPY_PATH",
        "description": "Integer part: int(3.75) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "int(3.75)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 10
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
