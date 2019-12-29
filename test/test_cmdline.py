import tempfile
from contextlib import ExitStack as does_not_raise
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Union

import pytest

from did import did, DayRange
from did.worklog import FirstJobNotArriveError


def test_create_job_log_file_if_doesnt_exist():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        subdir_path = Path(temp_dir_path, 'subdir')
        job_log_file_path = Path(subdir_path, 'job_log')

        assert temp_dir_path.exists()
        assert not subdir_path.exists()
        assert not job_log_file_path.exists()

        did.main(['--log-file', str(job_log_file_path), 'arrive'])

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
                fake_now = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                DayRange.today = fake_now.date()
                did.main(cmdline_args=['--log-file', str(job_log_file_path),
                                       *args],
                         now=fake_now)

            assert subdir_path.exists()
            assert job_log_file_path.exists()

            if expected_log_contents is not None:
                with open(job_log_file_path) as job_log_file:
                    contents = job_log_file.read()
                    assert contents == expected_log_contents
            else:
                # TODO: The file shouldn't be created in the first place
                pass
