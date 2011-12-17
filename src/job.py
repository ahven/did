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


class JobListError(Exception):
    """Base class for all exceptions related to JobList"""
    pass


class FirstJobNotArriveError(JobListError):
    """Raised when trying to append a first job, which is not an "arrive" job.
    """
    def __str__(self):
        return "First job is not an \"arrive\" job"


class NonChronologicalOrderError(JobListError):
    """Raised when trying to append a job with an earlier time than the job
    added last.

    Attributes:
        last_datetime -- The time of the last job on the list.
        appended_datetime -- The time of the job attempted to be added.
    """
    def __init__(self, last, appended):
        self.last_datetime = last
        self.appended_datetime = appended


class JobList:
    def __init__(self):
        self.jobs = []
        self._days = {}

    def push_job(self, date, name):
        if date < self.last_end():
            raise NonChronologicalOrderError(self.last_end(), date)

        job = JobFactory().create(self.last_end(), date, name, len(self.jobs))
        if 0 == len(self.jobs):
            if not isinstance(job, ArriveJob):
                raise FirstJobNotArriveError()

        # Count the "days"
        if isinstance(job, ArriveJob):
            self._append_day(job.end.date(), len(self.jobs))
        else:
            day = job.start.date()
            last = job.end.date()
            while day <= last:
                self._append_day(day, len(self.jobs))
                day += datetime.timedelta(1)

        self.jobs.append(job)

    def days(self):
        """Return a list of datetime.date objects, when the jobs occur."""
        days = self._days.keys()
        days.sort()
        return days

    def first_job_for_day(self, day):
        """Return index of the first job in a given day.
        Return None if there are no such jobs."""
        if day in self._days:
            return self._days[day]
        else:
            return None

    def _append_day(self, day, index):
        if not day in self._days:
            self._days[day] = index


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
