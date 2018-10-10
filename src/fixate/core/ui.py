"""
This module details user input api
"""
import time
from queue import Queue, Empty
from pubsub import pub
from fixate.core.exceptions import UserInputError
from fixate.core.checks import chk_log_value
from fixate.config import RESOURCES

USER_CONFIRMATION = ("OK", "ABORT", "CANCEL")
USER_YES_NO = ("YES", "NO")
USER_PASS_FAIL = ("PASS", "FAIL")
USER_RETRY_ABORT_FAIL = ("RETRY", "ABORT", "FAIL")
USER_RETRY_ABORT = ("RETRY", "ABORT")


def _user_req(msg):
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
    pub.sendMessage('UI_block_start')
    pub.sendMessage('UI_req', msg=msg, q=q)
    resp = q.get()
    pub.sendMessage('UI_block_end')
    return resp


def _user_image(path):
    """
    A GUI function that updates the displayed image on-screen
    :param path:
     A relative path to the image
    """
    pub.sendMessage('UI_image', path=path)


def _user_image_clear():
    """
    A GUI function that updates the displayed image on-screen
    :param path:
     A relative path to the image
    """
    pub.sendMessage('UI_image_clear')


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
    pub.sendMessage('UI_block_start')
    pub.sendMessage('UI_req_input', msg=msg, q=q, target=target, attempts=attempts, kwargs=kwargs)
    resp = q.get()
    pub.sendMessage('UI_block_end')
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
        raise ValueError("Requires at least two choices to work, {} provided".format(choices))
    q = Queue()
    pub.sendMessage('UI_block_start')
    pub.sendMessage('UI_req_choices', msg=msg, q=q, choices=choices, target=target, attempts=attempts)
    resp = q.get()
    pub.sendMessage('UI_block_end')
    return resp


def user_info(msg):
    pub.sendMessage('UI_display', msg=msg)


def user_info_important(msg):
    pub.sendMessage('UI_display_important', msg=msg)


def user_input(msg):
    """
    Get information from the user
    :param msg:
        text string indicating the request to the user
    :param input_type:
        tells the _user_driver that this is an input and not to print the default choices text
    :return:
        user response
    """
    # TODO - fix validation, bring it all into one method?? or move validation into target function for consistency
    return _user_req_input(msg)


def _float_validate(entry):
    try:
        return float(entry)
    except ValueError:
        user_info('Please enter a number')
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
    WIP
    Prompts the user to complete an action.
    Actively monitors the target infinitely until the event is detected or a user fail event occurs
    :param msg:
    Message to display to the user
    :param target:

    :return:
    """
    q = Queue()
    abort = Queue()
    # UI command that will push
    # False into the queue if the user fails the test through an external interface.
    # True if the user passes the test through an external interface.
    pub.sendMessage('UI_action', msg=msg, q=q, abort=abort)
    while True:
        try:
            itm = q.get_nowait()
            abort.put(True)
            return itm
        except Empty:
            pass
        if target():
            abort.put(True)
            return True
        time.sleep(0)  # Yield control for other threads but don't slow down target


def user_ok(msg):
    return _user_req(msg)


def user_image(path):
    return _user_image(path)


def user_image_clear():
    return _user_image_clear()


def user_confirmation_box(msg, attempts=1):
    return user_choices(msg, choices=USER_CONFIRMATION, attempts=attempts)


def user_retry_abort_fail(msg):
    return _user_req_choices(msg, target=_user_choices, choices=USER_RETRY_ABORT_FAIL)


def user_retry_abort(msg):
    return _user_req_choices(msg, target=_user_choices, choices=USER_RETRY_ABORT)


def user_retry_auto():
    return "RESULT", "RETRY"


def user_pass_fail(msg, attempts=1):
    return _user_req_choices(msg, attempts=attempts, target=_user_choices, choices=USER_PASS_FAIL)


def user_yes_no(msg, attempts=1):
    return _user_req_choices(msg, attempts=attempts, target=_user_choices, choices=USER_YES_NO)


def _user_choices(response, choices):
    if len(response) > 0:
        for choice in choices:
            if choice.startswith(response.upper()):
                return choice
    return False


def user_choices(msg, choices, attempts=5):
    """
    Get information from the user
    :param msg:
        text string indicating the request to the user
    :return:
        user response
    """
    return _user_req_choices(msg, attempts=attempts, target=_user_choices, choices=choices)


def _ten_digit_serial(response):  # input_type argument added due to input_type="INPUT" on user_serial
    return (len(response) == 10) and int(response)


def user_serial(msg, target=_ten_digit_serial, attempts=5):
    serial = _user_req_input(msg, attempts=attempts, target=target)
    return serial


def user_post_sequence_info_pass(msg):
    """
    Hook to display relevant information at the end of a sequence.
    Only displayed if the sequence passes.
    :param msg: String as it should be displayed
    :return:
    """
    try:
        # Prevents duplicate messages
        if msg not in RESOURCES["SEQUENCER"].context_data["_post_sequence_info_pass"]:
            RESOURCES["SEQUENCER"].context_data["_post_sequence_info_pass"].append(msg)
    except KeyError:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info_pass"] = [msg]


def user_post_sequence_info_fail(msg):
    """
    Hook to display relevant information at the end of a sequence.
    Take care to only call at the end of tests to ensure that retries of the test do not clutter output
    :param msg: String as it should be displayed
    :return:
    """
    try:
        # Prevents duplicate messages
        if msg not in RESOURCES["SEQUENCER"].context_data["_post_sequence_info_fail"]:
            RESOURCES["SEQUENCER"].context_data["_post_sequence_info_fail"].append(msg)
    except KeyError:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info_fail"] = [msg]


def user_post_sequence_info(msg):
    """
    Hook to display relevant information at the end of a sequence.
    Take care to only call at the end of tests to ensure that retries of the test do not clutter output
    :param msg: String as it should be displayed
    :return:
    """
    try:
        # Prevents duplicate messages
        if msg not in RESOURCES["SEQUENCER"].context_data["_post_sequence_info"]:
            RESOURCES["SEQUENCER"].context_data["_post_sequence_info"].append(msg)
    except KeyError:
        RESOURCES["SEQUENCER"].context_data["_post_sequence_info"] = [msg]


RETRY_METHODS = {"RETRY ABORT SKIP": user_retry_abort_fail, "RETRY ABORT": user_retry_abort}


def user_retry(msg, retry_method):
    method = RETRY_METHODS.get(retry_method, None)
    while True:
        try:
            return method(msg)[1]
        except TypeError:
            return "RETRY"
        except UserInputError:
            pass
