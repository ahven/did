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
from colorama import Fore, Style
from job import ArriveJob, BreakJob, CurrentJob, TaskJob
from stats import JobDayStats


def color_for_job(job):
    if isinstance(job, TaskJob):
        return Fore.YELLOW + Style.BRIGHT
    elif isinstance(job, BreakJob):
        return Fore.BLACK + Style.BRIGHT
    elif isinstance(job, CurrentJob):
        return Fore.CYAN + Style.BRIGHT
    elif isinstance(job, ArriveJob):
        return Fore.RED
    else:
        return ""

def color_for_duration(job):
    if isinstance(job, TaskJob):
        return Fore.MAGENTA + Style.BRIGHT
    else:
        return ""


class JobReport:
    def __init__(self, joblist):
        self.joblist = joblist
        self.current_day = datetime.datetime.min
        self.max_days = None

    def set_max_days(self, max_days=None):
        """Set the maximum number of days to be displayed

        Only the last max_days number of days will be displayed.
        Use None for no limit of the number of days.
        """
        self.max_days = max_days

    def display(self):
        index = 0
        days = self.joblist.days()
        for day in days:
            index += 1
            if self.max_days is None or index + self.max_days > len(days):
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
        print Fore.GREEN + str(day) + Style.RESET_ALL

    def _print_day_footer(self, day):
        stats = JobDayStats(self.joblist, day)
        work_time = stats.get_work_time()
        break_time = stats.get_break_time()
        current_time = stats.get_current_time()

        if current_time > datetime.timedelta(0):
            print "  Worked %s (+current=%s)   Slacked %s (+current=%s)" % (
                self.duration_to_string(work_time),
                self.duration_to_string(work_time + current_time),
                self.duration_to_string(break_time),
                self.duration_to_string(break_time + current_time))
        else:
            print "  Worked %-6s   Slacked %s" % (
                    self.duration_to_string(work_time),
                    self.duration_to_string(break_time))

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

        print "  %s .. %s  %s  %s%-30s%s  %s%s%s" % (
                self.time_as_string(start_time),
                self.time_as_string(end_time),
                job.letter(),
                color_for_job(job),
                job.name,
                Style.RESET_ALL,
                color_for_duration(job),
                self.duration_to_string(duration),
                Style.RESET_ALL)

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
