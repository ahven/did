# -*- coding: utf-8 -*-
"""
Copyright (C) 2011 Michał Czuczman

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


class JobFactoryTest(unittest.TestCase):

    def setUp(self):
        self.factory = job.JobFactory()
        self.start = datetime.datetime(2011, 1, 1, 8)
        self.end = datetime.datetime(2011, 1, 1, 9)
        self.num = 1

    def tearDown(self):
        pass

    def name_to_instance(self, name, cls):
        item = self.factory.create(self.start, self.end, name, self.num)
        self.assertTrue(isinstance(item, cls))


    def test_task(self):
        self.name_to_instance("task", job.TaskJob)

    def test_task_dot(self):
        self.name_to_instance("task.", job.TaskJob)

    def test_break_dot(self):
        self.name_to_instance(".break", job.BreakJob)

    def test_break_asterisks(self):
        self.name_to_instance("fds **", job.BreakJob)

    def test_arrive(self):
        self.name_to_instance("arrive", job.ArriveJob)

    def test_current(self):
        self.name_to_instance("## current", job.CurrentJob)


class JobListFirstTest(unittest.TestCase):

    def setUp(self):
        self.joblist = job.JobList()
        self.start = datetime.datetime(2011, 1, 1, 8)

    def test_first_task(self):
        with self.assertRaises(job.FirstJobNotArriveError):
            self.joblist.push_job(self.start, "task")

    def test_first_break(self):
        with self.assertRaises(job.FirstJobNotArriveError):
            self.joblist.push_job(self.start, ".break")

    def test_first_current(self):
        with self.assertRaises(job.FirstJobNotArriveError):
            self.joblist.push_job(self.start, "## current")


class JobListOrderTest(unittest.TestCase):

    def setUp(self):
        self.joblist = job.JobList()
        self.date1 = datetime.datetime(2011, 1, 1, 8)
        self.date2 = datetime.datetime(2011, 1, 1, 9)

    def test_ordered(self):
        self.assertEqual(len(self.joblist), 0)
        self.assertEqual(self.joblist.last_end(), datetime.datetime.min)

        self.joblist.push_job(self.date1, "arrive")
        self.assertEqual(len(self.joblist), 1)
        self.assertEqual(self.joblist.last_end(), self.date1)

        self.joblist.push_job(self.date2, "task")
        self.assertEqual(len(self.joblist), 2)
        self.assertEqual(self.joblist.last_end(), self.date2)

    def test_same_date(self):
        self.joblist.push_job(self.date1, "arrive")
        self.joblist.push_job(self.date1, "task")
        self.assertEqual(len(self.joblist), 2)
        self.assertEqual(self.joblist.last_end(), self.date1)

    def test_invalid_order(self):
        self.joblist.push_job(self.date2, "arrive")
        with self.assertRaises(job.NonChronologicalOrderError):
            self.joblist.push_job(self.date1, "task")
        self.assertEqual(len(self.joblist), 1)
        self.assertEqual(self.joblist.last_end(), self.date2)


class JobListDaysTest(unittest.TestCase):

    def setUp(self):
        self.joblist = job.JobList()

    def assertDays(self, days):
        self.assertListEqual(self.joblist.days(), days)

    def assertFirst(self, day, index):
        self.assertEqual(self.joblist.first_job_for_day(day), index)


    def test_empty(self):
        self.assertDays([])
        self.assertFirst(datetime.date(2011, 1, 1), None)

    def test_arrive(self):
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.assertDays([datetime.date(2011, 1, 1)])
        self.assertFirst(datetime.date(2010, 12, 31), None)
        self.assertFirst(datetime.date(2011, 1, 1), 0)
        self.assertFirst(datetime.date(2011, 1, 2), None)

    def test_one_day(self):
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 9), "task")
        self.assertDays([datetime.date(2011, 1, 1)])
        self.assertFirst(datetime.date(2010, 12, 31), None)
        self.assertFirst(datetime.date(2011, 1, 1), 0)
        self.assertFirst(datetime.date(2011, 1, 2), None)

    def test_two_days(self):
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 2, 1), "task")
        self.assertDays([datetime.date(2011, 1, 1),
                           datetime.date(2011, 1, 2)])
        self.assertFirst(datetime.date(2010, 12, 31), None)
        self.assertFirst(datetime.date(2011, 1, 1), 0)
        self.assertFirst(datetime.date(2011, 1, 2), 1)

    def test_task_gap(self):
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 3, 1), "task")
        self.assertDays([datetime.date(2011, 1, 1),
                           datetime.date(2011, 1, 2),
                           datetime.date(2011, 1, 3)])
        self.assertFirst(datetime.date(2010, 12, 31), None)
        self.assertFirst(datetime.date(2011, 1, 1), 0)
        self.assertFirst(datetime.date(2011, 1, 2), 1)
        self.assertFirst(datetime.date(2011, 1, 3), 1)
        self.assertFirst(datetime.date(2011, 1, 4), None)

    def test_skipped_days(self):
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 8), "arrive")
        self.joblist.push_job(datetime.datetime(2011, 1, 1, 9), "task1")
        self.joblist.push_job(datetime.datetime(2011, 1, 3, 9), "arrive")
        self.assertDays([datetime.date(2011, 1, 1),
                           datetime.date(2011, 1, 3)])
        self.assertFirst(datetime.date(2010, 12, 31), None)
        self.assertFirst(datetime.date(2011, 1, 1), 0)
        self.assertFirst(datetime.date(2011, 1, 2), None)
        self.assertFirst(datetime.date(2011, 1, 3), 2)
        self.assertFirst(datetime.date(2011, 1, 4), None)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
