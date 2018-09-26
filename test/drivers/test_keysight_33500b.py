import unittest
from fixate.drivers.funcgen.keysight_33500b import Keysight33500B
from fixate.core.discover import discover_visa, filter_connected
from fixate.core.exceptions import *


def get_funcgen():
    instruments = discover_visa()
    connected = filter_connected(instruments, [("Keysight33500B", Keysight33500B)])
    if not connected:
        raise Exception("Cannot find valid function generator")
    return connected["Keysight33500B"]


class BaseSetup:
    def setUp(self):
        import visa
        rm = visa.ResourceManager()
        resource = rm.open_resource("USB0::2391::9991::MY52303676::0::INSTR")
        self.testcls = Keysight33500B(instrument=resource)
        self.testcls.reset()

    def tearDown(self):
        self.testcls.reset()


@unittest.skip("Requires instrument connected to run")
class Waveforms(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_sin(self):
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.waveform.sin()
        self.assertIn("SIN", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_square(self):
        self.testcls.channel1.waveform.square()
        self.assertIn("SQU", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_ramp(self):
        self.testcls.channel1.waveform.ramp()
        self.assertIn("RAMP", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_pulse(self):
        self.testcls.channel1.waveform.pulse()
        self.assertIn("PULS", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_arb(self):
        self.testcls.channel1.waveform.arb()
        self.assertIn("ARB", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_triangle(self):
        self.testcls.channel1.waveform.triangle()
        self.assertIn("TRI", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_noise(self):
        self.testcls.channel1.waveform.noise()
        self.assertIn("NOIS", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_dc(self):
        self.testcls.channel1.waveform.dc()
        self.assertIn("DC", self.testcls.instrument.query("SOUR1:FUNC?"))

    def test_prbs(self):
        self.testcls.channel1.waveform.prbs()
        self.assertIn("PRBS", self.testcls.instrument.query("SOUR1:FUNC?"))


@unittest.skip("Requires instrument connected to run")
class ChannelConfig(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_vrms(self):
        self.testcls.channel1.load(50)
        self.testcls.channel1.vrms(2)
        # Units
        self.assertIn("VRMS", self.testcls.instrument.query("SOUR1:VOLT:UNIT?"))

        # Nominal Level
        self.assertAlmostEqual(2.0, float(self.testcls.instrument.query("SOUR1:VOLT?")))

        # Upper Limits
        self.testcls.channel1.vrms(3.5)
        self.assertAlmostEqual(3.5, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.vrms, 3.6)

        # Lower Limits
        self.testcls.channel1.vrms(354e-6)
        self.assertAlmostEqual(354e-6, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.vrms, 353e-6)

    def test_vpp(self):
        # Units
        self.assertIn("VPP", self.testcls.instrument.query("SOUR1:VOLT:UNIT?"))
        self.testcls.channel1.load(50)
        # Nominal Level
        self.testcls.channel1.vpp(2.1)
        self.assertAlmostEqual(2.1, float(self.testcls.instrument.query("SOUR1:VOLT?")))

        # Upper Limits
        self.testcls.channel1.vpp(10)
        self.assertAlmostEqual(10, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.vpp, 11)

        # Lower Limits
        self.testcls.channel1.vpp(0.001)
        self.assertAlmostEqual(0.001, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.vpp, 0.0001)

    def test_dbm(self):
        self.testcls.channel1.waveform.sin()
        self.assertIn("SIN", self.testcls.instrument.query("SOUR1:FUNC?"))
        self.testcls.channel1.load(50)
        # Nominal Level
        self.testcls.channel1.dbm(2)

        # Units
        self.assertIn("DBM", self.testcls.instrument.query("SOUR1:VOLT:UNIT?"))
        self.assertAlmostEqual(2.0, float(self.testcls.instrument.query("SOUR1:VOLT?")))

        # Upper Limits
        self.testcls.channel1.dbm(23.97)
        self.assertAlmostEqual(23.97, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.dbm, 23.98)

        # Lower Limits
        self.testcls.channel1.dbm(-56)
        self.assertAlmostEqual(-56, float(self.testcls.instrument.query("SOUR1:VOLT?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.dbm, -60)

    def test_frequency(self):
        self.testcls.channel1.frequency(5000)

        # Nominal Level
        self.assertAlmostEqual(5000, float(self.testcls.instrument.query("SOUR1:FREQ?")))

        # Upper Limits
        self.testcls.channel1.frequency(20e6)
        self.assertAlmostEqual(20e6, float(self.testcls.instrument.query("SOUR1:FREQ?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.frequency, 30e6)

        # Lower Limits
        self.testcls.channel1.frequency(0.000001)
        self.assertAlmostEqual(0.000001, float(self.testcls.instrument.query("SOUR1:FREQ?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.frequency, 1e-7)

    def test_phase(self):
        self.testcls.channel1.phase(30)

        # Nominal Level
        self.assertAlmostEqual(30, float(self.testcls.instrument.query("SOUR1:PHAS?")))

        # Upper Limits
        self.testcls.channel1.phase(360)
        self.assertAlmostEqual(360, float(self.testcls.instrument.query("SOUR1:PHAS?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.phase, 362)

        # Lower Limits
        self.testcls.channel1.phase(-360)
        self.assertAlmostEqual(-360, float(self.testcls.instrument.query("SOUR1:PHAS?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.phase, -363)

    def test_offset(self):
        self.testcls.channel1.waveform.dc()
        self.testcls.channel1.load(50)
        self.assertIn("DC", self.testcls.instrument.query("SOUR1:FUNC?"))
        # self.testcls.channel1.waveform.square()
        # self.assertIn("SQU", self.testcls.instrument.query("SOUR1:FUNC?"))          #For Rigol

        # self.testcls.channel1.vpp(1e-3)
        # self.assertIn("VPP", self.testcls.instrument.query("SOUR1:VOLT:UNIT?"))
        # self.assertAlmostEqual(1e-3, float(self.testcls.instrument.query("SOUR1:VOLT?")))

        self.testcls.channel1.offset(100e-3)
        self.assertAlmostEqual(100e-3, float(self.testcls.instrument.query("SOUR1:VOLT:OFFS?")))

        # Upper Limits
        self.testcls.channel1.offset(5)
        self.assertAlmostEqual(5, float(self.testcls.instrument.query("SOUR1:VOLT:OFFS?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.offset, 5.01)

        # Lower Limits
        self.testcls.channel1.offset(-5)
        self.assertAlmostEqual(-5, float(self.testcls.instrument.query("SOUR1:VOLT:OFFS?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.offset, -5.01)

    def test_duty(self):
        # Check Ordering
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.duty(40)
        self.assertAlmostEqual(40, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))

        self.assertIn("SQU", self.testcls.instrument.query("SOUR1:FUNC?"))
        self.testcls.channel1.waveform.pulse()
        self.assertAlmostEqual(40, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.assertIn("PULS", self.testcls.instrument.query("SOUR1:FUNC?"))
        self.testcls.channel1.duty(60)
        self.assertAlmostEqual(60, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.assertIn("PULS", self.testcls.instrument.query("SOUR1:FUNC?"))
        self.testcls.channel1.waveform.square()
        self.assertAlmostEqual(60, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))
        self.assertIn("SQU", self.testcls.instrument.query("SOUR1:FUNC?"))

        # Upper Limits
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.duty(99)
        self.assertAlmostEqual(99, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.duty, 100)
        self.testcls.channel1.duty(50)
        self.testcls.channel1.waveform.pulse()
        self.testcls.channel1.duty(99)
        self.assertAlmostEqual(99, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.duty, 100)

        # Lower Limits
        self.testcls.channel1.duty(50)
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.duty(1)
        self.assertAlmostEqual(1, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.duty, -1)
        self.testcls.channel1.duty(50)
        self.testcls.channel1.waveform.pulse()
        self.testcls.channel1.duty(1)
        self.assertAlmostEqual(1, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.duty, -1)
        self.testcls.channel1.duty(1)
        self.assertAlmostEqual(1, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.testcls.channel1.waveform.square()
        self.assertAlmostEqual(1, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.duty, -1)

        self.testcls.channel1.duty(0.01)
        self.assertAlmostEqual(0.01, float(self.testcls.instrument.query("SOUR1:FUNC:SQU:DCYC?")))
        self.testcls.channel1.waveform.pulse()
        self.assertAlmostEqual(0.01, float(self.testcls.instrument.query("SOUR1:FUNC:PULS:DCYC?")))
        self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.duty, -1)


@unittest.skip("Requires instrument connected to run")
class Burst(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_burst_state(self):
        self.testcls.channel1.burst("1")
        self.assertIn("1", self.testcls.instrument.query("SOUR1:BURS:STAT?"))

    def test_gated(self):
        self.testcls.channel1.burst.gated()
        self.assertIn("GAT", self.testcls.instrument.query("SOUR1:BURS:MODE?"))

    def test_ncycle(self):
        self.testcls.channel1.burst.ncycle()
        self.assertIn("TRIG", self.testcls.instrument.query("SOUR1:BURS:MODE?"))

    def test_ncycle_cycles(self):
        self.testcls.channel1.burst.ncycle.cycles(3)
        self.assertAlmostEqual(3, float(self.testcls.instrument.query("SOUR1:BURS:NCYC?")))

    def test_cycles_infinite(self):
        self.testcls.channel1.burst.ncycle.cycles.infinite()
        self.assertAlmostEqual(9.9e37, float(self.testcls.instrument.query("SOUR1:BURS:NCYC?")))

    def test_period(self):
        self.testcls.channel1.burst.ncycle.burst_period(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("SOUR1:BURS:INT:PER?")))

    def test_gated_positive(self):
        self.testcls.channel1.burst.gated.positive()
        self.assertIn("NORM", self.testcls.instrument.query("SOUR1:BURS:GATE:POL?"))

    def test_gated_negative(self):
        self.testcls.channel1.burst.gated.negative()
        self.assertIn("INV", self.testcls.instrument.query("SOUR1:BURS:GATE:POL?"))

    def test_phase(self):
        self.testcls.channel1.burst.phase(30)
        self.assertAlmostEqual(30, float(self.testcls.instrument.query("SOUR1:BURS:PHAS?")))


@unittest.skip("Requires instrument connected to run")
class Modulate_Options(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_am_depth(self):
        self.testcls.channel1.modulate.am.depth(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("SOUR1:AM:DEPT?")))

    def test_am_dssc(self):
        self.testcls.channel1.modulate.am.dssc()
        self.assertIn("1", self.testcls.instrument.query("SOUR1:AM:DSSC?"))

    def test_fm_freq_dev(self):
        self.testcls.channel1.modulate.fm.freq_dev(100e3)
        self.assertAlmostEqual(100e3, float(self.testcls.instrument.query("SOUR1:FM:DEV?")))

    def test_pm_phase_dev(self):
        self.testcls.channel1.modulate.pm.phase_dev(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("SOUR1:PM:DEV?")))

    def test_fsk_hop_freq(self):
        self.testcls.channel1.modulate.fsk.hop_freq(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("SOUR1:FSK:FREQ?")))

    def test_rate(self):
        self.testcls.channel1.modulate.fsk.rate(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("SOUR1:FSK:INT:RATE?")))

    def test_modulate_percent(self):
        self.testcls.channel1.modulate.sum()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:SUM:STAT?"))
        self.testcls.channel1.modulate.sum.modulate_percent(50)
        self.assertAlmostEqual(50, float(self.testcls.instrument.query("SOUR1:SUM:AMPL?")))


@unittest.skip("Requires instrument connected to run")
class Modulate(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_am(self):
        self.testcls.channel1.modulate.am()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:AM:STAT?"))

    def test_fm(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))

    def test_pm(self):
        self.testcls.channel1.modulate.pm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:PM:STAT?"))

    def test_fsk(self):
        self.testcls.channel1.modulate.fsk()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FSK:STAT?"))

    def test_bpsk(self):
        self.testcls.channel1.modulate.bpsk()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:BPSK:STAT?"))

    def test_sum(self):
        self.testcls.channel1.modulate.sum()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:SUM:STAT?"))


@unittest.skip("Requires instrument connected to run")
class Trigger(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_immediate(self):
        self.testcls.trigger.immediate()
        self.assertIn("IMM", self.testcls.instrument.query("TRIG1:SOUR?"))

    def test_external(self):
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG1:SOUR?"))

    def test_external_rising(self):
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG1:SOUR?"))
        self.testcls.trigger.external.rising()
        self.assertIn("POS", self.testcls.instrument.query("TRIG1:SLOP?"))

    def test_external_falling(self):
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG1:SOUR?"))
        self.testcls.trigger.external.falling()
        self.assertIn("NEG", self.testcls.instrument.query("TRIG1:SLOP?"))

    def test_manual(self):
        self.testcls.trigger.manual()
        self.assertIn("BUS", self.testcls.instrument.query("TRIG1:SOUR?"))

    def test_initiate(self):
        self.testcls.trigger.manual.initiate()
        self.assertIn("BUS", self.testcls.instrument.query("TRIG1:SOUR?"))

    def test_timer(self):
        self.testcls.trigger.timer(10)
        self.assertIn("TIM", self.testcls.instrument.query("TRIG1:SOUR?"))
        self.assertAlmostEqual(10, float(self.testcls.instrument.query("TRIG1:TIM?")))

    def test_delay(self):
        self.testcls.trigger.delay(10)
        self.assertAlmostEqual(10, float(self.testcls.instrument.query("TRIG1:DEL?")))

    def test_out_off(self):
        self.testcls.trigger.out.off()
        self.assertIn("0", self.testcls.instrument.query("OUTP:TRIG?"))

    def test_out_rising(self):
        self.testcls.trigger.out.rising()
        self.assertIn("POS", self.testcls.instrument.query("OUTP:TRIG:SLOP?"))

    def test_out_falling(self):
        self.testcls.trigger.out.falling()
        self.assertIn("NEG", self.testcls.instrument.query("OUTP:TRIG:SLOP?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Source(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_internal(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("SOUR1:FM:SOUR?"))

    def test_external(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.external()
        self.assertIn("EXT", self.testcls.instrument.query("SOUR1:FM:SOUR?"))


@unittest.skip("Requires instrument connected to run")
class Channel_Activation(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_channel1(self):
        self.testcls.channel1(True)
        self.assertIn("1", self.testcls.instrument.query("OUTP1?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Shape(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_mod_sin(self):
        self.testcls.channel1.modulate.fm()
        self.testcls.channel1.modulate(True)
        self.assertIn("1", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.sin()
        self.assertIn("SIN", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_square(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.square()
        self.assertIn("SQU", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_triangle(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.triangle()
        self.assertIn("TRI", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_up_ramp(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.up_ramp()
        self.assertIn("RAMP", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_down_ramp(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.down_ramp()
        self.assertIn("NRAM", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_noise(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.noise()
        self.assertIn("NOIS", self.testcls.instrument.query("FM:INT:FUNC?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Activation(unittest.TestCase):
    def setUp(self):
        import visa
        rm = visa.ResourceManager()
        resource = rm.open_resource("USB0::2391::9991::MY52303676::0::INSTR")
        self.testcls = Keysight33500B(instrument=resource)
        self.testcls.reset()

    def test_mod_activation(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("0", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("SOUR1:FM:SOUR?"))
        self.testcls.channel1.modulate(True)
        self.assertIn("1", self.testcls.instrument.query("SOUR1:FM:STAT?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Frequency(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_mod_freq(self):
        self.testcls.channel1.modulate.fm()
        self.testcls.channel1.modulate(True)
        self.assertIn("1", self.testcls.instrument.query("SOUR1:FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.sin()
        self.assertIn("SIN", self.testcls.instrument.query("SOUR1:FM:INT:FUNC?"))
        # self.testcls.channel1.modulate.source.internal.shape.square()
        self.testcls.channel1.modulate.source.internal.frequency(100e3)
        self.assertAlmostEqual(100e3, float(self.testcls.instrument.query("SOUR1:FM:INT:FREQ?")))
