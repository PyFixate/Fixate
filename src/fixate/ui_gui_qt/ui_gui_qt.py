import traceback
import sys
import msvcrt
import time
import textwrap
from queue import Empty
from pubsub import pub
from queue import Queue
from fixate.core.exceptions import UserInputError
from fixate.core.common import ExcThread
from fixate.config import RESOURCES
import fixate.config
from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from . import layout

cmd_line_queue = Queue()
wrapper = textwrap.TextWrapper(width=75)
wrapper.break_long_words = False

wrapper.drop_whitespace = True


def kb_hit_monitor(cmd_q):
    while True:
        resp = cmd_q.get()
        if resp is None:
            break  # Command send to close kb_hit monitor
        q, abort, key_presses = resp  # Begin active monitoring
        while True:
            try:
                abort.get_nowait()
                break
            except Empty:
                pass
            if msvcrt.kbhit():  # Check for key press
                key_press = msvcrt.getch()
                key = key_presses.get(key_press, None)
                if key is not None:
                    q.put(key)
                    break
            time.sleep(0.05)


class KeyboardHook:
    def __init__(self):
        self.user_fail_queue = Queue()
        self.key_monitor = None

    def install(self):
        self.key_monitor = ExcThread(target=kb_hit_monitor,
                                     args=(self.user_fail_queue,))
        self.key_monitor.start()

    def uninstall(self):
        if self.key_monitor:
            self.user_fail_queue.put(None)
            self.key_monitor.stop()
            self.key_monitor.join()
        self.key_monitor = None


key_hook = KeyboardHook()

def exception_hook(exctype, value, traceback):
    # logger.error("{}:{}:{}".format(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)
    sys.exit(1)

class FixateGUI(QtWidgets.QMainWindow, layout.Ui_FixateUI):

    input_signal = pyqtSignal(str, tuple)
    output_signal = pyqtSignal(str, QtGui.QColor)
    label_update = pyqtSignal(str)
    progress = pyqtSignal()

    """Class Constructor and destructor"""
    def __init__(self,  worker, application):
        super(FixateGUI, self).__init__(None)
        self.register_events()
        self.setupUi(self)
        self.worker = worker
        self.application = application
        sys.excepthook = exception_hook
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.finished.connect(self.finish)
        self.worker.destroyed.connect(self.finish)
        self.destroyed.connect(self.finish)
        self.worker_thread.started.connect(self.worker.ui_run)
        self.worker_thread.start()
        self.Button_1.clicked.connect(self.button_1_click)
        self.Button_2.clicked.connect(self.button_2_click)
        self.Button_3.clicked.connect(self.button_3_click)
        self.input_signal.connect(self.get_input)
        self.output_signal.connect(self.display_output)
        self.label_update.connect(self.display_test)
        self.progress.connect(self.progress_update)
        self.inputQueue = Queue()

    def __del__(self):
        self.release()

    def release(self):
        print("D1")
        self.unregister_events()
        print("D2")
        self.worker.stop()
        print("D3")
        self.worker_thread.terminate()  # This is now safe, as self.worker.stop ensures resources have been released
        print("D4")
        self.hide()
        print("D5")

    def finish(self):
        print("FINISH")
        try:
            self.application.exit(self.worker.get_status())
        except BaseException:
            self.application.exit(11)

    """Pubsub handlers for setup and teardown
       These are run in the main thread"""
    def register_events(self):
        pub.subscribe(self._print_test_start, 'Test_Start')
        pub.subscribe(self._print_test_seq_start, 'TestList_Start')
        pub.subscribe(self._print_test_complete, 'Test_Complete')
        pub.subscribe(self._print_comparisons, 'Check')
        pub.subscribe(self._print_errors, "Test_Exception")
        pub.subscribe(self._print_sequence_end, "Sequence_Complete")
        pub.subscribe(self._user_ok, 'UI_req')
        pub.subscribe(self._user_choices, "UI_req_choices")
        pub.subscribe(self._user_input, 'UI_req_input')
        pub.subscribe(self._user_display, 'UI_display')
        pub.subscribe(self._user_display_important, "UI_display_important")
        pub.subscribe(self._print_test_skip, 'Test_Skip')
        pub.subscribe(self._print_test_retry, 'Test_Retry')
        pub.subscribe(self._user_action, 'UI_action')
        key_hook.install()
        return


    def unregister_events(self):
        pub.unsubAll()
        key_hook.uninstall()
        return


    """Slot handlers for thread-gui interaction
       These are run in the main thread"""
    def display_test(self, test_index):
        self.ActiveTest.setText("Test {} running".format(test_index))

    def display_output(self, message, colour):
        self.Events.append(message)
        self.Events.verticalScrollBar().setValue(self.Events.verticalScrollBar().maximum());

    def progress_update(self):
        self.ProgressBar.setValue(self.worker.get_current_task())
        print(self.ProgressBar.styleSheet())
        # if self.worker.sequencer.tests_failed > 0 or self.worker.sequencer.tests_errored > 0:


    def get_input(self, message, choices):
        self.Events.append(message)
        self.Events.verticalScrollBar().setValue(self.Events.verticalScrollBar().maximum());
        if len(choices) == 1:
            self.Button_2.setText(choices[0])
            self.Button_2.setEnabled(True)
            self.Button_2.setDefault(True)
        elif len(choices) == 2:
            self.Button_1.setText(choices[0])
            self.Button_1.setEnabled(True)
            self.Button_1.setDefault(True)
            self.Button_3.setText(choices[1])
            self.Button_3.setEnabled(True)
        else:
            self.Button_1.setText(choices[0])
            self.Button_1.setEnabled(True)
            self.Button_1.setDefault(True)
            self.Button_2.setText(choices[1])
            self.Button_2.setEnabled(True)
            self.Button_3.setText(choices[2])
            self.Button_3.setEnabled(True)

    """User IO handlers, emit signals to trigger main thread updates via slots.
       These are run in the sequencer thread"""
    def event_output(self, message, colour=QtGui.QColor(255, 255, 255)):
        self.output_signal.emit(message, colour)


    def gui_user_input(self, message, choices):
        self.input_signal.emit(message, choices)
        return self.inputQueue.get(True)


    """UI Event Handlers, process actions taken by the user on the GUI.
       These are run in the main thread """
    def button_1_click(self):
        self.inputQueue.put(self.Button_1.text())
        self.buttonReset()

    def button_2_click(self):
        self.inputQueue.put(self.Button_2.text())
        self.buttonReset()

    def button_3_click(self):
        self.inputQueue.put(self.Button_3.text())
        self.buttonReset()

    def buttonReset(self):
        self.Button_1.setText("")
        self.Button_2.setText("")
        self.Button_3.setText("")
        self.Button_1.setEnabled(False)
        self.Button_2.setEnabled(False)
        self.Button_3.setEnabled(False)
        self.Button_1.setDefault(False)
        self.Button_2.setDefault(False)
        self.Button_3.setDefault(False)


    """UI Callables, called from the sequencer thread"""
    def reformat_text(self, text_str, first_line_fill="", subsequent_line_fill=""):
        lines = []
        wrapper.initial_indent = first_line_fill
        wrapper.subsequent_indent = subsequent_line_fill
        for ind, line in enumerate(text_str.splitlines()):
            if ind != 0:
                wrapper.initial_indent = subsequent_line_fill
            lines.append(wrapper.fill(line))
        return '\n'.join(lines)


    def _user_action(self, msg, q, abort):
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
        self.event_output('\a')
        self.event_output(self.reformat_text(msg))
        self.event_output("Press escape to fail the test or space to pass")
        global key_hook
        key_hook.user_fail_queue.put((q, abort, {b'\x1b': False, b' ': True}))


    def _user_ok(self, msg, q):
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
        msg = self.reformat_text(msg + "\n\nPress Continue to continue...")
        self.event_output('\a')
        self.gui_user_input(msg, ("Continue",))
        q.put("Result", None)


    def _user_choices(self, msg, q, choices, target, attempts=5):
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
        choicesstr = "\n" + ', '.join(choices[:-1]) + ' or ' + choices[-1] + ' '
        for _ in range(attempts):
            # This will change based on the interface
            self.event_output('\a')
            ret_val = self.gui_user_input(self.reformat_text(msg + choicesstr), choices)
            ret_val = target(ret_val, choices)
            if ret_val:
                q.put(('Result', ret_val))
                return
        q.put('Exception', UserInputError("Maximum number of attempts {} reached".format(attempts)))


    def _user_input(self, msg, q, target=None, attempts=5, kwargs=None):
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
        msg = self.reformat_text(msg, initial_indent, subsequent_indent) + "\n>>> "
        wrapper.initial_indent = ""
        wrapper.subsequent_indent = ""
        for _ in range(attempts):
            # This will change based on the interface
            self.event_output('\a')
            ret_val = input(msg)
            if target is None:
                q.put(ret_val)
                return
            ret_val = target(ret_val, **kwargs)
            if ret_val:
                q.put(('Result', ret_val))
                return
        q.put('Exception', UserInputError("Maximum number of attempts {} reached".format(attempts)))


    def _user_display(self, msg):
        """
        :param msg:
        :param important: creates a line of "!" either side of the message
        :return:
        """
        self.event_output(self.reformat_text(msg))


    def _user_display_important(self, msg):
        """
        :param msg:
        :param important: creates a line of "!" either side of the message
        :return:
        """
        self.event_output("")
        self.event_output("!" * wrapper.width)
        self.event_output("")
        self.event_output(self.reformat_text(msg))
        self.event_output("")
        self.event_output("!" * wrapper.width)


    def _print_sequence_end(self, status, passed, failed, error, skipped, sequence_status):
        self.event_output("#" * wrapper.width)
        self.event_output(self.reformat_text("Sequence {}".format(sequence_status)))
        # self.event_output("Sequence {}".format(sequence_status))
        post_sequence_info = []
        if status == "PASSED":
            post_sequence_info.extend(RESOURCES["SEQUENCER"].context_data.get("_post_sequence_info_pass", []))
        elif status == "FAILED" or status == "ERROR":
            post_sequence_info.extend(RESOURCES["SEQUENCER"].context_data.get("_post_sequence_info_fail", []))
        post_sequence_info.extend(RESOURCES["SEQUENCER"].context_data.get("_post_sequence_info", []))

        if post_sequence_info:
            self.event_output("-" * wrapper.width)
            self.event_output("IMPORTANT INFORMATION")
            for itm in post_sequence_info:
                self.event_output(self.reformat_text(itm))
        self.event_output("-" * wrapper.width)
        # self.reformat_text
        self.event_output(self.reformat_text("Status: {}".format(status)))
        # self.event_output("Status: {}".format(status))
        self.event_output("#" * wrapper.width)
        self.event_output('\a')


    def _print_test_start(self, data, test_index):
        self.event_output("*" * wrapper.width)
        self.event_output(self.reformat_text("Test {}: {}".format(test_index, data.test_desc)))
        # self.event_output("Test {}: {}".format(test_index, data.test_desc))
        self.event_output("-" * wrapper.width)
        self.label_update.emit(test_index)
        self.progress.emit()

    def _print_test_seq_start(self, data, test_index):
        self.ProgressBar.setMaximum(self.worker.task_count)
        self.progress.emit()
        self._print_test_start(data, test_index)


    def _print_test_complete(self, data, test_index, status):
        sequencer = RESOURCES["SEQUENCER"]
        self.event_output("-" * wrapper.width)
        self.event_output(self.reformat_text("Checks passed: {}, Checks failed: {}".format(sequencer.chk_pass, sequencer.chk_fail)))
        # self.event_output("Checks passed: {}, Checks failed: {}".format(sequencer.chk_pass, sequencer.chk_fail))
        self.event_output(self.reformat_text("Test {}: {}".format(test_index, status.upper())))
        # self.event_output("Test {}: {}".format(test_index, status.upper()))
        self.event_output("-" * wrapper.width)


    def _print_test_skip(self, data, test_index):
        self.event_output("\nTest Marked as skip")


    def _print_test_retry(self, data, test_index):
        self.event_output(self.reformat_text("\nTest {}: Retry".format(test_index)))


    def _print_errors(self, exception, test_index):
        self.event_output("")
        self.event_output("!" * wrapper.width)
        self.event_output(self.reformat_text("Test {}: Exception Occurred, {} {}".format(test_index, type(exception), exception)))
            # self.event_output(self.reformat_text("Test {}: Exception Occurred, {} {}".format(test_index, type(exception), traceback.format_tb(exception.__traceback__))))
        # traceback.print_tb(exception.__traceback__)
        # print(type(exception), exception)
            # self.event_output("Test {}: Exception Occurred, {} {}".format(test_index, type(exception), exception))
        self.event_output("!" * wrapper.width)
        # TODO self.event_output traceback into a debug log file
        if fixate.config.DEBUG:
            traceback.print_tb(exception.__traceback__, file=sys.stderr)


    def round_to_3_sig_figures(self, chk):
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


    def _print_comparisons(self, passes, chk, chk_cnt, context):
        if passes:
            status = "PASS"
        else:
            status = "FAIL"
        format_dict = self.round_to_3_sig_figures(chk)
        if chk._min is not None and chk._max is not None:
            self.event_output(self.reformat_text("\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {_min} - {_max} : "
                                "{description}".format(
                status=status,
                comparison=chk.target.__name__[1:].replace('_', ' '),
                chk_cnt=chk_cnt,
                description=chk.description, **format_dict)))
        elif chk.nominal is not None and chk.tol is not None:
            self.event_output(self.reformat_text("\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {nominal} +- {tol}% : "
                                "{description}".format(
                status=status,
                comparison=chk.target.__name__[1:].replace('_', ' '),
                chk_cnt=chk_cnt,
                description=chk.description, **format_dict)))
        elif chk._min is not None or chk._max is not None or chk.nominal is not None:
            # Grabs the first value that isn't none. Nominal takes priority
            comp_val = next(format_dict[item] for item in ["nominal", "_min", "_max"] if format_dict[item] is not None)
            self.event_output(self.reformat_text("\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {comp_val} : "
                                "{description}".format(
                status=status,
                comparison=chk.target.__name__[1:].replace('_', ' '),
                comp_val=comp_val,
                chk_cnt=chk_cnt,
                description=chk.description, **format_dict)))
        else:
            if chk.test_val is not None:
                self.event_output(self.reformat_text(
                    "\nCheck {chk_cnt}: {status}: {test_val} : {description}".format(chk_cnt=chk_cnt,
                                                                                     description=chk.description,
                                                                                     status=status, **format_dict)))
            else:
                self.event_output(self.reformat_text(
                    "\nCheck {chk_cnt} : {status}: {description}".format(description=chk.description, chk_cnt=chk_cnt,
                                                                         status=status)))