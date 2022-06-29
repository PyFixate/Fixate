import pytest

"""These tests are a very minimum smoke test on the drivers.

while we work to get a more complete test in place that includes the
hardware, these are a minimum check that the module can at least
be imported"""


def test_driver_files():
    import fixate.drivers.dmm
    import fixate.drivers.dso
    import fixate.drivers.funcgen
    import fixate.drivers.lcr
    import fixate.drivers.pps


# Loading Pydaqmx will fail with NotImplementedError if the .h file is not found
# and an OSError if loading the .dll fails
@pytest.mark.xfail(
    raises=(OSError, NotImplementedError), reason="Requires DAQ DLL and .h"
)
def test_daq_driver_import():
    import fixate.drivers.daq


# NOTE: our ftdi library raises an import error if loading .dll failes
# This is masking a good portion of what we are trying to test.
@pytest.mark.xfail(raises=ImportError, reason="Requires FTDI DLL")
def test_ftdi_driver_import():
    import fixate.drivers.ftdi
