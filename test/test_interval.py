from datetime import datetime

import pytest

from did.interval import Interval


@pytest.mark.parametrize(
    'interval1,interval2,expectation',
    [(Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name="foo"),
      Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name="foo"),
      True),
     (Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name="foo"),
      Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 0),
               name="foo"),
      False),
     (Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name=".bar"),
      Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name=".bar"),
      True),
     (Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 55),
               name=".bar"),
      Interval(start=datetime(2019, 2, 17, 9, 7, 23),
               end=datetime(2019, 2, 17, 10, 20, 0),
               name=".bar"),
      False),
     ]
)
def test_interval_equals(interval1, interval2, expectation):
    assert expectation == (interval1 == interval2)
