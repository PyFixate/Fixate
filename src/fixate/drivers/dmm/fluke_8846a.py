from threading import Lock
from pyvisa import constants
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.core.common import mode_builder, deprecated
from fixate.drivers.dmm.helper import DMM
import time


class Fluke8846A(DMM):
    REGEX_ID = "FLUKE,8846A"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument, *args, **kwargs):
        self.instrument = instrument
        instrument.rtscts = 1
        self.lock = Lock()
        self.display = "on"
        self.instrument.timeout = 10000
        self.instrument.query_delay = 0
        self.instrument.delay = 0
        self.is_connected = True
        self.reset()
        self._manual_trigger = False
        self._samples = 1
        self._CLEAN_UP_FLAG = False
        self._ANALOG_FLAG = False
        self._DIGITAL_FLAG = False
        self._range_string = ""
        self._bandwidth = None
        self._mode = None
        # Set to True to have explicit error checks on each read
        self.legacy_mode = False
        self._modes = {
            "voltage_ac": "CONF:VOLTage:AC",
            "voltage_dc": "CONF:VOLTage:DC",
            "current_ac": "CONF:CURRent:AC",
            "current_dc": "CONF:CURRent:DC",
            "resistance": "CONF:RESistance",
            "fresistance": "CONF:FRESistance",
            "period": "CONF:PERiod",
            "frequency": "CONF:FREQuency",
            "temperature": "CONF:TEMPerature:RTD",
            "ftemperature": "CONF:TEMPerature:FRTD",
            "capacitance": "CONF:CAPacitance",
            "continuity": "CONF:CONTinuity",
            "diode": "CONF:DIODe",
        }
        self._filters = {
            "voltage_ac": "SENS:VOLT:AC",
            "voltage_dc": "SENS:VOLT:DC",
            "current_ac": "SENS:CURR:AC",
            "current_dc": "SENS:CURR:DC",
            "resistance": "SENS:RES",
            "fresistance": "SENS:FRES",
            None: "",
        }
        self._init_string = ""  # Unchanging

        self._resolution = {
            "voltage_ac": "VOLT:RES",
            "voltage_dc": "VOLT:RES",
            "current_ac": "CURR:AC:RES",
            "current_dc": "CURR:DC:RES",
            "resistance": "RES:RES",
            "fresistance": "RES:RES",
            "capacitance": "CAP:RES",
            None: "",
        }

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, val):
        self._write(f"SAMP:COUN {val}")
        self._is_error()
        self._samples = val

    def local(self):
        self._write("SYST:LOC")

    def remote(self):
        self._write("SYST:REM")

    def set_manual_trigger(self, samples=1):
        MAX_TRIGGER_COUNT = 5000
        self._manual_trigger = True
        self.samples = samples
        # set DMM to remote trigger
        self._write("TRIG:SOUR BUS")
        # Set number of samples to maximum:
        self._write(f"TRIG:COUN {int(MAX_TRIGGER_COUNT/samples)}")
        self._write("INIT")  # Wait for trigger
        self._is_error()  # Catch possible insufficient memory error (and others)

    def trigger(self):
        self._write("*TRG")  # Send trigger to instrument
        self._is_error()  # Catch errors. This might slow things down

    def measurement(self):
        """
        Sets up DMM triggering, creates list of measurements from the read buffer
        returns: a single value as a float
        """
        return self.measurements()[0]

    def measurements(self):
        if not self.mode:
            raise InstrumentError("Please set DMM mode before taking a measurement!")

        with self.lock:
            return self._read_measurements()

    def reset(self):
        """
        Checks for errors and then returns DMM to power up state
        """
        with self.lock:
            self._is_error(silent=True)
            self._write(["*rst", "SYST:REM", "*cls", f"disp {self.display}"])
            self._CLEAN_UP_FLAG = False
            self._is_error()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()
        self.is_connected = False

    def _write(self, data):
        """
        Writes data to the DMM
        raise: ParameterError if called with no data string
        """
        if data:
            if isinstance(data, str):
                self.instrument.write(data)
                time.sleep(0.05)
            else:
                for itm in data:
                    self.instrument.write(itm)
                time.sleep(0.05)
        else:
            raise ParameterError("Missing data in instrument write")

    def _read_measurements(self):
        """
        Attempts to read values from the DMM up until self.retrys_on_timeout amount of times
        After each attempt DMM is checked for errors
        If errors.VisaIOError during read error_cleanup is called
        raise: VisaIOError if exception on the last attempt
               ValueError if no values are read
        return: values read from the DMM
        """
        if self._manual_trigger:
            values = self.instrument.query_ascii_values("FETCH?")
            # Reset for next set of measurements (clear buffer).
            # Fluke does not allow you to manually clear the buffer, so this roundabout way is used instead
            self.set_manual_trigger(samples=self.samples)
        else:
            values = self.instrument.query_ascii_values("READ?")

        if self.legacy_mode:
            self._is_error()
        return values

    def _check_errors(self):
        """
        Queries the DMM for errors and splits the resp string into the message and error code
        return: Error code and Error msg
        """
        resp = self.instrument.query("SYST:ERR?")
        try:
            code, msg = resp.strip("\n").split(",")
            code = int(code)
            msg = msg.strip('"')
        except:
            code = -1
            msg = "Incompatible error response returned"
        return code, msg

    def _is_error(self, silent=False):
        """
        Creates list of errors
        raise: InstrumentError if silent false
        return: list of errors
        """
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
                    "Error(s) Returned from DMM\n"
                    + "\n".join(["Code: {code}\nMessage:{msg}" for code, msg in errors])
                )

    def error_cleanup(self):
        """
        When VisaIOError exception caught, DMM interrupt is sent, read buffer is cleared and DMM returned to power up
        state.  VI read buffer is then flushed.
        DMM is then returned to previous configuration
        """
        self._CLEAN_UP_FLAG = True
        # Disaster Recovery
        self.instrument.write("\x03;*RST;*CLS")  # CTRL-C
        time.sleep(1.1)  # time needed to clear the dmm read buffer
        self.instrument.flush(constants.VI_READ_BUF_DISCARD)
        self.instrument.close()
        self.instrument.open()

    def _set_measurement_mode(self, mode, _range=None, suffix=None):
        """
        Helper function used to set the measurement mode for voltage_ac, voltage_dc, current_ac, current_dc,
        resistance, fresistance. Reduces previous duplicate code.
        :param mode:
        :param _range:
        :param _resolution:
        :return:
        """
        self.mode = mode
        self._manual_trigger = False  # Default mode is auto trigger
        mode_str = f"{self._modes[self._mode]}"
        if _range is not None:
            mode_str += f" {_range}"
        if suffix is not None:
            mode_str += f" {suffix}"
        self._write(mode_str)
        self._write(
            [
                "SYST:REM",
                "TRIG:DEL:AUTO ON",
                "TRIG:SOUR IMM",
                "TRIG:COUN 1",
                f"SAMP:COUN {self.samples}",
            ]
        )
        self._is_error()

    def voltage_ac(self, _range=None):
        self._set_measurement_mode("voltage_ac", _range)

    def voltage_dc(self, _range=None, auto_impedance=False):
        # Auto impedance OFF is the default mode.
        if auto_impedance == True:
            command = "; :SENS:VOLT:DC:IMP:AUTO ON"
        else:
            command = "; :SENS:VOLT:DC:IMP:AUTO OFF"
        self._set_measurement_mode("voltage_dc", _range, suffix=command)

    def current_ac(self, _range=None):
        self._set_measurement_mode("current_ac", _range)

    def current_dc(self, _range=None):
        self._set_measurement_mode("current_dc", _range)

    def resistance(self, _range=None):
        self._set_measurement_mode("resistance", _range)

    def fresistance(self, _range=None):
        self._set_measurement_mode("fresistance", _range)

    def frequency(self, _range=None):
        self._set_measurement_mode("frequency", _range)

    def period(self, _range=None):
        self._set_measurement_mode("period", _range)

    def capacitance(self, _range=None):
        self._set_measurement_mode("capacitance", _range)

    def diode(self, low_current=True, high_voltage=False):
        """
        Writes configuration string for diode to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        self._set_measurement_mode(
            "diode",
            suffix=f"{int(bool(low_current))}, {int(bool(high_voltage))}",
        )

    def continuity(self):
        """
        Writes configuration string for continuity to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        self._set_measurement_mode("continuity")

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        """
        Creates the variable to set the mode configuration of the DMM
        param value: The string associated with the mode being set up
        raise: ParameterError if mode trying to be set is not valid
        """
        self._write("*rst")
        time.sleep(0.05)
        # do we need to set the default filter here?
        if value not in self._modes:
            raise ParameterError(f"Unknown mode {value} for DMM")
        self._mode = value

    def digital_filter(self):
        """
        Sets up DMM digital filtering
        raise: TypeError if trying to set digital filter in an AC mode
        """
        if "ac" in self._mode:
            raise TypeError
        self._write(self._filters[self.mode] + ":FILT:DIG:STAT ON")

    def analog_filter(self, bandwidth=None):
        """
        Sets up DMM analog filtering.  Writes the different filter strings depending on the configuration mode.  Hence,
        configuration must be set before calling filter.
        raise: ValueError if invalid filtering bandwidth is requested
        """
        if "ac" in self._mode:
            self._bandwidth = bandwidth or 20
            if self._bandwidth not in [3, 20, 200]:
                raise ValueError("Bandwidth must be 3, 20 or 200")
            self._write(self._filters[self.mode] + f":BAND {self._bandwidth}")

        elif any(x in self._mode for x in ["dc", "res"]):
            self._write(self._filters[self.mode] + ":FILT:STAT ON")
        pass

    def get_identity(self) -> str:
        """
        Meter returns the identification code of the meter as four fields separated by commas.
        These fields are:
            manufacturer ("FLUKE"); model (“45"); seven-digit serial number;
            version of main software and version of display software.
        :return:
            (example: FLUKE, 45, 9080025, 2.0, D2.0)
        """
        return self.instrument.query("*IDN?").strip()
