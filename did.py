#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
did - write what you just did, making a log

Copyright (C) 2010 Michał Czuczman

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

import sqlite3
import re
import datetime

class SqliteDidBase:
	def __init__(self, path):
		self.connection = sqlite3.connect(path)

class RobBase:
	def __init__(self,  path):
		self.events = []
		self._load(path)
		
	def _load(self, path):
		try:
			f = open(path,  "r")
			for line in f:
				m = re.match("(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?:"
						+ " (.+)$",  line)
				if m:
					parts = list(m.groups())
					job = parts.pop()
					for i in xrange(len(parts)):
						parts[i] = int(parts[i])
					while len(parts) < 6:
						parts.append(0)
					year,  month,  day,  hour,  minute,  second = parts
					dt = datetime.datetime(year,  month,  day,  hour,  minute,  second)
					self.events.append((dt, job))
				elif not re.match("#|\s*$", line):
					raise Exception("Invalid line",  line)
		except IOError as err:
			print "Error opening/reading from file '{0}': {1}".format(err.filename, err.strerror)
			
	def dump(self):
		for e in self.events:
			print e[0], e[1]


def main():
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-c",  "--configfile",
	                  metavar="FILE",
					  dest="configfile",
					  default="did.sqlite",
					  action="store",
					  help="set did database file (sqlite)")
	parser.add_option("-x", "--helpx",
	                  dest="help",
					  default="0",
					  action="store_const",
					  const="1",
					  help="show this help message")
	(options, args) = parser.parse_args()

	db = RobBase(options.configfile)
	db.dump()
	print "Help setting:", options.help

if __name__ == "__main__":
	main()
