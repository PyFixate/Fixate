import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.pps.bk_178x import BK178X
from fixate.drivers.pps.helper import PPS
from fixate.drivers.pps.siglent_spd_3303X import SPD3303X


def open() -> PPS:
    siglent = find_instrument_by_id(SPD3303X.REGEX_ID)
    if siglent is not None:
        # We've found a configured instrument so try to open it
        rm = pyvisa.ResourceManager()
        try:
            resource = rm.open_resource(siglent.address)
        except pyvisa.VisaIOError as e:
            raise InstrumentOpenError(f"Unable to open PPS: {siglent.address}") from e
        # Instantiate driver with connected instrument
        driver = SPD3303X(resource)
        fixate.drivers.log_instrument_open(driver)
        return driver

    bk_precision = find_instrument_by_id(BK178X.REGEX_ID)
    if bk_precision is not None:
        driver = BK178X(bk_precision.address)
        driver.baud_rate = bk_precision.parameters["baud_rate"]
        fixate.drivers.log_instrument_open(driver)
        return driver

    raise InstrumentNotFoundError
