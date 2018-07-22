import time
from amptest.drivers.pps import PPS
from amptest.lib.exceptions import ParameterError, InstrumentError


class SPD3303X(PPS):
    REGEX_ID = "3303X"
    INSTR_TYPE = "VISA"
    write_termination = "\n"
    read_termination = "\n"

    def __init__(self, instrument):
        self.instrument = instrument
        # (<api command>, <write or query>, <command>)
        self.api = [
            # Save commands
            ("save.group1", self.write, "*SAV 1"),
            ("save.group2", self.write, "*SAV 2"),
            ("save.group3", self.write, "*SAV 3"),
            ("save.group4", self.write, "*SAV 4"),
            ("save.group5", self.write, "*SAV 5"),
            # Recall commands
            ("recall.group1", self.write, "*RCL 1"),
            ("recall.group2", self.write, "*RCL 2"),
            ("recall.group3", self.write, "*RCL 3"),
            ("recall.group4", self.write, "*RCL 4"),
            ("recall.group5", self.write, "*RCL 5"),
            # Channel 1 Commands
            ("channel1.voltage", self.write, "CH1:VOLT {value}"),
            ("channel1.current", self.write, "CH1:CURR {value}"),
            ("channel1.off", self.write, "OUTPut CH1,OFF"),
            ("channel1.on", self.write, "OUTPut CH1,ON"),
            ("channel1.wave.on", self.write, "OUTPut:WAVE CH1,ON"),
            ("channel1.wave.off", self.write, "OUTPut:WAVE CH1,OFF"),
            ("channel1.timer.set.group1", self.write, "TIMEr:SET CH1,1,{voltage},{current},{time}"),
            ("channel1.timer.set.group2", self.write, "TIMEr:SET CH1,2,{voltage},{current},{time}"),
            ("channel1.timer.set.group3", self.write, "TIMEr:SET CH1,3,{voltage},{current},{time}"),
            ("channel1.timer.set.group4", self.write, "TIMEr:SET CH1,4,{voltage},{current},{time}"),
            ("channel1.timer.set.group5", self.write, "TIMEr:SET CH1,5,{voltage},{current},{time}"),
            ("channel1.timer.on()", self.write, "TIMEr CH1,ON;"),
            ("channel1.timer.off()", self.write, "TIMEr CH1,OFF;"),
            # Channel 2 Commands
            ("channel2.voltage", self.write, "CH1:VOLT {value}"),
            ("channel2.current", self.write, "CH1:CURR {value}"),
            ("channel2.off", self.write, "OUTPut CH2,OFF"),
            ("channel2.on", self.write, "OUTPut CH2,ON"),
            ("channel2.wave.on", self.write, "OUTPut:WAVE CH1,ON"),
            ("channel2.wave.off", self.write, "OUTPut:WAVE CH1,OFF"),
            ("channel2.timer.set.group1", self.write, "TIMEr:SET CH2,1,{voltage},{current},{time}"),
            ("channel2.timer.set.group2", self.write, "TIMEr:SET CH2,2,{voltage},{current},{time}"),
            ("channel2.timer.set.group3", self.write, "TIMEr:SET CH2,3,{voltage},{current},{time}"),
            ("channel2.timer.set.group4", self.write, "TIMEr:SET CH2,4,{voltage},{current},{time}"),
            ("channel2.timer.set.group5", self.write, "TIMEr:SET CH2,5,{voltage},{current},{time}"),
            ("channel2.timer.on()", self.write, "TIMEr CH2,ON;"),
            ("channel2.timer.off()", self.write, "TIMEr CH2,OFF;"),
            # Output Setting Commands
            ("output.independent", self.write, "OUTPut:TRACK 0"),
            ("output.series", self.write, "OUTPut:TRACK 1"),
            ("output.parallel", self.write, "OUTPut:TRACK 2"),
            # Address Setting Commands
            ("address.ip", self.write, "IPaddr {value}"),
            ("address.mask", self.write, "MASKaddr {value}"),
            ("address.gate", self.write, "GATEaddr {value}"),
            ("address.dhcp.on", self.write, "DHCP ON"),
            ("address.dhcp.off", self.write, "DHCP OFF"),

            ("idn", self.query_value, "*IDN?"),
            # Channel 1 Measuring
            ("channel1.measure.current", self.query_value, "MEAS:CURRent? CH1"),
            ("channel1.measure.voltage", self.query_value, "MEAS:VOLTage? {CH1}"),
            ("channel1.measure.power", self.query_value, "MEAS:POWEr? {CH1}"),
            ("channel1.timer.get.group1", self.query_value, "TIMEr:SET? CH1,1"),
            ("channel1.timer.get.group2", self.query_value, "TIMEr:SET? CH1,2"),
            ("channel1.timer.get.group3", self.query_value, "TIMEr:SET? CH1,3"),
            ("channel1.timer.get.group4", self.query_value, "TIMEr:SET? CH1,4"),
            ("channel1.timer.get.group5", self.query_value, "TIMEr:SET? CH1,5"),
            ("channel1.current.get", self.query_value, "CH1 CURRent?"),
            ("channel1.voltage.get", self.query_value, "CH1 VOLTage?"),
            # Channel 2 Measuring
            ("channel2.measure.current", self.query_value, "MEAS:CURRent? CH2"),
            ("channel2.measure.voltage", self.query_value, "MEAS:VOLTage? {CH2}"),
            ("channel2.measure.power", self.query_value, "MEAS:POWEr? {CH2}"),
            ("channel2.timer.get.group1", self.query_value, "TIMEr:SET? CH1,1"),
            ("channel2.timer.get.group2", self.query_value, "TIMEr:SET? CH1,2"),
            ("channel2.timer.get.group3", self.query_value, "TIMEr:SET? CH1,3"),
            ("channel2.timer.get.group4", self.query_value, "TIMEr:SET? CH1,4"),
            ("channel2.timer.get.group5", self.query_value, "TIMEr:SET? CH1,5"),
            ("channel1.current.get", self.query_value, "CH1 CURRent?"),
            ("channel1.voltage.get", self.query_value, "CH1 VOLTage?"),
            ("", self.query_value, ""),
            ("", self.query_value, ""),

        ]

    def query_value(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        return self.query_ascii_value(formatted_string)

    def query_ascii_values(self, value):
        response = self.instrument.query_ascii_values(value)
        self._is_error()
        return response

    def query_ascii_value(self, value):
        return self.query_ascii_values(value)[0]

    def write(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        self._write(formatted_string)

    def _format_string(self, base_str, **kwargs):
        kwargs['self'] = self
        prev_string = base_str
        cur_string = ""
        while True:
            cur_string = prev_string.format(**kwargs)
            if cur_string == prev_string:
                break
            prev_string = cur_string
        return cur_string

    @property
    def remote(self):
        pass

    @remote.setter
    def remote(self, val):
        if val not in [True, False]:
            raise ParameterError("remote must be True or False")

    @property
    def output_ch1(self):
        return self.instrument.query_ascii_values("")

    @output_ch1.setter
    def output_ch1(self, val):
        if val not in [True, False]:
            raise ParameterError("{} not True or False".format(val))
        state = "OFF"
        if val:
            state = "ON"
        self._write("OUTP CH1,{}".format(state))

    @property
    def voltage_max(self):
        pass

    @voltage_max.setter
    def voltage_max(self, val):
        pass

    @property
    def voltage(self):
        return self._read_value("MEAS:VOLT? CH1")

    @voltage.setter
    def voltage(self, val):
        self._write("CH1:VOLT {}".format(val))

    @property
    def current_max(self):
        pass

    @current_max.setter
    def current_max(self, val):
        pass

    def _read_value(self, data):
        values = self.instrument.query_ascii_values(data)
        self._is_error()
        return values[0]

    def _write(self, data):
        """
        The DG1022 cannot respond to visa commands as quickly as some other devices
        A 100ms delay was found to be reliable for most commands with the exception of the *IDN?
        identification command. An extra 100ms should be allowed for explicit calls to *IDN?
        Note:
        The 6000 number for the sleep is derived from trial and error. The write calls don't seem to block at the rate
        they write. By allowing 166uS delay for each byte of data then the Funcgen doesn't choke on the next call. A
        flat 100ms is added to allow processing time.
        This is especially important for commands that write large amounts of data such as user arbitrary forms.
        """
        self.instrument.write(data)
        self._is_error()

    def _check_errors(self):
        resp = self.instrument.query("SYST:ERR?")
        code, msg = resp.strip('\n').split(',')
        code = int(code)
        msg = msg.strip('"')
        return code, msg

    def _is_error(self, silent=False):
        errors = []
        while True:
            code, msg = self._check_errors()
            if code != 0:
                errors.append((code, msg))
            else:
                break
        if errors:
            if silent:
                return errors
            else:
                raise InstrumentError("Error(s) Returned from PPS\n" +
                                      "\n".join(["Code: {}\nMessage:{}".format(code, msg) for code, msg in errors]))
