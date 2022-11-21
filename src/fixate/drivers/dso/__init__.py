import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.dso.agilent_mso_x import MSO_X_3000
from fixate.drivers.dso.helper import DSO


def open() -> DSO:
    instrument = find_instrument_by_id(MSO_X_3000.REGEX_ID)
    if instrument is not None:
        # We've found a configured instrument so try to open it
        rm = pyvisa.ResourceManager()
        try:
            resource = rm.open_resource(instrument.address)
        except pyvisa.VisaIOError as e:
            raise InstrumentOpenError(
                f"Unable to open DSO: {instrument.address}"
            ) from e
        # Instantiate driver with connected instrument
        driver = MSO_X_3000(resource)
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise InstrumentNotFoundError
