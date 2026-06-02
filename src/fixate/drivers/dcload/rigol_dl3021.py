from typing import Any
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.drivers.dcload.helper import DCLoad, Mode


class RigolDL3021(DCLoad):
    """Driver for Rigol DL3021 DC electronic load."""

    REGEX_ID = "DL3021"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument: Any) -> None:
        self.instrument = instrument
        self.instrument.timeout = 1000
        self._set_current_range = None

    def write(self, command: str) -> None:
        """Write a command to the instrument."""
        try:
            self.instrument.write(command)
        except Exception as e:
            raise InstrumentError(f"Error writing to instrument: {e}") from e

    def query(self, command: str) -> str:
        """Query the instrument and return the response."""
        try:
            return self.instrument.query(command)
        except Exception as e:
            raise InstrumentError(f"Error querying instrument: {e}") from e

    def reset(self) -> None:
        """Reset the instrument to default factory settings."""
        self.write("*RST")

    def get_identity(self) -> str:
        """Finds the instrument's manufacturer, model number, serial number, and firmware version."""
        return self.query("*IDN?").strip()

    def set_mode(self, mode: Mode) -> None:
        """Set the mode of the load (for example, constant current, constant voltage, etc.)."""
        if mode == "CONSTANT_CURRENT":
            scpi_mode = "CURR"
        elif mode == "CONSTANT_VOLTAGE":
            scpi_mode = "VOLT"
        elif mode == "CONSTANT_RESISTANCE":
            scpi_mode = "RES"
        elif mode == "CONSTANT_POWER":
            scpi_mode = "POW"
        else:
            raise ParameterError(f"Invalid mode: {mode}")

        return self.write(f":SOUR:FUNC {scpi_mode}")

    def get_mode(self) -> str:
        """Get the mode of the load."""
        return self.query(":SOUR:FUNC?").strip()

    def set_enabled(self, enable: bool) -> None:
        """Enable or disable the load."""
        value = "ON" if enable else "OFF"
        return self.write(f":SOUR:INP:STAT {value}")

    def get_enabled(self) -> bool:
        """Get the enabled state of the load."""
        state = self.query(":SOUR:INP:STAT?").strip()
        return state == "1"

    def get_current(self) -> float:
        """Get the current value in Amps."""
        return float(self.query(":SOUR:CURR:LEV:IMM?").strip())

    def set_current_range(self, current_range: float) -> None:
        """Set the current range to the specified value in Amps."""
        if current_range > 60:
            raise ParameterError(
                f"Current range {current_range}A exceeds maximum of 60A for DL3021"
            )

        if current_range < 0:
            raise ParameterError(
                f"Current range must be positive. Got {current_range}A"
            )

        self._set_current_range = current_range
        return self.write(f":SOUR:CURR:RANG {current_range}")

    def get_current_range(self) -> float:
        """Get the current range in Amps."""
        return float(self.query(":SOUR:CURR:RANG?").strip())

    def set_current(self, current: float) -> None:
        """Set the current to the specified value in Amps."""
        if self._set_current_range is None:
            raise ParameterError("Current range must be set before setting current.")

        if current > self._set_current_range:
            raise ParameterError(
                f"Current {current}A exceeds set current range of {self._set_current_range}A"
            )

        return self.write(f":SOUR:CURR:LEV:IMM {current}")
