from fixate.drivers.pps.helper import PPS

import pyvisa
import fixate.drivers
from fixate.drivers.pps.bk_178x import BK178X
from fixate.drivers.pps.siglent_spd_3303X import SPD3303X
from fixate.config import find_instrument_by_id


def open() -> PPS:
    siglent = find_instrument_by_id(SPD3303X.REGEX_ID)
    if siglent is not None:
        # we've found a connected instrument so open and return it
        rm = pyvisa.ResourceManager()
        # open_resource could raise visa.VisaIOError?
        driver = SPD3303X(rm.open_resource(siglent.address))
        fixate.drivers.log_instrument_open(driver)
        return driver

    bk_precision = find_instrument_by_id(BK178X.REGEX_ID)
    if bk_precision is not None:
        driver = BK178X(bk_precision.address)
        driver.baud_rate = bk_precision.parameters["baud_rate"]
        fixate.drivers.log_instrument_open(driver)
        return driver

    raise fixate.drivers.InstrumentNotFoundError
