#!/usr/bin/env python3
"""
BE Testing - CLI Contract Validation Tests

Generated pytest script to validate the CLI spec against the running application.
Each command is tested as a parameterized test case using pytest.

This script supports two modes:
1. SRC Validation: Tests commands and captures outputs (no expected_stdout/stderr)
2. DST Contract Validation: Tests commands and validates outputs match expected

Generated at: 2026-03-06T22:40:18.529912+00:00
Project: libqalculate-mig
Milestone: 4
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
        "expected_stdout": "usage: qalc",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_version_output",
        "category": "VERSION_OUTPUT",
        "description": "Verify --version shows version",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--version"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.0.0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_invalid_option",
        "category": "INVALID_OPTIONS",
        "description": "Unknown option should produce error",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--unknown-flag"
        ],
        "expected_exit_code": 2,
        "expected_stdout": null,
        "expected_stderr": "Unrecognized option",
        "timeout_seconds": 10
    },
    {
        "name": "test_set_option_missing_value",
        "category": "INVALID_ARGS",
        "description": "Missing value for --set option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--set"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": "No option and value specified",
        "timeout_seconds": 10
    },
    {
        "name": "test_file_option_missing_file",
        "category": "INVALID_ARGS",
        "description": "Missing file path for --file option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--file"
        ],
        "expected_exit_code": 1,
        "expected_stdout": null,
        "expected_stderr": "No file specified",
        "timeout_seconds": 10
    },
    {
        "name": "test_diff_basic_polynomial",
        "category": "HAPPY_PATH",
        "description": "Differentiate a basic polynomial: diff(6x^2) = 12x",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "diff(6x^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "12x",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_diff_complex_expression",
        "category": "HAPPY_PATH",
        "description": "Differentiate a complex expression with sinh, sqrt, and multiple terms",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "diff(sinh(x^2)/(5x) + 3xy/sqrt(x))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.4 * cosh(x^2) + (3y) / (2 * sqrt(x)) - sinh(x^2) / (5x^2)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_integrate_indefinite_polynomial",
        "category": "HAPPY_PATH",
        "description": "Indefinite integral of polynomial: integrate(6x^2) = 2x^3 + C",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "integrate(6x^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2x^3 + C",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_integrate_definite_polynomial",
        "category": "HAPPY_PATH",
        "description": "Definite integral of polynomial: integrate(6x^2; 1; 5) = 248",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "integrate(6x^2; 1; 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "248",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_integrate_indefinite_complex",
        "category": "HAPPY_PATH",
        "description": "Indefinite integral with sinh and sqrt terms",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "integrate(sinh(x^2)/(5x) + 3xy/sqrt(x))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2x * sqrt(x) * y + 0.1 * Shi(x^2) + C",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_integrate_definite_complex",
        "category": "HAPPY_PATH",
        "description": "Definite integral with sinh and sqrt terms from 1 to 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "integrate(sinh(x^2)/(5x) + 3xy/sqrt(x); 1; 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3.656854249y + 0.8760076036",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_integrate_definite_special_functions",
        "category": "HAPPY_PATH",
        "description": "Definite integral with Ei, exponential, and trigonometric special functions",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "integrate(Ei(x) + 3^x - sin(ln(x)), 1, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8.434289610",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_romberg_numerical_integration",
        "category": "HAPPY_PATH",
        "description": "Romberg numerical integration: romberg(5x + ln(x), 1, 5)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "romberg(5x + ln(x), 1, 5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "64.04718956",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_fresnels",
        "category": "HAPPY_PATH",
        "description": "Fresnel S function: fresnels(5)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "fresnels(5)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.4991913819",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_igamma",
        "category": "HAPPY_PATH",
        "description": "Incomplete gamma function: gammainc(53, 5.2)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "gammainc(53, 5.2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.02201E34",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_betainc_complex",
        "category": "HAPPY_PATH",
        "description": "Incomplete beta function with complex argument",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "betainc(5i - 2, 32, 3.2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-9.431063439E27 - 5.083225623E27i",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_linear",
        "category": "HAPPY_PATH",
        "description": "Solve a linear equation: x + 3 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x + 3 = 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = -3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_quadratic",
        "category": "HAPPY_PATH",
        "description": "Solve a quadratic equation: -x^2 + 3x = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "-x^2 + 3x = 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = (sqrt(5) + 3) / 2 or x = 3/2 - sqrt(5) / 2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_cubic_factored",
        "category": "HAPPY_PATH",
        "description": "Solve a cubic equation: x^3-5x^2-4x+20=0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x^3-5x^2-4x+20=0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 5 or x = 2 or x = -2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_cubic_rearranged",
        "category": "HAPPY_PATH",
        "description": "Solve cubic with terms on both sides: 2x^3 + 5x -5x^2 + 21 = 9x + x^3 + 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "2x^3 + 5x -5x^2 + 21 = 9x + x^3 + 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 5 or x = 2 or x = -2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_cubic_with_implicit_mult",
        "category": "HAPPY_PATH",
        "description": "Solve cubic with implicit multiplication in input",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x*(2x^2 + 5 -5x) + 21 = 9x + x^3 +1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 5 or x = 2 or x = -2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_exponential",
        "category": "HAPPY_PATH",
        "description": "Solve exponential equation: 5^x = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "5^x = 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = ln(3) / ln(5)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_cubic_exact",
        "category": "HAPPY_PATH",
        "description": "Solve cubic with exact radical solution",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x^3 + x^2 + x = 5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 2 / (3 * cbrt(3 * sqrt(561) - 71)) - 1/3 - cbrt(3 * sqrt(561) - 71) / 3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_quartic_repeated_root",
        "category": "HAPPY_PATH",
        "description": "Solve quartic with all equal roots: x^4 + 20x^3 + 150x^2 + 500x + 625 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x^4 + 20x^3 + 150x^2 + 500x + 625 = 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = -5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_fractional_exponent",
        "category": "HAPPY_PATH",
        "description": "Solve equation with fractional exponents: x^(1/3) + x^(2/3) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x^(1/3) + x^(2/3) = 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 2 * sqrt(13) - 5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_logarithmic",
        "category": "HAPPY_PATH",
        "description": "Solve equation with logarithm: ln(x) + x = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "ln(x) + x = 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = lambertw(e^3)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_lambert_w",
        "category": "HAPPY_PATH",
        "description": "Solve equation requiring Lambert W: 2^(3x) + 4x = 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "2^(3x) + 4x = 5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 5/4 - lambertw(6 * 8^(1/4) * ln(2)) / (3 * ln(2))",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_self_power",
        "category": "HAPPY_PATH",
        "description": "Solve x^(-3x) = 2 (two Lambert W branches)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "x^(-3x) = 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = e^lambertw(-ln(2) / 3) or x = e^lambertw(-ln(2) / 3, -1)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_trig_simple",
        "category": "HAPPY_PATH",
        "description": "Solve simple trig equation: 1/3 * sin(3x) - 1/3 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "1/3 * sin(3x) - 1/3 = 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = (2/3) * pi * n + pi / 6",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_trig_two_solutions",
        "category": "HAPPY_PATH",
        "description": "Solve trig equation with two periodic solutions: 2/3 * sin(3x) - 1/3 = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "2/3 * sin(3x) - 1/3 = 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = (2/3) * pi * n + (5/18) * pi or x = (2/3) * pi * n + pi / 18",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_sin_plus_cos",
        "category": "HAPPY_PATH",
        "description": "Solve sin(x) + cos(x) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sin(x) + cos(x) = 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 2 pi * n or x = 2 pi * n + pi / 2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_sin_eq_1_plus_cos",
        "category": "HAPPY_PATH",
        "description": "Solve sin(x) = 1 + cos(x)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sin(x) = 1 + cos(x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 2 pi * n + pi or x = 2 pi * n + pi / 2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_trig_cos_with_phase",
        "category": "HAPPY_PATH",
        "description": "Solve sqrt(2) * cos(3x + pi/6) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sqrt(2) * cos(3x + pi/6) = 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = (2/3) * pi * n + pi / 36 or x = (2/3) * pi * n - (5/36) * pi",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_trig_sin_scaled",
        "category": "HAPPY_PATH",
        "description": "Solve 2 * sin(3x/4) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "2 * sin(3x/4) = 1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = (8/3) * pi * n + (10/9) * pi or x = (8/3) * pi * n + (2/9) * pi",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_tan_with_phase",
        "category": "HAPPY_PATH",
        "description": "Solve tan(x/4 + pi/3) = sqrt(3)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "tan(x/4 + pi/3) = sqrt(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 4 pi * n",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_sin_squared_eq_cubed",
        "category": "HAPPY_PATH",
        "description": "Solve sin(x)^2 = sin(x)^3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sin(x)^2 = sin(x)^3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = pi * n or x = 2 pi * n + pi / 2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_sin_eq_sin_half",
        "category": "HAPPY_PATH",
        "description": "Solve sin(x) = sin(x/2)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sin(x) = sin(x/2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = 2 pi * n or x = 4 pi * n + (2/3) * pi or x = 4 pi * n - (2/3) * pi",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_sin4x_plus_cos2x",
        "category": "HAPPY_PATH",
        "description": "Solve sin(4x) + cos(2x) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "sin(4x) + cos(2x) = 0"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x = pi * n + (7/12) * pi or x = pi * n - pi / 12 or x = (pi * n) / 2 - pi / 4",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_newtonsolve_ei",
        "category": "HAPPY_PATH",
        "description": "Newton-Raphson solve: Ei(x) = 3 starting at 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation try exact",
            "newtonsolve(Ei(x) = 3, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.397510842",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_secantsolve_ei",
        "category": "HAPPY_PATH",
        "description": "Secant method solve: Ei(x) = 3 with x0=1, x1=4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation try exact",
            "secantsolve(Ei(x) = 3, 1, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.397510842",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_newtonsolve_ei_complex",
        "category": "HAPPY_PATH",
        "description": "Newton-Raphson solve with complex result: Ei(x) = 3i",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation try exact",
            "newtonsolve(Ei(x) = 3i, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1.160849461 + 1.034283360i",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_numerical_polynomial_7",
        "category": "HAPPY_PATH",
        "description": "Numerical solve of degree-7 polynomial",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation try exact",
            "-s",
            "unicode 1",
            "x^7 - x^5 + 3x^2 + 5x = 3"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0.4706753153",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_solve_numerical_self_power",
        "category": "HAPPY_PATH",
        "description": "Numerical solve: x^(5x) = 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation try exact",
            "-s",
            "unicode 1",
            "x^(5x) = 5"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1.284730245",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_constant_term",
        "category": "HAPPY_PATH",
        "description": "Extract constant coefficient: coeff(3x + 4, 0) = 4",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3x + 4, 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_linear_term",
        "category": "HAPPY_PATH",
        "description": "Extract linear coefficient: coeff(3y + 4, 1) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3y + 4, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_missing_power",
        "category": "HAPPY_PATH",
        "description": "Extract coefficient of missing power: coeff(3a + 4, 2) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3a + 4, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_cubic_term",
        "category": "HAPPY_PATH",
        "description": "Extract cubic coefficient from expanded polynomial",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(4x*(2x^2 + 5 -5x), 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_quadratic_combined",
        "category": "HAPPY_PATH",
        "description": "Extract quadratic coefficient from combined terms: coeff(x^3-7x^2-4x-5x^2, 2) = -12",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(x^3-7x^2-4x-5x^2, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-12",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_zero_constant",
        "category": "HAPPY_PATH",
        "description": "Constant term cancels to zero: coeff(1+x^3-4x-5x^2-1, 0) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(1+x^3-4x-5x^2-1, 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_explicit_variable",
        "category": "HAPPY_PATH",
        "description": "Extract coefficient with explicit variable: coeff(3x + 4, 1, x) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3x + 4, 1, x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Coefficient for absent variable: coeff(3x + 4, 1, y) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3x + 4, 1, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_coeff_multivariate",
        "category": "HAPPY_PATH",
        "description": "Coefficient in multivariate polynomial: coeff(3x + 2y + 4, 1, y) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "coeff(3x + 2y + 4, 1, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pcontent_simple",
        "category": "HAPPY_PATH",
        "description": "Polynomial content: pcontent(3x + 6) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "pcontent(3x + 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pcontent_cubic",
        "category": "HAPPY_PATH",
        "description": "Polynomial content of cubic: pcontent(2x^3-4x^2-6x-8x^2) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "pcontent(2x^3-4x^2-6x-8x^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pcontent_different_variable",
        "category": "HAPPY_PATH",
        "description": "Content with different variable: pcontent(2y^3-3y^2-6y-8y^2) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "pcontent(2y^3-3y^2-6y-8y^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_pcontent_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Content with respect to non-present variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "pcontent(2x^3-3x^2-6x-8x^2, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2x^3 - 11x^2 - 6x",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_lcoeff_linear",
        "category": "HAPPY_PATH",
        "description": "Leading coefficient of linear: lcoeff(6+ 3x) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "lcoeff(6+ 3x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_lcoeff_combined_quadratic",
        "category": "HAPPY_PATH",
        "description": "Leading coefficient with combined terms: lcoeff(6 -5x^2 + 3x^2) = -2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "lcoeff(6 -5x^2 + 3x^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_lcoeff_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Leading coefficient when poly is constant in given variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "lcoeff(6 -5x^2 + 3x^2, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6 - 2x^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_lcoeff_multivariate",
        "category": "HAPPY_PATH",
        "description": "Leading coefficient in y: lcoeff(6 -5x^2 + 3x^2 + 2y, y) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "lcoeff(6 -5x^2 + 3x^2 + 2y, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_ldegree_linear",
        "category": "HAPPY_PATH",
        "description": "Lowest degree: ldegree(3x) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "ldegree(3x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_ldegree_cancelled_constant",
        "category": "HAPPY_PATH",
        "description": "Lowest degree when constant cancels: ldegree(6 -5x^2 - 6) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "ldegree(6 -5x^2 - 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_ldegree_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Lowest degree for non-present variable: ldegree(-5x^2, y) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "ldegree(-5x^2, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_ldegree_multivariate",
        "category": "HAPPY_PATH",
        "description": "Lowest degree in y: ldegree(3yx^2 + 2y, y) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "ldegree(3yx^2 + 2y, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_degree_linear",
        "category": "HAPPY_PATH",
        "description": "Degree of linear polynomial: degree(3x + 6) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "degree(3x + 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_degree_cubic",
        "category": "HAPPY_PATH",
        "description": "Degree of cubic: degree(2x^3-4x^2-6x-8x^2) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "degree(2x^3-4x^2-6x-8x^2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_degree_cancelled_leading",
        "category": "HAPPY_PATH",
        "description": "Degree when leading term cancels: degree(2x^3-3x^2-6x-2x^3) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "degree(2x^3-3x^2-6x-2x^3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_degree_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Degree in absent variable: degree(2x^3-3x^2-6x-2x^3, y) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "degree(2x^3-3x^2-6x-2x^3, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_primpart_simple",
        "category": "HAPPY_PATH",
        "description": "Primitive part: primpart(3x + 6) = x + 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "primpart(3x + 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "x + 2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_primpart_cubic",
        "category": "HAPPY_PATH",
        "description": "Primitive part of cubic: primpart(-12x^3 + 30x - 20)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "primpart(-12x^3 + 30x - 20)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6x^3 - 15x + 10",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_primpart_multivariate",
        "category": "HAPPY_PATH",
        "description": "Primitive part in y variable: primpart(2xy + 8y + 16, y)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "primpart(2xy + 8y + 16, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "(xy) / 2 + 2y + 4",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_tcoeff_linear",
        "category": "HAPPY_PATH",
        "description": "Trailing coefficient: tcoeff(6+ 3x) = 6",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "tcoeff(6+ 3x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_tcoeff_combined",
        "category": "HAPPY_PATH",
        "description": "Trailing coefficient with combined terms: tcoeff(-5x^2 + 3x - x) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "tcoeff(-5x^2 + 3x - x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_tcoeff_wrong_variable",
        "category": "HAPPY_PATH",
        "description": "Trailing coefficient in absent variable",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "tcoeff(6x -5x^2 + 3x^2, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6x - 2x^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_tcoeff_multivariate",
        "category": "HAPPY_PATH",
        "description": "Trailing coefficient in y",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "tcoeff(6 -5x^2 + 3x^2 + 2y, y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6 - 2x^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_punit_negative",
        "category": "HAPPY_PATH",
        "description": "Polynomial unit: punit(-3x) = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "punit(-3x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_punit_negative_leading",
        "category": "HAPPY_PATH",
        "description": "Polynomial unit with negative leading: punit(1-3x) = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "punit(1-3x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_punit_positive",
        "category": "HAPPY_PATH",
        "description": "Polynomial unit: punit(3x-1) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "punit(3x-1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_polynomial_at_point",
        "category": "HAPPY_PATH",
        "description": "Simple polynomial limit: limit(x^2-4, 2) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(x^2-4,2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_rational_at_zero",
        "category": "HAPPY_PATH",
        "description": "Rational function limit at 0: limit((x^3-4x)/(2x^2+3x),0) = -4/3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^3-4x)/(2x^2+3x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-4/3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_infinity_result",
        "category": "HAPPY_PATH",
        "description": "Limit yielding negative infinity: limit(x^3/(x+1)^2,-1) = -infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(x^3/(x+1)^2,-1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_cancellation",
        "category": "HAPPY_PATH",
        "description": "Limit with cancellation: limit((x+1)^2(x-1)/(x^3+1),-1) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x+1)^2(x-1)/(x^3+1),-1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_positive_infinity_result",
        "category": "HAPPY_PATH",
        "description": "Limit yielding +infinity: limit((x^2+2x+3)/(x-1)^2,1) = +infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^2+2x+3)/(x-1)^2,1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "+infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_subtraction_of_fractions",
        "category": "HAPPY_PATH",
        "description": "Limit of difference of fractions: limit(1/(1-x)-3/(1-x^3),1) = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(1/(1-x)-3/(1-x^3),1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_high_degree_cancellation",
        "category": "HAPPY_PATH",
        "description": "Limit with high degree cancellation: limit((3x^4-4x^3+1)/(x-1)^2,1) = 6",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((3x^4-4x^3+1)/(x-1)^2,1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "6",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_at_infinity_rational",
        "category": "HAPPY_PATH",
        "description": "Limit at infinity of rational function: limit((x^2-1)/(2x^2+1),infinity) = 1/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^2-1)/(2x^2+1),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_at_neg_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit at negative infinity: limit((x^3+x^2-4)/(2x^3+x+11),-infinity) = 1/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^3+x^2-4)/(2x^3+x+11),-infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_lower_degree_numerator",
        "category": "HAPPY_PATH",
        "description": "Limit zero at infinity when numerator has lower degree",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((3x^2+2x-1)/(x^3-x+2),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_higher_degree_numerator",
        "category": "HAPPY_PATH",
        "description": "Limit +infinity when numerator has higher degree",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x(x-1)(x-2))/(x^2+6x-9),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "+infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sqrt_ratio_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit of sqrt ratio at infinity: limit((sqrt(x^2+9))/(x+3),infinity) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((sqrt(x^2+9))/(x+3),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_cubed_rational_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit of cubed rational at infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((x^2+x-1)/(2x^2-x+1))^3,infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/8",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_power_100_ratio_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit of 100th power ratio at infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((x-1)^100*(6x+1)^200)/(3x+5)^300,infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3117982410208",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sqrt_difference_at_zero",
        "category": "HAPPY_PATH",
        "description": "Limit with sqrt: limit((sqrt(1+2x)-1)/(3x),0) = 1/3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((sqrt(1+2x)-1)/(3x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sqrt_difference_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit of sqrt difference at infinity: limit(sqrt(x^2+x)-x,infinity) = 1/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(sqrt(x^2+x)-x,infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_cbrt_difference_at_zero",
        "category": "HAPPY_PATH",
        "description": "Limit with cube root: limit((cbrt(1+x)-cbrt(1-x))/(x),0) = 2/3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((cbrt(1+x)-cbrt(1-x))/(x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2/3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_fractional_exponent",
        "category": "HAPPY_PATH",
        "description": "Limit with fractional exponents: limit((x^(2/3)-1)/(x^(3/5)-1),1) = 10/9",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^(2/3)-1)/(x^(3/5)-1),1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "10/9",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_exponential_form_1_plus_1_over_x",
        "category": "HAPPY_PATH",
        "description": "Exponential limit: limit((1+1/x)^(3x),infinity) = e^3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((1+1/x)^(3x),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "e^3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_exponential_form_1_over_x_squared",
        "category": "HAPPY_PATH",
        "description": "Exponential limit with x^2: limit((1+1/x^2)^(3x),infinity) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((1+1/x^2)^(3x),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_1_minus_fraction_power_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((1-1/3x)^x,infinity) = 1 / cbrt(e)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((1-1/3x)^x,infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1 / cbrt(e)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_ratio_power_x",
        "category": "HAPPY_PATH",
        "description": "Limit of ratio to the power x: limit(((x-1)/(x+1))^x,infinity) = 1 / e^2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((x-1)/(x+1))^x,infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1 / e^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_1_plus_2x_power_1_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((1+2x)^(1/x),0) = e^2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((1+2x)^(1/x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "e^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_quadratic_ratio_power_x",
        "category": "HAPPY_PATH",
        "description": "Limit quadratic over quadratic to the power x",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((x^2+2x+2)/(x^2+3))^(x),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "e^2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sin_over_x",
        "category": "HAPPY_PATH",
        "description": "Classic sin(x)/x limit: limit(sin(10x)/(10x),0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(sin(10x)/(10x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sin_ratio",
        "category": "HAPPY_PATH",
        "description": "Limit of sin(3x)/(2x): limit(sin(3x)/(2x),0) = 3/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(sin(3x)/(2x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_tan_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit of tan(8x)/x: limit(tan(8x)/(x),0) = 8",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(tan(8x)/(x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "8",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_sin_sin_ratio",
        "category": "HAPPY_PATH",
        "description": "Limit of sin(3x)/sin(5x): limit(sin(3x)/sin(5x),0) = 3/5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(sin(3x)/sin(5x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3/5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_1_minus_cos_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((1-cos(x))/(x),0) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((1-cos(x))/(x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_x_sin_pi_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(x*sin(pi/x),infinity) = pi",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(x*sin(pi/x),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "pi",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_tan_minus_sin_over_x3",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((tan(x)-sin(x))/(x^3),0) = 1/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((tan(x)-sin(x))/(x^3),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_asin_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(asin(x)/(x),0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(asin(x)/(x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_exponential_at_zero",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((3^x-1)/(6^x-1),0) = ln(3) / ln(6)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((3^x-1)/(6^x-1),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "ln(3) / ln(6)",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_ln_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(ln(1+x)/(x),0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(ln(1+x)/(x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_ln_at_e",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((ln(x)-1)/(x-e),e) = 1 / e",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((ln(x)-1)/(x-e),e)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1 / e",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_x_ln_difference_infinity",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(x*(ln(x+3)-ln(x)),infinity) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(x*(ln(x+3)-ln(x)),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_lhopital_exp_sin",
        "category": "HAPPY_PATH",
        "description": "L'Hopital limit: limit((sin(x))/(e^x-1),0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((sin(x))/(e^x-1),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_atan_asin_ratio",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(atan(3x)/asin(2x),0) = 3/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(atan(3x)/asin(2x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_cos_power_1_over_x",
        "category": "HAPPY_PATH",
        "description": "Limit: limit(cos(x)^(1/x),0) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(cos(x)^(1/x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_x_minus_sin_over_exp",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((x-sin(x))/(e^x-e^(-x)-2x),0) = 1/2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x-sin(x))/(e^x-e^(-x)-2x),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1/2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_limit_x_cubed_over_x_minus_atan",
        "category": "HAPPY_PATH",
        "description": "Limit: limit((x^3)/(x-atan(x)),0) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((x^3)/(x-atan(x)),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_adj_2x2",
        "category": "HAPPY_PATH",
        "description": "Adjugate of 2x2 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "adj([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[5  -2; -4  1]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_adj_3x3",
        "category": "HAPPY_PATH",
        "description": "Adjugate of 3x3 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "adj([1, 2, 3; 4, 5, 6; 1, 0, 9])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[45  -18  -3; -30  6  6; -5  2  -3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_cofactor_2x2",
        "category": "HAPPY_PATH",
        "description": "Cofactor of 2x2 matrix at (1,1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cofactor([1 2; 4 5], 1, 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_cofactor_3x3",
        "category": "HAPPY_PATH",
        "description": "Cofactor of 3x3 matrix at (1,2)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cofactor([1 2 3; 4 5 6; 1 0 9], 1, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-30",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_det_1x1",
        "category": "HAPPY_PATH",
        "description": "Determinant of 1x1 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "det([[1]])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_det_2x2",
        "category": "HAPPY_PATH",
        "description": "Determinant of 2x2 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "det([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_det_3x3",
        "category": "HAPPY_PATH",
        "description": "Determinant of 3x3 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "det([1 2 3; 4 5 6; 1 0 9])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-30",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_det_4x4",
        "category": "HAPPY_PATH",
        "description": "Determinant of 4x4 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "det([3 4 7 9; 5 4 -1 4; 8 7 8 5; 4 3 0 9])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-412",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_dot_product_2d",
        "category": "HAPPY_PATH",
        "description": "Dot product of 2D vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dot((1; 2); (3, 4))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "11",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_dot_product_3d",
        "category": "HAPPY_PATH",
        "description": "Dot product of 3D vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dot((1; 2; 3); (4; 5; 6))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "32",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_dot_product_operator",
        "category": "HAPPY_PATH",
        "description": "Dot product using . operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(1; 2; 3).(4; 5; 6)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "32",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_cross_product",
        "category": "HAPPY_PATH",
        "description": "Cross product of 3D vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "cross((1; 2; 3); (4; 5; 6))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[-3  6  -3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_multiplication",
        "category": "HAPPY_PATH",
        "description": "Matrix multiplication",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "((1; 2; 3); (4; 5; 6)) * ((7; 8); (9; 10); (11; 12))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[58  64; 139  154]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_inverse_2x2",
        "category": "HAPPY_PATH",
        "description": "Inverse of 2x2 matrix using ^-1 operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "((1; 2); (3; 4))^-1"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[-2  1; 1.5  -0.5]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_inverse_function",
        "category": "HAPPY_PATH",
        "description": "Inverse of matrix using inverse() function",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "inverse([1 2; 3 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[-5  2; 3  -1]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_rank_1",
        "category": "HAPPY_PATH",
        "description": "Rank of rank-1 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rk([1 2 3; 3 6 9])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_rank_2",
        "category": "HAPPY_PATH",
        "description": "Rank of rank-2 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rk([1 2 3; 0 2 2; 1 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_rank_identity",
        "category": "HAPPY_PATH",
        "description": "Rank of identity matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rk(identity(3))"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_rref",
        "category": "HAPPY_PATH",
        "description": "Reduced row echelon form",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rref([1 3 1 9; 1 1 -1 1; 3 11 5 35])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  0  -2  -3; 0  1  1  4; 0  0  0  0]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_transpose",
        "category": "HAPPY_PATH",
        "description": "Matrix transpose",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "transpose([1 2; 3 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  3; 2  4]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_transpose_operator",
        "category": "HAPPY_PATH",
        "description": "Matrix transpose using .' operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "[1 2 3; 4 5 6].'"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  4; 2  5; 3  6]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_permanent_1x1",
        "category": "HAPPY_PATH",
        "description": "Permanent of 1x1 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "permanent([1])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_permanent_2x2",
        "category": "HAPPY_PATH",
        "description": "Permanent of 2x2 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "permanent([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "13",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_permanent_3x3",
        "category": "HAPPY_PATH",
        "description": "Permanent of 3x3 matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "permanent([1 2 3; 4 5 6; 1 0 9])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "144",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_norm_single",
        "category": "HAPPY_PATH",
        "description": "Norm of single-element vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "norm([2])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_norm_2d",
        "category": "HAPPY_PATH",
        "description": "Norm of 2D vector (3,4) = 5",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "norm([3, 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_norm_3d",
        "category": "HAPPY_PATH",
        "description": "Norm of 3D vector (2,3,6) = 7",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "norm([2, 3, 6])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "7",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_magnitude_scalar",
        "category": "HAPPY_PATH",
        "description": "Magnitude of scalar: magnitude(-2) = 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "magnitude(-2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_magnitude_vector",
        "category": "HAPPY_PATH",
        "description": "Magnitude of vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "magnitude([-2, 3, 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "5.385164807",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_identity_scalar",
        "category": "HAPPY_PATH",
        "description": "Identity matrix from size: identity(1) = 1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "identity(1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_identity_3x3",
        "category": "HAPPY_PATH",
        "description": "3x3 identity matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "identity(3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  0  0; 0  1  0; 0  0  1]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_identity_from_matrix",
        "category": "HAPPY_PATH",
        "description": "Identity matrix matching dimensions of given matrix",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "identity([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  0; 0  1]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_vector_creation",
        "category": "HAPPY_PATH",
        "description": "Create vector from values",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "vector(1, 2, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_vector_empty",
        "category": "HAPPY_PATH",
        "description": "Create empty vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "vector()"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix_creation",
        "category": "HAPPY_PATH",
        "description": "Create 3x3 matrix from values",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "matrix(3, 3, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  3; 4  5  6; 7  8  9]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_matrix2vector",
        "category": "HAPPY_PATH",
        "description": "Flatten matrix to vector",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "matrix2vector([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  4  5]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_horzcat",
        "category": "HAPPY_PATH",
        "description": "Horizontal concatenation of vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "horzcat([1], [2 3], [4 5 6 7])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  3  4  5  6  7]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_vertcat",
        "category": "HAPPY_PATH",
        "description": "Vertical concatenation of row vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "vertcat([1 2], [3 4], [5 6])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2; 3  4; 5  6]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_rows",
        "category": "HAPPY_PATH",
        "description": "Count matrix rows",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rows([1 2; 3 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_columns",
        "category": "HAPPY_PATH",
        "description": "Count matrix columns",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "columns([1 2; 4 5])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "2",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_dimension",
        "category": "HAPPY_PATH",
        "description": "Vector dimension",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dimension([1 2 3 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_elements",
        "category": "HAPPY_PATH",
        "description": "Count matrix elements",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "elements([1 2; 3 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_element_access_row",
        "category": "HAPPY_PATH",
        "description": "Access matrix row: element([1 2; 3 4], 1)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "element([1 2; 3 4], 1)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_element_access_cell",
        "category": "HAPPY_PATH",
        "description": "Access matrix element: element([1 2 3; 4 5 6; 1 0 9], 1, 3) = 3",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "element([1 2 3; 4 5 6; 1 0 9], 1, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "3",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_row_access",
        "category": "HAPPY_PATH",
        "description": "Access matrix row: row([1 2; 3 4], 2) = [3  4]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "row([1 2; 3 4], 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[3  4]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_column_access",
        "category": "HAPPY_PATH",
        "description": "Access matrix column: column([1 2; 3 4], 2) = [2  4]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "column([1 2; 3 4], 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[2  4]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_part_submatrix",
        "category": "HAPPY_PATH",
        "description": "Extract submatrix: part([1 2 3; 4 5 6; 7 8 9; 10 11 12], 1, 2, 4, 3)",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "part([1 2 3; 4 5 6; 7 8 9; 10 11 12], 1, 2, 4, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[2  3; 5  6; 8  9; 11  12]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_hadamard_product",
        "category": "HAPPY_PATH",
        "description": "Hadamard (element-wise) product of matrices",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "hadamard([1 2 3; 4 5 6]; [7 8 9; 10 11 12])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[7  16  27; 40  55  72]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_sort_ascending",
        "category": "HAPPY_PATH",
        "description": "Sort vector ascending",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sort([5, 2, 0, 1, 3, -4, 0])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[-4  0  0  1  2  3  5]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_sort_descending",
        "category": "HAPPY_PATH",
        "description": "Sort vector descending",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "sort([5, 2, 0, 1, 3, -4, 0], 0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[5  3  2  1  0  0  -4]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_rank_vector",
        "category": "HAPPY_PATH",
        "description": "Rank ordering of vector elements",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "rank([6, 7, 1, 4])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[3  4  1  2]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_combine_vectors",
        "category": "HAPPY_PATH",
        "description": "Combine multiple vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "combine([1, 2], [3], [4, 5, 6])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  2  3  4  5  6]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_slice_vector",
        "category": "HAPPY_PATH",
        "description": "Slice a vector: slice([5, 6, 7, 8, 9], 2, 4) = [6  7  8]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "slice([5, 6, 7, 8, 9], 2, 4)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[6  7  8]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_elementwise_multiply",
        "category": "HAPPY_PATH",
        "description": "Element-wise multiply using .* operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "[1 2].*[3 4]"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[3  8]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_elementwise_power",
        "category": "HAPPY_PATH",
        "description": "Element-wise power using .^ operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "[1 2; 3 4].^2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[1  4; 9  16]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_elementwise_divide",
        "category": "HAPPY_PATH",
        "description": "Element-wise divide using ./ operator",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "[2 4; 6 12]./[1 2; 3 4]"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[2  2; 2  3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_vector_scalar_arithmetic",
        "category": "HAPPY_PATH",
        "description": "Vector arithmetic: (1; 2; 3) * 2 - 2",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "(1; 2; 3) * 2 - 2"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[0  2  4]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_genvector_basic",
        "category": "HAPPY_PATH",
        "description": "Generate vector: genvector(x+10, 1, 2, 2) = [11  12]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "genvector(x+10, 1, 2, 2)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[11  12]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_genvector_steps",
        "category": "HAPPY_PATH",
        "description": "Generate vector with steps: genvector(x+10, 1, 2, 3) = [11  11.5  12]",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "genvector(x+10, 1, 2, 3)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[11  11.5  12]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_entrywise_simple",
        "category": "HAPPY_PATH",
        "description": "Element-wise function application",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "entrywise(x, [4 10 12], x)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[4  10  12]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_entrywise_two_vars",
        "category": "HAPPY_PATH",
        "description": "Element-wise function with two variable vectors",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "entrywise(x / y, [4 10 12], x, [2 2 4], y)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "[2  5  3]",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_batch_file_execution",
        "category": "FILE_INPUT",
        "description": "Execute a batch test file with --test-file option",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "--test-file",
            "calculus.batch"
        ],
        "expected_exit_code": 0,
        "expected_stdout": null,
        "expected_stderr": null,
        "timeout_seconds": 60,
        "setup": {
            "create_file": {
                "path": "calculus.batch",
                "content": "diff(6x^2)\n\t12x\n"
            }
        },
        "cleanup": {
            "delete_files": [
                "calculus.batch"
            ]
        }
    },
    {
        "name": "test_pipe_expression_stdin",
        "category": "PIPE_INPUT",
        "description": "Evaluate expression from stdin pipe",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t"
        ],
        "stdin": "2+2",
        "expected_exit_code": 0,
        "expected_stdout": "4",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_empty_expression",
        "category": "BOUNDARY",
        "description": "Empty expression should enter interactive mode or return gracefully",
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
        "name": "test_boundary_limit_at_zero_divergent",
        "category": "BOUNDARY",
        "description": "Limit that diverges: limit(sin(x)/(x^3),0) = +infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(sin(x)/(x^3),0)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "+infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_dimension_empty_vector",
        "category": "BOUNDARY",
        "description": "Dimension of empty vector: dimension([]) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "dimension([])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_columns_empty",
        "category": "BOUNDARY",
        "description": "Columns of empty matrix: columns([]) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "columns([])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_elements_empty",
        "category": "BOUNDARY",
        "description": "Elements of empty matrix: elements([]) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "elements([])"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 10
    },
    {
        "name": "test_boundary_limit_exp_at_infinity",
        "category": "BOUNDARY",
        "description": "Exponential limit at infinity: limit((e^x-e^(-x))/(2),infinity) = +infinity",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((e^x-e^(-x))/(2),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "+infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_limit_exp_at_neg_infinity",
        "category": "HAPPY_PATH",
        "description": "Exponential limit at negative infinity: limit((e^x+e^(-x))/(e^x-e^(-x)),-infinity) = -1",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit((e^x+e^(-x))/(e^x-e^(-x)),-infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "-1",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_limit_quadratic_power_x_squared_zero",
        "category": "BOUNDARY",
        "description": "Limit converging to 0 via x^2 exponent",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((2x-5)/(2x-2))^(4x^2),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_limit_quadratic_power_x_squared_infinity",
        "category": "BOUNDARY",
        "description": "Limit diverging to +infinity via x^2 exponent",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(((3x+6)/(3x-1))^(x^2),infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "+infinity",
        "expected_stderr": null,
        "timeout_seconds": 30
    },
    {
        "name": "test_boundary_2_exp_x_sin_neg_infinity",
        "category": "BOUNDARY",
        "description": "Limit of oscillating dampened function: limit(2^x*sin(2pi*x),-infinity) = 0",
        "command": "qalc",
        "subcommand": "",
        "args": [
            "-t",
            "-s",
            "approximation exact",
            "-s",
            "fr 2",
            "limit(2^x*sin(2pi*x),-infinity)"
        ],
        "expected_exit_code": 0,
        "expected_stdout": "0",
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
