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
from WorkSession import WorkSession


class FirstJobNotArriveError(Exception):
    """Raised when trying to append a first log event, which is not an "arrive".
    """
    def __str__(self):
        return "First log event is not an \"arrive\""


class NonChronologicalOrderError(Exception):
    """Raised when trying to append a job with an earlier time than the job
    added last.

    Attributes:
        last_datetime - -The time of the last job on the list.
        appended_datetime - -The time of the job attempted to be added.
    """
    def __init__(self, last, appended):
        self.last_datetime = last
        self.appended_datetime = appended


class WorkLog(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.sessions_ = []

    def _check_chronology(self, datetime):
        end = self.end()
        if end != None and end > datetime:
            raise NonChronologicalOrderError(end, datetime)

    def append_log_event(self, datetime, text):
        self._check_chronology(datetime)

        if text == "arrive":
            self.sessions_.append(WorkSession(datetime, True))
        elif text == "arrive ooo":
            self.sessions_.append(WorkSession(datetime, False))
        else:
            if len(self.sessions_) == 0:
                raise FirstJobNotArriveError()
            self.sessions_[-1].append_log_event(datetime, text)

    def append_assumed_interval(self, datetime):
        self._check_chronology(datetime)

        if len(self.sessions_) > 0:
            self.sessions_[-1].append_assumed_interval(datetime)

    def end(self):
        if len(self.sessions_) == 0:
            return None
        else:
            return self.sessions_[-1].end()

    def sessions(self):
        return self.sessions_

    def overhours(self, stats_factory):
        overhours = datetime.timedelta(0)
        for session in self.sessions_:
            stats = stats_factory.new_session_stats(session)
            overhours += stats.overhours()
        return overhours

    def last_break_interval(self):
        for session in reversed(self.sessions_):
            last_break = session.last_break_interval()
            if last_break is not None:
                return last_break
        return None

    def last_work_interval(self):
        for session in reversed(self.sessions_):
            last_work = session.last_work_interval()
            if last_work is not None:
                return last_work
        return None

    def compute_stats(self, stats_factory):
        total_overtime = datetime.timedelta(0)
        for session in self.sessions_:
            stats = stats_factory.new_session_stats(session)
            total_overtime += stats.overhours()
            session.set_stats(stats)
            session.set_total_overtime(total_overtime)

    def map_names(self, func):
        for session in self.sessions_:
            session.map_names(func)
