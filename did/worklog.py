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

from did.dispatchers import TypeBasedDispatcher
from did.session import AppendingToClosedSessionError, WorkSession
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
        reader = WorkLogReader(self)
        reader.load(file_name)

    def _check_chronology(self, date_time: datetime.datetime):
        end = self.end()
        if end is not None and end > date_time:
            raise NonChronologicalOrderError(end, date_time)

    def append_log_event(self, date_time: datetime.datetime, text):
        self._check_chronology(date_time)

        if text == "arrive":
            self._close_last_session()
            if self.last_work_session_start_date is not None:
                if date_time.date() == self.last_work_session_start_date:
                    raise MultipleSessionsInOneDayError(
                        self.last_work_session_start_date)
            self.last_work_session_start_date = date_time.date()
            self.sessions_.append(
                WorkSession(date_time, self.accounting.clone(), True))
        elif text == "arrive ooo":
            self._close_last_session()
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
        self._close_last_session()
        if name == 'daily_work_time':
            self.accounting.daily_work_time = parse_timedelta(value)
        else:
            raise InvalidParameter(name)

    def set_break(self, break_config: PaidBreakConfig):
        self._close_last_session()
        self.accounting.set_break(break_config)

    def delete_break(self, name: str):
        self._close_last_session()
        self.accounting.delete_break(name)

    def _close_last_session(self):
        if self.sessions_:
            self.sessions_[-1].close()

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


class WorkLogReader:
    _action_handler = TypeBasedDispatcher()

    def __init__(self, worklog: WorkLog):
        self._worklog = worklog

    def load(self, file_name: str):
        for line_number, parsed_line in enumerate(job_reader(file_name),
                                                  start=1):
            try:
                self._action_handler.handle(self, parsed_line)
            except Exception as error:
                print("Error while parsing file \"{}\", line {}:"
                      .format(file_name, line_number))
                raise error

    @_action_handler.register(Event)
    def handle_event(self, event: Event):
        try:
            self._worklog.append_log_event(event.timestamp, event.text)
        except AppendingToClosedSessionError as error:
            raise ConfigChangeDuringSessionError() from error

    @_action_handler.register(SetParam)
    def handle_set_param(self, set_param: SetParam):
        self._worklog.set_parameter(set_param.name, set_param.value)

    @_action_handler.register(PaidBreakConfig)
    def handle_paid_break_config(self, paid_break_config: PaidBreakConfig):
        self._worklog.set_break(paid_break_config)

    @_action_handler.register(DeletePaidBreak)
    def handle_delete_paid_break(self, item: DeletePaidBreak):
        self._worklog.delete_break(item.name)
