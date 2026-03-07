"""
Loader for libqalculate XML definition files.

Parses functions.xml, units.xml, currencies.xml, variables.xml, and prefixes.xml
to extract definition items with their names, categories, and metadata. These are
used by the CLI list commands and the calculator engine for name resolution.

The XML files use a custom format with <names> elements that encode name properties
via prefix flags. See _parse_name_entry() for the full flag decoding.
"""

from __future__ import annotations

import os
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DefinitionItem:
    """A single parsed definition from the XML data files.

    Attributes:
        name: Primary display name (the first usable non-plural,
              non-avoid_input name found in the <names> element).
        alt_names: Alternative display names (subsequent usable names).
        title: Human-readable title from the <title> element.
        category: Category path, e.g. "Number Theory/Prime Numbers".
        item_type: One of 'function', 'unit', 'variable', 'prefix'.
        is_hidden: True if the element contains <hidden>true</hidden>.
        is_active: True unless all names are marked inactive (leading '-').
        is_currency: True for items loaded from currencies.xml.
        is_composite: True for units with type="composite".
        subtype: Finer classification string. For functions: 'builtin' or
                 'expression'. For units: 'base', 'alias', 'composite', or
                 'builtin'. For variables: 'builtin' or 'expression'. For
                 prefixes: 'decimal' or 'binary'.
    """

    name: str
    alt_names: list[str] = field(default_factory=list)
    title: str = ""
    category: str = ""
    item_type: str = ""
    is_hidden: bool = False
    is_active: bool = True
    is_currency: bool = False
    is_composite: bool = False
    subtype: str = ""


# ---------------------------------------------------------------------------
# Name prefix flag system
# ---------------------------------------------------------------------------
#
# In libqalculate, each comma-separated name in the <names> element can carry
# a prefix of flag letters followed by a colon.  Hyphens in the flag string
# are mere separators (e.g. "a-cr" means flags {a, c, r}).
#
# Flag meanings:
#   a  = abbreviation
#   r  = reference (a primary, look-up-able name)
#   u  = unicode
#   p  = plural
#   s  = suffix / avoid_input
#   o  = case-sensitive only
#   c  = completion-only (when with 'p') or case-resistant
#   i  = avoid_input
#
# A leading '-' before the flags (e.g. "-r:centillion") marks the name as
# inactive.


def _nfkc_dedup(s: str) -> str:
    """Normalize for deduplication: use NFKC for micro sign (µ→μ)
    but preserve distinct Unicode characters like ℃, ℉."""
    # Replace micro sign with Greek mu for deduplication
    result = s.replace("\u00B5", "\u03BC")  # µ → μ
    return result


def _parse_flag_chars(flag_str: str) -> set[str]:
    """Split a flag prefix string into individual flag characters.

    Hyphens are discarded.  Example: "a-cr" -> {'a', 'c', 'r'}.
    """
    return {ch for ch in flag_str if ch != "-"}


def _parse_name_entry(raw: str) -> tuple[str, set[str], bool]:
    """Parse a single name entry from a <names> element.

    Returns (name, flags, is_inactive).
    """
    text = raw.strip()
    if not text:
        return ("", set(), False)

    is_inactive = False
    if text.startswith("-"):
        is_inactive = True
        text = text[1:]

    # Split on the first ':' to separate flags from the actual name.
    # The flag portion must consist only of ASCII letters and hyphens.
    if ":" in text:
        colon_idx = text.index(":")
        candidate_flags = text[:colon_idx]
        if candidate_flags and all(c.isalpha() or c == "-" for c in candidate_flags):
            flags = _parse_flag_chars(candidate_flags)
            name = text[colon_idx + 1:]
            return (name, flags, is_inactive)

    # No recognised flag prefix
    return (text, set(), False)


def _should_skip_name(flags: set[str], name: str = "") -> bool:
    """Return True if the name should be excluded from display lists.

    Excluded categories:
      - Pure plural names (flag 'p' without 'a' or 'r')
      - Avoid-input (flag 'i')
      - Completion-only plurals (flags 'c' and 'p' without 'a' or 'r')
      - Pure case-sensitive-only variants (exactly flag 'o')
      - Abbreviation+suffix names with _digit patterns
    """
    has_a = "a" in flags
    has_r = "r" in flags

    # Plural without abbreviation or reference
    if "p" in flags and not has_a and not has_r:
        return True

    # Avoid-input (flag 'i' only; 's' means suffix, still displayable)
    if "i" in flags:
        return True

    # Completion-only plural
    if "c" in flags and "p" in flags and not has_a and not has_r:
        return True

    # Case-sensitive-only variant (flag 'o'): these are ASCII fallbacks
    # for Unicode names and should be hidden from listings.
    if "o" in flags:
        return True

    # Abbreviation+suffix names with _digit+type_suffix patterns:
    # e.g., a_0unit gets converted to a₀unit which is hidden.
    # But c_1L is kept (the 'L' after digit is just a short label, not a type suffix).
    if has_a and "s" in flags and name:
        for ci in range(len(name) - 1):
            if name[ci] == "_" and name[ci + 1].isdigit():
                j = ci + 1
                while j < len(name) and name[j].isdigit():
                    j += 1
                if j < len(name):
                    trailing = name[j:]
                    # Only skip if trailing text is a known type suffix
                    if trailing.lower() in ("unit", "constant", "variable"):
                        return True

    return False


def _format_display_name(name: str, flags: set[str], item_type: str,
                         item_has_suffix: bool = False) -> str:
    """Format a raw name string for human-readable display.

    Rules:
      - Abbreviation names (flag 'a') are kept verbatim.
      - Function names with underscores: lowerCamelCase.
      - Unit/prefix all-lowercase names with underscores: UpperCamelCase.
      - Variable all-lowercase names: UpperCamelCase only if the item has
        any name with the 's' (suffix) flag. Otherwise verbatim.
      - Mixed-case names (already containing uppercase): verbatim.
    """
    if "a" in flags:
        # For abbreviation+suffix names, convert _digit to subscript
        # e.g., a_0 → a₀, c_1 → c₁
        if "s" in flags and "_" in name:
            import re
            subscripts = str.maketrans("0123456789", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089")
            # Only convert single-digit patterns like _0, _1 (not _220)
            result = re.sub(r'_(\d)$', lambda m: m.group(1).translate(subscripts), name)
            if result != name:
                return result
        return name

    # For suffix-flagged items, convert single trailing digit to subscript
    # (applies to names like exp2 → exp₂, log2 → log₂, but NOT exp10)
    if "s" in flags and name and name[-1].isdigit() and item_type in ("function", "variable"):
        # Only convert if there's exactly one trailing digit
        if len(name) >= 2 and not name[-2].isdigit() and name[-2] != "_":
            subscripts = str.maketrans("0123456789", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089")
            name = name[:-1] + name[-1].translate(subscripts)

    if "_" not in name:
        return name

    parts = name.split("_")

    if item_type == "function":
        # lowerCamelCase: first word unchanged, rest capitalize first letter
        # BUT keep verbatim if first part is a single char (namespace prefix like g_)
        if len(parts[0]) <= 1:
            return name  # Keep g_duration, etc. verbatim
        return parts[0] + "".join(w[0].upper() + w[1:] if w else "" for w in parts[1:])

    if item_type in ("unit", "prefix"):
        # If name starts with lowercase: UpperCamelCase
        # If name starts with uppercase: keep verbatim (already has casing)
        if name[0].islower():
            return "".join(w[0].upper() + w[1:] if w else "" for w in parts)
        return name

    if item_type == "variable":
        # For suffix-flagged items: UpperCamelCase with special cases
        if item_has_suffix:
            last_us = name.rfind("_")
            if last_us >= 0:
                trailing = name[last_us + 1:]
                if trailing.isalpha() and len(trailing) <= 1:
                    return name  # Keep verbatim (e.g., deuteron_u)
                if trailing.isdigit() and len(trailing) == 1:
                    # Single trailing digit: convert to subscript,
                    # keep the base name lowercase (e.g., pauli_0 → pauli₀)
                    subscripts = str.maketrans(
                        "0123456789",
                        "\u2080\u2081\u2082\u2083\u2084"
                        "\u2085\u2086\u2087\u2088\u2089")
                    base = name[:last_us]
                    return base + trailing.translate(subscripts)
            return "".join(w[0].upper() + w[1:] if w else "" for w in parts)
        # For non-suffix items:
        if name != name.lower():
            return name  # Mixed-case names (Hz_to_J): verbatim
        # All-lowercase: UpperCamelCase only if every alphabetic part ≥ 2 chars
        for p in parts:
            if p.isalpha() and len(p) < 2:
                return name  # Has single-letter alphabetic part → verbatim
        return "".join(w[0].upper() + w[1:] if w else "" for w in parts)

    return name


def _parse_names(names_text: str, item_type: str = "") -> tuple[str, list[str]]:
    """Parse a <names> element into (primary_name, alt_names).

    The primary name is selected to match the SRC's
    ``preferredInputName(false, false)`` which prefers non-abbreviated,
    non-unicode reference names.  All other displayable names become
    alternatives.

    Names that are plural-only, avoid_input, completion-only, or pure
    case-sensitive variants are excluded.

    Returns:
        (primary_name, [alt_names]).  primary_name may be "" if no usable
        name was found.
    """
    if not names_text:
        return ("", [])

    # Pre-scan: detect if any name in the item has suffix flag
    item_has_suffix = False
    for raw_part in names_text.split(","):
        _, flags_check, _ = _parse_name_entry(raw_part)
        if "s" in flags_check:
            item_has_suffix = True
            break

    # First pass: collect all usable (display, flags) pairs in order.
    candidates: list[tuple[str, set[str]]] = []
    for raw_part in names_text.split(","):
        name, flags, _inactive = _parse_name_entry(raw_part)
        if not name:
            continue
        if _should_skip_name(flags, name):
            continue
        display = _format_display_name(name, flags, item_type, item_has_suffix)
        candidates.append((display, flags))

    if not candidates:
        return ("", [])

    # Second pass: pick the preferred primary name.
    # Priority: first non-abbreviated, non-unicode name.
    # Fallback: first non-abbreviated name (even if unicode).
    # Fallback: first name overall.
    primary_idx = 0
    for idx, (display, flags) in enumerate(candidates):
        if "a" not in flags and "u" not in flags:
            primary_idx = idx
            break
    # If no non-abbreviated non-unicode name found, use the first name (idx 0)

    primary = candidates[primary_idx][0]
    alts: list[str] = []
    seen = {_nfkc_dedup( primary)}

    # Collect alternates in original order, skipping duplicates.
    for idx, (display, flags) in enumerate(candidates):
        if idx == primary_idx:
            continue
        norm = _nfkc_dedup( display)
        if norm not in seen:
            alts.append(display)
            seen.add(norm)

    return (primary, alts)


def _all_names_inactive(names_text: str) -> bool:
    """Return True if every name in the names string is marked inactive
    (leading '-')."""
    if not names_text:
        return False
    parts = [p.strip() for p in names_text.split(",") if p.strip()]
    if not parts:
        return False
    return all(p.startswith("-") for p in parts)


# ---------------------------------------------------------------------------
# Raw name extraction (for backward-compatible .names field)
# ---------------------------------------------------------------------------


def _parse_names_raw(names_str: str) -> list[str]:
    """Parse a names string into a list of bare name strings with all flag
    prefixes stripped.  This preserves every name (including plurals and
    avoid_input entries) for use in look-up tables.
    """
    if not names_str:
        return []
    result: list[str] = []
    for part in names_str.split(","):
        part = part.strip()
        if not part:
            continue
        cleaned = part
        if cleaned.startswith("-"):
            cleaned = cleaned[1:]
        while ":" in cleaned:
            idx = cleaned.index(":")
            prefix_part = cleaned[:idx]
            if prefix_part and all(c.isalpha() or c == "-" for c in prefix_part):
                cleaned = cleaned[idx + 1:]
            else:
                break
        if cleaned:
            result.append(cleaned)
    return result


# ---------------------------------------------------------------------------
# XML element helpers
# ---------------------------------------------------------------------------


def _clean_title(text: str | None) -> str:
    """Clean a <title> element value.

    Strips the '!'-delimited translation key prefix.
    E.g. "!units!Length" -> "Length".
    """
    if not text:
        return ""
    text = text.strip()
    if text.startswith("!"):
        parts = text.split("!")
        for part in reversed(parts):
            if part:
                return part
    return text


def _elem_text(elem: ET.Element, child_tag: str) -> str:
    """Return the stripped text of a direct child element, or ""."""
    child = elem.find(child_tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _is_hidden(elem: ET.Element) -> bool:
    """Check if an element has <hidden>true</hidden>."""
    return _elem_text(elem, "hidden").lower() == "true"


def _build_category_path(parts: list[str]) -> str:
    """Join non-empty category parts with '/'."""
    return "/".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Functions loader
# ---------------------------------------------------------------------------


def load_functions(data_dir: str) -> list[DefinitionItem]:
    """Load function definitions from ``functions.xml``.

    Args:
        data_dir: Path to the directory containing the XML files.

    Returns:
        A list of :class:`DefinitionItem` for every function found.
    """
    path = Path(data_dir) / "functions.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []
    _walk_function_categories(root, [], items)
    return items


def _walk_function_categories(
    parent: ET.Element,
    category_stack: list[str],
    items: list[DefinitionItem],
) -> None:
    for child in parent:
        if child.tag == "category":
            cat_title = _clean_title(_elem_text(child, "title"))
            new_stack = category_stack + [cat_title] if cat_title else list(category_stack)
            _walk_function_categories(child, new_stack, items)
        elif child.tag in ("builtin_function", "function"):
            item = _parse_function_element(child, category_stack)
            if item is not None:
                items.append(item)


def _parse_function_element(
    elem: ET.Element,
    category_stack: list[str],
) -> DefinitionItem | None:
    names_text = _elem_text(elem, "names")
    title = _clean_title(_elem_text(elem, "title"))
    hidden = _is_hidden(elem)

    subtype = "builtin" if elem.tag == "builtin_function" else "expression"

    primary, alts = _parse_names(names_text, item_type="function")

    if not primary:
        primary = elem.get("name", "")
    if not primary:
        return None

    is_active = True  # Items are active by default; '-' prefix only deactivates the name for input parsing

    return DefinitionItem(
        name=primary,
        alt_names=alts,
        title=title,
        category=_build_category_path(category_stack),
        item_type="function",
        is_hidden=hidden,
        is_active=is_active,
        is_currency=False,
        is_composite=False,
        subtype=subtype,
    )


# ---------------------------------------------------------------------------
# Units loader
# ---------------------------------------------------------------------------


def load_units(data_dir: str) -> list[DefinitionItem]:
    """Load unit definitions from ``units.xml``.

    Args:
        data_dir: Path to the directory containing the XML files.

    Returns:
        A list of :class:`DefinitionItem` for every unit found.
    """
    path = Path(data_dir) / "units.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []
    _walk_unit_categories(root, [], items, is_currency=False)
    return items


def _walk_unit_categories(
    parent: ET.Element,
    category_stack: list[str],
    items: list[DefinitionItem],
    is_currency: bool,
) -> None:
    for child in parent:
        if child.tag == "category":
            cat_title = _clean_title(_elem_text(child, "title"))
            new_stack = category_stack + [cat_title] if cat_title else list(category_stack)
            _walk_unit_categories(child, new_stack, items, is_currency)
        elif child.tag in ("unit", "builtin_unit"):
            item = _parse_unit_element(child, category_stack, is_currency)
            if item is not None:
                items.append(item)


def _parse_unit_element(
    elem: ET.Element,
    category_stack: list[str],
    is_currency: bool,
) -> DefinitionItem | None:
    names_text = _elem_text(elem, "names")
    title = _clean_title(_elem_text(elem, "title"))
    hidden = _is_hidden(elem)

    if elem.tag == "builtin_unit":
        subtype = "builtin"
    else:
        subtype = elem.get("type", "alias")

    is_composite = subtype == "composite"

    primary, alts = _parse_names(names_text, item_type="unit")

    if not primary:
        primary = elem.get("name", "")
    if not primary:
        return None

    is_active = True  # Items are active by default; '-' prefix only deactivates the name for input parsing

    return DefinitionItem(
        name=primary,
        alt_names=alts,
        title=title,
        category=_build_category_path(category_stack),
        item_type="unit",
        is_hidden=hidden,
        is_active=is_active,
        is_currency=is_currency,
        is_composite=is_composite,
        subtype=subtype,
    )


# ---------------------------------------------------------------------------
# Currencies loader
# ---------------------------------------------------------------------------


def load_currencies(data_dir: str) -> list[DefinitionItem]:
    """Load currency definitions from ``currencies.xml``.

    Currencies use the same XML structure as units but are all flagged with
    ``is_currency=True``.

    Args:
        data_dir: Path to the directory containing the XML files.

    Returns:
        A list of :class:`DefinitionItem` for every currency found.
    """
    path = Path(data_dir) / "currencies.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []
    _walk_unit_categories(root, [], items, is_currency=True)
    return items


# ---------------------------------------------------------------------------
# Variables loader
# ---------------------------------------------------------------------------


def load_variables(data_dir: str) -> list[DefinitionItem]:
    """Load variable definitions from ``variables.xml``.

    Args:
        data_dir: Path to the directory containing the XML files.

    Returns:
        A list of :class:`DefinitionItem` for every variable found.
    """
    path = Path(data_dir) / "variables.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []
    _walk_variable_categories(root, [], items)
    return items


def _walk_variable_categories(
    parent: ET.Element,
    category_stack: list[str],
    items: list[DefinitionItem],
) -> None:
    for child in parent:
        if child.tag == "category":
            cat_title = _clean_title(_elem_text(child, "title"))
            new_stack = category_stack + [cat_title] if cat_title else list(category_stack)
            _walk_variable_categories(child, new_stack, items)
        elif child.tag in ("variable", "builtin_variable"):
            item = _parse_variable_element(child, category_stack)
            if item is not None:
                items.append(item)


def _parse_variable_element(
    elem: ET.Element,
    category_stack: list[str],
) -> DefinitionItem | None:
    names_text = _elem_text(elem, "names")
    title = _clean_title(_elem_text(elem, "title"))
    hidden = _is_hidden(elem)

    subtype = "builtin" if elem.tag == "builtin_variable" else "expression"

    primary, alts = _parse_names(names_text, item_type="variable")

    if not primary:
        primary = elem.get("name", "")
    if not primary:
        return None

    is_active = True  # Items are active by default; '-' prefix only deactivates the name for input parsing

    return DefinitionItem(
        name=primary,
        alt_names=alts,
        title=title,
        category=_build_category_path(category_stack),
        item_type="variable",
        is_hidden=hidden,
        is_active=is_active,
        is_currency=False,
        is_composite=False,
        subtype=subtype,
    )


# ---------------------------------------------------------------------------
# Prefixes loader
# ---------------------------------------------------------------------------


def load_prefixes(data_dir: str) -> list[DefinitionItem]:
    """Load prefix definitions from ``prefixes.xml``.

    Prefixes are direct children of the root element (no <category> wrapper).
    Each ``<prefix>`` has a ``type`` attribute (``decimal`` or ``binary``)
    and an ``<exponent>`` child.

    Args:
        data_dir: Path to the directory containing the XML files.

    Returns:
        A list of :class:`DefinitionItem` for every prefix found.
    """
    path = Path(data_dir) / "prefixes.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []

    for child in root:
        if child.tag == "prefix":
            item = _parse_prefix_element(child)
            if item is not None:
                items.append(item)

    return items


def _parse_prefix_element(elem: ET.Element) -> DefinitionItem | None:
    names_text = _elem_text(elem, "names")
    hidden = _is_hidden(elem)

    prefix_type = elem.get("type", "decimal")
    exponent_text = _elem_text(elem, "exponent")

    primary, alts = _parse_names(names_text, item_type="prefix")

    if not primary:
        primary = elem.get("name", "")
    if not primary:
        return None

    # Build a descriptive title, e.g. "kilo (10^3)" or "kibi (2^10)"
    base = "2" if prefix_type == "binary" else "10"
    category = "Binary" if prefix_type == "binary" else "Decimal"
    title_str = f"{primary} ({base}^{exponent_text})" if exponent_text else primary

    return DefinitionItem(
        name=primary,
        alt_names=alts,
        title=title_str,
        category=category,
        item_type="prefix",
        is_hidden=hidden,
        is_active=True,
        is_currency=False,
        is_composite=False,
        subtype=prefix_type,
    )


# ---------------------------------------------------------------------------
# Datasets loader
# ---------------------------------------------------------------------------


def load_datasets(data_dir: str) -> list[DefinitionItem]:
    """Load dataset definitions from ``datasets.xml``."""
    path = Path(data_dir) / "datasets.xml"
    if not path.exists():
        return []
    tree = ET.parse(str(path))
    root = tree.getroot()
    items: list[DefinitionItem] = []
    _walk_dataset_elements(root, items)
    return items


def _walk_dataset_elements(parent: ET.Element, items: list[DefinitionItem]) -> None:
    for child in parent:
        if child.tag == "category":
            _walk_dataset_elements(child, items)
        elif child.tag == "dataset":
            names_text = _elem_text(child, "names")
            title = _clean_title(_elem_text(child, "title"))
            hidden = _is_hidden(child)
            primary, alts = _parse_names(names_text, item_type="function")
            if not primary:
                primary = child.get("name", "")
            if not primary and title:
                primary = title
            if not primary:
                continue
            items.append(DefinitionItem(
                name=primary,
                alt_names=alts,
                title=title,
                category="Data Sets",
                item_type="dataset",
                is_hidden=hidden,
                is_active=True,
                is_currency=False,
                is_composite=False,
                subtype="dataset",
            ))


# ---------------------------------------------------------------------------
# Convenience: load all definitions from a data directory
# ---------------------------------------------------------------------------


def load_all(data_dir: str) -> dict[str, list[DefinitionItem]]:
    """Load all definition files from the given data directory.

    Args:
        data_dir: Path to the directory containing the XML definition files.

    Returns:
        A dict mapping definition type names to lists of DefinitionItem::

            {
                "functions": [...],
                "units": [...],
                "currencies": [...],
                "variables": [...],
                "prefixes": [...],
            }

    Missing XML files are silently skipped (the corresponding list will be
    empty).

    Raises:
        FileNotFoundError: If *data_dir* itself does not exist.
    """
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    return {
        "functions": load_functions(data_dir),
        "units": load_units(data_dir),
        "currencies": load_currencies(data_dir),
        "variables": load_variables(data_dir),
        "prefixes": load_prefixes(data_dir),
    }


# ---------------------------------------------------------------------------
# Formatting helpers for CLI display
# ---------------------------------------------------------------------------


def format_item_names(item: DefinitionItem) -> str:
    """Format an item's names for display in a list.

    Returns a string like ``"primary / alt1 / alt2"``.
    """
    parts = [item.name]
    for alt in item.alt_names:
        if alt not in parts:
            parts.append(alt)
    return " / ".join(parts)


def format_item_display(item: DefinitionItem) -> str:
    """Format an item for a single line of CLI list output.

    Returns a string like ``"name / alt1 / alt2 - Title"``.
    """
    names_str = format_item_names(item)
    if item.title:
        return f"{names_str} - {item.title}"
    return names_str


def filter_visible(items: list[DefinitionItem]) -> list[DefinitionItem]:
    """Return only items that are neither hidden nor inactive."""
    return [item for item in items if not item.is_hidden and item.is_active]
