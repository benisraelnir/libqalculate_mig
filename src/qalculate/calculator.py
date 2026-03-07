"""High-level Calculator API for the qalculate Python port.

This module provides the ``Calculator`` class which serves as the primary
entry point for loading definitions, evaluating expressions, and managing
settings.  For Milestone 1 the evaluator handles simple integer arithmetic
only (``+``, ``-``, ``*``, ``/``, parentheses).
"""

from __future__ import annotations

import os
import re
from fractions import Fraction
from pathlib import Path
from typing import Optional

from qalculate.definitions.loader import (
    DefinitionItem,
    load_currencies,
    load_datasets,
    load_functions,
    load_prefixes,
    load_units,
    load_variables,
)


class Calculator:
    """Core calculator object that owns loaded definitions and settings.

    Usage::

        calc = Calculator()
        calc.load_global_definitions()
        result = calc.evaluate_simple("2+2")
        # result == "4"
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Definition registries
        self.functions: list[DefinitionItem] = []
        self.units: list[DefinitionItem] = []
        self.variables: list[DefinitionItem] = []
        self.prefixes: list[DefinitionItem] = []
        self.currencies: list[DefinitionItem] = []
        self.datasets: list[DefinitionItem] = []

        # Settings
        self.precision: int = 10
        self.base: int = 10
        self.angle_unit: str = "rad"
        self.use_unicode_signs: bool = True
        self.terse: bool = False
        self.color: int = 0
        self.time_limit: int = 0

        # Internal state
        self.loaded: bool = False
        self._data_dir: Optional[str] = None

    # ------------------------------------------------------------------
    # Data directory resolution
    # ------------------------------------------------------------------

    def find_data_dir(self) -> str:
        """Find the data directory containing XML/JSON definition files.

        The search order is:

        1. The ``QALCULATE_DATA_DIR`` environment variable, if set.
        2. ``../../data/`` relative to this source file (works when running
           from a source checkout).
        3. Common system-wide install paths.

        Returns:
            The absolute path to the data directory.

        Raises:
            FileNotFoundError: If no data directory can be located.
        """
        if self._data_dir is not None:
            return self._data_dir

        # 1. Environment variable
        env_dir = os.environ.get("QALCULATE_DATA_DIR")
        if env_dir and Path(env_dir).is_dir():
            self._data_dir = str(Path(env_dir).resolve())
            return self._data_dir

        # 2. Relative to this package
        pkg_dir = Path(__file__).resolve().parent
        candidate = pkg_dir.parent.parent / "data"
        if candidate.is_dir():
            self._data_dir = str(candidate)
            return self._data_dir

        # 3. Common install paths
        for system_path in (
            "/usr/share/qalculate/",
            "/usr/local/share/qalculate/",
        ):
            if Path(system_path).is_dir():
                self._data_dir = system_path
                return self._data_dir

        raise FileNotFoundError(
            "Cannot locate qalculate data directory. "
            "Set the QALCULATE_DATA_DIR environment variable."
        )

    # ------------------------------------------------------------------
    # Definition loading
    # ------------------------------------------------------------------

    def load_global_definitions(
        self,
        load_units: bool = True,
        load_functions: bool = True,
        load_variables: bool = True,
        load_datasets: bool = True,
        load_currencies: bool = True,
    ) -> None:
        """Load definitions from XML files in the data directory.

        Each flag controls whether the corresponding XML file is parsed.
        After a successful call the ``loaded`` attribute is set to ``True``.

        Parameters:
            load_units: Parse ``units.xml``.
            load_functions: Parse ``functions.xml``.
            load_variables: Parse ``variables.xml``.
            load_datasets: Parse ``datasets.xml``.
            load_currencies: Parse ``currencies.xml``.
        """
        data_dir = self.find_data_dir()

        if load_functions:
            self.functions = _load_functions(data_dir)
        if load_units:
            self.units = _load_units(data_dir)
        if load_variables:
            self.variables = _load_variables(data_dir)
            self._add_builtin_variables()
        if load_currencies:
            self.currencies = _load_currencies(data_dir)
        if load_datasets:
            self.datasets = _load_datasets(data_dir)
            # Dataset functions (atom, planet, etc.)
            if load_functions:
                self._add_dataset_functions()

        # Prefixes are always loaded when any definitions are requested.
        if load_units or load_functions or load_variables:
            self.prefixes = _load_prefixes(data_dir)

        self.loaded = True

    def _add_builtin_variables(self) -> None:
        """Add built-in variables not defined in XML."""
        builtins = [
            ("ans", ["answer", "ans1"], "Last Answer"),
            ("ans2", [], "Answer 2"),
            ("ans3", [], "Answer 3"),
            ("ans4", [], "Answer 4"),
            ("ans5", [], "Answer 5"),
            ("x", [], "Default Unknown"),
            ("y", [], "Default Unknown"),
            ("z", [], "Default Unknown"),
            ("n", [], "Default Unknown"),
            ("true", ["yes"], "True"),
            ("false", ["no"], "False"),
            ("undefined", [], "Undefined"),
            ("now", [], "Current Date and Time"),
            ("today", [], "Current Date"),
            ("tomorrow", [], "Tomorrow"),
            ("yesterday", [], "Yesterday"),
            ("uptime", [], "Uptime"),
            ("precision", [], "Precision"),
            ("percent", ["%"], "Percent"),
            ("permille", ["\u2030"], "Per Mille"),
            ("permyriad", ["\u2031"], "Per Myriad"),
            ("i", [], "Imaginary Unit"),
            ("e", [], "Euler's Number"),
            ("pi", ["\u03c0"], "Pi"),
            ("euler", ["\u03b3"], "Euler's Constant"),
            ("golden", ["\u03c6"], "Golden Ratio"),
            ("catalan", [], "Catalan's Constant"),
            ("apery", [], "Apery's Constant"),
            ("plastic", ["\u03c1"], "Plastic Constant"),
            ("pythagoras", [], "Pythagoras' Constant"),
            ("omega", [], "Omega Constant"),
            ("tau", ["\u03c4"], "Tau"),
            ("PlusInfinity", ["\u221e", "infinity"], "Plus Infinity"),
            ("MinusInfinity", [], "Minus Infinity"),
            ("dozen", ["dz", "doz"], "Dozen"),
            ("BakersDozen", [], "Baker's Dozen"),
            ("score", [], "Score"),
            ("gross", ["gro"], "Gross"),
            ("GreatGross", [], "Great Gross"),
            ("hundred", [], "Hundred"),
            ("thousand", [], "Thousand"),
            ("million", [], "Million"),
            ("billion", [], "Billion"),
            ("trillion", [], "Trillion"),
            ("quadrillion", [], "Quadrillion"),
            ("quintillion", [], "Quintillion"),
            ("sextillion", [], "Sextillion"),
            ("septillion", [], "Septillion"),
            ("octillion", [], "Octillion"),
            ("nonillion", [], "Nonillion"),
            ("decillion", [], "Decillion"),
            ("undecillion", [], "Undecillion"),
            ("duodecillion", [], "Duodecillion"),
            ("tredecillion", [], "Tredecillion"),
            ("quattuordecillion", [], "Quattuordecillion"),
            ("quindecillion", [], "Quindecillion"),
            ("sexdecillion", [], "Sexdecillion"),
            ("septendecillion", [], "Septendecillion"),
            ("octodecillion", [], "Octodecillion"),
            ("novemdecillion", [], "Novemdecillion"),
            ("vigintillion", [], "Vigintillion"),
            ("centillion", [], "Centillion"),
            ("googol", [], "Googol"),
            ("googolplex", [], "Googolplex"),
            ("LongHundred", ["GreatHundred", "twelfty"], "Long Hundred"),
            ("LongThousand", [], "Long Thousand"),
            ("MR", [], "Memory Register"),
            ("pauli\u2080", ["\u03c3\u2080"], "Pauli Matrix 0"),
            ("pauli\u2081", ["\u03c3\u2081"], "Pauli Matrix 1"),
            ("pauli\u2082", ["\u03c3\u2082"], "Pauli Matrix 2"),
            ("pauli\u2083", ["\u03c3\u2083"], "Pauli Matrix 3"),
        ]
        for name, alts, title in builtins:
            # Check for duplicates
            if any(v.name == name for v in self.variables):
                continue
            self.variables.append(DefinitionItem(
                name=name,
                alt_names=alts,
                title=title,
                category="",
                item_type="variable",
                is_hidden=False,
                is_active=True,
                is_currency=False,
                is_composite=False,
                subtype="builtin",
            ))

    def _add_dataset_functions(self) -> None:
        """Add dataset functions (atom, planet, etc.)."""
        for ds in self.datasets:
            if not any(f.name == ds.name for f in self.functions):
                self.functions.append(DefinitionItem(
                    name=ds.name,
                    alt_names=ds.alt_names,
                    title=ds.title,
                    category="Data Sets",
                    item_type="function",
                    is_hidden=ds.is_hidden,
                    is_active=ds.is_active,
                    is_currency=False,
                    is_composite=False,
                    subtype="dataset",
                ))

    # ------------------------------------------------------------------
    # Simple expression evaluation (Milestone 1)
    # ------------------------------------------------------------------

    _SAFE_EXPR_RE = re.compile(r"^[\d+\-*/().\s]*$")

    def evaluate_simple(self, expression: str) -> str:
        """Evaluate a simple arithmetic expression and return the result as
        a string.

        Supported tokens: integers, ``+``, ``-``, ``*``, ``/``, parentheses,
        and whitespace.

        Special cases:
        * An empty (or whitespace-only) expression returns ``"0"``.
        * Division uses integer (floor) semantics when both operands are
          integers and the result is exact; otherwise a ``Fraction`` is used,
          ultimately producing an integer string when the fraction is whole.

        Parameters:
            expression: The arithmetic expression to evaluate.

        Returns:
            The evaluated result formatted as a string.

        Raises:
            ValueError: If the expression contains disallowed characters.
            ZeroDivisionError: On division by zero.
        """
        expr = expression.strip()
        if not expr:
            return "0"

        # Safety check: only allow digits, operators, parens, dots, whitespace
        if not self._SAFE_EXPR_RE.match(expr):
            raise ValueError(f"Expression contains disallowed characters: {expr!r}")

        try:
            # Replace '/' with Fraction-based division to get exact results.
            # We evaluate in a restricted namespace.
            result = self._eval_arithmetic(expr)
        except ZeroDivisionError:
            raise
        except Exception as exc:
            raise ValueError(f"Failed to evaluate expression: {exc}") from exc

        # Format the result
        if isinstance(result, Fraction):
            if result.denominator == 1:
                return str(result.numerator)
            # Return as decimal if it terminates, otherwise as fraction
            return str(result)
        if isinstance(result, float):
            if result == int(result):
                return str(int(result))
            return str(result)
        return str(result)

    # ------------------------------------------------------------------
    # Internal arithmetic evaluator
    # ------------------------------------------------------------------

    @staticmethod
    def _eval_arithmetic(expr: str):
        """Parse and evaluate *expr* using a small recursive-descent parser
        that only understands integers, ``+``, ``-``, ``*``, ``/``, and
        parentheses.  All arithmetic is done with ``fractions.Fraction``
        so that exact integer results are preserved.

        Returns a ``Fraction`` (or ``int``).
        """
        tokens = _tokenize(expr)
        pos = [0]  # mutable index

        def peek():
            if pos[0] < len(tokens):
                return tokens[pos[0]]
            return None

        def consume(expected=None):
            tok = tokens[pos[0]]
            if expected is not None and tok != expected:
                raise ValueError(f"Expected {expected!r}, got {tok!r}")
            pos[0] += 1
            return tok

        def parse_expr():
            """expr := term (('+' | '-') term)*"""
            left = parse_term()
            while peek() in ("+", "-"):
                op = consume()
                right = parse_term()
                if op == "+":
                    left = left + right
                else:
                    left = left - right
            return left

        def parse_term():
            """term := unary (('*' | '/') unary)*"""
            left = parse_unary()
            while peek() in ("*", "/"):
                op = consume()
                right = parse_unary()
                if op == "*":
                    left = left * right
                else:
                    if right == 0:
                        raise ZeroDivisionError("division by zero")
                    left = Fraction(left, right) if isinstance(left, int) and isinstance(right, int) else left / right
            return left

        def parse_unary():
            """unary := ('+' | '-')* atom"""
            if peek() == "-":
                consume()
                return -parse_unary()
            if peek() == "+":
                consume()
                return parse_unary()
            return parse_atom()

        def parse_atom():
            """atom := NUMBER | '(' expr ')'"""
            tok = peek()
            if tok == "(":
                consume("(")
                val = parse_expr()
                consume(")")
                return val
            # Must be a number
            consume()  # advance
            try:
                return int(tok)
            except ValueError:
                return Fraction(tok)

        result = parse_expr()
        if pos[0] != len(tokens):
            raise ValueError(f"Unexpected token: {tokens[pos[0]]!r}")
        return result

    # ------------------------------------------------------------------
    # Expression formatting
    # ------------------------------------------------------------------

    @staticmethod
    def format_expression(expression: str) -> str:
        """Format *expression* by adding spaces around binary operators.

        Unary minus at the start of the expression or after an opening
        parenthesis is preserved without extra spacing.

        Examples::

            >>> Calculator.format_expression("1+1")
            '1 + 1'
            >>> Calculator.format_expression("-5+3")
            '-5 + 3'
            >>> Calculator.format_expression("2*3+4/2")
            '2 * 3 + 4 / 2'
        """
        if not expression:
            return expression

        tokens = _tokenize(expression)
        parts: list[str] = []
        for i, tok in enumerate(tokens):
            if tok in ("+", "-", "*", "/"):
                # Determine whether this is a unary operator:
                # It is unary if it is the first token, or follows another
                # operator or an opening parenthesis.
                is_unary = (
                    i == 0
                    or tokens[i - 1] in ("+", "-", "*", "/", "(")
                )
                if is_unary:
                    parts.append(tok)
                else:
                    parts.append(f" {tok} ")
            else:
                parts.append(tok)
        return "".join(parts)

    # ------------------------------------------------------------------
    # List helpers (for CLI --list* commands)
    # ------------------------------------------------------------------

    def list_functions(self, search: str = "") -> list[DefinitionItem]:
        """Return functions matching *search* (case-insensitive substring)."""
        return self._filter_items(self.functions, search)

    def list_units(self, search: str = "") -> list[DefinitionItem]:
        """Return units matching *search*."""
        return self._filter_items(self.units, search)

    def list_variables(self, search: str = "") -> list[DefinitionItem]:
        """Return variables matching *search*."""
        return self._filter_items(self.variables, search)

    def list_prefixes(self, search: str = "") -> list[DefinitionItem]:
        """Return prefixes matching *search*."""
        return self._filter_items(self.prefixes, search)

    def list_currencies(self, search: str = "") -> list[DefinitionItem]:
        """Return currencies matching *search*."""
        return self._filter_items(self.currencies, search)

    def list_datasets(self, search: str = "") -> list[DefinitionItem]:
        """Return datasets matching *search*."""
        return self._filter_items(self.datasets, search)

    def list_all(self, search: str = "") -> list[DefinitionItem]:
        """Return all definition items matching *search*, across all kinds."""
        combined = (
            self.functions
            + self.units
            + self.variables
            + self.prefixes
            + self.currencies
            + self.datasets
        )
        return self._filter_items(combined, search)

    @staticmethod
    def _filter_items(items: list[DefinitionItem], search: str) -> list[DefinitionItem]:
        """Return items whose name, title, or any alias matches *search*
        (case-insensitive substring match).  If *search* is empty, return all
        items."""
        if not search:
            return list(items)
        needle = search.lower()
        result: list[DefinitionItem] = []
        for item in items:
            if (
                needle in item.name.lower()
                or needle in item.title.lower()
                or any(needle in n.lower() for n in item.alt_names)
            ):
                result.append(item)
        return result

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------

    def set_option(self, option_str: str) -> None:
        """Apply a ``set``-style option string such as ``"base 16"`` or
        ``"precision 20"``.

        Multiple options separated by ``;`` are supported.
        """
        for part in option_str.split(";"):
            part = part.strip()
            if not part:
                continue
            tokens = part.split(None, 1)
            if len(tokens) < 2:
                continue
            key, value = tokens[0].lower(), tokens[1].strip()
            self._apply_setting(key, value)

    def _apply_setting(self, key: str, value: str) -> None:
        """Apply a single setting *key*/*value* pair."""
        if key == "base":
            try:
                self.base = int(value)
            except ValueError:
                pass
        elif key == "precision":
            try:
                self.precision = int(value)
            except ValueError:
                pass
        elif key in ("angle", "angleunit", "angle_unit"):
            self.angle_unit = value.lower()
        elif key in ("unicode", "u8"):
            self.use_unicode_signs = value not in ("0", "off", "false", "no")
        elif key in ("ignore", "language"):
            # Accept but do not act on locale/language settings for now
            pass

    def load_defaults(self) -> None:
        """Reset all settings to their defaults."""
        self.precision = 10
        self.base = 10
        self.angle_unit = "rad"
        self.use_unicode_signs = True
        self.terse = False
        self.color = 0
        self.time_limit = 0


# ======================================================================
# Module-level helpers (thin wrappers around loader to avoid name
# clashes with the method parameter names in load_global_definitions)
# ======================================================================

def _load_functions(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_functions as _lf
    return _lf(data_dir)


def _load_units(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_units as _lu
    return _lu(data_dir)


def _load_currencies(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_currencies as _lc
    return _lc(data_dir)


def _load_variables(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_variables as _lv
    return _lv(data_dir)


def _load_prefixes(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_prefixes as _lp
    return _lp(data_dir)


def _load_datasets(data_dir: str) -> list[DefinitionItem]:
    from qalculate.definitions.loader import load_datasets as _ld
    return _ld(data_dir)


# ======================================================================
# Tokenizer for simple arithmetic expressions
# ======================================================================

def _tokenize(expr: str) -> list[str]:
    """Split *expr* into a flat list of tokens (number literals and
    single-character operators/parentheses)."""
    tokens: list[str] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "+-*/()":
            tokens.append(ch)
            i += 1
        elif ch.isdigit() or ch == ".":
            start = i
            while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
                i += 1
            tokens.append(expr[start:i])
        else:
            raise ValueError(f"Unexpected character in expression: {ch!r}")
    return tokens
