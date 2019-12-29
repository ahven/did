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


class WorkSessionStats(object):
    """
    Count total work time and break time for a WorkSession
    """

    def __init__(self, session):
        self.session_ = session
        self.time_worked_ = datetime.timedelta(0)
        self.time_slacked_ = datetime.timedelta(0)
        self._analyze()

    def _analyze(self):
        for interval in self.session_.intervals():
            duration = interval.end() - interval.start()
            if interval.is_break():
                self.add_break_time(duration)
            else:
                self.add_work_time(duration)

    def add_work_time(self, duration):
        self.time_worked_ += duration

    def add_break_time(self, duration):
        self.time_slacked_ += duration

    def add_work_seconds(self, seconds):
        self.add_work_time(datetime.timedelta(0, seconds))

    def add_break_seconds(self, seconds):
        self.add_break_time(datetime.timedelta(0, seconds))

    def time_worked(self):
        return self.time_worked_

    def time_slacked(self):
        return self.time_slacked_

    def overhours(self):
        return self.time_worked_ - self.expected_work_time()

    def expected_work_time(self):
        if self.session_.is_workday():
            seconds = 8 * 60 * 60
        else:
            seconds = 0
        return datetime.timedelta(0, seconds)
