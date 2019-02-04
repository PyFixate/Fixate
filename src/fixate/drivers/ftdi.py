import ctypes
import struct
import time
import os
from fixate.core.common import bits
from fixate.core.exceptions import InstrumentError, InstrumentNotConnected
import fixate.config
import fixate.core.discover


def open(ftdi_description=""):
    """Open is the public api for the bit bang driver for discovering and opening a connection
    to a valid bit bang device
    :param restrictions:
    A dictionary containing the extents of the required equipment
    :return:
    A instantiated class connected to a valid bit_bang class
    """
    devices = fixate.core.discover.discover_ftdi()
    for dev in devices:
        if ftdi_description.encode() == dev.Description or ftdi_description == "":
            return FTDI2xx(dev.Description)
    raise InstrumentNotConnected("No valid ftdi found by description '{}'".format(ftdi_description))


# Definitions
UCHAR = ctypes.c_ubyte
PCHAR = ctypes.POINTER(ctypes.c_char)
PUCHAR = ctypes.POINTER(ctypes.c_ubyte)
DWORD = ctypes.c_ulong
LPDWORD = ctypes.POINTER(ctypes.c_ulong)
FT_HANDLE = DWORD


class FT_STATUS(object):
    FT_OK = DWORD(0)
    FT_INVALID_HANDLE = DWORD(1)
    FT_DEVICE_NOT_FOUND = DWORD(2)
    FT_DEVICE_NOT_OPENED = DWORD(3)
    FT_IO_ERROR = DWORD(4)
    FT_INSUFFICIENT_RESOURCES = DWORD(5)
    FT_INVALID_PARAMETER = DWORD(6)
    FT_INVALID_BAUD_RATE = DWORD(7)
    FT_DEVICE_NOT_OPENED_FOR_ERASE = DWORD(8)
    FT_DEVICE_NOT_OPENED_FOR_WRITE = DWORD(9)
    FT_FAILED_TO_WRITE_DEVICE = DWORD(10)
    FT_EEPROM_READ_FAILED = DWORD(11)
    FT_EEPROM_WRITE_FAILED = DWORD(12)
    FT_EEPROM_ERASE_FAILED = DWORD(13)
    FT_EEPROM_NOT_PRESENT = DWORD(14)
    FT_EEPROM_NOT_PROGRAMMED = DWORD(15)
    FT_INVALID_ARGS = DWORD(16)
    FT_NOT_SUPPORTED = DWORD(17)
    FT_OTHER_ERROR = DWORD(18)

    def get_status_message(self, value):
        for msg, itm in FT_STATUS.__dict__.items():
            try:
                if itm.value == value:
                    return msg
            except AttributeError:
                pass


class FT_DEVICE(object):
    FT_DEVICE_232BM = DWORD(0)
    FT_DEVICE_232AM = DWORD(1)
    FT_DEVICE_100AX = DWORD(2)
    FT_DEVICE_UNKNOWN = DWORD(3)
    FT_DEVICE_2232C = DWORD(4)
    FT_DEVICE_232R = DWORD(5)
    FT_DEVICE_2232H = DWORD(6)
    FT_DEVICE_4232H = DWORD(7)
    FT_DEVICE_232H = DWORD(8)
    FT_DEVICE_X_SERIES = DWORD(9)


class FLAGS(object):
    FT_OPEN_BY_SERIAL_NUMBER = DWORD(1)
    FT_OPEN_BY_DESCRIPTION = DWORD(2)
    FT_OPEN_BY_LOCATION = DWORD(4)


class BIT_MODE(object):
    FT_BITMODE_RESET = DWORD(0x00)
    FT_BITMODE_ASYNC_BITBANG = DWORD(0x01)
    FT_BITMODE_MPSSE = DWORD(0x02)
    FT_BITMODE_SYNC_BITBANG = DWORD(0x04)
    FT_BITMODE_MCU_HOST = DWORD(0x08)
    FT_BITMODE_FAST_SERIAL = DWORD(0x10)
    FT_BITMODE_CBUS_BITBANG = DWORD(0x20)
    FT_BITMODE_SYNC_FIFO = DWORD(0x40)


# Add null padding if 64 bit
if struct.calcsize("P") == 8:
    class FT_DEVICE_LIST_INFO_NODE(ctypes.Structure):
        _fields_ = [("Flags", DWORD),
                    ("Type", DWORD),
                    ("ID", DWORD),
                    ("LocId", DWORD),
                    ("SerialNumber", ctypes.c_char * 16),
                    ("Description", ctypes.c_char * 64),
                    ("ftHandle", DWORD),
                    ("null_padding", DWORD)]
else:  # 32 bit
    class FT_DEVICE_LIST_INFO_NODE(ctypes.Structure):
        _fields_ = [("Flags", DWORD),
                    ("Type", DWORD),
                    ("ID", DWORD),
                    ("LocId", DWORD),
                    ("SerialNumber", ctypes.c_char * 16),
                    ("Description", ctypes.c_char * 64),
                    ("ftHandle", DWORD)]


class WORD_LENGTH(object):
    FT_BITS_8 = UCHAR(8)
    FT_BITS_7 = UCHAR(7)


class STOP_BITS(object):
    FT_STOP_BITS_1 = UCHAR(0)
    FT_STOP_BITS_2 = UCHAR(2)


class PARITY(object):
    FT_PARITY_NONE = UCHAR(0)
    FT_PARITY_ODD = UCHAR(1)
    FT_PARITY_EVEN = UCHAR(2)
    FT_PARITY_MARK = UCHAR(3)
    FT_PARITY_SPACE = UCHAR(4)


if os.name == 'nt':
    try:
        ftdI2xx = ctypes.WinDLL("FTD2XX.dll")
    except Exception as e:
        raise ImportError("Unable to find FTD2XX.dll.\nPlugging in FDTI device will install DLL.") from e
else:
    try:
        ftdI2xx = ctypes.cdll.LoadLibrary('/usr/local/lib/libftd2xx.so')
    except Exception as e:
        raise ImportError("Unable to find libftd2xx.so.\nInstall as per https://www.ftdichip.com/Drivers/D2XX/Linux/ReadMe-linux.txt") from e


_ipdwNumDevs = DWORD(0)
_p_ipdwNumDevs = LPDWORD(_ipdwNumDevs)


def create_device_info_list():
    # FT_CreateDeviceInfoList needs to be called before info can be retrieved
    stat = DWORD()
    stat.value = ftdI2xx.FT_CreateDeviceInfoList(_p_ipdwNumDevs)
    # print(stat)
    if stat.value != FT_STATUS.FT_OK.value:
        pass
        # print(stat)
        # print(type(stat))
        # print(type(FT_STATUS.FT_OK))
        # print(ipdwNumDevs)


def _get_device_info_detail(pDest):
    # FT_GetDeviceInfoDetail
    stat = DWORD()
    dev = pDest[0]
    handle = DWORD()
    flags = DWORD()
    typeid = DWORD()
    id = DWORD()
    locid = DWORD()
    sn = ctypes.create_string_buffer(16)
    desc = ctypes.create_string_buffer(64)
    stat.value = ftdI2xx.FT_GetDeviceInfoDetail(dev,
                                                flags,
                                                typeid,
                                                id,
                                                locid,
                                                sn,
                                                desc,
                                                ctypes.byref(handle))

    if stat.value != FT_STATUS.FT_OK.value:
        raise Exception("FT_GetDeviceInfoDetail failed")

        # print("flags {}".format(flags))
        # print("typeid {}".format(typeid))
        # print("id {}".format(id))
        # print("locid {}".format(locid))
        # print("sn {}".format(sn))
        # print("desc {}".format(desc))
        # print("handle {}".format(handle))


# FT_GetDeviceInfoList
def get_device_info_list():
    stat = DWORD()
    pDest = (FT_DEVICE_LIST_INFO_NODE * _ipdwNumDevs.value)()
    # for num in range(_ipdwNumDevs.value):
    # print(dir(pDest[num]))
    # print(pDest[num].Flags)

    stat.value = ftdI2xx.FT_GetDeviceInfoList(pDest, ctypes.byref(_ipdwNumDevs))
    if stat.value != FT_STATUS.FT_OK.value:
        raise Exception("FT_GetDeviceInfoList failed")

    # for field in FT_DEVICE_LIST_INFO_NODE._fields_:
    # print("{}: {} - {}".format(field[0].upper(), getattr(pDest[0], field[0]), type(getattr(pDest[0], field[0]))))
    return pDest


class FTDI2xx(object):
    INSTR_TYPE = "FTDI"

    def __init__(self, ftdi_description):
        """
        :param handle:
            handle from device info
        :param flag:
            FLAGS
            FLAGS.FT_OPEN_BY_SERIAL_NUMBER
            FLAGS.FT_OPEN_BY_DESCRIPTION
            FLAGS.FT_OPEN_BY_LOCATION
        :param search_term:
            Accompanying search term set by the flag
        :return:
        """
        self.handle = DWORD()
        self.ftdi_description = ftdi_description
        self.cmd_status = DWORD()
        self._connect()
        self._baud_rate = None
        self.baud_rate = 9600
        self.bit_mode = BIT_MODE.FT_BITMODE_CBUS_BITBANG
        self.pin_value_mask = 0b111

        self.std_delay = 0.01
        self.delay = time.sleep
        # Data characteristics
        self._word_length = WORD_LENGTH.FT_BITS_8
        self._stop_bits = STOP_BITS.FT_STOP_BITS_1
        self._parity = PARITY.FT_PARITY_NONE
        self._data_characteristics_set = False
        self.bb_data = 1 << 0
        self.bb_clk = 1 << 1
        self.bb_latch = 1 << 2
        self.bb_bytes = 1
        self.bb_inv_mask = 0

    def _connect(self):
        self.cmd_status.value = ftdI2xx.FT_OpenEx(ctypes.c_char_p(self.ftdi_description),
                                                  FLAGS.FT_OPEN_BY_DESCRIPTION,
                                                  ctypes.byref(self.handle))
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_OpenEx failed")

    def close(self):
        self.cmd_status.value = ftdI2xx.FT_Close(self.handle)
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_Close failed {}".format(self.cmd_status.value))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def word_length(self):
        return self._word_length

    @word_length.setter
    def word_length(self, val):
        if str(val) == '8':
            self._word_length = WORD_LENGTH.FT_BITS_8
        elif str(val) == '7':
            self._word_length = WORD_LENGTH.FT_BITS_7
        else:
            raise ValueError("Word Length must be either 7 or 8")
        self._data_characteristics_set = False

    @property
    def stop_bits(self):
        return self._stop_bits

    @stop_bits.setter
    def stop_bits(self, val):
        if str(val) == '1':
            self._stop_bits = STOP_BITS.FT_STOP_BITS_1
        elif str(val) == '2':
            self._stop_bits = STOP_BITS.FT_STOP_BITS_2
        else:
            raise ValueError("Stop bits must be either 1 or 2")
        self._data_characteristics_set = False

    @property
    def parity(self):
        return self._parity

    @parity.setter
    def parity(self, val):
        try:
            parity = [itm for itm in PARITY.__dict__ if itm.startswith('FT_PARITY') and val.upper() in itm][0]
        except IndexError:
            raise ValueError("Invalid parity: Please select from {}".
                             format(','.join([itm for itm in PARITY.__dict__ if itm.startswith('FT_PARITY')])))
        self._parity = getattr(PARITY, parity)
        self._data_characteristics_set = False

    @property
    def baud_rate(self):
        return self._baud_rate

    @baud_rate.setter
    def baud_rate(self, rate):
        try:
            self.cmd_status.value = ftdI2xx.FT_SetBaudRate(self.handle, DWORD(rate))
            if self.cmd_status.value != FT_STATUS.FT_OK.value:
                raise InstrumentError("FT_SetBaudRate failed")
            self._baud_rate = rate
        except:
            self._baud_rate = None
            raise

    def write_bit_mode(self, mask, validate=False):
        """
            handle; gained from device info
            mask; value to write for the mask
                for BIT_MODE.FT_BITMODE_CBUS_BITBANG
                upper nibble is input (0) output (1)
                lower nibble is pin value low (0) high (1)
            bit_mode; Type BIT_MODE
        """
        self.cmd_status.value = ftdI2xx.FT_SetBitMode(self.handle, UCHAR(mask), self.bit_mode)
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_SetBitMode failed")
        data_bus = UCHAR()
        if validate:
            self.cmd_status.value = ftdI2xx.FT_GetBitMode(self.handle, ctypes.byref(data_bus))
            if self.cmd_status.value != FT_STATUS.FT_OK.value:
                raise InstrumentError("FT_GetBitMode failed")
            return data_bus.value & self.pin_value_mask == mask & self.pin_value_mask

    def get_cbus_pins(self):
        try:
            self.cmd_status.value = ftdI2xx.FT_SetBitMode(self.handle, UCHAR(0), BIT_MODE.FT_BITMODE_CBUS_BITBANG)
            if self.cmd_status.value != FT_STATUS.FT_OK.value:
                raise InstrumentError("FT_SetBitMode failed")
            data_bus = UCHAR()
            self.cmd_status.value = ftdI2xx.FT_GetBitMode(self.handle, ctypes.byref(data_bus))
            if self.cmd_status.value != FT_STATUS.FT_OK.value:
                raise InstrumentError("FT_GetBitMode failed")
        finally:
            self.cmd_status.value = ftdI2xx.FT_SetBitMode(self.handle, UCHAR(self.pin_value_mask), self.bit_mode)
        return data_bus.value
        # self.write_bit_mode(self.pin_value_mask)

    def write(self, data, size=None):
        if not self._data_characteristics_set:
            self._set_data_characteristics()

        if size is None:
            size = len(data)
        buffer = ctypes.create_string_buffer(bytes(data), size)
        bytes_written = DWORD()
        self.cmd_status.value = ftdI2xx.FT_Write(self.handle,
                                                 buffer,
                                                 ctypes.sizeof(buffer),
                                                 ctypes.byref(bytes_written))
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_Write failed")

    def read(self):
        buffer = self._read()
        return buffer.value

    def read_raw(self):
        buffer = self._read()
        return buffer.raw

    def _read(self):
        if not self._data_characteristics_set:
            self._set_data_characteristics()

        amount_in_rx_queue = DWORD()
        amount_in_tx_queue = DWORD()
        status = DWORD()
        self.cmd_status.value = ftdI2xx.FT_GetStatus(self.handle,
                                                     ctypes.byref(amount_in_rx_queue),
                                                     ctypes.byref(amount_in_tx_queue),
                                                     ctypes.byref(status))
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_GetStatus failed")
        buffer = ctypes.create_string_buffer(amount_in_rx_queue.value)
        bytes_read = DWORD()
        self.cmd_status.value = ftdI2xx.FT_Read(self.handle,
                                                ctypes.byref(buffer),
                                                amount_in_rx_queue,
                                                ctypes.byref(bytes_read))
        if self.cmd_status.value != FT_STATUS.FT_OK.value:
            raise InstrumentError("FT_Read failed")
        return buffer

    def _set_data_characteristics(self):
        if not [x for x in [self.word_length, self.stop_bits, self.parity] if x is None]:
            self.cmd_status.value = ftdI2xx.FT_SetDataCharacteristics(self.handle,
                                                                      self.word_length,
                                                                      self.stop_bits,
                                                                      self.parity)
            if self.cmd_status.value != FT_STATUS.FT_OK.value:
                raise InstrumentError("FT_SetDatCharacteristics failed")
            self._data_characteristics_set = True
            return
        raise ValueError("Please ensure that word length, stop bits and parity are set")

    def serial_shift_bit_bang(self, data, bytes_required=None):
        bytes_required = bytes_required or self.bb_bytes
        if self.bit_mode == BIT_MODE.FT_BITMODE_CBUS_BITBANG:
            bit_bang = self._serial_shift_bit_bang(data, bytes_required,
                                                   bb_mask=(self.bb_clk + self.bb_data + self.bb_latch) << 4)
            for byte in bit_bang:
                self.write_bit_mode(byte)
        else:
            bit_bang = self._serial_shift_bit_bang(data, bytes_required, bb_mask=0)
            self.write(bit_bang)

    def configure_bit_bang(self, bit_mode, bytes_required, latch_mask=1, clk_mask=2, data_mask=4, invert_mask=0b000):
        """
        :param bit_mode:
        :param bytes_required:
        :param latch_mask: CBUS Pin for latch. 1 Default for Relay Matrix
        :param clk_mask: CBUS Pin for clock. 2 Default for Relay Matrix
        :param data_mask: CBUS Pin for data. 4 Default for Relay Matrix
        :param invert_mask: Mask for inverting. 0b111 For all inverted 0b000 for all non inverted
        based on MSB 0b<latch><clock><data> LSB
        :return:
        """
        self.bb_bytes = bytes_required
        self.bit_mode = bit_mode
        self.write_bit_mode(self.pin_value_mask)
        self.bb_data = data_mask
        self.bb_clk = clk_mask
        self.bb_latch = latch_mask
        self.bb_inv_mask = 0
        if (1 << 2) & invert_mask:
            self.bb_inv_mask += self.bb_latch
        if (1 << 1) & invert_mask:
            self.bb_inv_mask += self.bb_clk
        if 1 & invert_mask:
            self.bb_inv_mask += self.bb_data

    def _serial_shift_bit_bang(self, data, bytes_required, bb_mask):
        data_out = bytearray()

        data_out.append(bb_mask + self.bb_inv_mask)
        for b in bits(data, num_bytes=bytes_required):
            # Write Data
            if b:
                data_out.append(bb_mask + self.bb_data ^ self.bb_inv_mask)
                # Clock Up
                data_out.append(bb_mask + (self.bb_data + self.bb_clk) ^ self.bb_inv_mask)
            else:
                data_out.append(bb_mask + self.bb_inv_mask)
                # Clock Up
                data_out.append(bb_mask + self.bb_clk ^ self.bb_inv_mask)
        # Latch to output
        data_out.append(bb_mask + self.bb_inv_mask)
        data_out.append(bb_mask + self.bb_latch ^ self.bb_inv_mask)
        data_out.append(bb_mask + self.bb_inv_mask)
        return data_out
