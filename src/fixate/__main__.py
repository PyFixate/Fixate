import logging
import logging.handlers
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from functools import partial
from importlib.machinery import SourceFileLoader
from zipimport import zipimporter
from pubsub import pub
import fixate.config
from fixate.core.exceptions import SequenceAbort
from fixate.core.ui import user_serial, user_ok
from fixate.reporting import register_csv, unregister_csv
from fixate.ui_cmdline import register_cmd_line, unregister_cmd_line
import fixate.sequencer

parser = ArgumentParser(
    description="""
Fixate Command Line Interface

""",
    formatter_class=RawTextHelpFormatter,
)

logger = logging.getLogger(__name__)

# Optional Arguments
mutex_group = parser.add_mutually_exclusive_group()
mutex_group.add_argument(
    "-p",
    "--path",
    help="""Path to the directory where the script file is located. 
                         This is mutually exclusive with --zip""",
)
mutex_group.add_argument(
    "-z",
    "--zip",
    help="""Path to zip file of test scripts. Mutually exclusive with --path""",
)
parser.add_argument(
    "-l",
    "--local_log",
    "--local-log",
    help="""Deprecated. Use the -c config to set up reporting to a different directory
                    Overrides the logging path to the current working directory""",
    action="store_true",
)
parser.add_argument(
    "-q",
    "--qtgui",
    help="""Argument to select the qt gui mode. This is still in early development""",
    action="store_true",
)
parser.add_argument(
    "-d",
    "--dev",
    help="""Activate Dev Mode for more debug information""",
    action="store_true",
)
parser.add_argument(
    "-c",
    "--config",
    help="""Specify the path to a configuration file.
                    Configuration files are in yaml format. 
                    Values in this file take precedence over those in a global config file. 
                    This argument can be used multiple times with later config files taking precedence over earlier ones
                    """,
    action="append",
    default=[],
)
parser.add_argument(
    "-i",
    "--index",
    help="""Selector string that is parsed into test_data.get() hosted in the path or zip_selector file.
                    This can be used to distinguish between different configurations of tests""",
    default="default",
)
parser.add_argument(
    "--zip_selector",
    "--zip-selector",
    help="""File name in zip that hosts the test_data object to return tests. 
                    Only used if zip file is parsed in path. Use to override from default of test_variants.py""",
    default="test_variants.py",
)
parser.add_argument(
    "--script-params",
    help="""Call this for sequence context information available to the test script and logging services
                    These values will be split on = and parsed as strings into a dictionary
                    Eg. --script-params version=1 --script-params foo=bar
                    output would be
                    >>>fixate.config.RESOURCES["SEQUENCER"].context_data
                    {"version": "1", "foo":"bar", "serial_number":<--serial_number value>}
                    """,
    action="append",
    default=[],
)
parser.add_argument(
    "--serial_number", "--serial-number", help=("Serial number of the DUT.")
)
parser.add_argument(
    "--log-file", action="store", help="Specify a file to write the log to"
)
parser.add_argument(
    "--non-interactive",
    action="store_true",
    help="The sequencer will not prompt for retries.",
)
parser.add_argument(
    "--disable-logs", action="store_true", help="Turn off diagnostic logs"
)


def load_test_suite(script_path, zip_path, zip_selector):
    """
    Attempts to load a Fixate Script file from an absolute path.
    Try loading from zip, then direct script otherwise
    :param script_path:
    :param zip_path:
    :param zip_selector:
    :return:
    """
    if not any([script_path, zip_path]):
        raise ValueError("Cannot load test suite without appropriate path selected")
    if script_path is not None:
        # Do a script file load
        importer = SourceFileLoader("module.loaded_tests", script_path)
        loader = importer.load_module
        sys.path.insert(0, os.path.dirname(script_path))
    else:
        # Use Zip File
        importer = zipimporter(zip_path)
        loader = partial(importer.load_module, zip_selector.split(".")[0])
        sys.path.append(zip_path)
    logger.debug("Sys Path Appended")
    logger.debug("Source File Loaded")
    loaded_script = loader()
    sys.modules["module.loaded_tests"] = loaded_script
    logger.debug("Loaded Module")
    return loaded_script


class FixateController:
    """
    This class acts as the base controller for the command line interface.
    It may be subclassed for different execution environments
    """

    def __init__(self, sequencer, test_script_path, args):
        register_cmd_line()
        self.worker = FixateWorker(
            sequencer=sequencer, test_script_path=test_script_path, args=args
        )

    def fixate_exec(self):
        exit_code = self.worker.ui_run()
        unregister_cmd_line()
        return exit_code


class FixateSupervisor:
    def __init__(self, test_script_path, args):

        # General setup
        self.test_script_path = test_script_path
        self.args = args
        self.sequencer = fixate.sequencer.Sequencer()
        fixate.config.RESOURCES["SEQUENCER"] = self.sequencer

        # Environment specific setup
        # TODO remove this to plugin architecture
        if self.args.qtgui:  # Run with the QT GUI

            class QTController(FixateController):
                def __init__(self, sequencer, test_script_path, args):
                    from PyQt5 import QtWidgets, QtCore
                    import fixate.ui_gui_qt as gui

                    self.worker = FixateWorker(
                        test_script_path=test_script_path,
                        args=args,
                        sequencer=sequencer,
                    )

                    QtWidgets.QApplication.setAttribute(
                        QtCore.Qt.AA_EnableHighDpiScaling
                    )
                    self.fixateApp = QtWidgets.QApplication(sys.argv)
                    self.fixateApp.setQuitOnLastWindowClosed(False)
                    self.fixateDisplay = gui.FixateGUI(self.worker, self.fixateApp)
                    # Duplicate call except in the case where termination is caused by logoff/shutdown
                    self.fixateApp.aboutToQuit.connect(self.fixateDisplay.on_finish)
                    self.fixateDisplay.show()

                def fixate_exec(self):
                    self.fixateDisplay.run_sequencer()
                    exit_code = self.fixateApp.exec()

                    # Cleanup won't run in the case of Windows logoff/shutdown, but it doesn't need to, Windows will take care of it in that case
                    self.fixateApp.closeAllWindows()
                    return exit_code

            self.controller = QTController(
                sequencer=self.sequencer, test_script_path=test_script_path, args=args
            )
        else:  # Command line execution
            self.controller = FixateController(
                sequencer=self.sequencer, test_script_path=test_script_path, args=args
            )

    def run_fixate(self):
        return self.controller.fixate_exec()


class FixateWorker:
    def __init__(self, sequencer, test_script_path, args):
        self.sequencer = sequencer
        self.test_script_path = test_script_path
        self.args = args
        self.start = False
        self.clean = False
        self.config = None

    def get_task_count(self):
        return self.sequencer.count_tests()

    def get_current_task(self):
        return self.sequencer.tests_completed()

    def get_test_tree(self):
        return self.sequencer.get_tree()

    def stop(self):
        """This function is called in case of unusual termination, and runs in the main thread"""
        self.sequencer._handle_sequence_abort()
        pub.sendMessage(
            "Sequence_Abort", exception=SequenceAbort("Application Closing")
        )

        return 11

    def ui_run(self):

        serial_number = None
        test_selector = None
        self.start = True

        try:
            # args = parser.parse_args()
            if self.args.dev:
                fixate.config.DEBUG = True

            if self.args.serial_number is None:
                serial_number = user_serial("Please enter serial number")
                self.sequencer.context_data["serial_number"] = serial_number[1]
                if serial_number == "ABORT_FORCE":
                    return
            else:
                self.sequencer.context_data["serial_number"] = self.args.serial_number

            if self.test_script_path is None:
                self.test_script_path = self.args.path

            if self.args.non_interactive:
                self.sequencer.non_interactive = True

            # parse script params
            for param in self.args.script_params:
                k, v = param.split("=")
                self.sequencer.context_data[k] = v

                self.sequencer.context_data["index"] = self.args.index
            # Load test suite
            test_suite = load_test_suite(
                self.args.path, self.args.zip, self.args.zip_selector
            )
            test_data = retrieve_test_data(test_suite, self.args.index)
            self.sequencer.load(test_data)

            if self.args.local_log:
                try:
                    fixate.config.plg_csv["tpl_csv_path"] = [
                        "{tpl_time_stamp}-{index}.csv"
                    ]
                except (AttributeError, KeyError):
                    pass
            register_csv()
            self.sequencer.status = "Running"

            self.sequencer.run_sequence()
            if not self.sequencer.non_interactive:
                user_ok("Finished testing")

        except BaseException:
            import traceback

            input(traceback.print_exc())
            raise
        finally:
            unregister_csv()
            if serial_number == "ABORT_FORCE" or test_selector == "ABORT_FORCE":
                return 11
            # Let the supervisor know that the program is finishing normally
            self.clean = True
            if self.sequencer.end_status == "FAILED":
                return 10
            elif self.sequencer.status == "Aborted":
                return 11
            elif self.sequencer.end_status == "ERROR":
                return 12
            else:
                return 5


def retrieve_test_data(test_suite, index):
    """
    Tries to retrieve test data from the loaded test_suite module
    :param test_suite: Imported module with tests available
    :param index: index of test_data for getting the sequence
    :return: Dictionary of related test data. Keys as strings Keys(<sequence>,<version>,...)
    """
    try:
        data = test_suite.test_data
    except AttributeError:
        # Try legacy API
        return test_suite.TEST_SEQUENCE
    try:
        sequence = data[index]
    except KeyError as e:
        raise ValueError("Invalid test index parsed: {}".format(index)) from e
    return sequence


class RotateEachInstanceHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, mode="a", backupCount=0, encoding=None, delay=False):
        super().__init__(
            filename=filename,
            mode=mode,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
        )
        self.rotated = False

    def emit(self, record):
        if not self.rotated:
            self.rotated = True
            self.doRollover()
        super().emit(record)


def exception_hook(exctype, value, tb):
    # Sometime we don't see stderr when there is a crash. So we will log any unhandled exception
    # to improve debugging and visibility of errors.
    # note, unhandled exception might originate from a Qt Slot. For info on what Qt does
    # In that case, see the documentation here:
    # https://www.riverbankcomputing.com/static/Docs/PyQt5/incompatibilities.html#unhandled-python-exceptions
    logger.exception("Unhandled Exception", exc_info=(exctype, value, tb))
    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)


def run_main_program(test_script_path=None):
    sys.excepthook = exception_hook

    args, unknown = parser.parse_known_args()
    if not args.disable_logs:
        fixate.config.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

        handler = RotateEachInstanceHandler(
            fixate.config.LOG_DIRECTORY / "fixate.log", backupCount=10
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)

    fixate.config.load_config(args.config)
    fixate.config.load_dict_config({"log_file": args.log_file})
    supervisor = FixateSupervisor(test_script_path, args)
    exit(supervisor.run_fixate())


# Setup configuration
if __name__ == "__main__":
    run_main_program()
