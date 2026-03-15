import pyvisa
from fixate.core.exceptions import InstrumentError
from fixate.drivers.dso.helper import DSO
import time


# Example IDN Strings
# KEYSIGHT TECHNOLOGIES,DSOX1202G,CN60074190,02.10.2019111333
# KEYSIGHT TECHNOLOGIES,DSO-X 1102G,CN57096441,01.20.2019061038
# AGILENT TECHNOLOGIES,MSO-X 3014A,MY51360314,02.43.2018020635
class MSO_X_3000(DSO):
    # Regex needs work to detect only the 4 channel scopes we have:
    REGEX_ID = "(KEYSIGHT|AGILENT) TECHNOLOGIES,[DM]SO-?X"
    INSTR_TYPE = "VISA"
    retrys_on_timeout = 1

    def __init__(self, instrument):
        super().__init__(instrument)
        self.display = "on"
        self.is_connected = True
        self._mode = "STOP"
        self._wave_acquired = False
        self._triggers_read = 0

        self.reset()
        self.instrument.query_delay = 0.2
        self.instrument.timeout = 1000

        # If, for example this does not have 4 channels, we can do:
        # We would actually call some function like not_availalbe() that would raise a better error
        self.ch3 = lambda: 1 / 0
        self.ch4 = lambda: 1 / 0

    def single(self) -> None:
        """
        Specific implementation of the single trigger setup for Agilent MSO-X
        """
        self._triggers_read = 0
        self._raise_if_error()  # Raises if any errors were made during setup
        # Stop
        # Clear status registers (CLS)
        self.instrument.write(":STOP;*CLS")
        self._store["time_base_wait"] = (
            self.instrument.query_ascii_values(":TIM:RANG?")[0]
            + self.instrument.query_ascii_values(":TIM:POS?")[0]
        )
        # Enables the Event service request register (SRE)
        # Currently we're not using events. wait_on_trigger is polling. The current implementation
        # doesn't work when using a LAN connection to the instrument, so we will comment out for now
        # self.instrument.enable_event(visa.constants.EventType.service_request, visa.constants.VI_QUEUE)
        self.instrument.write(":SINGLE")
        while True:
            if self.instrument.query_ascii_values(":AER?")[0]:
                break
            time.sleep(0.1)

        self._mode = "SINGLE"
        self._wave_acquired = False

    def run(self):
        self._triggers_read = 0
        self.write(":STOP;*CLS")
        # Currently we're not using events. wait_on_trigger is polling. The current implementation
        # doesn't work when using a LAN connection to the instrument, so we will comment out for now
        # self.instrument.enable_event(visa.constants.EventType.service_request, visa.constants.VI_QUEUE)
        self.instrument.write(":RUN")
        while True:
            if self.instrument.query_ascii_values(":AER?")[0]:
                break
            time.sleep(0.1)
        self._mode = "RUN"
        self._wave_acquired = False

    def stop(self):
        self._triggers_read = 0
        self.instrument.write(":STOP")
        self._mode = "STOP"
        self._wave_acquired = False

    def _write(self, value):
        self.instrument.write(value)

    def acquire(self, acquire_type="normal", averaging_samples=0):
        """
        :param channel
         string indicating the channel eg. 1, 2, 3, 4, FUNC,(FUNC,includes MATH,functions)
        :param acquire_type:
         "normal"
         "averaging"
         "hresolution" - High Resolution
         "peak" - Peak Detect
        :param averaging_samples:
         averaging_samples: number of samples used when acquire_type is set to averaging
        :return:
        """
        self.write("TIMebase:MODE MAIN")
        if acquire_type.lower() == "normal":
            self.write(":ACQuire:TYPE normal")
        elif acquire_type.lower() == "averaging":
            self.write(":ACQuire:TYPE average")
            self.write(":ACQuire:COUNt {}".format(averaging_samples))
        elif acquire_type.lower() == "hresolution":
            self.write(":ACQuire:TYPE hresolution")
        elif acquire_type.lower() == "peak":
            self.write(":ACQuire:TYPE peak")
        else:
            raise ValueError("Invalid acquire type {}".format(acquire_type))

    def waveform_preamble(self):
        values = self.query_ascii_values(":WAV:PRE?")
        wav_form_dict = {"0": "BYTE", "1": "WORD", "4": "ASCii"}
        acq_type_dict = {
            "0": "NORMAL",
            "1": "PEAK",
            "2": "AVERAGE",
            "3": "HIGH RESOLUTION",
        }
        labels = [
            "format",
            "acquire",
            "wav_points",
            "avg_cnt",
            "x_increment",
            "x_origin",
            "x_reference",
            "y_increment",
            "y_origin",
            "y_reference",
        ]
        preamble = {}
        for index, val in enumerate(values):
            if index == 0:
                preamble["format"] = wav_form_dict[str(int(values[0]))]
            elif index == 1:
                preamble["acquire"] = acq_type_dict[str(int(values[1]))]
            else:
                preamble[labels[index]] = val
        return preamble

    def waveform_values(self, signal, file_name="", file_type="csv"):
        """
        Retrieves currently present waveform data from the specified channel and optionally saves it to a file.
        The oscilliscope must be in the stopped state to retrive waveform data.

        This method queries the instrument for raw data points, scales them using
        the waveform preamble (origin, increment, and reference values), and
        converts them into time and voltage arrays.

        Args:
            signal (str|int): The source channel (e.g., 1, "2").
            file_name (str, optional): The path/name of the file to save data to.
                Defaults to "", which skips file saving.
            file_type (str, optional): The format for the output file.
                Supported: "csv". Defaults to "csv".

        Returns:
            tuple: A tuple containing (time_values, values) as lists of floats.

        Raises:
            ValueError: If no data is available on the selected channel.
            NotImplementedError: If an unsupported file_type is requested.
        """
        try:
            # If the channel is not able to be converted to an int, then its almost definitely not an analogue source
            # i.e. you might have requested "math" or "function" that is not supported by this method.
            int_signal = int(signal)
        except ValueError:
            raise ValueError(
                "Please select an analog channel. Math or function channels are not supported."
            )

        # Exit early if the requested channel is not currently displayed:
        ch_state = int(self.instrument.query(f":CHANnel{int_signal}:DISPlay?"))
        if not ch_state:
            raise ValueError("Requested channel is not active!")

        # Set the channel:
        self.instrument.write(f":WAVeform:SOURce CHANnel{int_signal}")
        # Explicitly set this to avoid confusion
        self.instrument.write(":WAVeform:FORMat BYTE")
        self.instrument.write(":WAVeform:UNSigned 0")

        # Pick the points mode depending on the current acquisiton mode:
        acq_type = str(self.instrument.query(":ACQuire:TYPE?")).strip("\n")
        if acq_type == "AVER" or acq_type == "HRES":
            points_mode = "NORMal"
            # Use for Average and High Resoultion acquisition Types.
            # If the :WAVeform:POINts:MODE is RAW, and the Acquisition Type is Average, the number of points available is 0. If :WAVeform:POINts:MODE is MAX, it may or may not return 0 points.
            # If the :WAVeform:POINts:MODE is RAW, and the Acquisition Type is High Resolution, then the effect is (mostly) the same as if the Acq. Type was Normal (no box-car averaging).
            # Note: if you use :SINGle to acquire the waveform in AVERage Acq. Type, no average is performed, and RAW works.
        else:
            points_mode = "RAW"  # Use for Acq. Type NORMal or PEAK

        # This command sets the points mode to MAX AND ensures that the maximum # of points to be transferred is set, though they must still be on screen
        self.instrument.write(":WAVeform:POINts MAX")
        # The above command sets the points mode to MAX. So we set it here to make sure its what we want.
        self.instrument.write(":WAVeform:POINts:MODE " + points_mode)

        # Check if there is actually data to acquire:
        data_available = int(self.query(":WAVeform:POINTs?"))
        if data_available == 0:
            # No data is available
            # Setting a channel to be a waveform source turns it on, so we need to turn it off now:
            self.write(f":CHANnel{int_signal}:DISPlay OFF")
            raise ValueError("No data is available")

        preamble = self.waveform_preamble()
        # Grab the data from the scope:
        # datatype definition is "b" for byte. See struct module details.
        data = self.instrument.query_binary_values(
            ":WAV:DATA?", datatype="b", is_big_endian=True
        )

        x = []
        y = []
        # Modify some things if we are in peak detect mode:
        data_len = int(len(data) / 2) if acq_type == "PEAK" else len(data)
        multiplier = 2 if acq_type == "PEAK" else 1
        for i in range(data_len):
            x_val = (i - preamble["x_reference"]) * preamble["x_increment"] + preamble[
                "x_origin"
            ]

            if acq_type == "PEAK":
                # We need to double up on the time index
                # In peak detect mode, the points come out as low(t1),high(t1),low(t2),high(t2)
                y_min = (
                    preamble["y_origin"]
                    + (data[i * multiplier] - preamble["y_reference"])
                    * preamble["y_increment"]
                )
                y_max = (
                    preamble["y_origin"]
                    + (data[i * multiplier + 1] - preamble["y_reference"])
                    * preamble["y_increment"]
                )
                x.append(x_val)
                x.append(x_val)
                y.append(y_min)
                y.append(y_max)

            else:
                y_val = (
                    preamble["y_origin"]
                    + (data[i] - preamble["y_reference"]) * preamble["y_increment"]
                )

                x.append(x_val)
                y.append(y_val)

        if file_name and file_type == "csv":
            with open(file_name, "w") as f:
                f.write("x,y\n")
                for x_val, y_val in zip(x, y):
                    f.write(f"{x_val},{y_val}\n")

        elif file_name and file_type == "bin":
            raise NotImplementedError("Binary Output not implemented")
        return x, y

    def digitize(self, signals):
        signals = [self.validate_signal(sig) for sig in signals]
        self.write(":DIG {}".format(",".join(signals)))
        return signals

    def validate_signal(self, signal):
        """
        :param signal: String ie. "1", "2", "3", "4", "func", "math"
        :return:
        """
        try:
            if not (1 <= int(signal) <= 4):
                raise ValueError("Invalid source channel {}".format(signal))
            else:
                signal = "CHAN{}".format(int(signal))
        except ValueError:
            if signal.lower() not in ["func", "math"]:
                raise ValueError("Invalid source channel {}".format(signal))
            signal = signal.lower()
        return signal

    def reset(self):
        self.instrument.write("*CLS;*RST;:STOP")
        time.sleep(0.15)
        self._check_errors()

    def auto_scale(self):
        self.write(":AUT")

    def save_setup(self, file_name):
        self.instrument.timeout = 5000
        try:
            with open(file_name, "w") as f:
                setup = self.query(":SYSTem:SETup?")
                f.write(setup)
        finally:
            self.instrument.timeout = 1000

    def load_setup(self, file_name):
        self.instrument.timeout = 5000
        try:
            with open(file_name, "r") as f:
                setup = f.read()
            self.write(":SYSTem:SETup {}".format(setup))
        finally:
            self.instrument.timeout = 1000

    def query(self, value):
        try:
            response = self.instrument.query(value)
        finally:
            self._raise_if_error()
        return response

    def query_bool(self, value):
        return bool(self.query_ascii_value(value))

    def query_binary_values(self, value):
        response = self.instrument.query_binary_values(value)
        self._raise_if_error()
        return response

    def query_ascii_values(self, value):
        response = self.instrument.query_ascii_values(value)
        self._raise_if_error()
        return response

    def query_ascii_value(self, value):
        return self.query_ascii_values(value)[0]

    def query_value(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        return self.query_ascii_value(formatted_string)

    def query_after_acquire(self, base_str, *args, **kwargs):
        self.wait_for_acquire()
        try:
            formatted_string = self._format_string(base_str, **kwargs)
            return self.instrument.query_ascii_values(formatted_string)[0]
        except:
            self.instrument.close()
            self.instrument.open()
            raise

    def wait_for_trigger(self, timeout):
        """
        Waits for trigger for a set amount of time.
        If no trigger occurs, cancel the current measurement request
        Two options available:
        self._trigger_event(timeout) # Uses PyVisa Events
        self._trigger_poll(timeout) # Polls :TER? register
        :param timeout: timeout in seconds waiting for a trigger
        Exception raised on timeout
        :return:
        """
        self._trigger_poll(timeout)
        # self._trigger_event(timeout)

    def _trigger_event(self, timeout):
        try:
            self.instrument.wait_on_event(
                pyvisa.constants.EventType.service_request, timeout * 1000
            )
            self._triggers_read += 1
        except pyvisa.VisaIOError:
            self.instrument.clear()
            raise
        finally:
            self.instrument.disable_event(
                pyvisa.constants.EventType.service_request, pyvisa.constants.VI_QUEUE
            )
            self.instrument.discard_events(
                pyvisa.constants.EventType.service_request, pyvisa.constants.VI_QUEUE
            )

    def _trigger_poll(self, timeout):
        start = time.time()
        while True:
            trigger = self.instrument.query_ascii_values(":TER?")[0]
            if trigger:
                break
            if time.time() - start > timeout:
                raise TimeoutError("Trigger didn't occur in {}s".format(timeout))
        self._triggers_read += 1

    def wait_for_acquire(self):
        if not self._triggers_read:
            self.wait_for_trigger(1)
        if self._wave_acquired:
            return

        elif self._mode == "SINGLE":
            # Wait for mode to change to stop
            start = time.time()
            timeout = self._store["time_base_wait"] * 1.2
            while int(self.instrument.query_ascii_values(":OPER:COND?")[0]) & 1 << 3:
                if time.time() - start > timeout:
                    raise TimeoutError("Waveform did not acquire in the specified time")
            self._wave_acquired = True
            return
        elif self._mode == "RUN":
            # Can't detect a complete acquire, just going to have to risk it
            self._wave_acquired = True
            return
        else:
            raise Exception(
                "Cannot acquire waveform in this mode: {}".format(self._mode)
            )

    def read_raw(self):
        data = self.instrument.read_raw()
        self._raise_if_error()
        return data

    def _check_errors(self):
        time.sleep(0.1)
        resp = self.instrument.query("SYST:ERR?")
        code, msg = resp.strip("\n").split(",")
        code = int(code)
        msg = msg.strip('"')
        return code, msg

    def _raise_if_error(self):
        errors = []
        while True:
            code, msg = self._check_errors()
            if code != 0:
                errors.append((code, msg))
            else:
                break
        if errors:
            raise InstrumentError(
                "Error(s) Returned from DSO\n"
                + "\n".join(
                    ["Code: {}\nMessage:{}".format(code, msg) for code, msg in errors]
                )
            )

    def write(self, base_str, *args, **kwargs):
        formatted_string = self._format_string(base_str, **kwargs)
        self._write(formatted_string)

    def _format_string(self, base_str, **kwargs):
        kwargs["self"] = self
        prev_string = base_str
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

    def store_and_write(self, params, *args, **kwargs):
        base_str, store_dict = params
        self.store(store_dict)
        self.write(base_str, *args, **kwargs)

    def get_identity(self) -> str:
        """
        :return: AGILENT TECHNOLOGIES,<model>,<serial number>,X.XX.XX
                <model> ::= the model number of the instrument
                <serial number> ::= the serial number of the instrument
                <X.XX.XX> ::= the software revision of the instrument
        """
        return self.query("*IDN?").strip()
