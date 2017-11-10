import asyncio
import sys
import time
import re
from pubsub import pub
from fixate.core.common import TestList, TestClass
from fixate.core.exceptions import SequenceAbort, TestRetryExceeded, CheckFail
from fixate.core.ui import user_retry_abort_fail

STATUS_STATES = ["Idle", "Running", "Paused", "Finished", "Restart", "Aborted"]
TARGET_RETURN_STATES = ["Skipped", "Result", "Exception"]


def default_retry(*args, **kwargs):
    return "RETRY"


class ContextStackNode:
    def __init__(self, seq):
        self.index = 0
        if isinstance(seq, TestList):
            self.testlist = seq
        elif isinstance(seq, list):
            self.testlist = TestList(seq)

    def current(self):
        next_item = self.testlist[self.index]
        if not isinstance(next_item, TestList) and isinstance(next_item, list):
            # Convert a normal list into a TestList
            self.testlist[self.index] = TestList(next_item)
            next_item = self.testlist[self.index]
        return next_item


class ContextStack(list):
    def push(self, test):
        self.append(ContextStackNode(test))

    def top(self):
        return self[-1]


def test_list_repr(test_list):
    def levels_repr():
        return ".".join(str(x.index + 1) for x in context[1:])

    def curr_test_name():
        return top.current().test_desc

    def curr_test_skip():
        if isinstance(top.current(), TestList):
            return False
        return top.current().skip

    context = ContextStack()
    context.push(test_list)
    ret_list = []

    while context:
        top = context.top()
        if top.index >= len(top.testlist):  # Finished tests in the test list
            context.pop()
            if context:
                context.top().index += 1
        elif isinstance(top.current(), TestClass):
            ret_list.append({"level": levels_repr(), "test_name": curr_test_name(), "test_type": "test",
                             "test_skip": curr_test_skip(),
                             "parent": get_parent_level(levels_repr())})
            top.index += 1
        elif isinstance(top.current(), TestList):
            ret_list.append(
                {"level": levels_repr(), "test_name": curr_test_name(), "test_type": 'list',
                 "test_skip": curr_test_skip(),
                 "parent": get_parent_level(levels_repr())})
            context.push(top.current())
    return ret_list


def get_parent_level(level):
    m = re.match(r'^\d+$', level)

    if m:
        return 'Top'
    else:
        level = re.sub(r'\.\d+$', '', level)
        return level


class Sequencer:
    def __init__(self):
        self.tests = TestList()
        self._status = "Idle"
        self.active_test = None
        # pub.subscribe(self._handle_sequence_abort, "Seq_Abort")
        self.test_attempts = 0
        self.chk_fail = 0
        self.chk_pass = 0
        self.tests_failed = 0
        self.tests_passed = 0
        self.tests_errored = 0
        self.tests_skipped = 0
        self._skip_tests = set([])
        self.context = ContextStack()
        self.context_data = {}
        self.loop = asyncio.get_event_loop()
        self.retry_type = TestClass.RT_RETRY
        # self.retry_type = TestClass.RT_PROMPT

    def levels(self):
        """
        Get the current test context from the stack
        :return:
        """
        # Load now pushes whole test list as opposed to extending
        return ".".join(str(x.index + 1) for x in self.context[1:])

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        if val not in STATUS_STATES:
            raise ValueError("Invalid Sequencer Status")
        # Only if a change in status
        if val != self._status:
            pub.sendMessage('Sequence_Update', status=val)
            if self._status not in ["Paused"] and val in ["Running"]:
                pub.sendMessage('Sequence_Start')
            if val == "Restart":
                self._status = "Running"
                pub.sendMessage('Sequence_Update', status="Running")
            elif val in ["Aborted", "Finished"]:
                self._status = val
                if self.tests_errored or val == "Aborted":
                    end_status = "ERROR"
                elif self.tests_failed:
                    end_status = "FAILED"
                else:
                    end_status = "PASSED"
                # This notifies other sections on the final
                pub.sendMessage('Sequence_Complete', status=end_status, passed=self.tests_passed,
                                failed=self.tests_failed, error=self.tests_errored, skipped=self.tests_skipped,
                                sequence_status=self._status)
            else:
                self._status = val

    def load(self, val):
        self.context_data.clear()
        self.tests.append(val)
        self.context.push(self.tests)

    def clear_tests(self):
        if self.status == "Running":
            raise RuntimeError("Cannot clear tests while running")
        self.tests[:] = []
        self.context[:] = []
        self.context_data.clear()

    def run_sequence(self):
        """
        Runs the sequence from the beginning to end once
        :return:
        """
        self.status = "Running"
        try:
            self.run_once()
        finally:
            while self.context:
                top = self.context.top()
                if isinstance(top.current(), TestList):
                    top.current().exit()
                self.context.pop()

    def run_once(self):
        """
        Runs through the tests once as are pushed onto the context stack.
        Ie. One run through of the tests
        Once finished sets the status to Finished
        """
        while self.context:
            if self.status == "Running":
                try:
                    top = self.context.top()
                    if top.index >= len(top.testlist):  # Finished tests in the test list
                        self.context.pop()
                        pub.sendMessage("TestList_Complete", data=top.testlist, test_index=self.levels())
                        top.testlist.exit()
                        if self.context:
                            self.context.top().index += 1
                    elif isinstance(top.current(), TestClass):
                        if self.run_test():
                            top.index += 1
                        else:
                            if not self.retry_test(TestClass.RT_PROMPT):
                                self.tests_failed += 1
                                top.index += 1
                    elif isinstance(top.current(), TestList):
                        pub.sendMessage("TestList_Start", data=top.current(), test_index=self.levels())
                        top.current().enter()
                        self.context.push(top.current())
                    else:
                        raise SequenceAbort("Unknown Test Item Type")
                except BaseException as e:
                    pub.sendMessage("Test_Exception", exception=sys.exc_info()[1], test_index=self.levels())
                    pub.sendMessage("Sequence_Abort", exception=e)
                    self._handle_sequence_abort()
                    return
            else:
                time.sleep(0.1)
        self.status = "Finished"

    def run_test(self):
        """
        Runs the active test in the stack.
        Should only be called if the top of the stack is a TestClass
        :return: True if test passed, False if test failed or had an exception
        """

        active_test = self.context.top().current()
        active_test_status = "PENDING"
        pub.sendMessage("Test_Start", data=active_test, test_index=self.levels())
        if active_test.skip:
            self.tests_skipped += 1
            active_test_status = "SKIP"
            pub.sendMessage("Test_Skip", data=active_test, test_index=self.levels())
            pub.sendMessage("Test_Complete", data=active_test, test_index=self.levels(), status=active_test_status)
            return True

        attempts = 0
        abort_exceptions = [SequenceAbort, KeyboardInterrupt]
        abort_exceptions.extend(active_test.abort_exceptions)
        while True:
            attempts += 1
            # Retry exceeded test only when user is not involved in retry process
            try:
                if attempts > active_test.attempts and attempts != -1:
                    break
                self.chk_fail, self.chk_pass = 0, 0
                # Run the test
                try:
                    for index_context, current_level in enumerate(self.context):
                        current_level.current().set_up()
                    active_test.test()
                finally:
                    for current_level in self.context[index_context::-1]:
                        current_level.current().tear_down()
                if not self.chk_fail:
                    active_test_status = "PASS"
                    self.tests_passed += 1
                else:
                    active_test_status = "FAIL"
                    self.tests_failed += 1
                break
            except CheckFail:
                # Retry Logic for failed checks
                active_test_status = "FAIL"
                if not self.retry_test(TestClass.RT_RETRY):
                    # Retry handle set to skip the test
                    self.tests_failed += 1
                    break
            except tuple(abort_exceptions):
                pub.sendMessage("Test_Exception", exception=sys.exc_info()[1], test_index=self.levels())
                attempts = 0
                active_test_status = "ERROR"
                if not self.retry_test(TestClass.RT_PROMPT):
                    self.tests_errored += 1
                    break
            # Retry logic for exceptions
            except BaseException as e:
                pub.sendMessage("Test_Exception", exception=sys.exc_info()[1], test_index=self.levels())
                # Retry handle selected to skip the test.
                # Should be depreciated as test class shouldn't set sequencer behaviour
                active_test_status = "ERROR"
                if not self.retry_test(TestClass.RT_RETRY, prompt_message=repr(e)):
                    self.tests_errored += 1
                    break
            # Retry Logic
            pub.sendMessage("Test_Retry", data=active_test, test_index=self.levels())
        pub.sendMessage("Test_Complete", data=active_test, test_index=self.levels(), status=active_test_status)
        return active_test_status == "PASS"

    def retry_test(self, retry_type=None, prompt_message=""):
        if self.retry_type == TestClass.RT_ABORT or retry_type == TestClass.RT_ABORT:
            raise SequenceAbort("Sequence Aborted Automatically")
        elif self.retry_type == TestClass.RT_FAIL or retry_type == TestClass.RT_FAIL:
            return False
        elif retry_type == TestClass.RT_RETRY:
            return True
        elif retry_type == TestClass.RT_PROMPT:
            print(prompt_message)
            status, resp = user_retry_abort_fail(prompt_message)  # TODO Fix me
            if resp == "ABORT":
                raise SequenceAbort("Sequence Aborted By User")
            else:
                return resp == "RETRY"

    def _handle_sequence_abort(self):
        self.status = "Aborted"
        self.ABORT = True
        self.test_running = False

    def skip_test(self, index):
        try:
            self._skip_tests.update(index)
        except TypeError:
            self._skip_tests.add(index)

    def _restart(self):
        """
        Clear the stack and reset test_index to 0
        :return:
        """
        if self.status == "Running":
            raise RuntimeError("Cannot Restart if tests are still running")
        self.test_index = 0
        self.chk_fail = 0
        self.chk_pass = 0
        self.tests_failed = 0
        self.tests_passed = 0
        self.tests_errored = 0
        self.tests_skipped = 0
        self.status = "Restart"
        self.context[:] = []
        self.context.push(self.tests)
        self.context_data.clear()

    def check(self, chk, result):
        if result:
            self.chk_pass += 1
        else:
            self.chk_fail += 1
        pub.sendMessage("Check", passes=result, chk=chk,
                        chk_cnt=self.chk_pass + self.chk_fail, context=self.levels())
        if not result:
            raise CheckFail("Check function returned failure, aborting test")
        return result
