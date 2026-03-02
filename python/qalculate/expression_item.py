"""
ExpressionItem base class and ExpressionName.

Translated from libqalculate/ExpressionItem.h and ExpressionItem.cc.
ExpressionItem is the abstract base class for all named entities
(variables, functions, units) with name management, categories, descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
from abc import ABC, abstractmethod

from .includes import ExpressionItemType, NUMBERS
from .util import remove_blank_ends, equalsIgnoreCase, text_length_is_one, unicode_length


# ---------------------------------------------------------------------------
# ExpressionName
# ---------------------------------------------------------------------------

@dataclass
class ExpressionName:
    """
    Represents a named expression item with various display/parsing flags.

    When constructed with a name string, automatically detects:
    - abbreviation: single character names
    - unicode: names containing non-ASCII characters
    - suffix: names with underscore-separated suffix (e.g., 'var_x')
    - case_sensitive: abbreviations are case-sensitive
    """
    name: str = ""
    abbreviation: bool = False
    suffix: bool = False
    unicode: bool = False
    plural: bool = False
    reference: bool = False
    avoid_input: bool = False
    case_sensitive: bool = False
    completion_only: bool = False

    def __post_init__(self):
        """Auto-detect properties from name if name was provided and no flags explicitly set."""
        # Only auto-detect if the name was set but properties are at defaults
        # The C++ constructor auto-detects when called with a name string
        pass

    @classmethod
    def from_string(cls, sname: str) -> 'ExpressionName':
        """Create an ExpressionName with auto-detection of properties from the name string."""
        ename = cls(name=sname)

        # Detect unicode
        for ch in sname:
            if ord(ch) >= 0xC0:
                ename.unicode = True
                break

        # Detect abbreviation (single character names)
        if text_length_is_one(sname):
            ename.abbreviation = True
            ename.case_sensitive = True
        else:
            ename.abbreviation = False
            ename.case_sensitive = False

        # Detect suffix (underscore-separated suffix like "var_x")
        if len(sname) > 2:
            i = sname.find('_', 1)
            if i != -1 and i < len(sname) - 1:
                # Check no more underscores after this one
                if sname.find('_', i + 1) == -1:
                    ename.suffix = True
                    if i == 1:
                        ename.abbreviation = True
                        ename.case_sensitive = True

        # Detect trailing digits as suffix
        if not ename.case_sensitive and not ename.suffix:
            for i in range(1, len(sname)):
                # Find first non-continuation-byte character after position 0
                ch = sname[i]
                if ord(ch) > 0 or ord(ch) >= 0xC0:
                    # Check if rest is all digits
                    rest = sname[i:]
                    if rest and all(c in NUMBERS for c in rest):
                        ename.suffix = True
                        ename.abbreviation = True
                        ename.case_sensitive = True
                    break

        return ename

    def formattedName(self, type_val: int = -1, capitalize: bool = False,
                      html_suffix: bool = False, unicode_suffix: int = 0,
                      remove_typename: bool = False, hide_underscore: bool = False) -> str:
        """
        Return a formatted version of the name for display.
        Simplified version - full formatting with Calculator integration
        will be completed in later milestones.
        """
        if len(self.name) < 2:
            return self.name

        result = self.name

        if hide_underscore and '_' in result:
            result = result.replace('_', ' ')

        return result


# Global empty expression name singleton
empty_expression_name = ExpressionName()


# ---------------------------------------------------------------------------
# ExpressionItem (Abstract Base Class)
# ---------------------------------------------------------------------------

class ExpressionItem(ABC):
    """
    Abstract base class for all named entities in qalculate:
    variables, functions, and units.

    Provides name management, metadata (title, description, category),
    status flags, and reference counting.
    """

    def __init__(self, category: str = "", name: str = "",
                 title: str = "", description: str = "",
                 is_local: bool = True, is_builtin: bool = False,
                 is_active: bool = True):
        self._names: List[ExpressionName] = []
        self._title: str = remove_blank_ends(title)
        self._category: str = remove_blank_ends(category)
        self._description: str = description
        self._local: bool = is_local
        self._builtin: bool = is_builtin
        self._changed: bool = False
        self._approximate: bool = False
        self._precision: int = -1
        self._active: bool = is_active
        self._registered: bool = False
        self._hidden: bool = False
        self._destroyed: bool = False
        self._refcount: int = 0
        self._refs: List[ExpressionItem] = []

        name = remove_blank_ends(name)
        if name:
            self._names.append(ExpressionName.from_string(name))

    def set(self, item: 'ExpressionItem') -> None:
        """Copy properties from another ExpressionItem."""
        self._changed = item.hasChanged()
        self._approximate = item.isApproximate()
        self._precision = item.precision()
        self._active = item.isActive()
        for i in range(1, item.countNames() + 1):
            self._names.append(item.getName(i))
        self._title = item.title(return_name_if_no_title=False)
        self._category = item.category()
        self._description = item.description()
        self._local = item.isLocal()
        self._builtin = item.isBuiltin()
        self._hidden = item.isHidden()

    def destroy(self) -> bool:
        """Destroy this item. Returns True if immediately destroyed."""
        if self._refs:
            return False
        if self._refcount > 0:
            self._destroyed = True
        return True

    # ----- Registration -----

    def isRegistered(self) -> bool:
        return self._registered

    def setRegistered(self, is_registered: bool) -> None:
        self._registered = is_registered

    # ----- Title, description, category -----

    def title(self, return_name_if_no_title: bool = True,
              use_unicode: bool = False) -> str:
        """Get title, or name if title is empty and return_name_if_no_title is True."""
        if return_name_if_no_title and not self._title:
            pn = self.preferredName(abbreviation=False, use_unicode=use_unicode)
            return pn.name
        return self._title

    def setTitle(self, title: str) -> None:
        title = remove_blank_ends(title)
        if self._title != title:
            self._title = title
            self._changed = True

    def description(self) -> str:
        return self._description

    def setDescription(self, descr: str) -> None:
        descr = remove_blank_ends(descr)
        if self._description != descr:
            self._description = descr
            self._changed = True

    def category(self) -> str:
        return self._category

    def setCategory(self, cat: str) -> None:
        cat = remove_blank_ends(cat)
        if self._category != cat:
            self._category = cat
            self._changed = True

    # ----- Name management -----

    def name(self, use_unicode: bool = False) -> str:
        """Get the preferred name string."""
        for n in self._names:
            if n.unicode == use_unicode and not n.completion_only:
                return n.name
        if self._names:
            return self._names[0].name
        return ""

    def referenceName(self) -> str:
        """Get the reference name (the stable/canonical name)."""
        for n in self._names:
            if n.reference:
                return n.name
        if self._names:
            return self._names[0].name
        return ""

    def preferredName(self, abbreviation: bool = True, use_unicode: bool = False,
                      plural: bool = False, reference: bool = False,
                      can_display_unicode_fn: Optional[Callable] = None,
                      can_display_unicode_arg: Any = None) -> ExpressionName:
        """Get the preferred name matching the given criteria."""
        if len(self._names) == 1:
            return self._names[0]

        index = -1
        for i, n in enumerate(self._names):
            if (not reference or n.reference) and n.abbreviation == abbreviation \
                    and n.unicode == use_unicode and n.plural == plural \
                    and not n.completion_only:
                return n
            if index < 0:
                index = i
            else:
                curr = self._names[index]
                if n.completion_only != curr.completion_only:
                    if not n.completion_only:
                        index = i
                elif reference and n.reference != curr.reference:
                    if n.reference:
                        index = i
                elif not use_unicode and n.unicode != curr.unicode:
                    if not n.unicode:
                        index = i
                elif n.abbreviation != curr.abbreviation:
                    if n.abbreviation == abbreviation:
                        index = i
                elif n.plural != curr.plural:
                    if n.plural == plural:
                        index = i
                elif use_unicode and n.unicode != curr.unicode:
                    if n.unicode:
                        index = i

        if index >= 0:
            return self._names[index]
        return empty_expression_name

    def preferredInputName(self, abbreviation: bool = True, use_unicode: bool = False,
                           plural: bool = False, reference: bool = False,
                           can_display_unicode_fn: Optional[Callable] = None,
                           can_display_unicode_arg: Any = None) -> ExpressionName:
        """Get the preferred name for input (avoids avoid_input names)."""
        if len(self._names) == 1:
            return self._names[0]

        index = -1
        for i, n in enumerate(self._names):
            if (not reference or n.reference) and n.abbreviation == abbreviation \
                    and n.unicode == use_unicode and n.plural == plural \
                    and not n.avoid_input and not n.completion_only:
                return n
            if index < 0:
                index = i
            else:
                curr = self._names[index]
                if n.completion_only != curr.completion_only:
                    if not n.completion_only:
                        index = i
                elif reference and n.reference != curr.reference:
                    if n.reference:
                        index = i
                elif not use_unicode and n.unicode != curr.unicode:
                    if not n.unicode:
                        index = i
                elif n.avoid_input != curr.avoid_input:
                    if not n.avoid_input:
                        index = i
                elif n.abbreviation != curr.abbreviation:
                    if n.abbreviation == abbreviation:
                        index = i
                elif n.plural != curr.plural:
                    if n.plural == plural:
                        index = i
                elif use_unicode and n.unicode != curr.unicode:
                    if n.unicode:
                        index = i

        if index >= 0:
            return self._names[index]
        return empty_expression_name

    def preferredDisplayName(self, abbreviation: bool = True, use_unicode: bool = False,
                             plural: bool = False, reference: bool = False,
                             can_display_unicode_fn: Optional[Callable] = None,
                             can_display_unicode_arg: Any = None) -> ExpressionName:
        """Get the preferred name for display."""
        return self.preferredName(abbreviation, use_unicode, plural, reference,
                                  can_display_unicode_fn, can_display_unicode_arg)

    def getName(self, index: int) -> ExpressionName:
        """Get name by 1-based index."""
        if 0 < index <= len(self._names):
            return self._names[index - 1]
        return empty_expression_name

    def setName(self, name_or_ename, index: int = 1, force: bool = False) -> None:
        """Set name at 1-based index."""
        if isinstance(name_or_ename, str):
            ename = ExpressionName.from_string(name_or_ename)
        else:
            ename = name_or_ename

        if index < 1:
            self.addName(ename, 1)
            return
        if index > len(self._names):
            self.addName(ename)
            return
        self._names[index - 1] = ename
        self._changed = True

    def addName(self, name_or_ename, index: int = 0, force: bool = False) -> None:
        """Add a name at 1-based index (0 or > len means append)."""
        if isinstance(name_or_ename, str):
            ename = ExpressionName.from_string(name_or_ename)
        else:
            ename = name_or_ename

        if index < 1 or index > len(self._names):
            self._names.append(ename)
        else:
            self._names.insert(index - 1, ename)
        self._changed = True

    def countNames(self) -> int:
        return len(self._names)

    def clearNames(self) -> None:
        if self._names:
            self._names.clear()
            self._changed = True

    def clearNonReferenceNames(self) -> None:
        new_names = [n for n in self._names if n.reference]
        if len(new_names) != len(self._names):
            self._names = new_names
            self._changed = True

    def removeName(self, index: int) -> None:
        """Remove name at 1-based index."""
        if 0 < index <= len(self._names):
            self._names.pop(index - 1)
            self._changed = True

    def hasName(self, sname: str, case_sensitive: bool = False) -> int:
        """
        Check if the item has a name matching sname.
        Returns 1-based index if found, 0 if not.
        """
        for i, n in enumerate(self._names):
            if case_sensitive and n.case_sensitive and sname == n.name:
                return i + 1
            if (not case_sensitive or not n.case_sensitive) and equalsIgnoreCase(n.name, sname):
                return i + 1
        return 0

    def hasNameCaseSensitive(self, sname: str) -> int:
        """Check if the item has a name matching exactly (case-sensitive). Returns 1-based index."""
        for i, n in enumerate(self._names):
            if sname == n.name:
                return i + 1
        return 0

    def findName(self, abbreviation: int = -1, use_unicode: int = -1,
                 plural: int = -1) -> ExpressionName:
        """
        Find a name matching criteria. Use -1 for "don't care".
        Returns matching ExpressionName or empty_expression_name.
        """
        for n in self._names:
            if (abbreviation < 0 or n.abbreviation == bool(abbreviation)) \
                    and (use_unicode < 0 or n.unicode == bool(use_unicode)) \
                    and (plural < 0 or n.plural == bool(plural)):
                return n
        return empty_expression_name

    # ----- Status flags -----

    def isLocal(self) -> bool:
        return self._local

    def setLocal(self, is_local: bool, will_be_active: int = -1) -> bool:
        """Set local status. Simplified version without Calculator integration."""
        if self._builtin:
            return False
        self._local = is_local
        if will_be_active >= 0:
            self.setActive(bool(will_be_active))
        return True

    def isBuiltin(self) -> bool:
        return self._builtin

    def hasChanged(self) -> bool:
        return self._changed

    def setChanged(self, has_changed: bool) -> None:
        self._changed = has_changed

    def isApproximate(self) -> bool:
        return self._approximate

    def setApproximate(self, is_approx: bool = True) -> None:
        if is_approx != self._approximate:
            self._approximate = is_approx
            if not is_approx:
                self._precision = -1
            self._changed = True

    def precision(self) -> int:
        return self._precision

    def setPrecision(self, prec: int) -> None:
        if self._precision != prec:
            self._precision = prec
            if prec >= 0:
                self._approximate = True
            self._changed = True

    def isActive(self) -> bool:
        return self._active

    def setActive(self, is_active: bool) -> None:
        if is_active != self._active:
            self._active = is_active
            self._changed = True

    def isHidden(self) -> bool:
        return self._hidden

    def setHidden(self, is_hidden: bool) -> None:
        if is_hidden != self._hidden:
            self._hidden = is_hidden
            self._changed = True

    # ----- Reference counting -----

    def refcount(self) -> int:
        return self._refcount

    def ref(self, item: Optional['ExpressionItem'] = None) -> None:
        self._refcount += 1
        if item is not None:
            self._refs.append(item)

    def unref(self, item: Optional['ExpressionItem'] = None) -> None:
        if item is not None:
            for i, r in enumerate(self._refs):
                if r is item:
                    self._refcount -= 1
                    self._refs.pop(i)
                    break
        else:
            self._refcount -= 1

    def getReferencer(self, index: int) -> Optional['ExpressionItem']:
        """Get referencer by 1-based index."""
        if 0 < index <= len(self._refs):
            return self._refs[index - 1]
        return None

    def changeReference(self, from_item: 'ExpressionItem',
                        to_item: 'ExpressionItem') -> bool:
        return False

    # ----- Abstract methods -----

    @abstractmethod
    def type(self) -> ExpressionItemType:
        """Return the type of this expression item."""
        ...

    def subtype(self) -> int:
        """Return the subtype of this expression item."""
        return 0

    def id(self) -> int:
        """Return the ID of this expression item."""
        return 0

    @abstractmethod
    def copy(self) -> 'ExpressionItem':
        """Create a copy of this expression item."""
        ...
