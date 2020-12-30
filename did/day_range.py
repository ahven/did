"""
Copyright (C) 2012-2020 Michał Czuczman

This file is part of Did.

Did is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

Did is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Foobar; if not, write to the Free Software Foundation, Inc., 51 Franklin St,
Fifth Floor, Boston, MA  02110-1301  USA
"""
import datetime
from typing import Tuple

from did.dispatchers import RegexDispatcher, UnhandledDispatchError

today = datetime.date.today()


def date_from_isocalendar(iso_year: int,
                          iso_week: int,
                          iso_day: int
                          ) -> datetime.date:
    """Construct datetime.date() from given ISO year, week number and week day.
    This is the inverse of datetime.date.isocalendar()."""

    # http://stackoverflow.com/questions/304256/whats-the-best-way-to-find-the-inverse-of-datetime-isocalendar
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    year_start = fourth_jan - delta

    return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)


class InvalidRangeFormatError(Exception):
    """Exception raised when an invalid DayRange format was provided"""
    def __init__(self, range_specs):
        super().__init__()
        self.range_specs = range_specs

    def __str__(self):
        return "Invalid range: " + self.range_specs


TupleOfTwoDates = Tuple[datetime.date, datetime.date]


class DayRange:
    """A range of days. Multiple formats are supported.

    One day formats:
     * YYYY-MM-DD
     * YYYYMMDD
     * MM-DD, M-DD
     * DD, D
     * YYYY-Www-D
     * -X : X days ago

    Complete weeks:
     * YYYY-Www
     * Ww, Www

    Complete months:
     * YYYY-MM

    Complete years:
     * YYYY

    Range formats:
     * <first>..<last>
    """

    def __init__(self, range_spec: str):
        try:
            result = _parse_day_range(range_spec)  # type: TupleOfTwoDates
            self._first_day, self._last_day = result
        except UnhandledDispatchError:
            raise InvalidRangeFormatError(range_spec)
        except ValueError as error:
            # Creating the datetime.date() failed (e.g. for February 31st)
            raise InvalidRangeFormatError(range_spec) from error

    @property
    def first_day(self):
        """Return the first day of the range (read-only)"""
        return self._first_day

    @property
    def last_day(self):
        """Return the last day of the range (read-only)"""
        return self._last_day

    def __contains__(self, date):
        """Check if the given date belongs to this day range (inclusive)"""
        return self._first_day <= date <= self._last_day


_parse_day_range = RegexDispatcher()


def _one_day_range(date: datetime.date) -> Tuple[datetime.date, datetime.date]:
    """Return a (first, last) day range for a single day"""
    return date, date


@_parse_day_range.register(
        r'^([12][0-9]{3})(-?)(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$')
def _pattern_yyyy_mm_dd(groups: Tuple[str, ...]
                        ) -> Tuple[datetime.date, datetime.date]:
    return _one_day_range(
        datetime.date(int(groups[0]), int(groups[2]), int(groups[3])))


@_parse_day_range.register(r'^(0?[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$')
def _pattern_mm_dd(groups: Tuple[str, ...]
                   ) -> Tuple[datetime.date, datetime.date]:
    month = int(groups[0])
    day = int(groups[1])

    if month > today.month or (month == today.month and day > today.day):
        # Month-day is past today in this year.  Use the last year.
        year = today.year - 1
    else:
        # Month-day is today or less.  Use the current year.
        year = today.year

    return _one_day_range(datetime.date(year, month, day))


@_parse_day_range.register(r'^(0?[1-9]|[12][0-9]|3[01])$')
def _pattern_dd(groups: Tuple[str, ...]) -> Tuple[datetime.date, datetime.date]:
    year = today.year
    month = today.month
    day = int(groups[0])

    if day > today.day:
        month = month - 1
        if month < 1:
            month = 12
            year = year - 1

    return _one_day_range(datetime.date(year, month, day))


@_parse_day_range.register(
        r'^([12][0-9]{3})(-?)[wW](0[1-9]|[1-4][0-9]|5[0-3])\2([1-7])')
def _pattern_iso_week_date(groups: Tuple[str, ...]
                           ) -> Tuple[datetime.date, datetime.date]:
    return _one_day_range(date_from_isocalendar(
                int(groups[0]), int(groups[2]), int(groups[3])))


@_parse_day_range.register(r'^-(0|[1-9][0-9]*)$')
def _pattern_x_days_ago(groups: Tuple[str, ...]
                        ) -> Tuple[datetime.date, datetime.date]:
    return _one_day_range(today - datetime.timedelta(int(groups[0])))


@_parse_day_range.register(r'^0$')
def _pattern_today(groups: Tuple[str, ...]
                   ) -> Tuple[datetime.date, datetime.date]:
    # pylint: disable=unused-argument
    return _one_day_range(today)


@_parse_day_range.register(r'^([12][0-9]{3})-?[wW](0[1-9]|[1-4][0-9]|5[0-3])$')
def _pattern_iso_week(groups: Tuple[str, ...]
                      ) -> Tuple[datetime.date, datetime.date]:
    return (date_from_isocalendar(int(groups[0]), int(groups[1]), 1),
            date_from_isocalendar(int(groups[0]), int(groups[1]), 7))


@_parse_day_range.register(r'^[wW](0?[1-9]|[1-4][0-9]|5[0-3])$')
def _pattern_w_ww(groups: Tuple[str, ...]
                  ) -> Tuple[datetime.date, datetime.date]:
    (today_year, today_week) = today.isocalendar()[0:2]
    week = int(groups[0])

    if week > today_week:
        # Week is past current week in this year.  Use the last year.
        year = today_year - 1
    else:
        # Week is current week in this year or less.  Use the current year.
        year = today_year

    return (date_from_isocalendar(year, week, 1),
            date_from_isocalendar(year, week, 7))


@_parse_day_range.register(r'^[wW]-?0$')
def _pattern_current_week(groups: Tuple[str, ...]
                          ) -> Tuple[datetime.date, datetime.date]:
    # pylint: disable=unused-argument
    return (today - datetime.timedelta(today.weekday()),
            today + datetime.timedelta(6 - today.weekday()))


@_parse_day_range.register(r'^[wW]-([1-9][0-9]*)$')
def _pattern_x_weeks_ago(groups: Tuple[str, ...]
                         ) -> Tuple[datetime.date, datetime.date]:
    start = today - datetime.timedelta(today.weekday() + 7 * int(groups[0]))
    return start, start + datetime.timedelta(6)


@_parse_day_range.register(r'^([12][0-9]{3})-(0?[1-9]|1[012])$')
def _pattern_yyyy_mm(groups: Tuple[str, ...]
                     ) -> Tuple[datetime.date, datetime.date]:
    year = int(groups[0])
    month = int(groups[1])
    next_month = (month % 12) + 1
    if next_month == 1:
        next_months_year = year + 1
    else:
        next_months_year = year
    start = datetime.date(year, month, 1)
    end = (datetime.date(next_months_year, next_month, 1)
           - datetime.timedelta(1))
    return start, end


@_parse_day_range.register(r'^(2[0-9]{3})$')
def _pattern_yyyy(groups: Tuple[str, ...]
                  ) -> Tuple[datetime.date, datetime.date]:
    year = int(groups[0])
    return datetime.date(year, 1, 1), datetime.date(year, 12, 31)


@_parse_day_range.register(r'^([^.]*)\.\.([^.]*)$')
def _pattern_first_last(groups: Tuple[str, ...]
                        ) -> Tuple[datetime.date, datetime.date]:
    if groups[0] == '':
        first_day = datetime.date.min
    else:
        first_day = DayRange(groups[0]).first_day

    if groups[1] == '':
        last_day = datetime.date.max
    else:
        last_day = DayRange(groups[1]).last_day

    return first_day, last_day
