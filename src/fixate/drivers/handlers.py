"""
This module implements concrete AddressHandler type, that
can be used to implement IO for the fixate.core.switching module.
"""
from __future__ import annotations

from typing import Sequence
import itertools

from fixate.core.switching import Pin, PinValueAddressHandler
from fixate.drivers import ftdi


def _pins_for_one_relay_matrix(relay_matrix_num: int) -> list[Pin]:
    """
    A helper to create pin names for relay matrix cards.

    Returns 16 pin names. If relay_matrix_num is 1:
    1K1, 1K2, 1K3, ..., 1K16
    """
    return [f"{relay_matrix_num}K{relay}" for relay in range(1, 17)]


# This is a real quick test. Not worth the effort unravelling
# imports when ftdi isn't importable, just to get this into a
# proper test right now...
__expected = (
    "3K1 3K2 3K3 3K4 3K5 3K6 3K7 3K8 3K9 3K10 3K11 3K12 3K13 3K14 3K15 3K16".split()
)
assert _pins_for_one_relay_matrix(3) == __expected


class RelayMatrixAddressHandler(PinValueAddressHandler):
    """
    An address handler which uses the ftdi driver to control pins.

    We create this concrete address handler because we use it most
    often. FT232 is used to bit-bang to shift register that are control
    the switching in a jig.
    """

    def __init__(
        self,
        ftdi_description: str,
        relay_matrix_count: int,
        extra_pins: Sequence[Pin] = tuple(),
    ) -> None:
        relay_matrix_pin_list = tuple(
            itertools.chain.from_iterable(
                _pins_for_one_relay_matrix(rm_number)
                for rm_number in range(1, relay_matrix_count + 1)
            )
        )
        self.pin_list = relay_matrix_pin_list + tuple(extra_pins)
        # call the base class super _after_ we create the pin list
        super().__init__()

        # how many bytes? enough for every pin to get a bit. We might
        # end up with some left-over bits. The +7 in the expression
        # ensure we round up.
        bytes_required = (len(self.pin_list) + 7) // 8
        self._ftdi = ftdi.open(ftdi_description=ftdi_description)
        self._ftdi.configure_bit_bang(
            ftdi.BIT_MODE.FT_BITMODE_ASYNC_BITBANG,
            bytes_required=bytes_required,
            data_mask=4,
            clk_mask=2,
            latch_mask=1,
        )
        self._ftdi.baud_rate = 115200

    def close(self) -> None:
        self._ftdi.close()

    def _update_output(self, value: int) -> None:
        self._ftdi.serial_shift_bit_bang(value)
