import unittest
from fixate.drivers.funcgen.rigol_dg1022 import RigolDG1022
from fixate.core.discover import discover_visa, filter_connected
from fixate.core.exceptions import *


def get_funcgen():
    instruments = discover_visa()
    connected = filter_connected(instruments, [("RigolDG1022", RigolDG1022)])
    if not connected:
        raise Exception("Cannot find valid function generator")
    return connected["RigolDG1022"]


class BaseSetup:
    def setUp(self):
        self.testcls = get_funcgen()
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
        self.assertIn("SIN", self.testcls.instrument.query("FUNC?"))

    def test_square(self):
        self.testcls.channel1.waveform.square()
        self.assertIn("SQU", self.testcls.instrument.query("FUNC?"))

    def test_ramp(self):
        self.testcls.channel1.waveform.ramp()
        self.assertIn("RAMP", self.testcls.instrument.query("FUNC?"))

    def test_pulse(self):
        self.testcls.channel1.waveform.pulse()
        self.assertIn("PULS", self.testcls.instrument.query("FUNC?"))

    def test_arb(self):
        self.testcls.channel1.waveform.arb()
        self.assertIn("ARB", self.testcls.instrument.query("FUNC?"))

    def test_noise(self):
        self.testcls.channel1.waveform.noise()
        self.assertIn("NOIS", self.testcls.instrument.query("FUNC?"))


@unittest.skip("Requires instrument connected to run")
class ChannelConfig(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_vrms(self):
        self.testcls.channel1.vrms(2)
        # # Units
        self.assertIn("VRMS", self.testcls.instrument.query("VOLT:UNIT?"))

        # # Nominal Level
        self.assertAlmostEqual(2, float(self.testcls.instrument.query("VOLT?")))

        # # Upper Limits
        self.testcls.channel1.vrms(7.072)
        self.assertAlmostEqual(7.072, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vrms(4)
        self.assertAlmostEqual(4, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vrms(8)
        self.assertAlmostEqual(7.072136, float(self.testcls.instrument.query("VOLT?")))

        # # Lower Limits
        self.testcls.channel1.vrms(0.001414227)
        self.assertAlmostEqual(0.001414227, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vrms(0.0013)
        self.assertAlmostEqual(0.001414227, float(self.testcls.instrument.query("VOLT?")))

    def test_vpp(self):
        self.testcls.channel1.vpp(2.1)
        self.assertIn("VPP", self.testcls.instrument.query("VOLT:UNIT?"))
        self.assertAlmostEqual(2.1, float(self.testcls.instrument.query("VOLT?")))
        # # Units
        self.assertIn("VPP", self.testcls.instrument.query("VOLT:UNIT?"))

        # Nominal Level
        self.testcls.channel1.vpp(2.1)
        self.assertAlmostEqual(2.1, float(self.testcls.instrument.query("VOLT?")))

        # Upper Limits
        self.testcls.channel1.vpp(20)
        self.assertAlmostEqual(20, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vpp(4)
        self.assertAlmostEqual(4, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vpp(21)
        self.assertAlmostEqual(20, float(self.testcls.instrument.query("VOLT?")))

        # Lower Limits
        self.testcls.channel1.vpp(4e-3)
        self.assertAlmostEqual(4e-3, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vpp(5e-3)
        self.assertAlmostEqual(5e-3, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.vpp(1e-3)
        self.assertAlmostEqual(4e-3, float(self.testcls.instrument.query("VOLT?")))

    def test_dbm(self):
        """
        VDBM requires to set a finite load before
        setting the voltage value in dbm

        :return:
        """

        # self.testcls.channel1.waveform.square()
        # self.assertIn("SQU", self.testcls.instrument.query("FUNC?"))

        self.testcls.channel1.load(50)
        self.assertAlmostEqual(50, float(self.testcls.instrument.query("OUTP:LOAD?")))

        # Nominal Level
        self.testcls.channel1.dbm(2.1)
        self.assertIn("DBM", self.testcls.instrument.query("VOLT:UNIT?"))

        #
        # # Upper Limits
        self.testcls.channel1.dbm(23)
        self.assertAlmostEqual(23, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.dbm(20)
        self.assertAlmostEqual(20, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.dbm(25)
        self.assertAlmostEqual(23.98071, float(self.testcls.instrument.query("VOLT?")))

        # Lower Limits
        self.testcls.channel1.dbm(-49)
        self.assertAlmostEqual(-49, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.dbm(-35)
        self.assertAlmostEqual(-35, float(self.testcls.instrument.query("VOLT?")))
        self.testcls.channel1.dbm(-60)
        self.assertAlmostEqual(-49.99869, float(self.testcls.instrument.query("VOLT?")))

    def test_frequency(self):
        self.testcls.channel1.frequency(5000)

        # Nominal Level
        self.assertAlmostEqual(5000, float(self.testcls.instrument.query("FREQ?")))
        #
        # # Upper Limits
        self.testcls.channel1.frequency(20e6)
        self.assertAlmostEqual(20e6, float(self.testcls.instrument.query("FREQ?")))
        # self.assertRaisesRegex(InstrumentError, "value clipped to upper limit", self.testcls.channel1.frequency, 30e6)
        #
        # # Lower Limits
        self.testcls.channel1.frequency(0.000001)
        self.assertAlmostEqual(0.000001, float(self.testcls.instrument.query("FREQ?")))
        # self.assertRaisesRegex(InstrumentError, "value clipped to lower limit", self.testcls.channel1.frequency, 1e-7)

    def test_phase(self):
        self.testcls.channel1.phase(60)

        # Nominal Level
        self.assertAlmostEqual(60, float(self.testcls.instrument.query("PHAS?")))

        # # Upper Limits
        self.testcls.channel1.phase(180)
        self.assertAlmostEqual(180, float(self.testcls.instrument.query("PHAS?")))
        self.testcls.channel1.phase(25)
        self.assertAlmostEqual(25, float(self.testcls.instrument.query("PHAS?")))
        self.testcls.channel1.phase(184)
        self.assertAlmostEqual(180, float(self.testcls.instrument.query("PHAS?")))

        # # Lower Limits
        self.testcls.channel1.phase(-180)
        self.assertAlmostEqual(-180, float(self.testcls.instrument.query("PHAS?")))
        self.testcls.channel1.phase(-25)
        self.assertAlmostEqual(-25, float(self.testcls.instrument.query("PHAS?")))
        self.testcls.channel1.phase(-184)
        self.assertAlmostEqual(-180, float(self.testcls.instrument.query("PHAS?")))

    def test_offset(self):
        """
        set the waveform first and then the offset value.
        For Rigol, Square Waveform is used because DC waveform
        not available  in Rigol.

        :return:
        """
        self.testcls.channel1.waveform.square()
        self.assertIn("SQU", self.testcls.instrument.query("FUNC?"))  # For Rigol

        self.testcls.channel1.vpp(200e-3)
        self.assertIn("VPP", self.testcls.instrument.query("VOLT:UNIT?"))
        self.assertAlmostEqual(200e-3, float(self.testcls.instrument.query("VOLT?")))

        self.testcls.channel1.offset(100e-3)
        self.assertAlmostEqual(100e-3, float(self.testcls.instrument.query("VOLT:OFFS?")))

        # Upper Limits
        self.testcls.channel1.offset(9.9)
        self.assertAlmostEqual(9.9, float(self.testcls.instrument.query("VOLT:OFFS?")))
        self.testcls.channel1.offset(4)
        self.assertAlmostEqual(4, float(self.testcls.instrument.query("VOLT:OFFS?")))
        self.testcls.channel1.offset(9.91)
        self.assertAlmostEqual(9.9, float(self.testcls.instrument.query("VOLT:OFFS?")))  # Clipped to 9.9
        #
        # # Lower Limits
        self.testcls.channel1.offset(-9.9)
        self.assertAlmostEqual(-9.9, float(self.testcls.instrument.query("VOLT:OFFS?")))
        self.testcls.channel1.offset(-4)
        self.assertAlmostEqual(-4, float(self.testcls.instrument.query("VOLT:OFFS?")))
        self.testcls.channel1.offset(-9.91)
        self.assertAlmostEqual(-9.9, float(self.testcls.instrument.query("VOLT:OFFS?")))

    def test_duty(self):
        # Check Ordering
        """
        Set waveform to square or pulse only
         before the duty cycle is set

        :return:
        """

        self.testcls.channel1.waveform.square()
        self.assertIn("SQU", self.testcls.instrument.query("FUNC?"))
        self.testcls.channel1.duty(40)
        self.assertAlmostEqual(40, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))

        self.testcls.channel1.waveform.pulse()
        self.assertAlmostEqual(40, float(self.testcls.instrument.query("PULS:DCYC?")))
        self.assertIn("PULS", self.testcls.instrument.query("FUNC?"))
        self.testcls.channel1.duty(60)
        self.assertAlmostEqual(60, float(self.testcls.instrument.query("PULS:DCYC?")))
        self.assertIn("PULS", self.testcls.instrument.query("FUNC?"))
        self.testcls.channel1.waveform.square()
        self.assertAlmostEqual(60, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))

        # Upper Limits
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.duty(80)
        self.assertAlmostEqual(80, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))
        self.testcls.channel1.duty(25)
        self.assertAlmostEqual(25, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))
        self.testcls.channel1.duty(84)
        self.assertAlmostEqual(80, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))

        # # Lower Limits
        self.testcls.channel1.waveform.square()
        self.testcls.channel1.duty(20)
        self.assertAlmostEqual(20, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))
        self.testcls.channel1.duty(30)
        self.assertAlmostEqual(30, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))
        self.testcls.channel1.duty(14)
        self.assertAlmostEqual(20, float(self.testcls.instrument.query("FUNC:SQU:DCYC?")))


@unittest.skip("Requires instrument connected to run")
class Burst(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_burst_state(self):
        self.testcls.channel1.burst("ON")
        self.assertIn("ON", self.testcls.instrument.query("BURS:STAT?"))

    def test_gated(self):
        self.testcls.channel1.burst.gated()
        self.assertIn("GAT", self.testcls.instrument.query("BURS:MODE?"))

    def test_ncycle(self):
        self.testcls.channel1.burst.ncycle()
        self.assertIn("TRIG", self.testcls.instrument.query("BURS:MODE?"))

    def test_ncycle_cycles(self):
        self.testcls.channel1.burst.ncycle.cycles(3)
        self.assertAlmostEqual(3, float(self.testcls.instrument.query("BURS:NCYC?")))

    def test_cycles_infinite(self):
        self.testcls.channel1.burst.ncycle.cycles.infinite()
        self.assertIn("Infinite", self.testcls.instrument.query("BURS:NCYC?"))

    def test_period(self):
        self.testcls.channel1.burst.ncycle.burst_period(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("BURS:INT:PER?")))

    def test_gated_positive(self):
        self.testcls.channel1.burst.gated.positive()
        self.assertIn("NORM", self.testcls.instrument.query("BURS:GATE:POL?"))

    def test_gated_negative(self):
        self.testcls.channel1.burst.gated.negative()
        self.assertIn("INV", self.testcls.instrument.query("BURS:GATE:POL?"))

    def test_phase(self):
        self.testcls.channel1.burst.phase(30)
        self.assertAlmostEqual(30, float(self.testcls.instrument.query("BURS:PHAS?")))


@unittest.skip("Requires instrument connected to run")
class Modulate_Options(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_am_depth(self):
        self.testcls.channel1.modulate.am.depth(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("AM:DEPT?")))

    def test_fm_freq_dev(self):
        self.testcls.channel1.modulate.fm.freq_dev(500)
        self.assertAlmostEqual(500, float(self.testcls.instrument.query("FM:DEV?")))

    def test_pm_phase_dev(self):
        self.testcls.channel1.modulate.pm.phase_dev(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("PM:DEV?")))

    def test_fsk_hop_freq(self):
        self.testcls.channel1.modulate.fsk.hop_freq(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("FSK:FREQ?")))

    def test_rate(self):
        self.testcls.channel1.modulate.fsk()
        self.assertIn("OFF", self.testcls.instrument.query("FSK:STAT?"))
        self.testcls.channel1.modulate.fsk.rate(100)
        self.assertAlmostEqual(100, float(self.testcls.instrument.query("FSK:INT:RATE?")))


@unittest.skip("Requires instrument connected to run")
class Modulate(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_am(self):
        self.testcls.channel1.modulate.am()
        self.assertIn("OFF", self.testcls.instrument.query("AM:STAT?"))

    def test_fm(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))

    def test_pm(self):
        self.testcls.channel1.modulate.pm()
        self.assertIn("OFF", self.testcls.instrument.query("PM:STAT?"))

    def test_fsk(self):
        self.testcls.channel1.modulate.fsk()
        self.assertIn("OFF", self.testcls.instrument.query("FSK:STAT?"))


@unittest.skip("Requires instrument connected to run")
class Trigger(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_immediate(self):
        """
        Enable the burst mode before switching to
        a certain trigger mode

        :return:
        """

        self.testcls.channel1.burst(True)
        self.testcls.trigger.immediate()
        self.assertIn("IMM", self.testcls.instrument.query("TRIG:SOUR?"))

    def test_external(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG:SOUR?"))

    def test_external_rising(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG:SOUR?"))
        self.testcls.trigger.external.rising()
        self.assertIn("POS", self.testcls.instrument.query("TRIG:SLOP?"))

    def test_external_falling(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.external()
        self.assertIn("EXT", self.testcls.instrument.query("TRIG:SOUR?"))
        self.testcls.trigger.external.falling()
        self.assertIn("NEG", self.testcls.instrument.query("TRIG:SLOP?"))

    def test_manual(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.manual()
        self.assertIn("BUS", self.testcls.instrument.query("TRIG:SOUR?"))

    def test_delay(self):
        self.testcls.trigger.delay(1e-3)
        self.assertAlmostEqual(1e-3, float(self.testcls.instrument.query("TRIG:DEL?")))

    def test_out_off(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.manual()
        self.assertIn("BUS", self.testcls.instrument.query("TRIG:SOUR?"))
        self.testcls.trigger.out.off()
        self.assertIn("OFF", self.testcls.instrument.query("OUTP:TRIG?"))

    def test_out_rising(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.out.rising()
        self.assertIn("POS", self.testcls.instrument.query("OUTP:TRIG:SLOP?"))

    def test_out_falling(self):
        self.testcls.channel1.burst(True)
        self.testcls.trigger.out.falling()
        self.assertIn("NEG", self.testcls.instrument.query("OUTP:TRIG:SLOP?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Source(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_internal(self):
        """
        Enable a modulate state before enabling the modulate source

        :return:
        """
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))

    def test_external(self):
        self.testcls.channel1.modulate.am()
        self.assertIn("OFF", self.testcls.instrument.query("AM:STAT?"))
        self.testcls.channel1.modulate.source.external()
        self.assertIn("EXT", self.testcls.instrument.query("AM:SOUR?"))


@unittest.skip("Requires instrument connected to run")
class Channel_Activation(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_channel1(self):
        self.testcls.channel1(True)
        self.assertIn("ON", self.testcls.instrument.query("OUTP?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Shape(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_mod_sin(self):
        """
        Enable the modulate state and source before
        setting the modulate shape

        :return:
        """

        self.testcls.channel1.modulate.am()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.sin()
        self.assertIn("SIN", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_square(self):
        self.testcls.channel1.modulate.am()
        self.assertIn("OFF", self.testcls.instrument.query("AM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("AM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.square()
        self.assertIn("SQU", self.testcls.instrument.query("AM:INT:FUNC?"))

    def test_mod_triangle(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.triangle()
        self.assertIn("TRI", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_up_ramp(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.up_ramp()
        self.assertIn("RAMP", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_down_ramp(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.down_ramp()
        self.assertIn("NRAM", self.testcls.instrument.query("FM:INT:FUNC?"))

    def test_mod_noise(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate.source.internal.shape.noise()
        self.assertIn("NOIS", self.testcls.instrument.query("FM:INT:FUNC?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Activation(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_mod_activation(self):
        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate(True)
        self.assertIn("ON", self.testcls.instrument.query("FM:STAT?"))


@unittest.skip("Requires instrument connected to run")
class Modulate_Frequency(unittest.TestCase):
    def setUp(self):
        self.testcls = get_funcgen()
        self.testcls.reset()

    def test_mod_freq(self):
        """
        Enable modulate state and source and setting a modulate shape
        before setting the frequency

        :return:
        """

        self.testcls.channel1.modulate.fm()
        self.assertIn("OFF", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal()
        self.assertIn("INT", self.testcls.instrument.query("FM:SOUR?"))
        self.testcls.channel1.modulate(True)
        self.assertIn("ON", self.testcls.instrument.query("FM:STAT?"))
        self.testcls.channel1.modulate.source.internal.shape.sin()
        self.assertIn("SIN", self.testcls.instrument.query("FM:INT:FUNC?"))
        self.testcls.channel1.modulate.source.internal.frequency(200)
        self.assertAlmostEqual(200, float(self.testcls.instrument.query("FM:INT:FREQ?")))
