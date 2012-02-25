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

from WorkInterval import WorkInterval

class WorkSession(object):
    '''
    classdocs
    '''


    def __init__(self, start, is_workday=True):
        '''
        start - When the day starts

        is_workday - True if this is your workday,
            False if this complete session is overhours
        '''
        self.start_ = start
        self.is_workday_ = is_workday
        self.intervals_ = []

    def append_log_event(self, datetime, text):
        self.intervals_.append(WorkInterval(self.end(), datetime, text, False))

    def append_assumed_interval(self, datetime):
        if len(self.intervals_) > 0:
            self.intervals_.append(
                    WorkInterval(
                        self.end(), datetime, self.intervals_[-1].name(), True))

    def start(self):
        return self.start_

    def end(self):
        if len(self.intervals_) == 0:
            return self.start_
        else:
            return self.intervals_[-1].end()

    def intervals(self):
        return self.intervals_
