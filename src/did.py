#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
did - write what you just did, making a log

Copyright (C) 2010-2012 Michał Czuczman

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
import errno
import os
import subprocess
import sys
from SummaryReport import SummaryReport
from WorkLog import WorkLog
from WorkStatsFactory import WorkStatsFactory
from report import JobReport
from robfile import JobListLoader, JobListWriter
from optparse import OptionParser


class DidApplication:

    def run(self):
        self.parse_options()

        if self.options.run_editor:
            self.open_editor()

        if not os.path.exists(self.options.logfile):
            self.create_file(self.options.logfile)

        self.worklog = WorkLog()
        loader = JobListLoader(self.worklog)
        loader.load(self.options.logfile)

        if 0 < len(self.args):
            self.append_event(" ".join(self.args))
        elif self.worklog.end().date() == datetime.date.today():
            self.worklog.append_assumed_interval(datetime.datetime.now())

        stats_factory = WorkStatsFactory("PL")

        report = JobReport(self.worklog, stats_factory)
        report.set_max_days(self.options.max_days)
        report.display()

        summary = SummaryReport(self.worklog, stats_factory)
        summary.display()


    def parse_options(self):
        parser = OptionParser(usage="%prog [options] [CURRENT-TASK]")
        parser.add_option("-f", "--log-file",
                          metavar="FILE",
                          dest="logfile",
                          default=self.get_config_dir() + "/joblog",
                          action="store",
                          help="set the task database file")
        parser.add_option("-e", "--edit", action="store_true",
                          dest="run_editor",
                          help="open the task database file in an editor")
        parser.add_option("-l", "--last",
                          dest="max_days",
                          type="int",
                          default=1,
                          action="store",
                          help="set the number of last work days "
                               "in detailed view")
        (options, args) = parser.parse_args()
        self.options = options
        self.args = args

    def open_editor(self):
        editors = []
        if os.environ.has_key('VISUAL'):
            editors.append(os.environ['VISUAL'])
        if os.environ.has_key('EDITOR'):
            editors.append(os.environ['EDITOR'])
        editors.extend(["/usr/bin/vim", "/usr/bin/nano", "/usr/bin/pico",
                        "/usr/bin/vi", "/usr/bin/mcedit"])
        for editor in editors:
            if os.path.exists(editor):
                subprocess.call([editor, self.options.logfile])
                sys.exit()

    def get_config_dir(self):
        if 'HOME' in os.environ:
            return os.environ['HOME'] + "/.config/did"
        return "."

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    def create_file(self, filename):
        dirpart, unused_filepart = os.path.split(filename)
        if dirpart != '':
            self.mkdir_p(dirpart)
        file(filename, 'a').close()

    def append_event(self, name):
        writer = JobListWriter(self.options.logfile)
        now = datetime.datetime.now()
        writer.append(now, name)
        self.worklog.append_log_event(now, name)


if __name__ == "__main__":
    did = DidApplication()
    did.run()
