"""
DC ELectronic Load driver
========================= 

Use `DCLoad.open()` to connect to a DC electronic load.
Functions are dictated by the abstract superclass ``DCLoad`` in helper.py
"""

import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.dcload.rigol_dl3021 import RigolDL3021
from fixate.drivers.dcload.helper import DCLoad


def open() -> DCLoad:
    """
    Connect to a DC electronic load.

    Searches for a configured instrument and returns the first one found.

    Returns:
        DCLoad: open connection to the DCLoad
    """
    for DCLoad in (RigolDL3021,):
        instrument = find_instrument_by_id(DCLoad.REGEX_ID)
        if instrument is not None:
            # We've found a configured instrument so try to open it
            rm = pyvisa.ResourceManager()
            try:
                resource = rm.open_resource(instrument.address)
            except pyvisa.VisaIOError as e:
                raise InstrumentOpenError(
                    f"Unable to open DCLoad: {instrument.address}"
                ) from e
            # Instantiate driver with connected instrument
            driver = DCLoad(resource)
            fixate.drivers.log_instrument_open(driver)
            return driver
    raise InstrumentNotFoundError
