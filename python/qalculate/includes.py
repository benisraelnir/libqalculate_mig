"""
Qalculate enums, constants, and options structs.

Translated from libqalculate/includes.h.
All enums use IntEnum for C++ compatibility (integer comparisons work).
Options structs use dataclasses with defaults matching the C++ defaults.
"""

from __future__ import annotations

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------
QALCULATE_MAJOR_VERSION = 5
QALCULATE_MINOR_VERSION = 9
QALCULATE_MICRO_VERSION = 0

DEFAULT_PRECISION = 8

# ---------------------------------------------------------------------------
# ExpressionItemType
# ---------------------------------------------------------------------------

class ExpressionItemType(IntEnum):
    TYPE_VARIABLE = 0
    TYPE_FUNCTION = 1
    TYPE_UNIT = 2


# ---------------------------------------------------------------------------
# ComparisonResult
# ---------------------------------------------------------------------------

class ComparisonResult(IntEnum):
    EQUAL = 0
    GREATER = 1
    LESS = 2
    EQUAL_OR_GREATER = 3
    EQUAL_OR_LESS = 4
    NOT_EQUAL = 5
    UNKNOWN = 6
    EQUAL_LIMITS = 7
    CONTAINS = 8
    CONTAINED = 9
    OVERLAPPING_LESS = 10
    OVERLAPPING_GREATER = 11


def COMPARISON_MIGHT_BE_LESS_OR_GREATER(i: int) -> bool:
    return i >= ComparisonResult.UNKNOWN or i == ComparisonResult.NOT_EQUAL

def COMPARISON_NOT_FULLY_KNOWN(i: int) -> bool:
    return (i >= ComparisonResult.UNKNOWN or i == ComparisonResult.NOT_EQUAL
            or i == ComparisonResult.EQUAL_OR_LESS or i == ComparisonResult.EQUAL_OR_GREATER)

def COMPARISON_IS_EQUAL_OR_GREATER(i: int) -> bool:
    return (i == ComparisonResult.EQUAL or i == ComparisonResult.GREATER
            or i == ComparisonResult.EQUAL_OR_GREATER)

def COMPARISON_IS_EQUAL_OR_LESS(i: int) -> bool:
    return (i == ComparisonResult.EQUAL or i == ComparisonResult.LESS
            or i == ComparisonResult.EQUAL_OR_LESS)

def COMPARISON_IS_NOT_EQUAL(i: int) -> bool:
    return (i == ComparisonResult.NOT_EQUAL or i == ComparisonResult.LESS
            or i == ComparisonResult.GREATER)

def COMPARISON_MIGHT_BE_EQUAL(i: int) -> bool:
    return (i >= ComparisonResult.UNKNOWN or i == ComparisonResult.EQUAL_OR_LESS
            or i == ComparisonResult.EQUAL_OR_GREATER or i == ComparisonResult.EQUAL)

def COMPARISON_MIGHT_BE_NOT_EQUAL(i: int) -> bool:
    return (i >= ComparisonResult.UNKNOWN or i == ComparisonResult.EQUAL_OR_LESS
            or i == ComparisonResult.EQUAL_OR_GREATER or i == ComparisonResult.NOT_EQUAL)


# ---------------------------------------------------------------------------
# Plot enums
# ---------------------------------------------------------------------------

class PlotLegendPlacement(IntEnum):
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4
    BELOW = 5
    OUTSIDE = 6


class PlotStyle(IntEnum):
    LINES = 0
    POINTS = 1
    POINTS_LINES = 2
    BOXES = 3
    HISTOGRAM = 4
    STEPS = 5
    CANDLESTICKS = 6
    DOTS = 7
    POLAR = 8


class PlotSmoothing(IntEnum):
    NONE = 0
    UNIQUE = 1
    CSPLINES = 2
    BEZIER = 3
    SBEZIER = 4


class PlotFileType(IntEnum):
    AUTO = 0
    PNG = 1
    PS = 2
    EPS = 3
    LATEX = 4
    SVG = 5
    FIG = 6
    PDF = 7


# ---------------------------------------------------------------------------
# MathOperation
# ---------------------------------------------------------------------------

class MathOperation(IntEnum):
    MULTIPLY = 0
    DIVIDE = 1
    ADD = 2
    SUBTRACT = 3
    RAISE = 4
    EXP10 = 5
    LOGICAL_AND = 6
    LOGICAL_OR = 7
    LOGICAL_XOR = 8
    BITWISE_AND = 9
    BITWISE_OR = 10
    BITWISE_XOR = 11
    LESS = 12
    GREATER = 13
    EQUALS_LESS = 14
    EQUALS_GREATER = 15
    EQUALS = 16
    NOT_EQUALS = 17


# ---------------------------------------------------------------------------
# ComparisonType
# ---------------------------------------------------------------------------

class ComparisonType(IntEnum):
    LESS = 0
    GREATER = 1
    EQUALS_LESS = 2
    EQUALS_GREATER = 3
    EQUALS = 4
    NOT_EQUALS = 5


# ---------------------------------------------------------------------------
# SortFlags
# ---------------------------------------------------------------------------

class SortFlags(IntEnum):
    DEFAULT = 1 << 0
    SCIENTIFIC = 1 << 1


# ---------------------------------------------------------------------------
# Number base constants
# ---------------------------------------------------------------------------

BASE_ROMAN_NUMERALS = -1
BASE_TIME = -2
BASE_BINARY = 2
BASE_OCTAL = 8
BASE_DECIMAL = 10
BASE_DUODECIMAL = 12
BASE_HEXADECIMAL = 16
BASE_SEXAGESIMAL = 60
BASE_SEXAGESIMAL_2 = 62
BASE_SEXAGESIMAL_3 = 63
BASE_LATITUDE = 70
BASE_LATITUDE_2 = 71
BASE_LONGITUDE = 72
BASE_LONGITUDE_2 = 73
BASE_CUSTOM = -3
BASE_UNICODE = -4
BASE_GOLDEN_RATIO = -5
BASE_SUPER_GOLDEN_RATIO = -6
BASE_PI = -7
BASE_E = -8
BASE_SQRT2 = -9
BASE_BINARY_DECIMAL = -20
BASE_BIJECTIVE_26 = -26
BASE_FP16 = -30
BASE_FP32 = -31
BASE_FP64 = -32
BASE_FP128 = -33
BASE_FP80 = -34


def BASE_IS_SEXAGESIMAL(x: int) -> bool:
    return (BASE_SEXAGESIMAL <= x <= BASE_SEXAGESIMAL_3) or (BASE_LATITUDE <= x <= BASE_LONGITUDE_2)


# Min-exp constants
EXP_BASE_3 = -3
EXP_PRECISION = -1
EXP_NONE = 0
EXP_PURE = 1
EXP_SCIENTIFIC = 3

# Parse percent flag
PARSE_PERCENT_AS_ORDINARY_CONSTANT = 0x10


# ---------------------------------------------------------------------------
# NumberFractionFormat
# ---------------------------------------------------------------------------

class NumberFractionFormat(IntEnum):
    DECIMAL = 0
    DECIMAL_EXACT = 1
    FRACTIONAL = 2
    COMBINED = 3
    FRACTIONAL_FIXED_DENOMINATOR = 4
    COMBINED_FIXED_DENOMINATOR = 5
    PERCENT = 6
    PERMILLE = 7
    PERMYRIAD = 8


# ---------------------------------------------------------------------------
# MultiplicationSign
# ---------------------------------------------------------------------------

class MultiplicationSign(IntEnum):
    ASTERISK = 0
    DOT = 1
    X = 2
    ALTDOT = 3


# ---------------------------------------------------------------------------
# DivisionSign
# ---------------------------------------------------------------------------

class DivisionSign(IntEnum):
    SLASH = 0
    DIVISION_SLASH = 1
    DIVISION = 2


# ---------------------------------------------------------------------------
# BaseDisplay
# ---------------------------------------------------------------------------

class BaseDisplay(IntEnum):
    NONE = 0
    NORMAL = 1
    ALTERNATIVE = 2
    SUFFIX = 3


# ---------------------------------------------------------------------------
# IntervalDisplay
# ---------------------------------------------------------------------------

class IntervalDisplay(IntEnum):
    SIGNIFICANT_DIGITS = 0
    INTERVAL = 1
    PLUSMINUS = 2
    MIDPOINT = 3
    LOWER = 4
    UPPER = 5
    CONCISE = 6
    RELATIVE = 7


# ---------------------------------------------------------------------------
# DigitGrouping
# ---------------------------------------------------------------------------

class DigitGrouping(IntEnum):
    NONE = 0
    STANDARD = 1
    LOCALE = 2


# ---------------------------------------------------------------------------
# DateTimeFormat
# ---------------------------------------------------------------------------

class DateTimeFormat(IntEnum):
    ISO = 0
    LOCALE = 1


# ---------------------------------------------------------------------------
# TimeZone
# ---------------------------------------------------------------------------

class TimeZone(IntEnum):
    UTC = 0
    LOCAL = 1
    CUSTOM = 2


# ---------------------------------------------------------------------------
# ExpDisplay
# ---------------------------------------------------------------------------

class ExpDisplay(IntEnum):
    DEFAULT = 0
    UPPERCASE_E = 1
    LOWERCASE_E = 2
    POWER_OF_10 = 3


# ---------------------------------------------------------------------------
# RoundingMode
# ---------------------------------------------------------------------------

class RoundingMode(IntEnum):
    HALF_AWAY_FROM_ZERO = 0
    HALF_TO_EVEN = 1
    HALF_TO_ODD = 2
    HALF_TOWARD_ZERO = 3
    HALF_UP = 4
    HALF_DOWN = 5
    HALF_RANDOM = 6
    TOWARD_ZERO = 7
    AWAY_FROM_ZERO = 8
    UP = 9
    DOWN = 10


# ---------------------------------------------------------------------------
# Unicode signs display mode (anonymous enum in C++)
# ---------------------------------------------------------------------------

UNICODE_SIGNS_OFF = 0
UNICODE_SIGNS_ON = 1
UNICODE_SIGNS_ONLY_UNIT_EXPONENTS = 2
UNICODE_SIGNS_WITHOUT_EXPONENTS = 3

# Repeating decimals display mode
REPEATING_DECIMALS_OFF = 0
REPEATING_DECIMALS_ELLIPSIS = 1
REPEATING_DECIMALS_OVERLINE = 2

# Temporary custom time zone values
TZ_TRUNCATE = -21586
TZ_DOZENAL = -53172


# ---------------------------------------------------------------------------
# ApproximationMode
# ---------------------------------------------------------------------------

class ApproximationMode(IntEnum):
    EXACT = 0
    TRY_EXACT = 1
    APPROXIMATE = 2
    EXACT_VARIABLES = 3


# ---------------------------------------------------------------------------
# StructuringMode
# ---------------------------------------------------------------------------

class StructuringMode(IntEnum):
    NONE = 0
    EXPAND = 1
    FACTORIZE = 2
    HYBRID = 3

STRUCTURING_SIMPLIFY = StructuringMode.EXPAND


# ---------------------------------------------------------------------------
# AutoPostConversion
# ---------------------------------------------------------------------------

class AutoPostConversion(IntEnum):
    NONE = 0
    OPTIMAL_SI = 1
    BASE = 2
    OPTIMAL = 3

POST_CONVERSION_BEST = AutoPostConversion.OPTIMAL_SI


# ---------------------------------------------------------------------------
# MixedUnitsConversion
# ---------------------------------------------------------------------------

class MixedUnitsConversion(IntEnum):
    NONE = 0
    DOWNWARDS_KEEP = 1
    DOWNWARDS = 2
    DEFAULT = 3
    FORCE_INTEGER = 4
    FORCE_ALL = 5


# ---------------------------------------------------------------------------
# ReadPrecisionMode
# ---------------------------------------------------------------------------

class ReadPrecisionMode(IntEnum):
    DONT_READ_PRECISION = 0
    ALWAYS_READ_PRECISION = 1
    READ_PRECISION_WHEN_DECIMALS = 2


# ---------------------------------------------------------------------------
# AngleUnit
# ---------------------------------------------------------------------------

class AngleUnit(IntEnum):
    NONE = 0
    RADIANS = 1
    DEGREES = 2
    GRADIANS = 3
    CUSTOM = 4


# ---------------------------------------------------------------------------
# ComplexNumberForm
# ---------------------------------------------------------------------------

class ComplexNumberForm(IntEnum):
    RECTANGULAR = 0
    EXPONENTIAL = 1
    POLAR = 2
    CIS = 3


# ---------------------------------------------------------------------------
# ParsingMode
# ---------------------------------------------------------------------------

class ParsingMode(IntEnum):
    ADAPTIVE = 0
    IMPLICIT_MULTIPLICATION_FIRST = 1
    CONVENTIONAL = 2
    CHAIN = 3
    RPN = 4


# ---------------------------------------------------------------------------
# IntervalCalculation
# ---------------------------------------------------------------------------

class IntervalCalculation(IntEnum):
    NONE = 0
    VARIANCE_FORMULA = 1
    INTERVAL_ARITHMETIC = 2
    SIMPLE_INTERVAL_ARITHMETIC = 3


# ---------------------------------------------------------------------------
# NumberType (from Number.h)
# ---------------------------------------------------------------------------

class NumberType(IntEnum):
    RATIONAL = 0
    FLOAT = 1
    PLUS_INFINITY = 2
    MINUS_INFINITY = 3


# ---------------------------------------------------------------------------
# IntegerType (from Number.h)
# ---------------------------------------------------------------------------

class IntegerType(IntEnum):
    NONE = 0
    SINT = 1
    UINT = 2
    ULONG = 3
    SLONG = 4
    SIZE = 5


# ---------------------------------------------------------------------------
# PrefixType (from Prefix.h)
# ---------------------------------------------------------------------------

class PrefixType(IntEnum):
    DECIMAL = 0
    BINARY = 1
    NUMBER = 2


# ---------------------------------------------------------------------------
# CalendarSystem (from QalculateDateTime.h)
# ---------------------------------------------------------------------------

class CalendarSystem(IntEnum):
    GREGORIAN = 0
    MILANKOVIC = 1
    JULIAN = 2
    ISLAMIC = 3
    HEBREW = 4
    EGYPTIAN = 5
    PERSIAN = 6
    COPTIC = 7
    ETHIOPIAN = 8
    INDIAN = 9
    CHINESE = 10

NUMBER_OF_CALENDARS = 11

# Solar/Lunar constants
VERNAL_EQUINOX = 0
SUMMER_SOLSTICE = 90
AUTUMNAL_EQUINOX = 180
WINTER_SOLSTICE = 270


# ---------------------------------------------------------------------------
# SortOptions
# ---------------------------------------------------------------------------

@dataclass
class SortOptions:
    """Options for ordering the parts of a mathematical expression/result before display."""
    prefix_currencies: bool = True
    minus_last: bool = True


# ---------------------------------------------------------------------------
# PrintOptions
# ---------------------------------------------------------------------------

@dataclass
class PrintOptions:
    """Options for formatting and display of mathematical structures/results."""
    min_exp: int = EXP_PRECISION
    base: int = 10
    base_display: BaseDisplay = BaseDisplay.NONE
    lower_case_numbers: bool = False
    lower_case_e: bool = False
    number_fraction_format: NumberFractionFormat = NumberFractionFormat.DECIMAL
    indicate_infinite_series: int = 0  # char in C++, using int
    show_ending_zeroes: bool = False
    abbreviate_names: bool = True
    use_reference_names: bool = False
    place_units_separately: bool = True
    use_unit_prefixes: bool = True
    use_prefixes_for_all_units: bool = False
    use_prefixes_for_currencies: bool = False
    use_all_prefixes: bool = False
    use_denominator_prefix: bool = True
    negative_exponents: bool = False
    short_multiplication: bool = True
    limit_implicit_multiplication: bool = False
    allow_non_usable: bool = False
    use_unicode_signs: int = UNICODE_SIGNS_OFF
    multiplication_sign: MultiplicationSign = MultiplicationSign.DOT
    division_sign: DivisionSign = DivisionSign.DIVISION_SLASH
    spacious: bool = True
    excessive_parenthesis: bool = False
    halfexp_to_sqrt: bool = True
    min_decimals: int = 0
    max_decimals: int = -1
    use_min_decimals: bool = True
    use_max_decimals: bool = True
    round_halfway_to_even: bool = False  # deprecated
    improve_division_multipliers: bool = True
    prefix: Any = None  # Prefix object or None
    is_approximate: Optional[list] = None  # mutable container for bool flag
    sort_options: SortOptions = field(default_factory=SortOptions)
    comma_sign: str = ""
    decimalpoint_sign: str = ""
    can_display_unicode_string_function: Optional[Callable] = None
    can_display_unicode_string_arg: Any = None
    hide_underscore_spaces: bool = False
    preserve_format: bool = False
    allow_factorization: bool = False
    spell_out_logical_operators: bool = False
    restrict_to_parent_precision: bool = True
    restrict_fraction_length: bool = False
    exp_to_root: bool = False
    preserve_precision: bool = False
    interval_display: IntervalDisplay = IntervalDisplay.INTERVAL
    digit_grouping: DigitGrouping = DigitGrouping.NONE
    date_time_format: DateTimeFormat = DateTimeFormat.ISO
    time_zone: TimeZone = TimeZone.LOCAL
    custom_time_zone: int = 0
    twos_complement: bool = True
    hexadecimal_twos_complement: bool = False
    binary_bits: int = 0
    exp_display: ExpDisplay = ExpDisplay.DEFAULT
    duodecimal_symbols: bool = False
    rounding: RoundingMode = RoundingMode.HALF_AWAY_FROM_ZERO

    def comma(self) -> str:
        """Returns the comma sign used (default sign or comma_sign)."""
        return self.comma_sign if self.comma_sign else ","

    def decimalpoint(self) -> str:
        """Returns the decimal sign used (default sign or decimalpoint_sign)."""
        return self.decimalpoint_sign if self.decimalpoint_sign else "."


# ---------------------------------------------------------------------------
# InternalPrintStruct
# ---------------------------------------------------------------------------

@dataclass
class InternalPrintStruct:
    """Internal structure used during printing."""
    depth: int = 0
    power_depth: int = 0
    division_depth: int = 0
    wrap: bool = False
    num: Optional[str] = None
    den: Optional[str] = None
    re: Optional[str] = None
    im: Optional[str] = None
    exp: Optional[str] = None
    minus: bool = False
    exp_minus: bool = False
    parent_approximate: bool = False
    parent_precision: int = 0
    iexp: Optional[int] = None


# ---------------------------------------------------------------------------
# ParseOptions
# ---------------------------------------------------------------------------

@dataclass
class ParseOptions:
    """Options for parsing expressions."""
    variables_enabled: bool = True
    functions_enabled: bool = True
    unknowns_enabled: bool = True
    units_enabled: bool = True
    rpn: bool = False
    base: int = 10
    limit_implicit_multiplication: bool = False
    read_precision: ReadPrecisionMode = ReadPrecisionMode.DONT_READ_PRECISION
    dot_as_separator: bool = False
    comma_as_separator: bool = False
    brackets_as_parentheses: bool = False
    angle_unit: AngleUnit = AngleUnit.NONE
    unended_function: Any = None  # MathStructure or None
    preserve_format: bool = False
    default_dataset: Any = None  # DataSet or None
    parsing_mode: ParsingMode = ParsingMode.ADAPTIVE
    twos_complement: bool = False
    hexadecimal_twos_complement: bool = False
    binary_bits: int = 0


# ---------------------------------------------------------------------------
# EvaluationOptions
# ---------------------------------------------------------------------------

@dataclass
class EvaluationOptions:
    """Options for calculation."""
    approximation: ApproximationMode = ApproximationMode.TRY_EXACT
    sync_units: bool = True
    sync_nonlinear_unit_relations: bool = True
    keep_prefixes: bool = False
    calculate_variables: bool = True
    calculate_functions: bool = True
    test_comparisons: int = 1  # bool-like int; 1 = true
    isolate_x: bool = True
    expand: int = 1  # bool-like int; 1 = true
    combine_divisions: bool = False
    reduce_divisions: bool = True
    allow_complex: bool = True
    allow_infinite: bool = True
    assume_denominators_nonzero: int = 0  # 0 = false
    warn_about_denominators_assumed_nonzero: bool = True
    split_squares: bool = True
    keep_zero_units: bool = True
    auto_post_conversion: AutoPostConversion = AutoPostConversion.OPTIMAL
    mixed_units_conversion: MixedUnitsConversion = MixedUnitsConversion.DEFAULT
    structuring: StructuringMode = StructuringMode.NONE
    parse_options: ParseOptions = field(default_factory=ParseOptions)
    isolate_var: Any = None  # MathStructure or None
    do_polynomial_division: bool = True
    protected_function: Any = None  # MathFunction or None
    complex_number_form: ComplexNumberForm = ComplexNumberForm.RECTANGULAR
    local_currency_conversion: bool = True
    transform_trigonometric_functions: bool = True
    interval_calculation: IntervalCalculation = IntervalCalculation.VARIANCE_FORMULA


# ---------------------------------------------------------------------------
# Precision constants (from Number.h)
# ---------------------------------------------------------------------------

EQUALS_PRECISION_DEFAULT = -1
EQUALS_PRECISION_LOWEST = -2
EQUALS_PRECISION_HIGHEST = -3


# ---------------------------------------------------------------------------
# Prime number tables (small, from includes.h)
# ---------------------------------------------------------------------------

NR_OF_PRIMES = 600

PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
    127, 131, 137, 139, 149, 151, 157, 163, 167, 173,
    179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
    233, 239, 241, 251, 257, 263, 269, 271, 277, 281,
    283, 293, 307, 311, 313, 317, 331, 337, 347, 349,
    353, 359, 367, 373, 379, 383, 389, 397, 401, 409,
    419, 421, 431, 433, 439, 443, 449, 457, 461, 463,
    467, 479, 487, 491, 499, 503, 509, 521, 523, 541,
    547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
    607, 613, 617, 619, 631, 641, 643, 647, 653, 659,
    661, 673, 677, 683, 691, 701, 709, 719, 727, 733,
    739, 743, 751, 757, 761, 769, 773, 787, 797, 809,
    811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
    877, 881, 883, 887, 907, 911, 919, 929, 937, 941,
    947, 953, 967, 971, 977, 983, 991, 997, 1009, 1013,
    1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061, 1063, 1069,
    1087, 1091, 1093, 1097, 1103, 1109, 1117, 1123, 1129, 1151,
    1153, 1163, 1171, 1181, 1187, 1193, 1201, 1213, 1217, 1223,
    1229, 1231, 1237, 1249, 1259, 1277, 1279, 1283, 1289, 1291,
    1297, 1301, 1303, 1307, 1319, 1321, 1327, 1361, 1367, 1373,
    1381, 1399, 1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451,
    1453, 1459, 1471, 1481, 1483, 1487, 1489, 1493, 1499, 1511,
    1523, 1531, 1543, 1549, 1553, 1559, 1567, 1571, 1579, 1583,
    1597, 1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657,
    1663, 1667, 1669, 1693, 1697, 1699, 1709, 1721, 1723, 1733,
    1741, 1747, 1753, 1759, 1777, 1783, 1787, 1789, 1801, 1811,
    1823, 1831, 1847, 1861, 1867, 1871, 1873, 1877, 1879, 1889,
    1901, 1907, 1913, 1931, 1933, 1949, 1951, 1973, 1979, 1987,
    1993, 1997, 1999, 2003, 2011, 2017, 2027, 2029, 2039, 2053,
    2063, 2069, 2081, 2083, 2087, 2089, 2099, 2111, 2113, 2129,
    2131, 2137, 2141, 2143, 2153, 2161, 2179, 2203, 2207, 2213,
    2221, 2237, 2239, 2243, 2251, 2267, 2269, 2273, 2281, 2287,
    2293, 2297, 2309, 2311, 2333, 2339, 2341, 2347, 2351, 2357,
    2371, 2377, 2381, 2383, 2389, 2393, 2399, 2411, 2417, 2423,
    2437, 2441, 2447, 2459, 2467, 2473, 2477, 2503, 2521, 2531,
    2539, 2543, 2549, 2551, 2557, 2579, 2591, 2593, 2609, 2617,
    2621, 2633, 2647, 2657, 2659, 2663, 2671, 2677, 2683, 2687,
    2689, 2693, 2699, 2707, 2711, 2713, 2719, 2729, 2731, 2741,
    2749, 2753, 2767, 2777, 2789, 2791, 2797, 2801, 2803, 2819,
    2833, 2837, 2843, 2851, 2857, 2861, 2879, 2887, 2897, 2903,
    2909, 2917, 2927, 2939, 2953, 2957, 2963, 2969, 2971, 2999,
    3001, 3011, 3019, 3023, 3037, 3041, 3049, 3061, 3067, 3079,
    3083, 3089, 3109, 3119, 3121, 3137, 3163, 3167, 3169, 3181,
    3187, 3191, 3203, 3209, 3217, 3221, 3229, 3251, 3253, 3257,
    3259, 3271, 3299, 3301, 3307, 3313, 3319, 3323, 3329, 3331,
    3343, 3347, 3359, 3361, 3371, 3373, 3389, 3391, 3407, 3413,
    3433, 3449, 3457, 3461, 3463, 3467, 3469, 3491, 3499, 3511,
    3517, 3527, 3529, 3533, 3539, 3541, 3547, 3557, 3559, 3571,
    3581, 3583, 3593, 3607, 3613, 3617, 3623, 3631, 3637, 3643,
    3659, 3671, 3673, 3677, 3691, 3697, 3701, 3709, 3719, 3727,
    3733, 3739, 3761, 3767, 3769, 3779, 3793, 3797, 3803, 3821,
    3823, 3833, 3847, 3851, 3853, 3863, 3877, 3881, 3889, 3907,
    3911, 3917, 3919, 3923, 3929, 3931, 3943, 3947, 3967, 3989,
    4001, 4003, 4007, 4013, 4019, 4021, 4027, 4049, 4051, 4057,
    4073, 4079, 4091, 4093, 4099, 4111, 4127, 4129, 4133, 4139,
    4153, 4157, 4159, 4177, 4201, 4211, 4217, 4219, 4229, 4231,
    4241, 4243, 4253, 4259, 4261, 4271, 4273, 4283, 4289, 4297,
    4327, 4337, 4339, 4349, 4357, 4363, 4373, 4391, 4397, 4409,
]

SQP_LT_1000 = 11
SQP_LT_2000 = 17
SQP_LT_10000 = 28
SQP_LT_25000 = 40
SQP_LT_100000 = 68
NR_OF_SQUARE_PRIMES = 170

SQUARE_PRIMES = [
    4, 9, 25, 49, 121, 169, 289, 361, 529, 841,
    961, 1369, 1681, 1849, 2209, 2809, 3481, 3721, 4489, 5041,
    5329, 6241, 6889, 7921, 9409, 10201, 10609, 11449, 11881, 12769,
    16129, 17161, 18769, 19321, 22201, 22801, 24649, 26569, 27889, 29929,
    32041, 32761, 36481, 37249, 38809, 39601, 44521, 49729, 51529, 52441,
    54289, 57121, 58081, 63001, 66049, 69169, 72361, 73441, 76729, 78961,
    80089, 85849, 94249, 96721, 97969, 100489, 109561, 113569, 120409, 121801,
    124609, 128881, 134689, 139129, 143641, 146689, 151321, 157609, 160801, 167281,
    175561, 177241, 185761, 187489, 192721, 196249, 201601, 208849, 212521, 214369,
    218089, 229441, 237169, 241081, 249001, 253009, 259081, 271441, 273529, 292681,
    299209, 310249, 316969, 323761, 326041, 332929, 344569, 351649, 358801, 361201,
    368449, 375769, 380689, 383161, 398161, 410881, 413449, 418609, 426409, 434281,
    436921, 452929, 458329, 466489, 477481, 491401, 502681, 516961, 528529, 537289,
    546121, 552049, 564001, 573049, 579121, 591361, 597529, 619369, 635209, 654481,
    657721, 674041, 677329, 683929, 687241, 703921, 727609, 734449, 737881, 744769,
    769129, 776161, 779689, 786769, 822649, 829921, 844561, 863041, 877969, 885481,
    896809, 908209, 935089, 942841, 954529, 966289, 982081, 994009, 1018081, 1026169,
]

LARGEST_RAISED_PRIME_EXPONENT = 10

RAISED_PRIMES = [
    # exponent 3 (2^3, 3^3, 5^3, ...)
    [8, 27, 125, 343, 1331, 2197, 4913, 6859, 12167, 24389,
     29791, 50653, 68921, 79507, 103823, 148877, 205379, 226981, 300763, 357911,
     389017, 493039, 571787, 704969, 912673, 1030301, 1092727, 1225043, 1295029, 1442897,
     2048383, 2248091, 2571353, 2685619, 3307949, 3442951, 3869893, 4330747, 4657463, 5177717,
     5735339, 5929741, 6967871, 7189057, 7645373, 7880599, 9393931, 11089567],
    # exponent 4
    [16, 81, 625, 2401, 14641, 28561, 83521, 130321, 279841, 707281,
     923521, 1874161, 2825761, 3418801, 4879681, 7890481, 12117361],
    # exponent 5
    [32, 243, 3125, 16807, 161051, 371293, 1419857, 2476099, 6436343, 20511149],
    # exponent 6
    [64, 729, 15625, 117649, 1771561, 4826809, 24137569, 47045881, 148035889],
    # exponent 7
    [128, 2187, 78125, 823543, 19487171, 62748517, 410338673],
    # exponent 8
    [256, 6561, 390625, 5764801, 214358881, 815730721],
    # exponent 9
    [512, 19683, 1953125, 40353607],
    # exponent 10
    [1024, 59049, 9765625, 282475249],
]


# ---------------------------------------------------------------------------
# Unicode sign constants
# ---------------------------------------------------------------------------

SIGN_DEGREE = "\u00b0"
SIGN_POWER_0 = "\u2070"
SIGN_POWER_1 = "\u00b9"
SIGN_POWER_2 = "\u00b2"
SIGN_POWER_3 = "\u00b3"
SIGN_POWER_4 = "\u2074"
SIGN_POWER_5 = "\u2075"
SIGN_POWER_6 = "\u2076"
SIGN_POWER_7 = "\u2077"
SIGN_POWER_8 = "\u2078"
SIGN_POWER_9 = "\u2079"
SIGN_EURO = "\u20ac"
SIGN_POUND = "\u00a3"
SIGN_CENT = "\u00a2"
SIGN_YEN = "\u00a5"
SIGN_MICRO = "\u00b5"
SIGN_PI = "\u03c0"
SIGN_MULTIPLICATION = "\u00d7"
SIGN_MULTIDOT = "\u22c5"
SIGN_MIDDLEDOT = "\u00b7"
SIGN_MULTIBULLET = "\u2219"
SIGN_SMALLCIRCLE = "\u2022"
SIGN_DIVISION_SLASH = "\u2215"
SIGN_DIVISION = "\u00f7"
SIGN_MINUS = "\u2212"
SIGN_PLUS = "\uff0b"
SIGN_SQRT = "\u221a"
SIGN_ALMOST_EQUAL = "\u2248"
SIGN_APPROXIMATELY_EQUAL = "\u2245"
SIGN_ZETA = "\u03b6"
SIGN_GAMMA = "\u03b3"
SIGN_PHI = "\u03c6"
SIGN_LESS_OR_EQUAL = "\u2264"
SIGN_GREATER_OR_EQUAL = "\u2265"
SIGN_NOT_EQUAL = "\u2260"
SIGN_CAPITAL_SIGMA = "\u03a3"
SIGN_CAPITAL_PI = "\u03a0"
SIGN_CAPITAL_OMEGA = "\u03a9"
SIGN_CAPITAL_GAMMA = "\u0393"
SIGN_CAPITAL_BETA = "\u0392"
SIGN_INFINITY = "\u221e"
SIGN_PLUSMINUS = "\u00b1"

THIN_SPACE = "\u2009"
NNBSP = "\u202f"
NBSP = "\u00a0"

# ---------------------------------------------------------------------------
# Character constants
# ---------------------------------------------------------------------------

ID_WRAP_LEFT_CH = '{'
ID_WRAP_RIGHT_CH = '}'
DOT_CH = '.'
ZERO_CH = '0'
ONE_CH = '1'
TWO_CH = '2'
THREE_CH = '3'
FOUR_CH = '4'
FIVE_CH = '5'
SIX_CH = '6'
SEVEN_CH = '7'
EIGHT_CH = '8'
NINE_CH = '9'
PLUS_CH = '+'
MINUS_CH = '-'
MULTIPLICATION_CH = '*'
MULTIPLICATION_2_CH = ' '
DIVISION_CH = '/'
EXP_CH = 'E'
EXP2_CH = 'e'
POWER_CH = '^'
SPACE_CH = ' '
LEFT_PARENTHESIS_CH = '('
RIGHT_PARENTHESIS_CH = ')'
LEFT_VECTOR_WRAP_CH = '['
RIGHT_VECTOR_WRAP_CH = ']'
FUNCTION_VAR_PRE_CH = '\\'
COMMA_CH = ','
NAME_NUMBER_PRE_CH = '_'
UNIT_DIVISION_CH = '/'
AND_CH = '&'
OR_CH = '|'
LESS_CH = '<'
GREATER_CH = '>'
BITWISE_NOT_CH = '~'
LOGICAL_NOT_CH = '!'
NOT_CH = '!'
EQUALS_CH = '='

# String constants
ID_WRAP_LEFT = "{"
ID_WRAP_RIGHT = "}"
ID_WRAPS = "{}"
DOT_S = "."
SEXADOT = ":"
COMMA_S = ","
COMMAS = ",;"
NUMBERS = "0123456789"
NUMBER_ELEMENTS = "0123456789.:"
SIGNS = "+-*/^"
OPERATORS = "~+-*/^&|!<>="
PARENTHESISS = "()"
LEFT_PARENTHESIS = "("
RIGHT_PARENTHESIS = ")"
VECTOR_WRAPS = "[]"
LEFT_VECTOR_WRAP = "["
RIGHT_VECTOR_WRAP = "]"
SPACES = " \t\n"
SPACE_S = " "
RESERVED = "\'@\\{}?\""
PLUS_S = "+"
MINUS_S = "-"
MULTIPLICATION_S = "*"
MULTIPLICATION_2 = " "
DIVISION_S = "/"
EXP_S = "E"
EXPS = "Ee"
POWER_S = "^"
LOGICAL_AND = "&&"
LOGICAL_OR = "||"
LOGICAL_NOT = "!"
BITWISE_AND = "&"
BITWISE_OR = "|"
BITWISE_NOT = "~"
SHIFT_RIGHT = ">>"
SHIFT_LEFT = "<<"
LESS_S = "<"
GREATER_S = ">"
NOT_S = "!"
EQUALS_S = "="
SINF = "INF"
UNDERSCORE = "_"

NOT_IN_NAMES = RESERVED + OPERATORS + SPACES + SEXADOT + DOT_S + VECTOR_WRAPS + PARENTHESISS + COMMAS


# ---------------------------------------------------------------------------
# Default instances (module-level singletons)
# ---------------------------------------------------------------------------

default_sort_options = SortOptions()
default_print_options = PrintOptions()
default_parse_options = ParseOptions()
default_evaluation_options = EvaluationOptions()
