"""
Arbitrary-precision Number class for qalculate.

Translated from libqalculate/Number.h and Number.cc.
Uses fractions.Fraction for exact rationals and mpmath.mpf/mpc for
floating-point and complex arithmetic.

Design Decision #1: Dual representation approach.
- A NumberType tag (RATIONAL, FLOAT, PLUS_INFINITY, MINUS_INFINITY)
- For RATIONAL: stored as fractions.Fraction in self._rational
- For FLOAT: stored as mpmath.mpf in self._float_val (with optional interval bounds)
- Complex: optional imaginary part as a separate Number object
- Precision tracked via self._precision and self._approximate flags
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Optional, List, Tuple, Union

import mpmath

from .includes import (
    NumberType, IntegerType, ComparisonResult, MathOperation, RoundingMode,
    PrintOptions, BaseDisplay, InternalPrintStruct,
    EQUALS_PRECISION_DEFAULT, EQUALS_PRECISION_LOWEST, EQUALS_PRECISION_HIGHEST,
    DEFAULT_PRECISION,
    default_print_options,
)


def _get_precision() -> int:
    """Get the current working precision in decimal digits."""
    # TODO: When Calculator is implemented, use CALCULATOR.getPrecision()
    return DEFAULT_PRECISION


def _set_mpmath_prec(prec: int = 0) -> None:
    """Set mpmath decimal places from qalculate precision."""
    if prec <= 0:
        prec = _get_precision()
    # Add extra guard digits for intermediate calculations
    mpmath.mp.dps = prec + 10


class Number:
    """
    Arbitrary-precision number supporting rational, float, complex,
    and special values (±infinity).
    """

    __slots__ = (
        '_type', '_rational', '_float_val', '_float_lower', '_float_upper',
        '_imaginary', '_approximate', '_precision', '_is_imag_part',
    )

    def __init__(self, value=None, denom=None, exp10=None, po=None):
        """
        Construct a Number.

        Number()             -> zero
        Number(int)          -> integer
        Number(int, int)     -> rational (num/denom)
        Number(int, int, int) -> num/denom * 10^exp10
        Number(str)          -> parse from string
        Number(Number)       -> copy
        Number(float)        -> approximate float
        Number(Fraction)     -> exact rational
        Number(mpmath.mpf)   -> float
        """
        self._type: NumberType = NumberType.RATIONAL
        self._rational: Fraction = Fraction(0)
        self._float_val: Optional[mpmath.mpf] = None
        self._float_lower: Optional[mpmath.mpf] = None
        self._float_upper: Optional[mpmath.mpf] = None
        self._imaginary: Optional[Number] = None
        self._approximate: bool = False
        self._precision: int = -1
        self._is_imag_part: bool = False

        if value is None:
            return
        elif isinstance(value, Number):
            self._copy_from(value)
        elif isinstance(value, int):
            if denom is not None and exp10 is not None:
                self._rational = Fraction(value, int(denom))
                if exp10 != 0:
                    if exp10 > 0:
                        self._rational *= Fraction(10 ** int(exp10))
                    else:
                        self._rational /= Fraction(10 ** int(-exp10))
            elif denom is not None:
                self._rational = Fraction(value, int(denom))
            else:
                self._rational = Fraction(value)
        elif isinstance(value, float):
            self._type = NumberType.FLOAT
            _set_mpmath_prec()
            self._float_val = mpmath.mpf(value)
            self._approximate = True
        elif isinstance(value, Fraction):
            self._rational = value
        elif isinstance(value, (mpmath.mpf,)):
            self._type = NumberType.FLOAT
            self._float_val = value
            self._approximate = True
        elif isinstance(value, str):
            self._parse_string(value, po)
        else:
            try:
                self._rational = Fraction(value)
            except (ValueError, TypeError):
                pass

    def _copy_from(self, other: 'Number') -> None:
        """Copy all fields from another Number."""
        self._type = other._type
        self._rational = other._rational
        self._float_val = other._float_val
        self._float_lower = other._float_lower
        self._float_upper = other._float_upper
        self._imaginary = Number(other._imaginary) if other._imaginary is not None else None
        self._approximate = other._approximate
        self._precision = other._precision
        self._is_imag_part = other._is_imag_part

    def _parse_string(self, s: str, po=None) -> None:
        """Parse a number from string representation."""
        s = s.strip()
        if not s:
            return

        # Handle special values
        lower = s.lower()
        if lower in ('inf', '+inf', 'infinity', '+infinity'):
            self._type = NumberType.PLUS_INFINITY
            return
        elif lower in ('-inf', '-infinity'):
            self._type = NumberType.MINUS_INFINITY
            return

        # Try parsing as rational (fraction)
        if '/' in s and 'e' not in s.lower():
            parts = s.split('/')
            if len(parts) == 2:
                try:
                    num = int(parts[0].strip())
                    den = int(parts[1].strip())
                    self._rational = Fraction(num, den)
                    return
                except (ValueError, ZeroDivisionError):
                    pass

        # Try parsing as integer
        try:
            self._rational = Fraction(int(s))
            return
        except ValueError:
            pass

        # Try parsing as decimal/scientific notation
        try:
            self._rational = Fraction(s)
            return
        except (ValueError, ZeroDivisionError):
            pass

        # Fall back to mpmath float
        try:
            _set_mpmath_prec()
            self._type = NumberType.FLOAT
            self._float_val = mpmath.mpf(s)
            self._approximate = True
        except (ValueError, TypeError):
            # If all parsing fails, stay as zero
            self._type = NumberType.RATIONAL
            self._rational = Fraction(0)

    # ===================================================================
    # Setters
    # ===================================================================

    def set(self, value=None, denom=None, exp10=None, keep_precision=False, keep_imag=False):
        """Set the value. Overloaded to handle various input types."""
        if isinstance(value, Number):
            old_prec = self._precision
            old_approx = self._approximate
            old_imag = self._imaginary
            self._copy_from(value)
            if keep_precision:
                self._precision = old_prec
                self._approximate = old_approx
            if keep_imag:
                self._imaginary = old_imag
        elif isinstance(value, int):
            if not keep_imag:
                self._imaginary = None
            self._type = NumberType.RATIONAL
            if denom is not None and exp10 is not None:
                self._rational = Fraction(value, int(denom))
                if exp10 != 0:
                    if exp10 > 0:
                        self._rational *= Fraction(10 ** int(exp10))
                    else:
                        self._rational /= Fraction(10 ** int(-exp10))
            elif denom is not None:
                self._rational = Fraction(value, int(denom))
            else:
                self._rational = Fraction(value)
            self._float_val = None
            self._float_lower = None
            self._float_upper = None
            if not keep_precision:
                self._approximate = False
                self._precision = -1
        elif isinstance(value, str):
            self._parse_string(value)

    def setPlusInfinity(self, keep_precision=False, keep_imag=False):
        if not keep_imag:
            self._imaginary = None
        self._type = NumberType.PLUS_INFINITY
        self._rational = Fraction(0)
        self._float_val = None
        if not keep_precision:
            self._approximate = False
            self._precision = -1

    def setMinusInfinity(self, keep_precision=False, keep_imag=False):
        if not keep_imag:
            self._imaginary = None
        self._type = NumberType.MINUS_INFINITY
        self._rational = Fraction(0)
        self._float_val = None
        if not keep_precision:
            self._approximate = False
            self._precision = -1

    def setFloat(self, d_value: float):
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.mpf(d_value)
        self._approximate = True

    def setImaginaryPart(self, value, denom=None, exp10=None):
        if isinstance(value, Number):
            self._imaginary = Number(value)
        else:
            self._imaginary = Number(value, denom, exp10)
        self._imaginary._is_imag_part = True

    def clear(self, keep_precision=False):
        self._type = NumberType.RATIONAL
        self._rational = Fraction(0)
        self._float_val = None
        self._float_lower = None
        self._float_upper = None
        self._imaginary = None
        if not keep_precision:
            self._approximate = False
            self._precision = -1

    def clearReal(self):
        self._type = NumberType.RATIONAL
        self._rational = Fraction(0)
        self._float_val = None

    def clearImaginary(self):
        self._imaginary = None

    # ===================================================================
    # Value conversion to Python native types
    # ===================================================================

    def _to_mpf(self) -> mpmath.mpf:
        """Convert to mpmath.mpf regardless of internal type."""
        _set_mpmath_prec()
        if self._type == NumberType.RATIONAL:
            if self._rational.denominator == 1:
                return mpmath.mpf(int(self._rational))
            return mpmath.mpf(self._rational.numerator) / mpmath.mpf(self._rational.denominator)
        elif self._type == NumberType.FLOAT:
            return self._float_val if self._float_val is not None else mpmath.mpf(0)
        elif self._type == NumberType.PLUS_INFINITY:
            return mpmath.inf
        elif self._type == NumberType.MINUS_INFINITY:
            return -mpmath.inf
        return mpmath.mpf(0)

    def _to_fraction(self) -> Fraction:
        """Convert to Fraction (only meaningful for rationals)."""
        if self._type == NumberType.RATIONAL:
            return self._rational
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            return Fraction(float(self._float_val))
        return Fraction(0)

    def _promote_to_float(self) -> None:
        """Promote rational to float representation."""
        if self._type == NumberType.RATIONAL:
            _set_mpmath_prec()
            self._float_val = self._to_mpf()
            self._type = NumberType.FLOAT

    def floatValue(self) -> float:
        return float(self._to_mpf())

    def intValue(self) -> int:
        if self._type == NumberType.RATIONAL:
            return int(self._rational)
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            return int(self._float_val)
        return 0

    def lintValue(self) -> int:
        return self.intValue()

    def llintValue(self) -> int:
        return self.intValue()

    def uintValue(self) -> int:
        v = self.intValue()
        return max(0, v)

    def ulintValue(self) -> int:
        return self.uintValue()

    # ===================================================================
    # Approximation / Precision
    # ===================================================================

    def isApproximate(self) -> bool:
        return self._approximate

    def isFloatingPoint(self) -> bool:
        return self._type == NumberType.FLOAT

    def isInterval(self, ignore_imag=True) -> bool:
        if self._float_lower is not None and self._float_upper is not None:
            return True
        if not ignore_imag and self._imaginary is not None:
            return self._imaginary.isInterval()
        return False

    def setApproximate(self, is_approximate=True):
        self._approximate = is_approximate
        if not is_approximate:
            self._precision = -1

    def precision(self, calculate_from_interval=0) -> int:
        return self._precision

    def setPrecision(self, prec: int):
        self._precision = prec
        if prec >= 0:
            self._approximate = True

    def setPrecisionAndApproximateFrom(self, other: 'Number'):
        if other._approximate and (not self._approximate or (other._precision >= 0 and (self._precision < 0 or other._precision < self._precision))):
            self._approximate = True
            if other._precision >= 0 and (self._precision < 0 or other._precision < self._precision):
                self._precision = other._precision

    # ===================================================================
    # Type / Value queries
    # ===================================================================

    def isUndefined(self) -> bool:
        return False  # We don't have NaN representation yet

    def isInfinite(self, ignore_imag=True) -> bool:
        if self._type in (NumberType.PLUS_INFINITY, NumberType.MINUS_INFINITY):
            return True
        if not ignore_imag and self._imaginary is not None:
            return self._imaginary.isInfinite()
        return False

    def isPlusInfinity(self, ignore_imag=False) -> bool:
        if ignore_imag:
            return self._type == NumberType.PLUS_INFINITY and not self.hasImaginaryPart()
        return self._type == NumberType.PLUS_INFINITY

    def isMinusInfinity(self, ignore_imag=False) -> bool:
        if ignore_imag:
            return self._type == NumberType.MINUS_INFINITY and not self.hasImaginaryPart()
        return self._type == NumberType.MINUS_INFINITY

    def hasRealPart(self) -> bool:
        if self._type in (NumberType.PLUS_INFINITY, NumberType.MINUS_INFINITY):
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational != 0
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val != 0
        return False

    def hasImaginaryPart(self) -> bool:
        return self._imaginary is not None and self._imaginary.isNonZero()

    def isComplex(self) -> bool:
        return self.hasImaginaryPart()

    def isInteger(self, integer_type: IntegerType = IntegerType.NONE) -> bool:
        if self._type != NumberType.RATIONAL:
            return False
        if self._imaginary is not None and self._imaginary.isNonZero():
            return False
        return self._rational.denominator == 1

    def isRational(self) -> bool:
        if self._type != NumberType.RATIONAL:
            return False
        if self._imaginary is not None and self._imaginary.isNonZero():
            return False
        return True

    def isReal(self) -> bool:
        if self._type in (NumberType.PLUS_INFINITY, NumberType.MINUS_INFINITY):
            return True
        if self._imaginary is not None and self._imaginary.isNonZero():
            return False
        return True

    def isNonInteger(self) -> bool:
        if self._type != NumberType.RATIONAL:
            return False
        return self._rational.denominator != 1

    def isFraction(self) -> bool:
        return self.isNonInteger()

    def isZero(self) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational == 0 and (self._imaginary is None or self._imaginary.isZero())
        if self._type == NumberType.FLOAT:
            return (self._float_val is not None and self._float_val == 0 and
                    (self._imaginary is None or self._imaginary.isZero()))
        return False

    def isNonZero(self) -> bool:
        if self._type in (NumberType.PLUS_INFINITY, NumberType.MINUS_INFINITY):
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational != 0 or (self._imaginary is not None and self._imaginary.isNonZero())
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val != 0 or (self._imaginary is not None and self._imaginary.isNonZero())
        return False

    def isOne(self) -> bool:
        if self.hasImaginaryPart():
            return False
        if self._type == NumberType.RATIONAL:
            return self._rational == 1
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val == 1
        return False

    def isTwo(self) -> bool:
        if self.hasImaginaryPart():
            return False
        if self._type == NumberType.RATIONAL:
            return self._rational == 2
        return False

    def isMinusOne(self) -> bool:
        if self.hasImaginaryPart():
            return False
        if self._type == NumberType.RATIONAL:
            return self._rational == -1
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val == -1
        return False

    def isI(self) -> bool:
        if self._imaginary is None or not self._imaginary.isOne():
            return False
        return not self.hasRealPart()

    def isMinusI(self) -> bool:
        if self._imaginary is None or not self._imaginary.isMinusOne():
            return False
        return not self.hasRealPart()

    def isNegative(self) -> bool:
        if self._type == NumberType.MINUS_INFINITY:
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational < 0
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val < 0
        return False

    def isNonNegative(self) -> bool:
        if self._type == NumberType.PLUS_INFINITY:
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational >= 0
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val >= 0
        return False

    def isPositive(self) -> bool:
        if self._type == NumberType.PLUS_INFINITY:
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational > 0
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val > 0
        return False

    def isNonPositive(self) -> bool:
        if self._type == NumberType.MINUS_INFINITY:
            return True
        if self._type == NumberType.RATIONAL:
            return self._rational <= 0
        if self._type == NumberType.FLOAT and self._float_val is not None:
            return self._float_val <= 0
        return False

    def realPartIsNegative(self) -> bool:
        return self.isNegative()

    def realPartIsNonNegative(self) -> bool:
        return self.isNonNegative()

    def realPartIsPositive(self) -> bool:
        return self.isPositive()

    def realPartIsNonZero(self) -> bool:
        return self.hasRealPart()

    def realPartIsRational(self) -> bool:
        return self._type == NumberType.RATIONAL

    def imaginaryPartIsNegative(self) -> bool:
        return self._imaginary is not None and self._imaginary.isNegative()

    def imaginaryPartIsPositive(self) -> bool:
        return self._imaginary is not None and self._imaginary.isPositive()

    def imaginaryPartIsNonNegative(self) -> bool:
        return self._imaginary is None or self._imaginary.isNonNegative()

    def imaginaryPartIsNonPositive(self) -> bool:
        return self._imaginary is None or self._imaginary.isNonPositive()

    def imaginaryPartIsNonZero(self) -> bool:
        return self._imaginary is not None and self._imaginary.isNonZero()

    def hasNegativeSign(self) -> bool:
        if self.hasRealPart():
            return self.isNegative()
        return self.imaginaryPartIsNegative()

    def hasPositiveSign(self) -> bool:
        if self.hasRealPart():
            return self.isPositive()
        return self.imaginaryPartIsPositive()

    def isEven(self) -> bool:
        if not self.isInteger():
            return False
        return int(self._rational) % 2 == 0

    def isOdd(self) -> bool:
        if not self.isInteger():
            return False
        return int(self._rational) % 2 != 0

    def isPerfectSquare(self) -> bool:
        if not self.isInteger() or self.isNegative():
            return False
        n = int(self._rational)
        root = math.isqrt(n)
        return root * root == n

    # ===================================================================
    # Part extraction
    # ===================================================================

    def realPart(self) -> 'Number':
        result = Number(self)
        result._imaginary = None
        return result

    def imaginaryPart(self) -> 'Number':
        if self._imaginary is not None:
            result = Number(self._imaginary)
            result._is_imag_part = False
            return result
        return Number()

    def numerator(self) -> 'Number':
        if self._type == NumberType.RATIONAL:
            return Number(int(self._rational.numerator))
        return Number(self)

    def denominator(self) -> 'Number':
        if self._type == NumberType.RATIONAL:
            return Number(int(self._rational.denominator))
        return Number(1)

    def integer(self) -> 'Number':
        """Return the integer part (truncate toward zero)."""
        if self._type == NumberType.RATIONAL:
            return Number(int(self._rational))
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            return Number(int(self._float_val))
        return Number(self)

    def lowerEndPoint(self, include_imag=False) -> 'Number':
        return Number(self)

    def upperEndPoint(self, include_imag=False) -> 'Number':
        return Number(self)

    # ===================================================================
    # Comparison
    # ===================================================================

    def equals(self, other, allow_interval=False, allow_infinite=False) -> bool:
        if isinstance(other, int):
            if self.hasImaginaryPart():
                return False
            if self._type == NumberType.RATIONAL:
                return self._rational == other
            if self._type == NumberType.FLOAT and self._float_val is not None:
                return self._float_val == other
            return False
        if not isinstance(other, Number):
            return False
        # Check imaginary parts
        if self.hasImaginaryPart() != other.hasImaginaryPart():
            return False
        if self.hasImaginaryPart() and not self._imaginary.equals(other._imaginary):
            return False
        # Check real parts
        if self._type != other._type:
            if not allow_infinite:
                if self.isInfinite() or other.isInfinite():
                    return False
            # Compare cross-type
            return self._to_mpf() == other._to_mpf()
        if self._type == NumberType.RATIONAL:
            return self._rational == other._rational
        elif self._type == NumberType.FLOAT:
            if self._float_val is not None and other._float_val is not None:
                return self._float_val == other._float_val
        elif self._type in (NumberType.PLUS_INFINITY, NumberType.MINUS_INFINITY):
            return allow_infinite
        return False

    def compare(self, other, ignore_imag=False) -> ComparisonResult:
        """Compare this number with other. Returns ComparisonResult."""
        if isinstance(other, int):
            other = Number(other)
        if not ignore_imag:
            if self.hasImaginaryPart() or other.hasImaginaryPart():
                return ComparisonResult.UNKNOWN
        if self.isInfinite() or other.isInfinite():
            if self._type == other._type:
                return ComparisonResult.EQUAL
            if self._type == NumberType.PLUS_INFINITY:
                return ComparisonResult.GREATER
            if self._type == NumberType.MINUS_INFINITY:
                return ComparisonResult.LESS
            if other._type == NumberType.PLUS_INFINITY:
                return ComparisonResult.LESS
            if other._type == NumberType.MINUS_INFINITY:
                return ComparisonResult.GREATER
        a = self._to_mpf()
        b = other._to_mpf()
        if a == b:
            return ComparisonResult.EQUAL
        elif a > b:
            return ComparisonResult.GREATER
        else:
            return ComparisonResult.LESS

    def isGreaterThan(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.compare(other) == ComparisonResult.GREATER

    def isLessThan(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        return self.compare(other) == ComparisonResult.LESS

    def isGreaterThanOrEqualTo(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        c = self.compare(other)
        return c in (ComparisonResult.GREATER, ComparisonResult.EQUAL)

    def isLessThanOrEqualTo(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        c = self.compare(other)
        return c in (ComparisonResult.LESS, ComparisonResult.EQUAL)

    # Numerator/denominator comparison helpers
    def numeratorEquals(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.numerator == i
        return False

    def numeratorIsGreaterThan(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.numerator > i
        return False

    def numeratorIsLessThan(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.numerator < i
        return False

    def denominatorEquals(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.denominator == i
        return False

    def denominatorIsGreaterThan(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.denominator > i
        return False

    def denominatorIsLessThan(self, i: int) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.denominator < i
        return False

    def denominatorIsEven(self) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.denominator % 2 == 0
        return False

    def denominatorIsTwo(self) -> bool:
        return self.denominatorEquals(2)

    def numeratorIsEven(self) -> bool:
        if self._type == NumberType.RATIONAL:
            return self._rational.numerator % 2 == 0
        return False

    def numeratorIsOne(self) -> bool:
        return self.numeratorEquals(1)

    def numeratorIsMinusOne(self) -> bool:
        return self.numeratorEquals(-1)

    # ===================================================================
    # Basic arithmetic (mutating methods)
    # ===================================================================

    def _result_approx(self, other: 'Number') -> None:
        """Propagate approximate flag from other."""
        self.setPrecisionAndApproximateFrom(other)

    def add(self, other, op=None) -> bool:
        """Add other to self (in-place). With op, dispatch to operation."""
        if isinstance(other, int):
            other = Number(other)
        if op is not None:
            return self._do_operation(other, op)
        # Handle infinities
        if self.isInfinite() and other.isInfinite():
            if self._type != other._type:
                self.clear()
                return False  # indeterminate
            return True
        if other.isInfinite():
            self._type = other._type
            self._rational = Fraction(0)
            self._float_val = None
            self._result_approx(other)
            return True
        if self.isInfinite():
            return True
        # Handle imaginary parts
        if other.hasImaginaryPart():
            if self._imaginary is None:
                self._imaginary = Number()
            self._imaginary.add(other._imaginary)
        # Real part addition
        if self._type == NumberType.RATIONAL and other._type == NumberType.RATIONAL:
            self._rational += other._rational
        else:
            self._promote_to_float()
            self._float_val = self._to_mpf() + other._to_mpf()
            self._type = NumberType.FLOAT
        self._result_approx(other)
        return True

    def subtract(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        neg = Number(other)
        neg.negate()
        return self.add(neg)

    def multiply(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        # Handle infinities
        if self.isInfinite() or other.isInfinite():
            if self.isZero() or other.isZero():
                self.clear()
                return False  # indeterminate 0*inf
            s_neg = self.hasNegativeSign()
            o_neg = other.hasNegativeSign()
            if s_neg != o_neg:
                self.setMinusInfinity()
            else:
                self.setPlusInfinity()
            return True
        # Complex multiplication: (a+bi)(c+di) = (ac-bd) + (ad+bc)i
        if self.hasImaginaryPart() or other.hasImaginaryPart():
            a = self.realPart()
            b = self.imaginaryPart()
            c = other.realPart()
            d = other.imaginaryPart()
            # real = ac - bd
            ac = Number(a); ac.multiply(c)
            bd = Number(b); bd.multiply(d)
            real = Number(ac); real.subtract(bd)
            # imag = ad + bc
            ad = Number(a); ad.multiply(d)
            bc = Number(b); bc.multiply(c)
            imag = Number(ad); imag.add(bc)
            self._copy_from(real)
            if imag.isNonZero():
                self._imaginary = imag
            else:
                self._imaginary = None
            return True
        # Real multiplication
        if self._type == NumberType.RATIONAL and other._type == NumberType.RATIONAL:
            self._rational *= other._rational
        else:
            self._float_val = self._to_mpf() * other._to_mpf()
            self._type = NumberType.FLOAT
        self._result_approx(other)
        return True

    def divide(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if other.isZero():
            return False
        if self.isZero():
            return True
        # Handle infinities
        if self.isInfinite() and other.isInfinite():
            self.clear()
            return False  # indeterminate
        if other.isInfinite():
            self.clear()
            self._result_approx(other)
            return True
        if self.isInfinite():
            if other.isNegative():
                if self._type == NumberType.PLUS_INFINITY:
                    self._type = NumberType.MINUS_INFINITY
                else:
                    self._type = NumberType.PLUS_INFINITY
            return True
        # Complex division
        if self.hasImaginaryPart() or other.hasImaginaryPart():
            # (a+bi)/(c+di) = ((ac+bd) + (bc-ad)i) / (c^2+d^2)
            a = self.realPart()
            b = self.imaginaryPart()
            c = other.realPart()
            d = other.imaginaryPart()
            denom = Number(c); denom.multiply(c)
            d2 = Number(d); d2.multiply(d)
            denom.add(d2)
            ac = Number(a); ac.multiply(c)
            bd = Number(b); bd.multiply(d)
            real = Number(ac); real.add(bd); real.divide(denom)
            bc = Number(b); bc.multiply(c)
            ad = Number(a); ad.multiply(d)
            imag = Number(bc); imag.subtract(ad); imag.divide(denom)
            self._copy_from(real)
            if imag.isNonZero():
                self._imaginary = imag
            else:
                self._imaginary = None
            return True
        # Real division
        if self._type == NumberType.RATIONAL and other._type == NumberType.RATIONAL:
            self._rational /= other._rational
        else:
            oval = other._to_mpf()
            if oval == 0:
                return False
            self._float_val = self._to_mpf() / oval
            self._type = NumberType.FLOAT
        self._result_approx(other)
        return True

    def recip(self) -> bool:
        """Set to 1/self."""
        if self.isZero():
            return False
        one = Number(1)
        one.divide(self)
        self._copy_from(one)
        return True

    def negate(self) -> bool:
        if self._type == NumberType.RATIONAL:
            self._rational = -self._rational
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            self._float_val = -self._float_val
        elif self._type == NumberType.PLUS_INFINITY:
            self._type = NumberType.MINUS_INFINITY
        elif self._type == NumberType.MINUS_INFINITY:
            self._type = NumberType.PLUS_INFINITY
        if self._imaginary is not None:
            self._imaginary.negate()
        return True

    def setNegative(self, is_negative: bool):
        if is_negative and self.isPositive():
            self.negate()
        elif not is_negative and self.isNegative():
            self.negate()

    def abs(self) -> bool:
        if self.hasImaginaryPart():
            # |a+bi| = sqrt(a^2 + b^2)
            a = self.realPart()
            b = self.imaginaryPart()
            a.square(); b.square()
            a.add(b)
            a.sqrt()
            self._copy_from(a)
            return True
        if self.isNegative():
            self.negate()
        return True

    def signum(self) -> bool:
        if self.isZero():
            return True
        if self.isPositive():
            self.set(1)
        elif self.isNegative():
            self.set(-1)
        return True

    def square(self) -> bool:
        return self.multiply(Number(self))

    # ===================================================================
    # Powers and roots
    # ===================================================================

    def raise_(self, other, try_exact=True) -> bool:
        """Raise self to the power of other. Named raise_ to avoid Python keyword."""
        if isinstance(other, int):
            other = Number(other)
        if other.isZero():
            self.set(1)
            return True
        if self.isZero():
            if other.isNegative():
                return False  # 0^(-n)
            return True  # 0^n = 0
        if other.isOne():
            return True
        if self.isOne():
            return True
        # Integer exponents for rationals
        if other.isInteger() and self._type == NumberType.RATIONAL and not self.hasImaginaryPart():
            exp = int(other._rational)
            if abs(exp) < 10000:  # Reasonable limit
                self._rational = self._rational ** exp
                self._result_approx(other)
                return True
        # General case: use mpmath
        _set_mpmath_prec()
        if self.hasImaginaryPart():
            a = self._to_mpf()
            b = self.imaginaryPart()._to_mpf()
            base = mpmath.mpc(a, b)
        else:
            base = self._to_mpf()
        if other.hasImaginaryPart():
            c = other._to_mpf()
            d = other.imaginaryPart()._to_mpf()
            exp = mpmath.mpc(c, d)
        else:
            exp = other._to_mpf()
        try:
            result = mpmath.power(base, exp)
        except (ValueError, ZeroDivisionError):
            return False
        if isinstance(result, mpmath.mpc):
            if abs(result.imag) < mpmath.mpf(10) ** (-mpmath.mp.dps + 5):
                self._type = NumberType.FLOAT
                self._float_val = result.real
                self._imaginary = None
            else:
                self._type = NumberType.FLOAT
                self._float_val = result.real
                self._imaginary = Number()
                self._imaginary._type = NumberType.FLOAT
                self._imaginary._float_val = result.imag
                self._imaginary._approximate = True
        else:
            self._type = NumberType.FLOAT
            self._float_val = mpmath.mpf(result)
            self._imaginary = None
        self._approximate = True
        self._result_approx(other)
        return True

    # Alias for raise_ since C++ uses raise()
    def power(self, other, try_exact=True) -> bool:
        return self.raise_(other, try_exact)

    def sqrt(self) -> bool:
        if self.isZero():
            return True
        if self.isNegative() and not self.hasImaginaryPart():
            # sqrt of negative: result is imaginary
            self.negate()
            self.sqrt()
            imag = Number(self)
            self.clear()
            self._imaginary = imag
            return True
        _set_mpmath_prec()
        if self._type == NumberType.RATIONAL and not self.hasImaginaryPart():
            # Check for perfect square
            num = self._rational.numerator
            den = self._rational.denominator
            sn = math.isqrt(num)
            sd = math.isqrt(den)
            if sn * sn == num and sd * sd == den:
                self._rational = Fraction(sn, sd)
                return True
        # Fall back to mpmath
        self._float_val = mpmath.sqrt(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def cbrt(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.cbrt(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def root(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        _set_mpmath_prec()
        self._float_val = mpmath.root(self._to_mpf(), other._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def exp(self) -> bool:
        """e^self"""
        _set_mpmath_prec()
        self._float_val = mpmath.exp(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def exp2_func(self) -> bool:
        """2^self"""
        _set_mpmath_prec()
        self._float_val = mpmath.power(2, self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def exp10_func(self) -> bool:
        """10^self"""
        _set_mpmath_prec()
        self._float_val = mpmath.power(10, self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def exp10(self, other=None) -> bool:
        """If other given: self *= 10^other. If not: self = 10^self."""
        if other is None:
            return self.exp10_func()
        if isinstance(other, int):
            other = Number(other)
        ten_pow = Number(10)
        ten_pow.raise_(other)
        return self.multiply(ten_pow)

    def exp2(self, other=None) -> bool:
        if other is None:
            return self.exp2_func()
        if isinstance(other, int):
            other = Number(other)
        two_pow = Number(2)
        two_pow.raise_(other)
        return self.multiply(two_pow)

    # ===================================================================
    # Modular arithmetic / Rounding
    # ===================================================================

    def mod(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if other.isZero():
            return False
        if self._type == NumberType.RATIONAL and other._type == NumberType.RATIONAL:
            # Python modulo
            self._rational = self._rational % other._rational
        else:
            _set_mpmath_prec()
            self._float_val = mpmath.fmod(self._to_mpf(), other._to_mpf())
            self._type = NumberType.FLOAT
        self._result_approx(other)
        return True

    def rem(self, other) -> bool:
        return self.mod(other)

    def irem(self, other, quotient=None) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if not self.isInteger() or not other.isInteger() or other.isZero():
            return False
        a = int(self._rational)
        b = int(other._rational)
        if quotient is not None:
            q, r = divmod(a, b)
            quotient.set(q)
            self.set(r)
        else:
            self.set(a % b)
        return True

    def iquo(self, other, remainder=None) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if not self.isInteger() or not other.isInteger() or other.isZero():
            return False
        a = int(self._rational)
        b = int(other._rational)
        if remainder is not None:
            q, r = divmod(a, b)
            remainder.set(r)
            self.set(q)
        else:
            self.set(a // b)
        return True

    def smod(self, other) -> bool:
        """Symmetric modulo."""
        if isinstance(other, int):
            other = Number(other)
        if not self.isInteger() or not other.isInteger() or other.isZero():
            return False
        a = int(self._rational)
        b = int(other._rational)
        r = a % b
        if r > b // 2:
            r -= b
        self.set(r)
        return True

    def isIntegerDivisible(self, other) -> bool:
        if not self.isInteger() or not other.isInteger() or other.isZero():
            return False
        return int(self._rational) % int(other._rational) == 0

    def round(self, mode_or_other=None, halfway_to_even=True) -> bool:
        if isinstance(mode_or_other, Number):
            # round(self / other) * other
            if mode_or_other.isZero():
                return False
            temp = Number(self)
            temp.divide(mode_or_other)
            temp.round()
            temp.multiply(mode_or_other)
            self._copy_from(temp)
            return True
        if isinstance(mode_or_other, RoundingMode):
            # TODO: implement various rounding modes
            pass
        # Default: round to nearest integer
        if self._type == NumberType.RATIONAL:
            self._rational = Fraction(round(self._rational))
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            self._float_val = mpmath.nint(self._float_val)
        return True

    def floor(self, other=None) -> bool:
        if isinstance(other, Number):
            if other.isZero():
                return False
            temp = Number(self)
            temp.divide(other)
            temp.floor()
            temp.multiply(other)
            self._copy_from(temp)
            return True
        if self._type == NumberType.RATIONAL:
            self._rational = Fraction(math.floor(self._rational))
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            self._float_val = mpmath.floor(self._float_val)
        return True

    def ceil(self, other=None) -> bool:
        if isinstance(other, Number):
            if other.isZero():
                return False
            temp = Number(self)
            temp.divide(other)
            temp.ceil()
            temp.multiply(other)
            self._copy_from(temp)
            return True
        if self._type == NumberType.RATIONAL:
            self._rational = Fraction(math.ceil(self._rational))
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            self._float_val = mpmath.ceil(self._float_val)
        return True

    def trunc(self, other=None) -> bool:
        if isinstance(other, Number):
            if other.isZero():
                return False
            temp = Number(self)
            temp.divide(other)
            temp.trunc()
            temp.multiply(other)
            self._copy_from(temp)
            return True
        if self._type == NumberType.RATIONAL:
            self._rational = Fraction(int(self._rational))
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            self._float_val = mpmath.mpf(int(self._float_val))
        return True

    def frac(self) -> bool:
        """Fractional part: self - trunc(self)"""
        int_part = Number(self)
        int_part.trunc()
        self.subtract(int_part)
        return True

    def isqrt(self) -> bool:
        """Integer square root."""
        if not self.isInteger() or self.isNegative():
            return False
        self.set(math.isqrt(int(self._rational)))
        return True

    # ===================================================================
    # Bitwise operations
    # ===================================================================

    def bitAnd(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(int(self._rational) & int(other._rational))
        return True

    def bitOr(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(int(self._rational) | int(other._rational))
        return True

    def bitXor(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(int(self._rational) ^ int(other._rational))
        return True

    def bitNot(self) -> bool:
        if not self.isInteger():
            return False
        self.set(~int(self._rational))
        return True

    def shiftLeft(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(int(self._rational) << int(other._rational))
        return True

    def shiftRight(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(int(self._rational) >> int(other._rational))
        return True

    # ===================================================================
    # Trigonometric functions
    # ===================================================================

    def sin(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.sin(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def cos(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.cos(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def tan(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.tan(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def asin(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.asin(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def acos(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.acos(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def atan(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.atan(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def atan2(self, other, allow_zero=False) -> bool:
        if isinstance(other, int):
            other = Number(other)
        _set_mpmath_prec()
        self._float_val = mpmath.atan2(self._to_mpf(), other._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def sinh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.sinh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def cosh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.cosh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def tanh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.tanh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def asinh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.asinh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def acosh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.acosh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def atanh(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.atanh(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def arg(self) -> bool:
        """Complex argument."""
        _set_mpmath_prec()
        if self.hasImaginaryPart():
            result = mpmath.arg(mpmath.mpc(self._to_mpf(), self._imaginary._to_mpf()))
            self._float_val = result
            self._type = NumberType.FLOAT
            self._imaginary = None
            self._approximate = True
        elif self.isNegative():
            self.pi()
        else:
            self.set(0)
        return True

    # ===================================================================
    # Exponential / Logarithmic
    # ===================================================================

    def ln(self) -> bool:
        _set_mpmath_prec()
        val = self._to_mpf()
        if val <= 0:
            if val == 0:
                return False
            # ln of negative: ln|x| + pi*i
            self._float_val = mpmath.log(-val)
            self._type = NumberType.FLOAT
            self._approximate = True
            self._imaginary = Number()
            self._imaginary._type = NumberType.FLOAT
            self._imaginary._float_val = mpmath.pi
            self._imaginary._approximate = True
            return True
        self._float_val = mpmath.log(val)
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def log(self, base) -> bool:
        """Logarithm to specified base."""
        if isinstance(base, int):
            base = Number(base)
        _set_mpmath_prec()
        self._float_val = mpmath.log(self._to_mpf()) / mpmath.log(base._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def lambertW(self, k=None) -> bool:
        _set_mpmath_prec()
        if k is not None and isinstance(k, Number):
            self._float_val = mpmath.lambertw(self._to_mpf(), int(k._to_mpf()))
        else:
            self._float_val = mpmath.lambertw(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    # ===================================================================
    # Mathematical constants
    # ===================================================================

    def e(self, use_cached=True) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.e
        self._approximate = True
        self._imaginary = None

    def pi(self) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.pi
        self._approximate = True
        self._imaginary = None

    def catalan(self) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.catalan
        self._approximate = True
        self._imaginary = None

    def euler(self) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.euler
        self._approximate = True
        self._imaginary = None

    # ===================================================================
    # Special functions
    # ===================================================================

    def gamma(self) -> bool:
        _set_mpmath_prec()
        try:
            self._float_val = mpmath.gamma(self._to_mpf())
        except (ValueError, ZeroDivisionError):
            return False
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def digamma(self) -> bool:
        _set_mpmath_prec()
        try:
            self._float_val = mpmath.digamma(self._to_mpf())
        except (ValueError, ZeroDivisionError):
            return False
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def zeta(self, other=None) -> bool:
        _set_mpmath_prec()
        try:
            if other is not None:
                self._float_val = mpmath.hurwitz(self._to_mpf(), other._to_mpf())
            else:
                self._float_val = mpmath.zeta(self._to_mpf())
        except (ValueError, ZeroDivisionError):
            return False
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def erf(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.erf(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def erfc(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.erfc(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def erfi(self) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.erfi(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def besselj(self, other) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.besselj(other._to_mpf(), self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def bessely(self, other) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.bessely(other._to_mpf(), self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    # ===================================================================
    # Combinatorial
    # ===================================================================

    def factorial(self) -> bool:
        if self.isInteger() and self.isNonNegative():
            n = int(self._rational)
            if n < 10000:
                self._rational = Fraction(math.factorial(n))
                return True
        _set_mpmath_prec()
        self._float_val = mpmath.factorial(self._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def doubleFactorial(self) -> bool:
        if not self.isInteger() or self.isNegative():
            return False
        n = int(self._rational)
        result = 1
        while n > 1:
            result *= n
            n -= 2
        self._rational = Fraction(result)
        return True

    def multiFactorial(self, other) -> bool:
        if not self.isInteger() or self.isNegative() or not other.isInteger() or other.isNonPositive():
            return False
        n = int(self._rational)
        k = int(other._rational)
        result = 1
        while n > 1:
            result *= n
            n -= k
        self._rational = Fraction(result)
        return True

    def binomial(self, m, k) -> bool:
        _set_mpmath_prec()
        self._float_val = mpmath.binomial(m._to_mpf(), k._to_mpf())
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    def gcd(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        self.set(math.gcd(int(self._rational), int(other._rational)))
        return True

    def lcm(self, other) -> bool:
        if not self.isInteger() or not other.isInteger():
            return False
        a = int(self._rational)
        b = int(other._rational)
        self.set(abs(a * b) // math.gcd(a, b) if a and b else 0)
        return True

    def bernoulli(self) -> bool:
        if not self.isInteger() or self.isNegative():
            return False
        _set_mpmath_prec()
        n = int(self._rational)
        self._float_val = mpmath.bernoulli(n)
        self._type = NumberType.FLOAT
        self._approximate = True
        return True

    # ===================================================================
    # Random
    # ===================================================================

    def rand(self) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.rand()
        self._approximate = True

    def randn(self) -> None:
        _set_mpmath_prec()
        self._type = NumberType.FLOAT
        self._float_val = mpmath.mpf(random.gauss(0, 1))
        self._approximate = True

    def intRand(self, ceil_val) -> None:
        if isinstance(ceil_val, Number):
            ceil_val = int(ceil_val._rational) if ceil_val.isInteger() else int(ceil_val._to_mpf())
        self._type = NumberType.RATIONAL
        self._rational = Fraction(random.randint(0, max(0, ceil_val - 1)))

    # ===================================================================
    # Boolean logic
    # ===================================================================

    def getBoolean(self) -> int:
        """Return 1 for true (non-zero), 0 for false (zero), -1 for unknown."""
        if self.isZero():
            return 0
        if self.isNonZero():
            return 1
        return -1

    def toBoolean(self):
        if self.isNonZero():
            self.set(1)
        else:
            self.set(0)

    def setTrue(self, is_true=True):
        self.set(1 if is_true else 0)

    def setFalse(self):
        self.set(0)

    def setLogicalNot(self):
        self.set(1 if self.isZero() else 0)

    # ===================================================================
    # Dispatch operation
    # ===================================================================

    def _do_operation(self, other: 'Number', op: MathOperation) -> bool:
        if op == MathOperation.ADD:
            return self.add(other)
        elif op == MathOperation.SUBTRACT:
            return self.subtract(other)
        elif op == MathOperation.MULTIPLY:
            return self.multiply(other)
        elif op == MathOperation.DIVIDE:
            return self.divide(other)
        elif op == MathOperation.RAISE:
            return self.raise_(other)
        elif op == MathOperation.EXP10:
            return self.exp10(other)
        return False

    # ===================================================================
    # Printing
    # ===================================================================

    def print(self, po: PrintOptions = None) -> str:
        """Format the number as a string for display."""
        if po is None:
            po = default_print_options

        if self._type == NumberType.PLUS_INFINITY:
            return "infinity"
        elif self._type == NumberType.MINUS_INFINITY:
            return "-infinity"

        result = ""
        if self._type == NumberType.RATIONAL:
            if self._rational.denominator == 1:
                result = str(self._rational.numerator)
            else:
                if po.number_fraction_format.value >= 2:  # FRACTIONAL or COMBINED
                    result = f"{self._rational.numerator}/{self._rational.denominator}"
                else:
                    # Decimal display
                    result = self._format_decimal(po)
        elif self._type == NumberType.FLOAT and self._float_val is not None:
            result = self._format_float(po)
        else:
            result = "0"

        # Add imaginary part
        if self.hasImaginaryPart():
            imag_str = self._imaginary.print(po)
            if result and result != "0":
                if self._imaginary.isNegative():
                    result += " - " + imag_str.lstrip('-') + "i"
                else:
                    result += " + " + imag_str + "i"
            else:
                result = imag_str + "i"

        return result

    def _format_decimal(self, po: PrintOptions) -> str:
        """Format a rational number as decimal."""
        if self._rational.denominator == 1:
            return str(self._rational.numerator)

        # Use float conversion for decimal display
        f = float(self._rational)
        prec = po.max_decimals if po.use_max_decimals and po.max_decimals >= 0 else _get_precision()
        result = f"{f:.{prec}g}"
        return result

    def _format_float(self, po: PrintOptions) -> str:
        """Format a float number as string."""
        if self._float_val is None:
            return "0"
        prec = _get_precision()
        result = mpmath.nstr(self._float_val, prec, strip_zeros=True)
        return result

    # ===================================================================
    # Operator overloads
    # ===================================================================

    def __repr__(self) -> str:
        return f"Number({self.print()})"

    def __str__(self) -> str:
        return self.print()

    def __eq__(self, other) -> bool:
        if isinstance(other, Number):
            return self.equals(other)
        if isinstance(other, int):
            return self.equals(other)
        return NotImplemented

    def __ne__(self, other) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __lt__(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if isinstance(other, Number):
            return self.isLessThan(other)
        return NotImplemented

    def __le__(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if isinstance(other, Number):
            return self.isLessThanOrEqualTo(other)
        return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if isinstance(other, Number):
            return self.isGreaterThan(other)
        return NotImplemented

    def __ge__(self, other) -> bool:
        if isinstance(other, int):
            other = Number(other)
        if isinstance(other, Number):
            return self.isGreaterThanOrEqualTo(other)
        return NotImplemented

    def __neg__(self) -> 'Number':
        result = Number(self)
        result.negate()
        return result

    def __add__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(self)
        result.add(other)
        return result

    def __radd__(self, other) -> 'Number':
        return self.__add__(other)

    def __sub__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(self)
        result.subtract(other)
        return result

    def __rsub__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(other)
        result.subtract(self)
        return result

    def __mul__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(self)
        result.multiply(other)
        return result

    def __rmul__(self, other) -> 'Number':
        return self.__mul__(other)

    def __truediv__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(self)
        result.divide(other)
        return result

    def __pow__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        result = Number(self)
        result.raise_(other)
        return result

    def __xor__(self, other) -> 'Number':
        """Exponentiation (matching C++ operator^)."""
        return self.__pow__(other)

    def __iadd__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        self.add(other)
        return self

    def __isub__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        self.subtract(other)
        return self

    def __imul__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        self.multiply(other)
        return self

    def __itruediv__(self, other) -> 'Number':
        if isinstance(other, int):
            other = Number(other)
        self.divide(other)
        return self

    def __abs__(self) -> 'Number':
        result = Number(self)
        result.abs()
        return result

    def __int__(self) -> int:
        return self.intValue()

    def __float__(self) -> float:
        return self.floatValue()

    def __bool__(self) -> bool:
        return self.isNonZero()

    def __hash__(self) -> int:
        if self._type == NumberType.RATIONAL:
            return hash(self._rational)
        return hash(self.floatValue())


# ---------------------------------------------------------------------------
# Module-level constants (well-known Number instances)
# ---------------------------------------------------------------------------

nr_zero = Number(0)
nr_one = Number(1)
nr_two = Number(2)
nr_three = Number(3)
nr_minus_one = Number(-1)
nr_half = Number(1, 2)
nr_minus_half = Number(-1, 2)
nr_plus_inf = Number()
nr_plus_inf.setPlusInfinity()
nr_minus_inf = Number()
nr_minus_inf.setMinusInfinity()
nr_one_i = Number()
nr_one_i.setImaginaryPart(Number(1))
nr_minus_i = Number()
nr_minus_i.setImaginaryPart(Number(-1))
