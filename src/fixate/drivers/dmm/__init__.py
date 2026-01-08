"""
Digital multimeter driver
=========================

Use `dmm.open()` to connect to a digital multimeter.
Functions are dictated by the abstract superclass ``DMM`` in helper.py

::

    dmm.measure(*mode, **mode_params)
    dmm.reset()
"""
import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.dmm.fluke_8846a import Fluke8846A
from fixate.drivers.dmm.keithley_6500 import Keithley6500
from fixate.drivers.dmm.helper import DMM


def open() -> DMM:
    """
    Connect to a digital multimeter.

    Searches for a configured instrument and returns the first one found.

    Returns:
        DMM: open connection to the DMM
    """
    for DMM in (Fluke8846A, Keithley6500):
        instrument = find_instrument_by_id(DMM.REGEX_ID)
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
            driver = DMM(resource)
            fixate.drivers.log_instrument_open(driver)
            return driver
    raise InstrumentNotFoundError
