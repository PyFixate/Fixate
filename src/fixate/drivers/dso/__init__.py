import pyvisa
import fixate.drivers
from fixate.drivers.dso.helper import DSO
from fixate.drivers.dso.agilent_mso_x import MSO_X_3000
from fixate.config import find_instrument_by_id


def open() -> DSO:
    instrument = find_instrument_by_id(MSO_X_3000.REGEX_ID)
    if instrument is not None:
        # we've found a connected instrument so open and return it
        rm = pyvisa.ResourceManager()
        # open_resource could raise visa.VisaIOError?
        driver = MSO_X_3000(rm.open_resource(instrument.address))
        fixate.drivers.log_instrument_open(driver)
        return driver
    raise fixate.drivers.InstrumentNotFoundError
