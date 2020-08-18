import struct
import serial

from fixate.drivers.pps import PPS
from fixate.core.exceptions import ParameterError

"""
Communication Protocol
Byte0   Byte1    Byte2    Byte 3-24     Byte 25
0xAA    Address  Command  Command Data  Checksum
        !=0xFF

Status Packet
Byte0   Byte1    Byte2    Byte3         Byte 3-24     Byte 25
0xAA    Address  0x12     Status Byte   Command Data  Checksum
        !=0xFF

Status Byte
0x90 - Checksum incorrect
0xA0 - Parameter incorrect
0xB0 - Unrecognized command
0xC0 - Invalid command
0x80 - Command was successful

Command Byte
0x20 - Setting the remote control mode
0x21 - Setting the output ON/OFF state
0x22 - Setting the maximum output voltage
0x23 - Setting the output voltage
0x24 - Setting the output current
0x25 - Setting the communication address
0x26 - Reading the present operation status of the power supply
0x27 - Enter the calibration mode
0x28 - Reading the calibration mode state
0x29 - Calibrate voltage value
0x2A - Sending the actual output voltage to calibration program
0x2B - Calibrate current value
0x2C - Sending the actual output current to the calibration program
0x2D - Save the calibration data to EEPROM
0x2E - Setting calibration information
0x2F - Reading calibration information
0x31 - Reading product's model, series number and version information
0x32 - Restoring the factory default calibration data
0x37 - Enable the local key
0x12 - The returned status

Command Data is little endian
"""
COMMANDS = (
    (0x20, "Setting the remote control mode"),
    (0x21, "Setting the output ON/OFF state"),
    (0x22, "Setting the maximum output voltage"),
    (0x23, "Setting the output voltage"),
    (0x24, "Setting the output current"),
    (0x25, "Setting the communication address"),
    (0x26, "Reading the present operation status of the power supply"),
    (0x27, "Enter the calibration mode"),
    (0x28, "Reading the calibration mode state"),
    (0x29, "Calibrate voltage value"),
    (0x2A, "Sending the actual output voltage to calibration program"),
    (0x2B, "Calibrate current value"),
    (0x2C, "Sending the actual output current to the calibration program"),
    (0x2D, "Save the calibration data to EEPROM"),
    (0x2E, "Setting calibration information"),
    (0x2F, "Reading calibration information"),
    (0x31, "Reading product's model, series number and version information"),
    (0x32, "Restoring the factory default calibration data"),
    (0x37, "Enable the local key"),
    (0x12, "The returned status)"),
)


class PPSInterface(PPS):
    INSTR_TYPE = "SERIAL"
    REGEX_ID = "model: 6823"
    DATA_BYTE = serial.EIGHTBITS
    STOP_BIT = serial.STOPBITS_ONE
    PARITY = serial.PARITY_NONE
    PACKET_LENGTH = 26
    _baud_rate = None
    instrument = None
    com_port = None
    _baud_rates = [4800, 9600, 19200, 38400]
    connected = False
    attempts = 5  # Command attempts

    def __init__(self, com_port):
        self.com_port = com_port

    def _connect(self):
        self.instrument = serial.Serial(
            port=self.com_port,
            baudrate=self.baud_rate,
            parity=self.PARITY,
            stopbits=self.STOP_BIT,
            bytesize=self.DATA_BYTE,
            timeout=0.5,
        )
        self.connected = True

    @property
    def baud_rate(self):
        return self._baud_rate

    @baud_rate.setter
    def baud_rate(self, val):
        if int(val) in self._baud_rates:
            # Set baud rate
            try:
                self.instrument.close()
            except:
                pass
            self._baud_rate = val
            self._connect()
        else:
            raise ValueError(
                "Baud rate {} one of the specified baud rates {}".format(
                    val, ",".join("{}".format(rate) for rate in self._baud_rates)
                )
            )

    @staticmethod
    def _little_endian_encode(val):
        # Maximum data used in protocol is 4 bytes
        return struct.pack("<I", val)

    @staticmethod
    def _little_endian_decode(val):
        # Maximum data used in protocol is 4 bytes
        data = bytearray(4)
        data[0 : len(val)] = val[:]
        return struct.unpack_from("<I", data)[0]

    def _packet_encode(self, command, *data_tuples):
        """
        :param command: Commands from module listed Command Bytes
        :param data_tuples: (<data as int>, <bytes>) Bytes cannot be greater than 4
        :return: PACKET_LENGTH byte packet for use in sending commands to the power supply
        """
        packet = bytearray(self.PACKET_LENGTH)
        # Start Bit
        packet[0] = 0xAA
        # Address #TODO link to address
        packet[1] = 0x00
        # Command
        packet[2] = command
        packet_index = 3
        for data, num_bytes in data_tuples:
            packet[
                packet_index : packet_index + num_bytes
            ] = self._little_endian_encode(data)[0:num_bytes]
            packet_index += num_bytes
            if packet_index >= self.PACKET_LENGTH:
                raise ValueError("Too many bytes to pack into packet")
        # Checksum
        packet[-1] = self._checksum(packet)
        return packet

    def _packet_decode(self, packet, *data_tuples):
        """
        :param command: Commands from module listed Command Bytes
        :param data_tuples: (<data name>, <bytes>) Bytes cannot be greater than 4
        :return: Dictionary for accessing the packet elements by name (lowercase)
        """
        if packet[-1] != self._checksum(packet):
            raise IOError("Invalid Checksum on packet")
        data = {}
        # Start Bit
        data["start"] = packet[0]
        # Address
        data["address"] = packet[1]
        # Command
        data["command"] = packet[2]
        packet_index = 3
        for name, num_bytes in data_tuples:
            data[name] = self._little_endian_decode(
                packet[packet_index : packet_index + num_bytes]
            )
            packet_index += num_bytes
            if packet_index >= self.PACKET_LENGTH:
                raise ValueError("Too many data values to unpack from packet")
        # Checksum
        data["checksum"] = packet[-1]
        return data

    def _checksum(self, data):
        if len(data) != self.PACKET_LENGTH:
            raise ValueError(
                "Checksum cannot be calculated on data length {}".format(len(data))
            )
        return sum(data[:-1]) % 256

    def communicate(self, command, *data_tuples):
        packet = self._packet_encode(command, *data_tuples)
        # Flush read buffer
        self.instrument.flushInput()
        x = 0
        while True:
            x += 1
            try:
                self._send(packet)
                recv = self._read()
                self._validate(recv)
                return recv
            except IOError:
                if x == self.attempts:
                    raise

    def _send(self, packet):
        self.instrument.write(packet)

    def _read(self):
        return self.instrument.read(26)

    def _validate(self, packet):
        if len(packet) == 26:
            if packet[-1] != self._checksum(packet):
                raise IOError("Invalid checksum on packet received from power supply")
            if packet[2] == 0x12:
                # status packet
                if packet[3] == 0x90:
                    raise IOError("Invalid checksum on packet to power supply")
                if packet[3] == 0xA0:
                    raise IOError("Invalid Parameter sent to power supply")
                if packet[3] == 0xB0:
                    raise IOError("Unrecognised Command sent to power supply")
                if packet[3] == 0xC0:
                    raise IOError("Invalid Command sent to power supply")
                if packet[3] != 0x80:
                    raise IOError("Invalid status return byte")
        else:
            raise IOError("No returning packet found")

    def get_identity(self):
        pass


class BK178X(PPSInterface):
    REGEX_ID = "model: 6823"
    _output_ch1 = None
    _remote = None
    _voltage_max = None
    _address = 0

    @property
    def remote(self):
        return self._remote

    @remote.setter
    def remote(self, val):
        if val not in [True, False]:
            raise ParameterError("remote must be True or False")
        self.communicate(0x20, (val, 1))
        self._remote = val

    @property
    def output_ch1(self):
        return self._output_ch1

    @output_ch1.setter
    def output_ch1(self, val):
        if val not in [True, False]:
            raise ParameterError("{} not True or False".format(val))
        self.communicate(0x21, (val, 1))
        self._output_ch1 = val

    @property
    def voltage_max(self):
        return self._voltage_max

    @voltage_max.setter
    def voltage_max(self, val):
        # Convert volts to millivolts
        val = round(val, 2) * 1000
        self.communicate(0x22, (val, 4))

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, val):
        # Convert volts to millivolts
        val = int(round(val, 2) * 1000)
        self.communicate(0x23, (val, 4))
        self._voltage = val

    @property
    def current_max(self):
        return self._current_max

    @current_max.setter
    def current_max(self, val):
        # Convert amps to milliamps
        val = int(round(val, 2) * 1000)
        self.communicate(0x24, (val, 2))
        self._current_max = val

    @property
    def calibration_info(self):
        packet = self.communicate(0x2F)
        return "".join(chr(i) for i in packet[3:23] if i != 0x00)

    @calibration_info.setter
    def calibration_info(self, val):
        if val in [str] and len(val) < 20:
            info = [ord(c) for c in val]
            self.communicate(0x2E, (info, 20))

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, val):
        self.communicate(0x25, (val, 1))
        self._address = val

    def read(self):
        packet = self.communicate(0x26)
        data = self._packet_decode(
            packet,
            ("current", 2),
            ("voltage", 4),
            ("status", 1),
            ("current_limit", 2),
            ("voltage_max", 4),
            ("voltage_setting", 4),
        )
        data["output"] = data["status"] & 1
        data["over_heat"] = data["status"] & (1 << 1)
        data["current"] /= 1000
        data["voltage"] /= 1000
        data["voltage_max"] /= 1000
        data["voltage_setting"] /= 1000
        data["current_limit"] /= 1000
        output_mode = (data["status"] & (0b11 << 2)) >> 2
        if output_mode == 1:
            output_mode = "CV"
        elif output_mode == 2:
            output_mode = "CC"
        else:
            output_mode = "UNREG"
        data["output_mode"] = output_mode
        data["fan_speed"] = (data["status"] & (0b111 << 4)) >> 4
        data["remote"] = (data["status"] & 1 << 7) >> 7
        return data

    def identify(self, as_string=False):
        packet = self.communicate(0x31)
        data = self._packet_decode(packet, ("model", 4), ("software_version", 2))
        data["model"] = "".join(chr(i) for i in packet[3:8] if i != 0x00)
        data["serial_number"] = "".join(chr(i) for i in packet[10:20] if i != 0x00)
        ret_val = data
        if as_string:
            ret_val = ""
            for key, value in sorted(data.items()):
                ret_val += "{}: {},".format(key, value)
        return ret_val

    def get_identity(self) -> str:
        """
        ['address: 0,
        checksum: 40,
        command: 49,
        model: 6823,
        serial_number: 3697210019,
        software_version: 29440,
        start: 170,', '9600']
        :return:
        """
        return self.identify(as_string=True)
