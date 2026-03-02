"""
Utility functions for qalculate.

Translated from libqalculate/util.h and util.cc.
Provides string manipulation, path helpers, locale/Unicode helpers,
number-string conversions, and time utilities.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import time
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

from .includes import (
    MathOperation, SPACES, OPERATORS, NUMBERS,
    LEFT_PARENTHESIS_CH, RIGHT_PARENTHESIS_CH,
    LEFT_PARENTHESIS, RIGHT_PARENTHESIS,
    PLUS_CH, MINUS_CH, MULTIPLICATION_CH, DIVISION_CH, POWER_CH, EXP_CH,
    QALCULATE_MAJOR_VERSION, QALCULATE_MINOR_VERSION, QALCULATE_MICRO_VERSION,
)
from .support import _


# ---------------------------------------------------------------------------
# String operations
# ---------------------------------------------------------------------------

def gsub(pattern: str, sub: str, s: str) -> str:
    """Global string substitution (not regex). Replaces all occurrences of pattern with sub."""
    return s.replace(pattern, sub)


def remove_blanks(s: str) -> str:
    """Remove all whitespace characters (spaces, tabs, newlines)."""
    return re.sub(r'[ \t\n]+', '', s)


def remove_duplicate_blanks(s: str) -> str:
    """Collapse consecutive whitespace to single spaces."""
    return re.sub(r'[ \t\n]+', ' ', s)


def remove_blank_ends(s: str) -> str:
    """Strip leading and trailing whitespace."""
    return s.strip()


def remove_parenthesis(s: str) -> str:
    """Recursively remove outer parentheses if they wrap the entire string."""
    while len(s) >= 2 and s[0] == LEFT_PARENTHESIS_CH and s[-1] == RIGHT_PARENTHESIS_CH:
        s = s[1:-1]
    return s


def wrap_p(s: str) -> str:
    """Wrap string in parentheses."""
    return LEFT_PARENTHESIS + s + RIGHT_PARENTHESIS


def is_in(s: str, c: str) -> bool:
    """Check if character c is in string s."""
    return c in s


def is_not_in(s: str, c: str) -> bool:
    """Check if character c is NOT in string s."""
    return c not in s


def sign_place(s: str, start: int = 0) -> int:
    """Find the first operator character in s starting at position start. Returns -1 if not found."""
    for i in range(start, len(s)):
        if s[i] in OPERATORS:
            return i
    return -1


def find_ending_bracket(s: str, start: int, missing: Optional[list] = None) -> int:
    """
    Find the position of the matching closing parenthesis.
    Starts searching from 'start' with an initial depth of 1.
    Returns -1 (equivalent to npos) if not found.
    If 'missing' is a list, sets missing[0] to the remaining unmatched count.
    """
    depth = 1
    pos = start
    while pos < len(s):
        if s[pos] == LEFT_PARENTHESIS_CH:
            depth += 1
        elif s[pos] == RIGHT_PARENTHESIS_CH:
            depth -= 1
            if depth == 0:
                if missing is not None:
                    missing[0] = 0
                return pos
        pos += 1
    if missing is not None:
        missing[0] = depth
    return -1


def op2ch(op: MathOperation) -> str:
    """Convert a MathOperation enum to its character representation."""
    mapping = {
        MathOperation.ADD: PLUS_CH,
        MathOperation.SUBTRACT: MINUS_CH,
        MathOperation.MULTIPLY: MULTIPLICATION_CH,
        MathOperation.DIVIDE: DIVISION_CH,
        MathOperation.RAISE: POWER_CH,
        MathOperation.EXP10: EXP_CH,
    }
    return mapping.get(op, ' ')


# ---------------------------------------------------------------------------
# Number/string conversions
# ---------------------------------------------------------------------------

def d2s(value: float, precision: int = 100) -> str:
    """Double to string conversion."""
    return f"{value:.{precision}G}"


def i2s(value: int) -> str:
    """Integer to string conversion."""
    return str(value)


def u2s(value: int) -> str:
    """Unsigned integer to string conversion."""
    return str(value)


def s2i(s: str) -> int:
    """String to integer conversion. Strips spaces before converting."""
    s = s.strip().replace(' ', '')
    if not s:
        return 0
    try:
        return int(s)
    except ValueError:
        return 0


def b2yn(b: bool, capital: bool = True) -> str:
    """Boolean to Yes/No string."""
    if capital:
        return _("Yes") if b else _("No")
    return _("yes") if b else _("no")


def b2tf(b: bool, capital: bool = True) -> str:
    """Boolean to True/False string."""
    if capital:
        return _("True") if b else _("False")
    return _("true") if b else _("false")


def b2oo(b: bool, capital: bool = True) -> str:
    """Boolean to On/Off string."""
    if capital:
        return _("On") if b else _("Off")
    return _("on") if b else _("off")


# ---------------------------------------------------------------------------
# GCD
# ---------------------------------------------------------------------------

def gcd(i1: int, i2: int) -> int:
    """Greatest common divisor."""
    return math.gcd(abs(i1), abs(i2))


# ---------------------------------------------------------------------------
# Unicode / locale helpers
# ---------------------------------------------------------------------------

def unicode_length(s: str) -> int:
    """Return the number of Unicode characters (code points) in the string."""
    return len(s)


def text_length_is_one(s: str) -> bool:
    """Check if the string contains exactly one Unicode character."""
    return len(s) == 1


def equalsIgnoreCase(s1: str, s2: str) -> bool:
    """Case-insensitive string comparison with Unicode support."""
    if not s1 and not s2:
        return True
    if not s1 or not s2:
        return False
    return s1.casefold() == s2.casefold()


def locale_to_utf8(s: str) -> str:
    """Convert locale-encoded string to UTF-8. In Python, strings are already Unicode."""
    return s


def locale_from_utf8(s: str) -> str:
    """Convert UTF-8 string to locale encoding. In Python, strings are already Unicode."""
    return s


def utf8_strdown(s: str) -> str:
    """Convert UTF-8 string to lowercase."""
    return s.lower()


def utf8_strup(s: str) -> str:
    """Convert UTF-8 string to uppercase."""
    return s.upper()


# ---------------------------------------------------------------------------
# Sub/suffix helpers
# ---------------------------------------------------------------------------

def sub_suffix_html(name: str) -> str:
    """Format a name with its suffix/subscript as HTML."""
    return sub_suffix(name, "<sub>", "</sub>")


def sub_suffix(name: str, tag_begin: str, tag_end: str) -> str:
    """
    Format a name with a subscript suffix.
    If name contains '_', uses the part after it as subscript.
    Otherwise, uses trailing digits or the last Unicode char as subscript.
    """
    if not name:
        return name

    i = name.rfind('_')
    use_fallback = (i == -1 or i == len(name) - 1 or i == 0)

    if use_fallback:
        # Check for trailing digits
        if name[-1] in NUMBERS:
            i2 = len(name) - 1
            while i2 > 0 and name[i2 - 1] in NUMBERS:
                i2 -= 1
            base_part = name[:i2]
            suffix_part = name[i2:]
        else:
            # Use last character
            base_part = name[:-1]
            suffix_part = name[-1:]
    else:
        base_part = name[:i]
        suffix_part = name[i + 1:]

    return base_part + tag_begin + suffix_part + tag_end


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------

def now() -> Tuple[int, int, int]:
    """Return current time as (hour, minute, second)."""
    t = time.localtime()
    return (t.tm_hour, t.tm_min, t.tm_sec)


def sleep_ms(milliseconds: int) -> None:
    """Sleep for the specified number of milliseconds."""
    time.sleep(milliseconds / 1000.0)


# ---------------------------------------------------------------------------
# Path / directory utilities
# ---------------------------------------------------------------------------

def getPackageDataDir() -> str:
    """Get the package data directory (where XML definition files live)."""
    return str(Path(__file__).parent / "data")


def getLocalDir() -> str:
    """Get the local user configuration directory for qalculate."""
    env_dir = os.environ.get("QALCULATE_USER_DIR")
    if env_dir:
        return env_dir

    if os.name == 'nt':
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "Qalculate")

    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return os.path.join(config_home, "qalculate")
    return os.path.join(os.path.expanduser("~"), ".config", "qalculate")


def getOldLocalDir() -> str:
    """Get the old-style local directory (~/.qalculate on Unix)."""
    if os.name == 'nt':
        return os.path.join(os.path.expanduser("~"), "Qalculate")
    return os.path.join(os.path.expanduser("~"), ".qalculate")


def getLocalDataDir() -> str:
    """Get the local data directory for user data."""
    env_dir = os.environ.get("QALCULATE_USER_DIR")
    if env_dir:
        return env_dir

    if os.name == 'nt':
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "Qalculate")

    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        return os.path.join(data_home, "qalculate")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "qalculate")


def getLocalTmpDir() -> str:
    """Get the local temporary/cache directory."""
    env_dir = os.environ.get("QALCULATE_USER_DIR")
    if env_dir:
        return env_dir

    if os.name == 'nt':
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, "cache", "Qalculate")

    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return os.path.join(cache_home, "qalculate")
    return os.path.join(os.path.expanduser("~"), ".cache", "qalculate")


def getGlobalDefinitionsDir() -> str:
    """Get the global definitions directory. Returns the package data dir."""
    return getPackageDataDir()


def getPackageLocaleDir() -> str:
    """Get the locale directory for translations."""
    return os.path.join(str(Path(__file__).parent.parent), "locale")


def buildPath(*parts: str) -> str:
    """Build a file path from components."""
    return os.path.join(*parts)


def dirExists(dirpath: str) -> bool:
    """Check if a directory exists."""
    return os.path.isdir(dirpath)


def fileExists(filepath: str) -> bool:
    """Check if a file or directory exists."""
    return os.path.exists(filepath)


def makeDir(dirpath: str) -> bool:
    """Create a directory. Returns True on success."""
    try:
        os.mkdir(dirpath)
        return True
    except OSError:
        return False


def recursiveMakeDir(dirpath: str) -> bool:
    """Create a directory and all parent directories. Returns True on success."""
    try:
        os.makedirs(dirpath, exist_ok=True)
        return True
    except OSError:
        return False


def removeDir(dirpath: str) -> bool:
    """Remove an empty directory. Returns True on success."""
    try:
        os.rmdir(dirpath)
        return True
    except OSError:
        return False


def move_file(from_file: str, to_file: str) -> bool:
    """Move/rename a file. Returns True on success."""
    try:
        shutil.move(from_file, to_file)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Version parsing
# ---------------------------------------------------------------------------

def parse_qalculate_version(version_string: str) -> list:
    """Parse a version string like '5.9.0' into a list of ints [5, 9, 0]."""
    parts = version_string.split('.')
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return result
