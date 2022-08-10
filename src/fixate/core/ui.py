"""
This module details user input api
"""
import time
from queue import Queue, Empty
from pubsub import pub
from fixate.config import RESOURCES
from collections import OrderedDict

USER_YES_NO = ("YES", "NO")
USER_RETRY_ABORT_FAIL = ("RETRY", "ABORT", "FAIL")


def _user_req_input(msg, target=None, attempts=5, **kwargs):
    """
    A blocking function that waits for the user returned values
    :param msg:
     A message that will be shown to the user
    :param target:
     A function that will verify the user input
    :param args:
     Args for the target
    :param kwargs:
     Kwargs for the target
    :return:
     Returns the user response
    """
    q = Queue()
    pub.sendMessage("UI_block_start")
    pub.sendMessage(
        "UI_req_input", msg=msg, q=q, target=target, attempts=attempts, kwargs=kwargs
    )
    resp = q.get()
    pub.sendMessage("UI_block_end")
    return resp


def _user_req_choices(msg, choices, target=None, attempts=5):
    """
    A blocking function that waits for the user returned values
    :param msg:
     A message that will be shown to the user
    :param target:
     A function that will verify the user input
    :param args:
     Args for the target
    :param kwargs:
     Kwargs for the target
    :return:
     Returns the user response
    """
    if len(choices) < 2:
        raise ValueError(
            "Requires at least two choices to work, {} provided".format(choices)
        )
    q = Queue()
    pub.sendMessage("UI_block_start")
    pub.sendMessage(
        "UI_req_choices",
        msg=msg,
        q=q,
        choices=choices,
        target=target,
        attempts=attempts,
    )
    resp = q.get()
    pub.sendMessage("UI_block_end")
    return resp


def user_info(msg):
    pub.sendMessage("UI_display", msg=msg)


def user_info_important(msg):
    pub.sendMessage("UI_display_important", msg=msg)


def user_input(msg):
    """
    Get information from the user
    :param msg:
        text string indicating the request to the user
    :return:
        user response
    """
    # TODO - fix validation, bring it all into one method?? or move validation into target function for consistency
    return _user_req_input(msg)


def _float_validate(entry):
    try:
        return float(entry)
    except ValueError:
        user_info("Please enter a number")
        return False


def user_input_float(msg):
    """
    Get information from the user
    :param msg:
        text string indicating the request to the user
    :return:
        user response if valid
    """
    return _user_req_input(msg, target=_float_validate)


def user_action(msg, target):
    """
    Prompts the user to complete an action.
    Actively monitors the target infinitely until the event is detected or a user fail event occurs
    :param msg:
    Message to display to the user
    :param target: A function that will be called until the user action is cancelled. The function
    should return False if it hasn't completed. If the action is finished return True.

    :return: True if target returns True to finish the loop, False if user
            cancels vi the UserActionCallback
    """

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

            if target():
                return True

            # Yield control for other threads but don't slow down target
            time.sleep(0)
    finally:
        # No matter what, if we exit, we want to reset the UI
        callback_obj.target_finished_callback()


def user_ok(msg):
    """
    Display the provided message and waits for the user to acknowledge

    :param msg:
     A message that will be shown to the user
    """
    q = Queue()
    pub.sendMessage("UI_block_start")
    pub.sendMessage("UI_req", msg=msg, q=q)
    resp = q.get()
    pub.sendMessage("UI_block_end")
    return resp


def user_image(path):
    pub.sendMessage("UI_image", path=path)


def user_image_clear():
    pub.sendMessage("UI_image_clear")


def user_gif(path):
    pub.sendMessage("UI_gif", path=path)


# TODO: This is used by the sequencer. Should make internal. Doesn't makes
# sense that a test script would call this.
def user_retry_abort_fail(msg):
    return _user_req_choices(msg, target=_user_choices, choices=USER_RETRY_ABORT_FAIL)


def user_yes_no(msg, attempts=1):
    return _user_req_choices(
        msg, attempts=attempts, target=_user_choices, choices=USER_YES_NO
    )


def _user_choices(response, choices):
    if len(response) > 0:
        for choice in choices:
            if choice.startswith(response.upper()):
                return choice
    return False


def _ten_digit_serial(response):
    return (len(response) == 10) and int(response)


def user_serial(msg, target=_ten_digit_serial, attempts=5):
    serial = _user_req_input(msg, attempts=attempts, target=target)
    return serial


def user_post_sequence_info_pass(msg):
    """
    Adds information to be displayed to the user at the end of the sequence passes
    This information will be displayed in the order that post sequence info calls are made and will remove duplicates
    :param msg: String as it should be displayed
    :return:
    """
    if "_post_sequence_info" not in RESOURCES["SEQUENCER"].context_data:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info"] = OrderedDict()
    RESOURCES["SEQUENCER"].context_data["_post_sequence_info"][msg] = "PASSED"


def user_post_sequence_info_fail(msg):
    """
    Adds information to be displayed to the user at the end of the sequence if the tests fail or error.
    This information will be displayed in the order that post sequence info calls are made and will remove duplicates
    :param msg: String as it should be displayed
    :return:
    """
    if "_post_sequence_info" not in RESOURCES["SEQUENCER"].context_data:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info"] = OrderedDict()
    RESOURCES["SEQUENCER"].context_data["_post_sequence_info"][msg] = "FAILED"


def user_post_sequence_info(msg):
    """
    Adds information to be displayed to the user at the end of the sequence
    This information will be displayed in the order that post sequence info calls are made and will remove duplicates
    :param msg: String as it should be displayed
    :return:
    """
    if "_post_sequence_info" not in RESOURCES["SEQUENCER"].context_data:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info"] = OrderedDict()
    RESOURCES["SEQUENCER"].context_data["_post_sequence_info"][msg] = "ALL"
