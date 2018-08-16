import argparse
import asyncio
import importlib.machinery
import os
import sys
import functools
import logging
from argparse import RawTextHelpFormatter
import zipimport
import fixate.config
from time import sleep
from fixate.config.local_config import save_local_config
from fixate.config import ASYNC_TASKS, RESOURCES
from fixate.core.ui import user_ok, user_input, user_serial, user_info
from fixate.reporting import register_csv, unregister_csv
from fixate.ui_cmdline import register_cmd_line, unregister_cmd_line
from fixate.core.exceptions import ScriptError, SequenceAbort
from pubsub import pub

try:
    asyncio.ensure_future
except AttributeError:
    asyncio.ensure_future = getattr(asyncio, 'async')  # Compatability with 3.4.4 and 3.5
parser = argparse.ArgumentParser(description="""
Fixate Command Line Interface

""", formatter_class=RawTextHelpFormatter)

logger = logging.getLogger(__name__)

# Optional Arguments
mutex_group = parser.add_mutually_exclusive_group()
mutex_group.add_argument('-p', '--path',
                         help="""Path to the directory where the script file is located. 
                         This is mutually exclusive with --zip""")
mutex_group.add_argument('-z', '--zip',
                         help="""Path to zip file of test scripts. Mutually exclusive with --path""", )

parser.add_argument('-l', '--local_log',
                    help="""Overrides the logging path to the current working directory""",
                    action="store_true")
parser.add_argument('-q', '--qtgui',
                    help="""Argument to select the qt gui mode. This is still in early development""",
                    action="store_true")
parser.add_argument('-d', '--dev',
                    help="""Activate Dev Mode for more debug information""",
                    action="store_true")
parser.add_argument('-n', '--n_loops',
                    help="""Loop the test. Use -1 for infinite loops""",
                    action="store")
parser.add_argument('-a', '--abort_force',
                    help="""Forces an abort instead of prompting the user for retry abort fail""",
                    action="store_true")
parser.add_argument('-f', '--fail_force',
                    help="""Forces a fail instead of prompting the user for retry abort fail""",
                    action="store_true")
parser.add_argument('-r', '--retry_force',
                    help="""Forces a retry instead of prompting the user for retry abort fail""",
                    action="store_true")
parser.add_argument('-i', '--index',
                    help="""Selector string that is parsed into test_data.get() hosted in the path or zip_selector file.
                    This can be used to distinguish between different configurations of tests""",
                    default="default")
parser.add_argument('--zip_selector',
                    help="""File name in zip that hosts the test_data object to return tests. 
                    Only used if zip file is parsed in path. Use to override from default of test_variants.py""",
                    default="test_variants.py")
parser.add_argument('--script-params',
                    help="""Call this for sequence context information available to the test script and logging services
                    These values will be split on = and parsed as strings into a dictionary
                    Eg. --script-params version=1 --script-params foo=bar
                    output would be
                    >>>fixate.config.RESOURCES["SEQUENCER"].context_data
                    {"version": "1", "foo":"bar", "serial_number":<--serial_number value>}
                    """,
                    action='append',
                    default=[])
parser.add_argument('--serial_number',
                    help=("Serial number of the DUT."))


def load_test_suite(script_path, zip_path, zip_selector):
    """
    Attempts to load a Fixate Script file from an absolute path.
    Try loading from zip, then direct script otherwise
    :param cli_args:
    :return:
    """
    if not any([script_path, zip_path]):
        raise ValueError("Cannot load test suite without appropriate path selected")
    if script_path is not None:
        # Do a script file load
        importer = importlib.machinery.SourceFileLoader('module.loaded_tests', script_path)
        loader = importer.load_module
        sys.path.append(os.path.dirname(script_path))
    else:
        # Use Zip File
        importer = zipimport.zipimporter(zip_path)
        loader = functools.partial(importer.load_module, zip_selector.split('.')[0])
        sys.path.append(zip_path)
    logger.debug("Sys Path Appended")
    logger.debug("Source File Loaded")
    loaded_script = loader()
    sys.modules["module.loaded_tests"] = loaded_script
    logger.debug("Loaded Module")
    return loaded_script


class FixateController:
    """This class acts as the base controller for the command line interface. It may be subclassed for different execution environments"""

    def __init__(self, sequencer, test_script_path, csv_output_path, args, loop):
        register_cmd_line()
        # self.register()
        self.worker = FixateWorker(sequencer=sequencer, test_script_path=test_script_path,
                                   csv_output_path=csv_output_path, args=args, loop=loop)

    def fixate_exec(self):
        exit_code = self.worker.ui_run()
        unregister_cmd_line()
        # self.unregister()
        return exit_code


class FixateSupervisor:
    def __init__(self, test_script_path, csv_output_path, args):

        # General setup
        self.test_script_path = test_script_path
        self.csv_output_path = csv_output_path
        self.args = args
        self.loop = asyncio.get_event_loop()
        self.sequencer = RESOURCES["SEQUENCER"]

        # Environment specific setup
        if self.args.qtgui:  # Run with the QT GUI
            self.loop = asyncio.new_event_loop()

            class QTController(FixateController):
                def __init__(self, sequencer, test_script_path, csv_output_path, args, loop):
                    from PyQt5 import QtWidgets
                    import fixate.ui_gui_qt as gui

                    self.worker = FixateWorker(test_script_path=test_script_path, csv_output_path=csv_output_path,
                                               args=args, loop=loop, sequencer=sequencer)

                    self.fixateApp = QtWidgets.QApplication(sys.argv)
                    self.fixateApp.setQuitOnLastWindowClosed(False)
                    self.fixateDisplay = gui.FixateGUI(self.worker, self.fixateApp)
                    self.fixateApp.aboutToQuit.connect(self.fixateDisplay.clean_up)  # Duplicate call except in the case where termination is caused by logoff/shutdown
                    self.fixateDisplay.show()

                def fixate_exec(self):
                    self.fixateDisplay.run_sequencer()
                    exit_code = self.fixateApp.exec()

                    # Cleanup won't run in the case of Windows logoff/shutdown, but it doesn't need to, Windows will take care of it in that case
                    self.fixateApp.closeAllWindows()
                    return exit_code

            self.controller = QTController(sequencer=self.sequencer, test_script_path=test_script_path,
                                           csv_output_path=csv_output_path, args=args, loop=self.loop)
        else:  # Command line execution
            self.controller = FixateController(sequencer=self.sequencer, test_script_path=test_script_path,
                                               csv_output_path=csv_output_path, args=args, loop=self.loop)

    def run_fixate(self):
        return self.controller.fixate_exec()


class FixateWorker():
    def __init__(self, sequencer, test_script_path, csv_output_path, args, loop):
        self.sequencer = sequencer
        self.test_script_path = test_script_path
        self.csv_output_path = csv_output_path
        self.args = args
        self.loop = loop
        self.start = False
        self.clean = False

    def get_task_count(self):
        return self.sequencer.count_tests()

    def get_current_task(self):
        return self.sequencer.tests_completed()

    def stop(self):
        """This function is called in case of unusual termination, and runs in the main thread"""
        self.sequencer._handle_sequence_abort()
        pub.sendMessage("Sequence_Abort", exception=SequenceAbort("Application closing"))
        self.loop.stop()

        for _ in range(15):
            if self.loop.is_running():  # Wait max 15 seconds for loop to end
                sleep(1)
            else:
                break
        try:
            self.loop.close()
        except Exception:
            pass  # If the thread has hung, or reached an uninterruptable state, ignore it, it'll be force terminated at the end anyway

        return 11

    def ui_run(self):

        asyncio.set_event_loop(self.loop)
        self.start = True

        try:
            # args = parser.parse_args()
            if self.args.dev:
                fixate.config.DEBUG = True
            if self.args.index is None:
                self.args.index = user_input("Please enter test selector string")[1]
            if self.args.serial_number is None:
                self.sequencer.context_data["serial_number"] = user_serial("Please enter serial number")[1]
            else:
                self.sequencer.context_data["serial_number"] = self.args.serial_number
            if self.test_script_path is None:
                self.test_script_path = self.args.path
            # parse script params
            for param in self.args.script_params:
                k, v = param.split("=")
                self.sequencer.context_data[k] = v

                self.sequencer.context_data["index"] = self.args.index
            # Load test suite
            test_suite = load_test_suite(self.args.path, self.args.zip, self.args.zip_selector)
            test_data = retrieve_test_data(test_suite, self.args.index)
            self.sequencer.load(test_data)
            if self.args.local_log:
                self.csv_output_path = os.path.join(os.path.dirname(self.test_script_path))
            if self.csv_output_path is None:
                self.csv_output_path = os.path.join(base_csv_path, self.sequencer.context_data.get("part_number", ""),
                                                    self.sequencer.context_data.get("module", ""))
            register_csv(self.csv_output_path)
            self.sequencer.status = 'Running'

            def init_tasks():
                pass

            def cancel_tasks():
                for task in ASYNC_TASKS:
                    task.cancel()

            def finished_test_run_response(future):
                future.result()
                self.loop.call_soon(cancel_tasks)
                self.loop.call_later(1, self.loop.stop)  # Max 1 second to clean up tasks before aborting

            def finished_test_run(future):
                self.loop.call_soon(cancel_tasks)
                if self.sequencer.status in ["Finished", "Aborted"]:
                    f = functools.partial(user_ok, "Finished testing")
                    self.loop.run_in_executor(None, f).add_done_callback(finished_test_run_response)

            init_tasks()
            self.loop.run_in_executor(None, self.sequencer.run_sequence).add_done_callback(finished_test_run)

            try:
                self.loop.run_forever()
            finally:
                self.loop.close()
        except BaseException:
            import traceback
            input(traceback.print_exc())
            raise
        finally:
            unregister_csv()
            save_local_config()
            self.clean = True  # Let the supervisor know that the program is finishing normally
            if self.sequencer.end_status == "FAILED":
                return 10
            elif self.sequencer.status == "Aborted":
                return 11
            elif self.sequencer.end_status == "ERROR":
                return 12
            else:
                # Else Passed is exit(0)
                return 0


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


def run_main_program(test_script_path=None, csv_output_path=None):
    args, unknown = parser.parse_known_args()
    supervisor = FixateSupervisor(test_script_path, csv_output_path, args)
    exit(supervisor.run_fixate())


# Default directory if none is provided
base_csv_path = os.path.dirname("\\\\cam-fs001\\Groups\\Production\\Test Programs\\Amptest Logs\\")

# Setup configuration
if __name__ == "__main__":
    run_main_program()
