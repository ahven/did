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
from job import BreakJob, CurrentJob, TaskJob


class JobDayStats:
    def __init__(self, joblist, day):
        self.joblist = joblist
        self.day = day
        self.work_time = datetime.timedelta(0)
        self.break_time = datetime.timedelta(0)
        self.current_time = datetime.timedelta(0)
        self._analyze()

    def _analyze(self):
        i = self.joblist.first_job_for_day(self.day)
        if i is not None:
            while i < len(self.joblist) and \
                    self.joblist[i].start.date() <= self.day:
                self._analyze_job(self.joblist[i])
                i += 1

    def _analyze_job(self, job):
        start = job.start
        end = job.end
        midnight = datetime.time(0, 0, 0)

        if start.date() < self.day:
            start = datetime.datetime.combine(self.day, midnight)
        if end.date() > self.day:
            end = datetime.datetime.combine(self.day, midnight)
            end += datetime.timedelta(1)

        diff = end - start

        if isinstance(job, TaskJob):
            self.work_time += diff;
        elif isinstance(job, BreakJob):
            self.break_time += diff
        elif isinstance(job, CurrentJob):
            self.current_time += diff

