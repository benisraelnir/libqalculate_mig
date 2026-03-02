"""
Prefix classes for unit prefixes (metric, binary, and arbitrary number prefixes).

Translated from libqalculate/Prefix.h and Prefix.cc.
Provides the Prefix abstract base class and concrete DecimalPrefix, BinaryPrefix,
and NumberPrefix subclasses for prefix management in the calculator.
"""

from __future__ import annotations

from typing import List, Optional, Callable, Any

from .includes import PrefixType
from .number import Number
from .expression_item import ExpressionName

# Sentinel empty values (mirrors C++ empty_string / empty_expression_name)
_empty_string = ""
_empty_expression_name = ExpressionName()


class Prefix:
    """
    Abstract base class for unit prefixes.

    A prefix is prepended to a unit to specify a quantity multiplier.
    A prefix has a numerical value which, raised to the unit's power,
    defines the effective quantity. For example, in "3 kilometers", kilo is
    a prefix with value 1000, so the result is 3000 meters. If the unit
    were squared, the prefix value would be raised to 2 (1,000,000).

    Prefixes can have up to three different names: a long name, a short name,
    and a short unicode name. The unicode name is an alternative to the short
    name that is preferred when unicode characters can be displayed.
    """

    def __init__(self, long_name: str = "", short_name: str = "",
                 unicode_name: str = "") -> None:
        self._names: List[ExpressionName] = []
        if unicode_name:
            ename = ExpressionName(name=unicode_name)
            ename.abbreviation = True
            ename.unicode = True
            ename.case_sensitive = True
            self._names.append(ename)
        if short_name:
            ename = ExpressionName(name=short_name)
            ename.abbreviation = True
            ename.case_sensitive = True
            self._names.append(ename)
        if long_name:
            ename = ExpressionName(name=long_name)
            ename.abbreviation = False
            ename.case_sensitive = False
            self._names.append(ename)

    # ----- Name accessors -----

    def shortName(self, return_long_if_no_short: bool = True,
                  use_unicode: bool = False) -> str:
        ename = self.preferredName(abbreviation=True, use_unicode=use_unicode)
        if not return_long_if_no_short and not ename.abbreviation:
            return _empty_string
        return ename.name

    def longName(self, return_short_if_no_long: bool = True,
                 use_unicode: bool = False) -> str:
        ename = self.preferredName(abbreviation=False, use_unicode=use_unicode)
        if not return_short_if_no_long and ename.abbreviation:
            return _empty_string
        return ename.name

    def unicodeName(self, return_short_if_no_unicode: bool = True) -> str:
        ename = self.preferredName(abbreviation=True, use_unicode=True)
        if not return_short_if_no_unicode and not ename.unicode:
            return _empty_string
        return ename.name

    def setShortName(self, short_name: str) -> None:
        for i, n in enumerate(self._names):
            if n.abbreviation and not n.unicode:
                if not short_name:
                    self.removeName(i + 1)
                else:
                    self._names[i].name = short_name
                    self._names[i].case_sensitive = True
                return
        if short_name:
            ename = ExpressionName(name=short_name)
            ename.abbreviation = True
            ename.case_sensitive = True
            self.addName(ename)

    def setLongName(self, long_name: str) -> None:
        for i, n in enumerate(self._names):
            if not n.abbreviation:
                if not long_name:
                    self.removeName(i + 1)
                else:
                    self._names[i].name = long_name
                    self._names[i].case_sensitive = False
                return
        if long_name:
            ename = ExpressionName(name=long_name)
            ename.abbreviation = False
            ename.case_sensitive = False
            self.addName(ename)

    def setUnicodeName(self, unicode_name: str) -> None:
        for i, n in enumerate(self._names):
            if n.abbreviation and n.unicode:
                if not unicode_name:
                    self.removeName(i + 1)
                else:
                    self._names[i].name = unicode_name
                    self._names[i].case_sensitive = True
                return
        if unicode_name:
            ename = ExpressionName(name=unicode_name)
            ename.abbreviation = True
            ename.unicode = True
            ename.case_sensitive = True
            self.addName(ename)

    def name(self, short_default: bool = True, use_unicode: bool = False,
             can_display_unicode_string_function: Optional[Callable] = None,
             can_display_unicode_string_arg: Any = None) -> str:
        return self.preferredName(
            short_default, use_unicode, False, False,
            can_display_unicode_string_function,
            can_display_unicode_string_arg
        ).name

    def referenceName(self) -> str:
        for n in self._names:
            if n.reference:
                return n.name
        if self._names:
            return self._names[0].name
        return _empty_string

    # ----- Name selection (preferredName / preferredInputName / preferredDisplayName) -----

    def preferredName(self, abbreviation: bool = False, use_unicode: bool = False,
                      plural: bool = False, reference: bool = False,
                      can_display_unicode_string_function: Optional[Callable] = None,
                      can_display_unicode_string_arg: Any = None) -> ExpressionName:
        if len(self._names) == 1:
            return self._names[0]
        index = -1
        for i, n in enumerate(self._names):
            if ((not reference or n.reference)
                    and n.abbreviation == abbreviation
                    and n.unicode == use_unicode
                    and n.plural == plural
                    and not n.completion_only
                    and (not use_unicode
                         or can_display_unicode_string_function is None
                         or can_display_unicode_string_function(n.name, can_display_unicode_string_arg))):
                return n
            if index < 0:
                index = i
            elif n.completion_only != self._names[index].completion_only:
                if not n.completion_only:
                    index = i
            elif reference and n.reference != self._names[index].reference:
                if n.reference:
                    index = i
            elif not use_unicode and n.unicode != self._names[index].unicode:
                if not n.unicode:
                    index = i
            elif n.abbreviation != self._names[index].abbreviation:
                if n.abbreviation == abbreviation:
                    index = i
            elif n.plural != self._names[index].plural:
                if n.plural == plural:
                    index = i
            elif use_unicode and n.unicode != self._names[index].unicode:
                if n.unicode:
                    index = i

        if (use_unicode and index >= 0 and self._names[index].unicode
                and can_display_unicode_string_function is not None
                and not can_display_unicode_string_function(
                    self._names[index].name, can_display_unicode_string_arg)):
            return self.preferredName(
                abbreviation, False, plural, reference,
                can_display_unicode_string_function,
                can_display_unicode_string_arg)
        if index >= 0:
            return self._names[index]
        return _empty_expression_name

    def preferredInputName(self, abbreviation: bool = False, use_unicode: bool = False,
                           plural: bool = False, reference: bool = False,
                           can_display_unicode_string_function: Optional[Callable] = None,
                           can_display_unicode_string_arg: Any = None) -> ExpressionName:
        if len(self._names) == 1:
            return self._names[0]
        index = -1
        for i, n in enumerate(self._names):
            if ((not reference or n.reference)
                    and n.abbreviation == abbreviation
                    and n.unicode == use_unicode
                    and not n.avoid_input
                    and not n.completion_only):
                return n
            if index < 0:
                index = i
            elif n.completion_only != self._names[index].completion_only:
                if not n.completion_only:
                    index = i
            elif reference and n.reference != self._names[index].reference:
                if n.reference:
                    index = i
            elif not use_unicode and n.unicode != self._names[index].unicode:
                if not n.unicode:
                    index = i
            elif n.avoid_input != self._names[index].avoid_input:
                if not n.avoid_input:
                    index = i
            elif abbreviation and n.abbreviation != self._names[index].abbreviation:
                if n.abbreviation:
                    index = i
            elif plural and n.plural != self._names[index].plural:
                if n.plural:
                    index = i
            elif not abbreviation and n.abbreviation != self._names[index].abbreviation:
                if not n.abbreviation:
                    index = i
            elif not plural and n.plural != self._names[index].plural:
                if not n.plural:
                    index = i
            elif use_unicode and n.unicode != self._names[index].unicode:
                if n.unicode:
                    index = i

        if (use_unicode and index >= 0 and self._names[index].unicode
                and can_display_unicode_string_function is not None
                and not can_display_unicode_string_function(
                    self._names[index].name, can_display_unicode_string_arg)):
            return self.preferredInputName(
                abbreviation, False, plural, reference,
                can_display_unicode_string_function,
                can_display_unicode_string_arg)
        if index >= 0:
            return self._names[index]
        return _empty_expression_name

    def preferredDisplayName(self, abbreviation: bool = False,
                             use_unicode: bool = False,
                             plural: bool = False, reference: bool = False,
                             can_display_unicode_string_function: Optional[Callable] = None,
                             can_display_unicode_string_arg: Any = None) -> ExpressionName:
        return self.preferredName(
            abbreviation, use_unicode, plural, reference,
            can_display_unicode_string_function,
            can_display_unicode_string_arg)

    # ----- Name management -----

    def getName(self, index: int) -> ExpressionName:
        """Return name at 1-based index; returns empty ExpressionName if not found."""
        if 0 < index <= len(self._names):
            return self._names[index - 1]
        return _empty_expression_name

    def setName(self, ename_or_str, index: int = 1) -> None:
        """Set name at 1-based index. If index is out of range, add instead."""
        if isinstance(ename_or_str, str):
            if index < 1:
                self.addName(ename_or_str, 1)
            elif index > len(self._names):
                self.addName(ename_or_str)
            elif self._names[index - 1].name != ename_or_str:
                self._names[index - 1].name = ename_or_str
        else:
            if index < 1:
                self.addName(ename_or_str, 1)
            elif index > len(self._names):
                self.addName(ename_or_str)
            elif self._names[index - 1].name != ename_or_str.name:
                self._names[index - 1] = ename_or_str

    def addName(self, ename_or_str, index: int = 0) -> None:
        """Add a name. index=0 appends; otherwise inserts at 1-based index."""
        if isinstance(ename_or_str, str):
            ename_or_str = ExpressionName(name=ename_or_str)
        if index < 1 or index > len(self._names):
            self._names.append(ename_or_str)
        else:
            self._names.insert(index - 1, ename_or_str)

    def countNames(self) -> int:
        return len(self._names)

    def clearNames(self) -> None:
        self._names.clear()

    def clearNonReferenceNames(self) -> None:
        self._names = [n for n in self._names if n.reference]

    def removeName(self, index: int) -> None:
        """Remove name at 1-based index."""
        if 0 < index <= len(self._names):
            del self._names[index - 1]

    def hasName(self, sname: str, case_sensitive: bool = True) -> int:
        """Return 1-based index of matching name, or 0 if not found."""
        for i, n in enumerate(self._names):
            if case_sensitive and n.case_sensitive:
                if sname == n.name:
                    return i + 1
            else:
                if n.name.lower() == sname.lower():
                    return i + 1
        return 0

    def hasNameCaseSensitive(self, sname: str) -> int:
        """Return 1-based index of exact match, or 0 if not found."""
        for i, n in enumerate(self._names):
            if sname == n.name:
                return i + 1
        return 0

    def findName(self, abbreviation: int = -1, use_unicode: int = -1,
                 plural: int = -1,
                 can_display_unicode_string_function: Optional[Callable] = None,
                 can_display_unicode_string_arg: Any = None) -> ExpressionName:
        for n in self._names:
            if ((abbreviation < 0 or n.abbreviation == bool(abbreviation))
                    and (use_unicode < 0 or n.unicode == bool(use_unicode))
                    and (plural < 0 or n.plural == bool(plural))
                    and (not n.unicode
                         or can_display_unicode_string_function is None
                         or can_display_unicode_string_function(
                             n.name, can_display_unicode_string_arg))):
                return n
        return _empty_expression_name

    # ----- Abstract methods -----

    def value(self, nexp=None) -> Number:
        """Return the value of the prefix, optionally raised to unit exponent.

        Subclasses must implement this.
        """
        raise NotImplementedError

    def type(self) -> int:
        """Return the prefix type (PrefixType enum value)."""
        raise NotImplementedError


class DecimalPrefix(Prefix):
    """
    A decimal (metric) prefix.

    A metric prefix has an integer exponent with base ten:
    value = 10 ^ (exponent * unit_exponent).
    For example, kilo has exponent 3 → value = 10^3 = 1000.
    """

    def __init__(self, exp10: int, long_name: str = "",
                 short_name: str = "", unicode_name: str = "") -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._exp: int = exp10

    def exponent(self, iexp=None) -> 'Number | int':
        """Return the effective exponent (prefix_exp * unit_exp).

        If iexp is a Number, returns a Number. If int or None, returns int.
        """
        if iexp is None:
            return self._exp
        if isinstance(iexp, Number):
            result = Number(iexp)
            result.multiply(Number(self._exp))
            return result
        return self._exp * int(iexp)

    def setExponent(self, iexp: int) -> None:
        self._exp = iexp

    def value(self, nexp=None) -> Number:
        if nexp is None:
            nr = Number(self._exp)
            nr.exp10()
            return nr
        if isinstance(nexp, Number):
            nr = Number(self.exponent(nexp))
            nr.exp10()
            return nr
        # int exponent
        nr = Number(self.exponent(nexp))
        nr.exp10()
        return nr

    def type(self) -> int:
        return PrefixType.DECIMAL


class BinaryPrefix(Prefix):
    """
    A binary prefix.

    A binary prefix has an integer exponent with base two:
    value = 2 ^ (exponent * unit_exponent).
    For example, kibi has exponent 10 → value = 2^10 = 1024.
    """

    def __init__(self, exp2: int, long_name: str = "",
                 short_name: str = "", unicode_name: str = "") -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._exp: int = exp2

    def exponent(self, iexp=None) -> 'Number | int':
        if iexp is None:
            return self._exp
        if isinstance(iexp, Number):
            result = Number(iexp)
            result.multiply(Number(self._exp))
            return result
        return self._exp * int(iexp)

    def setExponent(self, iexp: int) -> None:
        self._exp = iexp

    def value(self, nexp=None) -> Number:
        if nexp is None:
            nr = Number(self._exp)
            nr.exp2()
            return nr
        if isinstance(nexp, Number):
            nr = Number(self.exponent(nexp))
            nr.exp2()
            return nr
        nr = Number(self.exponent(nexp))
        nr.exp2()
        return nr

    def type(self) -> int:
        return PrefixType.BINARY


class NumberPrefix(Prefix):
    """
    A prefix with a free numerical value.

    A prefix without any predefined base, which can use any number.
    value = number ^ unit_exponent.
    """

    def __init__(self, nr: Number, long_name: str = "",
                 short_name: str = "", unicode_name: str = "") -> None:
        super().__init__(long_name, short_name, unicode_name)
        self._number: Number = Number(nr)

    def setValue(self, nr: Number) -> None:
        self._number = Number(nr)

    def value(self, nexp=None) -> Number:
        if nexp is None:
            return Number(self._number)
        nr = Number(self._number)
        if isinstance(nexp, Number):
            nr.raise_(nexp)
        else:
            nr.raise_(Number(nexp))
        return nr

    def type(self) -> int:
        return PrefixType.NUMBER
