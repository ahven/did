import tempfile
from contextlib import ExitStack as does_not_raise
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Union

import pytest

from did import did, day_range
from did.worklog import FirstJobNotArriveError


def run_did(job_log_file_path: Path,
            args: List[str],
            fake_time_str: str = None):
    if fake_time_str is not None:
        fake_now = datetime.strptime(fake_time_str, '%Y-%m-%d %H:%M:%S')
        true_today = day_range.today
        day_range.today = fake_now.date()
    else:
        fake_now = None

    try:
        did.main(cmdline_args=['--log-file', str(job_log_file_path), *args],
                 now=fake_now)
    finally:
        if fake_time_str is not None:
            day_range.today = true_today


def test_create_job_log_file_if_doesnt_exist():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        subdir_path = Path(temp_dir_path, 'subdir')
        job_log_file_path = Path(subdir_path, 'job_log')

        assert temp_dir_path.exists()
        assert not subdir_path.exists()
        assert not job_log_file_path.exists()

        run_did(job_log_file_path, ['arrive'])

        assert subdir_path.exists()
        assert job_log_file_path.exists()

        with open(job_log_file_path) as job_log_file:
            lines = job_log_file.readlines()
            assert len(lines) == 1
            assert lines[0].endswith(': arrive\n')


@pytest.mark.parametrize(
    "times_with_args,expectation",
    [([('2019-02-20 09:02:03', ("arrive",))],
      "2019-02-20 09:02:03: arrive\n"),
     ([('2019-02-20 09:02:03', ("arrive", "ooo"))],
      "2019-02-20 09:02:03: arrive ooo\n"),
     ([('2019-02-20 09:02:03', ("foobar",))],
      FirstJobNotArriveError),
     ([('2019-02-20 09:02:03', ("arrive",)),
       ('2019-02-20 10:00:00', ("foo",)),
       ('2019-02-20 10:20:55', (".bar",))],
      "2019-02-20 09:02:03: arrive\n"
      "2019-02-20 10:00:00: foo\n"
      "2019-02-20 10:20:55: .bar\n"),
     ])
def test_resulting_log(times_with_args: List[Tuple[str, str]],
                       expectation: Union[str, Exception]):
    if isinstance(expectation, type):
        context_manager = pytest.raises(expectation)
        expected_log_contents = None
    else:
        assert isinstance(expectation, str)
        context_manager = does_not_raise()
        expected_log_contents = expectation

    with context_manager:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            subdir_path = Path(temp_dir_path, 'subdir')
            job_log_file_path = Path(subdir_path, 'job_log')

            assert temp_dir_path.exists()
            assert not subdir_path.exists()
            assert not job_log_file_path.exists()

            for time_str, args in times_with_args:
                run_did(job_log_file_path, args, time_str)

            assert subdir_path.exists()
            assert job_log_file_path.exists()

            if expected_log_contents is not None:
                with open(job_log_file_path) as job_log_file:
                    contents = job_log_file.read()
                    assert contents == expected_log_contents
            else:
                # TODO: The file shouldn't be created in the first place
                pass


def test_range_report_negative_days():
    with tempfile.TemporaryDirectory() as temp_dir:
        job_log_file_path = Path(temp_dir, 'job_log')
        run_did(job_log_file_path, ["arrive"], "2019-02-15 09:02:00")
        # This used to cause exit(2) with the following message:
        # "error: argument -r/--range: expected one argument"
        run_did(job_log_file_path, ["-r", "-30.."], "2019-02-16 08:50:00")
