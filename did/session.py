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
from typing import List, Optional, Tuple

from did.interval import Interval
from did.worktime import Accounting


class AppendingToClosedSessionError(Exception):
    def __init__(self):
        super().__init__(
            "Attempted to append to a session that was already closed")


class WorkSession(object):
    """
    classdocs
    """

    def __init__(self,
                 start: datetime.datetime,
                 accounting: Accounting,
                 is_workday: bool = True,
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
        self._is_closed = False

        if events is not None:
            for timestamp, event in events:
                self.append_log_event(timestamp, event)
            self._is_closed = True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkSession):
            return False
        return (self._start == other._start and
                self._is_workday == other._is_workday and
                self._intervals == other._intervals)

    def __repr__(self):
        return ('WorkSession(start="{}", is_workday={}, intervals={})'
                .format(self._start, self._is_workday, self._intervals))

    def append_log_event(self, date_time, text):
        if self._is_closed:
            raise AppendingToClosedSessionError()
        self._intervals.append(Interval(self.end, date_time, text, False))

    def append_assumed_interval(self, date_time):
        if self._is_closed:
            raise AppendingToClosedSessionError()
        if len(self._intervals) > 0:
            name = self._intervals[-1].name
            self._intervals.append(Interval(self.end, date_time, name, True))

    def close(self):
        self._is_closed = True

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
