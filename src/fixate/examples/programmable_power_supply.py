"""
Examples on how to use the programmable power supply driver works
"""
import time

from fixate.core.common import TestClass, TestList
from fixate.drivers import pps
from fixate.core.checks import chk_passes
from fixate.core.ui import user_info

__version__ = "1"


class ProgrammablePowerSupply(TestClass):
    """
    This sets up the function generator for use in the
    This Test class cannot be used directly as it doesn't implement 'def test(self)'
    """

    pps = None

    def set_up(self):
        """
        You can set the com port and baud rate directly or your can auto discover
        :return:
        """
        self.pps = pps.open()

    def tear_down(self):
        # Tear down methods such as turning off the output at the end if required
        pass


class BasicCommands(ProgrammablePowerSupply):
    test_desc = "Run some programmable power supply functions"

    def test(self):
        user_info(self.pps.identify(as_string=True))

        user_info(self.pps.baud_rate)
        self.pps.remote = True
        self.pps.remote = False
        self.pps.remote = True
        self.pps.voltage = 12
        self.pps.output_ch1 = True
        time.sleep(1)
        self.pps.output_ch1 = False
        self.pps.voltage = 5.5
        self.pps.output_ch1 = True
        time.sleep(1)
        self.pps.output_ch1 = False
        self.pps.voltage = 24
        self.pps.output_ch1 = True
        time.sleep(1)
        self.pps.output_ch1 = False
        self.pps.voltage_max = 56
        self.pps.current_max = 0.5
        self.pps.output_ch1 = True
        resp = self.pps.read()
        user_info(resp)
        chk_passes("All Tests completed")


TEST_SEQUENCE = TestList([BasicCommands()])
