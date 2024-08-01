"""
Examples on how to use the function generator driver
"""
import time

from fixate.core.common import TestClass, TestList
from fixate.drivers import funcgen
from fixate.core.checks import chk_passes

__version__ = "1"


class FunctionGenerator(TestClass):
    """
    This sets up the function generator for use in the
    This Test class cannot be used directly as it doesn't implement 'def test(self)'
    """

    funcgen = None

    def set_up(self):
        self.funcgen = funcgen.open()

    def tear_down(self):
        # Enables local control for the function generator
        if self.funcgen:
            self.funcgen.local()
            self.funcgen.output_ch1 = False
            self.funcgen.output_ch2 = False
            self.funcgen.output_sync = False


class BasicWaves(FunctionGenerator):
    test_desc = "Generate a series of waves"

    def test(self):
        # Generate 1000Hz wave sin on ch1
        self.funcgen.function("sin", amplitude=5.0, frequency=1000, offset=0)
        time.sleep(1)
        # Enable output
        self.funcgen.output_ch1 = True
        # Generate 1000Hz square wave on ch1
        # Remembers the previous amplitude, frequency and offset
        self.funcgen.function("squ")
        time.sleep(1)
        # Set the duty cycle to 30
        self.funcgen.function("squ", duty_cycle=30)
        time.sleep(5)
        # Generate 5MHz sin wave on ch1
        self.funcgen.function("sin", frequency="5MHz", amplitude="2Vpp", offset=-0.1)

        time.sleep(1)
        self.funcgen.function("sin", frequency="5MHz", amplitude="2Vpp", offset="10mV")
        # Enables the front panel for the user
        self.funcgen.local()
        time.sleep(5)

        # Takes back the front panel for the software on first call
        # Generate 1kHz ramp wave on ch2
        self.funcgen.function("ramp", channel=2, frequency="1kHz", amplitude="6Vpp")
        self.funcgen.output_ch2 = True

        # Generate pulse function
        self.funcgen.function(
            "pulse", frequency="1kHz", duty_cycle=20, amplitude="5Vpp"
        )
        time.sleep(1)

        # Enable sync output for channel 1 at a phase of 90o
        self.funcgen.function("sin", amplitude=5.0, frequency=1000, offset=0, phase=90)
        self.funcgen.output_sync = True
        time.sleep(1)
        self.funcgen.output_ch1 = False
        time.sleep(1)
        self.funcgen.output_ch1 = True
        time.sleep(1)
        self.funcgen.output_ch1 = False
        time.sleep(1)
        self.funcgen.output_ch1 = True

        chk_passes()


TEST_SEQUENCE = TestList([BasicWaves()])
