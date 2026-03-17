import inspect
from abc import ABCMeta, abstractmethod
from typing import Callable, Literal, Union

from fixate.core.exceptions import InstrumentFeatureUnavailable, InstrumentError

number = Union[float, int]

"""
Callbacks
Write and query callbacks get passed down the tree of class variables.

They are then used to facilitate a single point of communication between 
the scope and the PC. This has the benefit of being able to mock the interface.
ie we can create a mock DSO that inherts the base and redefines functions.
"""
WriteCallback = Callable[[str], None]
QueryAsciiValuesCallback = Callable[[str], float]

# Prompt that a featrue is not available:
def unavailable(name: str | None = None):
    label = name or inspect.stack()[1].function
    return InstrumentFeatureUnavailable(f"{label} not available on this device")


class Channel:
    """
    DSO Channel implementation
    """

    def __init__(
        self, channel_name: str, write: WriteCallback, enabled: bool = True
    ) -> None:
        # Set enabled to false to note a device does not have this channel
        self.enabled = enabled
        self._ch_name = channel_name
        self._write = write
        self._ch_cmd = f"CHAN{self._ch_name}"

        self.coupling = Coupling(write, self._ch_cmd)
        self.probe = Probe(write, self._ch_cmd)

    def _check_en(self):
        if not self.enabled:
            raise unavailable(f"{self._ch_cmd} is not available on this device")

    def __call__(self, value: bool):
        self._check_en()
        self._write(f"CHAN1:DISP {int(value)}")

    def scale(self, value: number) -> None:
        self._check_en()
        self._write(f"{self._ch_cmd}:SCAL {value}")

    def offset(self, value: number) -> None:
        self._check_en()
        self._write(f"{self._ch_cmd}:OFFS {value}")

    def invert(self, value: bool) -> None:
        self._check_en()
        self._write(f"{self._ch_cmd}:INV {int(value)}")


class Coupling:
    """
    Defines the coupling interface
    """

    def __init__(self, write: WriteCallback, cmd_prefix: str):
        self._write = write
        self._cmd_prefix = cmd_prefix

    def ac(self) -> None:
        # AC Coupling
        self._write(f"{self._cmd_prefix}:COUP AC")

    def dc(self) -> None:
        # DC Coupling
        self._write(f"{self._cmd_prefix}:COUP DC")


class Probe:
    def __init__(self, write: WriteCallback, cmd_prefix: str):
        self._write = write
        self._cmd_prefix = cmd_prefix

    def attenuation(self, attenuation: number) -> None:
        self._write(f"{self._cmd_prefix}:PROB {attenuation}")


class TimeBase:
    def __init__(self, write: WriteCallback):
        self._write = write

    def scale(self, value: number) -> None:
        self._write(f"TIM:SCAL {value}")

    def position(self, value: number) -> None:
        self._write(f"TIM:POS {value}")


class TriggerCoupling(Coupling):
    """
    Extends the Coupling interface with extra functions that the trigger has
    """

    def lf_reject(self) -> None:
        self._write(f"{self._cmd_prefix}:COUP LFR")


class TriggerSweep:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write

    def auto(self) -> None:
        self._write("TRIG:SWE AUTO")

    def normal(self) -> None:
        self._write("TRIG:SWE NORM")


class TriggerMode:
    """
    Define the trigger mode interface
    """

    def __init__(self, write: WriteCallback):
        self.edge = TriggerEdge(write)


class TriggerSlopes:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write

    def rising(self) -> None:
        self._write("TRIG:EDGE:SLOPE POS")

    def falling(self) -> None:
        self._write("TRIG:EDGE:SLOPE NEG")

    def either(self) -> None:
        self._write("TRIG:EDGE:SLOPE EITH")

    def alternating(self) -> None:
        self._write("TRIG:EDGE:SLOPE ALT")


class TriggerSources:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write

    def ch1(self) -> None:
        self._write("TRIG:EDGE:SOUR CHAN1")

    def ch2(self) -> None:
        self._write("TRIG:EDGE:SOUR CHAN2")

    def ch3(self) -> None:
        self._write("TRIG:EDGE:SOUR CHAN3")

    def ch4(self) -> None:
        self._write("TRIG:EDGE:SOUR CHAN4")


class TriggerEdge:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write
        self.source = TriggerSources(write)
        self.slope = TriggerSlopes(write)

    def __call__(self) -> None:
        self._write("TRIG:MODE EDGE")

    def level(self, value: number) -> None:
        self._write(f"TRIG:EDGE:LEVEL {value}")


class Trigger:
    """
    Trigger base class
    """

    def __init__(self, write: WriteCallback):
        self._write = write

        self.mode = TriggerMode(write)
        self.sweep = TriggerSweep(write)
        self.coupling = TriggerCoupling(write, "TRIG")

    def hf_reject(self, value: bool) -> None:
        self._write(f"TRIG:HFR {int(value)}")


class Acquire:
    def __init__(self, write: WriteCallback):
        self._write = write

    def normal(self) -> None:
        self._write(f"ACQ:TYPE NORM")

    def peak_detect(self) -> None:
        self._write(f"ACQ:TYPE PEAK")

    def averaging(self, value) -> None:
        self._write(f"ACQ:TYPE AVER;:ACQ:COUN {value}")

    def high_resolution(self) -> None:
        self._write(f"ACQ:TYPE HRES")


# Yes this sucks...
class MeasurementBase:
    def __init__(self, query: QueryAsciiValuesCallback, command: str):
        self._query = query
        self._command = command

    def ch1(self):
        return self._query(self._command + " CHAN1")

    def ch2(self):
        return self._query(self._command + " CHAN2")

    def ch3(self):
        return self._query(self._command + " CHAN3")

    def ch4(self):
        return self._query(self._command + " CHAN4")

    def function(self):
        return self._query(self._command + " FUNC")

    def math(self):
        return self._query(self._command + " MATH")


class VAverageMeasurement:
    def __init__(self, query: QueryAsciiValuesCallback) -> None:
        self.cycle = MeasurementBase(query, "MEAS:VAV? CYCL,")
        self.display = MeasurementBase(query, "MEAS:VAV? DISP,")


class VRmsModesMeasurement:
    def __init__(self, query: QueryAsciiValuesCallback, mode: str) -> None:
        self.cycle = MeasurementBase(query, f"MEAS:VRMS? CYCL,{mode},")
        self.display = MeasurementBase(query, f"MEAS:VRMS? DISP,{mode},")


class VRmsMeasurement:
    def __init__(self, query: QueryAsciiValuesCallback) -> None:
        self.dc = VRmsModesMeasurement(query, "DC")
        self.ac = VRmsModesMeasurement(query, "AC")


class SourceSelector:
    """
    Retain compatibility of source selection from the old API
    dso.source1.ch1() for example will set the source1.source = "CHAN1"
    This is then queried by the two source measurement functions like 'delay'
    You must set the sources before calling a multi measurement function.
    """

    def __init__(self, store: dict, source: Literal["source1"] | Literal["source2"]):
        self._store = store
        # Name of the source:
        self.source = source

    def ch1(self) -> None:
        self._store[self.source] = "CHAN1"

    def ch2(self) -> None:
        self._store[self.source] = "CHAN2"

    def ch3(self) -> None:
        self._store[self.source] = "CHAN3"

    def ch4(self) -> None:
        self._store[self.source] = "CHAN4"

    def function(self) -> None:
        self._store[self.source] = "FUNC"

    def math(self) -> None:
        self._store[self.source] = "MATH"

    def wmemory1(self) -> None:
        self._store[self.source] = "WMEM1"

    def wmemory2(self) -> None:
        self._store[self.source] = "WMEM2"


class DefineThreshold:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write

    def percent(self, upper, middle, lower) -> None:
        self._write(f"MEAS:DEF THR,PERC,{upper},{middle},{lower}")

    def absolute(self, upper, middle, lower) -> None:
        self._write(f"MEAS:DEF THR,ABS,{upper},{middle},{lower}")


class Define:
    def __init__(self, write: WriteCallback) -> None:
        self.threshold = DefineThreshold(write)


class DelayEdges:
    def __init__(self, write: WriteCallback) -> None:
        self._write = write

    def rising_rising(self) -> None:
        self._write("MEAS:DEF DEL, +1, +1")

    def rising_falling(self) -> None:
        self._write("MEAS:DEF DEL, +1, -1")

    def falling_rising(self) -> None:
        self._write("MEAS:DEF DEL, -1, +1")

    def falling_falling(self) -> None:
        self._write("MEAS:DEF DEL, -1, -1")


class DelayMeasurement:
    def __init__(
        self, write: WriteCallback, query: QueryAsciiValuesCallback, store: dict
    ) -> None:
        self._write = write
        self._query = query
        self._store = store
        self.edges = DelayEdges(write)

    def __call__(self) -> float:
        return self._query(
            f"MEAS:DEL? {self._store['source1']},{self._store['source2']}"
        )


class VRatioMeasurement:
    def __init__(self, query: QueryAsciiValuesCallback, store: dict) -> None:
        self._query = query
        self._store = store

    def cycle(self) -> float:
        return self._query(
            f"MEAS:VRAT? CYCL,{self._store['source1']},{self._store['source2']}"
        )

    def display(self) -> float:
        return self._query(
            f"MEAS:VRAT? DISP,{self._store['source1']},{self._store['source2']}"
        )


class PhaseMeasurement:
    def __init__(self, query: QueryAsciiValuesCallback, store: dict) -> None:
        self._query = query
        self._store = store

    def __call__(self) -> float:
        return self._query(
            f"MEAS:PHAS? {self._store['source1']},{self._store['source2']}"
        )


class Measure:
    def __init__(
        self, write: WriteCallback, query: QueryAsciiValuesCallback, store: dict
    ) -> None:
        self.counter = MeasurementBase(query, "MEAS:COUN?")
        self.duty = MeasurementBase(query, "MEAS:DUTY?")
        self.fall_time = MeasurementBase(query, "MEAS:FALL?")
        self.rise_time = MeasurementBase(query, "MEAS:RIS?")
        self.frequency = MeasurementBase(query, "MEAS:FREQ?")
        self.cnt_edge_rising = MeasurementBase(query, "MEAS:NEDG?")
        self.cnt_edge_falling = MeasurementBase(query, "MEAS:PEDG?")
        self.cnt_pulse_positive = MeasurementBase(query, "MEAS:NPUL?")
        self.cnt_pulse_negative = MeasurementBase(query, "MEAS:PPUL?")
        self.period = MeasurementBase(query, "MEAS:PER?")
        self.pulse_width = MeasurementBase(query, "MEAS:PWID?")
        self.vamplitude = MeasurementBase(query, "MEAS:VAMP?")
        self.vbase = MeasurementBase(query, "MEAS:VBAS?")
        self.vtop = MeasurementBase(query, "MEAS:VTOP?")
        self.vmax = MeasurementBase(query, "MEAS:VMAX?")
        self.vmin = MeasurementBase(query, "MEAS:VMIN?")
        self.vpp = MeasurementBase(query, "MEAS:VPP?")
        self.xmax = MeasurementBase(query, "MEAS:XMAX?")
        self.xmin = MeasurementBase(query, "MEAS:XMIN?")
        # These need a little more construction to match the old API:
        self.vaverage = VAverageMeasurement(query)
        self.vrms = VRmsMeasurement(query)

        # Multi source measurements:
        self.define = Define(write)
        self.delay = DelayMeasurement(write, query, store)
        self.phase = PhaseMeasurement(query, store)
        self.vratio = VRatioMeasurement(query, store)


class DSO(metaclass=ABCMeta):
    """
    DSO Base class.
    You don't know what version of the scope you will get until run time.
    The regex id is going to be the defining factor as to how many channels the DSO has.

    We can assume for the helper class however that all the functionality is available.
    On runtime, the correct instrument is then selected and will error if its not implemented.
    """

    REGEX_ID: str = "DSO"
    INSTR_TYPE: str = "VISA"

    def __init__(self, instrument):
        self.instrument = instrument
        self.samples = 1

        # Callbacks:
        _write = self._write_cmd
        _query_after_acquire = self._query_after_acquire_cmd
        _query_bool = self._query_bool_cmd

        # Retain for compatibility:
        self._store: dict = {}

        # -------------------------
        # Construct the API:
        # -------------------------
        self.source1 = SourceSelector(self._store, "source1")
        self.source2 = SourceSelector(self._store, "source2")

        self.ch1 = Channel("1", _write)
        self.ch2 = Channel("2", _write)
        self.ch3 = Channel("3", _write)
        self.ch4 = Channel("4", _write)

        self.time_base = TimeBase(_write)

        self.trigger = Trigger(_write)

        self.acquire = Acquire(_write)

        self.measure = Measure(_write, _query_after_acquire, self._store)

    # Mandatory methods to implement per driver:
    @abstractmethod
    def single(self) -> None:
        """Sets oscilliscope to take a single shot measurement"""

    @abstractmethod
    def run(self) -> None:
        """Sets the oscilliscope to run mode"""

    @abstractmethod
    def stop(self) -> None:
        """Puts the oscillicope in stop mode"""

    @abstractmethod
    def reset(self) -> None:
        """Resets the oscilliscope"""

    @abstractmethod
    def wait_for_acquire(self) -> None:
        """Block until the current acquisition is complete."""

    @abstractmethod
    def get_identity(self) -> str:
        """Return the IDN string of the device"""

    @abstractmethod
    def _check_errors(self) -> tuple[int, str]:
        """Check the error buffer for errors"""

    # Query and write functions:
    def _write_cmd(self, cmd: str) -> None:
        """Write a SCPI command and raise on instrument error."""
        self.instrument.write(cmd)

    def _query_bool_cmd(self, cmd: str) -> bool:
        values = self.instrument.query_ascii_values(cmd)
        self._raise_if_error()
        return bool(values[0])

    def _query_after_acquire_cmd(self, cmd: str) -> float:
        """Wait for a complete acquisition then query."""
        self.wait_for_acquire()
        try:
            result = self.instrument.query_ascii_values(cmd)[0]
        except Exception:
            self.instrument.close()
            self.instrument.open()
            raise
        return result

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

    # Context management:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()
        self.is_connected = False
