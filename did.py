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

class Job:
    def __init__(self, start, end, name, num):
        self.start = start
        self.end = end
        self.name = name
        self.num = num
        self.brk = self.get_break_from_name(name)

    @staticmethod
    def get_break_from_name(name):
        if re.match("^##", name):
            return 3
        elif re == 'arrive':
            return 2
        elif re.match("^.", name) or re.match("\*\*", name):
            return 1
        else:
            return 0


class JobList:
    def __init__(self):
        self.jobs = []

    def push_job(self, date, name):
        self.jobs.append(Job(self.last_end(), date, name, len(self.jobs)))

    def last_end(self):
        if len(self.jobs) > 0:
            return self.jobs[-1].end
        else:
            return datetime.datetime(datetime.MINYEAR, 1, 1)

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

    def display(self):
        for job in self.joblist:
            date = job.end
            print "%d-%02d-%02d %02d:%02d:%02d: %s" % (
                    date.year, date.month, date.day,
                    date.hour, date.minute, date.second, job.name)


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
