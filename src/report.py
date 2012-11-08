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
from WorkInterval import WorkInterval


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

def get_name_color(is_break, is_assumed):
    if is_break:
        return Foreground.black + Attributes.bold
    elif is_assumed:
        return Foreground.brown
    else:
        return Foreground.brown + Attributes.bold

def get_duration_color(is_break, is_assumed):
    if is_break:
        return ""
    elif is_assumed:
        return Foreground.magenta
    else:
        return Foreground.magenta + Attributes.bold

class SessionDisplay:
    def display_session(self, session, stats, total_overtime):
        self.print_day_header(session)

        if len(session.intervals()) == 0:
            self.print_log_line(
                    "", time_as_string(session.start()),
                    Foreground.red, "arrive", "", "")

        self.display(session)

        self.print_day_footer(session, stats, total_overtime)

    def print_day_header(self, session):
        print
        print Foreground.green + str(session.start().date()),
        if not session.is_workday():
            print "  (Out of office)",
        print Attributes.reset

    def print_day_footer(self, session, stats, total_overtime):
        work_time = stats.time_worked()
        break_time = stats.time_slacked()
        overtime = stats.overhours();

        print "  Worked %-6s   Slacked %-6s   Overtime %-6s (running total %s)" % (
                    duration_to_string(work_time),
                    duration_to_string(break_time),
                    duration_to_string(overtime),
                    duration_to_string(total_overtime))

class SessionChronologicalDisplay(SessionDisplay):
    def display(self, session):
        for interval in session.intervals():
            self._print_interval(interval)

    def _print_interval(self, interval):
        name = interval.name()
        if interval.is_assumed():
            name += " (assumed)"

        self.print_log_line(
                time_as_string(interval.start()),
                time_as_string(interval.end()),
                get_name_color(interval.is_break(), interval.is_assumed()),
                name,
                get_duration_color(interval.is_break(), interval.is_assumed()),
                duration_to_string(interval.end() - interval.start()))

    def print_log_line(
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


class SessionAggregatedDisplay(SessionDisplay):
    def display(self, session):
        total_time = {}
        is_assumed = {}
        for interval in session.intervals():
            if interval.name() not in total_time:
                total_time[interval.name()] = datetime.timedelta(0)
            total_time[interval.name()] += interval.end() - interval.start()
            is_assumed[interval.name()] = interval.is_assumed()

        sorted_names = sorted(total_time, key=lambda x: total_time[x], reverse=True)
        for name in sorted_names:
            self._print_aggregated_interval(name, total_time[name], is_assumed[name])

    def _print_aggregated_interval(self, name, total_time, is_assumed):
        is_break = WorkInterval.name_is_break(name)
        if is_assumed:
            name += " (assumed)"
        print "   %s%-6s%s  %s%s%s" % (
                get_duration_color(is_break, is_assumed),
                duration_to_string(total_time),
                Attributes.reset,
                get_name_color(is_break, is_assumed),
                name,
                Attributes.reset)


class JobReport:
    def __init__(self, worklog, stats_factory,
                session_display=SessionChronologicalDisplay()):
        self.worklog = worklog
        self.stats_factory_ = stats_factory
        self.session_display = session_display

    def display(self, day_range):
        index = 0
        sessions = self.worklog.sessions()
        self.total_overtime = datetime.timedelta(0)
        for session in sessions:
            index += 1
            stats = self.stats_factory_.new_session_stats(session)
            self.total_overtime += stats.overhours()
            if day_range.contains(session.start().date()):
                self.session_display.display_session(
                        session, stats, self.total_overtime)
