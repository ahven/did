#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
did - write what you just did, making a log

Copyright (C) 2010-2011 Michał Czuczman

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
import os
import subprocess
import sys
from job import ArriveJob, JobList


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


class JobListLoader:
    def __init__(self, joblist):
        self.joblist = joblist

    def load(self, path):
        pattern = "(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?: (.+)$"
        rx = re.compile(pattern)
        try:
            f = open(path, "r")
            for line in f:
                m = rx.match(line)
                if m:
                    parts = list(m.groups())
                    job = parts.pop()
                    for i in xrange(len(parts)):
                        parts[i] = int(parts[i])
                    while len(parts) < 6:
                        parts.append(0)
                    year, month, day, hour, minute, second = parts
                    dt = datetime.datetime(
                                        year, month, day, hour, minute, second)
                    self.joblist.push_job(dt, job)
                elif not re.match("#|\s*$", line):
                    raise Exception("Invalid line", line)
        except IOError as err:
            print "Error opening/reading from file '{0}': {1}".format(
                                                    err.filename, err.strerror)

class JobListWriter:
    def __init__(self, filename):
        self.filename = filename

    def append(self, date, name):
        try:
            f = open(self.filename, "a")
            f.write("%d-%02d-%02d %02d:%02d:%02d: %s\n" %
                    (date.year, date.month, date.day,
                     date.hour, date.minute, date.second, name))
        except IOError as err:
            print "Error opening/writing to file '{0}': {1}".format(
                                                    err.filename, err.strerror)



def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] [CURRENT-TASK]")
    parser.add_option("-f", "--log-file",
                      metavar="FILE",
                      dest="logfile",
                      default="didlog",
                      action="store",
                      help="set did database file")
    parser.add_option("-e", "--edit", action="store_true", dest="run_editor",
                      help="Open the task file in an editor")
    (options, args) = parser.parse_args()

    if options.run_editor:
        editors = []
        if os.environ.has_key('VISUAL'):
            editors.append(os.environ['VISUAL'])
        if os.environ.has_key('EDITOR'):
            editors.append(os.environ['EDITOR'])
        editors.extend(["/usr/bin/vim", "/usr/bin/nano", "/usr/bin/pico",
                        "/usr/bin/vi", "/usr/bin/mcedit"])
        for editor in editors:
            if os.path.exists(editor):
                subprocess.call([editor, options.logfile])
                sys.exit()

    joblist = JobList()
    loader = JobListLoader(joblist)
    loader.load(options.logfile)

    if 0 < len(args):
        writer = JobListWriter(options.logfile)
        now = datetime.datetime.now()
        name = " ".join(args)
        writer.append(now, name)
        joblist.push_job(now, name)
    elif joblist.last_end().date() == datetime.date.today():
        joblist.push_job(datetime.datetime.now(), "## current")

    report = JobReport(joblist)
    report.display()

if __name__ == "__main__":
    main()
