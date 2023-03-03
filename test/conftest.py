import pytest
from pyvisa import VisaIOError


# INSTUMENT FIXTURES FOR DRIVER TESTS:
@pytest.fixture()
def funcgen():
    from drivers.J413 import dm

    try:
        funcgen = dm.funcgen
        funcgen.reset()
    except VisaIOError:
        assert False, "Could not open function generator"
    yield funcgen

    funcgen.reset()
    funcgen.channel1(False)


@pytest.fixture()
def dso():
    from drivers.J413 import dm

    try:
        dso = dm.dso
        dso.reset()
    except VisaIOError:
        assert False, "Could not open DSO."

    yield dso
    dso.reset()


@pytest.fixture()
def dmm():
    from drivers.J413 import dm

    try:
        dmm = dm.dmm
        dmm.reset()
        dmm.instrument.timeout = 7000
    except VisaIOError:
        assert False, "Could not open DMM."

    yield dmm


@pytest.fixture()
def pps():
    from drivers.J413 import dm

    try:
        pps = dm.pps
    except VisaIOError:
        assert False, "Could not open PPS."

    yield pps


# Relay Matrix for jig 413
@pytest.fixture()
def rm():
    from drivers.J413 import dm

    try:
        rm = dm.ftdi_J413
        rm.reset()
    except InstrumentNotConnected:
        False, "Could not open relay matrix"

    yield rm
    rm.reset()


@pytest.fixture()
def ftdi():
    import fixate.drivers.ftdi

    try:
        ftdi = fixate.drivers.ftdi.open()
        ftdi.reset()
    except Exception:
        False, "Could not open FTDI device."

    yield ftdi
    ftdi.close()


@pytest.fixture()
def FTDException():
    from fixate.drivers.ftdi import FTD2XXError as FTexception

    return FTexception
