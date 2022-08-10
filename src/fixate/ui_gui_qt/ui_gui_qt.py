import sys
import pkgutil
import textwrap
import traceback
import logging
from collections import OrderedDict
import os.path
from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QRectF
from pubsub import pub
import fixate.config
from fixate.config import RESOURCES
from fixate.core.exceptions import UserInputError, SequenceAbort
from . import layout

logger = logging.getLogger(__name__)

wrapper = textwrap.TextWrapper(width=75)
wrapper.break_long_words = False

wrapper.drop_whitespace = True

QT_GUI_WORKING_INDICATOR = os.path.join(
    os.path.dirname(__file__), "working_indicator.gif"
)

ERROR_STYLE = """
QProgressBar{
    padding: 1px;
    margin-right: 32px;
}
QProgressBar::chunk{
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f3baba, stop: 0.6 #d30505);
    margin: 0px;
    width: 1px;
}"""

STATUS_PRIORITY = OrderedDict(
    [
        ("In Progress", (QtGui.QBrush(Qt.yellow), QtGui.QBrush(Qt.black))),
        ("Error", (QtGui.QBrush(Qt.red), QtGui.QBrush(Qt.white))),
        ("Failed", (QtGui.QBrush(Qt.red), QtGui.QBrush(Qt.black))),
        ("Aborted", (QtGui.QBrush(Qt.gray), QtGui.QBrush(Qt.white))),
        ("Passed", (QtGui.QBrush(Qt.green), QtGui.QBrush(Qt.black))),
        ("Skipped", (QtGui.QBrush(Qt.cyan), QtGui.QBrush(Qt.black))),
    ]
)


def get_status_colours(status):
    return STATUS_PRIORITY[status]


class SequencerThread(QObject):
    def __init__(self, worker, completion_callback):
        super().__init__()
        self.worker = worker
        self.completion_callback = completion_callback

    def run_thread(self):
        exit_code = self.worker.ui_run()

        self.completion_callback(exit_code)


class FixateGUI(QtWidgets.QMainWindow, layout.Ui_FixateUI):
    """
    GUI Main window
    """

    # QT Signals
    # These are the thread safe signals to update UI elements
    # Multiple Choices/ OK  signal
    sig_choices_input = pyqtSignal(str, tuple)
    # Updates the test Information above the image
    sig_label_update = pyqtSignal(str, str)
    # Signal for the text user input
    sig_text_input = pyqtSignal(str)
    # Tree Events
    sig_tree_init = pyqtSignal(list)
    sig_tree_update = pyqtSignal(str, str)
    # Active Window
    sig_active_update = pyqtSignal(str)
    sig_active_clear = pyqtSignal()
    # Error Window
    sig_error_update = pyqtSignal(str)
    sig_error_clear = pyqtSignal(str)
    # History Windows
    sig_history_update = pyqtSignal(str)
    # Image Window
    sig_image_update = pyqtSignal(str)
    sig_gif_update = pyqtSignal(str)
    sig_image_clear = pyqtSignal()

    # Progress Signals
    sig_indicator_start = pyqtSignal()
    sig_indicator_stop = pyqtSignal()
    sig_progress = pyqtSignal()
    sig_finish = pyqtSignal()

    sig_button_reset = pyqtSignal()
    sig_progress_set_max = pyqtSignal(int)

    """Class Constructor and destructor"""

    def __init__(self, worker, application):
        super().__init__()
        self.application = application
        self.register_events()
        self.setupUi(self)

        # used as a lock in display_tree so it can only be run once.
        self.treeSet = False
        self.blocked = False
        self.closing = False

        # Extra GUI setup not supported in the designer
        self.TestTree.setColumnWidth(1, 90)
        self.TestTree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.TestTree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)

        self.dialog = None
        self.image_scene = QtWidgets.QGraphicsScene()
        self.ImageView.set_scene(self.image_scene)
        self.ImageView.setScene(self.image_scene)

        self.working_indicator = QtGui.QMovie(QT_GUI_WORKING_INDICATOR)
        self.WorkingIndicator.setMovie(self.working_indicator)
        self.sig_indicator_start.emit()

        self.status_code = -1  # Default status code used to check for unusual exit

        # Timers and Threads
        self.input_queue = Queue()
        self.worker = SequencerThread(worker, self._completion_code)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run_thread)

        # UI Binds
        self.Button_1.clicked.connect(self.on_button_1_click)
        self.Button_2.clicked.connect(self.on_button_2_click)
        self.Button_3.clicked.connect(self.on_button_3_click)
        self.UserInputBox.submit.connect(self.on_text_input_submit)

        self.bind_qt_signals()

    def run_sequencer(self):
        self.worker_thread.start()

    def closeEvent(self, event):
        """This function overrides closeEvent from the MainWindow class, called in case of unusual termination"""

        event.ignore()
        self.hide()
        self.on_finish()

    def bind_qt_signals(self):
        """
        Binds the qt signals to the appropriate handlers
        :return:
        """
        self.sig_finish.connect(self.on_finish)  # Normal termination
        self.sig_choices_input.connect(self.on_choices_input)
        self.sig_label_update.connect(self.on_label_update)
        self.sig_text_input.connect(self.on_text_input)
        self.sig_tree_init.connect(self.on_tree_init)
        self.sig_tree_update.connect(self.on_tree_update)
        self.sig_progress.connect(self.on_progress)
        self.sig_indicator_start.connect(self.on_indicator_start)
        self.sig_indicator_stop.connect(self.on_indicator_stop)
        self.sig_active_update.connect(self.on_active_update)
        self.sig_active_clear.connect(self.on_active_clear)
        # TODO: I don't think the error signals and window are used. Delete?
        self.sig_error_update.connect(self.on_error_update)
        self.sig_error_clear.connect(self.on_error_clear)
        self.sig_history_update.connect(self.on_history_update)
        self.sig_image_update.connect(self.on_image_update)
        self.sig_gif_update.connect(self.on_gif_update)
        self.sig_image_clear.connect(self.on_image_clear)
        self.sig_button_reset.connect(self.on_button_reset)
        self.sig_progress_set_max.connect(self.on_progress_set_max)

    """Pubsub handlers for setup and teardown
       These are run in the main thread"""

    def register_events(self):
        pub.subscribe(self._topic_Sequence_Abort, "Sequence_Abort")
        pub.subscribe(self._topic_UI_req, "UI_req")
        pub.subscribe(self._topic_UI_req_choices, "UI_req_choices")
        pub.subscribe(self._topic_UI_req_input, "UI_req_input")
        pub.subscribe(self._topic_UI_display, "UI_display")
        pub.subscribe(self._topic_UI_display_important, "UI_display_important")
        pub.subscribe(self._topic_UI_action, "UI_action")

        # Image Window
        pub.subscribe(self._topic_UI_image, "UI_image")
        pub.subscribe(self._topic_UI_gif, "UI_gif")
        pub.subscribe(self._topic_UI_image_clear, "UI_image_clear")

        pub.subscribe(self._topic_Test_Start, "Test_Start")
        pub.subscribe(self._topic_TestList_Start, "TestList_Start")
        pub.subscribe(self._topic_Test_Complete, "Test_Complete")
        pub.subscribe(self._topic_Check, "Check")
        pub.subscribe(self._topic_Test_Exception, "Test_Exception")
        pub.subscribe(self._topic_Sequence_Complete, "Sequence_Complete")
        pub.subscribe(self._topic_Test_Skip, "Test_Skip")
        pub.subscribe(self._topic_Test_Retry, "Test_Retry")

        pub.subscribe(self._topic_UI_block_start, "UI_block_start")
        pub.subscribe(self._topic_UI_block_end, "UI_block_end")

    def _topic_Test_Start(self, data, test_index):
        self._print_test_start(data, test_index)
        self.sig_indicator_start.emit()

    def _topic_UI_block_end(self):
        self.sig_image_clear.emit()
        self.sig_active_clear.emit()
        self.sig_indicator_start.emit()

    def unregister_events(self):
        pub.unsubAll()

    """Slot handlers for thread-gui interaction
       These are run in the main thread"""

    def on_text_input(self, message):
        self.ActiveEvent.append(message)
        self.ActiveEvent.verticalScrollBar().setValue(
            self.ActiveEvent.verticalScrollBar().maximum()
        )
        self.Events.append(message)
        self.Events.verticalScrollBar().setValue(
            self.Events.verticalScrollBar().maximum()
        )
        self.UserInputBox.setPlaceholderText("Input:")
        self.UserInputBox.setEnabled(True)
        self.UserInputBox.setFocus()

    def on_indicator_start(self):
        self.WorkingIndicator.show()
        self.working_indicator.start()

    def _topic_UI_block_start(self):
        self.sig_indicator_stop.emit()

    def on_indicator_stop(self):
        self.working_indicator.stop()
        self.WorkingIndicator.hide()

    def _topic_UI_image(self, path):
        self.sig_image_update.emit(path)

    def _topic_UI_gif(self, path):
        self.sig_gif_update.emit(path)

    def on_image_update(self, path):
        """
        Adds an image to the image viewer. These images can be stacked with transparent layers to form overlays
        :param path: Relative path to image within the test scripts package
        :return: None
        """
        try:
            image_data = pkgutil.get_data("module.loaded_tests", path)
        except (FileNotFoundError, OSError):
            # When running direct from the file system, if an image isn't found we
            # get FileNotFoundError. When running from a zip file, we get OSError
            logger.exception("Image path specific in the test script was invalid")
            # message dialog so the user knows the image didn't load
            self.file_not_found(path)
        else:
            image = QtGui.QPixmap()
            image.loadFromData(image_data)
            self.image_scene.addPixmap(image)

            if any(
                [
                    isinstance(x, QtWidgets.QGraphicsProxyWidget)
                    for x in self.image_scene.items()
                ]
            ):
                # If any gifs -  need to reset the window to allow auto adjust
                self.image_scene.setSceneRect(QRectF())

            self.ImageView.fitInView(
                0,
                0,
                self.image_scene.width(),
                self.image_scene.height(),
                QtCore.Qt.KeepAspectRatio,
            )

    def on_gif_update(self, path):
        """
        Adds a gif to the image scene and start playing.
        :param path: Relative path to gif within the test scripts package
        :return: None
        """
        try:
            image_data = pkgutil.get_data("module.loaded_tests", path)
        except (FileNotFoundError, OSError):
            # When running direct from the file system, if an image isn't found we
            # get FileNotFoundError. When running from a zip file, we get OSError
            logger.exception("Image path specific in the test script was invalid")
            # message dialog so the user knows the image didn't load
            self.file_not_found(path)
        else:
            # Remove any images/gifs from image scene
            if self.image_scene.items():
                logger.error("Unsupported behaviour when overlaying .gifs")
                self.image_scene.clear()  # clear the scene

            animation = QtWidgets.QLabel()
            image_qbytes = QtCore.QByteArray(image_data)
            gif_buffer = QtCore.QBuffer(image_qbytes)
            gif_buffer.open(QtCore.QIODevice.OpenModeFlag.ReadOnly)
            movie = QtGui.QMovie(gif_buffer, QtCore.QByteArray(b"gif"))
            movie.setCacheMode(QtGui.QMovie.CacheMode.CacheAll)

            if movie.isValid():
                animation.setMovie(movie)
                self.image_scene.addWidget(animation)
                # Random fix to force proper caching:
                # https://stackoverflow.com/questions/71072485/qmovie-from-qbuffer-from-qbytearray-not-displaying-gif
                movie.jumpToFrame(movie.frameCount() - 1)
                movie.start()
                # Need to force the window size as doesn't detect movie inside label
                self.image_scene.setSceneRect(QRectF(movie.frameRect()))
            else:
                logger.error("Unable to load animation: %s", path)
                # Let the user know that animation is missing
                self.warning_box("Unable to load animation!")

            self.ImageView.fitInView(
                0,
                0,
                self.image_scene.width(),
                self.image_scene.height(),
                QtCore.Qt.KeepAspectRatio,
            )

    def _topic_UI_image_clear(self):
        self.sig_image_clear.emit()

    def on_image_clear(self):
        """Create a fresh graphics scene"""
        # NOTE image_scene.clear() does not remove all properties as desired
        self.image_scene = QtWidgets.QGraphicsScene()
        self.ImageView.set_scene(self.image_scene)
        self.ImageView.setScene(self.image_scene)

    def file_not_found(self, path):
        """
        Display warning box for an invalid image path
        :param path:
        :return:
        """

        self.dialog = QtWidgets.QMessageBox()
        self.dialog.setText("Warning: Image not Found")
        self.dialog.setInformativeText("Filename: {}".format(path))
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.dialog.setDefaultButton(QtWidgets.QMessageBox.Ok)
        self.dialog.setIcon(QtWidgets.QMessageBox.Warning)
        self.dialog.exec()

    def warning_box(self, msg: str):
        """
        Display warning box with message
        :param msg: message to display
        :return:
        """

        self.dialog = QtWidgets.QMessageBox()
        self.dialog.setText("Warning!")
        self.dialog.setInformativeText(msg)
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.dialog.setDefaultButton(QtWidgets.QMessageBox.Ok)
        self.dialog.setIcon(QtWidgets.QMessageBox.Warning)
        self.dialog.exec()

    def on_tree_init(self, tree):

        # Make sure this function is only run once
        if self.treeSet:
            return
        self.treeSet = True

        level_stack = []
        for item in tree:
            # Check Level
            if item[0].count(".") + 1 <= len(
                level_stack
            ):  # Case 1: Going out one or more levels or same level
                for _ in range(len(level_stack) - item[0].count(".")):
                    level_stack.pop()
            elif item[0].count(".") + 1 > len(
                level_stack
            ):  # Case 2: Going in one or more levels
                for index in range(item[0].count(".") + 1 - len(level_stack), 0, -1):
                    split_index = item[0].split(".")
                    if index > 1:  # More than one level, append dummy items as required
                        dummy = QtWidgets.QTreeWidgetItem()
                        dummy.setText(0, ".".join(split_index[: -(index - 1)]))
                        dummy.setText(1, "Queued")
                        dummy.setTextAlignment(1, QtCore.Qt.AlignRight)
                        level_stack.append(dummy.clone())

            tree_item = QtWidgets.QTreeWidgetItem()
            tree_item.setText(0, item[0] + ". " + item[1])
            tree_item.setTextAlignment(1, QtCore.Qt.AlignRight)
            tree_item.setText(1, "Queued")

            level_stack.append(tree_item.clone())
            if len(level_stack) > 1:  # Child Add
                level_stack[-2].addChild(level_stack[-1])
            else:  # Top Level
                self.TestTree.addTopLevelItem(level_stack[-1])

    def on_tree_update(self, test_index, status):

        if len(test_index) == 0:
            return

        colours = get_status_colours(status)
        test_index = test_index.split(".")

        #   Find the test in the tree
        current_test = self.TestTree.findItems(
            test_index[0], QtCore.Qt.MatchStartsWith, 0
        )[0]
        while len(test_index) > 1:
            test_index[0:2] = ["".join(test_index[0] + "." + test_index[1])]
            for child_index in range(current_test.childCount()):
                if current_test.child(child_index).text(0).startswith(test_index[0]):
                    current_test = current_test.child(child_index)
                    break

        # Update the test
        if status not in ["Aborted"]:
            for i in range(2):
                current_test.setBackground(i, colours[0])
                current_test.setForeground(i, colours[1])
            current_test.setText(1, status)
            current_test.setExpanded(True)

        # In case of an abort, update all remaining tests
        else:
            # todo: this seems like the wrong place for this...
            self.sig_active_update.emit("Aborting, please wait...")
            sub_finish = False
            original_test = current_test
            while current_test is not None:
                if current_test.text(1) in ["Queued"]:
                    for i in range(2):
                        current_test.setBackground(i, colours[0])
                        current_test.setForeground(i, colours[1])
                    current_test.setText(1, status)
                    current_test.setExpanded(False)
                if current_test.childCount() > 0 and not sub_finish:  # Go in a level
                    current_test = current_test.child(0)
                    sub_finish = False
                elif current_test.parent() is not None:
                    if (
                        current_test.parent().indexOfChild(current_test)
                        >= current_test.parent().childCount() - 1
                    ):  # Come out a level
                        sub_finish = True
                        current_test = current_test.parent()
                    else:
                        current_test = current_test.parent().child(
                            current_test.parent().indexOfChild(current_test) + 1
                        )  # Same level
                        sub_finish = False
                else:  # Top level test, go to next test
                    current_test = self.TestTree.topLevelItem(
                        self.TestTree.indexOfTopLevelItem(current_test) + 1
                    )
                    sub_finish = False
            current_test = original_test

        # Check for last test in group
        while current_test.parent() is not None and (
            current_test.parent().indexOfChild(current_test)
            >= current_test.parent().childCount() - 1
            or status in ["Aborted"]
        ):
            parent_status = current_test.text(1)
            current_test = current_test.parent()
            for child_index in range(
                current_test.childCount()
            ):  # Check status of all child tests
                check_status = current_test.child(child_index).text(1)
                if list(STATUS_PRIORITY.keys()).index(check_status) < list(
                    STATUS_PRIORITY.keys()
                ).index(parent_status):
                    parent_status = check_status
            colours = get_status_colours(parent_status)
            for i in range(2):
                current_test.setBackground(i, colours[0])
                current_test.setForeground(i, colours[1])
            current_test.setText(1, parent_status)
            if parent_status not in ["In Progress"]:
                current_test.setExpanded(False)

    def on_label_update(self, test_index, description):
        self.ActiveTest.setText("Test {}:".format(test_index))
        self.TestDescription.setText("{}".format(description))

    def on_active_update(self, message):
        self.ActiveEvent.append(message)
        self.ActiveEvent.verticalScrollBar().setValue(
            self.ActiveEvent.verticalScrollBar().maximum()
        )

    def on_active_clear(self):
        self.ActiveEvent.clear()
        self.ActiveEvent.verticalScrollBar().setValue(
            self.ActiveEvent.verticalScrollBar().maximum()
        )

    def on_history_update(self, message):
        self.Events.append(message)
        self.Events.verticalScrollBar().setValue(
            self.Events.verticalScrollBar().maximum()
        )

    def on_error_update(self, message):
        self.Errors.append(message)
        self.Errors.verticalScrollBar().setValue(
            self.Errors.verticalScrollBar().maximum()
        )

    def on_error_clear(self):
        self.Errors.clear()
        self.Errors.verticalScrollBar().setValue(
            self.Errors.verticalScrollBar().maximum()
        )

    def on_progress(self):
        self.ActiveEvent.clear()
        self.ProgressBar.setValue(self.worker.worker.get_current_task())
        if (
            self.worker.worker.sequencer.tests_failed > 0
            or self.worker.worker.sequencer.tests_errored > 0
        ):
            self.ProgressBar.setStyleSheet(ERROR_STYLE)

    def on_choices_input(self, message, choices):
        self.Events.append(message)
        self.ActiveEvent.append(message)
        self.Events.verticalScrollBar().setValue(
            self.Events.verticalScrollBar().maximum()
        )
        self.ActiveEvent.verticalScrollBar().setValue(
            self.ActiveEvent.verticalScrollBar().maximum()
        )
        if isinstance(choices, bool):
            pass
        elif len(choices) == 1:
            self.Button_2.setText(choices[0])
            self.Button_2.setShortcut(QtGui.QKeySequence(choices[0][0:1]))
            self.Button_2.setEnabled(True)
            self.Button_2.setDefault(True)
            self.Button_2.setFocus()
        elif len(choices) == 2:
            self.Button_1.setText(choices[0])
            self.Button_1.setShortcut(QtGui.QKeySequence(choices[0][0:1]))
            self.Button_1.setEnabled(True)
            self.Button_1.setDefault(True)
            self.Button_1.setFocus()
            self.Button_3.setText(choices[1])
            self.Button_3.setShortcut(QtGui.QKeySequence(choices[1][0:1]))
            self.Button_3.setEnabled(True)
        else:
            self.Button_1.setText(choices[0])
            self.Button_1.setShortcut(QtGui.QKeySequence(choices[0][0:1]))
            self.Button_1.setEnabled(True)
            self.Button_1.setDefault(True)
            self.Button_1.setFocus()
            self.Button_2.setText(choices[1])
            self.Button_2.setShortcut(QtGui.QKeySequence(choices[1][0:1]))
            self.Button_2.setEnabled(True)
            self.Button_3.setText(choices[2])
            self.Button_3.setShortcut(QtGui.QKeySequence(choices[2][0:1]))
            self.Button_3.setEnabled(True)

    def _topic_Sequence_Abort(self, exception=None):
        """
        This function ensures that sequence aborting is handled correctly if the sequencer is blocked waiting for input
        """

        # Release sequence blocking calls
        if self.blocked:
            self.input_queue.put("ABORT_FORCE")

    def on_finish(self):
        """
        This function is the second one called for normal termination, and the first one called for unusual termination.
        Check for abnormal termination, and stop the sequencer if required; then stop and delete the thread
        """

        if (
            self.worker_thread is None
        ):  # This function has already run, therefore main already has the status code
            return

        # The following actions must be done in a specific order, be careful when making changes to this section
        self.closing = True

        if (
            self.status_code == -1
        ):  # Unusual termination - The sequencer hasn't finished yet, stop it
            self.status_code = self.worker.worker.stop()

        self.unregister_events()  # Prevent interruption by pubsub messages

        self.worker.deleteLater()  # Schedule the thread worker for deletion
        self.worker = None  # Remove the reference to allow the GC to clean up

        self.worker_thread.exit(self.status_code)  # Exit the thread
        self.worker_thread.wait(2000)  # 2 seconds for the thread to exit
        self.worker_thread.terminate()  # Force quit the thread if it is still running, if so, this will throw a warning
        self.worker_thread.deleteLater()  # Schedule the thread for deletion
        self.worker_thread = None  # Remove the reference to allow the GC to clean up

        #   Now close the GUI thread, return to the controller in main
        self.application.exit(self.status_code)

    """User IO handlers, emit signals to trigger main thread updates via slots.
       These are run in the sequencer thread"""

    def gui_user_input(self, message, choices=None):
        if choices is not None:  # Button Prompt
            self.sig_choices_input.emit(message, choices)
        else:  # Text Prompt
            self.sig_text_input.emit(message)

        self.blocked = True
        result = self.input_queue.get()
        self.blocked = False
        return result

    """UI Event Handlers, process actions taken by the user on the GUI.
       These are run in the main thread """

    def on_text_input_submit(self):
        self.input_queue.put(self.UserInputBox.toPlainText())
        self.UserInputBox.clear()
        self.UserInputBox.setPlaceholderText("")
        self.UserInputBox.setEnabled(False)

    def on_button_1_click(self):
        self.input_queue.put(self.Button_1.text())
        self.on_button_reset()

    def on_button_2_click(self):
        self.input_queue.put(self.Button_2.text())
        self.on_button_reset()

    def on_button_3_click(self):
        self.input_queue.put(self.Button_3.text())
        self.on_button_reset()

    def on_button_reset(self):
        self.Button_1.setText("")
        self.Button_2.setText("")
        self.Button_3.setText("")

        self.Button_1.setEnabled(False)
        self.Button_2.setEnabled(False)
        self.Button_3.setEnabled(False)

        self.Button_1.setDefault(False)
        self.Button_2.setDefault(False)
        self.Button_3.setDefault(False)

    def on_progress_set_max(self, test_count):
        self.ProgressBar.setMaximum(test_count)

    """Thread listener, called from the sequencer thread"""

    def _completion_code(self, code):
        """This function is the first one called when the sequencer completes normally.
        Set the exit code, and signal the main thread."""
        self.status_code = code
        self.sig_finish.emit()

    """UI Callables, called from the sequencer thread"""

    def reformat_text(self, text_str, first_line_fill="", subsequent_line_fill=""):
        lines = []
        wrapper.initial_indent = first_line_fill
        wrapper.subsequent_indent = subsequent_line_fill
        for ind, line in enumerate(text_str.splitlines()):
            if ind != 0:
                wrapper.initial_indent = subsequent_line_fill
            lines.append(wrapper.fill(line))
        return "\n".join(lines)

    def _topic_UI_action(self, msg, callback_obj):
        """
        This is for tests that aren't entirely dependant on the automated system.
        This works by monitoring a queue to see if the test completed successfully.
        Also while doing this it is monitoring if the Fail button is pressed to signal to
        the system that the test fails.

        TODO: Connect this to ESC also, so that it is consistent with the cli?

        Use this in situations where you want the user to do something (like press all the keys
        on a keypad) where the system is automatically monitoring for success but has no way of
        monitoring failure.
        :param msg: Information for the user
        :param callback_obj:
         callback_obj used to communicate back to the user_action call in ui.py.
        :return: None
        """

        # Subscribed to "UI_action" pubsub topic.
        # pub.sendMessage("UI_action", msg=msg, callback=callback_obj)
        if self.closing:
            # We're closing, so we won't connect the real input_queue.
            # Instead create a new one and put something in it so the
            # user action bails immediately.
            fake_input_queue = Queue()
            callback_obj.set_user_cancel_queue(fake_input_queue)
            fake_input_queue.put("Fail")
        else:
            callback_obj.set_user_cancel_queue(self.input_queue)
            # If the test script target finishes the user_action, we
            # want to reset the button back to the default state. So
            # we pass in the signal emit method to call button_reset
            # in the GUI thread.
            callback_obj.set_target_finished_callback(self.sig_button_reset.emit)
            self.sig_choices_input.emit(msg, ("Fail",))

    def _topic_UI_req(self, msg, q):
        """
        This can be replaced anywhere in the project that needs to implement the user driver
        The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the
        second part is the exception object or response object
        :param msg:
         Message for the user to understand what to do
        :param q:
         The result queue of type queue.Queue
        :return:
        """
        if self.closing:
            q.put("Result", None)
            return
        self.gui_user_input(msg, ("Continue",))
        q.put("Result", None)

    def _topic_UI_req_choices(self, msg, q, choices, target, attempts=5):
        """
        This can be replaced anywhere in the project that needs to implement the user driver
        Temporarily a simple input function.
        The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the
        second part is the exception object or response object
        This needs to be compatible with forced exit. Look to user action for how it handles a forced exit
        :param msg:
         Message for the user to understand what to input
        :param q:
         The result queue of type queue.Queue
        :param target:
         Optional
         Validation function to check if the user response is valid
        :param attempts:
        :return:
        """
        if self.closing:
            q.put(("Result", "ABORT_FORCE"))
            return

        for _ in range(attempts):
            # This will change based on the interface
            ret_val = self.gui_user_input(self.reformat_text(msg), choices)
            ret_val = target(ret_val, choices)
            if ret_val:
                q.put(("Result", ret_val))
                return
        q.put(
            "Exception",
            UserInputError("Maximum number of attempts {} reached".format(attempts)),
        )

    def _topic_UI_req_input(self, msg, q, target=None, attempts=5, kwargs=None):
        """
        This can be replaced anywhere in the project that needs to implement the user driver
        Temporarily a simple input function.
        The result needs to be put in the queue with the first part of the tuple as 'Exception' or 'Result' and the
        second part is the exception object or response object
        This needs to be compatible with forced exit. Look to user action for how it handles a forced exit
        :param msg:
         Message for the user to understand what to input
        :param q:
         The result queue of type queue.Queue
        :param target:
         Optional
         Validation function to check if the user response is valid
        :param attempts:

        :param kwargs:
        :return:
        """
        if self.closing:
            q.put(("Result", "ABORT_FORCE"))
            return

        msg = self.reformat_text(msg)
        wrapper.initial_indent = ""
        wrapper.subsequent_indent = ""
        for _ in range(attempts):
            # This will change based on the interface
            ret_val = self.gui_user_input(msg, None)
            if target is None or ret_val == "ABORT_FORCE":
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

    def _topic_UI_display(self, msg):
        """
        :param msg:
        :return:
        """
        if self.closing:
            return
        self.sig_active_update.emit(self.reformat_text(msg))
        self.sig_history_update.emit(self.reformat_text(msg))

    def _topic_UI_display_important(self, msg):
        """
        :param msg:
        :return:
        """
        if self.closing:
            return

        self.sig_history_update.emit("")
        self.sig_history_update.emit("!" * wrapper.width)
        self.sig_active_update.emit("!" * wrapper.width)
        self.sig_history_update.emit("")
        self.sig_history_update.emit(self.reformat_text(msg))
        self.sig_active_update.emit(self.reformat_text(msg))
        self.sig_history_update.emit("")
        self.sig_history_update.emit("!" * wrapper.width)
        self.sig_active_update.emit("!" * wrapper.width)

    def _topic_Sequence_Complete(
        self, status, passed, failed, error, skipped, sequence_status
    ):
        if self.closing:
            return

        self.sig_history_update.emit("#" * wrapper.width)
        post_sequence_info = RESOURCES["SEQUENCER"].context_data.get(
            "_post_sequence_info", {}
        )
        if post_sequence_info:
            self.sig_history_update.emit("-" * wrapper.width)
            self.sig_history_update.emit("IMPORTANT INFORMATION")
            self.sig_active_update.emit("IMPORTANT INFORMATION")

            for msg, state in post_sequence_info.items():
                if status == "PASSED":
                    if state == "PASSED" or state == "ALL":
                        self.sig_history_update.emit(self.reformat_text(msg))
                        self.sig_active_update.emit(self.reformat_text(msg))
                elif state != "PASSED":
                    self.sig_history_update.emit(self.reformat_text(msg))
                    self.sig_active_update.emit(self.reformat_text(msg))

        self.sig_history_update.emit("-" * wrapper.width)
        self.sig_history_update.emit(self.reformat_text("Status: {}".format(status)))
        self.sig_active_update.emit(self.reformat_text("Status: {}".format(status)))
        self.sig_history_update.emit("#" * wrapper.width)

    def _print_test_start(self, data, test_index):
        if self.closing:
            return

        self.sig_progress.emit()
        self.sig_history_update.emit("*" * wrapper.width)
        self.sig_history_update.emit(
            self.reformat_text("Test {}: {}".format(test_index, data.test_desc))
        )
        self.sig_history_update.emit("-" * wrapper.width)
        self.sig_label_update.emit(test_index, data.test_desc)
        self.sig_tree_update.emit(test_index, "In Progress")

    def _topic_TestList_Start(self, data, test_index):
        if self.closing:
            return

        self.sig_progress_set_max.emit(self.worker.worker.get_task_count())
        self.sig_tree_init.emit(self.worker.worker.get_test_tree())
        self.sig_progress.emit()
        self._print_test_start(data, test_index)

    def _topic_Test_Complete(self, data, test_index, status):
        if self.closing:
            return

        sequencer = RESOURCES["SEQUENCER"]
        self.sig_history_update.emit("-" * wrapper.width)
        self.sig_history_update.emit(
            self.reformat_text(
                "Checks passed: {}, Checks failed: {}".format(
                    sequencer.chk_pass, sequencer.chk_fail
                )
            )
        )
        self.sig_history_update.emit(
            self.reformat_text("Test {}: {}".format(test_index, status.upper()))
        )
        self.sig_history_update.emit("-" * wrapper.width)

        if status.upper() in ["ERROR", "SKIPPED"]:
            return

        if sequencer.chk_fail == 0:
            self.sig_tree_update.emit(test_index, "Passed")
        else:
            self.sig_tree_update.emit(test_index, "Failed")

    def _topic_Test_Skip(self, data, test_index):
        if self.closing:
            return

        self.sig_history_update.emit("\nTest Marked as skip")
        self.sig_tree_update.emit(test_index, "Skipped")

    def _topic_Test_Retry(self, data, test_index):
        if self.closing:
            return

        self.sig_history_update.emit(
            self.reformat_text("\nTest {}: Retry".format(test_index))
        )

    def _topic_Test_Exception(self, exception, test_index):
        if self.closing:
            return

        if isinstance(exception, SequenceAbort):
            self.sig_tree_update.emit(test_index, "Aborted")
        else:
            self.sig_tree_update.emit(test_index, "Error")
        self.sig_history_update.emit("")
        self.sig_history_update.emit("!" * wrapper.width)
        self.sig_active_update.emit("!" * wrapper.width)
        self.sig_history_update.emit(
            self.reformat_text(
                "Test {}: Exception Occurred, {} {}".format(
                    test_index, type(exception), exception
                )
            )
        )
        self.sig_active_update.emit(
            self.reformat_text(
                "Test {}: Exception Occurred, {} {}".format(
                    test_index, type(exception), exception
                )
            )
        )
        self.sig_history_update.emit("!" * wrapper.width)
        self.sig_active_update.emit("!" * wrapper.width)
        # TODO self.history_update traceback into a debug log file
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

    def _topic_Check(self, passes, chk, chk_cnt, context):
        if passes:
            status = "PASS"
        else:
            status = "FAIL"
        format_dict = self.round_to_3_sig_figures(chk)
        if chk._min is not None and chk._max is not None:
            msg = self.reformat_text(
                "\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {_min} - {_max} : "
                "{description}".format(
                    status=status,
                    comparison=chk.target.__name__[1:].replace("_", " "),
                    chk_cnt=chk_cnt,
                    description=chk.description,
                    **format_dict
                )
            )
            self.sig_history_update.emit(msg)
            if status == "FAIL":
                self.sig_active_update.emit(msg)
        elif chk.nominal is not None and chk.tol is not None:
            msg = self.reformat_text(
                "\nCheck {chk_cnt}: {status} when comparing {test_val} {comparison} {nominal} +- {tol}% : "
                "{description}".format(
                    status=status,
                    comparison=chk.target.__name__[1:].replace("_", " "),
                    chk_cnt=chk_cnt,
                    description=chk.description,
                    **format_dict
                )
            )
            self.sig_history_update.emit(msg)
            if status == "FAIL":
                self.sig_active_update.emit(msg)
        elif chk._min is not None or chk._max is not None or chk.nominal is not None:
            # Grabs the first value that isn't none. Nominal takes priority
            comp_val = next(
                format_dict[item]
                for item in ["nominal", "_min", "_max"]
                if format_dict[item] is not None
            )
            msg = self.reformat_text(
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
            self.sig_history_update.emit(msg)
            if status == "FAIL":
                self.sig_active_update.emit(msg)
        else:
            if chk.test_val is not None:
                msg = self.reformat_text(
                    "\nCheck {chk_cnt}: {status}: {test_val} : {description}".format(
                        chk_cnt=chk_cnt,
                        description=chk.description,
                        status=status,
                        **format_dict
                    )
                )
                self.sig_history_update.emit(msg)
                if status == "FAIL":
                    self.sig_active_update.emit(msg)
            else:
                msg = self.reformat_text(
                    "\nCheck {chk_cnt} : {status}: {description}".format(
                        description=chk.description, chk_cnt=chk_cnt, status=status
                    )
                )
                self.sig_history_update.emit(msg)
                if status == "FAIL":
                    self.sig_active_update.emit(msg)
