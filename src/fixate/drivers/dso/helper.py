from _typeshed import SupportsDunderGE
import inspect
from abc import ABCMeta, abstractmethod
from typing import Callable, Union

from fixate.core.exceptions import InstrumentError, InstrumentFeatureUnavailable

number = Union[float, int]

"""
Callbacks
Write and query callbacks get passed down the tree of class variables.

They are then used to facilitate a single point of communication between 
the scope and the PC. This has the benefit of being able to mock the interface.
ie we can create a mock DSO that inherts the base and redefines functions.
"""
WriteCallback = Callable[[str], None]
QueryCallback = Callable[[str], str]

# Prompt that a featrue is not available:
def unavailable(name: str | None = None):
    label = name or inspect.stack()[1].function
    return InstrumentFeatureUnavailable(f"{label} not available on this device")


class SourceSelector:
    """
    Retain compatibility of source selection from the old API
    dso.source1.ch1() for example will set the source1.source = "CHAN1"
    This is then queried by the two source measurement functions like 'delay'
    You must set the sources before calling a multi measurement function.
    """

    def __init__(self):
        # Selected source (CHAN1, CHAN2, ... ,FUNC, MATH, WMEM1, WMEM2
        self.source: str | None = None

    def ch1(self) -> None:
        self.source = "CHAN1"

    def ch2(self) -> None:
        self.source = "CHAN2"

    def ch3(self) -> None:
        self.source = "CHAN3"

    def ch4(self) -> None:
        self.source = "CHAN4"

    def function(self) -> None:
        self.source = "FUNC"

    def math(self) -> None:
        self.source = "MATH"

    def wmemory1(self) -> None:
        self.source = "WMEM1"

    def wmemory2(self) -> None:
        self.source = "WMEM2"


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


class Measurement:
    """
    Single channel measurement class
    """


class MultiMeasurement:
    """
    Mulitple source measurement class
    """

    # Need a way to mimmic the _store dict. Maybe just easiest to use the same method of a dict


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
        self.source1 = SourceSelector()
        self.source2 = SourceSelector()

        self.ch1 = Channel("1", _write)
        self.ch2 = Channel("2", _write)
        self.ch3 = Channel("3", _write)
        self.ch4 = Channel("4", _write)

        self.time_base = TimeBase(_write)

        self.trigger = Trigger(_write)

        self.acquire = Acquire(_write)

    @abstractmethod
    def wait_for_acquire(self) -> None:
        """Block until the current acquisition is complete."""

    # Query and write functions:
    def _write_cmd(self, cmd: str) -> None:
        """Write a SCPI command and raise on instrument error."""
        self.instrument.write(cmd)
        self._raise_if_error()

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

    @abstractmethod
    def _raise_if_error(self) -> None:
        """Clean error queue and raise InstrumentError if any exist."""

    # Context management:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrument.close()
        self.is_connected = False
