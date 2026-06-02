import pytest
from fixate.config import load_config
import fixate.drivers.dcload
from fixate.drivers.dcload.rigol_dl3021 import Mode
import time

load_config()  # Load fixate config file


@pytest.mark.drivertest
def test_open_dcload():
    opened = fixate.drivers.dcload.open()
    assert opened, "Could not open DCLoad"


@pytest.mark.drivertest
def test_get_identity(dcload):
    iden = dcload.get_identity()
    assert "DL3021" in iden


@pytest.mark.drivertest
def test_enable_load(dcload):
    # Turn load ON
    dcload.set_enabled(True)
    assert dcload.get_enabled() is True, "Load should be ON"
    # Turn load OFF
    dcload.set_enabled(False)
    assert dcload.get_enabled() is False, "Load should be OFF"


@pytest.mark.drivertest
@pytest.mark.parametrize(
    "mode, expected",
    [
        (Mode.CONSTANT_CURRENT, "CC"),
        (Mode.CONSTANT_VOLTAGE, "CV"),
        (Mode.CONSTANT_RESISTANCE, "CR"),
        (Mode.CONSTANT_POWER, "CP"),
    ],
)
def test_set_mode(dcload, mode, expected):
    """
    Verify that set_mode correctly sets the instrument mode.
    """
    dcload.set_mode(mode)
    actual = dcload.get_mode()

    assert actual == expected, f"Expected {expected}, got {actual}"

    dcload.set_enabled(False)


@pytest.mark.drivertest
@pytest.mark.parametrize(
    "min_current, max_current, num_steps, duration",
    [
        (0.0, 1.0, 6, 2),
    ],
)
def test_set_current(dcload, min_current, max_current, num_steps, duration):
    # Generate evenly spaced current values (inclusive)
    if num_steps == 1:
        currents = [min_current]
    else:
        step = (max_current - min_current) / (num_steps - 1)
        currents = [min_current + i * step for i in range(num_steps)]

    # Set mode and range
    dcload.set_mode(Mode.CONSTANT_CURRENT)
    max_current_val = max(currents)
    dcload.set_current_range(max_current_val + 0.5)
    dcload.set_enabled(True)

    for current in currents:
        dcload.set_current(current)
        time.sleep(duration)
        setpoint = float(dcload.get_current())

        assert abs(setpoint - current) < 1e-3, f"Expected {current}A, got {setpoint}A"

    dcload.set_enabled(False)


@pytest.mark.drivertest
def test_reset(dcload):
    dcload.reset()
    query = dcload.query("SYST:ERR?")
    assert '0,"No error"' == query.strip()
