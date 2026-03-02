"""
qalc – command-line interface for the Qalculate library.

Translated from src/qalc.cc.
This is a minimal stub for Milestone 1, implementing --help, --version,
basic non-interactive expression evaluation, and --test-file support.
The full interactive REPL is deferred to Milestone 4.
"""

from __future__ import annotations

import argparse
import sys
import os
from typing import List, Optional

from qalculate import __version__


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser mirroring the original qalc options."""
    parser = argparse.ArgumentParser(
        prog="qalc",
        description="Qalculate! - multi-purpose calculator",
        add_help=False,  # We implement our own --help to match C++ output format
    )

    # We use add_argument for the flags we handle in Milestone 1.
    # Additional flags are accepted but produce a stub notice.
    parser.add_argument("-h", "-help", "--help",
                        action="store_true", dest="show_help",
                        help="display this help and exit")
    parser.add_argument("-v", "-version", "--version",
                        action="store_true", dest="show_version",
                        help="show application version and exit")
    parser.add_argument("-t", "-terse", "--terse",
                        action="store_true", dest="terse",
                        help="reduce output to just the result")
    parser.add_argument("-i", "-interactive", "--interactive",
                        action="store_true", dest="interactive",
                        help="start in interactive mode")
    parser.add_argument("-s", "-set", "--set",
                        action="append", dest="set_options", metavar="OPTION VALUE",
                        help="as set command in interactive session")
    parser.add_argument("-b", "-base", "--base",
                        dest="base", metavar="BASE",
                        help="set the number base for results")
    parser.add_argument("-f", "-file", "--file",
                        dest="file", metavar="FILE",
                        help="execute commands from a file first")
    parser.add_argument("--test-file",
                        dest="test_file", metavar="FILE",
                        help="run a batch test file")
    parser.add_argument("-n", "-nodefs", "--nodefs",
                        action="store_true", dest="nodefs",
                        help="do not load any definitions from file")
    parser.add_argument("-m", "-time", "--time",
                        dest="maxtime", metavar="MILLISECONDS",
                        help="terminate calculation after specified time")
    parser.add_argument("-c", "-color", "--color",
                        dest="color", nargs="?", const="1", metavar="COLOR",
                        help="use colors")
    parser.add_argument("-e", "-exrates", "--exrates",
                        action="store_true", dest="exrates",
                        help="update exchange rates")
    parser.add_argument("-defaults", "--defaults",
                        action="store_true", dest="defaults",
                        help="load default settings")
    parser.add_argument("-l", "-list", "--list",
                        dest="list", nargs="?", const="", metavar="SEARCH TERM",
                        help="list variables, functions, units, and prefixes")
    parser.add_argument("--list-functions",
                        dest="list_functions", nargs="?", const="", metavar="SEARCH TERM")
    parser.add_argument("--list-units",
                        dest="list_units", nargs="?", const="", metavar="SEARCH TERM")
    parser.add_argument("--list-variables",
                        dest="list_variables", nargs="?", const="", metavar="SEARCH TERM")
    parser.add_argument("--list-prefixes",
                        dest="list_prefixes", nargs="?", const="", metavar="SEARCH TERM")
    parser.add_argument("-p",
                        dest="programming_base", nargs="?", const="",
                        metavar="BASE",
                        help="start in programming mode")
    parser.add_argument("-nounits", "--nounits", action="store_true")
    parser.add_argument("-nocurrencies", "--nocurrencies", action="store_true")
    parser.add_argument("-nofunctions", "--nofunctions", action="store_true")
    parser.add_argument("-novariables", "--novariables", action="store_true")
    parser.add_argument("-nodatasets", "--nodatasets", action="store_true")
    parser.add_argument("-u8", action="store_true", dest="unicode_on")
    # Note: +u8 cannot be handled by argparse (+ prefix not supported).
    # It is handled manually in main() by pre-processing argv.

    # Positional: the expression to evaluate
    parser.add_argument("expression", nargs="*", default=[],
                        help="expression to evaluate")

    return parser


# ---------------------------------------------------------------------------
# Help text (matches the original C++ output)
# ---------------------------------------------------------------------------

_HELP_TEXT = """\
usage: qalc [options] [expression]

where options are:

\t-b, -base BASE
\tset the number base for results and, optionally, expressions

\t-c, -color [COLOR]
\tuse colors to highlight different elements of expressions and results

\t-defaults
\tload default settings

\t-e, -exrates
\tupdate exchange rates

\t-f, -file FILE
\texecute commands from a file first

\t-h, -help
\tdisplay this help and exit

\t-i, -interactive
\tstart in interactive mode

\t-l, -list [SEARCH TERM]
\tdisplays a list of all user-defined or matching variables, functions, units, and prefixes

\t--list-functions [SEARCH TERM]
\tdisplays a list of all or matching functions

\t--list-prefixes [SEARCH TERM]
\tdisplays a list of all or matching prefixes

\t--list-units [SEARCH TERM]
\tdisplays a list of all or matching units

\t--list-variables [SEARCH TERM]
\tdisplays a list of all or matching variables

\t-m, -time MILLISECONDS
\tterminate calculation and display of result after specified amount of time

\t-n, -nodefs
\tdo not load any functions, units, or variables from file

\t-nocurrencies
\tdo not load any global currencies from file

\t-nodatasets
\tdo not load any global data sets from file

\t-nofunctions
\tdo not load any global functions from file

\t-nounits
\tdo not load any global units from file

\t-novariables
\tdo not load any global variables from file

\t-p [BASE]
\tstart in programming mode (same as -b "BASE BASE" -s "xor^", with base conversion)

\t-s, -set "OPTION VALUE"
\tas set command in interactive program session (e.g. -set "base 16")

\t-t, -terse
\treduce output to just the result of the input expression

\t-/+u8
\tswitch unicode support on/off

\t-v, -version
\tshow application version and exit

The program will start in interactive mode if no expression and no file \
is specified (or interactive mode is explicitly selected). Type help in \
interactive mode for information about available commands.

For more information about mathematical expression and different options, \
please consult the man page, or the relevant sections in the manual of the \
graphical user interface (available at \
https://qalculate.github.io/manual/index.html), which also includes a \
complete list of functions, variables, and units.
"""


# ---------------------------------------------------------------------------
# Batch test runner (--test-file)
# ---------------------------------------------------------------------------

def _run_test_file(filepath: str) -> int:
    """
    Run a batch test file.

    Each line in the file is either:
    - An expression to evaluate
    - A line starting with tab (expected output for the preceding expression)
    - Empty line / comment

    Returns 0 on success, 1 on failure.
    """
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1

    # For Milestone 1, this is a minimal stub that reads the file and
    # prints a placeholder. Full evaluation is deferred to later milestones.
    print(f"Test file: {filepath}")
    print("(Test evaluation not yet implemented – placeholder for Milestone 1)")
    return 0


# ---------------------------------------------------------------------------
# Stub expression evaluator
# ---------------------------------------------------------------------------

def _evaluate_expression(expression: str, terse: bool = False) -> str:
    """
    Evaluate a mathematical expression.

    Milestone 1 stub: handles basic integer arithmetic using Python eval
    for simple cases. Full expression parsing deferred to Milestone 2+.
    """
    expr = expression.strip()
    if not expr:
        return ""

    try:
        # Attempt simple arithmetic evaluation for basic integers
        # Only allow safe operations (digits, operators, parens)
        allowed = set("0123456789+-*/().^ %")
        if all(c in allowed or c.isspace() for c in expr):
            # Replace ^ with ** for Python power
            py_expr = expr.replace("^", "**")
            result = eval(py_expr, {"__builtins__": {}}, {})
            # Format as integer if possible
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return str(result)
    except Exception:
        pass

    return f"(expression evaluation not yet fully implemented: {expr})"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the qalc CLI."""
    if argv is None:
        argv = sys.argv[1:]

    # Pre-process: handle +u8 which argparse can't parse (+ prefix)
    unicode_off = False
    filtered_argv = []
    for a in argv:
        if a == "+u8":
            unicode_off = True
        else:
            filtered_argv.append(a)
    argv = filtered_argv

    parser = _build_parser()

    # Use parse_known_args to be tolerant of flags we don't yet handle
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit:
        return 1

    # --help
    if args.show_help:
        print(_HELP_TEXT)
        return 0

    # --version
    if args.show_version:
        print(__version__)
        return 0

    # --test-file
    if args.test_file:
        return _run_test_file(args.test_file)

    # Gather expression from positional args
    expression = " ".join(args.expression)
    if unknown:
        # Some unknown args might be part of the expression
        expression = " ".join(unknown + args.expression) if not expression else expression

    # Non-interactive mode: evaluate expression
    if expression:
        result = _evaluate_expression(expression, terse=args.terse)
        if result:
            if args.terse:
                print(result)
            else:
                print(f"  {result}")
        return 0

    # Interactive mode (or no expression given)
    if args.interactive or not expression:
        _interactive_mode()
        return 0

    return 0


def _interactive_mode() -> None:
    """Minimal interactive REPL stub for Milestone 1."""
    print(f"qalc {__version__}")
    print("Type 'help' for available commands, 'quit' to exit.")
    print("(Interactive mode is a stub in Milestone 1)")
    print()

    try:
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                break

            line = line.strip()
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                break
            if line.lower() == "help":
                print("Available commands (stub):")
                print("  help    - show this help")
                print("  quit    - exit the calculator")
                print("  exit    - exit the calculator")
                print("Full interactive mode will be implemented in Milestone 4.")
                continue
            if line.lower() == "version":
                print(__version__)
                continue

            result = _evaluate_expression(line)
            if result:
                print(f"  {result}")

    except KeyboardInterrupt:
        print()


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
