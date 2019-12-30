from datetime import datetime

import pytest

from did.WorkInterval import WorkInterval


@pytest.mark.parametrize(
    'interval1,interval2,expectation',
    [(WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name="foo"),
      WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name="foo"),
      True),
     (WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name="foo"),
      WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 0),
                   name="foo"),
      False),
     (WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name=".bar"),
      WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name=".bar"),
      True),
     (WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 55),
                   name=".bar"),
      WorkInterval(start=datetime(2019, 2, 17, 9, 7, 23),
                   end=datetime(2019, 2, 17, 10, 20, 0),
                   name=".bar"),
      False),
     ]
)
def test_work_interval_equals(interval1, interval2, expectation):
    assert expectation == (interval1 == interval2)
