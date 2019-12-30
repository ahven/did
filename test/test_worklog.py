# from unittest import TestCase
#
#
# class TestWorkLog(TestCase):
#     pass
import os
import tempfile
from contextlib import ExitStack as does_not_raise
from datetime import datetime

import pytest

from did.WorkSession import WorkSession
from did.worklog import WorkLog, FirstJobNotArriveError, \
    NonChronologicalOrderError


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3))]),
     ("2019-02-20 09:02:03: arrive ooo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3), is_workday=False)]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:00:00: foo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3), events=[
          (datetime(2019, 2, 20, 10, 0, 0), "foo")])]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:00:00: foo\n"
      "2019-02-20 10:20:55: .bar\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3), events=[
          (datetime(2019, 2, 20, 10, 0, 0), "foo"),
          (datetime(2019, 2, 20, 10, 20, 55), ".bar")])]),
     ("2019-02-20 09:02:03: foobar\n",
      FirstJobNotArriveError),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 07:03:00: arrive\n",
      NonChronologicalOrderError),
     ])
def test_reading(file_contents, expectation):
    if isinstance(expectation, type):
        context_manager = pytest.raises(expectation)
        expected_sessions = None
    else:
        context_manager = does_not_raise()
        expected_sessions = expectation

    with context_manager:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = os.path.join(temp_dir, 'job_log')
            with open(log_file_path, 'w') as log_file:
                log_file.write(file_contents)

            work_log = WorkLog(log_file_path)

            assert expected_sessions == work_log.sessions()
