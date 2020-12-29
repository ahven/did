# -*- coding: utf-8 -*-
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
from typing import Optional


def interval_name_denotes_a_break(name: str) -> bool:
    """Break names start with a "." or contain "**"."""
    return name.startswith(".") or "**" in name


class Interval:
    """The smallest unit of tracking time during which one activity was
    performed.
    """

    def __init__(self,
                 start: datetime.datetime,
                 end: datetime.datetime,
                 name: str,
                 is_assumed: bool = False,
                 is_break: Optional[bool] = None):
        """Make a new interval.

        If "is_break" is not provided explicitly, then it will be inferred
        from the name, treating this interval as a break in cases when the name
        starts with a "." or if it contains "**".
        """
        self._start = start
        self._end = end
        self.name = name
        self.is_assumed = is_assumed
        self._accounted_break_seconds = 0
        if is_break is not None:
            self.is_break = is_break
        else:
            self.is_break = interval_name_denotes_a_break(self.name)

    def __repr__(self):
        return ('Interval(start="{}", end="{}", name={}, is_assumed={}, '
                'is_break={})'
                .format(self._start, self._end, repr(self.name),
                        self.is_assumed, self.is_break))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return False
        return (self._start == other._start and
                self._end == other._end and
                self.name == other.name and
                self.is_assumed == other.is_assumed and
                self.is_break == other.is_break and
                self._accounted_break_seconds == other._accounted_break_seconds)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def real_duration(self):
        return self._end - self._start

    def adjusted_duration(self):
        return (self._end - self._start
                + datetime.timedelta(seconds=self._accounted_break_seconds))

    def duration(self, adjusted):
        if adjusted:
            return self.adjusted_duration()
        else:
            return self.real_duration()

    def account_break_duration(self, seconds):
        self._accounted_break_seconds += seconds

    def account_work_duration(self, seconds):
        self._accounted_break_seconds -= seconds
