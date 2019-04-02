import pytest
import time
import datetime
from fixate.core.checks import chk_smaller
from fixate.core.exceptions import CheckFail


def test_check_smaller():
    assert chk_smaller(1, 2)
    with pytest.raises(CheckFail):
        chk_smaller(2, 1)


def test_check_smaller_datetime_now():
    now = datetime.datetime.now()
    time.sleep(0.1)
    now_plus = datetime.datetime.now()
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)


def test_check_smaller_datetime_time():
    now = datetime.datetime.now()
    now = datetime.datetime.time(now)
    time.sleep(0.001)
    now_plus = datetime.datetime.now()
    now_plus = datetime.datetime.time(now_plus)
    assert chk_smaller(now, now_plus)
    with pytest.raises(CheckFail):
        chk_smaller(now_plus, now)


def test_check_smaller_datetime_milli():
    now = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
    now_minus = datetime.datetime(2000, 1, 1, 1, 1, 1, 0)
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

