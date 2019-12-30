from datetime import timedelta
from unittest import TestCase

from did.worklog import parse_timedelta, InvalidParameter


class TestParseTimedelta(TestCase):
    def verify(self, value, expected):
        self.assertEqual(expected, parse_timedelta(value))

    def test_days(self):
        self.verify("0d", timedelta(0))
        self.verify("1d", timedelta(days=1))
        self.verify("9d", timedelta(days=9))
        self.verify("09d", timedelta(days=9))
        self.verify("123d", timedelta(days=123))
        self.verify("18D", timedelta(days=18))

    def test_hours(self):
        self.verify("0h", timedelta(0))
        self.verify("1h", timedelta(hours=1))
        self.verify("9h", timedelta(hours=9))
        self.verify("009h", timedelta(hours=9))
        self.verify("123h", timedelta(hours=123))

    def test_minutes(self):
        self.verify("0m", timedelta(0))
        self.verify("1m", timedelta(minutes=1))
        self.verify("9m", timedelta(minutes=9))
        self.verify("0009m", timedelta(minutes=9))
        self.verify("123m", timedelta(minutes=123))

    def test_seconds(self):
        self.verify("0s", timedelta(0))
        self.verify("1s", timedelta(seconds=1))
        self.verify("9s", timedelta(seconds=9))
        self.verify("123s", timedelta(seconds=123))
        self.verify("18S", timedelta(seconds=18))

    def test_hours_minutes(self):
        self.verify("0h10m", timedelta(minutes=10))
        self.verify("1h5m", timedelta(hours=1, minutes=5))
        self.verify("1h05m", timedelta(hours=1, minutes=5))
        self.verify("9h55m", timedelta(hours=9, minutes=55))
        self.verify("123h90m", timedelta(hours=123, minutes=90))

    def test_hours_space_minutes(self):
        self.verify("0h 10m", timedelta(minutes=10))
        self.verify("1h  5m", timedelta(hours=1, minutes=5))
        self.verify("1h 05m", timedelta(hours=1, minutes=5))
        self.verify("9h\t55m", timedelta(hours=9, minutes=55))
        self.verify("123h\t 90m", timedelta(hours=123, minutes=90))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_timedelta("0")
        with self.assertRaises(ValueError):
            parse_timedelta("10")
        with self.assertRaises(ValueError):
            parse_timedelta("5q")
