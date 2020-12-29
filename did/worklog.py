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

from did.session import WorkSession
from did.worklog_file import parse_timedelta, Event, SetParam, \
    DeletePaidBreak, job_reader
from did.worktime import make_preset_accounting, WorkSessionStats, \
    PaidBreakConfig


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
        super().__init__("Non-chronological order")
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


class TooLongSessionError(Exception):
    def __init__(self, date: datetime.date, max_duration: datetime.timedelta):
        super().__init__("The session on {} is longer than the maximum session "
                         "length (equal to {})".format(date, max_duration))


class WorkLog:
    """
    A WorkLog keeps all information throughout the whole history.
    It consists of WorkSession's.
    """

    def __init__(self, file_name):
        """
        Constructor
        """
        self.sessions_ = []
        self.last_work_session_start_date = None
        self.file_name = file_name
        self.accounting = make_preset_accounting('PL-computer')
        self.max_session_length = datetime.timedelta(days=1)

        self._load_from_file(file_name)

    def _load_from_file(self, file_name):
        current_session_is_closed = False

        for line_number, parsed_line in enumerate(job_reader(file_name),
                                                  start=1):
            try:
                if isinstance(parsed_line, Event):
                    num_sessions = len(self.sessions_)
                    self.append_log_event(parsed_line.timestamp,
                                          parsed_line.text)
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
                    raise AssertionError('Unhandled parsed line: {}'
                                         .format(parsed_line))
            except Exception as error:
                print("Error while parsing file \"{}\", line {}:"
                      .format(file_name, line_number))
                raise error

    def _check_chronology(self, date_time: datetime.datetime):
        end = self.end()
        if end is not None and end > date_time:
            raise NonChronologicalOrderError(end, date_time)

    def append_log_event(self, date_time: datetime.datetime, text):
        self._check_chronology(date_time)

        if text == "arrive":
            if self.last_work_session_start_date is not None:
                if date_time.date() == self.last_work_session_start_date:
                    raise MultipleSessionsInOneDayError(
                        self.last_work_session_start_date)
            self.last_work_session_start_date = date_time.date()
            self.sessions_.append(
                WorkSession(date_time, self.accounting.clone(), True))
        elif text == "arrive ooo":
            self.sessions_.append(
                WorkSession(date_time, self.accounting.clone(), False))
        else:
            if not self.sessions_:
                raise FirstJobNotArriveError()
            session = self.sessions_[-1]
            if session.start + self.max_session_length < date_time:
                raise TooLongSessionError(session.start.date(),
                                          self.max_session_length)
            session.append_log_event(date_time, text)

    def set_parameter(self, name, value):
        if name == 'daily_work_time':
            self.accounting.daily_work_time = parse_timedelta(value)
        else:
            raise InvalidParameter(name)

    def append_assumed_interval(self, date_time: datetime.datetime):
        self._check_chronology(date_time)

        if self.sessions_:
            self.sessions_[-1].append_assumed_interval(date_time)

    def end(self):
        if self.sessions_:
            return self.sessions_[-1].end
        return None

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
