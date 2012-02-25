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

import re

class WorkInterval(object):
    '''
    classdocs
    '''


    def __init__(self, start, end, name, is_assumed=False):
        '''
        Constructor
        '''
        self.start_ = start
        self.end_ = end
        self.name_ = name
        self.is_assumed_ = is_assumed

    def is_break(self):
        # Break names start with a "." or contain "**"
        return re.match("\\.", self.name_) or re.search("\\*\\*", self.name_)

    def is_assumed(self):
        return self.is_assumed_

    def start(self):
        return self.start_

    def end(self):
        return self.end_

    def name(self):
        return self.name_
