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
from WorkSessionStats import WorkSessionStats


class JobReport:
    def __init__(self, worklog):
        self.worklog = worklog
        self.max_days = None

    def set_max_days(self, max_days=None):
        """Set the maximum number of sessions to be displayed

        Only the last max_days number of sessions will be displayed.
        Use None for no limit of the number of sessions.
        """
        self.max_days = max_days

    def display(self):
        index = 0
        sessions = self.worklog.sessions()
        for session in sessions:
            index += 1
            if self.max_days is None or index + self.max_days > len(sessions):
                self._print_session(session)

    def _print_session(self, session):
        self._print_day_header(session.start().date())

        if len(session.intervals()) == 0:
            self._print_log_line(
                    "", self.time_as_string(session.start()),
                    Fore.RED, "arrive", "", "")

        for interval in session.intervals():
            self._print_interval(interval)

        self._print_day_footer(session)

    def _print_day_header(self, day):
        print
        print Fore.GREEN + str(day) + Style.RESET_ALL

    def _print_day_footer(self, session):
        stats = WorkSessionStats(session)
        work_time = stats.time_worked()
        break_time = stats.time_slacked()

        print "  Worked %-6s   Slacked %s" % (
                    self.duration_to_string(work_time),
                    self.duration_to_string(break_time))

    def _print_interval(self, interval):
        if interval.is_break():
            name_color = Fore.BLACK + Style.BRIGHT
            duration_color = ""
        elif interval.is_assumed():
            name_color = Fore.YELLOW
            duration_color = Fore.MAGENTA
        else:
            name_color = Fore.YELLOW + Style.BRIGHT
            duration_color = Fore.MAGENTA + Style.BRIGHT

        name = interval.name()
        if interval.is_assumed():
            name += " (assumed)"

        self._print_log_line(
                self.time_as_string(interval.start()),
                self.time_as_string(interval.end()),
                name_color,
                name,
                duration_color,
                self.duration_to_string(interval.end() - interval.start()))

    def _print_log_line(
            self, start, end, name_color, name, duration_color, duration):
        print "  %5s .. %5s  %s%-30s%s  %s%s%s" % (
                start,
                end,
                name_color,
                name,
                Style.RESET_ALL,
                duration_color,
                duration,
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
