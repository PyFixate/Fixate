import struct
from fixate.core.exceptions import InstrumentError
from fixate.drivers.dso.helper import DSO
import time


class MSO_X_3000(DSO):
    REGEX_ID = "AGILENT TECHNOLOGIES,[DM]SO-X"
    INSTR_TYPE = "VISA"
    retrys_on_timeout = 1

    def __init__(self, instrument):
        super().__init__(instrument)
        self.display = "on"
        self.is_connected = True
        self.reset()
        self.instrument.query_delay = 0.2
        del self.instrument.timeout

    def acquire(self, acquire_type="normal", averaging_samples=0):
        """
        :param channel
         string indicating the channel eg. 1, 2, 3, 4, func (func includes math functions)
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
        wav_form_dict = {"0": "BYTE",
                         "1": "WORD",
                         "4": "ASCii"}
        acq_type_dict = {"0": "NORMAL",
                         "1": "PEAK",
                         "2": "AVERAGE",
                         "3": "HIGH RESOLUTION"}
        labels = ["format", "acquire", "wav_points", "avg_cnt", "x_increment", "x_origin", "x_reference", "y_increment",
                  "y_origin", "y_reference"]
        preamble = {}
        for index, val in enumerate(values):
            if index == 0:
                preamble["format"] = wav_form_dict[str(int(values[0]))]
            elif index == 1:
                preamble["acquire"] = acq_type_dict[str(int(values[1]))]
            else:
                preamble[labels[index]] = val
        return preamble

    def waveform_values(self, signals, file_name='', file_type='csv'):
        """
        :param signals:
         The channel ie "1", "2", "3", "4", "MATH", "FUNC"
        :param file_name:
         If
        :param file_type:
        :return:
        """
        signals = self.digitize(signals)
        return_vals = {}
        for sig in signals:
            return_vals[sig] = []
            results = return_vals[sig]
            self.write(":WAV:SOUR {}".format(sig))
            self.write(":WAV:FORM BYTE")
            self.write(":WAV:POIN:MODE RAW")
            preamble = self.waveform_preamble()
            data = self.retrieve_waveform_data()
            for index, datum in enumerate(data):
                time_val = index * preamble["x_increment"]
                y_val = preamble["y_origin"] + (datum - preamble["y_reference"]) * preamble["y_increment"]
                results.append((time_val, y_val))
        if file_name and file_type == 'csv':  # Needs work for multiple references
            with open(file_name, 'w') as f:
                f.write("x,y")
                for label in sorted(preamble):
                    f.write(",{},{}".format(label, preamble[label]))
                f.write('\n')
                for time_val, y_val in enumerate(results):
                    f.write("{time_val},{voltage}\n".format(time_val=time_val, voltage=y_val))
        elif file_name and file_type == 'bin':
            raise NotImplemented("Binary Output not implemented")
        return results

    def retrieve_waveform_data(self):
        self.instrument.write(":WAV:DATA?")
        time.sleep(0.2)
        data = self.read_raw()[:-1]  # Strip \n
        if data[0:1] != '#'.encode():
            raise InstrumentError("Pound Character missing in waveform data response")
        valid_bytes = data[int(data[1:2]) + 2:]  # data[1] denotes length value digits
        values = struct.unpack("%dB" % len(valid_bytes), valid_bytes)
        return values

    def measure_frequency(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_values(":MEAS:FREQ? {}".format(signal))

    def measure_phase(self, signal, reference):
        reference = self.validate_signal(reference)
        signal = self.validate_signal(signal)
        signal = self.digitize(signal)
        return self.query_ascii_value(":MEAS:PHAS? {} {}".format(signal, reference))

    def measure_v_pp(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:VPP? {}".format(signal))

    def measure_v_rms(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:VRMS? CYCLe,{}".format(signal))

    def measure_v_max(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:VMAX? {}".format(signal))

    def measure_v_min(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:VMIN? {}".format(signal))

    def measure_x_min(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:XMIN? {}".format(signal))

    def measure_x_max(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:XMAX? {}".format(signal))

    def measure_pulse_width(self, signal):
        signal = self.validate_signal(signal)
        return self.query_ascii_value(":MEAS:PWIDth? {}".format(signal))

    def digitize(self, signals):
        signals = [self.validate_signal(sig) for sig in signals]
        self.write(":DIG {}".format(','.join(signals)))
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
        self.write("*CLS")
        self.write("*RST")

    def auto_scale(self):
        self.write(":AUT")

    def save_setup(self, file_name):
        with open(file_name, 'w') as f:
            setup = self.query(":SYSTem:SETup?")
            f.write(setup)

    def load_setup(self, file_name):
        with open(file_name, 'r') as f:
            setup = f.read()
        self.write(":SYSTem:SETup {}".format(setup))

    def query(self, value):
        try:
            response = self.instrument.query(value)
        finally:
            self._raise_if_error()
        return response

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

    def write(self, value):
        self.instrument.write(value)
        self._raise_if_error()

    def read_raw(self):
        data = self.instrument.read_raw()
        self._raise_if_error()
        return data

    def _check_errors(self):
        resp = self.instrument.query("SYST:ERR?")
        code, msg = resp.strip('\n').split(',')
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
            raise InstrumentError("Error(s) Returned from DSO\n" +
                                  "\n".join(["Code: {}\nMessage:{}".format(code, msg) for code, msg in errors]))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()
        self.is_connected = False
