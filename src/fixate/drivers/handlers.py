"""
This module implements concrete AddressHandler type, that
can be used to implement IO for the fixate.core.switching module.
"""
from __future__ import annotations

from typing import Sequence

from fixate.core._switching import Pin, PinValueAddressHandler
from fixate.drivers import ftdi


class FTDIAddressHandler(PinValueAddressHandler):
    """
    An address handler which uses the ftdi driver to control pins.

    We create this concrete address handler because we use it most
    often. FT232 is used to bit-bang to shift register that are control
    the switching in a jig.
    """

    def __init__(
        self,
        ftdi_description: str,
        pins: Sequence[Pin] = tuple(),
    ) -> None:
        # pin_list must be defined before calling the base class __init__
        self.pin_list = tuple(pins)
        super().__init__()

        # how many bytes? enough for every pin to get a bit. We might
        # end up with some left-over bits. The +7 in the expression
        # ensures we round up.
        bytes_required = (len(self.pin_list) + 7) // 8
        self._ftdi = ftdi.open(ftdi_description=ftdi_description)
        self._ftdi.configure_bit_bang(
            ftdi.BIT_MODE.FT_BITMODE_ASYNC_BITBANG,
            bytes_required=bytes_required,
            data_mask=4,
            clk_mask=2,
            latch_mask=1,
        )
        # Measurement of baudrate vs bit-bang. The programming manual say 16 x, but that
        # only appears to be true for lower clock rates. Keeping the actual value at 115200
        # since that was used regularly in the past
        # baudrate      bit-bang update rate
        # 1_000_000     ~2 MHz
        # 750_000       ~2.4 MHz
        # 115_200       ~926 kHz
        # 10_000        ~160 kHz
        self._ftdi.baud_rate = 115_200

    def close(self) -> None:
        self._ftdi.close()

    def _update_output(self, value: int) -> None:
        self._ftdi.serial_shift_bit_bang(value)
