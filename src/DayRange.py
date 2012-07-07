'''
Created on 2012-06-04

@author: ahven
'''

import datetime
import re

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

    def contains(self, date):
        return self._first <= date and date <= self._last

    @patterns.register(
            r'^([12][0-9]{3})(-?)(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$')
    def _pattern_yyyy_mm_dd(self, groups):
        self._first = datetime.date(
                int(groups[0]), int(groups[2]), int(groups[3]))
        self._last = self._first

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

        self._first = datetime.date(year, month, day)
        self._last = self._first

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
