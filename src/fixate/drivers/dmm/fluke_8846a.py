from threading import Lock
from visa import constants
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.core.common import mode_builder
from fixate.drivers.dmm.helper import DMM
import time

MODES = {
    ":VOLTage": {
        ":DC": {
            "[:RATio]": {},
            " [{range}]":
                {", [{resolution}]": {}}},
        ":AC": {
            " [{range}]": {
                ", [{resolution}]": {}}}},
    ":CURRent": {
        ":DC": {
            " [{range}]": {
                ", [{resolution}]": {}}},
        ":AC": {
            " [{range}]": {
                ", [{resolution}]": {}}}},
    ":RESistance": {
        " [{range}]": {
            ", [{resolution}]": {}}},
    ":FRESistance": {
        " [{range}]": {
            ", [{resolution}]": {}}},
    ":FREQuency": {
        " [{range}]": {
            ", [{resolution}]": {}}},
    ":PERiod": {
        " [{range}]": {
            ", [{resolution}]": {}}},
    ":CAPacitance": {
        " [{range}]": {
            ", [{resolution}]": {}}},
    ":TEMPerature": {
        ":FRTD": {
            " [{RTD_type}]": {}},
        ":RTD": {
            " [{RTD_type}]": {}}},
    ":CONTinuity": {},
    ":DIODe": {
        " [{low_current}]": {
            ", [{high_voltage}]": {}}}
}

FILTERS = {
    "[SENSe:VOLTage]": {
        "[:DC]:FILTer:STATe ON; VOLTage:DC:FILTEr:DIGital:STATe OFF": {},
        ":AC:BANDwidth 20": {}},
    "[SENSe:CURRent]": {
        "[:DC]:FILTer:STATe ON; CURRent:DC:FILTEr:DIGital:STATe OFF": {},
        ":AC:BANDwidth 20": {}},
    "[SENSe:RESistance]:FILTer:STATe ON; RESistance:FILTEr:DIGital:STATe OFF": {},
    "[SENSe:FRESistance]:FILTer:STATe ON; FRESistance:FILTEr:DIGital:STATe OFF": {}
}


class Fluke8846A(DMM):
    """
    TODO Implement changing between RMS and Vpp.
    Force Vpp as default and call it explicitly when setting amplitude
    """
    REGEX_ID = "FLUKE,8846A"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument):
        super().__init__(instrument)
        instrument.rtscts = 1
        self.lock = Lock()
        self.display = "on"
        # del self.instrument.timeout
        self.instrument.timeout = 10000
        self.instrument.query_delay = 0
        self.instrument.delay = 0
        self.is_connected = True
        self.reset()
        self._CLEAN_UP_FLAG = False
        self._ANALOG_FLAG = False
        self._DIGITAL_FLAG = False
        self._range_string = ""
        self._bandwidth = None
        self._mode = None
        self._rtd_type = ""
        self._diode_str = ""
        self._range = None
        self._modes = {
            'voltage_ac': 'CONF:VOLTage:AC',
            'voltage_dc': 'CONF:VOLTage:DC',
            "current_ac": 'CONF:CURRent:AC',
            "current_dc": 'CONF:CURRent:DC',
            "resistance": 'CONF:RESistance',
            "fresistance": 'CONF:FRESistance',
            "period": 'CONF:PERiod',
            'frequency': 'CONF:FREQuency',
            "temperature": 'CONF:TEMPerature:RTD',
            "ftemperature": 'CONF:TEMPerature:FRTD',
            "capacitance": 'CONF:CAPacitance',
            "continuity": 'CONF:CONTinuity',
            "diode": 'CONF:DIODe'
        }
        self._filters = {
            'voltage_ac': 'SENS:VOLT:AC',
            'voltage_dc': 'SENS:VOLT:DC',
            "current_ac": 'SENS:CURR:AC',
            "current_dc": 'SENS:CURR:DC',
            "resistance": 'SENS:RES',
            'fresistance': 'SENS:FRES',
            None: ""
        }
        self._init_string = ""  # Unchanging
        self._range = {
            'voltage_ac': 'SENS:VOLT:RANG:',
            'voltage_dc': 'SENS:VOLT:RANG:',
            'current_ac': 'SENS:CURR:AC:RANG:',
            'current_dc': 'SENS:CURR:DC:RANG:',
            'resistance': 'SENS:RES:RANG:',
            'fresistance': 'SENS:RES:RANG:',
            'period': 'SENS:PER:VOLT:RANG:',
            'frequency': 'SENS:FREQ:VOLT:RANG:',
            'temperature': 'SENS:TEMP:RANG:RTD',
            'ftemperature': 'SENS:TEMP:RANG:FRTD',
            'capacitance': 'SENS:CAP:RANG:',
            None: "",
        }  # Set by property

        self._resolution = {
            'voltage_ac': 'VOLT:RES',
            'voltage_dc': 'VOLT:RES',
            'current_ac': 'CURR:AC:RES',
            'current_dc': 'CURR:DC:RES',
            'resistance': 'RES:RES',
            'fresistance': 'RES:RES',
            'capacitance': 'CAP:RES',
            None: "",
        }

    def measure(self, *mode, trigger=True, **mode_params):
        """
         if parameters empty then uses previous set mode
         The mode and mode parameters are used in mode_build to search recursively through the
         MODES dictionary to build the visa string necessary for the equipment to interpret the commands.
         usage
         measure('volt', 'dc')
            parsed to visa:
                'CONF:VOLTage:DC'
                'SENSe:VOLTage:DC:FILTer:STATe ON'
                'SENSe:VOLTage:DC:FILTer:DIGital:STATe OFF'
            which is setting the voltage to dc with the analog filter on
         measure('cur', 'ac', range=1)
            parsed to visa:
                'CONF:CURRent:AC'
                'SENSe:CURRent:AC:BANDwidth 20'
            which is setting the current to ac with the 20Hz filter enabled

        for more advanced functions that cannot be explained with this function use adv_measure

        NOTE:
        Since updating the API, the measure() method has been changed to maintain backward compatibility.  measure()
        still users mode_builder() to match the string entered with the mode string to be written, however instead of
        writing this to the dmm, this configuration mode string is used to call the new API mode setters.
        """
        if mode:
            self.reset()

            with self.lock:
                self._write(["SYST:REM", "TRIG:DEL:AUTO OFF", "TRIG:SOUR IMM", "TRIG:COUN {}".format(self.samples)])

                _measure_mode_string = "CONF{}".format(
                    mode_builder(MODES, {}, *mode, **mode_params))  # removed the list brackets

                set_mode = [k for k, v in self._modes.items() if v in _measure_mode_string][0]
                self._set_measurement_mode(set_mode, _range=mode_params.get('range', None))
                # discard first reading
                if trigger:
                    self._read_measurements()

        if trigger:
            # measurements = self.instrument.query_ascii_values("READ?")
            # self._is_error()
            measurements = self._read_measurements()
            return measurements

    def measurement(self):
        """
        Sets up DMM triggering, creates list of measurements from the read buffer
        returns: a single value as a float
        """

        if not self.mode:
            raise InstrumentError('Please set DMM mode before taking a measurement!')

        with self.lock:
            self._write(["SYST:REM", "TRIG:DEL:AUTO OFF", "TRIG:SOUR IMM", "TRIG:COUN 1"])
            self.samples = 1
            measurements = self._read_measurements()
            return measurements[0]

    def reset(self):
        """
        Checks for errors and then returns DMM to power up state
        """
        with self.lock:
            self._is_error(silent=True)
            self._write(["*rst", "SYST:REM", "*cls", "disp {}".format(self.display)])
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
        values = self.instrument.query_ascii_values("READ?")
        self._is_error()
        return values

    def _check_errors(self):
        """
        Queries the DMM for errors and splits the resp string into the message and error code
        return: Error code and Error msg
        """
        resp = self.instrument.query("SYST:ERR?")
        try:
            code, msg = resp.strip('\n').split(',')
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
                raise InstrumentError("Error(s) Returned from DMM\n" +
                                      "\n".join(["Code: {}\nMessage:{}".format(code, msg) for code, msg in errors]))

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

        # Setting up previous measurement
        self._write(self._build_mode_string())

        if self._ANALOG_FLAG:
            self.analog_filter(self._bandwidth or None)
        elif self._DIGITAL_FLAG:
            self.digital_filter()
        self._write(["SYST:REM", "TRIG:DEL:AUTO OFF", "TRIG:SOUR IMM", "TRIG:COUN {}".format(self.samples)])

    def _build_mode_string(self):
        """
        Creates list of configuration strings and combines into a single string
        return: Configuration string
        """
        build_list = [self._modes.get(self._mode, ""), self._range_string, self._rtd_type,
                      self._diode_str]
        build_string = " ".join([x for x in build_list if x != ''])

        return build_string

    def _set_measurement_mode(self, mode, _range=None):
        """
        Helper function used to set the measurement mode for voltage_ac, voltage_dc, current_ac, current_dc,
        resistance, fresistance. Reduces previous duplicate code.
        :param mode:
        :param _range:
        :param _resolution:
        :return:
        """
        self.mode = mode
        self.range = _range
        self._write(self._build_mode_string())
        self._is_error()

    def voltage_ac(self, _range=None):
        self._set_measurement_mode('voltage_ac', _range)

    def voltage_dc(self, _range=None):
        self._set_measurement_mode('voltage_dc', _range)

    def current_ac(self, _range=None, bandwidth=None):
        self._set_measurement_mode('current_ac', _range)

    def current_dc(self, _range=None):
        self._set_measurement_mode('current_dc', _range)

    def resistance(self, _range=None):
        self._set_measurement_mode('resistance', _range)

    def fresistance(self, _range=None):
        self._set_measurement_mode('fresistance', _range)

    def frequency(self, _range=None):
        self._set_measurement_mode('frequency', _range)

    def period(self, _range=None):
        self._set_measurement_mode('period', _range)

    def capacitance(self, _range=None):
        self._set_measurement_mode('capacitance', _range)

    def diode(self, low_current=True, high_voltage=False):
        """
        Writes configuration string for diode to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        self._diode_str = "{} {}".format(int(bool(low_current)), int(bool(high_voltage)))
        self._set_measurement_mode('diode')

    def continuity(self):
        """
        Writes configuration string for continuity to the DMM
        param _range: value set for the range
        param _resolution: value set for the resolution
        """
        self._set_measurement_mode('continuity')

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
        self._DIGITAL_FLAG = False
        self._ANALOG_FLAG = False
        self._range_string = ""
        self._resolution_string = ""
        if value not in self._modes:
            raise ParameterError('Unknown mode {} for DMM'.format(value))
        if self.mode != value:
            self._mode = value
        else:
            pass

    def digital_filter(self):
        """
        Sets up DMM digital filtering
        raise: TypeError if trying to set digital filter in an AC mode
        """
        self._DIGITAL_FLAG = True
        if "ac" in self._mode:
            raise TypeError
        self._write(self._filters[self.mode] + ":FILT:DIG:STAT ON")
        pass

    def analog_filter(self, bandwidth=None):
        """
        Sets up DMM analog filtering.  Writes the different filter strings depending on the configuration mode.  Hence,
        configuration must be set before calling filter.
        raise: ValueError if invalid filtering bandwidth is requested
        """
        self._ANALOG_FLAG = True
        if "ac" in self._mode:
            self._bandwidth = bandwidth or 20
            if self._bandwidth not in [3, 20, 200]:
                raise ValueError
            self._write(self._filters[self.mode] + ":BAND {}".format(self._bandwidth))

        elif any(x in self._mode for x in ["dc", "res"]):
            self._write(self._filters[self.mode] + ":FILT:STAT ON")
        pass

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, set_range=None):
        """
        Creates range string for configuration string
        param set_range: user defined value for the range
        """
        try:
            self._range = float(set_range)
            self._range_string = "{}".format(self.range)
        except TypeError:
            self._range = None
            self._range_string = ""
