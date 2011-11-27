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

import sqlite3
import re
import datetime

class JobType:
    TASK = 0
    BREAK = 1
    ARRIVE = 2
    CURRENT = 3

    def __init__(self, jobname):
        self.value = self.value_from_job_name(jobname)

    @classmethod
    def value_from_job_name(cls, name):
        if re.match("##", name):
            return cls.CURRENT
        elif name == 'arrive':
            return cls.ARRIVE
        elif re.match("\\.", name) or re.search("\\*\\*", name):
            return cls.BREAK
        else:
            return cls.TASK

    def letter(self):
        if self.value == self.TASK:
            return "T"
        elif self.value == self.BREAK:
            return "B"
        elif self.value == self.ARRIVE:
            return "A"
        elif self.value == self.CURRENT:
            return "C"


class Job:
    def __init__(self, start, end, name, num):
        self.start = start
        self.end = end
        self.name = name
        self.num = num
        self.type = JobType(name)


class JobList:
    def __init__(self):
        self.jobs = []

    def push_job(self, date, name):
        self.jobs.append(Job(self.last_end(), date, name, len(self.jobs)))

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


class JobReport:
    def __init__(self, joblist):
        self.joblist = joblist
        self.last_day = datetime.datetime.min

    def display(self):
        for job in self.joblist:
            self._print_job(job)

    def _start_day(self, day):
        if day != self.last_day:
            print
            print day
            self.last_day = day;

    def _print_job(self, job):
        if job.type.value == JobType.ARRIVE or \
                job.start == datetime.datetime.min:
            self._start_day(job.end.date())
            self._print_job_line(job, False, job.end)
        else:
            self._start_day(job.start.date())
            if job.start.date() == job.end.date():
                self._print_job_line(job, job.start, job.end)
            else:
                self._print_job_line(job, job.start, False)
                day = job.start.date() + datetime.timedelta(1)
                while day < job.end.date():
                    self._start_day(day)
                    self._print_job_line(job, False, False)
                    day = day + datetime.timedelta(1)
                self._start_day(job.end.date())
                self._print_job_line(job, False, job.end)

    def _print_job_line(self, job, start_time, end_time):
        print "  " + self.time_as_string(start_time) + " .. " + \
                self.time_as_string(end_time) + "  " + job.type.letter() + \
                "  " + job.name

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
    (options, args) = parser.parse_args()

    joblist = JobList()
    loader = JobListLoader(joblist)
    loader.load(options.logfile)

    if 0 < len(args):
        writer = JobListWriter(options.logfile)
        now = datetime.datetime.now()
        name = " ".join(args)
        writer.append(now, name)
        joblist.push_job(now, name)

    report = JobReport(joblist)
    report.display()

if __name__ == "__main__":
    main()
