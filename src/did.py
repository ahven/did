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
from job import JobList
from report import JobReport
from robfile import JobListLoader, JobListWriter

def get_config_dir():
    if 'HOME' in os.environ:
        return os.environ['HOME'] + "/.config/did"
    return "."


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] [CURRENT-TASK]")
    parser.add_option("-f", "--log-file",
                      metavar="FILE",
                      dest="logfile",
                      default = get_config_dir() + "/joblog",
                      action="store",
                      help="set the task database file")
    parser.add_option("-e", "--edit", action="store_true", dest="run_editor",
                      help="open the task database file in an editor")
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

    # Create a file if it doesn't exist
    if not os.path.exists(options.logfile):
        dirpart, unused_filepart = os.path.split(options.logfile)
        if dirpart != '':
            mkdir_p(dirpart)
        file(options.logfile, 'a').close()


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
