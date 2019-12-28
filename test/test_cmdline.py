import tempfile
from pathlib import Path

from did import did


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
