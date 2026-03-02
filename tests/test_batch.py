"""
Batch test harness for qalculate.

Reads .batch files that define expression → expected output pairs.
Format:
  - Lines not starting with tab: expression to evaluate
  - Lines starting with tab: expected output for previous expression
  - Empty lines: separators (ignored)

All batch tests are currently xfail since the full expression parser
is not yet implemented (Milestone 2+). This harness provides the
framework for verifying parity with the C++ implementation.
"""

from __future__ import annotations

import os
import glob
import pytest
from typing import List, Tuple

# Directory containing .batch files
BATCH_DIR = os.path.join(os.path.dirname(__file__), "batch")


def parse_batch_file(filepath: str) -> List[Tuple[str, str]]:
    """
    Parse a .batch file into (expression, expected_output) pairs.

    Returns a list of (expression, expected_output) tuples.
    """
    pairs = []
    current_expr = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")

            # Skip empty lines
            if not line.strip():
                current_expr = None
                continue

            if line.startswith("\t"):
                # This is an expected output line
                expected = line[1:]  # Strip the leading tab
                if current_expr is not None:
                    pairs.append((current_expr, expected))
                    current_expr = None
            else:
                # This is an expression line
                current_expr = line

    return pairs


def discover_batch_files() -> List[str]:
    """Discover all .batch files in the batch directory."""
    if not os.path.isdir(BATCH_DIR):
        return []
    return sorted(glob.glob(os.path.join(BATCH_DIR, "*.batch")))


# Collect all batch files for parametrization
_batch_files = discover_batch_files()


@pytest.fixture(scope="module")
def batch_files():
    """Return list of all batch file paths."""
    return _batch_files


class TestBatchDiscovery:
    """Tests for the batch test infrastructure itself."""

    def test_batch_directory_exists(self):
        """The batch test directory should exist."""
        assert os.path.isdir(BATCH_DIR), f"Batch directory not found: {BATCH_DIR}"

    def test_batch_files_found(self):
        """At least one batch file should exist."""
        assert len(_batch_files) > 0, "No .batch files found"

    def test_parse_operators_batch(self):
        """The operators.batch file should parse correctly."""
        filepath = os.path.join(BATCH_DIR, "operators.batch")
        if not os.path.isfile(filepath):
            pytest.skip("operators.batch not found")

        pairs = parse_batch_file(filepath)
        assert len(pairs) > 0, "No expression/expected pairs found"

        # Verify first pair: "1 + 2" → "3"
        assert pairs[0][0] == "1 + 2"
        assert pairs[0][1] == "3"

    def test_parse_batch_file_format(self):
        """All batch files should parse without errors."""
        for filepath in _batch_files:
            pairs = parse_batch_file(filepath)
            # Each file should have at least one pair
            assert len(pairs) > 0, f"No pairs in {os.path.basename(filepath)}"


# ---------------------------------------------------------------------------
# Parametrized batch tests (xfail for now)
# ---------------------------------------------------------------------------
# These tests will be enabled as expression evaluation is implemented.

def _get_batch_test_ids() -> List[str]:
    """Generate test IDs from batch file names."""
    return [os.path.splitext(os.path.basename(f))[0] for f in _batch_files]


@pytest.mark.xfail(reason="Expression evaluation not yet implemented (Milestone 2+)")
@pytest.mark.parametrize(
    "batch_file",
    _batch_files,
    ids=_get_batch_test_ids(),
)
def test_batch_file(batch_file: str):
    """
    Run all expression/expected pairs from a batch file.

    This test is expected to fail until the Calculator and expression
    parser are fully implemented in later milestones.
    """
    pairs = parse_batch_file(batch_file)
    assert len(pairs) > 0

    # Placeholder: once Calculator is available, evaluate each expression
    # and compare against expected output
    failures = []
    for expr, expected in pairs:
        # TODO: result = calculator.evaluate(expr)
        # For now, mark as not implemented
        result = None
        if result != expected:
            failures.append((expr, expected, result))

    if failures:
        fail_msg = f"\n{len(failures)} of {len(pairs)} tests failed in {os.path.basename(batch_file)}:\n"
        for expr, expected, result in failures[:5]:
            fail_msg += f"  {expr!r} → expected {expected!r}, got {result!r}\n"
        if len(failures) > 5:
            fail_msg += f"  ... and {len(failures) - 5} more\n"
        pytest.fail(fail_msg)
