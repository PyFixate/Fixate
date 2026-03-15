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


class Channel:
    """
    DSO Channel implementation
    """

    def __init__(
        self, channel_name: str, write: WriteCallback, enabled: bool = True
    ) -> None:
        self._ch_name = channel_name
        self._write = write
        # Set enabled = False if the DSO does not have this channel
        self._ch_cmd = f"CHAN{self._ch_name}"
        self._enabled = enabled
        # Maybe some fancy thing here to set all methods to raise an error if not enabled.

    def __call__(self, value: bool):
        self._write(f"CHAN1:DISP {int(value)}")

    def scale(self, value: number) -> None:
        self._write(f"{self._ch_cmd}:SCAL {value}")

    def offset(self, value: number) -> None:
        self._write(f"{self._ch_cmd}:OFFS {value}")

    def bandwidth(self, value: number) -> None:
        raise InstrumentError("This function is not implemented")

    def bandwidth_limit(self, value: bool) -> None:
        raise InstrumentError("This function is not implemented")

    def impedance(self, value: number) -> None:
        raise InstrumentError("This function is not implemented")

    def invert(self, value: bool) -> None:
        raise InstrumentError("This function is not implemented")


class Coupling:
    """
    Defines the coupling interface
    """

    def __init__(self, write: WriteCallback, cmd_prefix: str):
        self._write = write
        self._cmd_prefix = cmd_prefix


class TriggerCoupling(Coupling):
    """
    Extends the Coupling interface with extra functions that the trigger has
    """

    def extra_implementation_stuff(self):
        pass


class TriggerSweep:
    """
    Define the sweep interface on the trigger
    """

    def __init__(self, write: WriteCallback):
        self._write = write


class TriggerMode:
    """
    Define the trigger mode interface
    """

    def __init__(self, write: WriteCallback):
        self._write = write


class Trigger:
    """
    Trigger base class
    """

    def __init__(self, write: WriteCallback):
        self._write = write
        self.mode = TriggerMode(write)
        self.coupling = TriggerCoupling(write, "TRIG")
        self.sweep = TriggerSweep(write)


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
        self.ch1 = Channel("1", _write)
        self.ch2 = Channel("2", _write)
        self.ch3 = Channel("3", _write)
        self.ch4 = Channel("4", _write)

        self.trigger = Trigger(_write)
        # ... More stuff goes here. This will copy the original structure of the api dictionary

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
