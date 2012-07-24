'''
Created on 2012-06-04

@author: ahven
'''

import datetime
import re


# http://stackoverflow.com/questions/304256/whats-the-best-way-to-find-the-inverse-of-datetime-isocalendar
def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"

    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    year_start = fourth_jan - delta

    return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)


class InvalidRangeFormatError(Exception):

    def __init__(self, range_specs):
        self.range_specs = range_specs

    def __str__(self):
        return "Invalid range: " + self.range_specs


class PatternDecoratorDispatcher:
    """
    Decorator-based regex pattern dispatcher
    """

    def __init__(self):
        self.patterns = []

    def register(self, pattern):
        """Decorator to register a dispatching function"""
        regex = re.compile(pattern)
        def wrap(func):
            self.patterns.append( (regex, func) )
            return func
        return wrap

    def dispatch(self, obj, text):
        """
        Call the first registered function whose pattern matches given text.
        Passes a tuple containing all the subgroups of the match.
        Return True if there was a match and a function was called.
        Return False otherwise.
        """
        for regex, func in self.patterns:
            match = regex.search(text)
            if match:
                func(obj, match.groups())
                return True
        return False


class DayRange:
    '''
    A range of days

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

    Range formats:
     * <first>..<last>
    '''

    patterns = PatternDecoratorDispatcher()

    def __init__(self, range_specs):
        '''
        Constructor
        '''
        self.set_range_text(range_specs)

    def first_day(self):
        return self._first

    def last_day(self):
        return self._last

    def is_valid(self):
        return self._first <= self._last

    def set_range_text(self, range_specs):
        try:
            if not DayRange.patterns.dispatch(self, range_specs):
                raise InvalidRangeFormatError(range_specs)
        except ValueError:
            raise InvalidRangeFormatError(range_specs)

    def set_range(self, first, last):
        self._first = first
        self._last = last

    def set_date(self, date):
        self._first = date
        self._last = date

    def contains(self, date):
        return self._first <= date and date <= self._last

    @patterns.register(
            r'^([12][0-9]{3})(-?)(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$')
    def _pattern_yyyy_mm_dd(self, groups):
        self.set_date(
                datetime.date(int(groups[0]), int(groups[2]), int(groups[3])))

    @patterns.register(r'^(0?[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$')
    def _pattern_mm_dd(self, groups):
        today = datetime.date.today()
        month = int(groups[0])
        day = int(groups[1])

        if month > today.month or (month == today.month and day > today.day):
            # Month-day is past today in this year.  Use the last year.
            year = today.year - 1
        else:
            # Month-day is today or less.  Use the current year.
            year = today.year

        self.set_date(datetime.date(year, month, day))

    @patterns.register(r'^(0?[1-9]|[12][0-9]|3[01])$')
    def _pattern_dd(self, groups):
        today = datetime.date.today()
        year = today.year
        month = today.month
        day = int(groups[0])

        if day > today.day:
            month = month - 1
            if month < 1:
                month = 12
                year = year - 1

        self.set_date(datetime.date(year, month, day))

    @patterns.register(
            r'^([12][0-9]{3})(-?)[wW](0[1-9]|[1-4][0-9]|5[0-3])\2([1-7])')
    def _pattern_iso_week_date(self, groups):
        self.set_date(iso_to_gregorian(
                    int(groups[0]), int(groups[2]), int(groups[3])))

    @patterns.register(r'^-(0|[1-9][0-9]*)$')
    def _pattern_x_days_ago(self, groups):
        today = datetime.date.today()
        self.set_date(today - datetime.timedelta(int(groups[0])))

    @patterns.register(r'^0$')
    def _pattern_today(self, groups):
        self.set_date(datetime.date.today())

    @patterns.register(r'^([12][0-9]{3})-?[wW](0[1-9]|[1-4][0-9]|5[0-3])$')
    def _pattern_iso_week(self, groups):
        self.set_range(
                iso_to_gregorian(int(groups[0]), int(groups[1]), 1),
                iso_to_gregorian(int(groups[0]), int(groups[1]), 7))

    @patterns.register(r'^[wW](0?[1-9]|[1-4][0-9]|5[0-3])$')
    def _pattern_w_ww(self, groups):
        self.set_date(datetime.date.today())
        today = datetime.date.today()
        (today_year, today_week) = today.isocalendar()[0:2]
        week = int(groups[0])

        if week > today_week:
            # Week is past current week in this year.  Use the last year.
            year = today_year - 1
        else:
            # Week is current week in this year or less.  Use the current year.
            year = today_year

        self.set_range(
                iso_to_gregorian(year, week, 1),
                iso_to_gregorian(year, week, 7))

    @patterns.register(r'^([^.]*)\.\.([^.]*)$')
    def _pattern_first_last(self, groups):
        if groups[0] == '':
            self._first = datetime.date.min
        else:
            self._first = DayRange(groups[0])._first

        if groups[1] == '':
            self._last = datetime.date.max
        else:
            self._last = DayRange(groups[1])._last
