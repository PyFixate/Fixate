import pytest
import time
from fixate.core.checks import chk_smaller
from fixate.core.exceptions import CheckFail
from datetime import datetime, timedelta
from fixate.core.checks import CheckClass, chk_in_range, _in_range
from fixate.ui_cmdline.cmd_line import _print_comparisons


def test_time_struct_check_true():
    t = time.localtime(1545925765)
    chk = chk_in_range(t, time.localtime(1545925760), time.localtime(1545925777), "Time is in range")
    assert chk


def test_time_struct_check_false():
    with pytest.raises(CheckFail):
        t = time.localtime(1554452763)
        chk = chk_in_range(t, time.localtime(1545925760), time.localtime(1545925777), "Time is NOT in range")


def test_datetime_struct_check_true():
    t_min = datetime.now()
    time.sleep(1)
    t = datetime.now()
    time.sleep(1)
    t_max = datetime.now()
    chk = chk_in_range(t, t_min, t_max, "DateTime is in range")
    assert chk


def test_datetime_struct_check_false():
    with pytest.raises(CheckFail):
        t_min = datetime.now()
        time.sleep(1)
        t_max = datetime.now()
        time.sleep(1)
        t = datetime.now()
        chk = chk_in_range(t, t_min, t_max, "DateTime is not in range")
        assert chk


def test_check_formatting(capsys):
    '''
    Check output of checks for ints, datetime objects and floats
    :param capsys:
    :return:
    '''
    chk1 = CheckClass(_min=2, _max=4, test_val=3, target=_in_range)
    date_obj = datetime(2019, 1, 1, 0, 0)
    chk2 = CheckClass(_min=date_obj - timedelta(seconds=2), _max=date_obj + timedelta(seconds=2), test_val=date_obj, target=_in_range)
    chk3 = CheckClass(_min=2.12345, _max=3.12345, test_val=2.9876543210, target=_in_range)

    _print_comparisons(True, chk1, 1, None)
    captured = capsys.readouterr()
    assert captured.out.strip('\n') == "Check 1: PASS when comparing 3 in range 2 - 4 :"
    _print_comparisons(True, chk2, 2, None)
    captured = capsys.readouterr()
    output = "Check 2: PASS when comparing 2019-01-01 00:00:00 in range {} - {} :".format(date_obj - timedelta(seconds=2),
                                                                                 date_obj + timedelta(seconds=2))
    expected = captured.out.strip('\n').replace('\n', ' ')
    assert output == expected
    _print_comparisons(True, chk3, 3, None)
    captured = capsys.readouterr()
    assert captured.out.strip('\n') == "Check 3: PASS when comparing 2.99 in range 2.12 - 3.12 :"


def test_check_smaller():
    assert chk_smaller(1, 2)
    with pytest.raises(CheckFail):
        chk_smaller(2, 1)


def test_check_smaller_datetime_now():
    now = datetime.now()
    time.sleep(0.1)
    now_plus = datetime.now()
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)


def test_check_smaller_datetime_time():
    now = datetime.now()
    now = datetime.time(now)
    time.sleep(0.001)
    now_plus = datetime.now()
    now_plus = datetime.time(now_plus)
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)


def test_check_smaller_datetime_milli():
    now = datetime(2000, 1, 1, 1, 1, 1, 1)
    now_minus = datetime(2000, 1, 1, 1, 1, 1, 0)
    assert chk_smaller(now_minus, now)
    with pytest.raises(CheckFail):
        chk_smaller(now, now_minus)


def test_check_smaller_time():
    now = time.time()
    time.sleep(1)
    now_plus = time.time()
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)


def test_check_smaller_localtime():
    now = time.localtime()
    time.sleep(1)
    now_plus = time.localtime()
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)

