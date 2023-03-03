"""
funcgen is the function generator driver.

Use funcgen.open to connect to a connected digital multi meter
Functions are dictacted by the metaclass in helper.py

Usage:
myfuncgen = funcgen.open()
myfuncgen.function('sin', freq='1kHz')
myfuncgen.function('square', 'ch2', amplit=5, offset=2.5, freq='1kHz')
myfuncgen.output_ch1 = True
myfuncgen.output_ch2 = True

functions:
function(self, *mode, **mode_params):
adv_function(self, *mode, **mode_params):
reset(self):

properties:
output_ch1
output_ch2
output_ch3
output_ch4
"""
import pyvisa

import fixate.drivers
from fixate.config import find_instrument_by_id
from fixate.drivers import InstrumentNotFoundError, InstrumentOpenError
from fixate.drivers.funcgen.helper import FuncGen
from fixate.drivers.funcgen.keysight_33500b import Keysight33500B
from fixate.drivers.funcgen.rigol_dg1022 import RigolDG1022


def open() -> FuncGen:
    """Open is the public api for the dmm driver for discovering and opening a connection
    to a valid Digital Multimeter
    :return:
    A instantiated class connected to a valid funcgen
    """
    for driver_class in (Keysight33500B, RigolDG1022):
        instrument = find_instrument_by_id(driver_class.REGEX_ID)
        if instrument is not None:
            # We've found a configured instrument so try to open it
            rm = pyvisa.ResourceManager()
            try:
                resource = rm.open_resource(instrument.address)
            except pyvisa.VisaIOError as e:
                raise InstrumentOpenError(
                    f"Unable to open FuncGen: {instrument.address}"
                ) from e
            # Instantiate driver with connected instrument
            driver = driver_class(resource)
            fixate.drivers.log_instrument_open(driver)
            return driver
    raise InstrumentNotFoundError
