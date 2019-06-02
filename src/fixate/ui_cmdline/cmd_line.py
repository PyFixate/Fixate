import traceback
import sys
import time
import textwrap
from pubsub import pub
from fixate.ui_cmdline.kbhit import KBHit
from queue import Queue
from fixate.core.exceptions import UserInputError
from fixate.core.common import ExcThread
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
    pub.subscribe(_user_choices, "UI_req_choices")
    pub.subscribe(_user_input, "UI_req_input")
    pub.subscribe(_user_display, "UI_display")
    pub.subscribe(_user_display_important, "UI_display_important")
    pub.subscribe(_print_test_skip, "Test_Skip")
    pub.subscribe(_print_test_retry, "Test_Retry")
    pub.subscribe(_user_action, "UI_action")
    key_hook.install()

    return


def unregister_cmd_line():
    key_hook.uninstall()
    return


def reformat_text(text_str, first_line_fill="", subsequent_line_fill=""):
    lines = []
    wrapper.initial_indent = first_line_fill
    wrapper.subsequent_indent = subsequent_line_fill
    for ind, line in enumerate(text_str.splitlines()):
        if ind != 0:
            wrapper.initial_indent = subsequent_line_fill
        lines.append(wrapper.fill(line))
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
    print(reformat_text(msg))
    print('Press escape or "f" to fail')
    cancel_queue = Queue()
    callback_obj.set_user_cancel_queue(cancel_queue)
    callback_obj.set_target_finished_callback(key_hook.stop_monitor)

    key_hook.start_monitor(cancel_queue, {b"\x1b": False, b"f": False})


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
    msg = reformat_text(msg + "\n\nPress Enter to continue...")
    print("\a")
    input(msg)
    q.put("Result", None)


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
        ret_val = input(reformat_text(msg + choicesstr))
        ret_val = target(ret_val, choices)
        if ret_val:
            q.put(("Result", ret_val))
            return
    q.put(
        "Exception",
        UserInputError("Maximum number of attempts {} reached".format(attempts)),
    )


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
    msg = reformat_text(msg, initial_indent, subsequent_indent) + "\n>>> "
    wrapper.initial_indent = ""
    wrapper.subsequent_indent = ""
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
    q.put(
        "Exception",
        UserInputError("Maximum number of attempts {} reached".format(attempts)),
    )


def _user_display(msg):
    """
    :param msg:
    :param important: creates a line of "!" either side of the message
    :return:
    """
    print(reformat_text(msg))


def _user_display_important(msg):
    """
    :param msg:
    :param important: creates a line of "!" either side of the message
    :return:
    """
    print("")
    print("!" * wrapper.width)
    print("")
    print(reformat_text(msg))
    print("")
    print("!" * wrapper.width)


def _print_sequence_end(status, passed, failed, error, skipped, sequence_status):
    print("#" * wrapper.width)
    print(reformat_text("Sequence {}".format(sequence_status)))
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
                    print(reformat_text(msg))
            elif state != "PASSED":
                print(reformat_text(msg))

    print("-" * wrapper.width)
    # reformat_text
    print(reformat_text("Status: {}".format(status)))
    # print("Status: {}".format(status))
    print("#" * wrapper.width)
    print("\a")


def _print_test_start(data, test_index):
    print("*" * wrapper.width)
    print(reformat_text("Test {}: {}".format(test_index, data.test_desc)))
    # print("Test {}: {}".format(test_index, data.test_desc))
    print("-" * wrapper.width)


def _print_test_complete(data, test_index, status):
    sequencer = RESOURCES["SEQUENCER"]
    print("-" * wrapper.width)
    print(
        reformat_text(
            "Checks passed: {}, Checks failed: {}".format(
                sequencer.chk_pass, sequencer.chk_fail
            )
        )
    )
    # print("Checks passed: {}, Checks failed: {}".format(sequencer.chk_pass, sequencer.chk_fail))
    print(reformat_text("Test {}: {}".format(test_index, status.upper())))
    # print("Test {}: {}".format(test_index, status.upper()))
    print("-" * wrapper.width)


def _print_test_skip(data, test_index):
    print("\nTest Marked as skip")


def _print_test_retry(data, test_index):
    print(reformat_text("\nTest {}: Retry".format(test_index)))


def _print_errors(exception, test_index):
    print("")
    print("!" * wrapper.width)
    print(
        reformat_text(
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


def round_to_3_sig_figures(chk):
    """
    Tries to round elements to 3 significant figures for formatting
    :param chk:
    :return:
    """
    ret_dict = {}
    for element in ["_min", "_max", "test_val", "nominal", "tol"]:
        ret_dict[element] = getattr(chk, element, None)
        try:
            ret_dict[element] = "{:.3g}".format(ret_dict[element])
        except:
            pass
    return ret_dict


def _print_comparisons(passes, chk, chk_cnt, context):
    if passes:
        status = "PASS"
    else:
        status = "FAIL"
    format_dict = round_to_3_sig_figures(chk)
    if chk._min is not None and chk._max is not None:
        print(
            reformat_text(
                "\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {_min} - {_max} : "
                "{description}".format(
                    status=status,
                    comparison=chk.target.__name__[1:].replace("_", " "),
                    chk_cnt=chk_cnt,
                    description=chk.description,
                    **format_dict
                )
            )
        )
    elif chk.nominal is not None and chk.tol is not None:
        print(
            reformat_text(
                "\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {nominal} +- {tol}% : "
                "{description}".format(
                    status=status,
                    comparison=chk.target.__name__[1:].replace("_", " "),
                    chk_cnt=chk_cnt,
                    description=chk.description,
                    **format_dict
                )
            )
        )
    elif chk._min is not None or chk._max is not None or chk.nominal is not None:
        # Grabs the first value that isn't none. Nominal takes priority
        comp_val = next(
            format_dict[item]
            for item in ["nominal", "_min", "_max"]
            if format_dict[item] is not None
        )
        print(
            reformat_text(
                "\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {comp_val} : "
                "{description}".format(
                    status=status,
                    comparison=chk.target.__name__[1:].replace("_", " "),
                    comp_val=comp_val,
                    chk_cnt=chk_cnt,
                    description=chk.description,
                    **format_dict
                )
            )
        )
    else:
        if chk.test_val is not None:
            print(
                reformat_text(
                    "\nCheck {chk_cnt}: {status}: {test_val} : {description}".format(
                        chk_cnt=chk_cnt,
                        description=chk.description,
                        status=status,
                        **format_dict
                    )
                )
            )
        else:
            print(
                reformat_text(
                    "\nCheck {chk_cnt} : {status}: {description}".format(
                        description=chk.description, chk_cnt=chk_cnt, status=status
                    )
                )
            )
