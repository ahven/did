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

from console_codes import Foreground, Attributes
import datetime


def duration_to_string(diff):
    if diff is None or diff is False:
        return ''
    total_seconds = diff.total_seconds()
    time = ''
    if diff.total_seconds() < 0:
        time = '-'
        total_seconds = -total_seconds

    hours = total_seconds / 3600
    minutes = (total_seconds / 60) % 60

    if 0 < hours:
        time += "%dh" % hours
    time += "%dm" % minutes
    return time

def time_as_string(time):
    if time:
        return "%02d:%02d" % (time.hour, time.minute)
    else:
        return "     "


class JobReport:
    def __init__(self, worklog, stats_factory):
        self.worklog = worklog
        self.stats_factory_ = stats_factory
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
        self.total_overtime = datetime.timedelta(0)
        for session in sessions:
            index += 1
            stats = self.stats_factory_.new_session_stats(session)
            self.total_overtime += stats.overhours()
            if self.max_days is None or index + self.max_days > len(sessions):
                self._print_session(session, stats)

    def _print_session(self, session, stats):
        self._print_day_header(session.start().date())

        if len(session.intervals()) == 0:
            self._print_log_line(
                    "", time_as_string(session.start()),
                    Foreground.red, "arrive", "", "")

        for interval in session.intervals():
            self._print_interval(interval)

        self._print_day_footer(session, stats)

    def _print_day_header(self, day):
        print
        print Foreground.green + str(day) + Attributes.reset

    def _print_day_footer(self, session, stats):
        work_time = stats.time_worked()
        break_time = stats.time_slacked()
        overtime = stats.overhours();

        print "  Worked %-6s   Slacked %-6s   Overtime %-6s (total %s)" % (
                    duration_to_string(work_time),
                    duration_to_string(break_time),
                    duration_to_string(overtime),
                    duration_to_string(self.total_overtime))

    def _print_interval(self, interval):
        if interval.is_break():
            name_color = Foreground.black + Attributes.bold
            duration_color = ""
        elif interval.is_assumed():
            name_color = Foreground.brown
            duration_color = Foreground.magenta
        else:
            name_color = Foreground.brown + Attributes.bold
            duration_color = Foreground.magenta + Attributes.bold

        name = interval.name()
        if interval.is_assumed():
            name += " (assumed)"

        self._print_log_line(
                time_as_string(interval.start()),
                time_as_string(interval.end()),
                name_color,
                name,
                duration_color,
                duration_to_string(interval.end() - interval.start()))

    def _print_log_line(
            self, start, end, name_color, name, duration_color, duration):
        print "  %5s .. %5s  %s%-30s%s  %s%s%s" % (
                start,
                end,
                name_color,
                name,
                Attributes.reset,
                duration_color,
                duration,
                Attributes.reset)
