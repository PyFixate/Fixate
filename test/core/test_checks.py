import subprocess
import os.path
import sys

import pytest

from fixate.core.checks import *
from fixate.core.exceptions import CheckFail
import fixate.sequencer


chk_pass_data = [
    (chk_passes, [], {"description": "test abc description"}),
    (chk_log_value, [123], {"fmt": ".2f"}),
    (chk_in_range, [10, 1, 100], {}),
    (chk_in_tolerance, [10.1, 10, 2], {}),
    (chk_in_tolerance, [-5.2, -5, 10], {}),
    (chk_in_range_equal, [13, 10, 15], {}),
    (chk_in_range_equal, [10.12, 10.12, 15], {}),
    (chk_in_range_equal, [15.1, 10, 15.1], {}),
    (chk_in_range_equal, [-5, -6, -4], {}),
    (chk_in_range_equal_min, [12, 12, 15], {}),
    (chk_in_range_equal_max, [1e3, 12, 1e3], {}),
    (chk_outside_range, [1.1e3, 12, 1e3], {}),
    (chk_outside_range, [11, 12, 1e3], {}),
    (chk_outside_range_equal, [1e3, 12, 1e3], {}),
    (chk_outside_range_equal, [6, 12, 1e3], {}),
    (chk_outside_range_equal, [12, 12, 1e3], {}),
    (chk_outside_range_equal_min, [12, 12, 1e3], {}),
    (chk_outside_range_equal_max, [7e4, 12, 7e4], {}),
    (chk_smaller_or_equal, [23, 23], {}),
    (chk_smaller_or_equal, [-1e3, -1e2], {}),
    (chk_greater_or_equal, [-1e2, -1e3], {}),
    (chk_greater_or_equal, [123456, 123456], {}),
    (chk_smaller, [123456, 123457], {}),
    (chk_greater, [10, 9], {}),
    (chk_true, [1 == 1], {}),
    (chk_false, [1 < 1], {}),
    (chk_in_tolerance_equal, [12345.6, 12300, 1], {}),
    (chk_in_tolerance_equal, [110, 100, 10], {}),
    (chk_in_deviation_equal, [60, 50, 10], {}),
    (chk_equal, ["string", "string"], {}),
    (chk_equal, [1e5, 1e5], {}),
    (chk_equal, [[1, 2, 3, 4], [1, 2, 3, 4]], {}),
    (chk_equal, [(1, 2, 3, 4), (1, 2, 3, 4)], {}),
    (chk_equal, [{"a": 1, "b": 2}, {"b": 2, "a": 1}], {}),
    (chk_equal, [2 + 1j, 2 + 1j], {}),
    # TODO: find more types that are equated?
]


@pytest.mark.parametrize(("check", "args", "kwargs"), chk_pass_data)
def test_fixate_checks(check: Callable, args, kwargs):
    """test checks pass"""
    assert check(*args, **kwargs)


chk_fail_data = [
    (chk_fails, [], {}),
    (chk_in_range, [10, 11, 100], {}),
    (chk_in_range, [10, 10, 100], {}),
    (chk_in_tolerance, [12, 10, 1], {}),
    (chk_in_tolerance, [11, 10, 1], {}),
    (chk_in_range_equal, [13, 10, 11], {}),
    (chk_in_range_equal_min, [15, 12, 15], {}),
    (chk_in_range_equal_max, [12, 12, 15], {}),
    (chk_outside_range, [1.1e3, 12, 1.1e3], {}),
    (chk_outside_range, [1e2, 12, 1e3], {}),
    (chk_outside_range_equal, [20, 15, 100], {}),
    (chk_outside_range_equal_min, [20, 15, 100], {}),
    (chk_outside_range_equal_min, [100, 15, 100], {}),
    (chk_outside_range_equal_max, [7e3, 12, 7e4], {}),
    (chk_outside_range_equal_max, [12, 12, 7e4], {}),
    (chk_smaller_or_equal, [23 + 1e-11, 23 + 1e-12], {}),
    (chk_greater_or_equal, [-1e-2, -1e-3], {}),
    (chk_smaller, [123456, 123456], {}),
    (chk_smaller, [123458, 123457], {}),
    (chk_greater, [9, 9], {}),
    (chk_greater, [9 - 1e-12, 9], {}),
    (chk_true, [False], {}),
    (chk_false, [True], {}),
    (chk_in_tolerance_equal, [110, 100, 5], {}),
    (chk_in_tolerance_equal, [-5, -10, 30], {}),
    (chk_in_deviation_equal, [61, 50, 10], {}),
    (chk_in_deviation_equal, [-1e3, -0.9e3, 0.09e3], {}),
    (chk_equal, ["string", "sTring"], {}),
    (chk_equal, [[1, 2, 3, 4], [1, 2, 3, 4, 5]], {}),
    (chk_equal, [{"a": 1, "b": 2}, {"b": 1, "a": 2}], {}),
    (chk_equal, [2 + 1j, 1 + 1j], {}),
]


@pytest.mark.parametrize(("check", "args", "kwargs"), chk_fail_data)
def test_fixate_checks_fail(check: Callable, args, kwargs):
    """test checks fail"""
    with pytest.raises(CheckFail):
        check(*args, **kwargs)


@pytest.fixture
def mock_check_string(monkeypatch):
    """Mock the call to sequencer.check to return the check_string"""

    def mock_check(self, chkresult: CheckResult):
        return chkresult.check_string

    monkeypatch.setattr(fixate.sequencer.Sequencer, "check", mock_check)


chk_ui_string = [
    (chk_passes, [], {"description": "test"}, "PASS: test"),
    (
        chk_log_value,
        [123],
        {"description": "test float .2", "fmt": ".2f"},
        f"PASS: {123:.2f} : test float .2",
    ),
    (
        chk_log_value,
        [123.456],
        {"description": "test float", "fmt": ".2f"},
        f"PASS: {123.456:.2f} : test float",
    ),
    # (chk_log_value, [123.456], {"fmt": ".2f"}, ""),
    # (chk_log_value, [123], {"fmt": ".2f"}, ""),
    # (chk_equal, ["string", "string"], {}),
    # (chk_equal, [1e5, 1e5], {}),
    # (chk_equal, [[1,2,3,4], [1,2,3,4]], {}),
    # (chk_equal, [(1,2,3,4), (1,2,3,4)], {}),
    # (chk_equal, [{"a":1, "b":2}, {"a":1, "b":2}], {}),
    # (chk_equal, [2+1j, 2+1j], {}),
]


@pytest.mark.parametrize(("check", "args", "kwargs", "check_string"), chk_ui_string)
def test_checks_formatting(
    mock_check_string, check: Callable, args, kwargs, check_string
):
    """Test different formatting options"""
    assert check(*args, **kwargs) == check_string


def test_checks_logging():
    """TODO: somehow test checks are logged properly"""
    # NOTE: tiny coverage in test_script2log
    pass


test_raise_data = [
    # Missing args - probably overkill
    (chk_in_range, [], {}, TypeError),
    (chk_in_tolerance, [], {}, TypeError),
    (chk_in_range_equal, [], {}, TypeError),
    (chk_outside_range, [], {}, TypeError),
    (chk_outside_range_equal, [], {}, TypeError),
    (chk_outside_range_equal_min, [], {}, TypeError),
    (chk_outside_range_equal_max, [], {}, TypeError),
    (chk_smaller_or_equal, [], {}, TypeError),
    (chk_greater_or_equal, [], {}, TypeError),
    (chk_smaller, [], {}, TypeError),
    (chk_greater, [], {}, TypeError),
    (chk_true, [], {}, TypeError),
    (chk_false, [], {}, TypeError),
    (chk_in_tolerance_equal, [], {}, TypeError),
    (chk_in_deviation_equal, [], {}, TypeError),
    (chk_equal, [], {}, TypeError),
    # Invalid args
    (chk_greater, [1, "test"], {}, TypeError),
    # Format exceptions are swallowed so hard to test
]


@pytest.mark.parametrize(("check", "args", "kwargs", "exception"), test_raise_data)
def test_checks_raise(check: Callable, args, kwargs, exception: Exception):
    """Test other exceptions raised"""
    with pytest.raises(exception):
        check(*args, **kwargs)


script_dir = os.path.join(os.path.dirname(__file__), "scripts")


def test_basiccheckcoverage(tmp_path):
    """Run each check through standard fixate process"""
    script_path = os.path.join(script_dir, "basiccheckcoverage.py")
    log_path = os.path.join(str(tmp_path), "logfile.csv")
    ret = subprocess.call(
        [
            sys.executable,
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
