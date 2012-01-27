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
import unittest
import job
import stats


class TestJobDayStats(unittest.TestCase):

    def assertWorktime(self, h, m, s):
        self.assertEqual(self.stats.get_work_time(),
                    datetime.timedelta(0, s, 0, 0, m, h))

    def assertBreaktime(self, h, m, s):
        self.assertEqual(self.stats.get_break_time(),
                    datetime.timedelta(0, s, 0, 0, m, h))

    def assertCurrenttime(self, h, m, s):
        self.assertEqual(self.stats.get_current_time(),
                    datetime.timedelta(0, s, 0, 0, m, h))


class TestOneTask(TestJobDayStats):

    def setUp(self):
        self.joblist = job.JobList()
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 9, 30), "task")

    def testSameDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 1))
        self.assertWorktime(1, 30, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testEarlierDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2010, 8, 1))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testLaterDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 2))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)


class TestOneOverlongTask(TestJobDayStats):

    def setUp(self):
        self.joblist = job.JobList()
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 2, 3), "task")

    def testFirstDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 1))
        self.assertWorktime(16, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testNextDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 2))
        self.assertWorktime(3, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testEarlierDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2010, 8, 1))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testLaterDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 3))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)


class TestMultipleTask(TestJobDayStats):

    def setUp(self):
        self.joblist = job.JobList()
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 9), "task")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 9, 15), ".brk")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 12), "task2")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 12, 1, 1), ".brk")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 13, 1, 1), "task3")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 14), "## current")

    def testSameDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 1))
        self.assertWorktime(4, 45, 0)
        self.assertBreaktime(0, 16, 1)
        self.assertCurrenttime(0, 58, 59)

    def testEarlierDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2010, 8, 1))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)

    def testLaterDay(self):
        self.stats = stats.JobDayStats(self.joblist, datetime.date(2011, 1, 2))
        self.assertWorktime(0, 0, 0)
        self.assertBreaktime(0, 0, 0)
        self.assertCurrenttime(0, 0, 0)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
