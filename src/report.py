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

class ReportTimeUnit:
    def set_total_work_time(self, total_work_time):
        self.total_work_time = total_work_time

class ReportTimePercent(ReportTimeUnit):

    def to_string(self, diff):
        return "%.2f%%" % (100.0 * diff.total_seconds()
                / self.total_work_time.total_seconds())

class ReportTimeHoursMinutes(ReportTimeUnit):
    def to_string(self, diff):
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

    def __init__(self):
        self.stats_unit = ReportTimeHoursMinutes()
        self.job_unit = ReportTimeHoursMinutes()

    def set_unit(self, unit):
        self.job_unit = unit

    def total_work_time(self):
        work_time = datetime.timedelta(0)
        for session in self.sessions:
            work_time += session.stats().time_worked()
        return work_time

    def display(self, worklog, day_range):
        self.sessions = []
        self.print_header()
        for session in worklog.sessions():
            if day_range.contains(session.start().date()):
                self.sessions.append(session)
                self.print_session(session)
        self.print_footer()

    def print_header(self):
        pass

    def print_footer(self):
        if len(self.sessions) > 1:
            work_time = datetime.timedelta(0)
            break_time = datetime.timedelta(0)
            overtime = datetime.timedelta(0)
            for session in self.sessions:
                work_time += session.stats().time_worked()
                break_time += session.stats().time_slacked()
                overtime += session.stats().overhours();
            print
            print "Overall:  Worked %-6s   Slacked %-6s   Overtime %-6s" % (
                    self.stats_unit.to_string(work_time),
                    self.stats_unit.to_string(break_time),
                    self.stats_unit.to_string(overtime))

    def print_session(self, session):
        self.print_session_header(session)
        self.print_session_intervals(session)
        self.print_session_footer(session)

    def print_session_header(self, session):
        print
        print Foreground.green + str(session.start().date()),
        if not session.is_workday():
            print "  (Out of office)",
        print Attributes.reset

    def print_session_footer(self, session):
        work_time = session.stats().time_worked()
        break_time = session.stats().time_slacked()
        overtime = session.stats().overhours();

        print "  Worked %-6s   Slacked %-6s   Overtime %-6s (running total %s)" % (
                    self.stats_unit.to_string(work_time),
                    self.stats_unit.to_string(break_time),
                    self.stats_unit.to_string(overtime),
                    self.stats_unit.to_string(session.total_overtime()))

class SessionChronologicalDisplay(SessionDisplay):
    def print_session_intervals(self, session):
        if len(session.intervals()) == 0:
            self.print_log_line(
                    "", time_as_string(session.start()),
                    Foreground.red, "arrive", "", "")

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
                self.job_unit.to_string(interval.end() - interval.start()))

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


class AggregateTreeNode:
    def __init__(self):
        self.children = {}

    def add_interval(self, name_words, duration, is_assumed):
        if duration == datetime.timedelta(0):
            return
        if len(name_words) == 0:
            if is_assumed:
                name = '(assumed)'
            else:
                name = ''
            if not name in self.children:
                self.children[name] = datetime.timedelta(0)
            self.children[name] += duration
        else:
            if name_words[0] not in self.children:
                self.children[name_words[0]] = AggregateTreeNode()
            self.children[name_words[0]].add_interval(
                    name_words[1:], duration, is_assumed)

    def get_child_duration(self, name):
        if name in self.children:
            if isinstance(self.children[name], AggregateTreeNode):
                return self.children[name].get_duration()
            else:
                return self.children[name]
        else:
            return datetime.timedelta(0)

    def get_duration(self):
        duration = datetime.timedelta(0)
        for name in self.children.keys():
            if isinstance(self.children[name], AggregateTreeNode):
                duration += self.children[name].get_duration()
            else:
                duration += self.children[name]
        return duration

    def simplify(self):
        # Merge "a b c" with "a b d"
        while len(self.children) == 1:
            prefix = self.children.keys()[0]
            if not isinstance(self.children[prefix], AggregateTreeNode):
                break
            subtree = self.children[prefix]
            self.children = {}
            for name in subtree.children.keys():
                self.children[prefix + ' ' + name] = subtree.children[name]

        # Merge "a b" with "a c"
        for name in self.children.keys():
            child = self.children[name]
            if isinstance(child, AggregateTreeNode):
                child.simplify()
                if len(child.children) == 1:
                    del self.children[name]
                    name2 = child.children.keys()[0]
                    child = child.children[name2]
                    self.children[name + ' ' + name2] = child

    def display(self, unit, indent_level=0):
        sorted_names = sorted(
                self.children,
                key=lambda x: self.get_child_duration(x),
                reverse=True)
        for name in sorted_names:
            self._print_aggregated_interval(name, indent_level, unit)

    def _print_aggregated_interval(self, name, indent_level, unit):
        duration = self.get_child_duration(name)
        duration_str = unit.to_string(duration)
        is_break = WorkInterval.name_is_break(name)
        is_assumed = (name == "(assumed)")
        indent = ""
        for i in range(indent_level): indent += "     "
        print "   %s%s%-6s%s  %s%s%s" % (
                indent,
                get_duration_color(is_break, is_assumed),
                duration_str,
                Attributes.reset,
                get_name_color(is_break, is_assumed),
                name,
                Attributes.reset)
        if isinstance(self.children[name], AggregateTreeNode):
            self.children[name].display(unit, indent_level + 1)


class SessionAggregateDisplay(SessionDisplay):
    def __init__(self):
        SessionDisplay.__init__(self)

    def aggregation_begin(self):
        self.tree = AggregateTreeNode()

    def aggregation_add_session(self, session):
        for interval in session.intervals():
            self.tree.add_interval(
                    interval.name().split(),
                    interval.end() - interval.start(),
                    interval.is_assumed())

    def aggregation_end(self):
        self.tree.simplify()
        self.job_unit.set_total_work_time(self.total_work_time())
        self.tree.display(self.job_unit)


class SessionAggregateDayDisplay(SessionAggregateDisplay):
    def __init__(self):
        SessionAggregateDisplay.__init__(self)

    def print_session_intervals(self, session):
        self.aggregation_begin()
        self.aggregation_add_session(session)
        self.aggregation_end()


class SessionAggregateRangeDisplay(SessionAggregateDayDisplay):
    def __init__(self):
        SessionAggregateDayDisplay.__init__(self)

    def print_header(self):
        self.aggregation_begin()

    def print_footer(self):
        self.aggregation_end()
        SessionDisplay.print_footer(self)
        if 1 == len(self.sessions):
            SessionDisplay.print_session_footer(self, self.sessions[0])

    def print_session_intervals(self, session):
        self.aggregation_add_session(session)

    def print_session_header(self, session):
        pass

    def print_session_footer(self, session):
        pass
