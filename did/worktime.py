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
import copy
import datetime
from typing import Optional, List


class UnsupportedBreakConfig(Exception):
    pass


class PaidBreakConfig:
    def __init__(self,
                 name: Optional[str] = None,
                 duration: Optional[datetime.timedelta] = None,
                 max_occurrences_per_day: Optional[int] = None,
                 splittable: Optional[bool] = None,
                 earned_after_preceding_work_time: Optional[
                     datetime.timedelta] = None,
                 min_day_total_work_time: Optional[datetime.timedelta] = None):
        """
        Definition of a kind of paid breaks.
        :param name: The name, an identifier.
        :param duration: Duration of the break.
        :param max_occurrences_per_day: The maximum number of times the break
           may occur in one a day. None indicates there is no limit.
        :param splittable: False if the break counts only if it's in one chunk.
           True if the break might be split into multiple chunks.
        :param earned_after_preceding_work_time: Minimum length of preceding
           work time required to earn the break. None means no limit.
        :param min_day_total_work_time: Minimum total length of all work time
           in a given day to be able to earn the break in a day.

        None is allowed for "name", "duration" and "splittable" only to simplify
        parsing, but actually they are required to be non-None, so they must be
        later set to proper values.
        """
        self.name = name
        self.duration = duration
        self.max_occurrences_per_day = max_occurrences_per_day
        self.splittable = splittable
        self.earned_after_preceding_work_time = earned_after_preceding_work_time
        self.min_day_total_work_time = min_day_total_work_time


class Accounting:
    def __init__(self,
                 daily_work_time: datetime.timedelta,
                 break_configs: List[PaidBreakConfig]):
        self.daily_work_time = daily_work_time
        self.break_configs = break_configs

    def clone(self):
        return copy.deepcopy(self)

    def _find_break(self, name: str) -> Optional[int]:
        for index, break_config in enumerate(self.break_configs):
            if break_config.name == name:
                return index
        return None

    def delete_break(self, name: str):
        index = self._find_break(name)
        if index is None:
            raise ValueError("Break \"{}\" doesn't exist".format(name))
        del self.break_configs[index]

    def set_break(self, break_config: PaidBreakConfig):
        index = self._find_break(break_config.name)
        if index is None:
            self.break_configs.append(break_config)
        else:
            self.break_configs[index] = break_config


class Preset:
    def __init__(self, name: str, description: str, accounting: Accounting):
        self.name = name
        self.description = description
        self.accounting = accounting


PRESETS = {preset.name: preset for preset in [
    Preset('default',
           "8 hours work per day, no paid breaks",
           Accounting(
               daily_work_time=datetime.timedelta(hours=8),
               break_configs=[])
           ),
    Preset('PL-computer',
           """Official work session stats in Poland.

           Breaks treated as work time:
             * 5 minutes of break ("computer break") after an hour of work.
               Scaling down, but not up. So this effectively gives a break
               lasting one twelfth of the recent work, but not longer than 5
               minutes.
             * One 15 minutes break per day ("breakfast break"), if the day
               has at least 6 work hours.""",
           Accounting(
               daily_work_time=datetime.timedelta(hours=8),
               break_configs=[
                   PaidBreakConfig(
                       name="breakfast",
                       duration=datetime.timedelta(minutes=15),
                       max_occurrences_per_day=1,
                       splittable=True,  # officially it's not, but...
                       min_day_total_work_time=datetime.timedelta(
                           hours=6)),
                   PaidBreakConfig(
                       name="computer",
                       duration=datetime.timedelta(minutes=5),
                       max_occurrences_per_day=None,
                       splittable=True,  # officially it's not, but...
                       earned_after_preceding_work_time=datetime.timedelta(
                           hours=1)),
               ])
           ),
]}


def make_preset_accounting(name: str) -> Accounting:
    return PRESETS[name].accounting.clone()


class WorkSessionStats(object):
    """
    Count total work time and break time for a WorkSession, accounting for paid
    breaks treated as work time.

    The "adjusted duration" of breaks is decreased to exclude the time that
    is treated as work time.  In return, the "adjusted duration" of work jobs
    is extended proportionally for all work tasks in a session.
    """

    def __init__(self, session):
        self._session = session
        self.daily_break = None  # type: Optional[PaidBreakConfig]
        self.computer_break = None  # type: Optional[PaidBreakConfig]
        self._time_worked = datetime.timedelta(0)
        self._time_slacked = datetime.timedelta(0)

        self.break_seconds_counted_as_work = 0
        self.recent_work_seconds = 0

        self._assign_breaks(self._session.accounting().break_configs)
        if self.daily_break is not None and self._session.is_workday():
            self.usable_daily_break_seconds = (
                    self.daily_break.duration.total_seconds() *
                    self.daily_break.max_occurrences_per_day)
        else:
            self.usable_daily_break_seconds = 0

        real_work_seconds = 0

        for interval in self._session.intervals():
            if interval.is_break:
                self._analyze_break(interval)
            else:
                duration = interval.end - interval.start
                self._analyze_work(duration.total_seconds())
                real_work_seconds += duration.total_seconds()

        for interval in self._session.intervals():
            if not interval.is_break:
                interval.account_break_duration(
                    self.break_seconds_counted_as_work
                    * interval.real_duration().total_seconds()
                    / real_work_seconds)

    def _assign_breaks(self, break_configs):
        for break_config in break_configs:
            if not break_config.splittable:
                raise UnsupportedBreakConfig(
                    "Sorry, non-splittable breaks are not supported yet")

            if break_config.max_occurrences_per_day is None:
                if break_config.min_day_total_work_time is not None:
                    raise UnsupportedBreakConfig(
                        "Sorry, min_day_total_work_time is not yet supported "
                        "with computer breaks")
                if break_config.earned_after_preceding_work_time is None:
                    raise UnsupportedBreakConfig(
                        "Sorry, earn_work_time is required for non-\"daily\" "
                        "breaks")
                if self.computer_break is not None:
                    raise UnsupportedBreakConfig(
                        "Sorry, only at most one computer break is supported")
                self.computer_break = break_config
            else:
                if break_config.max_occurrences_per_day != 1:
                    raise UnsupportedBreakConfig(
                        "Sorry, only one occurrence of the daily break is "
                        "supported now")
                if break_config.earned_after_preceding_work_time is not None:
                    raise UnsupportedBreakConfig(
                        "Sorry, earned_after_preceding_work_time is not yet "
                        "supported with daily breaks")
                if self.daily_break is not None:
                    raise UnsupportedBreakConfig(
                        "Sorry, only at most one daily break is supported")
                self.daily_break = break_config

    def _analyze_break(self, interval):
        duration_seconds = interval.real_duration().total_seconds()

        if self.computer_break is not None:
            used_computer_break_seconds = min(self._legal_break_seconds(),
                                              duration_seconds)
            duration_seconds -= used_computer_break_seconds
            interval.account_work_duration(used_computer_break_seconds)
            self.add_work_seconds(used_computer_break_seconds)
            self.break_seconds_counted_as_work += used_computer_break_seconds
            self.recent_work_seconds -= (
                    used_computer_break_seconds / self._computer_break_scale())

        if self.daily_break is not None:
            used_daily_break_seconds = min(self.usable_daily_break_seconds,
                                           duration_seconds)
            self.usable_daily_break_seconds -= used_daily_break_seconds
            duration_seconds -= used_daily_break_seconds
            interval.account_work_duration(used_daily_break_seconds)
            self.add_work_seconds(used_daily_break_seconds)
            self.break_seconds_counted_as_work += used_daily_break_seconds

        self.add_break_seconds(duration_seconds)

    def _legal_break_seconds(self):
        if self.computer_break is not None:
            computer_break_after_seconds = (
                self.computer_break.earned_after_preceding_work_time
                    .total_seconds())
            # Cap to maximum (e.g. to one hour)
            if self.recent_work_seconds > computer_break_after_seconds:
                self.recent_work_seconds = computer_break_after_seconds

            return self.recent_work_seconds * self._computer_break_scale()
        else:
            return 0

    def _computer_break_scale(self):
        return (1.0 * self.computer_break.duration.total_seconds() /
                self.computer_break.earned_after_preceding_work_time
                .total_seconds())

    def _analyze_work(self, duration_seconds):
        self.add_work_seconds(duration_seconds)
        self.recent_work_seconds += duration_seconds

    def add_work_time(self, duration):
        self._time_worked += duration

    def add_break_time(self, duration):
        self._time_slacked += duration

    def add_work_seconds(self, seconds):
        self.add_work_time(datetime.timedelta(0, seconds))

    def add_break_seconds(self, seconds):
        self.add_break_time(datetime.timedelta(0, seconds))

    def time_worked(self):
        return self._time_worked

    def time_slacked(self):
        return self._time_slacked

    def overhours(self):
        return self._time_worked - self.expected_work_time()

    def expected_work_time(self):
        if self._session.is_workday():
            return self._session.accounting().daily_work_time
        else:
            return datetime.timedelta(0)
