import time
from typing import Literal
import pytest
from fixate.config import load_config
import fixate.drivers.dcload
from fixate.drivers.dcload.rigol_dl3021 import RigolDL3021

load_config()  # Load fixate config file


@pytest.mark.drivertest
def test_open_dcload():
    """Test that we can open a connection to the DC load."""
    opened = fixate.drivers.dcload.open()
    assert opened, "Could not open DCLoad"


@pytest.mark.drivertest
def test_get_identity(dcload: RigolDL3021):
    """Test that we can get the identity string from the DC load."""
    iden = dcload.get_identity()
    assert "DL3021" in iden


@pytest.mark.drivertest
def test_enable_load(dcload: RigolDL3021):
    """Test that we can enable and disable the load."""
    # Turn load ON
    dcload.set_enabled(True)
    assert dcload._get_enabled() is True, "Load should be ON"
    # Turn load OFF
    dcload.set_enabled(False)
    assert dcload._get_enabled() is False, "Load should be OFF"


@pytest.mark.drivertest
@pytest.mark.parametrize(
    "mode, expected",
    [
        ("constant_current", "CC"),
        ("constant_voltage", "CV"),
        ("constant_resistance", "CR"),
        ("constant_power", "CP"),
    ],
)
def test_set_mode(
    dcload: RigolDL3021,
    mode: Literal["constant_current"]
    | Literal["constant_voltage"]
    | Literal["constant_resistance"]
    | Literal["constant_power"],
    expected: Literal["CC"] | Literal["CV"] | Literal["CR"] | Literal["CP"],
):
    """Verify that set_mode correctly sets the instrument mode."""
    dcload.set_mode(mode)
    actual = dcload._get_mode()

    assert actual == expected, f"Expected {expected}, got {actual}"

    dcload.set_enabled(False)


@pytest.mark.drivertest
@pytest.mark.parametrize(
    "min_current, max_current, num_steps, duration",
    [
        (0.0, 1.0, 6, 2),
    ],
)
def test_set_current(
    dcload: RigolDL3021,
    min_current: float,
    max_current: float,
    num_steps: Literal[6],
    duration: Literal[2],
):
    """Test setting the current on the DC load."""
    # Generate evenly spaced current values (inclusive)
    if num_steps == 1:
        currents = [min_current]
    else:
        step = (max_current - min_current) / (num_steps - 1)
        currents = [min_current + i * step for i in range(num_steps)]

    # Set mode and range
    dcload.set_mode("constant_current")
    dcload.set_current_range("high")
    dcload.set_enabled(True)

    for current in currents:
        dcload.set_current(current)
        time.sleep(duration)
        setpoint = float(dcload._get_current())

        assert abs(setpoint - current) < 1e-3, f"Expected {current}A, got {setpoint}A"

    dcload.set_enabled(False)


@pytest.mark.drivertest
def test_reset(dcload: RigolDL3021):
    """Test that resetting the instrument clears errors."""
    dcload.reset()
    query = dcload._query("SYST:ERR?")
    assert '0,"No error"' == query.strip()
