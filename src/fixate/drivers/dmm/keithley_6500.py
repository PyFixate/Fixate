from threading import Lock
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.drivers.dmm.helper import DMM
import time


class Keithley6500(DMM):
    REGEX_ID = "KEITHLEY INSTRUMENTS,MODEL DMM6500"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument, *args, **kwargs):
        # Delay between call to self.measurement() and querying the DMM.
        self.measurement_delay = 0.2
        self.instrument = instrument
        instrument.rtscts = 1
        self.lock = Lock()
        self.instrument.timeout = 10000
        self.instrument.query_delay = 0.3  # Stop DMM crash
        self.instrument.delay = 0
        self.is_connected = True
        self.reset()
        self._manual_trigger = False
        self._samples = 1
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

    # Adapted for different DMM behaviour
    @property
    def display(self):
        return self.display

    @display.setter
    def display(self, val):
        if val == "off":
            self._display = "OFF"
        else:
            self._display = "ON100"

        self._write(f"DISP:LIGH:STAT {self._display}")

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, val):
        # Sample number is per mode.

        # Clip values to upper and lower bounds. DMM likes to crash if set out of bounds
        if val < 1 or val > 1000000:
            raise ParameterError(
                "Number of samples out of bounds. Must be between 1 and 1000000"
            )

        self._write(f":COUN {val}")
        self._is_error()
        self._samples = val

    def local(self):
        # Keithley does not have a way to release the DMM from remote mode
        # So just set up a trigger loop. Requires *TRG to be sent to drop it out of the loop (call to remote()).
        self.samples = 1
        self._write("TRIG:LOAD 'EMPTY'")  # Load empty model
        self._write("TRIG:BLOC:MDIG 1, 'defbuffer1', 1")
        self._write("TRIG:BLOC:DEL:CONS 2, 0.1")
        self._write("TRIG:BLOC:BRAN:EVEN 3, COMM, 5")
        self._write("TRIG:BLOC:BRAN:ALW 4, 1")
        self._write("TRIG:BLOC:BUFF:CLE 5")
        self._write("TRAC:CLE")
        self._write("INIT")

    def remote(self):
        # Stop trigger loop and return to normal
        self._write("*TRG")
        self._is_error()

    def set_manual_trigger(self, samples=1):
        """
        Setup instrument for manual triggering
        :param samples: Number of samples to take per trigger

        Use trigger_measurement() to trigger a measurement.
        Use measurements() to retrieve measurements.
        """
        self._manual_trigger = True
        self.samples = samples
        self._write("TRIG:LOAD 'EMPTY'")  # Load empty model
        self._write(f"TRIG:BLOC:MDIG 1, 'defbuffer1', {samples}")
        self._write("TRAC:CLE")
        self._is_error()

    def trigger(self):
        """
        Manually trigger a measurement and store in instrument buffer.
        """
        if self._manual_trigger == False:
            raise InstrumentError("Manual trigger mode not set.")
        self._write("INIT; *WAI")
        self._is_error()

    def measurement(self, delay=None):
        """
        Sets up DMM triggering, creates list of measurements from the read buffer

        delay: If not set, will wait for self.measurement_delay seconds before triggering a measurement. If set, will wait for delay seconds before triggering a measurement.
        returns: a single value as a float
        """
        if delay is None:
            delay = self.measurement_delay

        if delay > 0:
            time.sleep(delay)
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
        self._is_error(silent=True)
        # Wait for previous commands to finish, reset, clear event logs
        self._write("*RST")
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
                time.sleep(0.05)  # Sleep to stop DMM crashes
            elif isinstance(data, list) and all([isinstance(itm, str) for itm in data]):
                # If we have a list of strings
                for itm in data:
                    self.instrument.write(itm)
                    time.sleep(0.05)  # Sleep to stop DMM crashes
            else:
                raise ParameterError("Invalid data to send to instrument")
        else:
            raise ParameterError("Missing data in instrument write")

    def _read_measurements(self):
        """
        Attempts to read values from the DMM
        After each attempt DMM is checked for errors
        raise: VisaIOError if exception on the last attempt
               ValueError if no values are read
        return: values read from the DMM
        """
        if not self._manual_trigger:
            self.instrument.query("READ?; *WAI")  # Start sampling into debuffer1

        # Get number of readings in buffer
        readings = self.instrument.query_ascii_values("TRAC:ACTual?")
        values = self.instrument.query_ascii_values(
            f"TRAC:DATA? 1, {readings[0]}"
        )  # Read values from the once done.
        if self.legacy_mode:
            self._is_error()

        self._write("TRAC:CLE")  # Clear buffer on exit for next reading
        return values

    def _check_errors(self):
        """
        Queries the DMM for errors and splits the resp string into the message and error code
        return: Error code and Error msg
        """
        resp = self.instrument.query("SYST:ERR:NEXT?")
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
                        [f"Code: {code}\nMessage:{msg}" for code, msg in errors]
                    )
                )

    def _set_measurement_mode(self, mode, _range=None, suffix=None):
        """
        Helper function used to set the measurement mode for voltage_ac, voltage_dc, current_ac, current_dc,
        resistance, fresistance. Reduces previous duplicate code.
        :param mode:
        :param _range:
        :return:
        """
        self.mode = mode
        self._manual_trigger = False
        mode_str = f"SENS:FUNC '{self._modes[self._mode]}'"
        if _range is not None:
            mode_str += f"; :SENS:{self._modes[self._mode]}:RANGE {_range}"
        if suffix is not None:
            mode_str += suffix
        self._write(mode_str)
        self._write(f":COUN {self.samples}")
        self._is_error()

    def voltage_ac(self, _range=None):
        self._set_measurement_mode("voltage_ac", _range)

    def voltage_dc(self, _range=None, auto_impedance=False):
        # Auto impedance OFF is the default mode.
        if auto_impedance == True:
            command = "; :SENS:VOLT:DC:INP AUTO"
        else:
            command = "; :SENS:VOLT:DC:INP MOHM10"
        self._set_measurement_mode("voltage_dc", _range, suffix=command)

    def current_ac(self, _range=None):
        self._set_measurement_mode("current_ac", _range)

    def current_dc(self, _range=None):
        self._set_measurement_mode("current_dc", _range)

    def resistance(self, _range=None):
        self._set_measurement_mode("resistance", _range)

    def fresistance(self, _range=None):
        self._set_measurement_mode("fresistance", _range)

    def frequency(self, _range=None, _volt_range=None):
        """
        :param _volt_range: The voltage range to perform the measurement.
        range for DMM is constant for frequency measurements
        """
        command = None
        if _volt_range:
            # Have to construct an alternative commnad for FREQuency range
            command = (
                f"; :SENS:FREQ:THR:RANG:AUTO OFF; :SENS:FREQ:THR:RANG {_volt_range}"
            )
        self._set_measurement_mode("frequency", suffix=command)

    def period(self, _range=None, _volt_range=None):
        """
        :param _range: The voltage range to perform the measurement.
        """
        command = None
        if _volt_range:
            # Have to construct an alternative commnad for PERiod range
            command = f"; :SENS:PER:THR:RANG:AUTO OFF; :SENS:PER:THR:RANG {_volt_range}"
        self._set_measurement_mode("period", suffix=command)

    def capacitance(self, _range=None):
        self._set_measurement_mode("capacitance", _range)

    def diode(self, low_current=True, high_voltage=False):
        # Cannot set range. 10V fixed range
        command = None
        if low_current == True:
            command = "; :SENS:DIOD:BIAS:LEV 0.0001"  # 100uA
        if low_current == False:
            command = "; :SENS:DIOD:BIAS:LEV 0.001"  # 1mA
        self._set_measurement_mode("diode", suffix=command)

    def continuity(self):
        """
        Writes configuration string for continuity to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        # 1 kOhm fixed range
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
        self._write("*RST")
        if value not in self._modes:
            raise ParameterError(f"Unknown mode {value} for DMM")
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
