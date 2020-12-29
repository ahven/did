# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Michał Czuczman

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
from typing import List, Optional, Pattern, Tuple

from did.interval import Interval
from did.worktime import Accounting


class WorkSession(object):
    """
    classdocs
    """

    def __init__(self,
                 start: datetime.datetime,
                 accounting: Accounting,
                 is_workday: bool = True,
                 filter_regex: Optional[Pattern] = None,
                 events: Optional[List[Tuple[datetime.datetime, str]]] = None):
        """
        start - When the day starts

        is_workday - True if this is your workday,
            False if this complete session is overhours
        """
        self._start = start
        self._accounting = accounting
        self._is_workday = is_workday
        self._intervals: List[Interval] = []
        self._filter_regex = filter_regex

        if events is not None:
            for timestamp, event in events:
                self.append_log_event(timestamp, event)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkSession):
            return False
        return (self._start == other._start and
                self._is_workday == other._is_workday and
                self._intervals == other._intervals and
                self._filter_regex == other._filter_regex)

    def __repr__(self):
        return ('WorkSession(start="{}", is_workday={}, filter_regex={}, '
                'intervals={})'
                .format(self._start, self._is_workday, repr(self._filter_regex),
                        self._intervals))

    def append_log_event(self, date_time, text):
        self._intervals.append(Interval(
                self.end, date_time, text, False, self._is_matched(text)))

    def append_assumed_interval(self, date_time):
        if len(self._intervals) > 0:
            name = self._intervals[-1].name
            self._intervals.append(
                    Interval(self.end, date_time, name, True,
                             self._is_matched(name)))

    def set_filter_regex(self, regex):
        self._filter_regex = regex

    def has_filter(self):
        return self._filter_regex is not None

    def has_matched_jobs(self):
        for interval in self._intervals:
            if interval.is_selected:
                return True
        return False

    def _is_matched(self, name):
        if self._filter_regex is None:
            return True
        else:
            return self._filter_regex.search(name) is not None

    def matched_work_time(self, adjusted):
        duration = datetime.timedelta(0)
        for interval in self._intervals:
            if interval.is_selected and not interval.is_break:
                duration += interval.duration(adjusted)
        return duration

    def matched_break_time(self, adjusted):
        duration = datetime.timedelta(0)
        for interval in self._intervals:
            if interval.is_selected and interval.is_break:
                duration += interval.duration(adjusted)
        return duration

    @property
    def start(self):
        return self._start

    def accounting(self):
        return self._accounting

    @property
    def end(self):
        if len(self._intervals) == 0:
            return self._start
        else:
            return self._intervals[-1].end

    def is_workday(self):
        return self._is_workday

    def intervals(self):
        return self._intervals

    def last_break_interval(self):
        for interval in reversed(self._intervals):
            if interval.is_break:
                return interval
        return None

    def last_work_interval(self):
        for interval in reversed(self._intervals):
            if not interval.is_break:
                return interval
        return None

    def set_stats(self, stats):
        self._stats = stats

    def set_total_overtime(self, total_overtime):
        self._total_overtime = total_overtime

    def stats(self):
        return self._stats

    def total_overtime(self):
        return self._total_overtime
