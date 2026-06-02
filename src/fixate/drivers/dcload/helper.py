from typing import Protocol, Literal

# List of modes that an electronic load can be set to
Mode = Literal[
    "CONSTANT_CURRENT",
    "CONSTANT_VOLTAGE",
    "CONSTANT_RESISTANCE",
    "CONSTANT_POWER",
]


class DCLoad(Protocol):
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
        """Enable (1) or disable (0) the load."""
        ...

    def set_current(self, current: float) -> None:
        """Set the load current to the specified value in Amps."""
        ...

    def set_current_range(self, current_range: float) -> None:
        """Set the current range to the specified value in Amps."""
        ...
