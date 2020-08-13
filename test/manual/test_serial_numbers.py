"""
Tests for opening various instruments without having to manually run test scripts
Make sure local_config.json has been configured to include the required instruments

"""
from pubsub import pub
from fixate.drivers import dmm, lcr, dso, funcgen, pps
import time
import pytest


@pytest.fixture(autouse=True)
def subscriber():
    """
    prevent pubsub topics being carried over between tests
    """
    pub.subscribe(writer_function, "driver_open")
    yield
    pub.unsubscribe(writer_function, "driver_open")


def writer_function(instr_type, identity):
    """
    function that would be used by the csv writer
    """
    msg = [
        "{:.2f}".format(time.perf_counter()),
        "DRIVER",
        instr_type,
        identity,
    ]
    print(msg)


def test_open_lcr():
    lcr.open()


def test_open_dmm():
    dmm.open()


def test_open_dso():
    dso.open()


def test_open_funcgen():
    funcgen.open()


def test_open_pps():
    pps.open()
