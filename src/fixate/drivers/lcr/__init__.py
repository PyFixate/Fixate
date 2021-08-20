"""
lcr is the lcr meter driver.

Use lcr.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

"""
from fixate.drivers.lcr.helper import LCR, TestResult
import pyvisa
import fixate.drivers
from fixate.drivers.lcr.agilent_u1732c import AgilentU1732C
from fixate.config import find_instrument_by_id


def open() -> LCR:
    instrument = find_instrument_by_id(AgilentU1732C.REGEX_ID)
    if instrument is not None:
        # we've found a connected instrument so open and return it
        rm = pyvisa.ResourceManager()
        # open_resource could raise visa.VisaIOError?
        driver = AgilentU1732C(rm.open_resource(instrument.address))
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise fixate.drivers.InstrumentNotFoundError
