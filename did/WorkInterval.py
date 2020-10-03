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
        self._start = start
        self._end = end
        self._name = name
        self._is_assumed = is_assumed
        self._is_selected = is_selected
        self._is_break = is_break if is_break is not None else self.name_is_break(self._name)
        self._accounted_break_seconds = 0

    def __repr__(self):
        return ('WorkInterval(start="{}", end="{}", name={}, is_assumed={}, '
                'is_selected={}, is_break={})'
                .format(self._start, self._end, repr(self._name),
                        self._is_assumed, self._is_selected, self._is_break))

    def __eq__(self, other: 'WorkInterval'):
        return (self._start == other._start and
                self._end == other._end and
                self._name == other._name and
                self._is_assumed == other._is_assumed and
                self._is_selected == other._is_selected and
                self._is_break == other._is_break and
                self._accounted_break_seconds == other._accounted_break_seconds)

    def is_break(self):
        return self._is_break

    def is_assumed(self):
        return self._is_assumed

    def is_selected(self):
        return self._is_selected

    def start(self):
        return self._start

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

    def name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    @staticmethod
    def name_is_break(name):
        # Break names start with a "." or contain "**"
        return bool(re.match("\\.", name) or re.search("\\*\\*", name))
