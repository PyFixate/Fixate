from typing import Protocol, Literal
from fixate.drivers import DriverProtocol

# List of modes that an electronic load can be set to
Mode = Literal[
    "constant_current",
    "constant_voltage",
    "constant_resistance",
    "constant_power",
]


class DCLoad(DriverProtocol, Protocol):
    """Abstract class for DC electronic load drivers."""

    REGEX_ID: str

    def __init__(self, instrument) -> None:
        ...

    def reset(self) -> None:
        """Reset the instrument to a known state."""
        ...

    def get_identity(self) -> str:
        """Return instrument identity string."""
        ...

    def set_mode(self, mode: Mode) -> None:
        """Set the mode of the load (for example, constant current, constant voltage, etc.)."""
        ...

    def set_enabled(self, enable: bool) -> None:
        """Enable (TRUE) or disable (FALSE) the load."""
        ...

    def set_current(self, current: float) -> None:
        """Set the load current to the specified value in Amps."""
        ...

    def set_current_range(self, current_range: float) -> None:
        """Set the current range to the specified value in Amps."""
        ...
