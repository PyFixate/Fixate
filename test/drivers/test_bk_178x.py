from unittest import TestCase
import unittest
import serial
import sys
from fixate.drivers.pps.bk_178x import BK178X

out = sys.stdout
nl = '\n'

@unittest.skip("Requires instrument connected to run")
class PacketFormedCorrectly(TestCase):
    length_packet = 26

    def setUp(self):
        self.test_cls = BK178X(None)
        self.test_cls.address = 0

    def _build_byte_array(self, iterable):
        return ''.join(chr(i) for i in iterable)

    def _calculate_checksum(self, cmd):
        assert ((len(cmd) == self.length_packet - 1) or (len(cmd) == self.length_packet))
        checksum = 0
        for i in range(self.length_packet - 1):
            checksum += ord(cmd[i])
        checksum %= 256
        return checksum

    def test_max_voltage_command(self):
        """
        Known command to work with powersupply
        :return:
        """
        max_voltage_5_command = bytearray(26)
        max_voltage_5_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        max_voltage_5_command[-1] = 0x67
        self.assertTrue(self.test_cls.CommandProperlyFormed(self._build_byte_array(max_voltage_5_command)))

    def test_checksum(self):
        """Return the sum of the bytes in cmd modulo 256.
        """
        max_voltage_5_command = bytearray(26)
        max_voltage_5_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        max_voltage_5_command[-1] = 0x67
        self.assertEqual(self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command[:-1])), 0x67)
        max_voltage_5_command[0] = 0x00
        self.assertEqual(self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command[:-1])), 0xbd)
        self.assertEqual(self.test_cls.CalculateChecksum(self._build_byte_array([0x00] * 25)), 0x00)
        # Test that it ignores the last element if it is a full length packet
        max_voltage_5_command[-1] = 0x67
        self.assertEqual(self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command)), 0xbd)
        max_voltage_5_command[-1] = 0xbd
        self.assertEqual(self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command)), 0xbd)

    def test_start_byte(self):
        max_voltage_5_command = bytearray(26)
        max_voltage_5_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        max_voltage_5_command[-1] = 0x67
        for x in range(170):
            max_voltage_5_command[0] = x
            max_voltage_5_command[-1] = self.test_cls.CalculateChecksum(
                self._build_byte_array(max_voltage_5_command[:-1]))
            self.assertFalse(self.test_cls.CommandProperlyFormed(self._build_byte_array(max_voltage_5_command)))
        max_voltage_5_command[0] = 170
        max_voltage_5_command[-1] = self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command[:-1]))
        self.assertTrue(self.test_cls.CommandProperlyFormed(self._build_byte_array(max_voltage_5_command)))

    def test_address(self):
        command = bytearray(26)
        max_voltage_5_command = command
        max_voltage_5_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        max_voltage_5_command[-1] = 0x67
        for x in range(0xff):
            max_voltage_5_command[1] = x
            max_voltage_5_command[-1] = self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command))
            self.assertTrue(self.test_cls.CommandProperlyFormed(self._build_byte_array(max_voltage_5_command)))
        max_voltage_5_command[1] = 0xff
        max_voltage_5_command[-1] = self.test_cls.CalculateChecksum(self._build_byte_array(max_voltage_5_command))
        self.assertFalse(self.test_cls.CommandProperlyFormed(self._build_byte_array(max_voltage_5_command)))

    def test_commands(self):
        test_command = bytearray(26)
        test_command[0] = 0xaa
        test_command[-1] = self.test_cls.CalculateChecksum(self._build_byte_array(test_command))
        commands = (
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
            0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x31, 0x32, 0x37, 0x12
        )
        for x in range(0xff):
            test_command[2] = x
            test_command[-1] = self.test_cls.CalculateChecksum(self._build_byte_array(test_command))
            self.assertEqual(self.test_cls.CommandProperlyFormed(self._build_byte_array(test_command)), x in commands)

    def test_command_checksum(self):
        test_command = bytearray(26)
        test_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        for y in range(0xff):
            test_command[3] = y
            for x in range(0xff):
                test_command[-1] = x
                test_resp = x == self.test_cls.CalculateChecksum(self._build_byte_array(test_command))
                self.assertEqual(self.test_cls.CommandProperlyFormed(self._build_byte_array(test_command)), test_resp)


class BKPS178xInterface(TestCase):
    length_packet = 26

    def setUp(self):
        self.test_cls = BK178X(None)
        self.test_cls._address = 0

    def _build_byte_array(self, iterable):
        return ''.join(chr(i) for i in iterable).encode()

    def _command_properly_formed(self, cmd):
        '''Return 1 if a command is properly formed; otherwise, return 0.
        '''
        commands = (
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
            0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x31, 0x32, 0x37, 0x12
        )
        # Must be proper length
        if len(cmd) != self.length_packet:
            # out("Command length = " + str(len(cmd)) + "-- should be " + \
            # str(self.length_packet) + nl)
            return 0
        # First character must be 0xaa
        if cmd[0] != 0xaa:
            # out("First byte should be 0xaa" + nl)
            return 0
        # Second character (address) must not be 0xff
        if cmd[1] == 0xff:
            # out("Second byte cannot be 0xff" + nl)
            return 0
        # Third character must be valid command
        if cmd[2] not in commands:
            # out("Third byte not a valid command:  %s\n" % byte3)
            return 0
        # Calculate checksum and validate it
        checksum = self._calculate_checksum(cmd)
        if checksum != cmd[-1]:
            # out("Incorrect checksum" + nl)
            return 0
        return 1

    def _calculate_checksum(self, cmd):
        '''Return the sum of the bytes in cmd modulo 256.
        '''
        assert ((len(cmd) == self.length_packet - 1) or (len(cmd) == self.length_packet))
        return sum(cmd[:-1]) % 256

    def test_command_properly_formed(self):
        command = bytearray(26)
        max_voltage_5_command = command
        max_voltage_5_command[0:5] = [0xaa, 0x00, 0x22, 0x88, 0x13]
        max_voltage_5_command[-1] = 0x67
        self.assertTrue(self._command_properly_formed(max_voltage_5_command))
        max_voltage_5_command[0] = 0xab
        self.assertFalse(self._command_properly_formed(max_voltage_5_command))

    def test_little_endian_encode(self):
        self.assertEqual(self.test_cls._little_endian_encode(5)[0], 5)
        self.assertEqual(self.test_cls._little_endian_encode(5)[:], b'\x05\x00\x00\x00')
        self.assertEqual(self.test_cls._little_endian_encode(1 << 8)[:], b'\x00\x01\x00\x00')
        self.assertEqual(self.test_cls._little_endian_encode(1 << 8)[1], 1)
        self.assertEqual(self.test_cls._little_endian_encode(1 << 16)[:], b'\x00\x00\x01\x00')
        self.assertEqual(self.test_cls._little_endian_encode(1 << 16)[2], 1)
        self.assertEqual(self.test_cls._little_endian_encode(1 << 24)[:], b'\x00\x00\x00\x01')
        self.assertEqual(self.test_cls._little_endian_encode(1 << 24)[3], 1)
        self.assertEqual(self.test_cls._little_endian_encode((1 << 32) - 1)[:], b'\xff\xff\xff\xff')

    def test_little_endian_decode(self):
        self.assertEqual(self.test_cls._little_endian_decode(self.test_cls._little_endian_encode((1 << 32) - 1)),
                         (1 << 32) - 1)
        self.assertEqual(self.test_cls._little_endian_decode(self.test_cls._little_endian_encode(0xAABBCCDD)),
                         0xAABBCCDD)
        for x in range(32):
            self.assertEqual(self.test_cls._little_endian_decode(self.test_cls._little_endian_encode(1 << x)),
                             1 << x)

    def test_packet_encode(self):
        command = bytearray(26)
        command[0:3] = [0xaa, 0x00, 0x26]
        command[-1] = sum(command[:-1]) % 256
        self.assertEqual(self.test_cls._packet_encode(0x26), command)
        command[3] = 0xFF
        command[-1] = sum(command[:-1]) % 256
        self.assertEqual(self.test_cls._packet_encode(0x26, (0xFF, 1)), command)
        command[4] = 0xAA
        command[6] = 0xBB
        command[-1] = sum(command[:-1]) % 256
        self.assertEqual(self.test_cls._packet_encode(0x26, (0xFF, 1), (0xAA, 2), (0xBB, 1)), command)

    def test_packet_decode(self):
        command = bytearray(26)
        command[0:3] = [0xaa, 0x00, 0x26]
        command[-1] = sum(command[:-1]) % 256
        decoded = self.test_cls._packet_decode(self.test_cls._packet_encode(0x26))
        self.assertEqual(decoded, {"command": 0x26, "address": 0x00, "start": 0xAA, "checksum": command[-1]})
        command[3] = 0xFF
        command[-1] = sum(command[:-1]) % 256
        decoded = self.test_cls._packet_decode(self.test_cls._packet_encode(0x26, (0xFF, 1)), ("my0xff", 1))
        self.assertEqual(decoded, {"command": 0x26, "address": 0x00, "start": 0xAA, "checksum": command[-1],
                                   "my0xff": 0xFF})
        command[4:5] = [0xAA, 0xBB]
        command[6] = 0xCC
        command[-1] = sum(command[:-1]) % 256
        decoded = self.test_cls._packet_decode(self.test_cls._packet_encode(0x26, (0xFF, 1), (0xAABB, 2), (0xCC, 4)),
                                               ("my0xff", 1), ("my0xaabb", 2), ("my0xcc", 4))
        self.assertEqual(decoded, {"command": 0x26, "address": 0x00, "start": 0xAA, "checksum": command[-1],
                                   "my0xff": 0xFF, "my0xaabb": 0xAABB, "my0xcc": 0xCC})


class InstrumentInterface:
    '''Provides the interface to a 26 byte instrument along with utility
    functions.
    '''
    debug = 0  # Set to 1 to see dumps of commands and responses
    length_packet = 26  # Number of bytes in a packet
    convert_current = 1e3  # Convert current in A to 1 mA
    convert_voltage = 1e3  # Convert voltage in V to mV
    convert_power = 1e3  # Convert power in W to mW
    # Number of settings storage registers
    lowest_register = 1
    highest_register = 25

    def Initialize(self, com_port, baudrate, address=0):
        self.sp = serial.Serial(com_port, baudrate)
        self.address = address

    def DumpCommand(self, bytes):
        '''Print out the contents of a 26 byte command.  Example:
            aa .. 20 01 ..   .. .. .. .. ..
            .. .. .. .. ..   .. .. .. .. ..
            .. .. .. .. ..   cb
        '''
        assert (len(bytes) == self.length_packet)
        header = " " * 3
        out(header)
        for i in range(self.length_packet):
            if i % 10 == 0 and i != 0:
                out(nl + header)
            if i % 5 == 0:
                out(" ")
            s = "%02x" % ord(bytes[i])
            if s == "00":
                # Use the decimal point character if you see an
                # unattractive printout on your machine.
                # s = "."*2
                # The following alternate character looks nicer
                # in a console window on Windows.
                s = chr(250) * 2
            out(s)
        out(nl)

    def CommandProperlyFormed(self, cmd):
        '''Return 1 if a command is properly formed; otherwise, return 0.
        '''
        commands = (
            0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29,
            0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x31, 0x32, 0x37, 0x12
        )
        # Must be proper length
        if len(cmd) != self.length_packet:
            out("Command length = " + str(len(cmd)) + "-- should be " + \
                str(self.length_packet) + nl)
            return 0
        # First character must be 0xaa
        if ord(cmd[0]) != 0xaa:
            out("First byte should be 0xaa" + nl)
            return 0
        # Second character (address) must not be 0xff
        if ord(cmd[1]) == 0xff:
            out("Second byte cannot be 0xff" + nl)
            return 0
        # Third character must be valid command
        byte3 = "%02X" % ord(cmd[2])
        if ord(cmd[2]) not in commands:
            out("Third byte not a valid command:  %s\n" % byte3)
            return 0
        # Calculate checksum and validate it
        checksum = self.CalculateChecksum(cmd)
        if checksum != ord(cmd[-1]):
            out("Incorrect checksum" + nl)
            return 0
        return 1

    def CalculateChecksum(self, cmd):
        '''Return the sum of the bytes in cmd modulo 256.
        '''
        assert ((len(cmd) == self.length_packet - 1) or (len(cmd) == self.length_packet))
        checksum = 0
        for i in range(self.length_packet - 1):
            checksum += ord(cmd[i])
        checksum %= 256
        return checksum

    def StartCommand(self, byte):
        return chr(0xaa) + chr(self.address) + chr(byte)

    def SendCommand(self, command):
        '''Sends the command to the serial stream and returns the 26 byte
        response.
        '''
        assert (len(command) == self.length_packet)
        self.sp.write(command)
        response = self.sp.read(self.length_packet)
        assert (len(response) == self.length_packet)
        return response

    def ResponseStatus(self, response):
        '''Return a message string about what the response meant.  The
        empty string means the response was OK.
        '''
        responses = {
            0x90: "Wrong checksum",
            0xA0: "Incorrect parameter value",
            0xB0: "Command cannot be carried out",
            0xC0: "Invalid command",
            0x80: "",
        }
        assert (len(response) == self.length_packet)
        assert (ord(response[2]) == 0x12)
        return responses[ord(response[3])]

    def CodeInteger(self, value, num_bytes=4):
        '''Construct a little endian string for the indicated value.  Two
        and 4 byte integers are the only ones allowed.
        '''
        assert (num_bytes == 1 or num_bytes == 2 or num_bytes == 4)
        value = int(value)  # Make sure it's an integer
        s = chr(value & 0xff)
        if num_bytes >= 2:
            s += chr((value & (0xff << 8)) >> 8)
            if num_bytes == 4:
                s += chr((value & (0xff << 16)) >> 16)
                s += chr((value & (0xff << 24)) >> 24)
                assert (len(s) == 4)
        return s

    def DecodeInteger(self, str):
        '''Construct an integer from the little endian string. 1, 2, and 4 byte
        strings are the only ones allowed.
        '''
        assert (len(str) == 1 or len(str) == 2 or len(str) == 4)
        n = ord(str[0])
        if len(str) >= 2:
            n += (ord(str[1]) << 8)
            if len(str) == 4:
                n += (ord(str[2]) << 16)
                n += (ord(str[3]) << 24)
        return n

    def GetReserved(self, num_used):
        '''Construct a string of nul characters of such length to pad a
        command to one less than the packet size (leaves room for the
        checksum byte.
        '''
        num = self.length_packet - num_used - 1
        assert (num > 0)
        return chr(0) * num

    def PrintCommandAndResponse(self, cmd, response, cmd_name):
        '''Print the command and its response if debugging is on.
        '''
        assert (cmd_name)
        if self.debug:
            out(cmd_name + " command:" + nl)
            self.DumpCommand(cmd)
            out(cmd_name + " response:" + nl)
            self.DumpCommand(response)

    def GetCommand(self, command, value, num_bytes=4):
        '''Construct the command with an integer value of 0, 1, 2, or
        4 bytes.
        '''
        cmd = self.StartCommand(command)
        if num_bytes > 0:
            r = num_bytes + 3
            cmd += self.CodeInteger(value)[:num_bytes] + self.Reserved(r)
        else:
            cmd += self.Reserved(0)
        cmd += chr(self.CalculateChecksum(cmd))
        assert (self.CommandProperlyFormed(cmd))
        return cmd

    def GetData(self, data, num_bytes=4):
        '''Extract the little endian integer from the data and return it.
        '''
        assert (len(data) == self.length_packet)
        if num_bytes == 1:
            return ord(data[3])
        elif num_bytes == 2:
            return self.DecodeInteger(data[3:5])
        elif num_bytes == 4:
            return self.DecodeInteger(data[3:7])
        else:
            raise Exception("Bad number of bytes:  %d" % num_bytes)

    def Reserved(self, num_used):
        assert (num_used >= 3 and num_used < self.length_packet - 1)
        return chr(0) * (self.length_packet - num_used - 1)

    def SendIntegerToPS(self, byte, value, msg, num_bytes=4):
        '''Send the indicated command along with value encoded as an integer
        of the specified size.  Return the instrument's response status.
        '''
        cmd = self.GetCommand(byte, value, num_bytes)
        response = self.SendCommand(cmd)
        self.PrintCommandAndResponse(cmd, response, msg)
        return self.ResponseStatus(response)

    def GetIntegerFromPS(self, cmd_byte, msg, num_bytes=4):
        '''Construct a command from the byte in cmd_byte, send it, get
        the response, then decode the response into an integer with the
        number of bytes in num_bytes.  msg is the debugging string for
        the printout.  Return the integer.
        '''
        assert (num_bytes == 1 or num_bytes == 2 or num_bytes == 4)
        cmd = self.StartCommand(cmd_byte)
        cmd += self.Reserved(3)
        cmd += chr(self.CalculateChecksum(cmd))
        assert (self.CommandProperlyFormed(cmd))
        response = self.SendCommand(cmd)
        self.PrintCommandAndResponse(cmd, response, msg)
        return self.DecodeInteger(response[3:3 + num_bytes])

    def Dec2Bin(self, number):
        '''convert dec integer to binary string bStr'''
        bStr = ''
        if number < 0:
            raise ValueError("must be a positive integer")
        if number == 0:
            return '0'
        while number > 0:
            bStr = str(number % 2) + bStr
            number = number >> 1
        return bStr

    def StateBinStr(self, binStr):
        if binStr[0] == "0":
            op_mode = "Front Panel"
        else:
            op_mode = "Remote Control"

        if binStr[1:4] == "000":
            fan = "off"
        elif binStr[1:4] == "001":
            fan = "1"
        elif binStr[1:4] == "010":
            fan = "2"
        elif binStr[1:4] == "011":
            fan = "3"
        elif binStr[1:4] == "100":
            fan = "4"
        elif binStr[1:4] == "101":
            fan = "5"

        if binStr[4:6] == "00":
            outp_mode = "Off"
        elif binStr[4:6] == "01":
            outp_mode = "CV"
        elif binStr[4:6] == "10":
            outp_mode = "CC"
        elif binStr[4:6] == "11":
            outp_mode = "Unreg"

        if binStr[6] == "0":
            heat_pro = "Normal"
        else:
            heat_pro = "Abnormal"

        if binStr[7] == "0":
            out_state = "OFF"
        else:
            out_state = "ON"
        stateStr = ["   Operation Mode: " + str(op_mode), "   Fan Speed: " + str(fan),
                    "   Output Mode: " + str(outp_mode), "   Over heat protection: " + str(heat_pro),
                    "   Output State: " + str(out_state)]
        return '\t'.join(stateStr)