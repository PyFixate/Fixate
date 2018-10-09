"""
CSV Definitions
REPORT_FORMAT_VERSION = 3
Several parameters are now configure from fixate.config which can be set via -c command or defaults.
REPORT_FORMAT_VERSION: Now user configurable as the parameters can change the format of the file
tpl_time_stamp: How is the time stamp used for start and end time. Default "{0:%Y}{0:%m}{0:%d}-{0:%H}{0:%M}{0:%S}"
tpl_csv_path:

plugins = {
    "fixate.reporting.csv": {
        "REPORT_FORMAT_VERSION": 3,
        "tpl_time_stamp": "{0:%Y}{0:%m}{0:%d}-{0:%H}{0:%M}{0:%S}",
        "tpl_csv_path": ["{fixate.config.plugins[fixate.reporting.csv][tpl_time_stamp]}"
                              "-{index}.csv"],
        "tpl_first_line": [
            "0",
            'Sequence',
            "started={start_date_time}",
            "fixate-version={fixate_version}",
            "test-script-name={test_script_name}",
            "test_script-version={test_script_version}",
            "report-format={REPORT_FORMAT_VERSION}",
            "serial_number={serial_number}",
            "index_string={index_string}"]
First Line
tpl_first_line

Last Line
<Time Elapsed (s)>,Sequence,ended=tmp_time_stamp,tests-passed=<passed>,
tests-failed=<failed>,tests-error=<error>,tests-skipped=<skipped>,sequence=<FINISHED ABORTED>

Test Start
<Time Elapsed (s)>,Test <index>,start,<test_desc>,<test_desc_long>

Test Parameters
<Time Elapsed (s)>,test-parmaeters,<param_name>=<param_value> ... <param_name>=<param_value>

Check Function
<Time Elapsed (s)>,Test <index>,check<index>,<check type>,<description>,<PASS FAIL>,... //Defaults for others extend
... For in_range*, outside_range*,
<test_val>,<_min>,<_max>
... For equal, *_or_equal, log_value, smaller, greater
<test_val>,<nominal>
... For in_tolerance
<test_val>,<nominal>,<tol>
... For passes, fails no more fields

Check Exception
<Time Elapsed (s)>,Test <index>,check<index>,exception,<exception_message>

Test End
<Time Elapsed (s)>,Test <index>,end,<PASS FAIL ERROR>,checks-passed=<passed>,checks-failed<failed>,checks-error=<errors>

REPORT_FORMAT_VERSION = 2

First Line
<Time Elapsed (s)>,Sequence,started=<YYYYMMDD-hhmmss>,fixate-version=<version>,test-script-name=<script>,
test_script-version=<script.__version__,report-format=<csv.REPORT_FORMAT_VERSION>, part_number=<part_number>,
module=<module>, serial_number=<serial_number>

Last Line
<Time Elapsed (s)>,Sequence,ended=<YYYYMMDD - hhmmss>,<FAILED ABORTED PASSED>,tests-passed=<passed>,
tests-failed=<failed>,tests-error=<error>,tests-skipped=<skipped>,sequence=<FINISHED ABORTED>

Test Start
<Time Elapsed (s)>,Test <index>,start,<test_desc>,<test_desc_long>

Test Parameters
<Time Elapsed (s)>,test-parmaeters,<param_name>=<param_value> ... <param_name>=<param_value>

Check Function
<Time Elapsed (s)>,Test <index>,check<index>,<check type>,<description>,<PASS FAIL>,... //Defaults for others extend
... For in_range*, outside_range*,
<test_val>,<_min>,<_max>
... For equal, *_or_equal, log_value, smaller, greater
<test_val>,<nominal>
... For in_tolerance
<test_val>,<nominal>,<tol>
... For passes, fails no more fields

Check Exception
<Time Elapsed (s)>,Test <index>,check<index>,exception,<exception_message>

Test End
<Time Elapsed (s)>,Test <index>,end,<PASS FAIL ERROR>,checks-passed=<passed>,checks-failed<failed>,checks-error=<errors>
"""
import csv
import datetime
import sys
import os
import time

from pubsub import pub

from queue import Queue
from fixate.core.common import TestClass
from fixate.core.common import ExcThread
import fixate
import fixate.config


class TestClassImp(TestClass):
    """
    Minimum implementation of the Test class so that it can be used for parameter extraction from the
    actual implemented test classes
    """

    def test(self):
        pass


class CSVWriter:
    def __init__(self, ):
        self.csv_queue = Queue()
        self.csv_writer = None
        # data = fixate.config.get_config_dict()
        # data.update(fixate.config.get_plugin_data('plg_csv'))
        # self.csv_dir = os.path.join(*fixate.config.render_template(data["tpl_csv_path"], **data,
        #                                                            **fixate.config.RESOURCES["SEQUENCER"].context_data))
        self.reporting = CsvReporting()

    def install(self):
        self.csv_writer = ExcThread(target=self._csv_write,
                                    args=(self.csv_queue,))
        self.csv_writer.start()

    def uninstall(self):
        if self.csv_writer:
            self.csv_queue.put(None)
            self.csv_writer.stop()
            self.csv_writer.join()
        self.csv_writer = None

    def _csv_write(self, cmd_q):
        while True:
            line = cmd_q.get()
            if line is None:
                break  # Command send to close csv_writer
            try:
                os.makedirs(os.path.dirname(self.reporting.csv_path))
            except OSError as e:
                pass
            with open(self.reporting.csv_path, 'a+', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(line)


class CsvReporting:
    def __init__(self):
        self.exception_in_test = False
        self.failed = False
        self.chk_cnt = 0
        self.csv_path = ''
        self.test_module = None
        self.start_time = None
        self.current_test = None
        self.data = fixate.config.get_config_dict()
        self.data.update(fixate.config.get_plugin_data('plg_csv'))

    def sequence_update(self, status):
        # Do Start Sequence Reporting
        if status in ["Running"]:
            sequencer = fixate.config.RESOURCES["SEQUENCER"]
            self.data.update(sequencer.context_data)
            # Create new csv path
            self.data["start_date_time"] = self.data["tpl_time_stamp"].format(datetime.datetime.now())
            self.test_module = sys.modules["module.loaded_tests"]
            if fixate.config.log_file:
                self.csv_path = fixate.config.log_file
            else:
                self.csv_path = os.path.join(
                    *fixate.config.render_template(self.data["tpl_csv_path"], **self.data, self=self))
            self.data["fixate_version"] = fixate.__version__
            # Add dev if installed in editable mode
            if 'site-packages' not in __file__:
                self.data["fixate_version"] += 'dev'
            self.data["test_script_name"] = os.path.basename(self.test_module.__file__).split('.')[0]
            self.data.update(sequencer.context_data)
            self.start_time = time.clock()
            self._write_line_to_csv(fixate.config.render_template(self.data["tpl_first_line"], **self.data, self=self))

    def sequence_complete(self, status, passed, failed, error, skipped, sequence_status):
        self._write_line_to_csv(["{:.2f}".format(time.clock() - self.start_time),
                                 'Sequence',
                                 "ended={}".format(self.data["tpl_time_stamp"].format(datetime.datetime.now())),
                                 sequence_status,
                                 "tests-passed={}".format(passed),
                                 "tests-failed={}".format(failed),
                                 "tests-error={}".format(error),
                                 "tests-skipped={}".format(skipped),
                                 "sequence={}".format(status.upper())])
        # Close out the reporting
        self.test_module = None

    def test_start(self, data, test_index):
        """
        :param data:
         the test class that is being started
        :param test_index:
         the test index in the sequencer
        """
        # Add a test record for this result that is overridden if the test is repeated
        # [0, 0, 0] -> Passed, Failed, Exception
        # Test <test_index>, start, <test name>
        self._write_line_to_csv(["{:.2f}".format(time.clock() - self.start_time),
                                 'Test {}'.format(test_index), 'start', data.test_desc, data.test_desc_long])

        test_params = self.extract_test_parameters(data)
        self.current_test = test_index
        if len(test_params):
            # Test <test_index>, test-parameters, <param_name>=<param_value>, ...
            param_line = ["{:.2f}".format(time.clock() - self.start_time),
                          'Test {}'.format(test_index), 'test-parameters']
            for param_name, param_value in test_params:
                param_line.append('{}={}'.format(param_name, param_value))
            self._write_line_to_csv(param_line)

    def test_exception(self, exception, test_index):
        self.current_test = test_index
        exc_line = ["{:.2f}".format(time.clock() - self.start_time),
                    'Test {}'.format(test_index),
                    'exception',
                    repr(exception)]
        self._write_line_to_csv(exc_line)

    def test_comparison(self, passes, chk, chk_cnt, context):
        # pub.sendMessage("Check", passes=result, chk=chk, context=self.get_context())
        if passes:
            status = "PASS"
        else:
            status = "FAIL"
        # Test <test_index>, check<number>, <check type>, <status>, <test_val>, <expected>
        # If exception <test_index>, check<number>, <exception details>
        chk_line = ["{:.2f}".format(time.clock() - self.start_time),
                    'Test {}'.format(context),
                    'check{}'.format(chk_cnt),
                    chk.target.__name__[1:].replace('check_', '').replace('_', ' '),
                    chk.description, status, chk.test_val]
        chk_line.extend([x for x in [chk.nominal, chk._min, chk._max, chk.tol] if x is not None])

        self._write_line_to_csv(chk_line)
        self.chk_cnt += 1

    def test_complete(self, data, test_index, status):
        self.current_test = test_index
        try:
            sequencer = fixate.config.RESOURCES["SEQUENCER"]
            passed = sequencer.chk_pass
            failed = sequencer.chk_fail

            self._write_line_to_csv(["{:.2f}".format(time.clock() - self.start_time),
                                     'Test {}'.format(test_index),
                                     'end',
                                     status,
                                     'checks-passed={}'.format(passed),
                                     'checks-failed={}'.format(failed)])
        finally:
            self.chk_cnt = 0

    def user_wait_start(self, *args, **kwargs):
        self._write_line_to_csv(["{:.2f}".format(time.clock() - self.start_time),
                                 'Test {}'.format(self.current_test),
                                 'user_wait_start'])

    def user_wait_end(self, *args, **kwargs):
        self._write_line_to_csv(["{:.2f}".format(time.clock() - self.start_time),
                                 'Test {}'.format(self.current_test),
                                 'user_wait_end'])

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

    def _write_line_to_csv(self, line):
        """
        :param line:
         single line of data with each column as an element in the list
        :return:
        """
        global writer
        writer.csv_queue.put(line)
        # try:
        #     os.makedirs(self.csv_dir)
        # except OSError:
        #     pass
        # with open(self.csv_path, 'a+', newline='') as f:
        #     writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        #     writer.writerow(line)


writer = None


def register_csv():
    """
    :param csv_dir: Base directory for for csv file
    :param args: Args as parsed into the command line interface
    :return:
    """
    global writer
    writer = CSVWriter()
    writer.install()
    pub.subscribe(writer.reporting.test_start, 'Test_Start')
    pub.subscribe(writer.reporting.test_comparison, 'Check')
    pub.subscribe(writer.reporting.test_exception, "Test_Exception")
    pub.subscribe(writer.reporting.test_complete, "Test_Complete")
    pub.subscribe(writer.reporting.sequence_update, "Sequence_Update")
    pub.subscribe(writer.reporting.sequence_complete, "Sequence_Complete")
    pub.subscribe(writer.reporting.user_wait_start, "UI_block_start")
    pub.subscribe(writer.reporting.user_wait_end, "UI_block_end")


def unregister_csv():
    """
    Note, will disable the final result eg. Unit Passed
    :return:
    """
    global writer
    pub.unsubscribe(writer.reporting.test_start, 'Test_Start')
    pub.unsubscribe(writer.reporting.test_comparison, 'Check')
    pub.unsubscribe(writer.reporting.test_exception, "Test_Exception")
    pub.unsubscribe(writer.reporting.test_complete, "Test_Complete")
    pub.unsubscribe(writer.reporting.sequence_update, "Sequence_Update")
    pub.unsubscribe(writer.reporting.sequence_complete, "Sequence_Complete")
    pub.unsubscribe(writer.reporting.user_wait_start, "UI_block_start")
    pub.unsubscribe(writer.reporting.user_wait_end, "UI_block_end")
    writer.uninstall()
