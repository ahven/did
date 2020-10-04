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


def ecma48(param):
    return "\x1B[%dm" % (param)


class Foreground(object):
    black = ecma48(30)
    red = ecma48(31)
    green = ecma48(32)
    brown = ecma48(33)
    blue = ecma48(34)
    magenta = ecma48(35)
    cyan = ecma48(36)
    white = ecma48(37)


class Attributes(object):
    reset = ecma48(0)
    bold = ecma48(1)
