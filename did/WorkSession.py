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

from WorkInterval import WorkInterval

class WorkSession(object):
    '''
    classdocs
    '''


    def __init__(self, start, is_workday=True, filter_regex=None):
        '''
        start - When the day starts

        is_workday - True if this is your workday,
            False if this complete session is overhours
        '''
        self.start_ = start
        self.is_workday_ = is_workday
        self.intervals_ = []
        self.filter_regex_ = filter_regex

    def append_log_event(self, datetime, text):
        self.intervals_.append(WorkInterval(
                self.end(), datetime, text, False, self._is_matched(text)))

    def append_assumed_interval(self, datetime):
        if len(self.intervals_) > 0:
            name = self.intervals_[-1].name()
            self.intervals_.append(
                    WorkInterval(
                        self.end(), datetime, name, True, self._is_matched(name)))

    def set_filter_regex(self, regex):
        self.filter_regex_ = regex

    def has_filter(self):
        return self.filter_regex_ is not None

    def has_matched_jobs(self):
        for interval in self.intervals_:
            if interval.is_selected():
                return True
        return False

    def _is_matched(self, name):
        if self.filter_regex_ is None:
            return True
        else:
            return self.filter_regex_.search(name) is not None

    def matched_work_time(self, adjusted):
        duration = datetime.timedelta(0)
        for interval in self.intervals_:
            if interval.is_selected() and not interval.is_break():
                duration += interval.duration(adjusted)
        return duration

    def matched_break_time(self, adjusted):
        duration = datetime.timedelta(0)
        for interval in self.intervals_:
            if interval.is_selected() and interval.is_break():
                duration += interval.duration(adjusted)
        return duration

    def start(self):
        return self.start_

    def end(self):
        if len(self.intervals_) == 0:
            return self.start_
        else:
            return self.intervals_[-1].end()

    def is_workday(self):
        return self.is_workday_

    def intervals(self):
        return self.intervals_

    def last_break_interval(self):
        for interval in reversed(self.intervals_):
            if interval.is_break():
                return interval
        return None

    def last_work_interval(self):
        for interval in reversed(self.intervals_):
            if not interval.is_break():
                return interval
        return None

    def set_stats(self, stats):
        self.stats_ = stats

    def set_total_overtime(self, total_overtime):
        self.total_overtime_ = total_overtime

    def stats(self):
        return self.stats_

    def total_overtime(self):
        return self.total_overtime_

    def map_names(self, func):
        for interval in self.intervals_:
            interval.set_name(func(interval.name()))
