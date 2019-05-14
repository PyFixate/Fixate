import pytest
import subprocess
import os.path
import csv


def dict_line(line):
    return {
        col.split("=")[0]: col.split("=")[1] for col in line if len(col.split("=")) == 2
    }


def compare_dicts(test, expected, filter_keys):
    test = {k: v for k, v in test.items() if k not in filter_keys}
    expected = {k: v for k, v in expected.items() if k not in filter_keys}
    assert test == expected


def compare_logs(test_log, expected_log):
    with open(test_log, "r") as f:
        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
        # Discard first column which is execution time
        test_first, *test_lines, test_last = [line[1:] for line in reader]

    with open(expected_log) as f:
        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
        # Discard first column which is execution time
        expected_first, *expected_lines, expected_last = [line[1:] for line in reader]
    assert test_lines == expected_lines
    # Check first line
    compare_dicts(
        dict_line(test_first),
        dict_line(expected_first),
        filter_keys={"started", "fixate-version"},
    )
    # CHeck last line
    compare_dicts(dict_line(test_last), dict_line(expected_last), filter_keys={"ended"})


log_dir = os.path.join(os.path.dirname(__file__), "expect-logs")
script_dir = os.path.join(os.path.dirname(__file__), "scripts")


def test_basicpass(tmpdir):
    script_path = os.path.join(script_dir, "basicpass.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")
    ret = subprocess.call(
        [
            "python",
            "-m",
            "fixate",
            "-p",
            script_path,
            "--serial-number",
            "0123456789",
            "--log-file",
            log_path,
            "--non-interactive",
        ]
    )
    assert ret == 5
    compare_logs(os.path.join(log_dir, "basicpass.csv"), log_path)


def test_basicfail(tmpdir):
    script_path = os.path.join(script_dir, "basicfail.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")
    ret = subprocess.call(
        [
            "python",
            "-m",
            "fixate",
            "-p",
            script_path,
            "--serial-number",
            "0123456789",
            "--log-file",
            log_path,
            "--non-interactive",
        ]
    )
    assert ret == 10
    compare_logs(os.path.join(log_dir, "basicfail.csv"), log_path)


basichierachy_data = [
    # the basic hierarchy test script has a test list with enter/exit, setup & teardown,
    # along with a single test which has a setup & tear down. By setting the "fail_flag"
    # or raise_flag as a script-param it is possible to force the script to fail a
    # check, or raise and exception in the flagged location.
    # Test for a simple passing case
    ["None", "None", None, 5],
    # Tests with a failing check
    ["test_test", "None", None, 10],
    ["test_setup", "None", None, 10],
    ["test_teardown", "None", None, 10],
    ["list_setup", "None", None, 10],
    ["list_teardown", "None", None, 10],
    # The current output of these is almost certainly not what we want. However I'm adding these for now as
    # a record of the current behaviour. It's not clear to me what the exit codes should be. At some point,
    # there is a level of definition to all of this. It's also not clear that it makes sense to allow checks
    # in the setup/tear down enter/exit, but if we don't stop it, we should at least test it.
    # In addition to all that, they fail because the log compare function assume the first and last lines of
    # the file are the sequence beginning and end entries. However, that is not the case when some exceptions are
    # raised. Ideally we will improve the log comparison to be more sophisticated.
    pytest.mark.xfail(["list_enter", "None", None, 11]),
    pytest.mark.xfail(["list_exit", "None", None, 11]),
    # Tests which raise an exception. Note: There are some bug in the order. We test the current behaviour
    ["None", "test_test", None, 10],
    # Tests which raise an exception. XFAIL tests which demonstrate the desired behaviour.
    pytest.mark.xfail(
        ["None", "test_test", "xfail", 10],
        reason="Assert Log order not chronological with checks",
        strict=True,
    ),
]


@pytest.mark.parametrize("fail_flag,raise_flag,xfail,return_code", basichierachy_data)
def test_basichierachy(tmpdir, fail_flag, raise_flag, xfail, return_code):
    script_path = os.path.join(script_dir, "basichierachy.py")
    log_path = os.path.join(str(tmpdir), "logfile.csv")

    if not xfail:
        expected_log_path = os.path.join(
            log_dir, "basichierachy-{}-{}.csv".format(fail_flag, raise_flag)
        )
    else:
        expected_log_path = os.path.join(
            log_dir, "basichierachy-{}-{}-{}.csv".format(fail_flag, raise_flag, xfail)
        )

    ret = subprocess.call(
        [
            "python",
            "-m",
            "fixate",
            "-p",
            script_path,
            "--serial-number",
            "0123456789",
            "--log-file",
            log_path,
            "--non-interactive",
            "--script-params",
            "fail_flag=" + fail_flag,
            "--script-params",
            "raise_flag=" + raise_flag,
        ]
    )

    assert ret == return_code
    compare_logs(expected_log_path, log_path)
