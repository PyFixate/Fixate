import time
from fixate.core.common import mode_builder, unit_scale
from fixate.core.exceptions import ParameterError, InstrumentError
from fixate.drivers.funcgen.helper import FuncGen
from functools import update_wrapper
import inspect

MODES = {
    ":SINusoid": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    ":SQUare": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    ":RAMP": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    ":PULSE": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    ":NOISe DEFault": {",[{amplitude}]": {",[{offset}]": {}}},
    ":DC DEFault,DEFault": {",[{offset}]": {}},
    ":PRBS": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
    ":ARB": {" [{frequency}]": {",[{amplitude}]": {",[{offset}]": {}}}},
}

ADV_MODES = {":SQUare:" "DCYCle"}


class Keysight33500B(FuncGen):
    REGEX_ID = "Agilent Technologies,335..B"
    INSTR_TYPE = "VISA"

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
        self._store = {"ch1_duty": "50", "ch2_duty": "50", "ch1_modulate_source": "INT"}

        self.api = [
            # waveform selection
            # Channel 1:
            (
                "channel1.waveform.sin",
                self.store_and_write,
                ("SOUR1:FUNC SIN", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.square",
                self.store_and_write,
                (
                    "SOUR1:FUNC SQU\r\nSOUR1:FUNC:SQU:DCYC {self._store[ch1_duty]}",
                    {"ch1_waveform_handler": "channel1.waveform.square"},
                ),
            ),
            (
                "channel1.waveform.ramp",
                self.store_and_write,
                ("SOUR1:FUNC RAMP", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.pulse",
                self.store_and_write,
                (
                    "SOUR1:FUNC PULS\r\nPULS:DCYC {self._store[ch1_duty]}",
                    {"ch1_waveform_handler": "channel1.waveform.pulse"},
                ),
            ),
            (
                "channel1.waveform.arb",
                self.store_and_write,
                ("SOUR1:FUNC  ARB", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.triangle",
                self.store_and_write,
                ("SOUR1:FUNC TRI", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.noise",
                self.store_and_write,
                ("SOUR1:FUNC NOIS", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.dc",
                self.store_and_write,
                ("SOUR1:FUNC DC", {"ch1_waveform_handler": None}),
            ),
            (
                "channel1.waveform.prbs",
                self.store_and_write,
                ("SOUR1:FUNC PRBS", {"ch1_waveform_handler": None}),
            ),
            # Channel Configuration
            # Channel 1:
            ("channel1.vrms", self.write, "SOUR1:VOLT:UNIT VRMS\r\nVOLT {value}"),
            ("channel1.vpp", self.write, "SOUR1:VOLT:UNIT VPP\r\nVOLT {value}"),
            ("channel1.dbm", self.write, "SOUR1:VOLT:UNIT DBM\r\nVOLT {value}"),
            ("channel1.offset", self.write, "SOUR1:VOLT:OFFS {value}"),
            ("channel1.phase", self.write, "SOUR1:PHAS {value}"),
            (
                "channel1.duty",
                self.store_and_execute,
                ({"ch1_duty": "{value}"}, "ch1_waveform_handler"),
            ),
            ("channel1.frequency", self.write, "SOUR1:FREQ {value}"),
            # Channel Activation
            ("channel1._call", self.write, "OUTP {value}"),
            # Sync Configuration
            ("sync.polarity.normal", self.write, ""),
            ("sync.mode.normal", self.write, ""),
            # Sync Mode source only works on one. Need to manually override so that only channel 1 being passed works
            ("sync.mode.source", self.write, ""),
            ("sync._call", self.write, "OUTP {value}"),
            # Trigger Configuration
            ("trigger.immediate", self.write, "TRIG1:SOUR IMM"),
            ("trigger.external._call", self.write, "TRIG1:SOUR EXT"),
            (
                "trigger.external.rising",
                self.write,
                "TRIG1:SOUR EXT\r\n TRIG1:SLOP POS",
            ),
            (
                "trigger.external.falling",
                self.write,
                "TRIG1:SOUR EXT\r\n TRIG1:SLOP NEG",
            ),
            ("trigger.manual._call", self.write, "TRIG1:SOUR BUS"),
            ("trigger.manual.initiate", self.write, "TRIG1:SOUR BUS"),
            ("trigger.timer", self.write, "TRIG:SOUR TIM\r\n TRIG1:TIM {seconds}"),
            ("trigger.delay", self.write, "TRIG1:DEL {seconds}"),
            ("trigger.out._call", self.write, "OUTP:TRIG"),
            ("trigger.out.off", self.write, "OUTP:TRIG OFF"),
            ("trigger.out.rising", self.write, "OUTP:TRIG ON\r\n OUTP:TRIG:SLOP POS"),
            ("trigger.out.falling", self.write, "OUTP:TRIG ON\r\n OUTP:TRIG:SLOP NEG"),
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
                {"ch1_modulate_state": "SUM", "ch1_modulate_setting": "FREQ"},
            ),
            # MODULATE SOURCES:
            (
                "channel1.modulate.source.internal._call",
                self.write,
                "SOUR1:{self._store[ch1_modulate_state]}:" "SOUR INT",
            ),
            (
                "channel1.modulate.source.external",
                self.write,
                "SOUR1:{self._store[ch1_modulate_state]}:SOUR EXT",
            ),
            # MODULATE ACTIVATION:
            # Channel 1:
            (
                "channel1.modulate._call",
                self.write,
                "{self._store[ch1_modulate_state]}:SOUR {self._store[ch1_modulate_source]}\r\n"
                "{self._store[ch1_modulate_state]}:STAT {value}",
            ),
            # MODULATE OPTIONS:
            # Channel 1:
            ("channel1.modulate.am.depth", self.write, "SOUR1:AM:DEPT {value}"),
            ("channel1.modulate.am.dssc", self.write, "SOUR1:AM:DSSC ON"),
            ("channel1.modulate.fm.freq_dev", self.write, "SOUR1:FM:DEV {value}"),
            ("channel1.modulate.pm.phase_dev", self.write, "SOUR1:PM:DEV {value}"),
            ("channel1.modulate.fsk.hop_freq", self.write, "SOUR1:FSK:FREQ {value}"),
            ("channel1.modulate.fsk.rate", self.write, "SOUR1:FSK:INT:RATE {value}"),
            (
                "channel1.modulate.sum.modulate_percent",
                self.write,
                "SOUR1:SUM:AMPL {percent}",
            ),
            # Internal
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
            # Modulate Frequency
            (
                "channel1.modulate.source.internal.frequency",
                self.write,
                "SOUR1:{self._store[ch1_modulate_state]}:INT:{self._store[ch1_modulate_setting]} {value}",
            ),
            # LOAD:
            # channel1:
            ("channel1.load._call", self.write, "OUTP1:LOAD {ohms}"),
            ("channel1.load.infinite", self.write, "OUTP1:LOAD INF"),
            # BURST
            # Channel 1:
            ("channel1.burst.gated._call", self.write, "SOUR1:BURS:MODE GAT"),
            ("channel1.burst._call", self.write, "SOUR1:BURS:STAT {value}"),
            ("channel1.burst.ncycle._call", self.write, "SOUR1:BURS:MODE TRIG"),
            (
                "channel1.burst.ncycle.cycles._call",
                self.write,
                "SOUR1:BURS:NCYC {cycles}",
            ),
            (
                "channel1.burst.ncycle.cycles.infinite",
                self.write,
                "SOUR1:BURS:NCYC INF",
            ),
            (
                "channel1.burst.ncycle.burst_period",
                self.write,
                "SOUR1:BURS:INT:PER {seconds}",
            ),
            ("channel1.burst.gated.positive", self.write, "SOUR1:BURS:GATE:POL NORM"),
            ("channel1.burst.gated.negative", self.write, "SOUR1:BURS:GATE:POL INV"),
            ("channel1.burst.phase", self.write, "SOUR1:BURS:PHAS {degrees}"),
        ]

        # ----------------------------------------------------------------------------------------------------------------------

        self.init_api()

    def self_test(self):
        timeout = self.instrument.timeout
        try:
            self.instrument.timeout = 20000
            resp = self.instrument.query("*TST?")
            if "0" not in resp:
                raise InstrumentError("Failed Self Test")
        finally:
            self.instrument.timeout = timeout

    def local(self):
        """
        Gives local control back to the instrument
        Remote control is activated on any other commands set to the device
        :return:
        """
        self._write("SYSTem:LOCal")

    def reset(self):
        """
        Be aware that the funcgen can have a short period where it sets to 5Vpp 1kHz with the output on for a short
        period. This could cause issues. Ensure that setup is in a safe state to receive such a signal.
        :return:
        """
        self._write("*RST;*CLS")
        self._write("OUTP1:LOAD INF")

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
                self.instrument.write(data)
                time.sleep(0.1 + len(data) / 6000)
            else:
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
            handler(*args)

    def store_and_write(self, params, *args, **kwargs):
        base_str, store_dict = params
        self.store(store_dict)
        self.write(base_str, *args, **kwargs)

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
        Identification string contains four comma separated fields:
              Manufacturer name, Model number, Serial number, Revision code
        :return:
        Identification string is in the following format for the 33500 Series instruments:
            Keysight Technologies,[Model Number],[10-char Serial Number],A.aaa-B.bb-C.cc-DD-EE
                A.aaa = Firmware revision
                B.bb = Front panel FW revision
                C.cc = Power supply controller FW revision
                DD = FPGA revision
                EE = PCBA revision
        """
        return self.instrument.query("*IDN?").strip()
