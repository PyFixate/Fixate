import ctypes
import logging
from collections.abc import Collection
from enum import IntEnum, IntFlag, StrEnum, unique

from fixate.core.exceptions import FixateError, InstrumentNotConnected
from fixate.drivers import log_instrument_open
from fixate.drivers.ftdi import FT_HANDLE, FTD2XXError, check_return
from fixate.drivers.ftdi._libmpsse import libmpsse

# For more information see https://ftdichip.com/wp-content/uploads/2020/08/AN_177_User_Guide_For_LibMPSSE-I2C-1.pdf
# Additionally, the source code for libMPSSE is available as part of this download: https://ftdichip.com/wp-content/uploads/2025/08/libmpsse-windows-1.0.8.zip

DWORD = ctypes.c_ulong
UCHAR = ctypes.c_ubyte
USHORT = ctypes.c_ushort
LPDWORD = ctypes.POINTER(DWORD)
PCHAR = ctypes.c_char_p

logger = logging.getLogger(__name__)


class I2CError(FixateError):
    """Base class for I2C errors."""

    pass


class SPIError(FixateError):
    """Base class for SPI errors."""

    pass


class Protocol(StrEnum):
    I2C = "i2c"
    SPI = "spi"
    # TODO - add more protocols as needed


@unique
class I2CTransferOptions(IntFlag):
    START_BIT = 0x01
    STOP_BIT = 0x02
    BREAK_ON_NACK = 0x04
    NACK_LAST_BYTE = 0x08
    FAST_TRANSFER_BYTES = 0x10
    FAST_TRANSFER_BITS = 0x20
    NO_ADDRESS = 0x40


@unique
class I2CClockRate(IntEnum):
    STANDARD_MODE = 100000
    FAST_MODE = 400000
    FAST_MODE_PLUS = 1000000
    HIGH_SPEED_MODE = 3400000


@unique
class I2COptions(IntFlag):
    DISABLE_3PHASE_CLOCKING = 0x01
    ENABLE_DRIVE_ONLY_ZERO = 0x02
    # This option is not documented in the user guide, but is mentioned in the source code.
    ENABLE_PIN_STATE_CONFIG = 0x10
    # Bits 4 - 31 are reserved


class I2CChannelConfig(ctypes.Structure):
    _fields_ = [
        ("ClockRate", DWORD),
        ("LatencyTimer", UCHAR),
        ("Options", DWORD),
        ("Pin", DWORD),
        ("currentPinState", USHORT),
    ]


class Mpsse:
    """
    Base class for MPSSE drivers. This class should not be instantiated directly, but should be derived from for specific protocols.
    Derived classes should implement protocol-specific functionality, but can rely on the base class for connection management and other common functionality.
    """

    INSTR_TYPE = "FTDI"
    REGEX_ID = ""  # this is only here to 'satisfy' the DriverProtocol interface

    def __init__(self, ftdi_description: str):
        self.ftdi_description = ftdi_description
        self._handle = FT_HANDLE()

    def get_identity(self) -> str:
        """Return identity string representing connected ftdi object"""
        return self.ftdi_description


class MpsseI2C(Mpsse):
    def __init__(self, ftdi_description: str):
        super().__init__(ftdi_description)
        self._connect()

    def _connect(self):
        check_return(
            libmpsse.I2C_OpenChannelByDescription(
                self.ftdi_description.encode("utf-8"), ctypes.byref(self._handle)
            )
        )

    def configure(
        self, config: I2CChannelConfig | None = None, options: I2COptions | None = None
    ):
        if config is None:
            config = I2CChannelConfig(
                ClockRate=I2CClockRate.STANDARD_MODE,  # standard 100 kHz I2C clock rate, this is the default speed used by pyftdi.
                LatencyTimer=16,
                Options=options.value if options is not None else 0,
                Pin=0,
                currentPinState=0,
            )
        check_return(libmpsse.I2C_InitChannel(self._handle, ctypes.byref(config)))

    def read(
        self, address: int, length: int, options: I2CTransferOptions | None = None
    ) -> bytes:
        """Read data from an I2C device.

        Args:
            address: The 7-bit I2C address of the device to read from.
            length: The number of bytes to read.
            options: Optional transfer options. See I2CTransferOptions for more information.

        Returns:
            The data read from the I2C device.

        Raises:
            FTD2XXError: Via check_return if the underlying library call fails.
                FT_IO_ERROR will occur if the device does not transfer the expected number of bytes.
                FT_DEVICE_NOT_FOUND will occur if the device does not respond.
        """
        # libmpsse handles the conversion of the address and read/write bit, so we just need to pass the 7-bit address.
        _addr = UCHAR(address)
        _buffer = (UCHAR * length)()
        _bytes_read = DWORD()
        try:
            check_return(
                libmpsse.I2C_DeviceRead(
                    self._handle,
                    _addr,
                    ctypes.byref(_buffer),
                    length,
                    ctypes.byref(_bytes_read),
                    options.value if options is not None else 0,
                )
            )
        except FTD2XXError as e:
            if e.args[0] == libmpsse.FT_IO_ERROR:
                raise FTD2XXError(
                    f"Expected to read {length} bytes, but only read {_bytes_read.value} bytes."
                ) from e
            elif e.args[0] == libmpsse.FT_DEVICE_NOT_FOUND:
                raise FTD2XXError(f"Device with address {address} not found.") from e
            else:
                # Something else happened that isn't documented by the libmpsse library.
                raise
        return bytes(_buffer[: _bytes_read.value])

    def write(
        self,
        address: int,
        data: bytes | bytearray | Collection[int],
        options: I2CTransferOptions | None = None,
    ):
        """Write data to an I2C device.

        Args:
            address: The 7-bit I2C address of the device to write to.
            data: The data to write to the device.
            options: Optional transfer options. See I2CTransferOptions for more information.

        Raises:
            FTD2XXError: Via check_return if the underlying library call fails.
                FT_IO_ERROR will occur if the device does not transfer the expected number of bytes.
                FT_DEVICE_NOT_FOUND will occur if the device does not respond.
                FT_FAILED_TO_WRITE_DEVICE will occur if the device nACKs a byte and the BREAK_ON_NACK option is specified.
        """
        # libmpsse handles the conversion of the address and read/write bit, so we just need to pass the 7-bit address.
        _addr = UCHAR(address)
        _buffer = (UCHAR * len(data))(*data)
        _bytes_written = DWORD()
        try:
            check_return(
                libmpsse.I2C_DeviceWrite(
                    self._handle,
                    _addr,
                    ctypes.byref(_buffer),
                    len(data),
                    ctypes.byref(_bytes_written),
                    options.value if options is not None else 0,
                )
            )
        except FTD2XXError as e:
            if e.args[0] == libmpsse.FT_IO_ERROR:
                raise FTD2XXError(
                    f"Expected to write {len(data)} bytes, but only wrote {_bytes_written.value} bytes."
                ) from e
            elif e.args[0] == libmpsse.FT_DEVICE_NOT_FOUND:
                raise FTD2XXError(f"Device with address {address} not found.") from e
            elif e.args[0] == libmpsse.FT_FAILED_TO_WRITE_DEVICE:
                raise FTD2XXError(
                    f"Device with address {address} NACKed a byte."
                ) from e
            else:
                # Something else happened that isn't documented by the libmpsse library.
                raise

    def exchange(
        self,
        address: int,
        data: bytes | bytearray | Collection[int],
        write_options: I2CTransferOptions,
        read_length: int,
        read_options: I2CTransferOptions,
    ) -> bytes:
        """Write data to an I2C device, then read data from the device with a repeated start.

        Args:
            address: The 7-bit I2C address of the device to write to and read from.
            data: The data to write to the device before reading. E.g. a register address to read from.
            read_length: The number of bytes to read from the device after writing.
            write_options: Transfer options for the write operation. See I2CTransferOptions for more information.
            read_options: Transfer options for the read operation. See I2CTransferOptions for more information.

        Returns:
            The data read from the I2C device after writing.

        Raises:
            FTD2XXError
        """

        # First we write to the device with address and the data to write (e.g. register address), then we read from the device with the same address and the specified number of bytes to read.
        # the options parameters will determine if start|stop|repeated-start bits are sent.
        self.write(address, data, options=write_options)
        return self.read(address, read_length, options=read_options)

    def write_gpio(self, direction: int, pin_values: int):
        """Set the state of the GPIO pins.

        Args:
            direction: Direction of the GPIO pins. 1 for output, 0 for input.
            pin_values: Values of the GPIO pins. For output pins, 1 for high, 0 for low. For input pins, this value is ignored.

        Raises:
            FTD2XXError: Via check_return if the underlying library call fails.
        """
        _dir = UCHAR(direction)
        _values = UCHAR(pin_values)
        check_return(libmpsse.I2C_WriteGPIO(self._handle, _dir, _values))

    def read_gpio(self) -> int:
        """Read the state of the GPIO pins.

        Returns:
            The state of the GPIO pins. For output pins, 1 for high, 0 for low. For input pins, 1 for high, 0 for low.

        Raises:
            FTD2XXError: Via check_return if the underlying library call fails.
        """
        _values = UCHAR()
        check_return(libmpsse.I2C_ReadGPIO(self._handle, ctypes.byref(_values)))
        return _values.value

    def get_simple_interface(self, address: int) -> "MpsseI2CSimpleInterface":
        """Get a simple interface to the I2C device similar to the port concept used by pyftdi. This is not intended to be a
        full-featured interface, but can be useful for simple use cases where the full flexibility of the underlying library is not needed.

        Returns:
            An instance of MpsseI2CSimpleInterface that provides a simplified interface to the I2C device.
        """

        return MpsseI2CSimpleInterface(self, address)

    def close(self):
        check_return(libmpsse.I2C_CloseChannel(self._handle))


class MpsseI2CSimpleInterface:
    """A simple interface to an I2C device that provides basic read and write functionality without requiring the user to specify transfer options or other parameters.
    This is intended to be used for simple use cases where the full flexibility of the underlying library is not needed. Similar to the pyftdi library.
    """

    def __init__(self, main_interface: MpsseI2C, address: int):
        self._main_interface = main_interface
        self._address = address

    def read(self, length: int) -> bytes:
        """Read data from the I2C device.

        This method uses default transfer options that should be suitable for most use cases. If you need more control over the transfer, you can use the read method of the main interface MpsseI2C directly.

        Args:
            length: The number of bytes to read.

        Returns:
            The data read from the I2C device.

        Raises:
            FTD2XXError
        """

        options = (
            I2CTransferOptions.START_BIT
            | I2CTransferOptions.STOP_BIT
            | I2CTransferOptions.BREAK_ON_NACK
        )
        return self._main_interface.read(self._address, length, options=options)

    def read_from(self, register: int, length: int) -> bytes:
        """Read data from a specific register of the I2C device.

        This method uses default transfer options that should be suitable for most use cases. If you need more control over the transfer, you can use the exchange method of the main interface MpsseI2C directly.

        Args:
            register: The register address to read from.
            length: The number of bytes to read.

        Returns:
            The data read from the specified register of the I2C device.

        Raises:
            FTD2XXError
        """
        # these options will result in a repeated start between the write and read operations.
        write_options = I2CTransferOptions.START_BIT | I2CTransferOptions.BREAK_ON_NACK
        read_options = (
            I2CTransferOptions.START_BIT
            | I2CTransferOptions.STOP_BIT
            | I2CTransferOptions.BREAK_ON_NACK
        )
        return self._main_interface.exchange(
            self._address,
            bytes([register]),
            write_options=write_options,
            read_length=length,
            read_options=read_options,
        )

    def write(self, data: bytes | bytearray | Collection[int]):
        """Write data to the I2C device.

        This method uses default transfer options that should be suitable for most use cases. If you need more control over the transfer, you can use the write method of the main interface MpsseI2C directly.

        Args:
            data: The data to write to the I2C device.

        Raises:
            FTD2XXError
        """

        options = (
            I2CTransferOptions.START_BIT
            | I2CTransferOptions.STOP_BIT
            | I2CTransferOptions.BREAK_ON_NACK
        )
        return self._main_interface.write(self._address, data, options=options)

    def write_to(self, register: int, data: bytes | bytearray | Collection[int]):
        """Write data to a specific register of the I2C device.

        This method uses default transfer options that should be suitable for most use cases. If you need more control over the transfer, you can use the exchange method of the main interface MpsseI2C directly.

        Args:
            register: The register address to write to.
            data: The data to write to the specified register of the I2C device.

        Raises:
            FTD2XXError
        """
        # TODO - might need to consider the possibility of the register being multiple bytes, but for now assume it's just one byte.

        write_options = (
            I2CTransferOptions.START_BIT
            | I2CTransferOptions.STOP_BIT
            | I2CTransferOptions.BREAK_ON_NACK
        )
        return self._main_interface.write(
            self._address, bytes([register]) + bytes(data), options=write_options
        )


@unique
class SPITransferOptions(IntEnum):
    # TODO - complete me
    def __init__(self, value):
        raise NotImplementedError("SPI support not yet implemented.")


class MpsseSPI(Mpsse):
    INSTR_TYPE = "FTDI"
    # TODO - complete me
    def __init__(self, ftdi_description: str):
        raise NotImplementedError("SPI support not yet implemented.")


def open(protocol: Protocol | str, ftdi_description: str) -> Mpsse:
    """Open an MPSSE device with the given protocol and description.

    Args:
        protocol: The protocol to use with the device. This determines which MPSSE class to instantiate.
        ftdi_description: The description of the device to open. This is the "Description" field from the D2XX API (aka).

    Returns:
        An instance of the appropriate MPSSE class for the given protocol, initialized with the device corresponding to the given description.

    Raises:
        InstrumentNotConnected: If no device with the given description is found.
        ValueError: If an unsupported protocol is specified.
    """

    if protocol == Protocol.I2C or protocol == "i2c":
        try:
            driver = MpsseI2C(ftdi_description)
        except FTD2XXError:
            raise InstrumentNotConnected(
                f"FTDI device with description '{ftdi_description}' not found."
            )
    elif protocol == Protocol.SPI or protocol == "spi":
        # TODO - implement me
        raise NotImplementedError("SPI support not yet implemented.")
    else:
        raise ValueError(
            f"Unsupported protocol '{protocol}'. Supported protocols are: {[p.value for p in Protocol]}."
        )

    log_instrument_open(driver)
    return driver


def lib_versions() -> tuple[int, int]:
    """
    Get the versions of the libMPSSE and libftdi libraries.
    Returns:
        A tuple containing the libMPSSE version and the libftdi version, both as integers in the format 0xAABBCCDD where AA is the major version, BB is the minor version, CC is the patch version, and DD is the build number.
    """
    mpsse_version = DWORD(0)
    libftdi_version = DWORD(0)

    libmpsse.Ver_libMPSSE(ctypes.byref(mpsse_version), ctypes.byref(libftdi_version))

    return mpsse_version.value, libftdi_version.value
