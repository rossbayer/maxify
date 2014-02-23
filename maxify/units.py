"""
Module defines available units that can be assigned to an individual metric.
"""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import locale
import os
import re

# By default, force locale-specific formatting into default locale specified
# via the LANG environment variable.
lang = os.environ.get("LANG")
if lang:
    locale.setlocale(locale.LC_ALL, lang)


class ParsingError(BaseException):
    """Type of error generated due to a bad attempt at a data conversion.
    """
    pass


class Unit(object):
    """Basetype for different units of measurement that can be associated with
    a metric.

    """

    @staticmethod
    def parse(s):
        """Parses a string value and returns an object representing the runtime
        value of the string.

        :param str s: The string value to parse.

        :return: The parsed value.
        :raises ParsingError: Raised if the value cannot be parsed by the
        unit type.

        """
        raise NotImplementedError("Method not implemented on base class")

    @staticmethod
    def to_str(value):
        """Converts a persisted, internal representation of a metric's value
        into a string representation that can be displayed in a user interface
        or the REPR based on the type of unit.

        :param value: The value to convert.

        :return: `str` with display value of the provided value.

        """
        return value

    @classmethod
    def display_name(cls):
        """The display name of the unit type.

        """
        return cls.__name__


class Int(Unit):
    """An integer unit."""

    @staticmethod
    def parse(s):
        try:
            return int(s)
        except ValueError:
            raise ParsingError("Invalid int expression: " + s)

    @staticmethod
    def to_str(value):
        return format(value, "n")


class Float(Unit):
    """A floating-point number unit."""

    @staticmethod
    def parse(s):
        try:
            return Decimal(s)
        except InvalidOperation:
            raise ParsingError("Invalid float expression: " + s)

    @staticmethod
    def to_str(value):
        return format(value, "n")


class Duration(Unit):
    """A time duration unit equivalent to a span of time"""

    # Collection of strings representing unit of duration mapped to a number of
    # seconds.
    _durations = (
        ({"days", "day", "d"}, 86400),
        ({"hours", "hour", "hrs", "hr", "h"}, 3600),
        ({"minutes", "minute", "mins", "min", "m"}, 60),
        ({"seconds", "second", "secs", "sec", "s"}, 1)
    )

    # Regex used to parse a duration string
    _expr_re = re.compile("(?:(?P<unit>[A-Za-z]+)\s*(?P<num>\d+\.?\d*))|"
                          "(?:(?P<num_alt>\d+\.?\d*)\s*(?P<unit_alt>[A-Za-z]+)"
                          ")")

    @classmethod
    def parse(cls, s):
        if s is None:
            return None

        if isinstance(s, Decimal):
            return s

        if isinstance(s, int):
            return Decimal(s)

        # First, attempt to parse it as a time format
        value = cls._try_parse_time_fmt(s)
        if value:
            return value

        value = Decimal(0)
        for match in cls._expr_re.finditer(s):
            num = match.group("num") if match.group("num") \
                else match.group("num_alt")
            unit = match.group("unit") if match.group("unit") \
                else match.group("unit_alt")

            found_units = [(u, m) for (u, m) in cls._durations if unit in u]
            if not len(found_units):
                raise ParsingError("Invalid duration expression: " +
                                   match.group())
            _, multiplier = found_units[0]
            value += Decimal(num) * multiplier

        return value

    @staticmethod
    def to_str(value):
        duration = timedelta(seconds=value)
        return str(duration)

    @staticmethod
    def _try_parse_time_fmt(s):
        dt = None
        try:
            dt = datetime.strptime(s, "%H:%M:%S")
        except ValueError:
            pass

        try:
            dt = datetime.strptime(s, "%H:%M")
        except ValueError:
            pass

        if dt:
            t = dt.time()
            return t.hour * 3600 + t.minute * 60 + t.second
        else:
            return None


#: Set of available unit types
units = [
    Duration,
    Int,
    Float
]


def determine_unit_and_value(str_value):
    """For a given string value, determine the type of unit is represents and
    parse its value.

    :param str str_value: Value to determine unit type for.

    :return: Tuple in the form of (:class:`Unit`, object) if a valid unit is
    found.  If no valid unit type is determined from the specified value,
    ``(None, None)`` will be returned.

    :rtype: tuple

    """
    for unit_type in units:
        try:
            value = unit_type.parse(str_value)
            if value:
                return unit_type, value
        except ParsingError:
            pass

    return None, None