"""Command-line interface for qalc (Python port of libqalculate CLI).

This module replicates the argument parsing and output behaviour of the
original C++ ``qalc`` command so that the Python port is a drop-in
replacement at the CLI level.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from qalculate import __version__ as VERSION
from qalculate.calculator import Calculator
from qalculate.definitions.loader import (
    DefinitionItem,
    filter_visible,
    format_item_names,
)

# ======================================================================
# Constants
# ======================================================================

NUMBER_ELEMENTS = set("0123456789")

HELP_TEXT = """\
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

The program will start in interactive mode if no expression and no file is specified (or interactive mode is explicitly selected). Type help in interactive mode for information about available commands.

For more information about mathematical expression and different options, please consult the man page, or the relevant sections in the manual of the graphical user interface (available at https://qalculate.github.io/manual/index.html), which also includes a complete list of functions, variables, and units.
"""

LIST_FOOTER = ("\nFor more information about a specific function, variable, "
               "unit, or prefix, please use the info command (in interactive "
               "mode).\n\n")


# ======================================================================
# Helpers
# ======================================================================

def _unicode_len(s: str) -> int:
    """Approximate display width of *s* (single-width characters only)."""
    return len(s)


def _format_columns(names: list[str], cols: int = 80) -> str:
    """Format a list of name strings into tab-aligned columns."""
    if not names:
        return ""
    max_l = max(_unicode_len(n) for n in names)
    max_tabs = (max_l // 8) + 1
    col_width = max_tabs * 8
    max_c = max(cols // col_width, 1)

    # Single column: one item per line, no tab padding
    if max_c <= 1:
        return "\n".join(names) + "\n"

    lines: list[str] = []
    row: list[str] = []
    for i, name in enumerate(names):
        l = _unicode_len(name)
        nr_of_tabs = max_tabs - (l // 8)
        padded = name + "\t" * nr_of_tabs
        row.append(padded)
        if len(row) >= max_c:
            # Complete row: strip trailing tabs from the last item
            line = "".join(row[:-1]) + row[-1].rstrip("\t")
            lines.append(line)
            row = []
    if row:
        # Incomplete last row: keep trailing tabs
        lines.append("".join(row))
    return "\n".join(lines) + "\n"


def _name_matches(item: DefinitionItem, search: str) -> bool:
    """Check if a DefinitionItem matches a search term.

    Matches if the search term is a prefix of any name, or if it
    appears at the start of a word in the title.
    """
    s = search.lower()
    # Check primary name (prefix match)
    if item.name.lower().startswith(s):
        return True
    # Check alt names (prefix match)
    for n in item.alt_names:
        if n.lower().startswith(s):
            return True
    # Check title (word-boundary match: search at start of title words)
    title_lower = item.title.lower()
    if title_lower.startswith(s):
        return True
    # Check at word boundaries in title
    for i in range(1, len(title_lower)):
        if title_lower[i - 1] in " -/(" and title_lower[i:].startswith(s):
            return True
    return False


def _format_search_item(item: DefinitionItem) -> str:
    """Format an item for search results: 'name / alt1 (Title)'."""
    names_str = format_item_names(item)
    if item.title and item.title != item.name:
        return f"{names_str} ({item.title})"
    return names_str


# ======================================================================
# List commands
# ======================================================================

def list_defs(calc: Calculator, list_type: str, search_str: str = "") -> None:
    """Print definitions to stdout.

    list_type:
        '0' or '' - generic list (local items or search all)
        'f' - functions
        'v' - variables
        'u' - units
        'p' - prefixes
    """
    if list_type == '0' or list_type == '':
        if search_str:
            _list_search_all(calc, search_str)
        else:
            _list_local(calc)
    elif list_type == 'f':
        _list_type_items(calc.functions, search_str, "function")
    elif list_type == 'v':
        _list_type_items(calc.variables, search_str, "variable")
    elif list_type == 'u':
        _list_type_items(calc.units, search_str, "unit")
    elif list_type == 'p':
        _list_type_items(calc.prefixes, search_str, "prefix")


def _list_local(calc: Calculator) -> None:
    """List only locally-defined items (none for now)."""
    print("\nNo local variables, functions or units have been defined.")
    print(LIST_FOOTER, end="")


def _list_search_all(calc: Calculator, search: str) -> None:
    """Search across all definition types."""
    results: list[str] = []
    # Search functions, variables, units (not composite), prefixes
    all_items = (
        filter_visible(calc.functions) +
        filter_visible([u for u in calc.units if not u.is_composite]) +
        filter_visible(calc.currencies) +
        filter_visible(calc.variables) +
        filter_visible(calc.prefixes)
    )
    for item in all_items:
        if _name_matches(item, search):
            results.append(_format_search_item(item))

    results.sort()
    for r in results:
        print(r)
    print(LIST_FOOTER, end="")


def _list_type_items(items: list[DefinitionItem], search: str,
                     item_type: str) -> None:
    """List items of a specific type."""
    visible = filter_visible(items)
    if item_type == "unit":
        visible = [u for u in visible if not u.is_composite]

    if search:
        matching = [i for i in visible if _name_matches(i, search)]
        results = [_format_search_item(i) for i in matching]
        results.sort()
        for r in results:
            print(r)
    else:
        results = [format_item_names(i) for i in visible]
        results.sort()
        # Use column formatting for short-item types (functions, prefixes)
        # and single-column for long-item types (units, variables)
        if item_type in ("function", "prefix"):
            print(_format_columns(results), end="")
        else:
            print("\n".join(results) + "\n", end="")

    print(LIST_FOOTER, end="")


# ======================================================================
# Expression evaluation
# ======================================================================

def execute_expression(calc: Calculator, expression: str, terse: bool,
                       use_unicode: bool, color: int = 0) -> None:
    """Evaluate an expression and print the result."""
    try:
        result = calc.evaluate_simple(expression)
    except Exception:
        result = expression  # Fallback: print the expression itself

    # Replace ASCII minus with Unicode minus for display
    if use_unicode and result.startswith("-"):
        result = "\u2212" + result[1:]

    if terse:
        print(result)
    else:
        formatted = calc.format_expression(expression)
        if use_unicode:
            formatted = formatted.replace(" - ", " \u2212 ")
        print(f"{formatted} = {result}")


# ======================================================================
# File/Batch processing
# ======================================================================

def run_file_commands(calc: Calculator, filepath: str, terse: bool,
                      use_unicode: bool, color: int = 0) -> None:
    """Execute commands from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                execute_expression(calc, line.strip(), terse, use_unicode, color)
    except FileNotFoundError:
        pass  # Silently ignore missing file (matches SRC behavior)


def run_test_file(calc: Calculator, filepath: str) -> None:
    """Execute batch tests from a file in unit-test mode."""
    test_count = 0
    pass_count = 0
    fail_count = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"\033[31m\nFailed to open {filepath}\n\n\033[0m", end="")
        return

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n').rstrip('\r')

        # Skip empty lines and comments
        if not line or line.startswith('#') or line.startswith('//'):
            i += 1
            continue

        # Skip lines starting with tab (those are expected results, handled below)
        if line.startswith('\t'):
            i += 1
            continue

        # This is an expression line
        expr = line.strip()
        if not expr:
            i += 1
            continue

        # Next line should be expected result (starting with tab)
        expected = ""
        if i + 1 < len(lines):
            next_line = lines[i + 1].rstrip('\n').rstrip('\r')
            if next_line.startswith('\t'):
                expected = next_line.lstrip('\t').strip()
                i += 2
            else:
                i += 1
                continue
        else:
            i += 1
            continue

        # Evaluate and compare
        try:
            result = calc.evaluate_simple(expr)
        except Exception:
            result = ""

        test_count += 1
        if result == expected:
            pass_count += 1
        else:
            fail_count += 1

    if test_count == 0:
        # Red warning
        print(f"\033[31m\nWARNING: 0 tests were run "
              f"(indentation needs to be tab-based)\n\n\033[0m", end="")
    elif fail_count == 0:
        # Green success
        print(f"\033[32m\n{filepath} - {pass_count} tests passed"
              f"\n\n\033[0m", end="")
    else:
        # Red failures
        print(f"\033[31m\n{filepath} - {fail_count} of {test_count} tests "
              f"failed\n\n\033[0m", end="")


# ======================================================================
# Interactive REPL
# ======================================================================

def run_interactive(calc: Calculator, terse: bool, use_unicode: bool,
                    color: int = -1) -> None:
    """Run the interactive REPL."""
    # Default to color enabled in interactive mode (matches SRC behavior)
    if color < 0:
        color = 1
    prompt = "> "
    sys.stdout.write(prompt)
    sys.stdout.flush()

    try:
        for line in sys.stdin:
            line = line.rstrip('\n').rstrip('\r')
            if not line:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                continue

            # Echo the expression
            sys.stdout.write(f"{line}\n\n")

            # Evaluate
            try:
                result = calc.evaluate_simple(line.strip())
            except Exception:
                result = line.strip()

            if use_unicode and result.startswith("-"):
                result = "\u2212" + result[1:]

            if color:
                sys.stdout.write(f"  \033[0;36m{result}\033[0m\n\n")
            else:
                sys.stdout.write(f"  {result}\n\n")

            sys.stdout.write(prompt)
            sys.stdout.flush()
    except EOFError:
        pass


# ======================================================================
# Argument parsing (replicates C++ qalc custom parsing)
# ======================================================================

def _extract_value(svar: str, argv: list[str], i: int) -> tuple[str, int]:
    """Extract a value for an option.

    Supports formats: -opt VALUE, -opt=VALUE, -opt16 (numeric suffix).
    Returns (value, new_index).
    """
    # Check for = syntax
    if "=" in svar:
        eq_idx = svar.index("=")
        return svar[eq_idx + 1:], i

    # Check for numeric suffix (e.g., -b16, -c2)
    for j in range(1, len(svar)):
        if svar[j].isdigit() or svar[j] == '=':
            return svar[j:], i

    # Next argument
    if i + 1 < len(argv):
        return argv[i + 1], i + 1

    return "", i


def main(args: list[str] | None = None) -> int:
    """Main entry point for the qalc CLI."""
    if args is None:
        args = sys.argv[1:]

    # Phase 0: Build the full argv list
    argv = list(args)
    argc = len(argv)

    # Options state
    calc_arg_begun = False
    expression_parts: list[str] = []
    expression_after_argc = -1  # index of -- if found

    load_global_defs = True
    load_units = True
    load_functions = True
    load_variables = True
    load_datasets = True
    load_currencies = True

    result_only = False  # terse mode
    interactive_mode = False
    load_defaults = False
    fetch_exchange_rates = False
    programmers_mode = False
    unittest = False
    save_defs_on_exit = True
    enable_unicode = -1  # -1 = auto, 0 = off, 1 = on
    force_color = -1  # -1 = auto

    set_option_strings: list[str] = []
    command_file = ""
    time_limit = 0

    list_type = 'n'  # 'n' = no list
    search_str = ""

    # Detect -- position
    for idx in range(argc):
        if argv[idx] == "--":
            expression_after_argc = idx
            break

    # Phase 1: Parse arguments
    i = 0
    while i < argc:
        if calc_arg_begun:
            expression_parts.append(argv[i])
            i += 1
            continue

        arg = argv[i]

        # Strip the option name (normalize)
        svar = arg
        svalue = ""

        # Extract numeric suffix or = value from svar
        if len(svar) > 1 and svar[0] != '+':
            for j in range(1, len(svar)):
                if svar[j].isdigit():
                    if j == 2 or (j > 0 and svar[j-1] == '='):
                        svalue = svar[j:].lstrip('=')
                        svar = svar[:j].rstrip('=')
                        break
                elif svar[j] == '=':
                    svalue = svar[j+1:]
                    svar = svar[:j]
                    break

        # -- Help --
        if not calc_arg_begun and svar in ("-h", "-help", "--help"):
            sys.stdout.write(HELP_TEXT)
            return 0

        # -- Version --
        elif not calc_arg_begun and svar in ("-v", "-version", "--version"):
            print(VERSION)
            return 0

        # -- Unicode --
        elif not calc_arg_begun and arg == "-u8":
            enable_unicode = 1

        elif not calc_arg_begun and arg == "+u8":
            enable_unicode = 0

        # -- Exchange rates --
        elif not calc_arg_begun and svar in ("-e", "-exrates", "--exrates"):
            fetch_exchange_rates = True

        # -- Base --
        elif not calc_arg_begun and svar in ("-b", "-base", "--base"):
            if not svalue:
                if i + 1 < argc:
                    i += 1
                    svalue = argv[i]
            if svalue:
                set_option_strings.append(f"base {svalue}")

        # -- Color --
        elif not calc_arg_begun and svar in ("-c", "-color", "--color"):
            if svalue:
                try:
                    force_color = int(svalue)
                except ValueError:
                    force_color = 1
            else:
                force_color = 1

        # -- Programming mode --
        elif not calc_arg_begun and svar == "-p":
            programmers_mode = True
            if svalue:
                set_option_strings.append(f"base {svalue} {svalue}")
            elif i + 1 < argc and not argv[i+1].startswith("-"):
                i += 1
                svalue = argv[i]
                set_option_strings.append(f"base {svalue} {svalue}")
            set_option_strings.append("xor^ 1")

        elif not calc_arg_begun and arg == "+p":
            set_option_strings.append("base 10 10")
            set_option_strings.append("xor^ 0")

        # -- Terse --
        elif not calc_arg_begun and svar in ("-t", "-terse", "--terse"):
            result_only = True

        # -- Interactive --
        elif not calc_arg_begun and svar in ("-i", "-interactive", "--interactive"):
            interactive_mode = True

        # -- Defaults --
        elif not calc_arg_begun and svar in ("-defaults", "--defaults"):
            load_defaults = True

        # -- No definitions --
        elif not calc_arg_begun and svar in ("-n", "-nodefs", "--nodefs"):
            load_global_defs = False

        elif not calc_arg_begun and svar in ("-nounits", "--nounits"):
            load_units = False

        elif not calc_arg_begun and svar in ("-nofunctions", "--nofunctions"):
            load_functions = False

        elif not calc_arg_begun and svar in ("-novariables", "--novariables"):
            load_variables = False

        elif not calc_arg_begun and svar in ("-nocurrencies", "--nocurrencies"):
            load_currencies = False

        elif not calc_arg_begun and svar in ("-nodatasets", "--nodatasets"):
            load_datasets = False

        # -- Set option --
        elif not calc_arg_begun and svar in ("-s", "-set", "--set"):
            if not svalue:
                if i + 1 < argc:
                    i += 1
                    svalue = argv[i]
            if svalue:
                set_option_strings.append(svalue)
            else:
                print("No option and value specified for set command.")
                # Enter interactive mode
                interactive_mode = True
                _show_autocalc_prompt()
                return 0

        # -- Time limit --
        elif not calc_arg_begun and svar in ("-m", "-time", "--time"):
            if not svalue:
                if i + 1 < argc:
                    i += 1
                    svalue = argv[i]
            if svalue:
                try:
                    time_limit = max(0, int(svalue))
                except ValueError:
                    time_limit = 0

        # -- List --
        elif not calc_arg_begun and svar in ("-l", "-list", "--list"):
            list_type = '0'
            if svalue:
                search_str = svalue
            elif i + 1 < argc and not argv[i+1].startswith("-") and not argv[i+1].startswith("+"):
                i += 1
                search_str = argv[i]

        elif not calc_arg_begun and svar == "--list-functions":
            list_type = 'f'
            if svalue:
                search_str = svalue
            elif i + 1 < argc and not argv[i+1].startswith("-") and not argv[i+1].startswith("+"):
                i += 1
                search_str = argv[i]

        elif not calc_arg_begun and svar == "--list-units":
            list_type = 'u'
            if svalue:
                search_str = svalue
            elif i + 1 < argc and not argv[i+1].startswith("-") and not argv[i+1].startswith("+"):
                i += 1
                search_str = argv[i]

        elif not calc_arg_begun and svar == "--list-variables":
            list_type = 'v'
            if svalue:
                search_str = svalue
            elif i + 1 < argc and not argv[i+1].startswith("-") and not argv[i+1].startswith("+"):
                i += 1
                search_str = argv[i]

        elif not calc_arg_begun and svar == "--list-prefixes":
            list_type = 'p'
            if svalue:
                search_str = svalue
            elif i + 1 < argc and not argv[i+1].startswith("-") and not argv[i+1].startswith("+"):
                i += 1
                search_str = argv[i]

        # -- File --
        elif not calc_arg_begun and svar in ("-f", "-file", "--file", "--test-file"):
            is_test = svar == "--test-file"
            if not svalue:
                if i + 1 < argc:
                    i += 1
                    svalue = argv[i]
            if svalue:
                command_file = svalue
            else:
                print("No file specified.")
                interactive_mode = True
                _show_autocalc_prompt()
                return 0
            if is_test:
                load_defaults = True
                result_only = True
                unittest = True
                enable_unicode = 0
                interactive_mode = False
                save_defs_on_exit = False
                break

        # -- Double dash separator --
        elif not calc_arg_begun and arg == "--":
            calc_arg_begun = True

        # -- Unrecognized option --
        elif (not calc_arg_begun and expression_after_argc > 0
              and i < expression_after_argc
              and len(arg) > 1
              and (arg[0] == '-' or arg[0] == '+')
              and arg[1] not in "0123456789"):
            print(f"Unrecognized option: {arg}.")

        # -- Expression part --
        else:
            if not calc_arg_begun:
                calc_arg_begun = True
            expression_parts.append(arg)

        i += 1

    # Build the final expression
    calc_arg = " ".join(expression_parts).strip()

    # Determine unicode setting
    use_unicode = enable_unicode == 1 if enable_unicode >= 0 else True

    # Determine color setting (-1 = auto, let interactive mode decide)
    color = force_color if force_color >= 0 else -1

    # ---- Create Calculator ----
    calc = Calculator()

    if load_defaults:
        calc.load_defaults()

    # Apply set options
    for opt in set_option_strings:
        calc.set_option(opt)

    # ---- Handle list commands (need definitions loaded first) ----
    if list_type != 'n':
        if not load_global_defs:
            load_global_defs = True  # list always needs defs
        calc.load_global_definitions(
            load_units=load_units,
            load_functions=load_functions,
            load_variables=load_variables,
            load_datasets=load_datasets,
            load_currencies=load_currencies,
        )
        list_defs(calc, list_type, search_str)
        return 0

    # ---- Load definitions if needed ----
    if load_global_defs and not unittest:
        try:
            calc.load_global_definitions(
                load_units=load_units,
                load_functions=load_functions,
                load_variables=load_variables,
                load_datasets=load_datasets,
                load_currencies=load_currencies,
            )
        except FileNotFoundError:
            pass  # Gracefully handle missing data dir

    # ---- Handle test file ----
    if unittest and command_file:
        if load_global_defs:
            try:
                calc.load_global_definitions(
                    load_units=load_units,
                    load_functions=load_functions,
                    load_variables=load_variables,
                    load_datasets=load_datasets,
                    load_currencies=load_currencies,
                )
            except FileNotFoundError:
                pass
        run_test_file(calc, command_file)
        return 0

    # ---- Handle command file ----
    if command_file and not unittest:
        run_file_commands(calc, command_file, result_only, use_unicode, color)

    # ---- Handle expression ----
    has_expression = bool(calc_arg) or expression_after_argc >= 0
    if has_expression:
        execute_expression(calc, calc_arg, result_only, use_unicode, color)
        if not interactive_mode:
            return 0

    # ---- Interactive mode ----
    if interactive_mode or (not has_expression and not command_file):
        run_interactive(calc, result_only, use_unicode, color)

    return 0


def _show_autocalc_prompt() -> None:
    """Show the autocalc prompt (matches SRC behavior)."""
    sys.stdout.write(
        'Qalc now includes an option (controlled using "set autocalc") to '
        'continuously\ndisplay the result of the current expression as you '
        'type.\nDo you wish to activate this option (default: no)? > '
    )
    sys.stdout.flush()


def main_entry() -> None:
    """Console script entry point."""
    sys.exit(main())


if __name__ == "__main__":
    main_entry()
