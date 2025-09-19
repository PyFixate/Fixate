import pytest
import re
from fixate.core.exceptions import *
from fixate.config import load_config
import time
from typing import Tuple

load_config()  # Load fixate config file

# TODO: Add tests for "address" functions. Will likely have to xfail them because the PPS is not typically used with ethernet


@pytest.mark.drivertest
def test_open():
    import fixate.drivers.pps

    pps = fixate.drivers.pps.open()
    assert pps, "Could not open power supply"


@pytest.mark.parametrize("channel, query", [("channel1", "CH1"), ("channel2", "CH2")])
@pytest.mark.drivertest
def test_set_voltage(pps, channel, query):
    v = 0.1
    chan = getattr(pps, channel)
    chan.voltage(v)
    voltage = pps.instrument.query(query + ":VOLT?")
    assert float(voltage) == pytest.approx(v)


"""
    Old F/W = 1.01.01.02.05 Raises InstrumentError when voltage is set over range
    
    New F/W = 1.01.01.02.07R2 No longer raises InstrumentError when voltage is set over range
"""


@pytest.mark.xfail(
    reason="New firmware no longer raises InstrumentError on over range."
)
@pytest.mark.parametrize(
    "voltage, channel, query", [(32.1, "channel1", "CH1"), (32.1, "channel2", "CH2")]
)
@pytest.mark.drivertest
def test_set_voltage_over_range(pps, voltage, channel, query):
    chan = getattr(pps, channel)
    with pytest.raises(InstrumentError) as excinfo:
        chan.voltage(voltage)

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("channel, query", [("channel1", "CH1"), ("channel2", "CH2")])
@pytest.mark.drivertest
def test_set_current(pps, channel, query):
    i = 0.1
    chan = getattr(pps, channel)
    chan.current(i)
    current = pps.instrument.query(query + ":CURR?")
    assert float(current) == pytest.approx(i)


@pytest.mark.xfail(
    reason="New firmware no longer raises InstrumentError on over range."
)
@pytest.mark.parametrize(
    "current, channel, query", [(3.21, "channel1", "CH1"), (3.21, "channel2", "CH2")]
)
@pytest.mark.drivertest
def test_set_current_over_range(pps, current, channel, query):
    chan = getattr(pps, channel)
    with pytest.raises(InstrumentError) as excinfo:
        chan.current(current)

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize(
    "group, voltage",
    [
        ("group1", 1.111),
        ("group2", 1.211),
        ("group3", 1.311),
        ("group4", 1.411),
        ("group5", 1.511),
    ],
)
@pytest.mark.drivertest
def test_save_recall(pps, group, voltage):
    # The save command on its own will not error even if there is a typo in the message sent to the PPS.
    # The only way to test the save command is to verify with the recall command.
    pps.channel1.voltage(voltage)
    pps.channel2.voltage(voltage)
    getattr(pps.save, group)()  # Save settings
    time.sleep(0.5)  # PPS is slow. Need delays
    pps.channel1.voltage(0)  # Set to something different
    time.sleep(0.5)
    getattr(pps.recall, group)()  # Recall settings
    time.sleep(0.5)
    query = pps.instrument.query("CH1:VOLT?")
    assert float(query) == pytest.approx(voltage, abs=50e-3)


@pytest.mark.drivertest
def test_series_voltage(pps):
    v = 0.1
    pps.series.voltage(v)

    query1 = pps.instrument.query("CH1:VOLT?")
    query2 = pps.instrument.query("CH2:VOLT?")
    assert float(query1) + float(query2) == pytest.approx(v)


@pytest.mark.drivertest
def test_parallel_voltage(pps):
    v = 0.1
    pps.parallel.voltage(v)

    query1 = pps.instrument.query("CH1:VOLT?")
    query2 = pps.instrument.query("CH2:VOLT?")
    assert (float(query1) + float(query2)) / 2 == pytest.approx(v)


@pytest.mark.drivertest
def test_series_current(pps):
    i = 0.1
    pps.series.current(i)

    query1 = pps.instrument.query("CH1:CURR?")
    query2 = pps.instrument.query("CH2:CURR?")
    assert (float(query1) + float(query2)) / 2 == pytest.approx(i)


@pytest.mark.drivertest
def test_parallel_current(pps):
    i = 0.1
    pps.parallel.current(i)

    query1 = pps.instrument.query("CH1:CURR?")
    query2 = pps.instrument.query("CH2:CURR?")
    assert float(query1) + float(query2) == pytest.approx(i)


@pytest.mark.parametrize(
    "voltage, channel, query", [(1.2, "channel1", "CH1"), (2.2, "channel2", "CH2")]
)
@pytest.mark.drivertest
def test_measure_voltage(pps, channel, query, voltage):
    ch = getattr(pps, channel)
    ch.voltage(voltage)
    ch.current(0.1)

    ch(True)  # Channel ON
    time.sleep(1)  # Slow PPS again
    v = ch.measure.voltage()
    ch(False)  # Channel ON
    assert float(v) == pytest.approx(voltage, abs=50e-3)


# Need to use the patch jig to test any current other than 0.
@pytest.mark.parametrize(
    "current, channel, query", [(0.0, "channel1", "CH1"), (0.0, "channel2", "CH2")]
)
@pytest.mark.drivertest
def test_measure_current(pps, channel, query, current):
    ch = getattr(pps, channel)
    ch.current(current)

    ch(True)  # Channel ON
    time.sleep(1)  # Slow PPS again
    i = ch.measure.current()
    ch(False)  # Channel ON
    assert float(i) == pytest.approx(current, abs=1e-3)


# Need to use the patch jig to test any current other than 0.
@pytest.mark.parametrize(
    "current, voltage, channel, query",
    [(0.0, 1.1, "channel1", "CH1"), (0.0, 1.1, "channel2", "CH2")],
)
@pytest.mark.drivertest
def test_measure_power(pps, channel, query, current, voltage):
    ch = getattr(pps, channel)
    ch.current(current)

    ch(True)  # Channel ON
    time.sleep(1)  # Slow PPS again
    i = ch.measure.current()
    ch(False)  # Channel OFF
    assert float(i) == pytest.approx(current, abs=1e-3)


@pytest.mark.parametrize(
    "channel, waveform",
    [
        (
            "channel1",
            [[0.5, 0.5, 1], [1, 0.5, 1], [1.5, 0.5, 1], [2, 0.5, 1], [2.5, 0.5, 1]],
        ),
        (
            "channel2",
            [[0.5, 0.5, 1], [1, 0.5, 1], [1.5, 0.5, 1], [2, 0.5, 1], [2.5, 0.5, 1]],
        ),
    ],
)
@pytest.mark.drivertest
def test_set_timer(pps, channel, waveform):
    try:
        ch = getattr(pps, channel)
        ch.timer.set_waveform(waveform)
    except InstrumentError:
        assert False, "Error in set_timer test."


# The "wave" function is purely a display change.
@pytest.mark.drivertest
def test_set_wave(pps):
    try:
        pps.channel1.wave(True)
        time.sleep(1)
        pps.channel1.wave(False)
    except InstrumentError:
        assert False, "Error setting wave display"


@pytest.mark.drivertest
def test_identity(pps):
    idn = pps.get_identity()
    assert "Siglent Technologies,SPD3303X" in idn


""" Testing the regex parsing of error strings returned by SYST:ERR? query
    Note the response strings vary between firmware versions:
        Old F/W = 1.01.01.02.05     (released 2017)
            '<code> <message>'
        New F/W = 1.01.01.02.07R2   (released 2021)
            '±<code>, <message>'
"""

error_strings = [
    ("0 No Error", (0, "No Error")),  # Old F/W
    ("+0, No Error", (0, "No Error")),  # New F/W
    ("128 Error 128", (128, "Error 128")),  # OLD F/W
    ("+128, Error 128", (128, "Error 128")),  # New F/W
    ("-113,Undefined header,*ID2N?", (-113, "Undefined header,*ID2N?")),
    ("-113,Undefined header,SYST:ERR", (-113, "Undefined header,SYST:ERR")),
]


@pytest.mark.drivertest
@pytest.mark.parametrize(("error_string", "expected"), error_strings)
def test_error_parsing(pps, error_string: str, expected: Tuple):
    assert pps._parse_errors(error_string) == expected
