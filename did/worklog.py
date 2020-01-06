# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Michał Czuczman

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
import shlex
from typing import List

from pytimeparse.timeparse import timeparse

from did.WorkSession import WorkSession
from did.worktime import make_preset_accounting, WorkSessionStats, \
    PaidBreakConfig


def parse_timedelta(time_expression: str) -> datetime.timedelta:
    seconds = timeparse(time_expression)
    if seconds is None:
        raise ValueError("Invalid time interval expression: {}"
                         .format(time_expression))
    else:
        return datetime.timedelta(seconds=seconds)


class FirstJobNotArriveError(Exception):
    """Raised when trying to append a first log event, which is not an "arrive".
    """
    def __str__(self):
        return "First log event is not an \"arrive\""


class NonChronologicalOrderError(Exception):
    """Raised when trying to append a job with an earlier time than the job
    added last.

    Attributes:
        last_datetime - -The time of the last job on the list.
        appended_datetime - -The time of the job attempted to be added.
    """
    def __init__(self, last, appended):
        self.last_datetime = last
        self.appended_datetime = appended


class InvalidParameter(Exception):
    def __init__(self, param_name):
        super().__init__("Invalid parameter name: {}".format(param_name))


class ConfigChangeDuringSessionError(Exception):
    def __init__(self):
        super().__init__("Config parameters can't be changed while the session "
                         "is still running. Move it right before an 'arrive'.")


class MultipleSessionsInOneDayError(Exception):
    def __init__(self, date: datetime.date):
        super().__init__("Multiple sessions start on {}".format(date))


class WorkLog(object):
    """
    A WorkLog keeps all information throughout the whole history.
    It consists of WorkSession's.
    """

    def __init__(self, file_name, filter_regex=None):
        """
        Constructor
        """
        self.sessions_ = []
        self.last_work_session_start_date = None
        self.file_name = file_name
        self.filter_regex = filter_regex
        self.accounting = make_preset_accounting('PL-computer')

        if isinstance(self.filter_regex, str):
            self.filter_regex = re.compile(self.filter_regex)

        self._load_from_file(file_name)

    def _load_from_file(self, file_name):
        current_session_is_closed = False

        for line_number, parsed_line in enumerate(job_reader(file_name),
                                                  start=1):
            try:
                if isinstance(parsed_line, Event):
                    num_sessions = len(self.sessions_)
                    self.append_log_event(parsed_line.timestamp, parsed_line.text)
                    if (current_session_is_closed and
                            num_sessions == len(self.sessions_)):
                        # Something was appended to the current session,
                        # even though it has already been closed.
                        raise ConfigChangeDuringSessionError()
                    current_session_is_closed = False
                elif isinstance(parsed_line, SetParam):
                    self.set_parameter(parsed_line.name, parsed_line.value)
                    current_session_is_closed = True
                elif isinstance(parsed_line, PaidBreakConfig):
                    self.accounting.set_break(parsed_line)
                    current_session_is_closed = True
                elif isinstance(parsed_line, DeletePaidBreak):
                    self.accounting.delete_break(parsed_line.name)
                    current_session_is_closed = True
                else:
                    raise AssertionError('Unhandled parsed line: {}'.format(parsed_line))
            except Exception as e:
                print("Error while parsing file \"{}\", line {}:"
                      .format(file_name, line_number))
                raise e

    def _check_chronology(self, datetime):
        end = self.end()
        if end != None and end > datetime:
            raise NonChronologicalOrderError(end, datetime)

    def set_filter_regex(self, regex):
        self.filter_regex = regex
        for session in self.sessions_:
            session.set_filter_regex(regex)

    def has_filter(self):
        return self.filter_regex is not None

    def append_log_event(self, datetime, text):
        self._check_chronology(datetime)

        if text == "arrive":
            if self.last_work_session_start_date is not None:
                if datetime.date() == self.last_work_session_start_date:
                    raise MultipleSessionsInOneDayError(
                        self.last_work_session_start_date)
            self.last_work_session_start_date = datetime.date()
            self.sessions_.append(WorkSession(datetime, self.accounting.clone(),
                                              True, self.filter_regex))
        elif text == "arrive ooo":
            self.sessions_.append(WorkSession(datetime, self.accounting.clone(),
                                              False, self.filter_regex))
        else:
            if len(self.sessions_) == 0:
                raise FirstJobNotArriveError()
            self.sessions_[-1].append_log_event(datetime, text)

    def set_parameter(self, name, value):
        if name == 'daily_work_time':
            self.accounting.daily_work_time = parse_timedelta(value)
        else:
            raise InvalidParameter(name)

    def append_assumed_interval(self, datetime):
        self._check_chronology(datetime)

        if len(self.sessions_) > 0:
            self.sessions_[-1].append_assumed_interval(datetime)

    def end(self):
        if len(self.sessions_) == 0:
            return None
        else:
            return self.sessions_[-1].end()

    def sessions(self):
        return self.sessions_

    def last_break_interval(self):
        for session in reversed(self.sessions_):
            last_break = session.last_break_interval()
            if last_break is not None:
                return last_break
        return None

    def last_work_interval(self):
        for session in reversed(self.sessions_):
            last_work = session.last_work_interval()
            if last_work is not None:
                return last_work
        return None

    def compute_stats(self):
        total_overtime = datetime.timedelta(0)
        for session in self.sessions_:
            stats = WorkSessionStats(session)
            total_overtime += stats.overhours()
            session.set_stats(stats)
            session.set_total_overtime(total_overtime)

    def map_names(self, func):
        for session in self.sessions_:
            session.map_names(func)


class LineParser:
    def __init__(self, pattern, action):
        self.regex = re.compile(pattern)
        self.action = action

    def match(self, line):
        return self.regex.match(line)


class Event:
    def __init__(self, timestamp: datetime.timedelta, text: str):
        self.timestamp = timestamp
        self.text = text


class SetParam:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class DeletePaidBreak:
    def __init__(self, name):
        self.name = name


class InvalidLine(Exception):
    pass


class PaidBreakParseError(InvalidLine):
    def __init__(self, message):
        super().__init__('Error in \"config paid_break\": {}'.format(message))


class LineParserRegistry:
    def __init__(self):
        self.line_parsers = []  # type: List[LineParser]

    def register(self, pattern):
        def wrap(func):
            self.line_parsers.append(LineParser(pattern, func))
            return func
        return wrap


class Parser:
    line_parsers = LineParserRegistry()

    @line_parsers.register(
        r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?: (.+)$")
    def _event_line(self, match):
        parts = list(match.groups())
        text = parts.pop()
        for i in range(len(parts)):
            if parts[i] is None:
                parts[i] = 0
            else:
                parts[i] = int(parts[i])
        year, month, day, hour, minute, second = parts
        dt = datetime.datetime(year, month, day, hour, minute, second)
        return Event(dt, text)

    @line_parsers.register(r"#|\s*$")
    def _ignore_line(self, match):
        del match
        return None

    @line_parsers.register(r"config\s+([a-z_][a-z0-9_]*)\s*=\s*(.*)$")
    def _set_config_param(self, match):
        name = match.group(1)
        value = match.group(2).strip()
        return SetParam(name, value)

    @line_parsers.register(r"config\s+paid_break\s+(.*)")
    def _paid_break_config(self, match):
        args = shlex.split(match.group(1))
        if len(args) == 0:
            raise PaidBreakParseError("No arguments")

        paid_break = PaidBreakConfig(name=args.pop(0))

        def set_uniquely(attr, new_value):
            if getattr(paid_break, attr) is not None:
                raise PaidBreakParseError(
                    "Repeated setting of {} (to {} and {})"
                    .format(attr, repr(getattr(paid_break, attr)),
                            repr(new_value)))
            setattr(paid_break, attr, new_value)

        if len(args) == 0:
            raise PaidBreakParseError("Too little arguments")

        if args[0] == 'delete':
            if len(args) > 1:
                raise PaidBreakParseError("Extra arguments")
            return DeletePaidBreak(paid_break.name)

        for arg in args:
            if arg == 'daily':
                set_uniquely("max_occurrences_per_day", 1)
            elif arg == 'splittable':
                set_uniquely("splittable", True)
            elif arg == 'one_chunk':
                set_uniquely("splittable", False)
            elif '=' in arg:
                variable, value = arg.split('=', maxsplit=1)
                if variable == 'min_day_work_time':
                    set_uniquely("min_day_total_work_time",
                                 parse_timedelta(value))
                elif variable == 'earn_work_time':
                    set_uniquely("earned_after_preceding_work_time",
                                 parse_timedelta(value))
                else:
                    raise PaidBreakParseError('Not recognized parameter "{}"'
                                              .format(variable))
            else:
                try:
                    set_uniquely("duration", parse_timedelta(arg))
                except ValueError:
                    raise PaidBreakParseError("Not recognized argument \"{}\""
                                              .format(arg))

        if paid_break.duration is None:
            raise PaidBreakParseError("Missing setting of duration")
        if paid_break.splittable is None:
            raise PaidBreakParseError("Missing setting of \"splittable\" or "
                                      "\"one_chunk\"")
        return paid_break

    def process_line(self, line):
        for line_parser in self.line_parsers.line_parsers:
            match = line_parser.match(line)
            if match:
                return line_parser.action(self, match)
        raise InvalidLine("Invalid line: {}".format(line))


def job_reader(path):
    """
    Generator reading lines from a work log file.

    In each iteration the generator returns a (datetime, text) tuple.
    """
    try:
        with open(path, "r") as f:
            parser = Parser()
            for line in f:
                result = parser.process_line(line)
                if result is not None:
                    yield result
    except IOError as err:
        print("Error opening/reading from file '{0}': {1}".format(
                err.filename, err.strerror))


class JobListWriter:
    def __init__(self, filename):
        self.filename = filename

    def append(self, date, name):
        try:
            with open(self.filename, "a") as f:
                f.write("%d-%02d-%02d %02d:%02d:%02d: %s\n" %
                        (date.year, date.month, date.day,
                         date.hour, date.minute, date.second, name))
        except IOError as err:
            print("Error opening/writing to file '{0}': {1}".format(
                                                    err.filename, err.strerror))