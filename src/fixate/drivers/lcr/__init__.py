"""
lcr is the lcr meter driver.

Use lcr.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

"""
import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.lcr.agilent_u1732c import AgilentU1732C
from fixate.drivers.lcr.helper import LCR


def open() -> LCR:
    instrument = find_instrument_by_id(AgilentU1732C.REGEX_ID)
    if instrument is not None:
        # we've found a connected instrument so open and return it
        rm = pyvisa.ResourceManager()
        try:
            resource = rm.open_resource(instrument.address)
        except pyvisa.VisaIOError as e:
            raise InstrumentOpenError(
                f"Unable to open LCR: {instrument.address}"
            ) from e
        driver = AgilentU1732C(resource)
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise InstrumentNotFoundError
