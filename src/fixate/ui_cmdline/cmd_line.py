import traceback
import sys
import time
import textwrap
from pubsub import pub
from fixate.ui_cmdline.kbhit import KBHit
from queue import Queue
from fixate.core.exceptions import UserInputError
from fixate.core.common import ExcThread
from fixate.core.checks import CheckResult
from fixate.config import RESOURCES
import fixate.config

wrapper = textwrap.TextWrapper(width=75)
wrapper.break_long_words = False

wrapper.drop_whitespace = True

kb = KBHit()


class KeyboardHook:
    def kb_hit_monitor(self):
        while True:
            if self.stop_thread:
                self.monitoring = False
                break
            if self.monitor_active:
                self.monitoring = True
                if kb.kbhit():  # Check for key press
                    # Our dictionary keys are bytestring. We must do the same
                    # to the detected key press to ensure the look works!
                    key_press = bytes(kb.getch().encode())
                    key = self.keys_to_monitor.get(key_press, None)
                    if key is not None:
                        self.key_queue.put(key)
            else:
                self.monitoring = False
            time.sleep(0.05)

    def __init__(self):
        self.key_monitor_thread = None
        # a dictionary mapping key strings to values which will
        # be returned if matching key press is detected
        self.keys_to_monitor = {}

        self.key_queue = None
        # when true, the thread's will keep running
        self.stop_thread = False
        # when true, the thread will monitor key presses.
        # when false, it will sit waiting
        self.monitor_active = True
        self.monitoring = False

    def start_monitor(self, key_queue, keys_to_monitor):
        self.keys_to_monitor = keys_to_monitor
        self.key_queue = key_queue
        self.monitor_active = True
        while not self.monitoring:
            pass

    def stop_monitor(self):
        self.monitor_active = False
        while self.monitoring:
            pass
        self.keys_to_monitor = None
        self.key_queue = None

    def install(self):
        self.key_monitor_thread = ExcThread(target=self.kb_hit_monitor)
        self.key_monitor_thread.start()

    def uninstall(self):
        if self.key_monitor_thread:
            self.stop_thread = True
            self.key_monitor_thread.join()
        self.key_monitor_thread = None


key_hook = KeyboardHook()


def register_cmd_line():
    pub.subscribe(_print_test_start, "Test_Start")
    pub.subscribe(_print_test_start, "TestList_Start")
    pub.subscribe(_print_test_complete, "Test_Complete")
    pub.subscribe(_print_comparisons, "Check")
    pub.subscribe(_print_errors, "Test_Exception")
    pub.subscribe(_print_sequence_end, "Sequence_Complete")
    pub.subscribe(_user_ok, "UI_req")
    pub.subscribe(_user_ok_, "UI_req_")
    pub.subscribe(_user_choices, "UI_req_choices")
    pub.subscribe(_user_choices_, "UI_req_choices_")
    pub.subscribe(_user_input, "UI_req_input")
    pub.subscribe(_user_input_, "UI_req_input_")
    pub.subscribe(_user_display, "UI_display")
    pub.subscribe(_user_display_important, "UI_display_important")
    pub.subscribe(_print_test_skip, "Test_Skip")
    pub.subscribe(_print_test_retry, "Test_Retry")
    pub.subscribe(_user_action, "UI_action")
    pub.subscribe(_user_image, "UI_image")
    key_hook.install()

    return


def unregister_cmd_line():
    key_hook.uninstall()
    return


def _reformat_text(text_str, first_line_fill="", subsequent_line_fill=""):
    lines = []
    _wrapper_initial_indent = wrapper.initial_indent
    _wrapper_subsequent_indent = wrapper.subsequent_indent
    wrapper.initial_indent = first_line_fill
    wrapper.subsequent_indent = subsequent_line_fill
    for ind, line in enumerate(text_str.splitlines()):
        if ind != 0:
            wrapper.initial_indent = subsequent_line_fill
        lines.append(wrapper.fill(line))
    # reset the indents, calls to this method should not affect the global state
    wrapper.initial_indent = _wrapper_initial_indent
    wrapper.subsequent_indent = _wrapper_subsequent_indent
    return "\n".join(lines)


def _user_action(msg, callback_obj):
    """
    This is for tests that aren't entirely dependant on the automated system.
    This works by monitoring a queue to see if the test completed successfully.
    Also while doing this it is monitoring if the escape key is pressed to signal to the system that the test fails.
    Use this in situations where you want the user to do something (like press all the keys on a keypad) where the
    system is automatically monitoring for success but has no way of monitoring failure.
    :param msg:
     Information for the user
    :param q:
     The queue object to put false if the user fails the test
    :param abort:
     The queue object to abort this monitoring as the test has already passed.
    :return:
    None
    """
    print("\a")
    print(_reformat_text(msg))
    print('Press escape or "f" to fail')
    cancel_queue = Queue()
    callback_obj.set_user_cancel_queue(cancel_queue)
    callback_obj.set_target_finished_callback(key_hook.stop_monitor)

    key_hook.start_monitor(cancel_queue, {b"\x1b": False, b"f": False})


def _user_ok_(msg):
    msg = _reformat_text(msg + "\n\nPress Enter to continue...")
    print("\a")
    input(msg)


def _user_ok(msg, q):
    """
    This can be replaced anywhere in the project that needs to implement the user driver
    The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the second
    part is the exception object or response object
    :param msg:
     Message for the user to understand what to do
    :param q:
     The result queue of type queue.Queue
    :return:
    """
    msg = _reformat_text(msg + "\n\nPress Enter to continue...")
    print("\a")
    input(msg)
    q.put("Result", None)


def _user_choices_(msg, q, choices):
    choicesstr = "\n" + ", ".join(choices[:-1]) + " or " + choices[-1]
    print("\a")
    ret_val = input(_reformat_text(msg + choicesstr) + " ")
    q.put(ret_val)


def _user_choices(msg, q, choices, target, attempts=5):
    """
    This can be replaced anywhere in the project that needs to implement the user driver
    Temporarily a simple input function.
    The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the second
    part is the exception object or response object
    This needs to be compatible with forced exit. Look to user action for how it handles a forced exit
    :param msg:
     Message for the user to understand what to input
    :param q:
     The result queue of type queue.Queue
    :param target:
     Optional
     Validation function to check if the user response is valid
    :param attempts:
    :param args:
    :param kwargs:
    :return:
    """
    choicesstr = "\n" + ", ".join(choices[:-1]) + " or " + choices[-1] + " "
    for _ in range(attempts):
        # This will change based on the interface
        print("\a")
        ret_val = input(_reformat_text(msg + choicesstr))
        ret_val = target(ret_val, choices)
        if ret_val:
            q.put(("Result", ret_val))
            return
    q.put(
        "Exception",
        UserInputError("Maximum number of attempts {} reached".format(attempts)),
    )


def _user_input_(msg, q):
    """
    Get raw user input and put in on the queue.
    """
    initial_indent = ">>> "
    subsequent_indent = "    "  # TODO - determine is this is needed
    print("\a")
    resp = input(_reformat_text(msg, initial_indent, subsequent_indent) + "\n>>> ")
    q.put(resp)


def _user_input(msg, q, target=None, attempts=5, kwargs=None):
    """
    This can be replaced anywhere in the project that needs to implement the user driver
    Temporarily a simple input function.
    The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the second
    part is the exception object or response object
    This needs to be compatible with forced exit. Look to user action for how it handles a forced exit
    :param msg:
     Message for the user to understand what to input
    :param q:
     The result queue of type queue.Queue
    :param target:
     Optional
     Validation function to check if the user response is valid
    :param attempts:
    :param args:
    :param kwargs:
    :return:
    """
    initial_indent = ">>> "
    subsequent_indent = "    "
    # additional space added due to wrapper.drop_white_space being True, need to
    # drop white spaces, but keep the white space to separate the cursor from input message
    msg = _reformat_text(msg, initial_indent, subsequent_indent) + "\n>>> "
    for _ in range(attempts):
        # This will change based on the interface
        print("\a")
        ret_val = input(msg)
        if target is None:
            q.put(ret_val)
            return
        ret_val = target(ret_val, **kwargs)
        if ret_val:
            q.put(("Result", ret_val))
            return
    # Display failure of target and send exception
    error_str = f"Maximum number of attempts {attempts} reached. {target.__doc__}"
    _user_display(error_str)
    q.put(("Exception", UserInputError(error_str)))


def _user_display(msg):
    """
    :param msg:
    :param important: creates a line of "!" either side of the message
    :return:
    """
    print(_reformat_text(msg))


def _user_display_important(msg):
    """
    :param msg:
    :param important: creates a line of "!" either side of the message
    :return:
    """
    print("")
    print("!" * wrapper.width)
    print("")
    print(_reformat_text(msg))
    print("")
    print("!" * wrapper.width)


def _user_image(path):
    print("\a")
    _user_display_important("Image display not supported in command line")
    print(_reformat_text(f"This image would have been displayed in the GUI: {path}"))


def _print_sequence_end(status, passed, failed, error, skipped, sequence_status):
    print("#" * wrapper.width)
    print(_reformat_text("Sequence {}".format(sequence_status)))
    # print("Sequence {}".format(sequence_status))
    post_sequence_info = RESOURCES["SEQUENCER"].context_data.get(
        "_post_sequence_info", {}
    )
    if post_sequence_info:
        print("-" * wrapper.width)
        print("IMPORTANT INFORMATION")
        for msg, state in post_sequence_info.items():
            if status == "PASSED":
                if state == "PASSED" or state == "ALL":
                    print(_reformat_text(msg))
            elif state != "PASSED":
                print(_reformat_text(msg))

    print("-" * wrapper.width)
    # reformat_text
    print(_reformat_text("Status: {}".format(status)))
    # print("Status: {}".format(status))
    print("#" * wrapper.width)
    print("\a")


def _print_test_start(data, test_index):
    print("*" * wrapper.width)
    print(_reformat_text("Test {}: {}".format(test_index, data.test_desc)))
    # print("Test {}: {}".format(test_index, data.test_desc))
    print("-" * wrapper.width)


def _print_test_complete(data, test_index, status):
    sequencer = RESOURCES["SEQUENCER"]
    print("-" * wrapper.width)
    print(
        _reformat_text(
            "Checks passed: {}, Checks failed: {}".format(
                sequencer.chk_pass, sequencer.chk_fail
            )
        )
    )
    # print("Checks passed: {}, Checks failed: {}".format(sequencer.chk_pass, sequencer.chk_fail))
    print(_reformat_text("Test {}: {}".format(test_index, status.upper())))
    # print("Test {}: {}".format(test_index, status.upper()))
    print("-" * wrapper.width)


def _print_test_skip(data, test_index):
    print("\nTest Marked as skip")


def _print_test_retry(data, test_index):
    print(_reformat_text("\nTest {}: Retry".format(test_index)))


def _print_errors(exception, test_index):
    print("")
    print("!" * wrapper.width)
    print(
        _reformat_text(
            "Test {}: Exception Occurred, {} {}".format(
                test_index, type(exception), exception
            )
        )
    )
    # print("Test {}: Exception Occurred, {} {}".format(test_index, type(exception), exception))
    print("!" * wrapper.width)
    # TODO print traceback into a debug log file
    if fixate.config.DEBUG:
        traceback.print_tb(exception.__traceback__, file=sys.stderr)


def _print_comparisons(passes: bool, chk: CheckResult, chk_cnt: int, context: str):
    msg = f"\nCheck {chk_cnt}: " + chk.check_string
    print(_reformat_text(msg))
