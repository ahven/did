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


class WorkStatsFactory(object):
    """
    classdocs
    """

    def __init__(self, country):
        """
        Constructor
        """
        self.country_ = country

    def new_session_stats(self, session):
        if self.country_ == "PL":
            return PolishWorkSessionStats(session)
        else:
            return WorkSessionStats(session)


class WorkSessionStats(object):
    """
    Count total work time and break time for a WorkSession
    """

    def __init__(self, session):
        self.session_ = session
        self.time_worked_ = datetime.timedelta(0)
        self.time_slacked_ = datetime.timedelta(0)
        self._analyze()

    def _analyze(self):
        for interval in self.session_.intervals():
            duration = interval.end() - interval.start()
            if interval.is_break():
                self.add_break_time(duration)
            else:
                self.add_work_time(duration)

    def add_work_time(self, duration):
        self.time_worked_ += duration

    def add_break_time(self, duration):
        self.time_slacked_ += duration

    def add_work_seconds(self, seconds):
        self.add_work_time(datetime.timedelta(0, seconds))

    def add_break_seconds(self, seconds):
        self.add_break_time(datetime.timedelta(0, seconds))

    def time_worked(self):
        return self.time_worked_

    def time_slacked(self):
        return self.time_slacked_

    def overhours(self):
        return self.time_worked_ - self.expected_work_time()

    def expected_work_time(self):
        if self.session_.is_workday():
            seconds = 8 * 60 * 60
        else:
            seconds = 0
        return datetime.timedelta(0, seconds)


class PolishWorkSessionStats(WorkSessionStats):
    """
    Count official work session stats in Poland.

    Breaks treated as worktime:
     * 5 minutes of break ("computer break") after an hour of work. Scaling
       down, but not up.  So this effectively gives a break lasting one twelfth
       of the recent work, but not longer than 5 minutes.
     * One 15 minutes break per day, if the day has at least 6 work hours.

    The "adjusted duration" of breaks is decreased to exclude the time that
    is treated as work time.  In return, the "adjusted duration" of work jobs
    is extended proportionally for all work tasks in a session.
    """

    short_break_after_seconds = 60 * 60   # Make a break after one hour
    short_break_duration_seconds = 5 * 60 # The break lasts 5 minutes
    long_break_seconds = 15 * 60          # 15-minutes break
#    daily_work_seconds = 8 * 60 * 60      # 8 hours of work per day


    def __init__(self, session):
        """
        :param session:
        """
        self.break_seconds_counted_as_work = 0
        super().__init__(session)

    def _computer_break_scale(self):
        return 1.0 * self.short_break_duration_seconds \
                / self.short_break_after_seconds

    def _legal_break_seconds(self):
        # One hour maximum
        if self.recent_work_seconds > self.short_break_after_seconds:
            self.recent_work_seconds = self.short_break_after_seconds

        return self.recent_work_seconds * self._computer_break_scale()

    def _analyze_break(self, interval):
        duration_seconds = interval.real_duration().total_seconds()

        used_short_break_seconds = min(
                self._legal_break_seconds(), duration_seconds)
        used_long_break_seconds = min(
                self.usable_long_break_seconds,
                duration_seconds - used_short_break_seconds)

        interval.account_work_duration(
                used_short_break_seconds + used_long_break_seconds)
        self.add_work_seconds(
                used_short_break_seconds + used_long_break_seconds)
        self.add_break_seconds(
                duration_seconds
                - used_short_break_seconds - used_long_break_seconds)

        self.break_seconds_counted_as_work += (
                used_short_break_seconds + used_long_break_seconds)
        self.recent_work_seconds -= \
                used_short_break_seconds / self._computer_break_scale()
        self.usable_long_break_seconds -= used_long_break_seconds

    def _analyze_work(self, duration_seconds):
        self.add_work_seconds(duration_seconds)
        self.recent_work_seconds += duration_seconds

    def _analyze(self):
        self.recent_work_seconds = 0
        if self.session_.is_workday():
            self.usable_long_break_seconds = self.long_break_seconds
        else:
            self.usable_long_break_seconds = 0

        real_work_seconds = 0

        for interval in self.session_.intervals():
            if interval.is_break():
                self._analyze_break(interval)
            else:
                duration = interval.end() - interval.start()
                self._analyze_work(duration.total_seconds())
                real_work_seconds += duration.total_seconds()

        for interval in self.session_.intervals():
            if not interval.is_break():
                interval.account_break_duration(
                        self.break_seconds_counted_as_work
                        * interval.real_duration().total_seconds()
                        / real_work_seconds)
