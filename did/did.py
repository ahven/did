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
import re
import subprocess
import sys

from did.worklog import WorkLog, JobListWriter
from did.WorkStatsFactory import WorkStatsFactory
from did.report import ChronologicalSessionDisplay, AggregateSessionDisplay, \
        AggregateRangeDisplay, ReportTimePercent
from did.DayRange import DayRange


def forward_slash_unescape(escaped):
    unescaped = ''
    i = 0
    while i < len(escaped):
        if escaped[i] == '\\' and i + 1 < len(escaped):
            if escaped[i + 1] != '/':
                # copy the backslash
                unescaped += escaped[i]
            # copy the following character
            i += 1
            unescaped += escaped[i]
        else:
            unescaped += escaped[i]
        i += 1
    return unescaped


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
            self.open_editor()

        if not os.path.exists(self.args.logfile):
            self.create_file(self.args.logfile)

        self.worklog = WorkLog(file_name=self.args.logfile,
                               filter_regex=self.args.grep_pattern)

        if 0 < len(self.args.current_task):
            self.append_event(" ".join(self.args.current_task))
        elif self.worklog.end():
            if self.worklog.end().date() == self.now.date():
                self.worklog.append_assumed_interval(self.now)

        if self.args.categorized_report:
            self.apply_categorization()

        self.worklog.compute_stats(WorkStatsFactory("PL"))

        if self.args.aggregate_range:
            cls = AggregateRangeDisplay
        elif self.args.aggregate_day:
            cls = AggregateSessionDisplay
        else:
            cls = ChronologicalSessionDisplay

        session_display = cls(self.worklog, DayRange(self.args.range),
                              self.args.split_breaks)

        if self.args.percentage and (self.args.aggregate_range or self.args.aggregate_day):
            session_display.set_unit(ReportTimePercent(self.args.split_breaks))
        session_display.display()

    def apply_categorization(self):
        filename = self.get_config_dir() + "/categorization"
        rx = re.compile("^s/((?:[^\\\\/]|\\\\.)+)/((?:[^\\\\/]|\\\\.)*)/\\s*$")
        try:
            f = open(filename, "r")
            for line in f:
                if re.match("^\\s*(#|$)", line):
                    continue
                m = rx.match(line)
                if not m:
                    print("Invalid line in categorization file \"%s\": %s" \
                            % (filename, line))
                    sys.exit(1)
                pattern = forward_slash_unescape(m.group(1))
                subst = forward_slash_unescape(m.group(2))
                cat_rx = re.compile(pattern)
                self.worklog.map_names(lambda x: cat_rx.sub(subst, x))

        except IOError as err:
            print("Error opening/reading from file '{0}': {1}".format(
                    err.filename, err.strerror))

    def parse_options(self):
        parser = argparse.ArgumentParser(
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
        parser.add_argument("-c", "--categorized",
                            action="store_true",
                            dest="categorized_report",
                            help="apply categorizing regexes to job names")
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

    def open_editor(self):
        editors = []
        if 'VISUAL' in os.environ:
            editors.append(os.environ['VISUAL'])
        if 'EDITOR' in os.environ:
            editors.append(os.environ['EDITOR'])
        editors.extend(["/usr/bin/vim", "/usr/bin/nano", "/usr/bin/pico",
                        "/usr/bin/vi", "/usr/bin/mcedit"])
        for editor in editors:
            if os.path.exists(editor):
                subprocess.call([editor, self.args.logfile])
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
        with open(filename, 'a'):
            pass

    def append_event(self, name):
        if name == ".":
            # Last break interval
            last_break = self.worklog.last_break_interval()
            if last_break is None:
                name = ".break"
            else:
                name = last_break.name()
        elif name == ",":
            # Last work interval
            last_work = self.worklog.last_work_interval()
            if last_work is None:
                name = "work"
            else:
                name = last_work.name()

        writer = JobListWriter(self.args.logfile)
        writer.append(self.now, name)
        self.worklog.append_log_event(self.now, name)


def main(cmdline_args=sys.argv, now=None):
    app = DidApplication(cmdline_args, now)
    app.run()


if __name__ == "__main__":
    main()
