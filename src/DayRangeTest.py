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

    def verifyInvalid(self, text):
        self.assertRaises(InvalidRangeFormatError, DayRange, text)

    def testIso(self):
        self.verify("2012-05-30", d(2012, 5, 30), d(2012, 5, 30))
        self.verifyInvalid("2012-13-01")
        self.verifyInvalid("2012-00-01")
        self.verifyInvalid("2012-12-32")
        self.verifyInvalid("2012-02-30")
        self.verifyInvalid("2012-11-31")

    def testYYYYMMDD(self):
        self.verify("20120530", d(2012, 5, 30), d(2012, 5, 30))
        self.verifyInvalid("20121301")
        self.verifyInvalid("20120001")
        self.verifyInvalid("20121232")
        self.verifyInvalid("2012-0707")
        self.verifyInvalid("201207-07")

    def testRange(self):
        self.verify("2012-03-30..2012-06-20", d(2012, 3, 30), d(2012, 6, 20))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
