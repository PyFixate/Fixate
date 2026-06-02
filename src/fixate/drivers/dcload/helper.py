from typing import Protocol

"""
Abstract class for DC electronic load drivers. 
Aims to be reusable so that if new electronic load p/n's are added, they can be used with minimal effort. 
"""


class DCLoad(Protocol):
    REGEX_ID: str

    def __init__(self, instrument) -> None:
        ...

    def reset(self) -> None:
        # Reset the instrument to a known state.
        ...

    def get_identity(self) -> str:
        # Return instrument identity string (for example, the *IDN? response).
        ...

    def set_mode(self, mode) -> None:
        # Set the mode of the load (for example, constant current, constant voltage, etc.)
        ...

    def set_enabled(self, enable: bool) -> None:
        # Enable (1) or disable (0) the load
        ...

    def set_current(self, current: float) -> None:
        # Set the load current to the specified value in Amps
        ...

    def set_current_range(self, current_range: float) -> None:
        # Set the current range to the specified value in Amps
        ...
