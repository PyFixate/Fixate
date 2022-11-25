import pytest
import re
from fixate.core.exceptions import *
from fixate.config import load_config
import time

load_config()  # Load fixate config file


@pytest.mark.drivertest
def test_open_dmm(dmm):
    import fixate.drivers.dso

    dmm = fixate.drivers.dmm.open()
    assert dmm, "Could not open DMM"


@pytest.mark.drivertest
def test_reset(dmm):
    # This test might need improving?
    dmm.reset()
    query = dmm.instrument.query("SYST:ERR?")
    assert '+0,"No error"' == query.strip()


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("voltage_ac", "VOLT:AC"),
        ("voltage_dc", "VOLT"),
        ("current_dc", "CURR"),
        ("current_ac", "CURR:AC"),
        ("resistance", "RES"),
        ("fresistance", "FRES"),
        ("period", "PER"),
        ("frequency", "FREQ"),
        ("capacitance", "CAP"),
        ("continuity", "CONT"),
        ("diode", "DIOD"),
        pytest.param("temperature", "TEMP", marks=pytest.mark.xfail),
        pytest.param("ftemperature", "TEMP", marks=pytest.mark.xfail),
    ],
)
@pytest.mark.drivertest
def test_mode(mode, expected, dmm):
    getattr(dmm, mode)()

    query = dmm.instrument.query("SENS:FUNC?")
    assert query.strip('"\r\n') == expected


@pytest.mark.parametrize("nsample", [50000, 1])
@pytest.mark.drivertest
def test_samples(nsample, dmm):
    dmm.samples = nsample
    query = dmm.instrument.query("SAMP:COUN?")
    assert nsample == int(query.strip())


@pytest.mark.parametrize("nsample", [50001, 0])
@pytest.mark.drivertest
def test_samples_over_range(nsample, dmm):

    with pytest.raises(InstrumentError) as excinfo:
        dmm.samples = nsample
    assert re.search("Invalid parameter", str(excinfo.value))


@pytest.mark.parametrize(
    "mode, range",
    [
        ("voltage_ac", 1),
        ("voltage_ac", 10),
        ("voltage_dc", 1),
        ("voltage_dc", 10),
        ("current_dc", 1),
        ("current_dc", 10),
        ("current_ac", 1),
        ("current_ac", 10),
        ("resistance", 10),
        ("resistance", 10e6),
        ("fresistance", 10),
        ("fresistance", 10e6),
        ("capacitance", 1e-6),
        ("capacitance", 1e-9),
    ],
)
@pytest.mark.drivertest
def test_range(mode, range, dmm):
    getattr(dmm, mode)(_range=range)
    mod = dmm.instrument.query("SENS:FUNC?").strip('"\r\n')
    query = dmm.instrument.query(mod + ":RANG?")
    assert float(query) == pytest.approx(range)


# DMM does not return an error for under range. It just clips the value.
# It does return an error for over range however..
@pytest.mark.parametrize(
    "mode, range",
    [
        ("voltage_ac", 10000),
        ("voltage_dc", 10000),
        ("current_dc", 100),
        ("current_ac", 100),
        ("resistance", 10e9),
        ("fresistance", 10e9),
        ("capacitance", 1),
    ],
)
@pytest.mark.drivertest
def test_range_over_range(mode, range, dmm):
    with pytest.raises(InstrumentError) as excinfo:
        getattr(dmm, mode)(_range=range)
    assert re.search("Invalid parameter", str(excinfo.value))


@pytest.mark.parametrize(
    "mode, range",
    [
        ("frequency", 100e-3),
        ("frequency", 1000),
        ("period", 100e-3),
        ("period", 1000),
    ],
)
@pytest.mark.drivertest
def test_frequency_input_range(mode, range, dmm):
    getattr(dmm, mode)(_range=range)
    mod = dmm.instrument.query("SENS:FUNC?").strip('"\r\n')
    query = dmm.instrument.query(mod + ":VOLT:RANG?")

    assert float(query) == pytest.approx(range)


# DMM does not return an error for under range. It just clips the value.
# It does return an error for over range however..
@pytest.mark.parametrize(
    "mode, range",
    [
        ("frequency", 10e12),
        ("period", 10e12),
    ],
)
@pytest.mark.drivertest
def test_frequency_input_over_range(mode, range, dmm):
    with pytest.raises(InstrumentError) as excinfo:
        getattr(dmm, mode)(_range=range)
    assert re.search("Invalid parameter", str(excinfo.value))


@pytest.mark.parametrize(
    "mode",
    [
        "voltage_dc",
        "current_dc",
        "resistance",
        "fresistance",
    ],
)
@pytest.mark.drivertest
@pytest.mark.xfail(reason="Digital filter function not implemented correctly.")
def test_digital_filter(mode, dmm):
    getattr(dmm, mode)()
    dmm.digital_filter()

    mod = dmm.instrument.query("SENS:FUNC?").strip('"\r\n')
    query = dmm.instrument.query(mod + ":FILT:DIG?")

    assert query.strip('"\r\n') == "1"


@pytest.mark.parametrize(
    "mode",
    [
        "voltage_dc",
        "current_dc",
        "resistance",
        "fresistance",
    ],
)
@pytest.mark.drivertest
@pytest.mark.xfail(reason="Analog filter function not implemented correctly.")
def test_analog_filter(mode, dmm):
    getattr(dmm, mode)()
    dmm.analog_filter()

    mod = dmm.instrument.query("SENS:FUNC?").strip('"\r\n')
    query = dmm.instrument.query(mod + ":FILT:DIG?")

    assert query.strip('"\r\n') == "1"


@pytest.mark.drivertest
def test_measurement_resistance_2w(dmm, rm):
    dmm.samples = 5
    rm.mux.connectionMap("DMM_R1_2w")

    dmm.resistance(_range=100)
    res = dmm.measurement()
    assert res == pytest.approx(100, abs=1)


@pytest.mark.drivertest
def test_measurement_resistance_4w(dmm, rm):
    rm.mux.connectionMap("DMM_R1_4w")

    dmm.fresistance(_range=100)
    res = dmm.measurement()
    assert res == pytest.approx(100, abs=1)


@pytest.mark.drivertest
def test_measurement_voltage_dc(funcgen, dmm, rm):
    v = 100e-3
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.dc()
    funcgen.channel1.offset(v)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.voltage_dc(_range=100e-3)
    vdc = dmm.measurement()

    assert vdc == pytest.approx(v, abs=1e-3)


@pytest.mark.drivertest
def test_measurement_voltage_ac(funcgen, dmm, rm):
    v = 50e-3
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.voltage_ac(_range=100e-3)
    vrms = dmm.measurement()
    assert vrms == pytest.approx(v, abs=1e-3)


# Need to change jig wiring to measure anything other than 0
@pytest.mark.drivertest
def test_measurement_current_dc(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.current_dc(_range=100e-3)
    idc = dmm.measurement()

    assert idc == pytest.approx(0, abs=0.5e-3)


# Need to change jig wiring to measure anything other than 0
@pytest.mark.drivertest
def test_measurement_current_ac(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.current_ac(_range=100e-3)
    iac = dmm.measurement()

    assert iac == pytest.approx(0, abs=0.5e-3)


@pytest.mark.drivertest
def test_measurement_capacitance(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_C1")
    dmm.capacitance(_range=10e-6)
    c = dmm.measurement()

    assert c == pytest.approx(4.7e-6, abs=0.5e-6)


@pytest.mark.drivertest
def test_measurement_frequency(funcgen, dmm, rm):
    v = 50e-3
    f = 1000
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1.frequency(f)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.frequency(_range=100e-3)
    freq = dmm.measurement()
    assert freq == pytest.approx(freq, abs=10)


@pytest.mark.drivertest
def test_measurement_period(funcgen, dmm, rm):
    v = 50e-3
    f = 1000
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1.frequency(f)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.period(_range=100e-3)
    per = dmm.measurement()
    assert per == pytest.approx(1 / f, abs=5e-6)


@pytest.mark.drivertest
def test_measurement_continuity(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.continuity()
    cont = dmm.measurement()
    assert cont == pytest.approx(100, abs=1)


@pytest.mark.drivertest
def test_measurement_diode(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_D1")
    dmm.diode()
    meas = dmm.measurement()
    assert meas == pytest.approx(0.5, abs=0.05)


@pytest.mark.drivertest
def test_get_identity(dmm):
    iden = dmm.get_identity()
    assert "FLUKE,8846A" in iden
