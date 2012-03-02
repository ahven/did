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

import report

class SummaryReport(object):
    '''
    classdocs
    '''

    def __init__(self, worklog, stats_factory):
        '''
        Constructor
        '''
        self.worklog_ = worklog
        self.stats_factory_ = stats_factory

    def display(self):
        print
        print "Total overhours: %-6s" % (
                report.duration_to_string(
                    self.worklog_.overhours(self.stats_factory_)))
