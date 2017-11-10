import argparse
import asyncio
import importlib.machinery
import os
import sys
import functools
import logging
from argparse import RawTextHelpFormatter

import fixate.config
from fixate.config.local_config import save_local_config
from fixate.config import ASYNC_TASKS, RESOURCES
from fixate.core.ui import user_yes_no
from fixate.reporting import register_csv, unregister_csv
from fixate.ui_cmdline import register_cmd_line, unregister_cmd_line
from fixate.core.exceptions import ScriptError

try:
    asyncio.ensure_future  # Used in Python 3.4.<4
except AttributeError:
    asyncio.ensure_future = asyncio.async  # Compatabiltiy with 3.4.4 and 3.5

parser = argparse.ArgumentParser(description="fixate Command Line Interface", formatter_class=RawTextHelpFormatter)

logger = logging.getLogger(__name__)

# Optional Arguments
parser.add_argument('-p', '--path',
                    help="""Path to the script file to load tests""")

parser.add_argument('-ll', '--local_log',
                    help="""Path to the script file to load tests""",
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


def load_test_suite_from_path(path):
    """
    Attempts to load a fixate Script file from an absolute path
    :param path:
    :return:
    """
    logger.debug(path)
    sys.path.append(os.path.dirname(path))
    logger.debug("Sys Path Appended")
    loader = importlib.machinery.SourceFileLoader('module.loaded_tests', path)
    logger.debug("Source File Loaded")
    try:
        loaded_script = loader.load_module()
    except Exception as e:
        raise ScriptError("Invalid Python file type") from e
    logger.debug("Loaded Module")
    return loaded_script


def run_cmd_line(test_script_path=None, csv_output_path=None, args=None):
    sequencer = RESOURCES["SEQUENCER"]

    try:
        # args = parser.parse_args()
        if test_script_path is None:
            test_script_path = args.path
        sequencer.load(load_test_suite_from_path(test_script_path).TEST_SEQUENCE)
        if args.dev:
            fixate.config.DEBUG = True
        register_cmd_line()  # subscribe cmd_line to pub messages
        if args.local_log:
            csv_output_path = os.path.dirname(test_script_path)
        if csv_output_path is None:
            if test_script_path is None:
                csv_output_path = ""
            else:
                csv_output_path = os.path.dirname(test_script_path)

        register_csv(os.path.dirname(csv_output_path))
        sequencer.status = 'Running'
        loop = asyncio.get_event_loop()

        def init_tasks():
            pass

        def cancel_tasks():
            for task in ASYNC_TASKS:
                task.cancel()

        def finished_test_run_response(future):
            try:
                _, resp = future.result()
            except ValueError:
                f = functools.partial(user_yes_no, "Do you want to test another?")
                loop.run_in_executor(None, f).add_done_callback(finished_test_run_response)
                return
            if "NO".startswith(resp.upper()):
                loop.call_soon(cancel_tasks)
                loop.call_later(1, loop.stop)  # Max 1 second to clean up tasks before aborting
            if "YES".startswith(resp.upper()):
                sequencer._restart()
                loop.run_in_executor(None, sequencer.run_sequence).add_done_callback(finished_test_run)
                init_tasks()

        def finished_test_run(future):
            loop.call_soon(cancel_tasks)
            if sequencer.status in ["Finished", "Aborted"]:
                f = functools.partial(user_yes_no, "Do you want to test another?")
                loop.run_in_executor(None, f).add_done_callback(finished_test_run_response)

        init_tasks()
        loop.run_in_executor(None, sequencer.run_sequence).add_done_callback(finished_test_run)

        try:
            loop.run_forever()
        finally:
            loop.close()
    finally:
        unregister_cmd_line()
        unregister_csv()
        save_local_config()

        if sequencer.status == "Aborted":
            exit(1)


def run_main_program(test_script_path=None, csv_output_path=None):
    args = parser.parse_args()
    run_cmd_line(test_script_path, csv_output_path, args)

# Setup configuration
if __name__ == "__main__":
    run_main_program()
