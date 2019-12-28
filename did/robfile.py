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
import re
from WorkLog import NonChronologicalOrderError


def job_reader(path):
    """
    Generator reading lines from a work log file.

    In each iteration the generator returns a (datetime, text) tuple.
    """
    pattern = "(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?: (.+)$"
    rx = re.compile(pattern)
    try:
        f = open(path, "r")
        for line in f:
            m = rx.match(line)
            if m:
                parts = list(m.groups())
                text = parts.pop()
                for i in range(len(parts)):
                    if parts[i] is None:
                        parts[i] = 0
                    else:
                        parts[i] = int(parts[i])
                year, month, day, hour, minute, second = parts
                dt = datetime.datetime(
                        year, month, day, hour, minute, second)
                yield dt, text
            elif not re.match("#|\s*$", line):
                raise Exception("Invalid line", line)
    except NonChronologicalOrderError as err:
        print("Error: Non-chronological entries: appending", \
                err.appended_datetime, "after", err.last_datetime)
    except IOError as err:
        print("Error opening/reading from file '{0}': {1}".format(
                err.filename, err.strerror))


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
            print("Error opening/writing to file '{0}': {1}".format(
                                                    err.filename, err.strerror))
