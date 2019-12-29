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

import re

import datetime


class WorkInterval(object):
    """
    classdocs
    """

    def __init__(self, start, end, name, is_assumed=False, is_selected=True, is_break=None):
        """
        Constructor
        """
        self.start_ = start
        self.end_ = end
        self.name_ = name
        self.is_assumed_ = is_assumed
        self.is_selected_ = is_selected
        self.is_break_ = is_break if is_break is not None else self.name_is_break(self.name_)
        self.accounted_break_seconds_ = 0

    def is_break(self):
        return self.is_break_

    def is_assumed(self):
        return self.is_assumed_

    def is_selected(self):
        return self.is_selected_

    def start(self):
        return self.start_

    def end(self):
        return self.end_

    def real_duration(self):
        return self.end_ - self.start_

    def adjusted_duration(self):
        return (self.end_ - self.start_
                + datetime.timedelta(seconds=self.accounted_break_seconds_))

    def duration(self, adjusted):
        if adjusted:
            return self.adjusted_duration()
        else:
            return self.real_duration()

    def account_break_duration(self, seconds):
        self.accounted_break_seconds_ += seconds

    def account_work_duration(self, seconds):
        self.accounted_break_seconds_ -= seconds

    def name(self):
        return self.name_

    def set_name(self, name):
        self.name_ = name

    @staticmethod
    def name_is_break(name):
        # Break names start with a "." or contain "**"
        return re.match("\\.", name) or re.search("\\*\\*", name)
