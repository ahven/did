"""
Created on 2012-06-29

@author: ahven
"""
import unittest
import datetime
from did.day_range import DayRange, InvalidRangeFormatError

def d(year, month, day):
    return datetime.date(year, month, day)


class DayRangeTest(unittest.TestCase):

    def verify(self, text, expected_first, expected_last):
        day_range = DayRange(text)
        self.assertEqual(day_range.first_day, expected_first)
        self.assertEqual(day_range.last_day, expected_last)

    def verifyOne(self, text, expected):
        self.verify(text, expected, expected)

    def verifyFirstLength(self, text, expected_first, expected_num_days):
        self.verify(text, expected_first,
                expected_first + datetime.timedelta(expected_num_days - 1))

    def verifySameOutput(self, text1, text2):
        day_range1 = DayRange(text1)
        day_range2 = DayRange(text2)
        self.assertEqual(day_range1.first_day, day_range2.first_day)
        self.assertEqual(day_range1.last_day, day_range2.last_day)

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

    def testYYYYMM(self):
        self.verify("2013-01", d(2013, 1, 1), d(2013, 1, 31))
        self.verify("2013-2", d(2013, 2, 1), d(2013, 2, 28))
        self.verify("2012-02", d(2012, 2, 1), d(2012, 2, 29))
        self.verify("2012-12", d(2012, 12, 1), d(2012, 12, 31))
        self.verify("2012-04", d(2012, 4, 1), d(2012, 4, 30))
        self.verifyInvalid("2013-00")
        self.verifyInvalid("2013-13")

    def testYYYY(self):
        self.verify("2017", d(2017, 1, 1), d(2017, 12, 31))
        self.verify("2200", d(2200, 1, 1), d(2200, 12, 31))
        self.verifyInvalid("1999")
        self.verifyInvalid("3000")

    def testXDaysAgo(self):
        today = datetime.date.today()
        self.verifyOne("-1", today - datetime.timedelta(1))
        self.verifyOne("-300", today - datetime.timedelta(300))
        self.verifyOne("-0", today)
        self.verifyInvalid("-01")

    def testToday(self):
        today = datetime.date.today()
        self.verifyOne("0", today)

    def testIsoWeek(self):
        self.verify("2004-W53", d(2004, 12, 27), d(2005, 1, 2))
        self.verify("2005-w52", d(2005, 12, 26), d(2006, 1, 1))
        self.verify("2007W01", d(2007, 1, 1), d(2007, 1, 7))
        self.verify("2007w52", d(2007, 12, 24), d(2007, 12, 30))
        self.verifyInvalid("2007W1")
        self.verifyInvalid("2012W0")
        self.verifyInvalid("2012W54")

    def testWww(self):
        today = datetime.date.today()
        today_iso = today.isocalendar();
        # TODO: There's a bug, when tested with today=2019-12-30
        # self.verifySameOutput("W1", "%d-W01" % today.year)
        # self.verifySameOutput("W01", "%d-W01" % today.year)
        # self.verifySameOutput("w1", "%d-W01" % today.year)
        # self.verifySameOutput("w01", "%d-W01" % today.year)
        self.verifySameOutput("W%d" % today_iso[1],
                "%d-W%02d" % (today_iso[0], today_iso[1]))
        self.verifyInvalid("W54")

    def testCurrentWeek(self):
        today = datetime.date.today()
        self.verifyFirstLength("W0", today - datetime.timedelta(today.weekday()), 7)
        self.verifyFirstLength("w0", today - datetime.timedelta(today.weekday()), 7)
        self.verifyFirstLength("W-0", today - datetime.timedelta(today.weekday()), 7)
        self.verifyFirstLength("w-0", today - datetime.timedelta(today.weekday()), 7)
        self.verifyInvalid("W00")
        self.verifyInvalid("w-00")

    def testXWeeksAgo(self):
        today = datetime.date.today()
        self.verify("W-1",
                today - datetime.timedelta(today.weekday() + 7),
                today - datetime.timedelta(today.weekday() + 1))
        self.verify("W-20",
                today - datetime.timedelta(today.weekday() + 20 * 7),
                today - datetime.timedelta(today.weekday() + 20 * 7 - 6))
        self.verify("W-100",
                today - datetime.timedelta(today.weekday() + 100 * 7),
                today - datetime.timedelta(today.weekday() + 100 * 7 - 6))
        self.verifyInvalid("W-01")

    def testRange(self):
        self.verify("2012-03-30..2012-06-20", d(2012, 3, 30), d(2012, 6, 20))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
