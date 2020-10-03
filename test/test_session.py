from datetime import datetime
from unittest import TestCase

from did.session import WorkSession
from did.worktime import make_preset_accounting


class TestWorkSession(TestCase):
    def setUp(self) -> None:
        self.default_accounting = make_preset_accounting('PL-computer')

    def test___eq__(self):
        self.assertTrue(
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5),
                        accounting=self.default_accounting) ==
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5),
                        accounting=self.default_accounting)
        )
        self.assertFalse(
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 5),
                        accounting=self.default_accounting) ==
            WorkSession(start=datetime(2019, 2, 20, 9, 2, 6),
                        accounting=self.default_accounting)
        )
