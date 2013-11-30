"""
Module defines DSL/API for configuring a project via a Python.
"""

from datetime import datetime
from decimal import Decimal
import inspect
import re


class ConfigError(BaseException):
    """Type of error generated due to a configuration error, such as defining
    invalid units or metrics.
    """
    pass

class DataConversionError(BaseException):
    """Type of error generated due to a bad attempt at a data conversion.

    """
    pass


class Project(object):
    def __init__(self, name, desc, **kwargs):
        self.name = name
        self.desc = desc
        # Copy over any additional metadata/properties provided as keyword
        # arg
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self.metrics = {}

    def add_metric(self,
                   name,
                   units,
                   desc=None,
                   range=None,
                   default_value=None):
        if name in self.metrics:
            raise ConfigError("A metric named {0} already exists for this "
                              "project.")

        self.metrics[name] = Metric(name,
                                    units,
                                    desc=desc,
                                    range=range,
                                    default_value=default_value)

    def metric(self, name):
        return self.metrics[name]


class Metric(object):
    def __init__(self,
                 name,
                 units,
                 desc=None,
                 range=None,
                 default_value=None):
        if not inspect.isclass(units):
            raise ConfigError("Units specified must be a Unit class.")

        if not issubclass(units, Unit):
            raise ConfigError("A Metric's units must be a valid type of Unit.")

        self.name = name
        self.units = units
        self.desc = desc
        self.range = range
        self.default_value = default_value


class Unit(object):
    @staticmethod
    def parse(s):
        raise NotImplementedError("Method not implemented on base class")


class Int(Unit):
    @staticmethod
    def parse(s):
        return int(str)


class Float(Unit):
    @staticmethod
    def parse(s):
        return Decimal(s)


class Duration(Unit):
    units = (
        ({"hours", "hour", "hrs", "hr", "h"}, 3600),
        ({"minutes", "minute", "mins", "min", "m"}, 60),
        ({"seconds", "second", "secs", "sec", "s"}, 1)
    )

    expr_re = re.compile("(?:(?P<unit>[A-Za-z]+)\s*(?P<num>\d+\.?\d*))|"
                         "(?:(?P<num_alt>\d+\.?\d*)\s*(?P<unit_alt>[A-Za-z]+))")

    @classmethod
    def parse(cls, s):
        # Examples:
        # hrs, hours, h, hr
        # min, mins, m, minutes
        # sec, seconds, s, secs
        # days, d, day

        # HH:MM:SS
        # 55:10:00
        # 3 days, 2 hours, 10 mins
        # mins 10
        # 10h

        # First, attempt to parse it as a time format
        value = cls._try_parse_time_fmt(s)
        if value:
            return value

        # TODO - Expand this to handle multiple nested expressions, like
        # 4 hrs, 15 mins
        match = cls.expr_re.search(s)
        if match:
            num = match.group("num") if match.group("num") \
                else match.group("num_alt")
            unit = match.group("unit") if match.group("unit") \
                else match.group("unit_alt")

            _, multiplier = [(u, m) for (u, m) in cls.units if unit in u][0]
            value = Decimal(num) * multiplier

        return value

    @staticmethod
    def _try_parse_time_fmt(s):
        dt = None
        try:
            dt = datetime.strptime(s, "%H:%M:%S")
        except BaseException:
            pass

        try:
            dt = datetime.strptime(s, "%H:%M")
        except BaseException:
            pass

        if dt:
            t = dt.time()
            return t.hour * 3600 + t.minute * 60 + t.second
        else:
            return None


class Enum(Unit):
    pass


class String(Unit):
    pass