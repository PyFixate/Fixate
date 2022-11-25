import pytest
import re
import ctypes
import time
from fixate.core.exceptions import *
from fixate.config import load_config


load_config()  # Load fixate config file


@pytest.mark.drivertest
def test_open():
    import fixate.drivers.ftdi

    ftdi = fixate.drivers.ftdi.open(ftdi_description="Patch Panel Loop Back Jig")
    assert ftdi, "Could not open FTDI device"
    ftdi.close()


@pytest.mark.drivertest
def test_baud(ftdi, FTDException):
    # baud_rate setter checks the return code from the device
    ftdi.baud_rate = 115200


@pytest.mark.parametrize("baud", [1, 10, -2])
@pytest.mark.drivertest
def test_baud_invalid(ftdi, FTDException, baud):
    # Is try, except sufficient to test?
    # baud_rate setter checks the return code from the device
    with pytest.raises(FTDException) as excinfo:
        ftdi.baud_rate = baud
    assert re.search("INVALID_BAUD_RATE", str(excinfo.value))


@pytest.mark.parametrize("wordLength", [7, 8])
@pytest.mark.drivertest
def test_word_length(ftdi, wordLength):
    ftdi.word_length = wordLength
    ftdi._set_data_characteristics()


@pytest.mark.drivertest
def test_word_length_invalid(ftdi):
    with pytest.raises(ValueError):
        ftdi.word_length = 10
        ftdi._set_data_characteristics()


@pytest.mark.parametrize("stopBits", [2, 1])
@pytest.mark.drivertest
def test_stop_bits(ftdi, stopBits):
    ftdi.stop_bits = stopBits


@pytest.mark.drivertest
def test_stop_bits_invalid(ftdi):
    with pytest.raises(ValueError):
        ftdi.stop_bits = 10


@pytest.mark.parametrize("parity", ["none", "odd", "even"])
@pytest.mark.drivertest
def test_parity(ftdi, parity):
    ftdi.parity = parity


@pytest.mark.drivertest
def test_parity_invalid(ftdi):
    with pytest.raises(ValueError):
        ftdi.parity = "random"


@pytest.mark.drivertest
def test_write_bit_mode(ftdi):
    ftdi.write_bit_mode(0b110)


@pytest.mark.drivertest
def test_get_cbus_pins(ftdi):
    data_bus = ftdi.get_cbus_pins()  # Gets value of dataBus


@pytest.mark.drivertest
def test_configure_bit_bang(ftdi):
    ftdi.configure_bit_bang(
        ctypes.c_ulong(0x01),
        bytes_required=14,
        data_mask=4,
        clk_mask=2,
        latch_mask=1,
    )


@pytest.mark.drivertest
def test_serial_shift_bit_bang(ftdi):
    # Standard config for relay matrix:
    ftdi.configure_bit_bang(
        ctypes.c_ulong(0x01),
        bytes_required=14,
        data_mask=4,
        clk_mask=2,
        latch_mask=1,
    )
    ftdi.serial_shift_bit_bang(1152, bytes_required=2)  # Enable 1K1 on relay matrix
    time.sleep(0.5)
    ftdi.serial_shift_bit_bang(0)  # Turn off relay matrix
