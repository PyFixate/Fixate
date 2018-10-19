import pytest
import subprocess
import os.path
import csv


def dict_line(line):
    return {col.split('=')[0]: col.split('=')[1] for col in line if len(col.split('=')) == 2}


def compare_dicts(test, expected, filter_keys):
    test = {k: v for k, v in test.items() if k not in filter_keys}
    expected = {k: v for k, v in expected.items() if k not in filter_keys}
    assert test == expected


def compare_logs(test_log, expected_log):
    with open(test_log, 'r') as f:
        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
        # Discard first column which is execution time
        test_first, *test_lines, test_last = [line[1:] for line in reader]

    with open(expected_log) as f:
        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
        # Discard first column which is execution time
        expected_first, *expected_lines, expected_last = [line[1:] for line in reader]
    assert test_lines == expected_lines
    # Check first line
    compare_dicts(dict_line(test_first), dict_line(expected_first), filter_keys={"started", "fixate-version"})
    # CHeck last line
    compare_dicts(dict_line(test_last), dict_line(expected_last), filter_keys={"ended"})


log_dir = os.path.join(os.path.dirname(__file__), "expect-logs")
script_dir = os.path.join(os.path.dirname(__file__), "scripts")

def test_basicpass(tmpdir):
    script_path = os.path.join(script_dir, "basicpass.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")
    ret = subprocess.call(["python", "-m", "fixate",
                           "-p", script_path,
                           "--serial-number", "0123456789",
                           "--log-file", log_path,
                           "--non-interactive"])
    assert ret == 5
    compare_logs(os.path.join(log_dir, "basicpass.csv"), log_path)


def test_basicfail(tmpdir):
    script_path = os.path.join(script_dir, "basicfail.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")
    ret = subprocess.call(["python", "-m", "fixate",
                           "-p", script_path,
                           "--serial-number", "0123456789",
                           "--log-file", log_path,
                           "--non-interactive"])
    assert ret == 10
    compare_logs(os.path.join(log_dir, "basicfail.csv"), log_path)


basichierachy_data = [
    ["None", "None", 5],
    ["test_test", "None", 10],
]


@pytest.mark.parametrize("fail_flag,raise_flag,return_code", basichierachy_data)
def test_basichierachy(tmpdir, fail_flag, raise_flag, return_code):
    script_path = os.path.join(script_dir, "basichierachy.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")
    ret = subprocess.call(["python", "-m", "fixate",
                           "-p", script_path,
                           "--serial-number", "0123456789",
                           "--log-file", log_path,
                           "--non-interactive",
                           "--script-params", "fail_flag=" + fail_flag,
                           "--script-params", "raise_flag=" + raise_flag,
                           ])
    assert ret == return_code
    compare_logs(os.path.join(log_dir, "basichierachy-{}-{}.csv".format(fail_flag, raise_flag)),
                 log_path)
