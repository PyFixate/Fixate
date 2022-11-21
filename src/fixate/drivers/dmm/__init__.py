"""
dmm is the digital multimeter driver.

Use dmm.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

dmm.measure(*mode, **mode_params)
dmm.reset()
"""
import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.dmm.fluke_8846a import Fluke8846A
from fixate.drivers.dmm.helper import DMM


def open() -> DMM:
    instrument = find_instrument_by_id(Fluke8846A.REGEX_ID)
    if instrument is not None:
        # We've found a configured instrument so try to open it
        rm = pyvisa.ResourceManager()
        try:
            resource = rm.open_resource(instrument.address)
        except pyvisa.VisaIOError as e:
            raise InstrumentOpenError(
                f"Unable to open DMM: {instrument.address}"
            ) from e
        # Instantiate driver with connected instrument
        driver = Fluke8846A(resource)
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise InstrumentNotFoundError
