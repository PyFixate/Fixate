from typing import Any
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.drivers.dcload.helper import DCLoad
from strenum import StrEnum


class Mode(StrEnum):
    # Set the mode of the load.
    CONSTANT_CURRENT = "CURR"
    CONSTANT_VOLTAGE = "VOLT"
    CONSTANT_RESISTANCE = "RES"
    CONSTANT_POWER = "POW"


class RigolDL3021(DCLoad):
    REGEX_ID = "DL3021"
    INSTR_TYPE = "VISA"
    write_termination = "\n"
    read_termination = "\n"

    def __init__(self, instrument: Any) -> None:
        self.instrument = instrument
        self.instrument.timeout = 1000
        self.instrument.read_termination = self.read_termination
        self.instrument.write_termination = self.write_termination

    def write(self, command: str) -> None:
        try:
            self.instrument.write(command)
        except Exception as e:
            raise InstrumentError(f"Error writing to instrument: {e}") from e

    def query(self, command: str) -> str:
        try:
            return self.instrument.query(command)
        except Exception as e:
            raise InstrumentError(f"Error querying instrument: {e}") from e

    def reset(self) -> None:
        # Reset the instrument to default factory settings.
        self.write("*RST")

    def get_identity(self) -> str:
        # Finds the instrument's manufacturer, model number, serial number, and firmware version.
        return self.query("*IDN?").strip()

    def set_mode(self, mode: Mode) -> None:
        # Set the mode of the load
        if not isinstance(mode, Mode):
            raise ParameterError(f"Invalid mode: {mode}. Must be one of {list(Mode)}")

        return self.write(f":SOUR:FUNC {mode.value}")

    def get_mode(self) -> str:
        # Get the mode of the load
        return self.query(":SOUR:FUNC?").strip()

    def set_enabled(self, enable: bool) -> None:
        # Enable or disable the load
        value = "ON" if enable else "OFF"
        return self.write(f":SOUR:INP:STAT {value}")

    def get_enabled(self) -> bool:
        state = self.query(":SOUR:INP:STAT?").strip()
        return state == "1"

    def get_current(self) -> float:
        # Get the current value in Amps
        return float(self.query(":SOUR:CURR:LEV:IMM?").strip())

    def set_current_range(self, current_range: float) -> None:
        # Set the current range to the specified value in Amps
        if current_range > 60:
            raise ParameterError(
                f"Current range {current_range}A exceeds maximum of 60A for DL3021"
            )

        if current_range < 0:
            raise ParameterError(
                f"Current range must be positive. Got {current_range}A"
            )

        self._requested_current_range = current_range
        return self.write(f":SOUR:CURR:RANG {current_range}")

    def get_current_range(self) -> float:
        # Get the current range in Amps
        return float(self.query(":SOUR:CURR:RANG?").strip())

    def set_current(self, current: float) -> None:
        # Set the current to the specified value in Amps
        mode = self.get_mode()
        if mode != "CC":
            raise ParameterError(
                f"Cannot set current when mode is {mode}. Must be in CONSTANT_CURRENT mode."
            )

        if self._requested_current_range is None:
            raise ParameterError(f"Current range must be set before setting current.")

        if current > self._requested_current_range:
            raise ParameterError(
                f"Current {current}A exceeds set current range of {self._requested_current_range}A"
            )

        return self.write(f":SOUR:CURR:LEV:IMM {current}")
