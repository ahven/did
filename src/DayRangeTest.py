'''
Created on 2012-06-29

@author: ahven
'''
import unittest
import datetime
from DayRange import DayRange, InvalidRangeFormatError

def d(year, month, day):
    return datetime.date(year, month, day)


class DayRangeTest(unittest.TestCase):

    def verify(self, text, expected_first, expected_last):
        day_range = DayRange(text)
        self.assertEqual(day_range.first_day(), expected_first)
        self.assertEqual(day_range.last_day(), expected_last)

    def verifyOne(self, text, expected):
        self.verify(text, expected, expected)

    def verifyInvalid(self, text):
        self.assertRaises(InvalidRangeFormatError, DayRange, text)

    def testIso(self):
        self.verifyOne("2012-05-30", d(2012, 5, 30))
        self.verifyInvalid("2012-13-01")
        self.verifyInvalid("2012-00-01")
        self.verifyInvalid("2012-12-32")
        self.verifyInvalid("2012-02-30")
        self.verifyInvalid("2012-11-31")

    def testYYYYMMDD(self):
        self.verifyOne("20120530", d(2012, 5, 30))
        self.verifyInvalid("20121301")
        self.verifyInvalid("20120001")
        self.verifyInvalid("20121232")
        self.verifyInvalid("2012-0707")
        self.verifyInvalid("201207-07")

    def testIsoWeekDate(self):
        self.verifyOne("2004-W53-6", d(2005, 1, 1))
        self.verifyOne("2004-W53-7", d(2005, 1, 2))
        self.verifyOne("2005-W52-6", d(2005, 12, 31))
        self.verifyOne("2007-W01-1", d(2007, 1, 1))
        self.verifyOne("2007-W52-7", d(2007, 12, 30))
        self.verifyOne("2008-W01-1", d(2007, 12, 31))
        self.verifyOne("2008-W01-2", d(2008, 1, 1))
        self.verifyOne("2009-W01-1", d(2008, 12, 29))

    def testMMDD(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)
        tomorrow = today + datetime.timedelta(1)

        self.verifyOne("1-01", d(today.year, 1, 1))
        self.verifyOne("01-01", d(today.year, 1, 1))
        self.verifyOne("%d-%02d" % (today.month, today.day), today)
        self.verifyOne("%d-%02d" % (yesterday.month, yesterday.day), yesterday)
        self.verifyOne("%d-%02d" % (tomorrow.month, tomorrow.day),
                    d(tomorrow.year - 1, tomorrow.month, tomorrow.day))

        self.verifyInvalid("13-01")
        self.verifyInvalid("02-30")
        self.verifyInvalid("4-31")

    def testDD(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(1)

        self.verifyOne("1", d(today.year, today.month, 1))
        self.verifyOne("01", d(today.year, today.month, 1))
        self.verifyOne("%d" % yesterday.day, yesterday)
        self.verifyOne("%d" % today.day, today)

        self.verifyInvalid("32")

    def testXDaysAgo(self):
        today = datetime.date.today()
        self.verifyOne("-1", today - datetime.timedelta(1))
        self.verifyOne("-300", today - datetime.timedelta(300))
        self.verifyOne("-0", today)
        self.verifyInvalid("-01")

    def testToday(self):
        today = datetime.date.today()
        self.verifyOne("0", today)

    def testRange(self):
        self.verify("2012-03-30..2012-06-20", d(2012, 3, 30), d(2012, 6, 20))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
