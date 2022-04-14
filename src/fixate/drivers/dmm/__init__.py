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
from fixate.config import find_instrument_by_id


def open() -> DMM:
    instrument = find_instrument_by_id(Fluke8846A.REGEX_ID)
    if instrument is not None:
        # we've found a connected instrument so open and return it
        rm = pyvisa.ResourceManager()
        # open_resource could raise visa.VisaIOError?
        driver = Fluke8846A(rm.open_resource(instrument.address))
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise fixate.drivers.InstrumentNotFoundError
