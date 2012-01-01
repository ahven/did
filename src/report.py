# -*- coding: utf-8 -*-
"""
Copyright (C) 2011-2012 Michał Czuczman

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
from job import ArriveJob, BreakJob, CurrentJob, TaskJob


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


class JobReport:
    def __init__(self, joblist):
        self.joblist = joblist
        self.current_day = datetime.datetime.min

    def display(self):
        for day in self.joblist.days():
            self._print_day(day)

    def _print_day(self, day):
        self._print_day_header(day)

        i = self.joblist.first_job_for_day(day)
        if i is not None:
            while i < len(self.joblist) and self.joblist[i].start.date() <= day:
                self._print_job_line(self.joblist[i], day)
                i += 1

        self._print_day_footer(day)

    def _print_day_header(self, day):
        print
        print day

    def _print_day_footer(self, day):
        stats = JobDayStats(self.joblist, day)
        if stats.current_time > datetime.timedelta(0):
            print "  Worked %s (+current=%s)   Slacked %s (+current=%s)" % (
                self.duration_to_string(stats.work_time),
                self.duration_to_string(stats.work_time + stats.current_time),
                self.duration_to_string(stats.break_time),
                self.duration_to_string(stats.break_time + stats.current_time))
        else:
            print "  Worked %-6s   Slacked %s" % (
                    self.duration_to_string(stats.work_time),
                    self.duration_to_string(stats.break_time))

    def _print_job_line(self, job, day):
        start_time = False
        end_time = False
        if job.starts_on(day):
            start_time = job.start
        if job.ends_on(day):
            end_time = job.end
        duration = job.duration(day)

        if isinstance(job, ArriveJob) and end_time == False:
            return

        print "  %s .. %s  %s  %-30s  %s" % (
                self.time_as_string(start_time),
                self.time_as_string(end_time),
                job.letter(),
                job.name,
                self.duration_to_string(duration))

    @staticmethod
    def duration_to_string(diff):
        if diff is None or diff is False:
            return ''
        hours = diff.days * 24 + diff.seconds / 3600
        minutes = (diff.seconds / 60) % 60
        time = ''
        if '' != time or 0 < hours:
            time += "%dh" % hours
        time += "%dm" % minutes
        return time

    @staticmethod
    def time_as_string(time):
        if time:
            return "%02d:%02d" % (time.hour, time.minute)
        else:
            return "     "
