"""
This module provides the user interface for fixate. It is agnostic of the
actual implementation of the UI and provides a standard set of functions used
to obtain or display information from/to the user.
"""

from typing import Callable, Any
from queue import Queue, Empty
from pubsub import pub

# going to honour the post sequence info display from `ui.py`
from fixate.config import RESOURCES
from fixate.core.exceptions import UserInputError
from collections import OrderedDict


class Validator:
    """
    Defines a validator object that can be used to validate user input.
    """

    def __init__(self, func: Callable[[Any], bool], errror_msg: str = "Invalid input"):
        """
        Args:
            func (function): The function to validate the input
            error_msg (str): The message to display if the input is invalid
        """
        self.func = func
        self.error_msg = errror_msg

    def __call__(self, resp: Any) -> bool:
        """
        Args:
            resp (Any): The response to validate

        Returns:
            bool: True if the response is valid, False otherwise
        """
        return self.func(resp)

    def __str__(self) -> str:
        return self.error_msg


def _user_request_input(msg: str):
    q = Queue()
    pub.sendMessage("UI_block_start")
    pub.sendMessage("UI_req_input_", msg=msg, q=q)
    resp = q.get()
    pub.sendMessage("UI_block_end")
    return resp


def user_input(msg: str) -> str:
    """
    A blocking function that asks the UI to ask the user for raw input.

    Args:
        msg (str): A message that will be shown to the user

    Returns:
        resp (str): The user response from the UI
    """
    return _user_request_input(msg)


def user_input_float(msg: str, attempts: int = 5) -> float:
    """
    A blocking function that asks the UI to ask the user for input and converts the response to a float.

    Args:
        msg (str): A message that will be shown to the user
        attempts (int): Number of attempts the user has to get the input right

    Returns:
        resp (float): The converted user response from the UI

    Raises:
        ValueError: If the user fails to enter a number after the specified number of attempts
    """
    resp = _user_request_input(msg)
    for _ in range(attempts):
        try:
            return float(resp)
        except ValueError:
            pub.sendMessage(
                "UI_display_important", msg="Invalid input, please enter a number"
            )
            resp = _user_request_input(msg)
    raise UserInputError("User failed to enter a number")


def _ten_digit_int_serial(serial: str) -> bool:
    return len(serial) == 10 and serial.isdigit()


_ten_digit_int_serial_v = Validator(
    _ten_digit_int_serial, "Please enter a 10 digit serial number"
)


def user_serial(
    msg: str,
    validator: Validator = _ten_digit_int_serial_v,
    return_type: Any = int,
    attempts: int = 5,
) -> Any:
    """
    A blocking function that asks the UI to ask the user for a serial number.

    Args:
        msg (str): A message that will be shown to the user
        validator (Validator): An optional function to validate the serial number,
            defaults to checking for a 10 digit integer. This function shall return
            True if the serial number is valid, False otherwise
        return_type (Any): The type to return the serial number as, defaults to int

    Returns:
        resp (str): The user response from the UI
    """
    resp = _user_request_input(msg)
    for _ in range(attempts):
        if validator(resp):
            return return_type(resp)
        pub.sendMessage("UI_display_important", msg=f"Invalid input: {validator}")
        resp = _user_request_input(msg)
    raise UserInputError("User failed to enter the correct format serial number")


def _user_req_choices(msg: str, choices: tuple):
    # TODO - do we really need this check since this is a private function and any callers should be calling correctly
    if len(choices) < 2:
        raise ValueError(f"Requires at least two choices to work, {choices} provided")
    q = Queue()
    pub.sendMessage("UI_block_start")
    pub.sendMessage("UI_req_choices_", msg=msg, q=q, choices=choices)
    resp = q.get()
    pub.sendMessage("UI_block_end")
    return resp


def _choice_from_response(choices: tuple, resp: str) -> str | bool:
    for choice in choices:
        if resp.startswith(choice[0]):
            return choice
    return False


def _user_choices(msg: str, choices: tuple, attempts: int = 5) -> str:
    resp = _user_req_choices(msg, choices).upper()
    for _ in range(attempts):
        choice = _choice_from_response(choices, resp)
        if choice:
            return choice
        pub.sendMessage(
            "UI_display_important",
            msg="Invalid input, please enter a valid choice; first letter or full word",
        )
        resp = _user_req_choices(msg, choices).upper()
    raise UserInputError("User failed to enter a valid response")


def user_yes_no(msg: str, attempts: int = 1) -> str:
    """
    A blocking function that asks the UI to ask the user for a yes or no response.

    Args:
        msg (str): A message that will be shown to the user

    Returns:
        resp (str): 'YES' or 'NO'
    """
    CHOICES = ("YES", "NO")
    return _user_choices(msg, CHOICES, attempts)


def _user_retry_abort_fail(msg: str, attempts: int = 1) -> str:
    CHOICES = ("RETRY", "ABORT", "FAIL")
    return _user_choices(msg, CHOICES, attempts)


def user_info(msg):
    pub.sendMessage("UI_display", msg=msg)


def user_info_important(msg):
    pub.sendMessage("UI_display_important", msg=msg)


def user_ok(msg):
    """
    A blocking function that asks the UI to display a message and waits for the user to press OK/Enter.
    """
    pub.sendMessage("UI_block_start")
    pub.sendMessage("UI_req_", msg=msg)
    pub.sendMessage("UI_block_end")
