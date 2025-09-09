from datetime import datetime
import logging
import sys
import os
import time
import json

from pydantic.dataclasses import dataclass, Field
from pydantic.json import pydantic_encoder
from pubsub import pub

from queue import Queue
from fixate.core.common import TestClass
from fixate.core.checks import CheckResult
import fixate
import fixate.config

logger = logging.getLogger()

"""
Example of a log file:  
Note that this is not currently exactly what the code outputs. It's more of a guide of what we want 
to get to.

{
    "serial_number" : "1234567890", 
    "start_time_millis": 1747868933064,
    "end_time_millis": 1747868933064,
    "outcome" : "FAIL",
    "outcome_details" : [] 
    "module_name" : "test_module",  
    "part_number" : "123456",
    "tests" : [
            {
                "test_name": "TestCrowbars",
                "test_list" : "MainTestList",
                "measurements" : [
                        {   
                            "name": "measure r41 resistance",
                            "outcome": "PASS",
                            "validators": [
                                "9 <= x <= 11"
                            ],
                            "units": {
                                "name": "ohm",
                                "code": "OHM",
                                "suffix": "\u2126"
                            },
                            "measured_value": 9.989233575589664
                        },
                        {   
                            "name": "measure r43 resistance",
                            "outcome": "FAIL",
                            "validators": [
                                "x < 119"
                            ],
                            "units": {
                                "name": "ohm",
                                "code": "OHM",
                                "suffix": "\u2126"
                            },
                            "measured_value": 900
                        },
                        {   
                            "name": "log the value of something",
                            "outcome": "PASS",
                            "validators": [ ],
                            "units": {
                                "name": "string",
                                "code": "STRING",
                                "suffix": ""
                            },
                            "measured_value": "On chk log, we might be able to dynamically populate the type information to put into the above fields"
                        },
                ],  
              "parameters": {"testclassargs": ["things","stuff"]}
              "start_time_millis": 1747868933064,
              "end_time_millis": 1747868933064,
            }
    ],
    "instruments" : [
            {
                "type" : "DMM", # We may need to add a type attribute to the drivers?
                "name" : "FLUKE BLAH BLAH",  
                "serial" : "1234",
            },
            {
                "type" : "DSO", # We may need to add a type attribute to the drivers?
                "name" : "Keysight BLAH BLAH",  
                "serial" : "1234",
            }
    ]
}

"""


class TestClassImp(TestClass):
    """
    Minimum implementation of the Test class so that it can be used for parameter extraction from the
    actual implemented test classes
    """

    def test(self):
        pass


"""
The log schema is defined by the following dataclasses
"""


@dataclass
class InstrumentLog:
    """
    Log entry for the instruments
    """

    serial = ""


@dataclass
class TestLog:
    """
    Log of data for a test list
    """

    measurements: list[CheckResult] = Field(
        default_factory=list
    )  # Class to store all the checks that get done in the testList
    parent_test_list: str = ""  # The parent test list that the test belongs to
    test_name: str = ""  # The name of the test class
    description: str = ""  # The test description
    description_long: str = ""  # The test description
    test_index: str = ""
    outcome: str = ""
    args: list[str] = Field(default_factory=list)  # args
    start_time_millis: int = 0
    end_time_millis: int = 0


@dataclass
class LogFile:
    """
    Logfile for a test run
    """

    tests: list[TestLog] = Field(default_factory=list)
    instruments: list[InstrumentLog] = Field(default_factory=list)
    serial_number: str = ""
    outcome: str = ""
    start_time_millis: int = 0
    end_time_millis: int = 0
    part_number: int = ""
    module_name: int = ""


class JSONWriter:
    def __init__(self):
        self.log_queue = Queue()
        self.json_writer = None

        self.log_file_path = fixate.config.LOG_DIRECTORY

        self.log_path = ""
        self.exception = None

        self._topics = [
            (self.test_start, "Test_Start"),
            (self.test_comparison, "Check"),
            (self.test_exception, "Test_Exception"),
            (self.test_complete, "Test_Complete"),  # Finish up the log file here
            (self.sequence_update, "Sequence_Update"),
            (self.sequence_complete, "Sequence_Complete"),
            (self.user_wait_start, "UI_block_start"),
            (self.user_wait_end, "UI_block_end"),
            (self.driver_open, "driver_open"),  # Log the instruments here
        ]

        self.logFile = LogFile()

    def install(self):

        for callback, topic in self._topics:
            pub.subscribe(callback, topic)

    def uninstall(self):
        for callback, topic in self._topics:
            pub.unsubscribe(callback, topic)

    def ensure_alive(self):
        pass

    def sequence_update(self, status):
        logger.info("Sequence update")
        if status in ["Running"]:
            self.logFile.start_time_millis = time.perf_counter()
            # Get the module name and test name etc
            test_module = sys.modules["module.loaded_tests"]
            module_name = os.path.basename(test_module.__file__).split(".")[0]
            self.logFile.module_name = module_name
            logger.info(f"module = {module_name}")

            # Get the serial number
            serial = fixate.config.RESOURCES["SEQUENCER"].context_data["serial_number"]
            logger.info(f"serial = {serial}")
            self.logFile.serial_number = serial

            # The part number is not necessarily in the context data yet...

    def sequence_complete(
        self, status, passed, failed, error, skipped, sequence_status
    ):

        self.logFile.end_time_millis = time.perf_counter()
        self.logFile.outcome = status
        logger.info(f"stoptime = {self.logFile.end_time_millis}")
        self.save_file()

    def test_start(self, data, test_index):
        """
        :param data:
         the test class that is being started
        :param test_index:
         the test index in the sequencer
        """
        logger.info("Test Start")
        logger.info(data)
        logger.info(test_index)

        new_test_log = TestLog()
        new_test_log.description = data.test_desc
        new_test_log.description_long = data.test_desc_long
        new_test_log.start_time_millis = time.perf_counter()
        new_test_log.test_name = data.__class__.__name__
        new_test_log.test_index = test_index
        new_test_log.args = self.extract_test_parameters(data)
        self.logFile.tests.append(new_test_log)

    def test_exception(self, exception, test_index):
        logger.info("test exception")
        logger.info(exception)
        logger.info(test_index)

    def test_comparison(
        self, passes: bool, chk: CheckResult, chk_cnt: int, context: str
    ):
        logger.info("Test comparison")
        logger.info(f"passes {passes}")
        logger.info(f"results {chk}")
        logger.info(f"count {chk_cnt}")
        logger.info(f"context {context}")

        self.logFile.tests[-1].measurements.append(chk)

    def test_complete(self, data, test_index, status):
        logger.info("Test complete")
        logger.info(data)
        logger.info(test_index)
        logger.info(status)

        self.logFile.tests[-1].outcome = status
        self.logFile.tests[-1].end_time_millis = time.perf_counter()

    def user_wait_start(self, *args, **kwargs):
        pass

    def user_wait_end(self, *args, **kwargs):
        pass

    def driver_open(self, instr_type, identity):
        logger.info("Driver Open")
        logger.info(instr_type)
        logger.info(identity)

    @staticmethod
    def extract_test_parameters(test_cls):
        """
        :param test_cls:
         The class to extract parameters from
        :return:
         the keys and values in the form in alphabetical order on the parameter names and zipped as
         [(param_name, param_value)]
        """
        comp = TestClassImp()
        keys = sorted(set(test_cls.__dict__) - set(comp.__dict__))
        return [(key, test_cls.__dict__[key]) for key in keys]

    def save_file(self):
        """
        Dumps the logfile to a .json file
        """
        now = datetime.now()
        json_data = json.dumps(self.logFile, indent=4, default=pydantic_encoder)
        with open(
            os.path.join(
                self.log_file_path,
                "test_log_" + now.strftime("%Y%m%d_%H%M%S") + ".json",
            ),
            "w",
        ) as f:
            f.write(json_data)
