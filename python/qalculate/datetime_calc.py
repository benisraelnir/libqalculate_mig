"""
Date/time types, calendar conversions, and date arithmetic.

Translated from libqalculate/QalculateDateTime.h and QalculateDateTime.cc.
Provides the QalculateDateTime class for date/time manipulation, along with
calendar conversion functions and astronomical calculation stubs.
"""

from __future__ import annotations

import calendar
import datetime
import math
from typing import Optional, Tuple

from .number import Number
from .includes import (
    CalendarSystem, PrintOptions, default_print_options,
    NUMBER_OF_CALENDARS,
)


def _is_leap_year(year: int) -> bool:
    """Check if a Gregorian year is a leap year."""
    return calendar.isleap(year)


def _days_in_month(year: int, month: int) -> int:
    """Return the number of days in a given month of a Gregorian year."""
    if month < 1 or month > 12:
        return 0
    return calendar.monthrange(year, month)[1]


class QalculateDateTime:
    """
    Date/time class supporting Gregorian calendar operations,
    date arithmetic, and timestamp conversion.
    """

    def __init__(self, year_or_ts_or_str=None, month=None, day=None):
        self._year: int = 0
        self._month: int = 1
        self._day: int = 1
        self._hour: int = 0
        self._minute: int = 0
        self._second: Number = Number(0)
        self._time_set: bool = False
        self.parsed_string: str = ""

        if year_or_ts_or_str is None:
            return
        elif isinstance(year_or_ts_or_str, QalculateDateTime):
            self._copy_from(year_or_ts_or_str)
        elif isinstance(year_or_ts_or_str, Number):
            self.set_from_timestamp(year_or_ts_or_str)
        elif isinstance(year_or_ts_or_str, str):
            self.set_from_string(year_or_ts_or_str)
        elif isinstance(year_or_ts_or_str, int) and month is not None and day is not None:
            self.set(year_or_ts_or_str, int(month), int(day))
        elif isinstance(year_or_ts_or_str, int):
            self._year = year_or_ts_or_str

    def _copy_from(self, other: 'QalculateDateTime') -> None:
        self._year = other._year
        self._month = other._month
        self._day = other._day
        self._hour = other._hour
        self._minute = other._minute
        self._second = Number(other._second)
        self._time_set = other._time_set
        self.parsed_string = other.parsed_string

    # ----- Comparison operators -----

    def _to_tuple(self) -> Tuple:
        return (self._year, self._month, self._day,
                self._hour, self._minute, self._second.floatValue())

    def __gt__(self, other: 'QalculateDateTime') -> bool:
        return self._to_tuple() > other._to_tuple()

    def __lt__(self, other: 'QalculateDateTime') -> bool:
        return self._to_tuple() < other._to_tuple()

    def __ge__(self, other: 'QalculateDateTime') -> bool:
        return self._to_tuple() >= other._to_tuple()

    def __le__(self, other: 'QalculateDateTime') -> bool:
        return self._to_tuple() <= other._to_tuple()

    def __ne__(self, other: 'QalculateDateTime') -> bool:
        return self._to_tuple() != other._to_tuple()

    def __eq__(self, other) -> bool:
        if not isinstance(other, QalculateDateTime):
            return NotImplemented
        return self._to_tuple() == other._to_tuple()

    # ----- Status queries -----

    def isFutureDate(self) -> bool:
        now = QalculateDateTime()
        now.setToCurrentDate()
        return self > now

    def isPastDate(self) -> bool:
        now = QalculateDateTime()
        now.setToCurrentDate()
        return self < now

    def timeIsSet(self) -> bool:
        return self._time_set

    # ----- Setters -----

    def setToCurrentDate(self) -> None:
        now = datetime.datetime.now()
        self._year = now.year
        self._month = now.month
        self._day = now.day
        self._hour = 0
        self._minute = 0
        self._second = Number(0)
        self._time_set = False

    def setToCurrentTime(self) -> None:
        now = datetime.datetime.now()
        self._year = now.year
        self._month = now.month
        self._day = now.day
        self._hour = now.hour
        self._minute = now.minute
        self._second = Number(now.second)
        self._time_set = True

    def set(self, year_or_date=None, month=None, day=None) -> bool:
        if isinstance(year_or_date, QalculateDateTime):
            self._copy_from(year_or_date)
            return True
        if isinstance(year_or_date, Number):
            return self.set_from_timestamp(year_or_date)
        if isinstance(year_or_date, str):
            return self.set_from_string(year_or_date)
        if year_or_date is not None and month is not None and day is not None:
            self._year = int(year_or_date)
            self._month = int(month)
            self._day = int(day)
            self._hour = 0
            self._minute = 0
            self._second = Number(0)
            self._time_set = False
            return True
        return False

    def set_from_timestamp(self, ts: Number) -> bool:
        """Set date from Unix timestamp."""
        try:
            t = float(ts._to_mpf())
            dt = datetime.datetime.utcfromtimestamp(t)
            self._year = dt.year
            self._month = dt.month
            self._day = dt.day
            self._hour = dt.hour
            self._minute = dt.minute
            self._second = Number(dt.second)
            self._time_set = True
            return True
        except (OSError, ValueError, OverflowError):
            return False

    def set_from_string(self, date_string: str) -> bool:
        """Parse a date string in ISO format or common formats."""
        self.parsed_string = date_string
        s = date_string.strip().strip('"')

        # Try ISO format: YYYY-MM-DD or YYYY-MM-DDThh:mm:ss
        try:
            if 'T' in s:
                dt = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
                self._year = dt.year
                self._month = dt.month
                self._day = dt.day
                self._hour = dt.hour
                self._minute = dt.minute
                self._second = Number(dt.second)
                self._time_set = True
                return True
            else:
                parts = s.split('-')
                if len(parts) == 3:
                    self._year = int(parts[0])
                    self._month = int(parts[1])
                    self._day = int(parts[2])
                    self._time_set = False
                    return True
        except (ValueError, IndexError):
            pass
        return False

    def setYear(self, year: int) -> None:
        self._year = year

    def setTime(self, hour: int, minute: int, sec: Number) -> bool:
        self._hour = hour
        self._minute = minute
        self._second = Number(sec)
        self._time_set = True
        return True

    # ----- Accessors -----

    def year(self) -> int:
        return self._year

    def month(self) -> int:
        return self._month

    def day(self) -> int:
        return self._day

    def hour(self) -> int:
        return self._hour

    def minute(self) -> int:
        return self._minute

    def second(self) -> Number:
        return self._second

    # ----- Date arithmetic -----

    def addDays(self, ndays: Number) -> bool:
        d = int(ndays._to_mpf())
        try:
            dt = datetime.date(self._year, self._month, self._day) + datetime.timedelta(days=d)
            self._year = dt.year
            self._month = dt.month
            self._day = dt.day
            return True
        except (ValueError, OverflowError):
            return False

    def addMonths(self, nmonths: Number) -> bool:
        m = int(nmonths._to_mpf())
        total_months = self._year * 12 + (self._month - 1) + m
        self._year = total_months // 12
        self._month = (total_months % 12) + 1
        # Clamp day
        max_day = _days_in_month(self._year, self._month)
        if self._day > max_day:
            self._day = max_day
        return True

    def addYears(self, nyears: Number) -> bool:
        y = int(nyears._to_mpf())
        self._year += y
        # Handle Feb 29 in non-leap years
        if self._month == 2 and self._day == 29 and not _is_leap_year(self._year):
            self._day = 28
        return True

    def addHours(self, nhours: Number) -> bool:
        h = int(nhours._to_mpf())
        self._time_set = True
        total_min = self._hour * 60 + self._minute + h * 60
        extra_days, remaining_min = divmod(total_min, 24 * 60)
        self._hour = remaining_min // 60
        self._minute = remaining_min % 60
        if extra_days:
            self.addDays(Number(extra_days))
        return True

    def addMinutes(self, nminutes: Number, remove_leap_second=True, convert_to_utc=True) -> bool:
        m = int(nminutes._to_mpf())
        self._time_set = True
        total_min = self._hour * 60 + self._minute + m
        extra_days, remaining_min = divmod(total_min, 24 * 60)
        self._hour = remaining_min // 60
        self._minute = remaining_min % 60
        if extra_days:
            self.addDays(Number(extra_days))
        return True

    def addSeconds(self, seconds: Number, count_leap_seconds=True, convert_to_utc=True) -> bool:
        s = float(seconds._to_mpf())
        self._time_set = True
        total_sec = self._hour * 3600 + self._minute * 60 + float(self._second._to_mpf()) + s
        extra_days = int(total_sec // 86400)
        remaining = total_sec - extra_days * 86400
        if remaining < 0:
            extra_days -= 1
            remaining += 86400
        self._hour = int(remaining // 3600)
        remaining -= self._hour * 3600
        self._minute = int(remaining // 60)
        remaining -= self._minute * 60
        self._second = Number(int(remaining))
        if extra_days:
            self.addDays(Number(extra_days))
        return True

    def add(self, date: 'QalculateDateTime') -> bool:
        """Add another date's components as a duration."""
        self.addYears(Number(date._year))
        self.addMonths(Number(date._month))
        self.addDays(Number(date._day))
        if date._time_set:
            self.addHours(Number(date._hour))
            self.addMinutes(Number(date._minute))
            self.addSeconds(date._second)
        return True

    # ----- Calendar queries -----

    def weekday(self) -> int:
        """Return day of week (1=Monday, 7=Sunday)."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return dt.isoweekday()
        except ValueError:
            return 0

    def week(self, start_sunday: bool = False) -> int:
        """Return ISO week number."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return dt.isocalendar()[1]
        except ValueError:
            return 0

    def yearday(self) -> int:
        """Return day of year (1-based)."""
        try:
            dt = datetime.date(self._year, self._month, self._day)
            return dt.timetuple().tm_yday
        except ValueError:
            return 0

    # ----- Timestamp / conversion -----

    def timestamp(self, reverse_utc: bool = False) -> Number:
        """Return Unix timestamp as Number."""
        try:
            dt = datetime.datetime(self._year, self._month, self._day,
                                   self._hour, self._minute, int(self._second._to_mpf()))
            epoch = datetime.datetime(1970, 1, 1)
            delta = dt - epoch
            return Number(int(delta.total_seconds()))
        except (ValueError, OverflowError):
            return Number(0)

    def toISOString(self) -> str:
        """Return ISO 8601 date string."""
        if self._time_set:
            return f"{self._year:04d}-{self._month:02d}-{self._day:02d}T{self._hour:02d}:{self._minute:02d}:{int(self._second._to_mpf()):02d}"
        return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

    def toLocalString(self) -> str:
        """Return locale-formatted date string."""
        return self.toISOString()

    def print(self, po: PrintOptions = None) -> str:
        if po is None:
            po = default_print_options
        return f'"{self.toISOString()}"'

    # ----- Time difference -----

    def secondsTo(self, date: 'QalculateDateTime',
                  count_leap_seconds: bool = True,
                  convert_to_utc: bool = True) -> Number:
        """Return number of seconds between self and date."""
        ts1 = self.timestamp()
        ts2 = date.timestamp()
        result = Number(ts2)
        result.subtract(ts1)
        return result

    def daysTo(self, date: 'QalculateDateTime', basis: int = 1,
               date_func: bool = True, remove_leap_seconds: bool = True) -> Number:
        """Return number of days between self and date."""
        try:
            d1 = datetime.date(self._year, self._month, self._day)
            d2 = datetime.date(date._year, date._month, date._day)
            delta = (d2 - d1).days
            return Number(delta)
        except ValueError:
            return Number(0)

    def yearsTo(self, date: 'QalculateDateTime', basis: int = 1,
                date_func: bool = True, remove_leap_seconds: bool = True) -> Number:
        """Return approximate number of years between self and date."""
        days = self.daysTo(date, basis, date_func, remove_leap_seconds)
        result = Number(days)
        result.divide(Number(36525, 100))  # 365.25
        return result


# ---------------------------------------------------------------------------
# Calendar conversion functions (stubs for now)
# ---------------------------------------------------------------------------

def calendarToDate(date: QalculateDateTime, y: int, m: int, d: int,
                   ct: CalendarSystem) -> bool:
    """Convert a calendar date to Gregorian. Stub - only Gregorian supported."""
    if ct == CalendarSystem.GREGORIAN:
        return date.set(y, m, d)
    # TODO: implement other calendar systems
    return date.set(y, m, d)


def dateToCalendar(date: QalculateDateTime,
                   ct: CalendarSystem) -> Tuple[int, int, int]:
    """Convert Gregorian date to another calendar system. Stub."""
    return (date.year(), date.month(), date.day())


def numberOfMonths(ct: CalendarSystem) -> int:
    """Return the number of months in a calendar system."""
    if ct == CalendarSystem.GREGORIAN:
        return 12
    elif ct == CalendarSystem.HEBREW:
        return 13
    elif ct == CalendarSystem.EGYPTIAN:
        return 13
    elif ct == CalendarSystem.COPTIC:
        return 13
    elif ct == CalendarSystem.ETHIOPIAN:
        return 13
    return 12


def monthName(month: int, ct: CalendarSystem,
              append_number: bool = False, append_leap: bool = True) -> str:
    """Return the name of a month. Basic implementation for Gregorian."""
    if ct == CalendarSystem.GREGORIAN:
        names = ["", "January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        if 1 <= month <= 12:
            return names[month]
    return str(month)


# Astronomical function stubs
def solarLongitude(date: QalculateDateTime) -> Number:
    """Calculate solar longitude. Stub."""
    return Number(0)


def findNextSolarLongitude(date: QalculateDateTime, longitude: Number) -> QalculateDateTime:
    """Find next date with given solar longitude. Stub."""
    return QalculateDateTime(date)


def lunarPhase(date: QalculateDateTime) -> Number:
    """Calculate lunar phase. Stub."""
    return Number(0)


def findNextLunarPhase(date: QalculateDateTime, phase: Number) -> QalculateDateTime:
    """Find next date with given lunar phase. Stub."""
    return QalculateDateTime(date)


# Chinese calendar stubs
def chineseYearInfo(year: int) -> Tuple[int, int, int, int]:
    """Return (cycle, year_in_cycle, stem, branch) for a Chinese year. Stub."""
    return (0, 0, 0, 0)


def chineseCycleYearToYear(cycle: int, year_in_cycle: int) -> int:
    """Convert Chinese cycle+year to Gregorian year. Stub."""
    return 0


def chineseStemBranchToCycleYear(stem: int, branch: int) -> int:
    """Convert stem+branch to cycle year. Stub."""
    return 0


def chineseStemName(stem: int) -> str:
    """Return Chinese stem name. Stub."""
    return ""


def chineseBranchName(branch: int) -> str:
    """Return Chinese branch name. Stub."""
    return ""
