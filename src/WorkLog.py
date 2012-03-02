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
        if self.end() != None and self.end() > datetime:
            raise NonChronologicalOrderError(self.end(), datetime)

    def append_log_event(self, datetime, text):
        self._check_chronology(datetime)

        if text == "arrive":
            self.sessions_.append(WorkSession(datetime, True))
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