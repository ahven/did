# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2019 Michał Czuczman

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

import unittest
import datetime
from did.worktime import WorkSessionStats, make_preset_accounting, Accounting
from did.WorkInterval import WorkInterval


class SessionMock:
    def __init__(self, accounting: Accounting, is_workday: bool):
        self.accounting_ = accounting
        self.intervals_ = []
        self.is_workday_ = is_workday

    def intervals(self):
        return self.intervals_

    def append_interval(self, seconds, is_break):
        start = self._end()
        end = start + datetime.timedelta(0, seconds)
        self.intervals_.append(
            WorkInterval(start, end,
                         name='interval{}'.format(len(self.intervals_)),
                         is_break=is_break))

    def accounting(self):
        return self.accounting_

    def is_workday(self):
        return self.is_workday_

    def _end(self):
        if len(self.intervals_) == 0:
            return datetime.datetime(2012, 1, 4, 8, 0, 0)
        else:
            return self.intervals_[-1].end()


class TestBasicSession(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def append_intervals(self, intervals):
        """
        Each interval may be specified as a single value.
        Use positive values for work intervals.
        Use negative values for break intervals.
        Use "0" for a work interval of length 0.
        Use None for a break interval of length 0.
        """
        for interval in intervals:
            if interval is None:
                self.session.append_interval(0, True)
            elif interval < 0:
                self.session.append_interval(-interval, True)
            else:
                self.session.append_interval(interval, False)

    def verify_generic(self, intervals, expected_work_seconds, expected_break_seconds,
               is_workday):
        accounting = make_preset_accounting('PL-computer')
        self.session = SessionMock(accounting, is_workday)
        self.append_intervals(intervals)
        stats = WorkSessionStats(self.session)
        expected_worktime = datetime.timedelta(0, expected_work_seconds)
        expected_breaktime = datetime.timedelta(0, expected_break_seconds)

        self.assertEqual(stats.time_worked(), expected_worktime)
        self.assertEqual(stats.time_slacked(), expected_breaktime)

    def verify(self, intervals, expected_work_seconds, expected_break_seconds):
        self.verify_generic(intervals, expected_work_seconds, expected_break_seconds, True)

    def verify_ooo(self, intervals, expected_work_seconds, expected_break_seconds):
        self.verify_generic(intervals, expected_work_seconds, expected_break_seconds, False)


    def test_only_work_adds_up(self):
        self.verify([5, 10, 20], 35, 0)

    def test_one_5_minutes_break_after_an_hour_of_work(self):
        self.verify([-15 * 60, 60 * 60, -5 * 60], 80 * 60, 0)
        self.verify([-15 * 60, 60 * 60, -4 * 60], 79 * 60, 0)
        self.verify([-15 * 60, 60 * 60, -6 * 60], 80 * 60, 1 * 60)
        self.verify([-15 * 60, 60 * 60, -5 * 60, 30 * 60], 110 * 60, 0)
        self.verify([-15 * 60, 60 * 60, -4 * 60, 30 * 60], 109 * 60, 0)
        self.verify([-15 * 60, 60 * 60, -6 * 60, 30 * 60], 110 * 60, 1 * 60)

    def test_two_5_minutes_break(self):
        self.verify([60 * 60, -5 * 60, 60 * 60, -5 * 60], 130 * 60, 0)

    def test_5_minutes_break_is_proportional(self):
        self.verify([-15 * 60, 12, -10], 15 * 60 + 13, 9)
        self.verify([-15 * 60, 30 * 60, -5 * 60], 47 * 60 + 30, 2 * 60 + 30)

    def test_running_hour_for_5_minutes_break(self):
        self.verify([60 * 60, -2 * 60, 30 * 60, -30 * 60], 112 * 60, 10 * 60)

    def test_break_may_be_split(self):
        self.verify([-15 * 60, 60 * 60, -60, -60, -60, -60, -60, -60],
                    80 * 60, 60)

    def test_15_minutes_break_anytime(self):
        self.verify([-15 * 60, 360 * 60], 375 * 60, 0)
        self.verify([200 * 60, -15 * 60, 160 * 60], 375 * 60, 0)

    def test_15_minutes_break_may_be_broken_up(self):
        self.verify([-5 * 60, 120 * 60, -10 * 60, 240 * 60, -20 * 60],
                    385 * 60, 10 * 60)

    def test_15_minutes_break_applies_even_on_no_work(self):
        # Assuming you work for at least 6 hours per day
        self.verify([-20 * 60], 15 * 60, 5 * 60)

    def test_ooo(self):
        self.verify_ooo([-60 * 60], 0, 60 * 60)
        self.verify_ooo([-60 * 60, 60 * 60], 60 * 60, 60 * 60)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
