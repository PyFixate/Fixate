from threading import Lock
from math import log10, floor
import time
from contextlib import contextmanager

from pyvisa import VisaIOError
from pyvisa.errors import VI_ERROR_TMO

from fixate.core.exceptions import InstrumentError, ParameterError, InstrumentTimeOut
from fixate.drivers.lcr.helper import LCR, TestResult
from fixate.core.common import unit_scale, unit_convert

"""
FUNC <OPTION>
- R
- L
- C
- Z
- ESR

FREQ <OPTION>
- 100
- 120
- 1k
- 10k

MODE <OPTION>
- SER
- PAL

RANG <OPTION>
For R
- 2
- 20
- 200
- 2k
- 20k
- 200k
- 2M
- 20M
- 200M
For L
- 2000u
- 20m
- 200m
- 2
- 20
- 200
- 2k
For C
- 2000p
- 20n
- 200n
- 2000n
- 20u
- 200u
- 20m
For Z
- 2
- 20
- 200
- 2k
- 20k
- 200k
- 2M
- 20M
- 200M
For ESR
None
DISP2 <OPTION>
- TH
- Q
- D

FETC? ALL
'\nRs, +x.xxxxxE+xx, Cs, +x.xxxxxE+xx, Rp, +x.xxxxxE+xx, Cp, +x.xxxxxE+xx, Z, +x.xxxxxE+xx, TH, +x.xxxxxE+xx, F,
+x.xxxxxE+xx, D, +x.xxxxxE+xx, Q, +x.xxxxxE+xx'
"""


class AgilentU1732C(LCR):
    REGEX_ID = "Agilent Technologies,U1732C"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument):
        super().__init__(instrument)
        self.lock = Lock()
        self.reset()
        self.instrument.delay = 0.1
        self.instrument.timeout = 2
        self.write_delay = 1  # 0.8sec delay minimum for reliable use
        self.read_delay = 0.05
        self._range = None
        self._frequency = 100

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, val):
        if val not in [100, 120, 1e3, 10e3, "100", "120", "1k", "10k"]:
            raise ParameterError("Frequency must be either '100', '120', '1k' or '10k'")
        self._frequency = val
        try:
            val = unit_convert(val, 1, 200)
        except TypeError:
            pass
        self._write("FREQ {}".format(val))

    @property
    def range(self):
        return self._range

    @range.setter
    def range(self, val):
        rng = unit_scale(str(val))
        if not rng == round(rng, -int(floor(log10(rng)))):
            raise ParameterError()
        if str(rng)[0] != "2":
            raise ParameterError()
        if not 2000e-9 <= rng <= 200e6:
            raise ParameterError()
        self._range = val
        self._write("RANG {}".format(unit_convert(rng, 2, 2000)))

    def measure(
        self, func=None, disp2=None, multiple_results=False, trigger=True, **mode_params
    ):
        """
        func
        - L Inductance
        - C Capacitance
        - R Resistance
        - Z Impedance
        - ESR Equivalent Series Resistance

        returns a namedtuple of the results from the meter.
        usage:
        >>>lcr = lcr.open()
        >>>result = lcr.measure(func='C', multiple_results=True)
        result.Rs #Resistance Series
        result.Cs #Capacitance Series
        result.Rp #Resistance Parallel
        result.Cp #Capacitance Parallel
        result.Z #Impedance
        result.TH #Phase
        result.F #Frequency
        result.D #
        result.Q #

        >>>result = lcr.measure(func='L', multiple_results=True)
        result.Rs #Resistance Series
        result.Ls #Inductance Series
        result.Rp #Resistance Parallel
        result.Lp #Inductance Parallel
        result.Z #Impedance
        result.TH #Phase
        result.F #Frequency
        result.D #
        result.Q #
        >>>result.Cs
        None

        # Getting a single result back
        >>>result = lcr.measure(func='ESR')
        >>>print(result)
        9.3888e-08
        >>>result.Rs
        AttributeError
        """
        if disp2 is not None:
            if disp2.upper() not in ["TH", "Q", "D"]:
                raise ParameterError("Display 2 must be either 'TH', 'Q' or 'D'")
            self._write("DISP2 {}".format(disp2))
        if func is not None:
            if func.upper() not in ["L", "C", "R", "Z", "ESR"]:
                raise ParameterError("Func must be either 'L', 'C', 'R', 'Z' or 'ESR'")
            self._write("FUNC {}".format(func))

        return self._read_measurement(multiple_results)

    def reset(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()

    def _write(self, data):
        try:
            if data:
                if isinstance(data, str):
                    self.instrument.write(data)
                    time.sleep(self.write_delay)
                else:
                    for itm in data:
                        self.instrument.write(itm)
                        time.sleep(self.write_delay)
                # self._is_error()
            else:
                raise ParameterError("Missing data in instrument write")
        except VisaIOError as e:
            # TODO Write to log
            raise InstrumentError("Unknown IO error from read operation") from e

    def _read(self):
        try:
            return self.instrument.read()
        except VisaIOError as e:
            # TODO Write to log
            if e.error_code == VI_ERROR_TMO:
                raise InstrumentTimeOut("Instrument Timed out on read operation") from e
            raise InstrumentError("Unknown IO error from read operation") from e

    def _read_measurement(self, multiple):
        with self.lock:
            if multiple:
                self._write("FETC? ALL")
                # Flushes the buffer if there are any other commands left over
                while True:
                    time.sleep(self.read_delay)
                    try:
                        measurements = self._read().strip("\n").split(",")
                        return TestResult(
                            **dict(
                                zip(
                                    measurements[0::2],
                                    [float(x) for x in measurements[1::2]],
                                )
                            )
                        )
                    except ValueError:
                        pass
                    except IndexError:
                        pass
            else:
                self._write("FETC?")
                # Flushes the buffer if there are any other commands left over
                while True:
                    time.sleep(self.read_delay)
                    try:
                        return float(self._read())
                    except ValueError:
                        pass

    def _is_error(self):
        self.instrument.write("SYST:ERR?")
        time.sleep(self.write_delay)
        err_resp = self._read()
        if "no error" not in err_resp.lower():
            raise InstrumentError(err_resp)

    @contextmanager
    def instrument_timeout(self, duration):
        """
        context manager for temporarily changing the instrument timeout value
        :param duration: timeout length in ms
        :return:
        """
        previous_timeout = self.instrument.timeout
        try:
            self.instrument.timeout = duration
            yield
        finally:
            self.instrument.timeout = previous_timeout

    def get_identity(self) -> str:
        """
        Can't find programmers manual to explain what these parameters are
        Best guess is <manufacturer><model><serial><some sort of software version>
        :return: e.g. "Agilent Technologies,U1732C,MY54510075\u0000\u0000,00.28"
        """
        # not sure why the default timeout is 2ms, we need a few hundred to reliably get the IDN string

        with self.instrument_timeout(1000):
            idn = self.instrument.query("*IDN?")
            # filter out nulls and escape characters
            return "".join(filter(str.isprintable, idn))
