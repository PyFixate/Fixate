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
from fixate.drivers import find_instruments_by_id, filter_connected_visa


def open() -> DMM:
    # Find all flukes in local config
    dmm_configs = find_instruments_by_id(Fluke8846A.REGEX_ID)
    # Find and open first connected instrument
    instrument = filter_connected_visa(dmm_configs)
    if instrument is not None:
        # Instantiate driver from visa connection
        driver = Fluke8846A(instrument)
        fixate.drivers.log_instrument_open(driver)
        return driver

    raise fixate.drivers.InstrumentNotFoundError
