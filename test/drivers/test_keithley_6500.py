import pytest
import re
from fixate.core.exceptions import *
from fixate.config import load_config
import time

load_config()  # Load fixate config file

# Test values for measurement functions:
# These are mostly defined either by J413 or an arbitrary number I picked.
TEST_RESISTANCE = 100  # Resistance in loopback jig for testing
TEST_RESISTANCE_TOL = 1  # 1 Ohm absolute tolerance
TEST_CAPACITANCE = 4.7e-6  # Capacitance in loopback jig for testing
TEST_CAPACITANCE_TOL = 0.5e-6
TEST_VOLTAGE_DC = 100e-3
TEST_VOLTAGE_DC_TOL = 1e-3
TEST_VOLTAGE_AC = 50e-3
TEST_VOLTAGE_AC_TOL = 1e-3
TEST_CURRENT_DC = 0
TEST_CURRENT_DC_TOL = 0.5e-3
TEST_CURRENT_AC = 0
TEST_CURRENT_AC_TOL = 0.5e-3
TEST_DIODE = 0.5
TEST_DIODE_TOL = 0.05
TEST_FREQ = 1e3
TEST_FREQ_TOL = 10
TEST_PERIOD = 1 / TEST_FREQ
TEST_PERIOD_TOL = 0.5e-3


@pytest.mark.drivertest
def test_open_dmm(dmm):
    import fixate.drivers.dso

    dmm = fixate.drivers.dmm.open()
    assert dmm, "Could not open DMM"


@pytest.mark.drivertest
def test_reset(dmm):
    dmm.reset()
    query = dmm.instrument.query("SYST:ERR?")
    assert '0,"No error;0;0 0"' == query.strip()


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("voltage_ac", "VOLT:AC"),
        ("voltage_dc", "VOLT:DC"),
        ("current_dc", "CURR:DC"),
        ("current_ac", "CURR:AC"),
        ("resistance", "RES"),
        ("fresistance", "FRES"),
        ("period", "PER:VOLT"),
        ("frequency", "FREQ:VOLT"),
        ("capacitance", "CAP"),
        ("continuity", "CONT"),
        ("diode", "DIOD"),
        ("temperature", "TEMP"),
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
    query = dmm.instrument.query(":COUN?")
    assert nsample == int(query.strip())


@pytest.mark.parametrize("nsample", [1000001, 0])
@pytest.mark.drivertest
def test_samples_over_range(nsample, dmm):
    with pytest.raises(ParameterError) as excinfo:
        dmm.samples = nsample
    assert re.search("Number of samples out of bounds", str(excinfo.value))


@pytest.mark.parametrize(
    "mode, range",
    [
        ("voltage_ac", 1),
        ("voltage_ac", 10),
        ("voltage_dc", 1),
        ("voltage_dc", 10),
        ("current_dc", 10e-6),
        ("current_dc", 3),
        ("current_ac", 100e-6),
        ("current_ac", 3),
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
    assert re.search("Parameter, measure range, expected value", str(excinfo.value))


@pytest.mark.parametrize(
    "mode, range",
    [
        ("frequency", 100e-3),
        ("frequency", 750),
    ],
)
@pytest.mark.drivertest
def test_frequency_input_range(mode, range, dmm):
    getattr(dmm, mode)(_volt_range=range)
    query = dmm.instrument.query(":SENS:FREQ:THR:RANG?")

    assert float(query) == pytest.approx(range)


@pytest.mark.parametrize(
    "mode, range",
    [
        ("period", 100e-3),
        ("period", 750),
    ],
)
@pytest.mark.drivertest
def test_period_input_range(mode, range, dmm):
    getattr(dmm, mode)(_volt_range=range)
    query = dmm.instrument.query(":SENS:PER:THR:RANG?")

    assert float(query) == pytest.approx(range)


@pytest.mark.parametrize(
    "mode, range",
    [
        ("frequency", 1000),
        ("period", 1000),
    ],
)
@pytest.mark.drivertest
def test_frequency_input_over_range(mode, range, dmm):
    with pytest.raises(InstrumentError) as excinfo:
        getattr(dmm, mode)(_volt_range=range)
    assert re.search("Parameter, measure threshold range", str(excinfo.value))


@pytest.mark.drivertest
def test_manual_trigger_exception(dmm):
    dmm.reset()  # Make sure DMM is not in manual trigger mode
    dmm.voltage_ac(10)
    with pytest.raises(InstrumentError) as excinfo:
        dmm.trigger()
    assert re.search("Manual trigger mode not set", str(excinfo.value))


@pytest.mark.drivertest
def test_manual_trigger(dmm):
    dmm.reset()  # Make sure DMM is not in manual trigger mode
    dmm.voltage_ac(10)
    dmm.set_manual_trigger(samples=10)  # Setup manual triggering
    dmm.trigger()  # Take the samples

    samples = dmm.measurements()

    assert (
        dmm._manual_trigger == True
    )  # Make sure mode setter is at least setting the flag
    assert len(samples) == 10  # Make sure we got what we asked for


@pytest.mark.drivertest
def test_measurement_resistance_2w(dmm, rm):
    dmm.samples = 5
    rm.mux.connectionMap("DMM_R1_2w")

    dmm.resistance(_range=100)
    res = dmm.measurement()
    assert res == pytest.approx(TEST_RESISTANCE, abs=TEST_RESISTANCE_TOL)


@pytest.mark.drivertest
def test_measurement_resistance_4w(dmm, rm):
    rm.mux.connectionMap("DMM_R1_4w")

    dmm.fresistance(_range=100)
    res = dmm.measurement()
    assert res == pytest.approx(TEST_RESISTANCE, abs=TEST_RESISTANCE_TOL)


@pytest.mark.drivertest
def test_measurement_voltage_dc(funcgen, dmm, rm):
    v = TEST_VOLTAGE_DC
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.dc()
    funcgen.channel1.offset(v)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.voltage_dc(_range=100e-3)
    vdc = dmm.measurement()

    assert vdc == pytest.approx(v, abs=TEST_VOLTAGE_DC)


@pytest.mark.drivertest
def test_measurement_voltage_ac(funcgen, dmm, rm):
    v = TEST_VOLTAGE_AC
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.voltage_ac(_range=100e-3)
    vrms = dmm.measurement()
    assert vrms == pytest.approx(v, abs=TEST_VOLTAGE_AC_TOL)


# Need to change jig wiring to measure anything other than 0
@pytest.mark.drivertest
def test_measurement_current_dc(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.current_dc(_range=100e-3)
    idc = dmm.measurement()

    assert idc == pytest.approx(TEST_CURRENT_DC, abs=TEST_CURRENT_DC_TOL)


# Need to change jig wiring to measure anything other than 0
@pytest.mark.drivertest
def test_measurement_current_ac(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.current_ac(_range=100e-3)
    iac = dmm.measurement()

    assert iac == pytest.approx(TEST_CURRENT_AC, abs=TEST_CURRENT_AC_TOL)


@pytest.mark.drivertest
def test_measurement_capacitance(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_C1")
    dmm.capacitance(_range=10e-6)
    c = dmm.measurement()

    assert c == pytest.approx(TEST_CAPACITANCE, abs=TEST_CAPACITANCE_TOL)


@pytest.mark.drivertest
def test_measurement_frequency(funcgen, dmm, rm):
    v = 50e-3
    f = TEST_FREQ
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1.frequency(f)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.frequency(_volt_range=100e-3)
    freq = dmm.measurement()
    assert freq == pytest.approx(freq, abs=TEST_FREQ_TOL)


@pytest.mark.drivertest
def test_measurement_period(funcgen, dmm, rm):
    v = 50e-3
    f = TEST_FREQ_TOL
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1.frequency(f)
    funcgen.channel1(True)

    time.sleep(0.5)
    dmm.period(_volt_range=100e-3)
    per = dmm.measurement()
    assert per == pytest.approx(1 / f, abs=TEST_PERIOD_TOL)


@pytest.mark.drivertest
def test_measurement_continuity(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_R1_2w")
    dmm.continuity()
    cont = dmm.measurement()
    assert cont == pytest.approx(TEST_RESISTANCE, abs=TEST_RESISTANCE_TOL)


@pytest.mark.drivertest
def test_measurement_diode(funcgen, dmm, rm):
    rm.mux.connectionMap("DMM_D1")
    dmm.diode()
    meas = dmm.measurement()
    assert meas == pytest.approx(TEST_DIODE, abs=TEST_DIODE_TOL)


@pytest.mark.drivertest
def test_get_nplc(dmm):
    dmm.voltage_dc()
    dmm.set_nplc(reset=True)
    query = dmm.get_nplc()
    assert query == pytest.approx(1)


@pytest.mark.drivertest
def test_set_nplc(dmm):
    dmm.voltage_dc()
    dmm.set_nplc(nplc=10)
    query = dmm.get_nplc()
    assert query == pytest.approx(10)

    dmm.set_nplc(nplc=None)  # Set to default
    query = dmm.get_nplc()
    assert query == pytest.approx(1)

    # invalid nplc value
    with pytest.raises(ParameterError):
        dmm.set_nplc(nplc=999)

    # invalid mode
    dmm.voltage_ac()
    with pytest.raises(ParameterError):
        dmm.set_nplc(nplc=1)


@pytest.mark.drivertest
def test_nplc_context_manager(dmm):
    dmm.voltage_dc()
    dmm.set_nplc(nplc=0.2)
    with dmm.nplc(1):
        query = dmm.get_nplc()
        assert query == pytest.approx(1)
    query = dmm.get_nplc()
    assert query == pytest.approx(0.2)

    with pytest.raises(ZeroDivisionError):
        with dmm.nplc(1):
            _ = 1 / 0  # make sure exception is not swallowed


@pytest.mark.drivertest
def test_min_avg_max(dmm, rm, funcgen):
    dmm.voltage_dc()
    dmm.set_nplc(nplc=0.02)

    values = dmm.min_avg_max(995, 1.1)
    min_val = values.min
    avg_val = values.avg
    max_val = values.max

    # does not guarantee that there is any input to the DMM so we can't guarantee that the min, avg, max are different
    assert min_val <= avg_val <= max_val

    v = 50e-3
    f = 50
    rm.mux.connectionMap("DMM_SIG")
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vrms(v)
    funcgen.channel1.frequency(f)
    funcgen.channel1(True)

    time.sleep(0.5)

    values = dmm.min_avg_max(995, 1.1)
    min_val = values.min
    avg_val = values.avg
    max_val = values.max

    assert min_val < avg_val < max_val


@pytest.mark.drivertest
def test_get_identity(dmm):
    iden = dmm.get_identity()
    assert "KEITHLEY INSTRUMENTS,MODEL DMM6500" in iden
