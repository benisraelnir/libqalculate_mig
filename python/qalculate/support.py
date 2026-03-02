"""
Internationalization (i18n) support module.

Translated from libqalculate/support.h.
All translation functions are identity/passthrough functions for now.
This preserves call sites for future i18n enablement.
"""


def _(text: str) -> str:
    """Gettext passthrough - returns text unchanged."""
    return text


def _n(singular: str, plural: str, n: int) -> str:
    """Plural-form gettext passthrough."""
    return singular if n == 1 else plural


def _c(context: str, text: str) -> str:
    """Context-based gettext passthrough."""
    return text


def N_(text: str) -> str:
    """Deferred translation marker passthrough."""
    return text
