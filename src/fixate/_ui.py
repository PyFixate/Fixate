"""
This module provides the user interface for fixate. It is agnostic of the
actual implementation of the UI and provides a standard set of functions used
to obtain or display information from/to the user.
"""

from typing import Callable, Any
from queue import Queue, Empty
import time
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
    pub.sendMessage("UI_req_input", msg=msg, q=q)
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
        UserInputError: If the user fails to enter a number after the specified number of attempts
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
    return_type: int | str = int,
    attempts: int = 5,
) -> Any:
    """
    A blocking function that asks the UI to ask the user for a serial number.

    Args:
        msg (str): A message that will be shown to the user
        validator (Validator): An optional function to validate the serial number,
            defaults to checking for a 10 digit integer. This function shall return
            True if the serial number is valid, False otherwise.
        return_type (int | str): The type to return the serial number as, defaults to int

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
    pub.sendMessage("UI_req_choices", msg=msg, q=q, choices=choices)
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


def user_info(msg: str):
    pub.sendMessage("UI_display", msg=msg)


def user_info_important(msg: str):
    pub.sendMessage("UI_display_important", msg=msg)


def user_ok(msg: str):
    """
    A blocking function that asks the UI to display a message and waits for the user to press OK/Enter.
    """
    pub.sendMessage("UI_block_start")
    pub.sendMessage("UI_req", msg=msg)
    pub.sendMessage("UI_block_end")


def user_action(msg: str, action_monitor: Callable[[], bool]) -> bool:
    """
    Prompts the user to complete an action.
    Actively monitors the target infinitely until the event is detected or a user fail event occurs

    Args:
        msg (str): Message to display to the user
        action_monitor (function): A function that will be called until the user action is cancelled. The function
            should return False if it hasn't completed. If the action is finished return True.

    Returns:
        bool: True if the action is finished, False otherwise
    """
    # UserActionCallback is used to handle the cancellation of the action either by the user or by the action itself
    class UserActionCallback:
        def __init__(self):
            # The UI implementation must provide queue.Queue object. We
            # monitor that object. If it is non-empty, we get the message
            # in the q and cancel the target call.
            self.user_cancel_queue = None

            # In the case that the target exists the user action instead
            # of the user, we need to tell the UI to do any clean up that
            # might be required. (e.g. return GUI buttons to the default state
            # Does not need to be implemented by the UI.
            # Function takes no args and should return None.
            self.target_finished_callback = lambda: None

        def set_user_cancel_queue(self, cancel_queue):
            self.user_cancel_queue = cancel_queue

        def set_target_finished_callback(self, callback):
            self.target_finished_callback = callback

    callback_obj = UserActionCallback()
    pub.sendMessage("UI_action", msg=msg, callback_obj=callback_obj)
    try:
        while True:
            try:
                callback_obj.user_cancel_queue.get_nowait()
                return False
            except Empty:
                pass

            if action_monitor():
                return True

            # Yield control for other threads but don't slow down target
            time.sleep(0)
    finally:
        # No matter what, if we exit, we want to reset the UI
        callback_obj.target_finished_callback()


def user_image(path: str):
    """
    Display an image to the user

    Args:
        path (str): The path to the image file. The underlying library does not take a pathlib.Path object.
    """
    pub.sendMessage("UI_image", path=path)


def user_image_clear():
    """
    Clear the image canvas
    """
    pub.sendMessage("UI_image_clear")


def user_gif(path: str):
    """
    Display a gif to the user

    Args:
        path (str): The path to the gif file. The underlying library does not take a pathlib.Path object.
    """
    pub.sendMessage("UI_gif", path=path)


def _user_post_sequence_info(msg: str, status: str):
    if "_post_sequence_info" not in RESOURCES["SEQUENCER"].context_data:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info"] = OrderedDict()
    RESOURCES["SEQUENCER"].context_data["_post_sequence_info"][msg] = status


def user_post_sequence_info_pass(msg: str):
    """
    Adds information to be displayed to the user at the end if the sequence passes
    This information will be displayed in the order that this function is called.
    Multiple calls with the same message will result in the previous being overwritten.

    This is useful for providing a summary of the sequence to the user at the end.

    Args:
        msg (str): The message to display.
    """
    _user_post_sequence_info(msg, "PASSED")


def user_post_sequence_info_fail(msg: str):
    """
    Adds information to be displayed to the user at the end if the sequence fails.
    This information will be displayed in the order that this function is called.
    Multiple calls with the same message will result in the previous being overwritten.

    This is useful for providing a summary of the sequence to the user at the end.

    Args:
        msg (str): The message to display.
    """
    _user_post_sequence_info(msg, "FAILED")


def user_post_sequence_info(msg: str):
    """
    Adds information to be displayed to the user at the end of the sequence.
    This information will be displayed in the order that this function is called.
    Multiple calls with the same message will result in the previous being overwritten.

    This is useful for providing a summary of the sequence to the user at the end.

    Args:
        msg (str): The message to display.
    """
    _user_post_sequence_info(msg, "ALL")
