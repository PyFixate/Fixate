"""
dmm is the digital multimeter driver.

Use dmm.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

dmm.measure(*mode, **mode_params)
dmm.reset()
"""
import fixate.drivers
from fixate.drivers.dmm.helper import DMM
from fixate.drivers.dmm.fluke_8846a import Fluke8846A
from fixate.drivers import find_instrument_by_id


def open() -> DMM:
    instrument = find_instrument_by_id(Fluke8846A.REGEX_ID)
    if instrument is not None:
        # we've found and connected to a visa instrument
        driver = Fluke8846A(instrument)
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise fixate.drivers.InstrumentNotFoundError
