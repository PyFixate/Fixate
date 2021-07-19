import time
import inspect
from functools import update_wrapper
from fixate.core.common import mode_builder, unit_scale
from fixate.core.exceptions import ParameterError, InstrumentError
from fixate.drivers.funcgen.helper import FuncGen

MODES = {
    ":SINusoid": {
        " [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}},
        ":CH2": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    },
    ":SQUare": {
        " [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}},
        ":CH2": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    },
    ":RAMP": {
        " [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}},
        ":CH2": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    },
    ":PULSE": {
        " [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}},
        ":CH2": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    },
    ":NOISe DEFault": {",[{amplitude}]": {",[{offset}]": {}}},
    ":DC DEFault,DEFault": {",[{offset}]": {}},
    ":USER": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
}

ADV_MODES = {":SQUare:" "DCYCle"}


# -----------------------------------------------------------------------------------------------------------------------
class RigolDG1022(FuncGen):
    REGEX_ID = "RIGOL TECHNOLOGIES,DG1022"
    INSTR_TYPE = "VISA"
    retrys_on_timeout = 3
    _verify = True

    def __init__(self, instrument):
        """
        The self._ values indicate the user values as entered if valid.
        The self.__ values are the sanitised values used internally in the system to parse between functions

        Limitations:
        The function generator switches internal relays at certain thresholds.
        Try to avoid these ranges in design if the function generator is loaded with a relatively low impedance
        Table of ranges on the same relay arrangement
        Min mVpp    Max mVpp
        4           60
        60.1        199.9
        200	        599.9
        600	        2000
        2001        6000
        6001        20000


        :param instrument:
        :return:
        """
        super().__init__(instrument)
        self.instrument.query_delay = 0.2
        self.instrument.timeout = 1000
        # Rigol Restrictions
        self.__restr_bandwidth = {"min": unit_scale("4uHz"), "max": unit_scale("20MHz")}
        self.__restr_phase = {"min": -180, "max": 180}
        self.__restr_amplitude = {
            "min": unit_scale("4mVpp"),
            "max": unit_scale("20Vpp"),
        }
        self._amplitude = None
        self._store = {"ch1_duty": "50", "ch2_duty": "50"}
        self.api = [
            # WAVEFORM SELECTION:
            # Channel 1:
            (
                "channel1.waveform.sin",
                self.store_and_write,
                ("FUNC SIN", {"ch1_waveform_handler": None}),  # base_str
            ),  # handler
            (
                "channel1.waveform.square",
                self.store_and_write,
                (
                    "FUNC SQU\r\nFUNC:SQU:DCYC {self._store[ch1_duty]}",
                    {"ch1_waveform_handler": "channel1.waveform.square"},
                ),
            ),
            (
                "channel1.waveform.ramp",
                self.store_and_write,
                ("FUNC RAMP", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.pulse",
                self.store_and_write,
                (
                    "FUNC PULS\r\nPULS:DCYC {self._store[ch1_duty]}",
                    {"ch1_waveform_handler": "channel1.waveform.pulse"},
                ),
            ),
            (
                "channel1.waveform.arb",
                self.store_and_write,
                ("FUNC USER", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.triangle",
                self.store_and_write,
                ("FUNC TRI", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.noise",
                self.store_and_write,
                ("FUNC NOIS", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.dc",
                self.store_and_write,
                ("FUNC DC", {"ch1_waveform_handler": None}),
            ),
            # Channel 2:
            (
                "channel2.waveform.sin",
                self.store_and_write,
                ("FUNC:CH2 SIN", {"ch2_waveform_handler": None}),  # base_str
            ),  # handler
            (
                "channel2.waveform.square",
                self.store_and_write,
                (
                    "FUNC:CH2 SQU\r\nFUNC:SQU:DCYC:CH2 {self._store[ch2_duty]}",
                    {"ch2_waveform_handler": "channel2.waveform.square"},
                ),
            ),
            (
                "channel2.waveform.ramp",
                self.store_and_write,
                ("FUNC:CH2 RAMP", {"ch2_waveform_handler": None}),
            ),
            (
                "channel2.waveform.pulse",
                self.store_and_write,
                (
                    "FUNC:CH2 PULS\r\nPULS:DCYC {self._store[ch2_duty]}",
                    {"ch2_waveform_handler": "channel2.waveform.pulse"},
                ),
            ),
            (
                "channel2.waveform.arb",
                self.store_and_write,
                ("FUNC:CH2 USER", {"ch2_waveform_handler": None}),
            ),
            (
                "channel2.waveform.triangle",
                self.store_and_write,
                ("FUNC:CH2 TRI", {"ch2_waveform_handler": None}),
            ),
            (
                "channel2.waveform.noise",
                self.store_and_write,
                ("FUNC:CH2 NOIS", {"ch2_waveform_handler": None}),
            ),
            (
                "channel2.waveform.dc",
                self.store_and_write,
                ("FUNC:CH2 DC", {"ch2_waveform_handler": None}),
            ),
            # CHANNEL CONFIGURATION:
            # Channel 1:
            ("channel1.vrms", self.write, "VOLT:UNIT VRMS\r\nVOLT {value}"),
            ("channel1.vpp", self.write, "VOLT:UNIT VPP\r\nVOLT {value}"),
            ("channel1.dbm", self.write, "VOLT:UNIT DBM\r\nVOLT {value}"),
            ("channel1.offset", self.write, "VOLT:OFFS {value}"),
            ("channel1.phase", self.write, "PHAS {value}"),
            (
                "channel1.duty",
                self.store_and_execute,
                ({"ch1_duty": "{value}"}, "ch1_waveform_handler"),
            ),
            ("channel1.frequency", self.write, "FREQ {value}"),
            # Channel 2:
            ("channel2.vrms", self.write, "VOLT:UNIT:CH2 VRMS\r\nVOLT {value}"),
            ("channel2.vpp", self.write, "VOLT:UNIT:CH2 VPP\r\nVOLT {value}"),
            ("channel2.dbm", self.write, "VOLT:UNIT:CH2 DBM\r\nVOLT {value}"),
            ("channel2.offset", self.write, "VOLT:OFFS:CH2 {value}"),
            ("channel2.phase", self.write, "PHAS:CH2 {value}"),
            ("channel2.duty", self.store, {"ch2_duty": "{value}"}),
            ("channel2.frequency", self.write, "FREQ:CH2 {value}"),
            # CHANNEL ACTIVATION:
            (
                "channel1._call",
                self.write,
                "OUTP {value}",
            ),  # True won't work here needs to be ON or 1, OFF or 0
            (
                "channel2._call",
                self.write,
                "OUTP:CH2 {value}",
            ),  # True won't work here needs to be ON or 1, OFF or 0
            # SYNC CONFIGURATION:
            ("sync.polarity.normal", self.write, ""),
            ("sync.mode.normal", self.write, ""),
            ("sync.mode.source", self.write, ""),
            ("sync._call", self.write, "OUTP {value}"),
            # TRIGGER CONFIGURATION:
            ("trigger.immediate", self.write, "TRIG:SOUR IMM"),
            ("trigger.external._call", self.write, "TRIG:SOUR EXT"),
            ("trigger.external.rising", self.write, "TRIG:SOUR EXT\r\n TRIG1:SLOP POS"),
            (
                "trigger.external.falling",
                self.write,
                "TRIG:SOUR EXT\r\n TRIG1:SLOP NEG",
            ),
            ("trigger.manual", self.write, "TRIG:SOUR BUS"),
            ("trigger.delay", self.write, "TRIG:DEL {seconds}"),
            ("trigger.out.off", self.write, "OUTP:TRIG OFF"),
            ("trigger.out._call", self.write, "OUTP:TRIG {output}"),
            ("trigger.out.rising", self.write, "OUTP:TRIG:SLOP POS"),
            ("trigger.out.falling", self.write, "OUTP:TRIG:SLOP NEG"),
            # Modulate
            # Channel 1:
            (
                "channel1.modulate.am._call",
                self.store,
                {"ch1_modulate_state": "AM", "ch1_modulate_setting": "FREQ"},
            ),
            (
                "channel1.modulate.fm._call",
                self.store,
                {"ch1_modulate_state": "FM", "ch1_modulate_setting": "FREQ"},
            ),
            (
                "channel1.modulate.pm._call",
                self.store,
                {"ch1_modulate_state": "PM", "ch1_modulate_setting": "FREQ"},
            ),
            (
                "channel1.modulate.fsk._call",
                self.store,
                {"ch1_modulate_state": "FSK", "ch1_modulate_setting": "RATE"},
            ),
            (
                "channel1.modulate.bpsk._call",
                self.store,
                {"ch1_modulate_state": "BPSK", "ch1_modulate_setting": "RATE"},
            ),
            (
                "channel1.modulate.sum._call",
                self.store,
                {"ch1_modulate_state": "SUM", "ch1_modulate_setting": "RATE"},
            ),
            # MODULATE SOURCES:
            (
                "channel1.modulate.source.internal._call",
                self.store_and_write,
                (
                    "{self._store[ch1_modulate_state]}:SOUR INT",
                    {"ch1_modulate_source": "INT"},
                ),
            ),
            (
                "channel1.modulate.source.external",
                self.store_and_write,
                (
                    "{self._store[ch1_modulate_state]}:SOUR EXT",
                    {"ch1_modulate_source": "EXT"},
                ),
            ),
            # MODULATE ACTIVATION:
            # Channel 1:
            (
                "channel1.modulate._call",
                self.write,
                "{self._store[ch1_modulate_state]}:STAT {value}\r\n{self._store[ch1_modulate_state]}:SOUR"
                "{self._store[ch1_modulate_source]}",
            ),
            # MODULATE OPTIONS:
            # Channel 1:
            ("channel1.modulate.am.depth", self.write, "AM:DEPT {value}"),
            ("channel1.modulate.fm.freq_dev", self.write, "FM:DEV {value}"),
            ("channel1.modulate.pm.phase_dev", self.write, "PM:DEV{value}"),
            ("channel1.modulate.fsk.hop_freq", self.write, "FSK:FREQ {value}"),
            ("channel1.modulate.fsk.rate", self.write, "FSK:INT:RATE {value}"),
            # MODULATE SHAPES:
            # Channel 1:
            (
                "channel1.modulate.source.internal.shape.sin",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC SIN",
            ),
            (
                "channel1.modulate.source.internal.shape.square",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC SQU",
            ),
            (
                "channel1.modulate.source.internal.shape.triangle",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC TRI",
            ),
            (
                "channel1.modulate.source.internal.shape.up_ramp",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC RAMP",
            ),
            (
                "channel1.modulate.source.internal.shape.down_ramp",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC NRAMP",
            ),
            (
                "channel1.modulate.source.internal.shape.noise",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:FUNC NOIS",
            ),
            # BURST
            # Channel 1:
            ("channel1.burst.gated._call", self.write, "BURS:MODE GAT"),
            ("channel1.burst._call", self.write, "BURS:STAT {value}"),
            ("channel1.burst.ncycle._call", self.write, "BURS:MODE TRIG"),
            ("channel1.burst.ncycle.cycles._call", self.write, "BURS:NCYC {cycles}"),
            ("channel1.burst.ncycle.cycles.infinite", self.write, "BURS:NCYC INF"),
            (
                "channel1.burst.ncycle.burst_period",
                self.write,
                "BURS:INT:PER {seconds}",
            ),
            ("channel1.burst.gated.positive", self.write, "BURS:GATE:POL NORM"),
            ("channel1.burst.gated.negative", self.write, "BURS:GATE:POL INV"),
            ("channel1.burst.phase", self.write, "BURS:PHAS {degrees}"),
            # Modulate Frequency
            (
                "channel1.modulate.source.internal.frequency",
                self.write,
                "{self._store[ch1_modulate_state]}:INT:{self._store[ch1_modulate_setting]} {value}",
            ),
            # LOAD:
            # channel1:
            ("channel1.load._call", self.write, "OUTP:LOAD {ohms}"),
            ("channel1.load.infinite", self.write, "OUTP:LOAD INF"),
            # channel2:
            ("channel2.load._call", self.write, "OUTP:LOAD:CH2 {ohms}"),
            ("channel2.load.infinite", self.write, "OUTP:LOAD:CH2 INF"),
        ]

        # -----------------------------------------------------------------------------------------------------------------------

        self.init_api()

    def sync_output(self, sync):
        """
        :param sync:
         True or False
        :return:
        None
        """
        if sync:
            self._write(["OUTPut:SYNC ON"])
        else:
            self._write(["OUTPut:SYNC OFF"])

    def trigger_output(self, trigger, rising=False, falling=False):
        """
        :param sync:
         True or False
        :return:
        None
        """
        if rising and falling:
            raise ValueError("Cannot trigger on both rising and falling edges")
        if trigger:
            if rising:
                self._write(["OUTPut:TRIGger:SLOPe POSitive"])
            if falling:
                self._write(["OUTPut:TRIGger:SLOPe NEGative"])
            self._write(["OUTPut:TRIGger ON"])
        else:
            self._write(["OUTPut:TRIGger OFF"])

    @property
    def verify_values(self):
        return self._verify

    @verify_values.setter
    def verify_values(self, val):
        if val not in [True, False]:
            raise ValueError("Invalid value. Use True or False")
        self._verify = val

    @property
    def amplitude_ch1(self):
        return self.instrument.query_ascii_values("VOLTAGE?")[0]

    @property
    def amplitude_ch2(self):
        return self.instrument.query_ascii_values("VOLTAGE:CH2?")[0]

    @amplitude_ch1.setter
    def amplitude_ch1(self, val):
        self._write("VOLTAGE {}".format(val))

    @amplitude_ch2.setter
    def amplitude_ch2(self, val):
        self._write("VOLTAGE:CH2 {}".format(val))

    @property
    def output_ch1(self):
        resp = self.instrument.query("OUTP?")
        if "OFF" in resp:
            return False
        elif "ON" in resp:
            return True

    @output_ch1.setter
    def output_ch1(self, val):
        if val not in [True, False]:
            raise ParameterError(
                "Unknown output {} value for CH1\r\nPlease select True or False".format(
                    val
                )
            )
        if val:
            self._write("OUTP ON")
        else:
            self._write("OUTP OFF")

    @property
    def output_ch2(self):
        resp = self.instrument.query("OUTP:CH2?")
        if "OFF" in resp:
            return False
        elif "ON" in resp:
            return True

    @output_ch2.setter
    def output_ch2(self, val):
        if val not in [True, False]:
            raise ParameterError(
                "Unknown output {} value for CH2\nPlease select True or False".format(
                    val
                )
            )
        if val:
            self._write("OUTP:CH2 ON")
        else:
            self._write("OUTP:CH2 OFF")

    @FuncGen.output_sync.setter
    def output_sync(self, val):
        time.sleep(0.5)
        if val not in [True, False]:
            raise ParameterError(
                "Unknown output {} value for SYNC\nPlease select True or False".format(
                    val
                )
            )
        self._output_sync = val
        if self._output_sync:
            self._write("OUTP:SYNC ON")
        else:
            self._write("OUTP:SYNC OFF")

    def local(self):
        """
        Gives local control back to the instrument
        Remote control is activated on any other commands set to the device
        :return:
        """
        time.sleep(0.5)
        self._write("SYSTem:LOCal")

    def reset(self):
        """
        Be aware that the funcgen can have a short period where it sets to 5Vpp 1kHz with the output on for a short
        period. This could cause issues. Ensure that setup is in a safe state to receive such a signal.
        :return:
        """
        # Due to the 5Vpp 1kHz signal. Explicit call to turn output off first
        self.output_ch1 = False
        self.output_ch2 = False
        self._write("*RST")

    def function(
        self, waveform, channel=1, duty_cycle=None, symmetry=None, phase=None, **kwargs
    ):
        """
         if parameters empty then uses previous set mode
         The mode and mode parameters are used in mode_build to search recursively through the
         MODES dictionary to build the visa string necessary for the equipment to interpret the commands.
         usage
         function('sin')
            parsed to visa:
                'APPLy:SINusoid'
         function('square', channel=2, amplit=5, offset=2.5, freq='1kHz')
            parsed to visa:
                'APPLy:SQUare:CH2 1000, 5, 2.5'
                corresponds to a square wave at 1kHz, where the min of the wave is at 0 and the max at 5V
        for more advanced functions that cannot be explained through waveform, amplitude, offset and frequency:
            use adv_function.
        """
        if int(channel) in range(1, 3):
            channel = "CH{}".format(channel)
        else:
            raise ValueError(
                "Invalid channel {} use a number between 1-2".format(channel)
            )
        mode = (waveform, channel)
        # self.reset()
        if duty_cycle is not None:
            if waveform.upper() not in "PULSE":
                if channel == "CH1":
                    self._write(
                        ["FUNCtion:{}:DCYCle {}".format(waveform.upper(), duty_cycle)]
                    )
                else:
                    self._write(
                        [
                            "FUNCtion:{}:DCYCle:{} {}".format(
                                waveform.upper(), channel, duty_cycle
                            )
                        ]
                    )
            else:
                if channel == "CH1":
                    self._write(["PULSe:DCYC {}".format(duty_cycle)])
                else:
                    self._write(["PULSe:DCYC:{} {}".format(channel, duty_cycle)])

        if symmetry is not None:
            if channel == "CH1":
                self._write(["FUNCtion:RAMP:SYMMetry {}".format(symmetry)])
            else:
                self._write(["FUNCtion:RAMP:SYMMetry:{} {}".format(channel, symmetry)])

        if phase is not None:
            if channel == "CH1":
                self._write(["PHASe {}".format(phase)])
            else:
                self._write(["PHASe:CH2 {}".format(phase)])

        self._write(["APPLy{}".format(mode_builder(MODES, {}, *mode, **kwargs))])

    def am(self, frequency, depth, source=None, waveform="SIN"):
        self._write(
            [
                "AM:SOURce INT",
                "AM:INT:FREQuency {frequency}".format(frequency=frequency),
                "AM:DEPTh {depth}".format(depth=depth),
                "AM:INT:FUNC {waveform}".format(waveform=waveform),
                "AM:STATe ON",
            ]
        )

    def disable_am(self):
        self._write(["AM:STATe OFF"])

    def enable_am(self):
        self._write(["AM:STATe ON"])

    def adv_function(self, *mode, **mode_params):
        """
        Exposes the advanced functionality of the function generator.
        Currently not implemented
        :param mode:
        :param mode_params:
        :return:
        """
        raise NotImplementedError

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
        if data:
            if isinstance(data, str):
                data = data.split("\r\n")
            for itm in data:
                self.instrument.write(itm)
                time.sleep(0.1 + len(itm) / 6000)
        else:
            raise ParameterError("Missing data in instrument write")
        self._is_error()

    def _check_errors(self):
        resp = self.instrument.query("SYST:ERR?")
        code, msg = resp.strip("\n").split(",")
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
                raise InstrumentError(
                    "Error(s) Returned from FuncGen\n"
                    + "\n".join(
                        [
                            "Code: {}\nMessage:{}".format(code, msg)
                            for code, msg in errors
                        ]
                    )
                )

    def write(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
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

    def store(self, store_dict, *args, **kwargs):
        """
        Store a dictionary of values in TestClass
        :param kwargs:
        Dictionary containing the parameters to store
        :return:
        """
        new_dict = store_dict.copy()
        for k, v in store_dict.items():
            # I want the same function from write to set up the string before putting it in new_dict
            try:
                new_dict[k] = v.format(**kwargs)
            except:
                pass
        self._store.update(new_dict)

    def store_and_execute(self, params, *args, **kwargs):
        store_dict, handler_id = params
        self.store(store_dict, *args, **kwargs)
        handler_string = self._store[handler_id]
        if handler_string is not None:
            *parents, func = handler_string.split(".")
            parent_obj = self
            for parent in parents:
                parent_obj = getattr(parent_obj, parent)
            handler = getattr(parent_obj, func)
            handler()

    def store_and_write(self, params, *args, **kwargs):
        base_str, store_dict = params
        self.store(store_dict)
        self.write(base_str, *args, **kwargs)

    def init_api(self):
        for func_str, handler, base_str in self.api:
            *parents, func = func_str.split(".")
            parent_obj = self
            try:
                for parent in parents:
                    parent_obj = getattr(parent_obj, parent)
                func_obc = getattr(parent_obj, func)
            except AttributeError:
                # print("FAILED ON:", func_str)
                raise
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
            return handler(base_str, **nkwargs)

        return update_wrapper(temp_func, func)
        # ------------------------------------------------------------------------------------------

    def get_identity(self):
        """
        Query ID character string of instrument, including a field separated by 4 “,”, manufactory, model, serial number
        and the edition number that consists of numbers and separated by “.” .
        :return: RIGOL TECHNOLOGIES,DG1022,DG1000000002,00.01.00.04.00
        """
        return self.instrument.query("*IDN?").strip()
