#!/usr/bin/env python3
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

import argparse
import datetime
import errno
import os
import sys

from did.argument_parser import ArgumentParser
from did.editor import open_editor
from did.worklog import WorkLog
from did.worklog_file import JobListWriter
from did.report import ChronologicalSessionDisplay, AggregateSessionDisplay, \
    AggregateRangeDisplay, ReportTimePercent, IntervalFilter
from did.day_range import DayRange


class DidApplication:
    def __init__(self, cmdline_args, now=None):
        if now is None:
            now = datetime.datetime.now()

        self.args = None
        self.cmdline_args = cmdline_args
        self.now = now

    def run(self):
        self.parse_options()

        if self.args.run_editor:
            open_editor(self.args.logfile)
            sys.exit()

        if not os.path.exists(self.args.logfile):
            self.create_file(self.args.logfile)

        self.worklog = WorkLog(file_name=self.args.logfile)

        if 0 < len(self.args.current_task):
            self.append_event(" ".join(self.args.current_task))
        elif self.worklog.end():
            if self.worklog.end().date() == self.now.date():
                self.worklog.append_assumed_interval(self.now)

        self.worklog.compute_stats()

        if self.args.aggregate_range:
            cls = AggregateRangeDisplay
        elif self.args.aggregate_day:
            cls = AggregateSessionDisplay
        else:
            cls = ChronologicalSessionDisplay

        session_display = cls(self.worklog,
                              DayRange(self.args.range),
                              adjusted=self.args.split_breaks,
                              filter=IntervalFilter(self.args.grep_pattern))

        if self.args.percentage and (self.args.aggregate_range or
                                     self.args.aggregate_day):
            session_display.set_unit(ReportTimePercent(self.args.split_breaks))
        session_display.display()

    def parse_options(self):
        parser = ArgumentParser(
            description='Command-line time tracking tool',
            usage='%(prog)s [options] [CURRENT-TASK]')
        parser.add_argument("-f", "--log-file",
                            metavar="FILE",
                            dest="logfile",
                            default=self.get_config_dir() + "/joblog",
                            action="store",
                            help="set the task database file")
        parser.add_argument("-e", "--edit", action="store_true",
                            dest="run_editor",
                            help="open the task database file in an editor")
        parser.add_argument("-r", "--range",
                            dest="range",
                            default="0",
                            action="store",
                            help="print log for days within given range")
        parser.add_argument("-d", "--aggregate-day",
                            action="store_true",
                            dest="aggregate_day",
                            help="display jobs aggregated for each day")
        parser.add_argument("-a", "--aggregate",
                            action="store_true",
                            dest="aggregate_range",
                            help="display jobs aggregated for the complete "
                                 "range")
        parser.add_argument("-g", "--grep",
                            metavar="PATTERN",
                            dest="grep_pattern",
                            default=None,
                            action="store",
                            help="display only jobs matching given pattern")
        parser.add_argument("-p", "--percentage",
                            action="store_true",
                            dest="percentage",
                            help="print times as percentage of total work time")
        parser.add_argument("-s", "--split-breaks",
                            action="store_true",
                            dest="split_breaks",
                            help="account the break time that is treated as "
                                 "work time evenly across all work jobs in a "
                                 "session")
        parser.add_argument('current_task',
                            nargs=argparse.REMAINDER,
                            help='What have you just been doing?')
        self.args = parser.parse_args(self.cmdline_args)

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
        with open(filename, 'a'):
            pass

    def append_event(self, name):
        if name == ".":
            # Last break interval
            last_break = self.worklog.last_break_interval()
            if last_break is None:
                name = ".break"
            else:
                name = last_break.name
        elif name == ",":
            # Last work interval
            last_work = self.worklog.last_work_interval()
            if last_work is None:
                name = "work"
            else:
                name = last_work.name

        writer = JobListWriter(self.args.logfile)
        writer.append(self.now, name)
        self.worklog.append_log_event(self.now, name)


def main(cmdline_args=None, now=None):
    if cmdline_args is None:
        cmdline_args = sys.argv[1:]

    app = DidApplication(cmdline_args, now)
    app.run()


if __name__ == "__main__":
    main()
