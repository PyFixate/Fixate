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
from fixate.config.local_config import save_local_config
from fixate.config import ASYNC_TASKS, RESOURCES
from fixate.core.ui import user_ok, user_input, user_serial, user_info
from fixate.reporting import register_csv, unregister_csv
from fixate.ui_cmdline import register_cmd_line, unregister_cmd_line
from fixate.core.exceptions import ScriptError

try:
    asyncio.ensure_future
except AttributeError:
    asyncio.ensure_future = asyncio.async  # Compatabiltiy with 3.4.4 and 3.5
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


def run_qt_gui(test_script_path=None, csv_output_path=None, args=None):
    from fixate.ui_gui_qt import register_qt_gui, unregister_qt_gui
    ui_run(test_script_path, csv_output_path, args, register_qt_gui, unregister_qt_gui)


def run_cmd_line(test_script_path=None, csv_output_path=None, args=None):
    ui_run(test_script_path, csv_output_path, args, register_cmd_line, unregister_cmd_line)


def ui_run(test_script_path, csv_output_path, args, register_ui, unregister_ui):
    """Common tasks for each UI"""
    sequencer = RESOURCES["SEQUENCER"]
    try:
        # args = parser.parse_args()
        if args.dev:
            fixate.config.DEBUG = True
        register_ui()  # subscribe to pub messages
        if args.index is None:
            args.index = user_input("Please enter test selector string")[1]
        if args.serial_number is None:
            sequencer.context_data["serial_number"] = user_serial("Please enter serial number")[1]
        else:
            sequencer.context_data["serial_number"] = args.serial_number
        if test_script_path is None:
            test_script_path = args.path
        # parse script params
        for param in args.script_params:
            k, v = param.split("=")
            sequencer.context_data[k] = v

        sequencer.context_data["index"] = args.index
        # Load test suite
        test_suite = load_test_suite(args.path, args.zip, args.zip_selector)
        test_data = retrieve_test_data(test_suite, args.index)
        sequencer.load(test_data)
        if args.local_log:
            csv_output_path = os.path.join(os.path.dirname(test_script_path))
        if csv_output_path is None:
            csv_output_path = os.path.join(base_csv_path, sequencer.context_data.get("part_number", ""),
                                           sequencer.context_data.get("module", ""))
        register_csv(csv_output_path)
        sequencer.status = 'Running'
        loop = asyncio.get_event_loop()

        def init_tasks():
            pass

        def cancel_tasks():
            for task in ASYNC_TASKS:
                task.cancel()

        def finished_test_run_response(future):
            future.result()
            loop.call_soon(cancel_tasks)
            loop.call_later(1, loop.stop)  # Max 1 second to clean up tasks before aborting

        def finished_test_run(future):
            loop.call_soon(cancel_tasks)
            if sequencer.status in ["Finished", "Aborted"]:
                f = functools.partial(user_ok, "Finished testing")
                loop.run_in_executor(None, f).add_done_callback(finished_test_run_response)

        init_tasks()
        loop.run_in_executor(None, sequencer.run_sequence).add_done_callback(finished_test_run)

        try:
            loop.run_forever()
        finally:
            loop.close()
    except BaseException:
        import traceback
        input(traceback.print_exc())
        raise
    finally:
        unregister_ui()
        unregister_csv()
        save_local_config()
        if sequencer.end_status == "FAILED":
            exit(10)
        elif sequencer.status == "Aborted":
            exit(11)
        elif sequencer.end_status == "ERROR":
            exit(12)
            # Else Passed is exit(0)


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
    if args.qtgui:
        run_qt_gui(test_script_path, csv_output_path, args)
    else:
        run_cmd_line(test_script_path, csv_output_path, args)


# Default directory if none is provided
base_csv_path = os.path.dirname("\\\\cam-fs001\\Groups\\Production\\Test Programs\\Amptest Logs\\")

# Setup configuration
if __name__ == "__main__":
    run_main_program()
