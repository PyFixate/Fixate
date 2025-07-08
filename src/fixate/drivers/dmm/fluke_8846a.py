from threading import Lock
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.drivers.dmm.helper import DMM
import time
from typing import Literal
import enum


class Fluke8846A(DMM):
    REGEX_ID = "FLUKE,8846A"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument, *args, **kwargs):
        # Delay between call to self.measurement() and querying the DMM.
        self.measurement_delay = 0
        self.instrument = instrument
        instrument.rtscts = 1
        self.lock = Lock()
        self.display = "on"
        self.instrument.timeout = 10000
        self.instrument.query_delay = 0  # Delay between write and read in a query
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
        self._nplc_modes = [
            "resistance",
            "fresistance",
            "voltage_dc",
            "current_dc",
            "temperature",
            "ftemperature",
        ]
        self._nplc_settings = [0.02, 0.2, 1, 10]
        self._default_nplc = 10  # Default NPLC setting as per Fluke 8846A manual
        self._init_string = ""  # Unchanging

        # High and low current port definition. Each definition encodes the maximum current able to
        # be measured by the port (in amps)
        self.current_ports = {"HIGH": 10, "LOW": 400e-3}

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
        """
        Manually trigger a measurement and store in instrument buffer.
        """
        if self._manual_trigger == False:
            raise InstrumentError("Manual trigger mode not set.")
        self._write("*TRG")  # Send trigger to instrument
        self._is_error()  # Catch errors. This might slow things down

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

    def min_avg_max(self, samples=1, sample_time=1):
        """
        automatically samples the DMM for a given number of samples and returns the min, max, and average values
        :param samples: number of samples to take
        :param sample_time: time to wait for the DMM to take the samples
        return: min, avg, max values as floats in a dataclass
        """

        self._write(f"SAMP:COUN {samples}")
        self._write("CALC:FUNC AVER")
        self._write("CALC:STAT ON")
        self._write("INIT")
        time.sleep(sample_time)
        min_ = self.instrument.query_ascii_values("CALC:AVER:MIN?")[0]
        avg_ = self.instrument.query_ascii_values("CALC:AVER:AVER?")[0]
        max_ = self.instrument.query_ascii_values("CALC:AVER:MAX?")[0]

        values = DMM.MeasurementStats(min=min_, avg=avg_, max=max_)

        # clean up
        self._write("CALC:STAT OFF")
        self._write("SAMP:COUN 1")

        return values

    def reset(self):
        """
        Checks for errors and then returns DMM to power up state
        """
        with self.lock:
            self._is_error(silent=True)
            self._write(["*rst", "SYST:REM", "*cls", f"disp {self.display}"])
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
                for itm in data:
                    self.instrument.write(itm)
                    time.sleep(0.05)  # Sleep to stop DMM crashes
            else:
                raise ParameterError("Invalid data to send to instrument")
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

    def current_ac(self, _range, port):
        """
        Set the measurement mode on the DMM to AC current.

        If the range and port selection are not compatible, i.e. someone has requested to measure
        1 A on the low range port with a maximum capability of 400 mA, an exception is raised.

        If the range requested can be measured by the low port, but the high port is selected, an
        exception is raised.
        """

        # Check the requested range is not more than the port capability:
        if _range > self.current_ports[port]:
            raise ValueError(
                "The selected port and range combination is not available for this instrument. Consider using a different multimeter"
            )

        # Raise an error if the high port is selected when the low port should be used:
        if _range < self.current_ports["LOW"] and port == "HIGH":
            raise ValueError(
                "High range port selected when the low range port should be used! Consider using a different multimeter."
            )

        self._set_measurement_mode("current_ac", _range)

    def current_dc(self, _range, port: Literal["HIGH", "LOW"]):
        """
        Set the measurement mode on the DMM to DC current.

        If the range and port selection are not compatible, i.e. someone has requested to measure
        1A on the low range port with a maximum capability of 400 mA, an exception is raised.

        If the range requested can be measured by the low port, but the high port is selected, an
        exception is raised.
        """

        # Check the requested range is not more than the port capability:
        if _range > self.current_ports[port]:
            raise ValueError(
                "The selected port and range combination is not available for this instrument. Consider using a different multimeter"
            )

        # Raise an error if the high port is selected when the low port should be used:
        if _range < self.current_ports["LOW"] and port == "HIGH":
            raise ValueError(
                "High range port selected when the low range port should be used! Consider using a different multimeter."
            )

        self._set_measurement_mode("current_dc", _range)

    def resistance(self, _range=None):
        self._set_measurement_mode("resistance", _range)

    def fresistance(self, _range=None):
        self._set_measurement_mode("fresistance", _range)

    def frequency(self, _range=None, _volt_range=None):
        if _volt_range:
            self._set_measurement_mode(
                "frequency", _range, suffix=f" ; :SENS:FREQ:VOLT:RANG {_volt_range}"
            )
        else:
            self._set_measurement_mode("frequency", _range)

    def period(self, _range=None, _volt_range=None):
        if _volt_range:
            self._set_measurement_mode(
                "period", _range, suffix=f" ; :SENS:PER:VOLT:RANG {_volt_range}"
            )
        else:
            self._set_measurement_mode("period", _range)

    def capacitance(self, _range=None):
        self._set_measurement_mode("capacitance", _range)

    def diode(self, low_current=True, high_voltage=False):
        """
        Writes configuration string for diode to the DMM
        param _range: value set for the range
        """
        self._set_measurement_mode(
            "diode",
            suffix=f"{int(bool(low_current))}, {int(bool(high_voltage))}",
        )

    def continuity(self):
        """
        Writes configuration string for continuity to the DMM
        param _range: value set for the range
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
        # do we need to set the default filter here?
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

    def set_nplc(self, nplc=None, reset=False):
        if reset is True or nplc is None:
            nplc = self._default_nplc
        elif nplc not in self._nplc_settings:
            raise ParameterError(f"Invalid NPLC setting {nplc}")

        if self._mode not in self._nplc_modes:
            raise ParameterError(f"NPLC setting not available for mode {self._mode}")

        mode_str = f"{self._modes[self._mode]}"

        # Remove the CONF: from the start of the string
        mode_str = mode_str.replace("CONF:", "")

        self._write(f"{mode_str}:NPLC {nplc}")  # e.g. VOLT:DC:NPLC 10

    def get_nplc(self):
        mode_str = f"{self._modes[self._mode]}"
        # Remove the CONF: from the start of the string
        mode_str = mode_str.replace("CONF:", "")
        return float(self.instrument.query(f"{mode_str}:NPLC?"))
