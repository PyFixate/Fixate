from threading import Lock
from pyvisa import constants
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.core.common import mode_builder, deprecated
from fixate.drivers.dmm.helper import DMM
import time


class Keithley6500(DMM):
    REGEX_ID = "KEITHLEY INSTRUMENTS,MODEL DMM6500"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument, *args, **kwargs):
        self.instrument = instrument
        instrument.rtscts = 1
        self.lock = Lock()
        self._display = "ON100"
        # del self.instrument.timeout
        self.instrument.timeout = 10000
        self.instrument.query_delay = 0.3  # Stop DMM crash
        self.instrument.delay = 0  # Stop DMM crash
        self.is_connected = True
        self.reset()
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
            "voltage_ac": "VOLT:AC",
            "voltage_dc": "VOLT:DC",
            "current_ac": "CURR:AC",
            "current_dc": "CURR:DC",
            "resistance": "RES",
            "fresistance": "FRES",
            "period": "PER",
            "frequency": "FREQ",
            "temperature": "TEMP",
            "capacitance": "CAP",
            "continuity": "CONT",
            "diode": "DIOD",
        }

        self._init_string = ""  # Unchanging

    # Adapter for different DMM behaviour
    @property
    def display(self):
        return self.display

    @display.setter
    def display(self, val):
        if val == "off":
            self._display = "OFF"
        else:
            self._display = "ON100"

        self._write(["DISP:LIGH:STAT {}".format(self._display)])

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, val):
        # Sample number is per mode.

        # Clip values to upper and lower bounds. DMM likes to crash if set out of bounds
        if val < 1:
            val = 1
        elif val > 1000000:
            val = 1000000

        self._write(["SENS:COUN {}".format(val)])
        self._is_error()
        self._samples = val

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
            # Wait for previous commands to finish, reset, clear event logs
            self._write(["*WAI; *RST; *CLS"])
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
        self._write(
            ["TRAC:CLE"]
        )  # Clear the reading buffer for next set of measurements.
        self.instrument.query("READ?")  # Start sampling into debuffer1
        values = self.instrument.query_ascii_values(
            "TRAC:DATA? 1, {}".format(self.samples)
        )  # Read values from the once done.
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
            code, msg = resp.strip("\n").split(',"')
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
            # Fix errors needs an overhaul.
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
                    + "\n".join(
                        [
                            "Code: {}\nMessage:{}".format(code, msg)
                            for code, msg in errors
                        ]
                    )
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
        :return:
        """
        self.mode = mode
        mode_str = "SENS:FUNC '{}'".format(self._modes[self._mode])
        if _range is not None:
            mode_str += "; :SENS:{}:RANGE {}".format(self._modes[self._mode], _range)
        if suffix is not None:
            mode_str += "; {}".format(suffix)
        self._write(mode_str)
        # Make sure sample count is set for the mode:
        self._write(["SENS:COUN {}".format(self.samples)])

        self._is_error()

    def voltage_ac(self, _range=None):
        self._set_measurement_mode("voltage_ac", _range)

    def voltage_dc(self, _range=None):
        self._set_measurement_mode("voltage_dc", _range)

    def current_ac(self, _range=None):
        self._set_measurement_mode("current_ac", _range)

    def current_dc(self, _range=None):
        self._set_measurement_mode("current_dc", _range)

    def resistance(self, _range=None):
        self._set_measurement_mode("resistance", _range)

    def fresistance(self, _range=None):
        self._set_measurement_mode("fresistance", _range)

    def frequency(self, _range=None):
        # Cannot set range for frequency measurement
        self._set_measurement_mode("frequency")

    def period(self, _range=None):
        # Cannot set range for period measurement
        self._set_measurement_mode("period")

    def capacitance(self, _range=None):
        self._set_measurement_mode("capacitance", _range)

    def diode(self, low_current=True, high_voltage=False):
        # Cannot set range. 10V fixed range
        if low_current == True:
            command = ":SENS:DIOD:BIAS:LEV 0.0001"  # 100uA
        if low_current == False:
            command = ":SENS:DIOD:BIAS:LEV 0.001"  # 1mA
        self._set_measurement_mode("diode", suffix=command)

    def continuity(self):
        """
        Writes configuration string for continuity to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        # 1 kOhm fixed range
        self._set_measurement_mode("continuity")

    def temperature(self):
        self._set_measurement_mode("temperature")

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
            raise ParameterError("Unknown mode {} for DMM".format(value))
        self._mode = value

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
