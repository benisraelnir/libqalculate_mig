"""
Unit tests for the Number class (qalculate.number).

Covers construction, type queries, arithmetic operations, comparisons,
special values, rounding, bitwise operations, and operator overloads.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from qalculate.number import (
    Number, nr_zero, nr_one, nr_two, nr_three,
    nr_minus_one, nr_half, nr_minus_half,
    nr_plus_inf, nr_minus_inf, nr_one_i, nr_minus_i,
)
from qalculate.includes import NumberType, ComparisonResult


# ===================================================================
# Construction
# ===================================================================

class TestNumberConstruction:
    """Test various ways to construct a Number."""

    def test_default_is_zero(self):
        n = Number()
        assert n.isZero()
        assert n.isInteger()
        assert n.intValue() == 0

    def test_from_int(self):
        n = Number(42)
        assert n.isInteger()
        assert n.intValue() == 42

    def test_from_negative_int(self):
        n = Number(-7)
        assert n.isInteger()
        assert n.isNegative()
        assert n.intValue() == -7

    def test_from_int_with_denom(self):
        n = Number(3, 4)
        assert n.isRational()
        assert not n.isInteger()
        assert n.isFraction()

    def test_from_int_with_denom_and_exp(self):
        n = Number(1, 1, 3)  # 1/1 * 10^3 = 1000
        assert n.isInteger()
        assert n.intValue() == 1000

    def test_from_string_integer(self):
        n = Number("123")
        assert n.isInteger()
        assert n.intValue() == 123

    def test_from_string_fraction(self):
        n = Number("5/8")
        assert n.isRational()
        assert not n.isInteger()

    def test_from_string_infinity(self):
        n = Number("inf")
        assert n.isPlusInfinity()

    def test_from_string_minus_infinity(self):
        n = Number("-inf")
        assert n.isMinusInfinity()

    def test_from_float(self):
        n = Number(3.14)
        assert n.isFloatingPoint()
        assert n.isApproximate()

    def test_from_fraction(self):
        n = Number(Fraction(2, 3))
        assert n.isRational()
        assert not n.isInteger()

    def test_copy_constructor(self):
        original = Number(99)
        copy = Number(original)
        assert copy.intValue() == 99
        # Mutation of copy should not affect original
        copy.add(Number(1))
        assert original.intValue() == 99


# ===================================================================
# Type Queries
# ===================================================================

class TestTypeQueries:
    """Test type query methods."""

    def test_isZero(self):
        assert Number(0).isZero()
        assert not Number(1).isZero()

    def test_isOne(self):
        assert Number(1).isOne()
        assert not Number(0).isOne()
        assert not Number(2).isOne()

    def test_isTwo(self):
        assert Number(2).isTwo()
        assert not Number(1).isTwo()

    def test_isMinusOne(self):
        assert Number(-1).isMinusOne()
        assert not Number(1).isMinusOne()

    def test_isNonZero(self):
        assert Number(1).isNonZero()
        assert not Number(0).isNonZero()

    def test_isPositive(self):
        assert Number(5).isPositive()
        assert not Number(0).isPositive()
        assert not Number(-5).isPositive()

    def test_isNegative(self):
        assert Number(-5).isNegative()
        assert not Number(0).isNegative()
        assert not Number(5).isNegative()

    def test_isNonNegative(self):
        assert Number(0).isNonNegative()
        assert Number(5).isNonNegative()
        assert not Number(-5).isNonNegative()

    def test_isNonPositive(self):
        assert Number(0).isNonPositive()
        assert Number(-5).isNonPositive()
        assert not Number(5).isNonPositive()

    def test_isEven(self):
        assert Number(4).isEven()
        assert Number(0).isEven()
        assert not Number(3).isEven()

    def test_isOdd(self):
        assert Number(3).isOdd()
        assert Number(7).isOdd()
        assert not Number(4).isOdd()

    def test_isPerfectSquare(self):
        assert Number(0).isPerfectSquare()
        assert Number(1).isPerfectSquare()
        assert Number(4).isPerfectSquare()
        assert Number(9).isPerfectSquare()
        assert not Number(2).isPerfectSquare()
        assert not Number(-1).isPerfectSquare()

    def test_isReal(self):
        assert Number(5).isReal()
        n = Number(3)
        n.setImaginaryPart(Number(4))
        assert not n.isReal()

    def test_isComplex(self):
        n = Number(3)
        n.setImaginaryPart(Number(4))
        assert n.isComplex()
        assert not Number(3).isComplex()

    def test_isInfinite(self):
        n = Number()
        n.setPlusInfinity()
        assert n.isInfinite()
        assert n.isPlusInfinity()
        assert not n.isMinusInfinity()

    def test_isInteger_queries(self):
        assert Number(5).isInteger()
        assert not Number(1, 2).isInteger()
        assert not Number(3.14).isInteger()

    def test_hasImaginaryPart(self):
        n = Number(3)
        assert not n.hasImaginaryPart()
        n.setImaginaryPart(Number(4))
        assert n.hasImaginaryPart()

    def test_hasRealPart(self):
        assert Number(5).hasRealPart()
        assert not Number(0).hasRealPart()


# ===================================================================
# Basic Arithmetic
# ===================================================================

class TestArithmetic:
    """Test arithmetic operations."""

    def test_add_integers(self):
        a = Number(3)
        a.add(Number(4))
        assert a.intValue() == 7

    def test_add_rationals(self):
        a = Number(1, 3)  # 1/3
        a.add(Number(1, 6))  # + 1/6 = 1/2
        assert a.equals(Number(1, 2))

    def test_subtract_integers(self):
        a = Number(10)
        a.subtract(Number(3))
        assert a.intValue() == 7

    def test_subtract_negative_result(self):
        a = Number(3)
        a.subtract(Number(10))
        assert a.intValue() == -7
        assert a.isNegative()

    def test_multiply_integers(self):
        a = Number(6)
        a.multiply(Number(7))
        assert a.intValue() == 42

    def test_multiply_by_zero(self):
        a = Number(42)
        a.multiply(Number(0))
        assert a.isZero()

    def test_divide_integers(self):
        a = Number(10)
        a.divide(Number(3))
        # 10/3 is a rational
        assert a.isRational()
        assert not a.isInteger()

    def test_divide_exact(self):
        a = Number(12)
        a.divide(Number(4))
        assert a.intValue() == 3

    def test_divide_by_zero_fails(self):
        a = Number(5)
        result = a.divide(Number(0))
        assert result is False

    def test_negate(self):
        a = Number(5)
        a.negate()
        assert a.intValue() == -5
        a.negate()
        assert a.intValue() == 5

    def test_abs_positive(self):
        a = Number(5)
        a.abs()
        assert a.intValue() == 5

    def test_abs_negative(self):
        a = Number(-5)
        a.abs()
        assert a.intValue() == 5

    def test_square(self):
        a = Number(7)
        a.square()
        assert a.intValue() == 49

    def test_recip(self):
        a = Number(4)
        a.recip()
        assert a.equals(Number(1, 4))

    def test_recip_zero_fails(self):
        a = Number(0)
        assert a.recip() is False


# ===================================================================
# Powers and Roots
# ===================================================================

class TestPowersAndRoots:
    """Test power and root operations."""

    def test_raise_integer_power(self):
        a = Number(2)
        a.raise_(Number(10))
        assert a.intValue() == 1024

    def test_raise_to_zero(self):
        a = Number(42)
        a.raise_(Number(0))
        assert a.isOne()

    def test_raise_zero_to_positive(self):
        a = Number(0)
        a.raise_(Number(5))
        assert a.isZero()

    def test_raise_one(self):
        a = Number(1)
        a.raise_(Number(100))
        assert a.isOne()

    def test_sqrt_perfect(self):
        a = Number(25)
        a.sqrt()
        # Perfect square: stays rational
        assert a.intValue() == 5

    def test_sqrt_non_perfect(self):
        a = Number(2)
        a.sqrt()
        # Not a perfect square: becomes float
        assert a.isFloatingPoint()
        # Approximate value check
        assert abs(a.floatValue() - math.sqrt(2)) < 1e-8

    def test_factorial(self):
        a = Number(5)
        a.factorial()
        assert a.intValue() == 120

    def test_factorial_zero(self):
        a = Number(0)
        a.factorial()
        assert a.intValue() == 1

    def test_double_factorial(self):
        a = Number(5)
        a.doubleFactorial()
        assert a.intValue() == 15  # 5!! = 5*3*1 = 15


# ===================================================================
# Modular and Rounding
# ===================================================================

class TestModularAndRounding:
    """Test modular arithmetic and rounding."""

    def test_mod(self):
        a = Number(17)
        a.mod(Number(5))
        assert a.intValue() == 2

    def test_irem(self):
        a = Number(17)
        a.irem(Number(5))
        assert a.intValue() == 2

    def test_iquo(self):
        a = Number(17)
        a.iquo(Number(5))
        assert a.intValue() == 3

    def test_iquo_with_remainder(self):
        a = Number(17)
        rem = Number()
        a.iquo(Number(5), rem)
        assert a.intValue() == 3
        assert rem.intValue() == 2

    def test_floor(self):
        a = Number(7, 2)  # 3.5
        a.floor()
        assert a.intValue() == 3

    def test_ceil(self):
        a = Number(7, 2)  # 3.5
        a.ceil()
        assert a.intValue() == 4

    def test_trunc(self):
        a = Number(7, 2)  # 3.5
        a.trunc()
        assert a.intValue() == 3

    def test_round(self):
        a = Number(7, 2)  # 3.5
        a.round()
        assert a.intValue() == 4

    def test_gcd(self):
        a = Number(12)
        a.gcd(Number(8))
        assert a.intValue() == 4

    def test_lcm(self):
        a = Number(4)
        a.lcm(Number(6))
        assert a.intValue() == 12

    def test_isIntegerDivisible(self):
        assert Number(12).isIntegerDivisible(Number(4))
        assert not Number(12).isIntegerDivisible(Number(5))


# ===================================================================
# Bitwise Operations
# ===================================================================

class TestBitwise:
    """Test bitwise operations."""

    def test_bitAnd(self):
        a = Number(0b1100)
        a.bitAnd(Number(0b1010))
        assert a.intValue() == 0b1000

    def test_bitOr(self):
        a = Number(0b1100)
        a.bitOr(Number(0b1010))
        assert a.intValue() == 0b1110

    def test_bitXor(self):
        a = Number(0b1100)
        a.bitXor(Number(0b1010))
        assert a.intValue() == 0b0110

    def test_bitNot(self):
        a = Number(0)
        a.bitNot()
        assert a.intValue() == -1  # ~0 = -1 in two's complement

    def test_shiftLeft(self):
        a = Number(1)
        a.shiftLeft(Number(4))
        assert a.intValue() == 16

    def test_shiftRight(self):
        a = Number(16)
        a.shiftRight(Number(4))
        assert a.intValue() == 1


# ===================================================================
# Comparison
# ===================================================================

class TestComparison:
    """Test comparison methods."""

    def test_equals_int(self):
        assert Number(5).equals(5)
        assert not Number(5).equals(6)

    def test_equals_number(self):
        assert Number(5).equals(Number(5))
        assert not Number(5).equals(Number(6))

    def test_compare_greater(self):
        assert Number(5).compare(Number(3)) == ComparisonResult.GREATER

    def test_compare_less(self):
        assert Number(3).compare(Number(5)) == ComparisonResult.LESS

    def test_compare_equal(self):
        assert Number(5).compare(Number(5)) == ComparisonResult.EQUAL

    def test_isGreaterThan(self):
        assert Number(5).isGreaterThan(Number(3))
        assert not Number(3).isGreaterThan(Number(5))

    def test_isLessThan(self):
        assert Number(3).isLessThan(Number(5))
        assert not Number(5).isLessThan(Number(3))

    def test_isGreaterThanOrEqualTo(self):
        assert Number(5).isGreaterThanOrEqualTo(Number(5))
        assert Number(5).isGreaterThanOrEqualTo(Number(3))

    def test_isLessThanOrEqualTo(self):
        assert Number(5).isLessThanOrEqualTo(Number(5))
        assert Number(3).isLessThanOrEqualTo(Number(5))

    def test_compare_with_int(self):
        assert Number(5).isGreaterThan(3)
        assert Number(3).isLessThan(5)

    def test_numerator_denominator_queries(self):
        n = Number(3, 4)  # 3/4
        assert n.numeratorEquals(3)
        assert n.denominatorEquals(4)
        assert n.numeratorIsGreaterThan(2)
        assert n.numeratorIsLessThan(4)
        assert n.denominatorIsGreaterThan(3)
        assert n.denominatorIsLessThan(5)


# ===================================================================
# Complex Numbers
# ===================================================================

class TestComplex:
    """Test complex number operations."""

    def test_set_imaginary_part(self):
        n = Number(3)
        n.setImaginaryPart(Number(4))
        assert n.isComplex()
        assert n.hasImaginaryPart()

    def test_real_part(self):
        n = Number(3)
        n.setImaginaryPart(Number(4))
        rp = n.realPart()
        assert rp.intValue() == 3
        assert not rp.hasImaginaryPart()

    def test_imaginary_part(self):
        n = Number(3)
        n.setImaginaryPart(Number(4))
        ip = n.imaginaryPart()
        assert ip.intValue() == 4

    def test_isI(self):
        assert nr_one_i.isI()
        assert not nr_minus_i.isI()

    def test_isMinusI(self):
        assert nr_minus_i.isMinusI()
        assert not nr_one_i.isMinusI()

    def test_clear_imaginary(self):
        n = Number(3)
        n.setImaginaryPart(Number(4))
        n.clearImaginary()
        assert not n.hasImaginaryPart()


# ===================================================================
# Special Values and Constants
# ===================================================================

class TestSpecialValues:
    """Test infinity and mathematical constants."""

    def test_plus_infinity(self):
        n = Number()
        n.setPlusInfinity()
        assert n.isPlusInfinity()
        assert n.isInfinite()
        assert n.isNonZero()
        assert n.isPositive()

    def test_minus_infinity(self):
        n = Number()
        n.setMinusInfinity()
        assert n.isMinusInfinity()
        assert n.isInfinite()
        assert n.isNonZero()
        assert n.isNegative()

    def test_negate_infinity(self):
        n = Number()
        n.setPlusInfinity()
        n.negate()
        assert n.isMinusInfinity()

    def test_pi_constant(self):
        n = Number()
        n.pi()
        assert n.isFloatingPoint()
        assert abs(n.floatValue() - 3.14159265358979) < 1e-10

    def test_e_constant(self):
        n = Number()
        n.e()
        assert n.isFloatingPoint()
        assert abs(n.floatValue() - 2.71828182845904) < 1e-10


# ===================================================================
# Precision and Approximation
# ===================================================================

class TestPrecision:
    """Test precision and approximation tracking."""

    def test_integer_not_approximate(self):
        n = Number(5)
        assert not n.isApproximate()

    def test_float_is_approximate(self):
        n = Number(3.14)
        assert n.isApproximate()

    def test_set_approximate(self):
        n = Number(5)
        n.setApproximate(True)
        assert n.isApproximate()
        n.setApproximate(False)
        assert not n.isApproximate()

    def test_set_precision(self):
        n = Number(5)
        n.setPrecision(10)
        assert n.precision() == 10
        assert n.isApproximate()

    def test_precision_propagation(self):
        a = Number(5)
        a.setPrecision(10)
        b = Number(3)
        b.setPrecisionAndApproximateFrom(a)
        assert b.isApproximate()
        assert b.precision() == 10


# ===================================================================
# Operator Overloads
# ===================================================================

class TestOperatorOverloads:
    """Test Python operator overloads."""

    def test_add_operator(self):
        result = Number(3) + Number(4)
        assert result.intValue() == 7

    def test_sub_operator(self):
        result = Number(10) - Number(3)
        assert result.intValue() == 7

    def test_mul_operator(self):
        result = Number(6) * Number(7)
        assert result.intValue() == 42

    def test_div_operator(self):
        result = Number(12) / Number(4)
        assert result.intValue() == 3

    def test_pow_operator(self):
        result = Number(2) ** Number(3)
        assert result.intValue() == 8

    def test_neg_operator(self):
        result = -Number(5)
        assert result.intValue() == -5

    def test_abs_operator(self):
        result = abs(Number(-5))
        assert result.intValue() == 5

    def test_int_conversion(self):
        assert int(Number(42)) == 42

    def test_float_conversion(self):
        assert float(Number(5)) == 5.0

    def test_bool_conversion(self):
        assert bool(Number(1))
        assert not bool(Number(0))

    def test_eq_operator(self):
        assert Number(5) == Number(5)
        assert not (Number(5) == Number(6))

    def test_ne_operator(self):
        assert Number(5) != Number(6)
        assert not (Number(5) != Number(5))

    def test_lt_operator(self):
        assert Number(3) < Number(5)
        assert not (Number(5) < Number(3))

    def test_le_operator(self):
        assert Number(3) <= Number(5)
        assert Number(5) <= Number(5)

    def test_gt_operator(self):
        assert Number(5) > Number(3)
        assert not (Number(3) > Number(5))

    def test_ge_operator(self):
        assert Number(5) >= Number(3)
        assert Number(5) >= Number(5)

    def test_int_right_operand(self):
        result = Number(3) + 4
        assert result.intValue() == 7

    def test_int_left_operand(self):
        result = 4 + Number(3)
        assert result.intValue() == 7

    def test_iadd_operator(self):
        n = Number(3)
        n += Number(4)
        assert n.intValue() == 7

    def test_isub_operator(self):
        n = Number(10)
        n -= Number(3)
        assert n.intValue() == 7

    def test_imul_operator(self):
        n = Number(6)
        n *= Number(7)
        assert n.intValue() == 42


# ===================================================================
# String Representation
# ===================================================================

class TestStringRepresentation:
    """Test str() and print() output."""

    def test_str_integer(self):
        assert str(Number(42)) == "42"

    def test_str_negative(self):
        assert str(Number(-7)) == "-7"

    def test_str_zero(self):
        assert str(Number(0)) == "0"

    def test_str_infinity(self):
        n = Number()
        n.setPlusInfinity()
        assert str(n) == "infinity"

    def test_str_minus_infinity(self):
        n = Number()
        n.setMinusInfinity()
        assert str(n) == "-infinity"

    def test_repr_contains_value(self):
        r = repr(Number(42))
        assert "42" in r


# ===================================================================
# Module-level Constants
# ===================================================================

class TestModuleConstants:
    """Test the pre-defined module-level Number constants."""

    def test_nr_zero(self):
        assert nr_zero.isZero()

    def test_nr_one(self):
        assert nr_one.isOne()

    def test_nr_two(self):
        assert nr_two.isTwo()

    def test_nr_three(self):
        assert nr_three.intValue() == 3

    def test_nr_minus_one(self):
        assert nr_minus_one.isMinusOne()

    def test_nr_half(self):
        assert nr_half.equals(Number(1, 2))

    def test_nr_minus_half(self):
        assert nr_minus_half.equals(Number(-1, 2))

    def test_nr_plus_inf(self):
        assert nr_plus_inf.isPlusInfinity()

    def test_nr_minus_inf(self):
        assert nr_minus_inf.isMinusInfinity()

    def test_nr_one_i(self):
        assert nr_one_i.isI()

    def test_nr_minus_i(self):
        assert nr_minus_i.isMinusI()


# ===================================================================
# Set and Clear
# ===================================================================

class TestSetAndClear:
    """Test set() and clear() methods."""

    def test_set_int(self):
        n = Number(5)
        n.set(10)
        assert n.intValue() == 10

    def test_set_number(self):
        n = Number(5)
        n.set(Number(42))
        assert n.intValue() == 42

    def test_set_from_string(self):
        n = Number()
        n.set("99")
        assert n.intValue() == 99

    def test_clear(self):
        n = Number(42)
        n.clear()
        assert n.isZero()
        assert not n.isApproximate()

    def test_clearReal(self):
        n = Number(42)
        n.setImaginaryPart(Number(5))
        n.clearReal()
        assert not n.hasRealPart() or n.intValue() == 0

    def test_setFloat(self):
        n = Number()
        n.setFloat(3.14)
        assert n.isFloatingPoint()
        assert n.isApproximate()
