import time
from fixate.drivers.pps import PPS
from fixate.core.exceptions import ParameterError, InstrumentError
from functools import update_wrapper
import inspect
import re


class SPD3303X(PPS):
    REGEX_ID = "3303X"
    INSTR_TYPE = "VISA"
    write_termination = "\n"
    read_termination = "\n"

    def __init__(self, instrument):
        super().__init__(instrument)
        self.instrument = instrument
        self.instrument.timeout = 1000
        # 100ms query delay recommended - some forum discussion says 300ms more robust
        self.instrument.query_delay = 0.1
        self.instrument.read_termination = self.read_termination
        self.instrument.write_termination = self.write_termination
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
            ("channel1.voltage", self.write, "OUTPut:TRACK 0;CH1:VOLT {value}"),
            ("channel1.current", self.write, "OUTPut:TRACK 0;CH1:CURR {value}"),
            ("channel1._call", self.write, "OUTPut:TRACK 0;OUTPut CH1,{value}"),
            ("channel1.wave", self.write, "OUTPut:TRACK 0;OUTPut:WAVE CH1,{value}"),
            # TODO Need to initialise all groups (1-5) to 0 V, A, s before setting the ones you need
            (
                "channel1.timer.set_waveform",
                self.write_timer,
                "OUTPut:TRACK 0;TIMEr:SET CH1,{group},{voltage},{current},{duration}",
            ),
            ("channel1.timer._call", self.write, "OUTPut:TRACK 0;TIMEr CH1,{value}"),
            # Channel 2 Commands
            ("channel2.voltage", self.write, "OUTPut:TRACK 0;CH2:VOLT {value}"),
            ("channel2.current", self.write, "OUTPut:TRACK 0;CH2:CURR {value}"),
            ("channel2._call", self.write, "OUTPut:TRACK 0;OUTPut CH2,{value}"),
            ("channel2.wave", self.write, "OUTPut:TRACK 0;OUTPut:WAVE CH2,{value}"),
            # TODO Need to initialise all groups (1-5) to 0 V, A, s before setting the ones you need
            (
                "channel2.timer.set_waveform",
                self.write_timer,
                "OUTPut:TRACK 0;TIMEr:SET CH2,{group},{voltage},{current},{duration}",
            ),
            ("channel2.timer._call", self.write, "OUTPut:TRACK 0;TIMEr CH2,{value}"),
            # Output Setting Commands
            (
                "series._call",
                self.write,
                "OUTPut:TRACK 1;OUTPut:TRACK 1;OUTPut CH1,{value}",
            ),
            ("series.voltage", self.write_half, "OUTPut:TRACK 1;CH1:VOLT {value}"),
            ("series.current", self.write, "OUTPut:TRACK 1;CH1:CURR {value}"),
            (
                "parallel._call",
                self.write,
                "OUTPut:TRACK 2;OUTPut:TRACK 2;OUTPut CH1,{value}",
            ),
            ("parallel.voltage", self.write, "OUTPut:TRACK 2;CH1:VOLT {value}"),
            ("parallel.current", self.write_half, "OUTPut:TRACK 2;CH1:CURR {value}"),
            # Address Setting Commands
            ("address.ip", self.write, "IPaddr {value}"),
            ("address.mask", self.write, "MASKaddr {value}"),
            ("address.gate", self.write, "GATEaddr {value}"),
            ("address.dhcp", self.write, "DHCP {value}"),
            # Channel 1 Measuring
            ("channel1.measure.current", self.query_value, "MEAS:CURRent? CH1"),
            ("channel1.measure.voltage", self.query_value, "MEAS:VOLTage? CH1"),
            ("channel1.measure.power", self.query_value, "MEAS:POWEr? CH1"),
            # Channel 2 Measuring
            ("channel2.measure.current", self.query_value, "MEAS:CURRent? CH2"),
            ("channel2.measure.voltage", self.query_value, "MEAS:VOLTage? CH2"),
            ("channel2.measure.power", self.query_value, "MEAS:POWEr? CH2"),
        ]
        self.init_api()

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

    def write_timer(self, base_str, waveform):

        if len(waveform) > 5:
            raise ValueError(
                "Error: Too many points in waveform. Waveform must have 5 or fewer points"
            )
        # We need to set the remaining waveforms to blank so that the previous values are initialised to 0
        blank = [[0, 0, 0] for _ in range(5 - len(waveform))]

        waveform.extend(blank)
        for group, wave in enumerate(waveform, start=1):
            voltage, current, duration = wave
            formatted_string = base_str.format(
                group=group, voltage=voltage, current=current, duration=duration
            )
            self._write(formatted_string)

    def write_half(self, base_str, value):
        formatted_string = self._format_string(base_str, value=value / 2)
        self._write(formatted_string)

    def _format_string(self, base_str, **kwargs):
        kwargs["self"] = self
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
        The SPD3303X cannot respond to visa commands as quickly as some other devices
        A 20ms delay was found to be reliable for most commands.
        Note:
        The 6000 number for the sleep is derived from trial and error. The write calls don't seem to block at the rate
        they write. By allowing 166uS delay for each byte of data then the Funcgen doesn't choke on the next call. A
        flat 20ms is added to allow processing time.
        This is especially important for commands that write large amounts of data such as user arbitrary forms.
        # NOTE: SPD programming tips recommends 10-100ms between write commands
        """
        for cmd in data.split(";"):
            self.instrument.write(cmd)
            time.sleep(0.02 + len(cmd) / 6000)
        self._is_error()

    @staticmethod
    def _parse_errors(error_response):
        """Parse error string for error code and message
        Has different form depending on F/W version:
            '<code> <message>'      (2017)
            '±<code>, <message>'    (2021)
        """
        comp = re.compile(r"([+-]?\d+)\,? *(.*)", re.UNICODE)
        match = comp.match(error_response)
        code = int(match[1])
        msg = match[2].strip('"')
        return code, msg

    def _is_error(self):
        resp = self.instrument.query("SYST:ERR?")
        if resp:
            code, msg = self._parse_errors(resp)
            if code != 0:
                raise InstrumentError(
                    f"Error Returned from PPS\nCode: {code}\nMessage: {msg}"
                )
        else:
            # NOTE: old F/W returns empty string to an incorrect query
            # On occasion the new F/W also does the first time after clearing an error
            raise InstrumentError("PPS Failed to respond to system query")

    def init_api(self):
        for func_str, handler, base_str in self.api:
            *parents, func = func_str.split(".")
            parent_obj = self
            for parent in parents:
                parent_obj = getattr(parent_obj, parent)
            func_obc = getattr(parent_obj, func)
            setattr(parent_obj, func, self.prepare_string(func_obc, handler, base_str))

    def prepare_string(self, func, handler, base_str, *args, **kwargs):
        def temp_func(*nargs, **nkwargs):
            """
            Only formats using **nkwargs
            New Temp
            :param nargs:
            :param nkwargs:
            :return:
            """
            sig = inspect.signature(func)
            keys = [itm[0] for itm in sig.parameters.items()]
            # Hard coding for RIGOL. BOOLS should be converted to "ON", "OFF"
            for index, param in enumerate(nargs):
                nkwargs[keys[index]] = param
            for k, v in nkwargs.items():
                if sig.parameters[k].annotation == bool:
                    if v:
                        nkwargs[k] = "ON"
                    else:
                        nkwargs[k] = "OFF"
            # new_str = base_str.format(**nkwargs)
            # handler(self, new_str)
            return handler(base_str, **nkwargs)

        return update_wrapper(temp_func, func)

    def get_identity(self) -> str:
        """
        :return:
            Return Info Manufacturer, product type, series No., software version,hardware version
            Typical Return Siglent Technologies, SPD3303X, SPD00001130025,1.01.01.01.02,V3.0
        """
        return self.instrument.query("*IDN?").strip()
