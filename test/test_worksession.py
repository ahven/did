from datetime import datetime
from unittest import TestCase

from did.WorkSession import WorkSession


class TestWorkSession(TestCase):
    def test___eq__(self):
        self.assertTrue(
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5)) ==
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5))
        )
        self.assertFalse(
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5)) ==
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 6))
        )
