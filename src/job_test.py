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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
