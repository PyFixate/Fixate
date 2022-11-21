"""
dmm is the digital multimeter driver.

Use dmm.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

dmm.measure(*mode, **mode_params)
dmm.reset()
"""
import pyvisa
import fixate.drivers
from fixate.drivers.dmm.helper import DMM
from fixate.drivers.dmm.fluke_8846a import Fluke8846A
from fixate.drivers.dmm.keithley_6500 import Keithley6500
from fixate.config import find_instrument_by_id


def open() -> DMM:

    for DMM in [Fluke8846A, Keithley6500]:
        instrument = find_instrument_by_id(DMM.REGEX_ID)
        if instrument is not None:
            # Attempt to open instrument in config file
            rm = pyvisa.ResourceManager()
            try:
                driver = DMM(rm.open_resource(instrument.address))
                fixate.drivers.log_instrument_open(driver)
                return driver
            except pyvisa.errors.VisaIOError:
                # Tried to open a DMM that is in the config, but not physically connected.
                pass
    raise fixate.drivers.InstrumentNotFoundError
