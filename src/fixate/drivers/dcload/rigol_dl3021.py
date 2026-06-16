from typing import Any
from fixate.core.exceptions import InstrumentError, ParameterError
from fixate.drivers.dcload.helper import DCLoad, Mode, CurrentRange


class RigolDL3021(DCLoad):
    """Driver for Rigol DL3021 DC electronic load."""

    REGEX_ID = "DL3021"
    INSTR_TYPE = "VISA"

    def __init__(self, instrument: Any) -> None:
        self.instrument = instrument
        self.instrument.timeout = 1000
        self._set_current_range: float | None = None

    def _write(self, command: str) -> None:
        """Write a command to the instrument."""
        try:
            self.instrument.write(command)
        except Exception as e:
            raise InstrumentError(f"Error writing to instrument: {e}") from e

    def _query(self, command: str) -> str:
        """Query the instrument and return the response."""
        try:
            return self.instrument.query(command)
        except Exception as e:
            raise InstrumentError(f"Error querying instrument: {e}") from e

    def reset(self) -> None:
        """Reset the instrument to default factory settings."""
        self._write("*RST")

    def get_identity(self) -> str:
        """Finds the instrument's manufacturer, model number, serial number, and firmware version."""
        return self._query("*IDN?").strip()

    def set_mode(self, mode: Mode) -> None:
        """Set the mode of the load (for example, constant current, constant voltage, etc.)."""
        if mode == "constant_current":
            scpi_mode = "CURR"
        elif mode == "constant_voltage":
            scpi_mode = "VOLT"
        elif mode == "constant_resistance":
            scpi_mode = "RES"
        elif mode == "constant_power":
            scpi_mode = "POW"
        else:
            raise ParameterError(f"Invalid mode: {mode}")

        return self._write(f":SOUR:FUNC {scpi_mode}")

    def _get_mode(self) -> str:
        """Get the mode of the load."""
        return self._query(":SOUR:FUNC?").strip()

    def set_enabled(self, enable: bool) -> None:
        """Enable (TRUE) or disable (FALSE) the load."""
        value = "ON" if enable else "OFF"
        return self._write(f":SOUR:INP:STAT {value}")

    def _get_enabled(self) -> bool:
        """Get the enabled state of the load."""
        state = self._query(":SOUR:INP:STAT?").strip()
        return state == "1"

    def _get_current(self) -> float:
        """Get the current value in Amps."""
        return float(self._query(":SOUR:CURR:LEV:IMM?").strip())

    def set_current_range(self, current_range: CurrentRange) -> None:
        """Set the current range to low (4A) or high (40A) or default (40A)."""
        if current_range == "low":
            scpi_mode = "MIN"
            self._set_current_range = 4.0
        elif current_range == "high":
            scpi_mode = "MAX"
            self._set_current_range = 40.0
        elif current_range == "default":
            self._set_current_range = 40.0
            scpi_mode = "DEF"
        else:
            raise ParameterError(f"Invalid current range: {current_range}")

        return self._write(f":SOUR:CURR:RANG {scpi_mode}")

    def _get_current_range(self) -> float:
        """Get the current range in Amps. 4 or 40 for the DL3021."""
        return float(self._query(":SOUR:CURR:RANG?").strip())

    def set_current(self, current: float) -> None:
        """Set the current to the specified value in Amps."""
        if self._set_current_range is None:
            raise ParameterError("Current range must be set before setting current.")

        if current > self._set_current_range:
            raise ParameterError(
                f"Current {current}A exceeds set current range of {self._set_current_range}A"
            )

        return self._write(f":SOUR:CURR:LEV:IMM {current}")
