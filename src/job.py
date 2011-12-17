# -*- coding: utf-8 -*-
"""
Copyright (C) 2011 Michał Czuczman

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

import abc
import datetime
import re

class Job:
    __metaclass__ = abc.ABCMeta
    def __init__(self, start, end, name, num):
        assert start <= end
        self.start = start
        self.end = end
        self.name = name
        self.num = num

    @abc.abstractmethod
    def letter(self):
        """Return a letter describing the job type"""

    def duration(self, date):
        """
        Return a datetime.timedelta specifying how long this job lasted on the
        given day.
        Return None if given day is out of range.
        Return False if duration doesn't make sense.
        """
        # I'd prefer datetime.datetime to datetime.date
        if isinstance(date, datetime.date):
            date = datetime.datetime(date.year, date.month, date.day)
        if date.date() < self.start.date():
            return None
        elif date.date() == self.start.date():
            if date.date() == self.end.date():
                return self.end - self.start
            else:
                return date + datetime.timedelta(1) - self.start
        elif date.date() < self.end.date():
            return datetime.timedelta(1)
        elif date.date() == self.end.date():
            return self.end - date
        else:
            return None

    def starts_on(self, date):
        return self.start.date() == date

    def ends_on(self, date):
        return self.end.date() == date


class TaskJob(Job):
    def letter(self):
        return 'T'


class BreakJob(Job):
    def letter(self):
        return 'B'


class ArriveJob(Job):
    def letter(self):
        return 'A'

    def duration(self, date):
        return False

    def starts_on(self, date):
        return False


class CurrentJob(Job):
    def letter(self):
        return 'C'


class JobFactory:
    def create(self, start, end, name, num):
        cls = self.name_to_class(name)
        job = cls(start, end, name, num)
        return job

    def name_to_class(self, name):
        if re.match("##", name):
            return CurrentJob
        elif name == 'arrive':
            return ArriveJob
        elif re.match("\\.", name) or re.search("\\*\\*", name):
            return BreakJob
        else:
            return TaskJob


class JobList:
    def __init__(self):
        self.jobs = []

    def push_job(self, date, name):
        job = JobFactory().create(self.last_end(), date, name, len(self.jobs))
        self.jobs.append(job)

    def last_end(self):
        if len(self.jobs) > 0:
            return self.jobs[-1].end
        else:
            return datetime.datetime.min

    def __iter__(self):
        return self.jobs.__iter__()

    def __len__(self):
        return len(self.jobs)

    def __contains__(self, v):
        return v in self.jobs

    def __getitem__(self, v):
        return self.jobs[v]
