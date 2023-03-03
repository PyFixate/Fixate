from fixate.drivers import pps, dmm, ftdi, dso, funcgen
from fixate.core.jig_mapping import AddressHandler, JigDriver, RelayMatrixMux


class DriverManager:
    def __init__(self):
        self._funcgen = None
        self._dmm = None
        self._ftdi_J413 = None
        self._ftdi_mux = None
        self._dso = None
        self._pps = None

    @property
    def funcgen(self):
        if self._funcgen is None:
            self._funcgen = funcgen.open()
            self._funcgen.reset()
            self._funcgen.instrument.timeout = 2000
        return self._funcgen

    @property
    def dso(self):
        if self._dso is None:
            self._dso = dso.open()
            self._dso.reset()
            self._dso.instrument.timeout = 2000
        return self._dso

    @property
    def dmm(self):
        if self._dmm is None:
            self._dmm = dmm.open()
            self._dmm.instrument.timeout = 7000
        return self._dmm

    @property
    def pps(self):
        if self._pps is None:
            self._pps = pps.open()
            self._pps.instrument.timeout = 2000
        return self._pps

    @property
    def ftdi_J413(self):
        if self._ftdi_J413 is None:
            self._ftdi_J413 = J413Relays()
            self._ftdi_J413.reset()
        return self._ftdi_J413

    @property
    def ftdi_mux(self):
        if self._ftdi_mux is None:
            self._ftdi_mux = ftdi.open(ftdi_description="Patch Panel Loop Back Jig")
            if self._ftdi_mux is None:
                raise InstrumentError(
                    "Could not find Jig ftdi chip\n"
                    "If problem persists, check USB cables and restart script"
                )
            self._ftdi_mux.configure_bit_bang(
                ftdi.BIT_MODE.FT_BITMODE_ASYNC_BITBANG,
                bytes_required=14,
                data_mask=4,
                clk_mask=2,
                latch_mask=1,
            )
            self._ftdi_mux.baud_rate = 115200
        return self._ftdi_mux


# *******************************************************************************


class connectionMap(RelayMatrixMux):
    pin_list = (
        "1K1",
        "1K2",
        "1K3",
        "1K4",
        "1K5",
        "1K6",
        "1K7",
        "1K8",
        "1K9",
        "1K10",
        "1K11",
        "1K12",
        "1K13",
        "1K14",
        "1K15",
        "1K16",
        "2K1",
        "2K2",
        "2K3",
        "2K4",
        "2K5",
        "2K6",
        "2K7",
        "2K8",
        "2K9",
        "2K10",
        "2K11",
        "2K12",
        "2K13",
        "2K14",
        "2K15",
        "2K16",
    )
    map_list = (
        ("No_Input",),
        ("SIG_DSO_CH1_1", "1K8", "1K11"),  # Connects sig gen to dso CH1
        ("SIG_DSO_CH2_1", "1K8", "1K12"),  # Connects sig gen to dso CH2
        ("SIG_DSO_CH2_2", "2K8", "2K12"),  # Connects sig gen to dso CH2
        (
            "SIG_DSO_CH12",
            "1K16",
            "2K16",
            "1K8",
            "1K11",
            "2K12",
        ),  # Connects DSO CH1 to sig gen and CH2 to sig gen through cap
        ("DMM_R1_2w", "1K13", "1K2"),  # Connect DMM through R1 (two wire measurement)
        (
            "DMM_R1_4w",
            "1K13",
            "1K2",
            "1K3",
        ),  # Connect DMM through R1 (two wire measurement)
        ("DMM_SIG", "1K2", "1K8"),  # Connect DMM through R1 (two wire measurement)
        ("DMM_C1", "1K16", "1K2"),  # Connect DMM through C1
        ("DMM_D1", "2K15", "2K2"),  # Connect DMM through C1
    )


# *******************************************************************************


class FTDIAddressHandler(AddressHandler):
    # A list of the actual relays implemented the jig.
    pin_list = (
        "1K1",
        "1K2",
        "1K3",
        "1K4",
        "1K5",
        "1K6",
        "1K7",
        "1K8",
        "1K9",
        "1K10",
        "1K11",
        "1K12",
        "1K13",
        "1K14",
        "1K15",
        "1K16",
        "2K1",
        "2K2",
        "2K3",
        "2K4",
        "2K5",
        "2K6",
        "2K7",
        "2K8",
        "2K9",
        "2K10",
        "2K11",
        "2K12",
        "2K13",
        "2K14",
        "2K15",
        "2K16",
    )

    def update_output(self, value):
        self.serial_shift(value)

    @staticmethod
    def serial_shift(serial_data):
        dm.ftdi_mux.serial_shift_bit_bang(serial_data)


# Note: a separate "JigDriver" is required for each USB hardware device
class J413Relays(JigDriver):
    multiplexers = (connectionMap(),)
    address_handlers = (FTDIAddressHandler(),)


dm = DriverManager()
