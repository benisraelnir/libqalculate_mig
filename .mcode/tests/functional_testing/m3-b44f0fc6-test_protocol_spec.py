#!/usr/bin/env python3
"""
BE Testing - CLI Contract Validation Tests

Generated pytest script to validate the CLI spec against the running application.
Each command is tested as a parameterized test case using pytest.

This script supports two modes:
1. SRC Validation: Tests commands and captures outputs (no expected_stdout/stderr)
2. DST Contract Validation: Tests commands and validates outputs match expected

Generated at: 2026-03-06T22:49:56.254618+00:00
Project: libqalculate-mig
Milestone: 3
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
        "name": "test_help_flag",
        "category": "HELP_OUTPUT",
        "description": "Verify --help displays usage information and exits successfully",
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
        "description": "Verify -h displays usage information and exits successfully",
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
        "name": "test_version_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version shows version number and exits",
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
        "name": "test_version_short_flag",
        "category": "VERSION_OUTPUT",
        "description": "Verify -v shows version number and exits",
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
        "name": "test_unit_volume_dm3_to_liters",
        "category": "HAPPY_PATH",
        "description": "Convert 5 cubic decimeters to liters",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 dm3 to L"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5 L",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_volume_25dm3_to_liters",
        "category": "HAPPY_PATH",
        "description": "Convert 25 dm^3 to liters",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "25 dm^3 to L"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "25 L",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_speed_miles_to_kmh",
        "category": "HAPPY_PATH",
        "description": "Convert miles/hours to km/h",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "20 miles / 2h to km/h"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "16.09344 km/h",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_meters_to_feet_mixed",
        "category": "HAPPY_PATH",
        "description": "Convert meters to feet with mixed-unit formatting (feet + inches)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1.74 m to ft"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5 ft + 8.503937008 in",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_meters_to_feet_no_mixed",
        "category": "HAPPY_PATH",
        "description": "Convert meters to feet without mixed-unit formatting (prepend - disables mixed)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1.74 m to -ft"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.708661417 ft",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_force_to_horsepower",
        "category": "HAPPY_PATH",
        "description": "Convert force * speed to horsepower",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "100 lbf * 60 mph to hp"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "15.99999752 hp",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_ohm_ampere_to_volt",
        "category": "HAPPY_PATH",
        "description": "Multiply ohms by amperes to get volts (automatic unit simplification)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "50 \u03a9 * 2 A"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100 V",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_to_base_units",
        "category": "HAPPY_PATH",
        "description": "Convert volts to base SI units",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "50 \u03a9 * 2 A to base"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100 kg\u00b7m\u00b2/(A\u00b7s\u00b3)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_newton_pascal_area",
        "category": "HAPPY_PATH",
        "description": "Divide newtons by pascals to get area",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10 N / 5 Pa"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2 m\u00b2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_newton_pascal_parenthesized",
        "category": "HAPPY_PATH",
        "description": "Parenthesized newton/pascal division",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(10 N)/(5 Pa)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2 m\u00b2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_reciprocal_speed",
        "category": "HAPPY_PATH",
        "description": "Convert m/s to reciprocal s/m",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 m/s to s/m"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.2 s/m",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_data_binary_prefix",
        "category": "HAPPY_PATH",
        "description": "Convert data rate * time to binary-prefixed bytes",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "500 megabit/s * 2 h to b?byte"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "419.0951586 GiB",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_unit_implicit_meters_to_feet",
        "category": "HAPPY_PATH",
        "description": "Implicit meter unit when converting bare number to feet",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1.74 to ft"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5 ft + 8.503937008 in",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sin_pi_half",
        "category": "HAPPY_PATH",
        "description": "Sine of pi/2 in radians equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "sin(pi/2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_cos_pi",
        "category": "HAPPY_PATH",
        "description": "Cosine of pi in radians equals -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "cos(pi)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u22121",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_tan_pi_quarter",
        "category": "HAPPY_PATH",
        "description": "Tangent of pi/4 in radians equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "tan(pi/4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sin_degrees",
        "category": "HAPPY_PATH",
        "description": "Sine of 90 degrees equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle degrees",
            "sin(90)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_cos_degrees",
        "category": "HAPPY_PATH",
        "description": "Cosine of 180 degrees equals -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle degrees",
            "cos(180)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u22121",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sin_gradians",
        "category": "HAPPY_PATH",
        "description": "Sine of 100 gradians equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle gradians",
            "sin(100)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_asin",
        "category": "HAPPY_PATH",
        "description": "Arc sine of 1 in radians equals pi/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "asin(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.570796327",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_acos_zero",
        "category": "HAPPY_PATH",
        "description": "Arc cosine of 0 in radians equals pi/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "acos(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.570796327",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_atan_one",
        "category": "HAPPY_PATH",
        "description": "Arc tangent of 1 in radians equals pi/4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "atan(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.7853981634",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_atan2",
        "category": "HAPPY_PATH",
        "description": "Two-argument arc tangent atan2(1, 1) equals pi/4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "atan2(1; 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.7853981634",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sinh",
        "category": "HAPPY_PATH",
        "description": "Hyperbolic sine of 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sinh(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.175201194",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_cosh",
        "category": "HAPPY_PATH",
        "description": "Hyperbolic cosine of 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cosh(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.543080635",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_tanh",
        "category": "HAPPY_PATH",
        "description": "Hyperbolic tangent of 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "tanh(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.7615941560",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_asinh",
        "category": "HAPPY_PATH",
        "description": "Inverse hyperbolic sine of 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "asinh(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.8813735870",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_acosh",
        "category": "HAPPY_PATH",
        "description": "Inverse hyperbolic cosine of 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "acosh(2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.316957897",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_atanh",
        "category": "HAPPY_PATH",
        "description": "Inverse hyperbolic tangent of 0.5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "atanh(0.5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.5493061443",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sinc",
        "category": "HAPPY_PATH",
        "description": "Sinc function sinc(1) = sin(1)/1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "sinc(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.8414709848",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_trig_sin_cos_identity",
        "category": "HAPPY_PATH",
        "description": "Verify sin(pi/2) - cos(pi) = 2 (from man page example)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "sin(pi/2) - cos(pi)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_time_addition",
        "category": "HAPPY_PATH",
        "description": "Add two time values and format as time",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10:31 + 8:30 to time"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "19:01",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_hours_minutes_addition",
        "category": "HAPPY_PATH",
        "description": "Add hours and minutes with unit syntax and format as time",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "10h 31min + 8h 30min to time"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "19:01",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_timezone_conversion",
        "category": "HAPPY_PATH",
        "description": "Convert CET datetime to UTC+8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"2020-07-10T07:50CET\" to utc+8"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2020-07-10T14:50:00+08:00",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_add_days_string",
        "category": "HAPPY_PATH",
        "description": "Add 523 days to a date using string + days syntax",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"2020-05-20\" + 523d"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2021-10-25",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_add_days_function",
        "category": "HAPPY_PATH",
        "description": "Add 523 days to a date using addDays function",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "addDays(2020-05-20; 523)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2021-10-25",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_subtraction_positive",
        "category": "HAPPY_PATH",
        "description": "Subtract two dates yielding positive day count",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"2020-11-05\" - \"2020-10-05\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "31 d",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_subtraction_negative",
        "category": "HAPPY_PATH",
        "description": "Subtract two dates yielding negative day count",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "\"2020-10-05\" - \"2020-10-15\""
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u221210 d",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_timestamp",
        "category": "HAPPY_PATH",
        "description": "Convert date to Unix timestamp",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "timestamp(2020-05-20T00:00:00Z)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1589932800",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_stamptodate",
        "category": "HAPPY_PATH",
        "description": "Convert Unix timestamp back to date",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "stamptodate(1589932800) to utc"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2020-05-20T00:00:00Z",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_lunarphase",
        "category": "HAPPY_PATH",
        "description": "Calculate lunar phase for a specific date",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "lunarphase(2022-02-11T00:00Z)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.32288434",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_date_nextlunarphase",
        "category": "HAPPY_PATH",
        "description": "Find next full moon (phase 0.5) after a date",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "nextlunarphase(0.5, 2022-02-11T00:00Z) to utc"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2022-02-16T16:56:27Z",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_mean_inline",
        "category": "HAPPY_PATH",
        "description": "Calculate arithmetic mean of inline values",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "mean(5; 6; 4; 2; 3; 7)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4.5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_stdev",
        "category": "HAPPY_PATH",
        "description": "Calculate standard deviation of inline values",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "stdev(5; 6; 4; 2; 3; 7)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.870828693",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_quartile_method8",
        "category": "HAPPY_PATH",
        "description": "Calculate first quartile using method 8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "quartile((5; 6; 4; 2; 3; 7); 1; 8)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2.916666667",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_percentile_method8",
        "category": "HAPPY_PATH",
        "description": "Calculate 25th percentile using method 8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "percentile([5 6 4 2 3 7]; 25; 8)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2.916666667",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_normdist",
        "category": "HAPPY_PATH",
        "description": "Normal distribution PDF at x=7, mean=0, stdev=5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "normdist(7; 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.05399096651",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_quadraticfit",
        "category": "HAPPY_PATH",
        "description": "Quadratic curve fitting on a data vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "quadraticfit([5 3 4 5 6 7 13 24])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.7797619048x\u00b2 \u2212 4.720238095x + 9.732142857",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_cubicfit",
        "category": "HAPPY_PATH",
        "description": "Cubic curve fitting on a data vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cubicfit([5 3 4 5 6 7 13 24])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.1489898990x\u00b3 \u2212 1.231601732x\u00b2 + 2.952741703x + 2.357142857",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_fdist_pdf",
        "category": "HAPPY_PATH",
        "description": "F-distribution PDF mode (4th arg=0)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "fdist(5, 2, 3, 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.02558260445",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_fdist_cdf",
        "category": "HAPPY_PATH",
        "description": "F-distribution CDF mode (4th arg=1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "fdist(5, 2, 3, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.8891420474",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_normdistinv",
        "category": "HAPPY_PATH",
        "description": "Inverse normal distribution: P=0.2, mean=5, stdev=2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "normdistinv(0.2, 5, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.316757533",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_chisqdistinv",
        "category": "HAPPY_PATH",
        "description": "Inverse chi-squared distribution: P=0.9, df=3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "chisqdistinv(0.9, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6.251388631",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_mode",
        "category": "HAPPY_PATH",
        "description": "Find mode of a vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "mode([1 3 7 5 1 1 1 3])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_median",
        "category": "HAPPY_PATH",
        "description": "Find median of a vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "median([1 3 7 5 1 1 1 3])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_stats_csv_mean",
        "category": "HAPPY_PATH",
        "description": "Load CSV file and compute mean of vector data",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "mean(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6.530919283",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_stdev",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and compute standard deviation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "stdev(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "23.44646004",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_total",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and compute total (sum)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "total(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "653.0919283",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_min",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and find minimum",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "min(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u221243.38345286",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_max",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and find maximum",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "max(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "54.40816396",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_range",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and compute range",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "range(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "97.79161682",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_median",
        "category": "HAPPY_PATH",
        "description": "Load CSV data and compute median",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "median(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8.084203925",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_number",
        "category": "HAPPY_PATH",
        "description": "Count elements in loaded CSV vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "number(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "100",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_stats_csv_iqr",
        "category": "HAPPY_PATH",
        "description": "Interquartile range of loaded CSV data",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "stats_setup.batch",
            "iqr(libqalculate_tests_vector)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "33.42899060",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "stats_setup.batch",
                "content": "libqalculate_tests_vector=load(tests/vectordata.csv)"
            }
        },
        "cleanup": {
            "delete_files": [
                "stats_setup.batch"
            ]
        }
    },
    {
        "name": "test_geo_circle_area",
        "category": "HAPPY_PATH",
        "description": "Area of circle with radius 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "circle(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "28.27433388",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_circumference",
        "category": "HAPPY_PATH",
        "description": "Circumference of circle with radius 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "circumference(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "18.84955592",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cone_volume",
        "category": "HAPPY_PATH",
        "description": "Volume of cone with radius 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cone(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "37.69911184",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cone_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of cone with radius 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cone_sa(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "75.39822369",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cube_volume",
        "category": "HAPPY_PATH",
        "description": "Volume of cube with side 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cube(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "27",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cube_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of cube with side 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cube_sa(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "54",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cylinder_volume",
        "category": "HAPPY_PATH",
        "description": "Volume of cylinder with radius 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cylinder(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "113.0973355",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_cylinder_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of cylinder with radius 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cylinder_sa(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "131.9468915",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_parallelogram",
        "category": "HAPPY_PATH",
        "description": "Area of parallelogram with base 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "parallelogram(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_parallelogram_perimeter",
        "category": "HAPPY_PATH",
        "description": "Perimeter of parallelogram with sides 3 and 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "parallelogram_perimeter(3,4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "14",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_rectprism_volume",
        "category": "HAPPY_PATH",
        "description": "Volume of rectangular prism 3x4x5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rectprism(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "60",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_rectprism_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of rectangular prism 3x4x5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rectprism_sa(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "94",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_triangleprism",
        "category": "HAPPY_PATH",
        "description": "Volume of triangular prism with base 3, height 4, length 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "triangleprism(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "30",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_tetrahedron",
        "category": "HAPPY_PATH",
        "description": "Volume of regular tetrahedron with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "tetrahedron(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.181980515",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_tetrahedron_height",
        "category": "HAPPY_PATH",
        "description": "Height of regular tetrahedron with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "tetrahedron_height(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2.449489743",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_tetrahedron_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of regular tetrahedron with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "tetrahedron_sa(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "15.58845727",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_sqpyramid",
        "category": "HAPPY_PATH",
        "description": "Volume of square pyramid with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sqpyramid(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6.363961031",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_sqpyramid_height",
        "category": "HAPPY_PATH",
        "description": "Height of square pyramid with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sqpyramid_height(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2.121320344",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_sqpyramid_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of square pyramid with edge 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sqpyramid_sa(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "24.58845727",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_pyramid",
        "category": "HAPPY_PATH",
        "description": "Volume of pyramid with base 3x4 and height 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "pyramid(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "20",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_rect",
        "category": "HAPPY_PATH",
        "description": "Area of rectangle 3x4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rect(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_rect_perimeter",
        "category": "HAPPY_PATH",
        "description": "Perimeter of rectangle 3x4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rect_perimeter(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "14",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_sphere_volume",
        "category": "HAPPY_PATH",
        "description": "Volume of sphere with radius 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sphere(4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "268.0825731",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_sphere_surface_area",
        "category": "HAPPY_PATH",
        "description": "Surface area of sphere with radius 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sphere_sa(4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "201.0619298",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_square_area",
        "category": "HAPPY_PATH",
        "description": "Area of square with side 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "square(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "9",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_square_perimeter",
        "category": "HAPPY_PATH",
        "description": "Perimeter of square with side 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "square_perimeter(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_trapezoid",
        "category": "HAPPY_PATH",
        "description": "Area of trapezoid with parallel sides 3,4 and height 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "trapezoid(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "17.5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_triangle_area",
        "category": "HAPPY_PATH",
        "description": "Area of triangle with base 3 and height 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "triangle(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_triangle_perimeter",
        "category": "HAPPY_PATH",
        "description": "Perimeter of triangle with sides 3, 4, 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "triangle_perimeter(3, 4, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_geo_hypot",
        "category": "HAPPY_PATH",
        "description": "Hypotenuse of right triangle with legs 3, 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "hypot(3, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_gamma_integer",
        "category": "HAPPY_PATH",
        "description": "Gamma function at integer argument: gamma(5) = 4! = 24",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "gamma(5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "24",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_gamma_half",
        "category": "HAPPY_PATH",
        "description": "Gamma function at half-integer: gamma(0.5) = sqrt(pi)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "gamma(0.5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.772453851",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_beta",
        "category": "HAPPY_PATH",
        "description": "Beta function B(2, 3)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "beta(2, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.08333333333",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_erf",
        "category": "HAPPY_PATH",
        "description": "Error function erf(1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "erf(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.8427007929",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_erfc",
        "category": "HAPPY_PATH",
        "description": "Complementary error function erfc(1) = 1 - erf(1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "erfc(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.1572992071",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_zeta_2",
        "category": "HAPPY_PATH",
        "description": "Riemann zeta function zeta(2) = pi^2/6",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "zeta(2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.644934067",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_heaviside_positive",
        "category": "HAPPY_PATH",
        "description": "Heaviside step function at positive value",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "heaviside(5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_heaviside_negative",
        "category": "HAPPY_PATH",
        "description": "Heaviside step function at negative value",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "heaviside(-3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_heaviside_zero",
        "category": "HAPPY_PATH",
        "description": "Heaviside step function at zero (half-maximum convention, value 0.5)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "heaviside(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_li",
        "category": "HAPPY_PATH",
        "description": "Logarithmic integral li(2)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "li(2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.045163780",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_Ei",
        "category": "HAPPY_PATH",
        "description": "Exponential integral Ei(1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "Ei(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.895117816",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_Si",
        "category": "HAPPY_PATH",
        "description": "Sine integral Si(1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "Si(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.9460830704",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_special_besselj",
        "category": "HAPPY_PATH",
        "description": "Bessel function of first kind J_0(1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "besselj(0, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.7651976866",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_var_assign_simple",
        "category": "HAPPY_PATH",
        "description": "Assign a simple value to a variable using :=",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "alpha := 5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_var_assign_expression",
        "category": "HAPPY_PATH",
        "description": "Assign an expression result to a variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "beta := 2+1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_var_vector_assign",
        "category": "HAPPY_PATH",
        "description": "Assign a vector to a variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "beta:=[1,2,3]"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_var_assign_and_use",
        "category": "FILE_INPUT",
        "description": "Assign a variable in a batch file and use it in a subsequent expression",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "var_test.batch",
            "alpha + beta"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "var_test.batch",
                "content": "alpha := 5\nbeta := 3"
            }
        },
        "cleanup": {
            "delete_files": [
                "var_test.batch"
            ]
        }
    },
    {
        "name": "test_var_reassign_incremental",
        "category": "FILE_INPUT",
        "description": "Reassign variable using its own value and verify final result",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "var_incr.batch",
            "alpha"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "11",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "var_incr.batch",
                "content": "alpha := 5\nbeta := 3\nalpha:= alpha + beta\nalpha:= alpha + beta"
            }
        },
        "cleanup": {
            "delete_files": [
                "var_incr.batch"
            ]
        }
    },
    {
        "name": "test_var_delete_command",
        "category": "FILE_INPUT",
        "description": "Delete a user-defined variable via batch file",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "var_del.batch",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "var_del.batch",
                "content": "testvar := 42\ndelete testvar"
            }
        },
        "cleanup": {
            "delete_files": [
                "var_del.batch"
            ]
        }
    },
    {
        "name": "test_var_vector_multiply",
        "category": "FILE_INPUT",
        "description": "Assign vector variable and perform element-wise multiplication",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-f",
            "vec_test.batch",
            "beta*2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[2  4  6]",
        "expected_stderr": null,
        "timeout_seconds": 30,
        "setup": {
            "create_file": {
                "path": "vec_test.batch",
                "content": "beta:=[1,2,3]"
            }
        },
        "cleanup": {
            "delete_files": [
                "vec_test.batch"
            ]
        }
    },
    {
        "name": "test_angle_setting_radians",
        "category": "HAPPY_PATH",
        "description": "Verify --set angle radians affects trig function input interpretation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle radians",
            "sin(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.8414709848",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_angle_setting_degrees",
        "category": "HAPPY_PATH",
        "description": "Verify --set angle degrees affects trig function input interpretation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle degrees",
            "sin(30)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_angle_setting_gradians",
        "category": "HAPPY_PATH",
        "description": "Verify --set angle gradians affects trig function input interpretation",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "angle gradians",
            "sin(200)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pipe_simple_expression",
        "category": "PIPE_INPUT",
        "description": "Evaluate expression piped via stdin",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "circle(3)",
        "expected_exit_code": 0,
        "expected_stdout": "28.27433388",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pipe_unit_conversion",
        "category": "PIPE_INPUT",
        "description": "Pipe a unit conversion expression via stdin",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "1000 g to kg",
        "expected_exit_code": 0,
        "expected_stdout": "1 kg",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pipe_multiple_expressions",
        "category": "PIPE_INPUT",
        "description": "Pipe multiple expressions via stdin (one per line)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "mean(1;2;3)\ncircle(5)",
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_invalid_unknown_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown option is treated as an expression (qalc does not reject unknown flags)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "--nonexistent-option"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_set_missing_value",
        "category": "INVALID_OPTIONS",
        "description": "The --set option with missing value prints a warning but exits 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "",
            "2+2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "No option and value specified",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_base_non_numeric",
        "category": "INVALID_OPTIONS",
        "description": "Invalid base value prints warning but still evaluates expression and exits 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-b",
            "abc",
            "-t",
            "42"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "Illegal base",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_file_not_found",
        "category": "INVALID_ARGS",
        "description": "Non-existent file for --file option should produce error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-f",
            "nonexistent_file_12345.batch"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_csv_not_found",
        "category": "INVALID_ARGS",
        "description": "Loading a non-existent CSV file should produce error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "load(nonexistent_file_12345.csv)"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_function_missing_args",
        "category": "INVALID_ARGS",
        "description": "Calling function without required arguments should produce error or warning",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cone()"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_unit_conversion_incompatible",
        "category": "INVALID_ARGS",
        "description": "Converting between incompatible units should produce error/warning",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "5 kg to m"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_trig_domain",
        "category": "INVALID_ARGS",
        "description": "Arc sine of value outside [-1,1] domain should handle gracefully",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "asin(2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_trig_zero",
        "category": "BOUNDARY",
        "description": "Trigonometric function at zero",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sin(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_cos_zero",
        "category": "BOUNDARY",
        "description": "Cosine at zero equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cos(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_sinh_zero",
        "category": "BOUNDARY",
        "description": "Hyperbolic sine at zero equals 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sinh(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_cosh_zero",
        "category": "BOUNDARY",
        "description": "Hyperbolic cosine at zero equals 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cosh(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_unit_zero_conversion",
        "category": "BOUNDARY",
        "description": "Convert zero quantity between units",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "0 m to ft"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0 ft",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_mean_single_value",
        "category": "BOUNDARY",
        "description": "Mean of a single value should be that value",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "mean(42)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "42",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_erf_zero",
        "category": "BOUNDARY",
        "description": "Error function at zero equals 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "erf(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_gamma_one",
        "category": "BOUNDARY",
        "description": "Gamma function at 1 equals 1 (0! = 1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "gamma(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_circle_zero_radius",
        "category": "BOUNDARY",
        "description": "Area of circle with zero radius is 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "circle(0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_hypot_zero",
        "category": "BOUNDARY",
        "description": "Hypotenuse with both legs zero is 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "hypot(0, 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_timestamp_epoch",
        "category": "BOUNDARY",
        "description": "Unix timestamp of epoch should be 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "timestamp(1970-01-01T00:00:00Z)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_dirac_nonzero",
        "category": "BOUNDARY",
        "description": "Dirac delta function at nonzero equals 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dirac(5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_large_unit_value",
        "category": "BOUNDARY",
        "description": "Large number unit conversion should not overflow",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "1e6 m to km"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1000 km",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_negative_unit_value",
        "category": "BOUNDARY",
        "description": "Negative values should convert correctly between units",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-1 m to cm"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "\u2212100 cm",
        "expected_stderr": null,
        "timeout_seconds": 30
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
