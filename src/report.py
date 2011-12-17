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

import datetime
from job import ArriveJob

class JobReport:
    def __init__(self, joblist):
        self.joblist = joblist
        self.current_day = datetime.datetime.min

    def display(self):
        for job in self.joblist:
            self._print_job(job)
        self._end_of_day()

    def _set_day(self, day):
        if day != self.current_day:
            self._end_of_day()
            print
            print day
            self.current_day = day
            self.day_stats = {'T': datetime.timedelta(0),
                              'B': datetime.timedelta(0),
                              'C': datetime.timedelta(0)}

    def _end_of_day(self):
        if self.current_day == datetime.datetime.min:
            return

        task_delta = self.day_stats['T']
        break_delta = self.day_stats['B']
        current_delta = self.day_stats['C']
        if current_delta > datetime.timedelta(0):
            print "  Worked %s (+current=%s)   Slacked %s (+current=%s)" % (
                    self.duration_to_string(task_delta),
                    self.duration_to_string(task_delta + current_delta),
                    self.duration_to_string(break_delta),
                    self.duration_to_string(break_delta + current_delta))
        else:
            print "  Worked %-6s   Slacked %s" % (
                    self.duration_to_string(task_delta),
                    self.duration_to_string(break_delta))


    def _print_job(self, job):
        if isinstance(job, ArriveJob) or job.start == datetime.datetime.min:
            self._set_day(job.end.date())
            self._print_job_line(job)
        else:
            self._set_day(job.start.date())
            if job.start.date() == job.end.date():
                self._print_job_line(job)
            else:
                self._print_job_line(job)
                day = job.start.date() + datetime.timedelta(1)
                while day < job.end.date():
                    self._set_day(day)
                    self._print_job_line(job)
                    day = day + datetime.timedelta(1)
                self._set_day(job.end.date())
                self._print_job_line(job)

    def _print_job_line(self, job):
        start_time = False
        end_time = False
        if job.starts_on(self.current_day):
            start_time = job.start
        if job.ends_on(self.current_day):
            end_time = job.end
        duration = job.duration(self.current_day)

        if not isinstance(job, ArriveJob):
            self.day_stats[job.letter()] += duration

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
