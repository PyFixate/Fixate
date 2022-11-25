import pytest
import re
from fixate.core.exceptions import *
from fixate.config import load_config

load_config()  # Load fixate config file


@pytest.mark.drivertest
def test_open_funcgen():
    import fixate.drivers.funcgen

    funcgen = fixate.drivers.funcgen.open()
    assert funcgen, "Could not open function generator"


@pytest.mark.drivertest
def test_sin(funcgen):
    funcgen.channel1.waveform.sin()
    assert "SIN\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_square(funcgen):
    funcgen.channel1.waveform.square()
    assert "SQU\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_ramp(funcgen):
    funcgen.channel1.waveform.ramp()
    assert "RAMP\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_pulse(funcgen):
    funcgen.channel1.waveform.pulse()
    assert "PULS\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_arb(funcgen):
    funcgen.channel1.waveform.arb()
    assert "ARB\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_triangle(funcgen):
    funcgen.channel1.waveform.triangle()
    assert "TRI\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_noise(funcgen):
    # Noise function has a small VRMS limit. Set this to not error
    funcgen.channel1.vrms(0.2)
    funcgen.channel1.waveform.noise()
    assert "NOIS\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_dc(funcgen):
    funcgen.channel1.waveform.dc()
    assert "DC\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_prbs(funcgen):
    funcgen.channel1.waveform.prbs()
    assert "PRBS\n" == funcgen.instrument.query("SOUR1:FUNC?")


@pytest.mark.drivertest
def test_vrms_units(funcgen):
    funcgen.channel1.vrms(2)
    assert "VRMS\n" == funcgen.instrument.query("SOUR1:VOLT:UNIT?")


@pytest.mark.drivertest
def test_vrms(funcgen):
    funcgen.channel1.vrms(2)
    assert float(funcgen.instrument.query("SOUR1:VOLT?")) == pytest.approx(2.0)


@pytest.mark.parametrize("v", [3.6, 353e-6])
@pytest.mark.drivertest
def test_vrms_over_range(v, funcgen):
    funcgen.channel1.load(50)
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.vrms(v)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_vpp_units(funcgen):
    funcgen.channel1.vpp(1)
    assert "VPP\n" == funcgen.instrument.query("SOUR1:VOLT:UNIT?")


@pytest.mark.drivertest
def test_vpp(funcgen):
    # Nominal Level
    funcgen.channel1.vpp(2.1)
    assert float(funcgen.instrument.query("SOUR1:VOLT?")) == pytest.approx(2.1)


@pytest.mark.parametrize("v", [21, 0.001])
@pytest.mark.drivertest
def test_vpp_over_range(v, funcgen):
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.vpp(v)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_dbm_units(funcgen):
    funcgen.channel1.waveform.sin()
    funcgen.channel1.load(50)
    funcgen.channel1.dbm(2)
    assert "DBM\n" == funcgen.instrument.query("SOUR1:VOLT:UNIT?")


@pytest.mark.drivertest
def test_dbm(funcgen):
    funcgen.channel1.load(50)
    funcgen.channel1.dbm(2.1)
    assert float(funcgen.instrument.query("SOUR1:VOLT?")) == pytest.approx(2.1)


@pytest.mark.parametrize("db", [23.98, -60])
@pytest.mark.drivertest
def test_dbm_over_range(db, funcgen):
    funcgen.channel1.load(50)
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.dbm(db)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_frequency(funcgen):
    funcgen.reset()
    funcgen.channel1.frequency(5000)

    assert float(funcgen.instrument.query("SOUR1:FREQ?")) == pytest.approx(5000)


@pytest.mark.parametrize("freq", [30e6, 1e-7])
@pytest.mark.drivertest
def test_frequency_over_range(freq, funcgen):
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.frequency(freq)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_phase(funcgen):
    funcgen.channel1.phase(30)
    assert float(funcgen.instrument.query("SOUR1:PHAS?")) == pytest.approx(30)


@pytest.mark.parametrize("phase", [362, -362])
@pytest.mark.drivertest
def test_phase_over_range(phase, funcgen):
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.phase(phase)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_offset(funcgen):
    funcgen.reset()
    funcgen.channel1.waveform.dc()
    funcgen.channel1.load(50)
    funcgen.channel1.offset(2.1)

    assert float(funcgen.instrument.query("SOUR1:VOLT:OFFS?")) == pytest.approx(2.1)


@pytest.mark.parametrize("offset", [362, -362])
@pytest.mark.drivertest
def test_offset_over_range(offset, funcgen):
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.offset(offset)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_duty_square(funcgen):
    funcgen.channel1.waveform.square()
    funcgen.channel1.duty(40)

    assert float(funcgen.instrument.query("SOUR1:FUNC:SQU:DCYC?")) == pytest.approx(40)


@pytest.mark.parametrize("duty", [101, -1])
@pytest.mark.drivertest
def test_duty_square_over_range(duty, funcgen):
    funcgen.channel1.duty(60)
    funcgen.channel1.waveform.square()
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.duty(duty)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_duty_pulse(funcgen):
    funcgen.channel1.duty(60)
    funcgen.channel1.waveform.pulse()

    assert float(funcgen.instrument.query("SOUR1:FUNC:PULS:DCYC?")) == pytest.approx(60)


@pytest.mark.parametrize("duty", [101, -1])
@pytest.mark.drivertest
def test_duty_pulse_over_range(duty, funcgen):
    funcgen.channel1.duty(60)
    funcgen.channel1.waveform.pulse()
    with pytest.raises(InstrumentError) as excinfo:
        funcgen.channel1.duty(duty)

    assert re.search("value clipped", str(excinfo.value))


@pytest.mark.drivertest
def test_burst(funcgen):
    funcgen.reset()
    funcgen.channel1.burst("1")
    assert "1\n" == funcgen.instrument.query("SOUR1:BURS:STAT?")


@pytest.mark.drivertest
def test_burst_gated(funcgen):
    funcgen.channel1.burst.gated()
    assert "GAT\n" == funcgen.instrument.query("SOUR1:BURS:MODE?")


@pytest.mark.drivertest
def test_burst_ncycle(funcgen):
    funcgen.channel1.burst.ncycle()
    assert "TRIG\n" == funcgen.instrument.query("SOUR1:BURS:MODE?")


@pytest.mark.drivertest
def test_burst_set_ncycles(funcgen):
    funcgen.channel1.burst.ncycle.cycles(3)
    assert float(funcgen.instrument.query("SOUR1:BURS:NCYC?")) == pytest.approx(3)


@pytest.mark.drivertest
def test_burst_set_ncycles_inf(funcgen):
    funcgen.channel1.burst.ncycle.cycles.infinite()
    assert float(funcgen.instrument.query("SOUR1:BURS:NCYC?")) == pytest.approx(9.9e37)


@pytest.mark.drivertest
def test_burst_period(funcgen):
    funcgen.channel1.burst.ncycle.burst_period(100)
    assert float(funcgen.instrument.query("SOUR1:BURS:INT:PER?")) == pytest.approx(100)


@pytest.mark.drivertest
def test_burst_gated_positive(funcgen):
    funcgen.channel1.burst.gated.positive()
    assert "NORM\n" == funcgen.instrument.query("SOUR1:BURS:GATE:POL?")


@pytest.mark.drivertest
def test_burst_gated_negative(funcgen):
    funcgen.channel1.burst.gated.negative()
    assert "INV\n" == funcgen.instrument.query("SOUR1:BURS:GATE:POL?")


@pytest.mark.drivertest
def test_burst_phase(funcgen):
    funcgen.channel1.burst.phase(30)
    assert float(funcgen.instrument.query("SOUR1:BURS:PHAS?")) == pytest.approx(30)


@pytest.mark.drivertest
def test_modulate_am_depth(funcgen):
    funcgen.channel1.modulate.am.depth(100)
    assert float(funcgen.instrument.query("SOUR1:AM:DEPT?")) == pytest.approx(100)


@pytest.mark.drivertest
def test_modulate_am_dssc(funcgen):

    funcgen.channel1.modulate.am.dssc()
    assert "1\n" == funcgen.instrument.query("SOUR1:AM:DSSC?")


@pytest.mark.drivertest
def test_modulate_fm_freq_dev(funcgen):

    funcgen.channel1.modulate.fm.freq_dev(100e3)
    assert float(funcgen.instrument.query("SOUR1:FM:DEV?")) == pytest.approx(100e3)


@pytest.mark.drivertest
def test_modulate_pm_phase_dev(funcgen):

    funcgen.channel1.modulate.pm.phase_dev(100)
    assert float(funcgen.instrument.query("SOUR1:PM:DEV?")) == pytest.approx(100)


@pytest.mark.drivertest
def test_modulate_fsk_hop_freq(funcgen):

    funcgen.channel1.modulate.fsk.hop_freq(100)
    assert float(funcgen.instrument.query("SOUR1:FSK:FREQ?")) == pytest.approx(100)


@pytest.mark.drivertest
def test_modulate_fsk_rate(funcgen):

    funcgen.channel1.modulate.fsk.rate(100)
    assert float(funcgen.instrument.query("SOUR1:FSK:INT:RATE?")) == pytest.approx(100)


@pytest.mark.drivertest
def test_modulate_sum(funcgen):

    funcgen.channel1.modulate.sum()
    assert "0\n" == funcgen.instrument.query("SOUR1:SUM:STAT?")


@pytest.mark.drivertest
def test_modulate_sum_percent(funcgen):
    funcgen.channel1.modulate.sum()
    funcgen.channel1.modulate.sum.modulate_percent(50)
    assert float(funcgen.instrument.query("SOUR1:SUM:AMPL?")) == pytest.approx(50)


@pytest.mark.parametrize(
    "mode, query",
    [
        ("am", "SOUR1:AM:STAT?"),
        ("fm", "SOUR1:FM:STAT?"),
        ("pm", "SOUR1:PM:STAT?"),
        ("fsk", "SOUR1:FSK:STAT?"),
        ("bpsk", "SOUR1:bpsk:STAT?"),
        ("sum", "SOUR1:SUM:STAT?"),
    ],
)
@pytest.mark.drivertest
def test_modulate(mode, query, funcgen):
    getattr(funcgen.channel1.modulate, mode)()

    assert "0\n" == funcgen.instrument.query(query)


@pytest.mark.parametrize(
    "trigger, expected",
    [
        ("immediate", "IMM"),
        ("external", "EXT"),
        ("manual", "BUS"),
    ],
)
@pytest.mark.drivertest
def test_trigger_type(trigger, expected, funcgen):

    trig = getattr(funcgen.trigger, trigger)
    trig()
    assert expected == funcgen.instrument.query("TRIG1:SOUR?").strip()


@pytest.mark.parametrize(
    "trigger, expected",
    [
        ("rising", "POS"),
        ("falling", "NEG"),
    ],
)
@pytest.mark.drivertest
def test_trigger_external(trigger, expected, funcgen):

    trig = getattr(funcgen.trigger.external, trigger)
    trig()
    assert expected == funcgen.instrument.query("TRIG1:SLOP?").strip()


@pytest.mark.drivertest
def test_trigger_manual_initiate(funcgen):

    funcgen.trigger.manual.initiate()
    assert "BUS\n" == funcgen.instrument.query("TRIG1:SOUR?")


@pytest.mark.drivertest
def test_trigger_timer_source(funcgen):
    funcgen.trigger.timer(10)
    assert "TIM\n" == funcgen.instrument.query("TRIG1:SOUR?")


@pytest.mark.drivertest
def test_trigger_timer(funcgen):
    funcgen.trigger.timer(10)
    assert float(funcgen.instrument.query("TRIG1:TIM?")) == pytest.approx(10)


@pytest.mark.drivertest
def test_trigger_delay(funcgen):
    funcgen.trigger.delay(20)
    assert float(funcgen.instrument.query("TRIG1:DEL?")) == pytest.approx(20)


@pytest.mark.parametrize("out, expected", [("rising", "POS"), ("falling", "NEG")])
@pytest.mark.drivertest
def test_trigger_out(out, expected, funcgen):
    getattr(funcgen.trigger.out, out)()
    assert expected == funcgen.instrument.query("OUTP:TRIG:SLOP?").strip()


@pytest.mark.drivertest
def test_trigger_out_off(funcgen):
    funcgen.trigger.out.off()
    assert "0\n" == funcgen.instrument.query("OUTP:TRIG?")


@pytest.mark.parametrize("source, expected", [("internal", "INT"), ("external", "EXT")])
@pytest.mark.drivertest
def test_modulate_source(source, expected, funcgen):
    funcgen.channel1.modulate.fm()
    sour = getattr(funcgen.channel1.modulate.source, source)
    sour()
    assert expected == funcgen.instrument.query("SOUR1:FM:SOUR?").strip()


@pytest.mark.drivertest
def test_channel_activation_on(funcgen):
    funcgen.channel1(True)
    assert "1\n" == funcgen.instrument.query("OUTP1?")


@pytest.mark.drivertest
def test_channel_activation_off(funcgen):
    funcgen.channel1(True)
    funcgen.channel1(False)
    assert "0\n" == funcgen.instrument.query("OUTP1?")


@pytest.mark.parametrize(
    "shape, expected",
    [
        ("sin", "SIN"),
        ("square", "SQU"),
        ("triangle", "TRI"),
        ("up_ramp", "RAMP"),
        ("down_ramp", "NRAM"),
        ("noise", "NOIS"),
    ],
)
@pytest.mark.drivertest
def test_modulate_shape(shape, expected, funcgen):
    funcgen.channel1.modulate.fm()
    mod = getattr(funcgen.channel1.modulate.source.internal.shape, shape)
    mod()
    assert expected == funcgen.instrument.query("FM:INT:FUNC?").strip()


@pytest.mark.drivertest
def test_modulate_activation_on(funcgen):
    funcgen.channel1.modulate.fm()
    funcgen.channel1.modulate.source.internal()
    funcgen.channel1.modulate(True)
    assert "1\n" == funcgen.instrument.query("SOUR1:FM:STAT?")


@pytest.mark.drivertest
def test_modulate_activation_off(funcgen):
    funcgen.channel1.modulate.fm()
    funcgen.channel1.modulate.source.internal()
    funcgen.channel1.modulate(True)
    funcgen.channel1.modulate(False)
    assert "0\n" == funcgen.instrument.query("SOUR1:FM:STAT?")


@pytest.mark.drivertest
def test_modulate_frequency(funcgen):
    funcgen.channel1.modulate.fm()
    funcgen.channel1.modulate.source.internal()
    funcgen.channel1.modulate(True)
    funcgen.channel1.modulate.source.internal.shape.sin()
    funcgen.channel1.modulate.source.internal.frequency(100e3)
    assert float(funcgen.instrument.query("SOUR1:FM:INT:FREQ?")) == pytest.approx(100e3)
