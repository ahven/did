import os
import tempfile
from contextlib import ExitStack as does_not_raise
from datetime import datetime, timedelta
from typing import List, Optional

import pytest

from did.session import WorkSession
from did.worklog import WorkLog, FirstJobNotArriveError, \
    NonChronologicalOrderError, ConfigChangeDuringSessionError, InvalidLine, \
    PaidBreakParseError, InvalidParameter, MultipleSessionsInOneDayError, \
    TooLongSessionError
from did.worktime import make_preset_accounting, Accounting, PaidBreakConfig

default_accounting = make_preset_accounting('PL-computer')


def custom_accounting(hours: Optional[int] = None,
                      set_breaks: List[PaidBreakConfig] = [],
                      delete_breaks: List[str] = []) -> Accounting:
    accounting = default_accounting.clone()
    if hours is not None:
        accounting.daily_work_time = hours
    for break_name in delete_breaks:
        accounting.delete_break(break_name)
    for break_config in set_breaks:
        accounting.set_break(break_config)
    return accounting


def verify_reading(file_contents, expectation):
    if isinstance(expectation, type):
        context_manager = pytest.raises(expectation)
        should_verify_sessions = False
    else:
        context_manager = does_not_raise()
        should_verify_sessions = True

    with context_manager:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file_path = os.path.join(temp_dir, 'job_log')
            with open(log_file_path, 'w') as log_file:
                log_file.write(file_contents)

            work_log = WorkLog(log_file_path)

            if should_verify_sessions:
                assert expectation == work_log.sessions()


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting)]),
     ("2019-02-20 09:02:03: arrive ooo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, is_workday=False)]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:00:00: foo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, events=[
          (datetime(2019, 2, 20, 10, 0, 0), "foo")])]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:00:00: foo\n"
      "2019-02-20 10:20:55: .bar\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, events=[
          (datetime(2019, 2, 20, 10, 0, 0), "foo"),
          (datetime(2019, 2, 20, 10, 20, 55), ".bar")])]),
     ("2019-02-20 09:02:03: foobar\n",
      FirstJobNotArriveError),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 07:03:00: arrive\n",
      NonChronologicalOrderError),
     ("foo\n",
      InvalidLine),
     ])
def test_basic_work_log_parsing(file_contents, expectation):
    verify_reading(file_contents, expectation)


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("config daily_work_time = 6h\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=custom_accounting(6))]),
     ("2019-02-20 09:02:03: arrive\n"
      "config daily_work_time = 6h\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting)]),
     ("2019-02-20 09:02:03: arrive\n"
      "config daily_work_time = 6h\n"
      "2019-02-20 10:00:00: foo\n",
      ConfigChangeDuringSessionError),
     ("config foo = 3h",
      InvalidParameter)
     ])
def test_config_daily_work_time_parsing(file_contents, expectation):
    verify_reading(file_contents, expectation)


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("config paid_break\n",
      PaidBreakParseError),
     ("config paid_break \"foo\"",
      PaidBreakParseError),
     ("config paid_break \"foo\" 15m",
      PaidBreakParseError),
     ("config paid_break \"foo\" 10m splittable\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=custom_accounting(
                       set_breaks=[PaidBreakConfig(
                           name='foo',
                           duration=timedelta(minutes=10),
                           splittable=True)]))]),
     ("config paid_break \"foo\" 10m one_chunk\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=custom_accounting(
                       set_breaks=[PaidBreakConfig(
                           name='foo',
                           duration=timedelta(minutes=10),
                           splittable=False)]))]),
     ("config paid_break \"foo\" 10m splittable min_day_work_time=2h"
      "   earn_work_time=30m\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=custom_accounting(
                       set_breaks=[PaidBreakConfig(
                           name='foo',
                           duration=timedelta(minutes=10),
                           splittable=False,
                           min_day_total_work_time=timedelta(hours=2),
                           earned_after_preceding_work_time=timedelta(
                               minutes=30))]))]),
     ("config paid_break \"computer\" delete\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=custom_accounting(
                       delete_breaks=["computer"]))]),
     ("config paid_break \"foo\" delete\n",
      ValueError),
     ("config paid_break \"foo\" 10m splittable\n"
      "config paid_break \"foo\" delete\n"
      "2019-02-20 09:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting)]),
     ])
def test_config_paid_break_parsing(file_contents, expectation):
    verify_reading(file_contents, expectation)


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:02:03: arrive\n",
      MultipleSessionsInOneDayError),
     ("2019-02-20 09:02:03: arrive ooo\n"
      "2019-02-20 10:02:03: arrive\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, is_workday=False),
       WorkSession(start=datetime(2019, 2, 20, 10, 2, 3),
                   accounting=default_accounting, is_workday=True)]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:02:03: arrive ooo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, is_workday=True),
       WorkSession(start=datetime(2019, 2, 20, 10, 2, 3),
                   accounting=default_accounting, is_workday=False)]),
     ])
def test_only_one_arrive_per_day(file_contents, expectation):
    verify_reading(file_contents, expectation)


@pytest.mark.parametrize(
    "file_contents,expectation",
    [("2019-02-20 09:02:03: arrive\n"
      "2019-02-21 09:02:03: foo\n",
      [WorkSession(start=datetime(2019, 2, 20, 9, 2, 3),
                   accounting=default_accounting, events=[
          (datetime(2019, 2, 21, 9, 2, 3), "foo")])]),
     ("2019-02-20 09:02:03: arrive\n"
      "2019-02-21 09:02:04: foo\n",
      TooLongSessionError),
     ])
def test_max_session_length(file_contents, expectation):
    verify_reading(file_contents, expectation)
