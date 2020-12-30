# -*- coding: utf-8 -*-
"""
Copyright (C) 2011-2020 Michał Czuczman

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
from typing import Optional, List, Dict, Union

from did.console_codes import Foreground, Attributes
from did.day_range import DayRange
from did.interval import interval_name_denotes_a_break, Interval
from did.session import WorkSession
from did.worklog import WorkLog


class ReportTimeUnit:
    def __init__(self, adjusted):
        self.adjusted_string = '*' if adjusted else ''

    def set_total_work_time(self, total_work_time):
        self.total_work_time = total_work_time


class ReportTimePercent(ReportTimeUnit):
    def to_string(self, diff):
        denominator = self.total_work_time.total_seconds()
        if denominator > 0:
            return "%.2f%%%s" % (100.0 * diff.total_seconds() / denominator,
                                 self.adjusted_string)
        else:
            return "NAN"


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
        time += self.adjusted_string
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


class IntervalDurationCounter:
    """Counts total duration from multiple intervals"""
    def __init__(self):
        self.work_time = datetime.timedelta(0)
        self.break_time = datetime.timedelta(0)

    def add_interval(self, interval: Interval, adjusted: bool):
        duration = interval.duration(adjusted)
        if interval.is_break:
            self.break_time += duration
        else:
            self.work_time += duration

    def add(self, other: 'IntervalDurationCounter'):
        self.work_time += other.work_time
        self.break_time += other.break_time


class IntervalFilter:
    def __init__(self, pattern: Optional[str] = None):
        self._regex = None
        if pattern is not None:
            self._regex = re.compile(pattern)

    def accepts_interval(self, interval: Interval) -> bool:
        if self._regex is None:
            return True
        return self._regex.search(interval.name) is not None

    def accepts_session(self, session: WorkSession) -> bool:
        if self._regex is None:
            return True
        return any(self.accepts_interval(interval)
                   for interval in session.intervals())

    def is_active(self) -> bool:
        return self._regex is not None

    def session_filtered_duration_counter(self,
                                          session: WorkSession,
                                          adjusted: bool
                                          ) -> IntervalDurationCounter:
        """Count duration of intervals in a session that match this filter"""
        counter = IntervalDurationCounter()
        for interval in session.intervals():
            if self.accepts_interval(interval):
                counter.add_interval(interval, adjusted)
        return counter


class Display:
    def __init__(self, worklog, day_range, adjusted, filter: IntervalFilter):
        self.worklog = worklog
        self.day_range = day_range
        self.adjusted = adjusted
        self.filter = filter

        self.overall_stats_unit = ReportTimeHoursMinutes(True)
        self.matched_stats_unit = ReportTimeHoursMinutes(self.adjusted)
        self.job_unit = ReportTimeHoursMinutes(self.adjusted)
        self.total_work_time = datetime.timedelta(0)
        self.total_break_time = datetime.timedelta(0)
        self.total_overtime = datetime.timedelta(0)
        self.matched_duration_counter = IntervalDurationCounter()
        for session in worklog.sessions():
            if session.start.date() in self.day_range:
                self.append_session(session)
                self.total_work_time += session.stats().time_worked()
                self.total_break_time += session.stats().time_slacked()
                self.total_overtime += session.stats().overhours()
                self.matched_duration_counter.add(
                    self.filter.session_filtered_duration_counter(session,
                                                                  adjusted))
        self.job_unit.set_total_work_time(self.total_work_time)

    def set_unit(self, unit):
        self.job_unit = unit
        self.job_unit.set_total_work_time(self.total_work_time)

    def display(self):
        self.print_header()
        self.print_content()
        self.print_footer()

    def print_header(self):
        pass

    def print_content(self):
        """This method must be overridden in a subclass"""
        raise NotImplementedError()

    def print_footer(self):
        print()
        if self.filter.is_active():
            print("Matched:  Work %-6s   Break %-6s" % (
                    self.matched_stats_unit.to_string(
                        self.matched_duration_counter.work_time),
                    self.matched_stats_unit.to_string(
                        self.matched_duration_counter.break_time)))
        print("Overall:  Worktime %-6s   Slacktime %-6s   Overtime %-6s" % (
                self.overall_stats_unit.to_string(self.total_work_time),
                self.overall_stats_unit.to_string(self.total_break_time),
                self.overall_stats_unit.to_string(self.total_overtime)))

    def append_session(self, session):
        """This method must be overridden in a subclass"""
        raise NotImplementedError()


class SessionDisplay(Display):
    def __init__(self, worklog, day_range, adjusted, filter: IntervalFilter):
        self.sessions: List[WorkSession] = []
        Display.__init__(self, worklog, day_range, adjusted, filter)

    def append_session(self, session):
        self.sessions.append(session)

    def print_content(self):
        for session in self.sessions:
            self.print_session(session)

    def print_session(self, session):
        if self.filter.accepts_session(session):
            self.job_unit.set_total_work_time(session.stats().time_worked())
            self.print_session_header(session)
            self.print_session_content(session)
            if self.filter.is_active():
                self.print_matched_jobs_footer(session)
            self.print_session_footer(session)

    def print_session_header(self, session):
        print()
        print(Foreground.green + str(session.start.date()), end=' ')
        if not session.is_workday():
            print("  (Out of office)", end=' ')
        print(Attributes.reset)

    def print_session_content(self, session):
        """This method must be overridden in a subclass"""
        raise NotImplementedError()

    def print_matched_jobs_footer(self, session):
        counter = self.filter.session_filtered_duration_counter(session,
                                                                self.adjusted)
        print("  Matched: Work %-6s   Break %-6s" % (
                self.matched_stats_unit.to_string(counter.work_time),
                self.matched_stats_unit.to_string(counter.break_time)))

    def print_session_footer(self, session):
        work_time = session.stats().time_worked()
        break_time = session.stats().time_slacked()
        overtime = session.stats().overhours()

        print("  Worktime %-6s   Slacktime %-6s   Overtime %-6s "
              "(running total %s)" % (
                    self.overall_stats_unit.to_string(work_time),
                    self.overall_stats_unit.to_string(break_time),
                    self.overall_stats_unit.to_string(overtime),
                    self.overall_stats_unit.to_string(
                        session.total_overtime())))


class ChronologicalSessionDisplay(SessionDisplay):
    def __init__(self,
                 worklog: WorkLog,
                 day_range: DayRange,
                 adjusted: bool,
                 filter: IntervalFilter):
        SessionDisplay.__init__(self, worklog, day_range, adjusted, filter)

    def print_session_content(self, session):
        if len(session.intervals()) == 0:
            self.print_log_line(
                    "", time_as_string(session.start),
                    Foreground.red, "arrive", "", "")

        for interval in session.intervals():
            if self.filter.accepts_interval(interval):
                self._print_interval(interval)

    def _print_interval(self, interval):
        name = interval.name
        if interval.is_assumed:
            name += " (assumed)"

        self.print_log_line(
                time_as_string(interval.start),
                time_as_string(interval.end),
                get_name_color(interval.is_break, interval.is_assumed),
                name,
                get_duration_color(interval.is_break, interval.is_assumed),
                self.job_unit.to_string(interval.duration(self.adjusted)))

    def print_log_line(
            self, start, end, name_color, name, duration_color, duration):
        print("  %5s .. %5s  %s%-30s%s  %s%s%s" % (
                start,
                end,
                name_color,
                name,
                Attributes.reset,
                duration_color,
                duration,
                Attributes.reset))


AggregateTreeChildType = Union['AggregateTreeNode', datetime.timedelta]


class AggregateTreeNode:
    def __init__(self, adjusted: bool, filter: IntervalFilter):
        self.children: Dict[str, AggregateTreeChildType] = {}
        self.adjusted = adjusted
        self._filter = filter

    def add_interval(self, name_words, duration, is_assumed):
        if duration == datetime.timedelta(0):
            return
        if len(name_words) == 0:
            if is_assumed:
                name = '(assumed)'
            else:
                name = ''
            if name not in self.children:
                self.children[name] = datetime.timedelta(0)
            self.children[name] += duration
        else:
            if name_words[0] not in self.children:
                self.children[name_words[0]] = AggregateTreeNode(self.adjusted,
                                                                 self._filter)
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
        for name in list(self.children.keys()):
            if isinstance(self.children[name], AggregateTreeNode):
                duration += self.children[name].get_duration()
            else:
                duration += self.children[name]
        return duration

    def simplify(self):
        # Merge "a b" with "a c"
        for name in list(self.children.keys()):
            child = self.children[name]
            if isinstance(child, AggregateTreeNode):
                child.simplify()
                if len(child.children) == 1:
                    del self.children[name]
                    name2 = list(child.children.keys())[0]
                    if name2 != '':
                        name += ' ' + name2
                    self.children[name] = child.children[name2]

    def display(self, unit, indent_level=0):
        sorted_names = sorted(
                self.children,
                key=self.get_child_duration,
                reverse=True)
        for name in sorted_names:
            self._print_aggregated_interval(name, indent_level, unit)

    def _print_aggregated_interval(self, name, indent_level, unit):
        duration = self.get_child_duration(name)
        duration_str = unit.to_string(duration)
        is_break = interval_name_denotes_a_break(name)
        is_assumed = (name == "(assumed)")
        indent = "     " * indent_level
        print("   %s%s%-6s%s  %s%s%s" % (
                indent,
                get_duration_color(is_break, is_assumed),
                duration_str,
                Attributes.reset,
                get_name_color(is_break, is_assumed),
                name,
                Attributes.reset))
        if isinstance(self.children[name], AggregateTreeNode):
            self.children[name].display(unit, indent_level + 1)

    def add_session(self, session):
        for interval in session.intervals():
            if self._filter.accepts_interval(interval):
                self.add_interval(
                        interval.name.split(),
                        interval.duration(self.adjusted),
                        interval.is_assumed)


class AggregateSessionDisplay(SessionDisplay):
    def __init__(self, worklog, day_range, adjusted, filter: IntervalFilter):
        SessionDisplay.__init__(self, worklog, day_range, adjusted, filter)

    def print_session_content(self, session):
        self.tree = AggregateTreeNode(self.adjusted, self.filter)
        self.tree.add_session(session)
        self.tree.simplify()
        self.tree.display(self.job_unit)


class AggregateRangeDisplay(Display):
    def __init__(self,
                 worklog: WorkLog,
                 day_range: DayRange,
                 adjusted: bool,
                 filter: IntervalFilter):
        self.tree = AggregateTreeNode(adjusted, filter)
        Display.__init__(self, worklog, day_range, adjusted, filter)

    def append_session(self, session):
        self.tree.add_session(session)

    def print_content(self):
        self.tree.simplify()
        self.tree.display(self.job_unit)
