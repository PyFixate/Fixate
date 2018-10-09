import pytest
import subprocess
import os.path


def test_basicpass(tmpdir):
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "basicpass.py")
    log_path = os.path.join(tmpdir, "logfile.csv")
    ret = subprocess.call(["python", "-m", "fixate",
                            "-p", script_path,
                           "--serial-number", "0123456789",
                            "--log-file", log_path])
    assert ret == 5
