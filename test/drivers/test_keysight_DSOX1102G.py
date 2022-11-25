import pytest
import re
from fixate.core.exceptions import *
from fixate.config import load_config

load_config()  # Load fixate config file

# TODO: Update tests to loop through all channels


def funcgen_sin(funcgen, v, frequency, offset, wavetype):
    funcgen.channel1.waveform.sin()
    if wavetype == "vrms":
        funcgen.channel1.vrms(v)
    else:
        funcgen.channel1.vpp(v)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)


def dso_setup_ch(dso, scale, time_scale, offset, ch):
    channel = getattr(dso, ch)
    channel.probe.attenuation(1)
    channel(True)
    dso.trigger.coupling.dc()
    dso.trigger.mode.edge.source.ch1()
    dso.trigger.mode.edge.slope.either()
    dso.trigger.mode.edge.level(offset)
    channel.scale(scale)  # Set range based on the voltage
    channel.offset(offset)
    dso.time_base.scale(time_scale)  # Set range based on the frequency
    dso.time_base.position(0)


@pytest.mark.drivertest
def test_open_dso(dso):
    import fixate.drivers.dso

    dso = fixate.drivers.dso.open()
    assert dso, "Could not open DSO"


@pytest.mark.parametrize("scale", [100, 5e-3])
@pytest.mark.drivertest
def test_channel_scale(scale, dso):

    dso.ch1.scale(scale)
    assert float(dso.query("CHAN1:SCAL?")) == pytest.approx(scale)


@pytest.mark.parametrize("scale", [1e-3, 200])
@pytest.mark.drivertest
def test_channel_scale_over_range(scale, dso):

    dso.ch1.scale(scale)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("CHAN1:SCAL?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("offset", [0, 20, -20])
@pytest.mark.drivertest
def test_offset(offset, dso):
    dso.ch1.scale(1)  # Set scales. Offset range is dependant on scale
    dso.ch2.scale(1)  # Set scales

    dso.ch1.offset(offset)
    query = float(dso.query("CHAN1:OFFS?"))
    assert query == pytest.approx(query)


@pytest.mark.parametrize("offset", [20.1, -20.1])
@pytest.mark.drivertest
def test_offset_over_range(offset, dso):
    dso.ch1.scale(1)  # Set scales. Offset range is dependant on scale
    dso.ch2.scale(1)  # Set scales

    dso.ch1.offset(offset)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("CHAN1:OFFS?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.drivertest
def test_coupling_ac(dso):
    dso.ch1.coupling.ac()
    assert dso.query("CHAN1:COUP?") == "AC\n"


@pytest.mark.drivertest
def test_coupling_dc(dso):
    dso.ch1.coupling.dc()
    assert dso.query("CHAN1:COUP?") == "DC\n"


@pytest.mark.parametrize("atten", [1.0, 0.1, 10000])
@pytest.mark.drivertest
def test_probe_attenuation(atten, dso):

    dso.ch1.probe.attenuation(atten)
    assert float(dso.query("CHAN1:PROB?")) == pytest.approx(atten)


@pytest.mark.parametrize("atten", [0.01, 20000])
@pytest.mark.drivertest
def test_probe_attenuation_over_range(atten, dso):

    dso.ch1.probe.attenuation(atten)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("CHAN1:PROB?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("scale", [50, 5e-9])
@pytest.mark.drivertest
def test_time_scale(scale, dso):
    dso.time_base.scale(scale)
    assert float(dso.query("TIM:SCAL?")) == pytest.approx(scale)


@pytest.mark.parametrize("scale", [60, 4e-9])
@pytest.mark.drivertest
def test_time_scale_over_range(scale, dso):
    dso.time_base.scale(scale)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("TIM:SCAL?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("pos", [10, -500, 500])
@pytest.mark.drivertest
def test_time_position(pos, dso):
    dso.time_base.scale(10)

    dso.time_base.position(pos)
    assert float(dso.query("TIM:POS?")) == pytest.approx(pos)


@pytest.mark.parametrize("pos", [-501, 501])
@pytest.mark.drivertest
def test_time_position_over_range(pos, dso):
    dso.time_base.position(pos)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("TIM:POS?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("level", [30, -30])
@pytest.mark.drivertest
def test_trigger_mode_edge(level, dso):
    dso.trigger.mode.edge.level(level)
    assert float(dso.query("TRIG:EDGE:LEVEL?")) == pytest.approx(level)


@pytest.mark.parametrize("level", [31, -31])
@pytest.mark.drivertest
def test_trigger_mode_edge_over_range(level, dso):
    dso.trigger.mode.edge.level(level)
    with pytest.raises(InstrumentError) as excinfo:
        dso.query("TRIG:EDGE:LEVEL?")

    assert re.search("Data out of range", str(excinfo.value))


@pytest.mark.parametrize("source, expected", [("ch1", "CHAN1"), ("ch2", "CHAN2")])
@pytest.mark.drivertest
def test_trigger_mode_source(source, expected, dso):

    sour = getattr(dso.trigger.mode.edge.source, source)
    sour()

    assert dso.query("TRIG:EDGE:SOUR?").strip() == expected


@pytest.mark.parametrize(
    "slope, expected",
    [("rising", "POS"), ("falling", "NEG"), ("either", "EITH"), ("alternating", "ALT")],
)
@pytest.mark.drivertest
def test_trigger_mode_slope(slope, expected, dso):

    sl = getattr(dso.trigger.mode.edge.slope, slope)
    sl()

    assert dso.query("TRIG:EDGE:SLOPE?").strip() == expected


@pytest.mark.parametrize("sweep, expected", [("normal", "NORM"), ("auto", "AUTO")])
@pytest.mark.drivertest
def test_trigger_mode_sweep(sweep, expected, dso):

    sw = getattr(dso.trigger.sweep, sweep)
    sw()

    assert dso.query("TRIG:SWE?").strip() == expected


@pytest.mark.parametrize(
    "coupling, expected", [("ac", "AC"), ("dc", "DC"), ("lf_reject", "LFR")]
)
@pytest.mark.drivertest
def test_trigger_coupling(coupling, expected, dso):

    coup = getattr(dso.trigger.coupling, coupling)
    coup()

    assert dso.query("TRIG:COUP?").strip() == expected


@pytest.mark.drivertest
def test_trigger_hf_reject(dso):
    dso.trigger.hf_reject(1)
    assert int(dso.query("TRIG:HFR?")) == 1


@pytest.mark.parametrize(
    "acq, expected",
    [
        ("normal", "NORM"),
        ("peak_detect", "PEAK"),
        ("averaging", "AVER"),
        ("high_resolution", "HRES"),
    ],
)
@pytest.mark.drivertest
def test_acquire(acq, expected, dso):

    if acq == "averaging":
        getattr(dso.acquire, acq)(200)
    else:
        getattr(dso.acquire, acq)()

    assert dso.query("ACQ:TYPE?").strip() == expected


## Measurement tests: ##
# TODO: define thresholds
# TODO: phase - dual channel
# TODO: vratio cycle - dual channel
# TODO: vratio display - dual channel
# TODO: cnt_edge_rising ? Not on this scope?
# TODO: cnt_edge_falling ? Not on this scope?
# TODO: cnt_pulse_positive ? Not on this scope?
# TODO: cnt_pulse_negative ? Not on this scope?


@pytest.mark.drivertest
def test_measure_frequency(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    vpp = 1
    frequency = 1000
    offset = 0.0
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_frequency = dso.measure.frequency.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_frequency == pytest.approx(frequency, abs=5)


@pytest.mark.drivertest
def test_measure_period(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    vpp = 1
    frequency = 1000
    offset = 0.0
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_period = dso.measure.period.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_period == pytest.approx((1 / frequency), abs=0.0001)


@pytest.mark.drivertest
def test_measure_vamplitude(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    vpp = 1
    frequency = 1000
    offset = 0.0
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vamp = dso.measure.vamplitude.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vamp == pytest.approx(vpp, abs=0.2)


@pytest.mark.drivertest
def test_measure_vaverage_cycle(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1
    offset = 0.5
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vav = dso.measure.vaverage.cycle.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vav == pytest.approx(offset, abs=0.05)


@pytest.mark.drivertest
def test_measure_vaverage_display(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1
    offset = 0.5
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vav = dso.measure.vaverage.display.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vav == pytest.approx(offset, abs=0.05)


@pytest.mark.drivertest
def test_measure_vbase(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1.5
    offset = 0.56
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vbase = dso.measure.vbase.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vbase == pytest.approx(-vpp / 2 + offset, abs=0.1)


@pytest.mark.drivertest
def test_measure_vtop(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1
    offset = 0.56
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vtop = dso.measure.vtop.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vtop == pytest.approx(vpp / 2 + offset, abs=0.05)


@pytest.mark.drivertest
def test_measure_vmax(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1.11
    offset = 0.211
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vmax = dso.measure.vmax.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vmax == pytest.approx(vpp / 2 + offset, abs=0.05)


@pytest.mark.drivertest
def test_measure_vmin(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1.5
    offset = 0.0
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vmin = dso.measure.vmin.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vmin == pytest.approx(-vpp / 2 + offset, abs=0.07)


@pytest.mark.drivertest
def test_measure_vpp(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vpp = 1.6
    offset = 0.31
    funcgen_sin(funcgen, vpp, frequency, offset, "vpp")

    ## DSO setup ##
    dso_setup_ch(dso, vpp / 4, (1 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vpp = dso.measure.vpp.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vpp == pytest.approx(
        vpp, abs=0.1
    )  # Lower tolerance, seemed to measure cosistently higher than it should


@pytest.mark.drivertest
def test_measure_vrms_dc_cycle(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 10e3
    vrms = 0.5
    offset = 0.232
    funcgen_sin(funcgen, vrms, frequency, offset, "vrms")

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vrms_cycle = dso.measure.vrms.dc.cycle.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vrms_cycle == pytest.approx(
        (vrms**2 + offset**2) ** 0.5, abs=0.05
    )


@pytest.mark.drivertest
def test_measure_vrms_dc_display(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 10e3
    vrms = 0.5
    offset = 0.232
    funcgen_sin(funcgen, vrms, frequency, offset, "vrms")

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vrms_display = dso.measure.vrms.dc.display.ch1()
    dso.stop()

    assert measured_vrms_display == pytest.approx(
        (vrms**2 + offset**2) ** 0.5, abs=0.05
    )


@pytest.mark.drivertest
def test_measure_vrms_ac_cycle(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 10e3
    vrms = 1.2
    offset = 0.232  # No effect now
    funcgen_sin(funcgen, vrms, frequency, offset, "vrms")

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vrms_cycle = dso.measure.vrms.dc.cycle.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vrms_cycle == pytest.approx(vrms, abs=0.05)


@pytest.mark.drivertest
def test_measure_vrms_ac_display(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 10e3
    vrms = 1.2
    offset = 0.232  # No effect now
    funcgen_sin(funcgen, vrms, frequency, offset, "vrms")

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    measured_vrms_display = dso.measure.vrms.dc.display.ch1()
    dso.stop()
    funcgen.channel1(False)

    assert measured_vrms_display == pytest.approx(vrms, abs=0.05)


@pytest.mark.drivertest
def test_measure_xmax(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.frequency(frequency)  # 1000Hz
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.offset(offset)
    funcgen.channel1.duty(50)  # Stop data out of range
    funcgen.channel1.waveform.pulse()
    funcgen.channel1.duty(0.5)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")
    dso.time_base.scale(50e-6)  # Zoom in a bit more

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_xmax = dso.measure.xmax.ch1()
    funcgen.channel1(False)

    assert measured_xmax == pytest.approx(0.0, abs=5e-6)


@pytest.mark.drivertest
def test_measure_xmin(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.waveform.ramp()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1.5 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.falling()
    dso.time_base.scale(50e-6)  # Zoom in a bit more

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_xmin = dso.measure.xmin.ch1()
    funcgen.channel1(False)

    assert measured_xmin == pytest.approx(0.0, abs=20e-6)


@pytest.mark.drivertest
def test_measure_fall_time(dso, funcgen, rm):
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.waveform.triangle()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (0.1 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.falling()

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_fall = dso.measure.fall_time.ch1()
    funcgen.channel1(False)

    assert measured_fall == pytest.approx(390e-6, abs=30e-6)


@pytest.mark.drivertest
def test_measure_rise_time(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.waveform.triangle()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (0.1 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.rising()

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_fall = dso.measure.rise_time.ch1()
    funcgen.channel1(False)

    assert measured_fall == pytest.approx(390e-6, abs=10e-6)


@pytest.mark.drivertest
def test_measure_counter(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.duty(50)  # Stop data out of range
    funcgen.channel1.waveform.square()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)
    funcgen.channel1.duty(50)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.rising()

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_counter = dso.measure.counter.ch1()
    funcgen.channel1(False)

    assert measured_counter == pytest.approx(frequency, abs=10)


@pytest.mark.drivertest
def test_measure_duty(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    duty = 12.5
    funcgen.channel1.duty(50)  # Stop data out of range
    funcgen.channel1.waveform.square()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)
    funcgen.channel1.duty(duty)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.rising()

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_counter = dso.measure.duty.ch1()
    funcgen.channel1(False)

    assert measured_counter == pytest.approx(12.5, abs=0.5)


@pytest.mark.drivertest
def test_measure_pulse_width(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1000
    vrms = 0.3
    offset = 0.0
    duty = 50
    funcgen.channel1.duty(50)  # Stop data out of range
    funcgen.channel1.waveform.square()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)
    funcgen.channel1.duty(duty)

    ## DSO setup ##
    dso_setup_ch(dso, (2 * 1.414 * vrms) / 4, (1 / frequency), offset, "ch1")
    dso.trigger.mode.edge.slope.rising()

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_counter = dso.measure.pulse_width.ch1()
    funcgen.channel1(False)

    assert measured_counter == pytest.approx((1 / frequency) * 0.01 * duty, abs=10e-6)


@pytest.mark.drivertest
@pytest.mark.xfail()
def test_measure_vratio(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH12")

    ## Funcgen setup ##
    frequency = 500
    vrms = 0.2
    funcgen.channel1.waveform.sin()
    funcgen.channel1.vpp(vrms)
    funcgen.channel1.frequency(frequency)

    ## DSO setup ##
    dso.ch1.probe.attenuation(1)
    dso.ch2.probe.attenuation(1)
    dso.ch1.scale(1)  # Vertical scale
    dso.ch2.scale(1)  # Vertical scale
    dso.ch1.offset(0)
    dso.ch2.offset(0)
    dso.ch1(True)
    dso.ch2(True)
    dso.trigger.coupling.dc()
    dso.trigger.mode.edge.source.ch1()
    dso.trigger.mode.edge.slope.either()
    dso.ch1.scale(vrms / 4)  # Set range based on the voltage
    dso.time_base.scale((1 / frequency))  # Set range based on the frequency
    dso.time_base.position(0)
    dso.source1.ch1()
    dso.source2.ch2()

    ## Measure ##
    funcgen.channel1(True)
    dso.run()
    ratio = dso.measure.vratio.cycle()
    dso.stop()
    funcgen.channel1(False)

    assert ratio == pytest.approx(0.5, abs=0.1)  # Tolerance and ratio need adjusting


@pytest.mark.drivertest
@pytest.mark.xfail()
def test_measure_cnt_edge_rising(dso, funcgen, rm):
    funcgen.reset()
    dso.reset()
    rm.mux.connectionMap("SIG_DSO_CH1_1")

    ## Funcgen setup ##
    frequency = 1234
    vrms = 0.3
    offset = 0.0
    funcgen.channel1.waveform.square()
    funcgen.channel1.vrms(vrms)
    funcgen.channel1.frequency(frequency)
    funcgen.channel1.offset(offset)
    funcgen.channel1.duty(50)

    ## DSO setup ##
    dso.ch1.probe.attenuation(1)
    dso.ch1.scale(1)  # Vertical scale
    dso.ch1(True)
    dso.ch2(False)
    dso.trigger.coupling.dc()
    dso.trigger.mode.edge.source.ch1()
    dso.trigger.mode.edge.slope.rising()
    dso.trigger.mode.edge.level(offset)
    dso.ch1.scale((2 * 1.414 * vrms) / 4)  # Set range based on the voltage
    dso.ch1.offset(offset)
    dso.time_base.scale(1 / frequency)  # Set range based on the frequency
    dso.time_base.position(0)

    ## Measure ##
    funcgen.channel1(True)
    dso.single()
    measured_edge = dso.measure.cnt_edge_rising.ch1()
    funcgen.channel1(False)

    assert measured_edge == pytest.approx(10, abs=0.1)
