"""
Testing the RetryMode implementation.
"""

from fixate.core.checks import chk_true
from fixate.core.common import TestClass, TestList
from fixate.core.ui import user_info, user_ok


class SimpleTestToPass(TestClass):
    """Simple test case that always passes"""

    test_desc = __qualname__

    def set_up(self):
        user_info("Setting up to pass")

    def test(self):
        user_info("Testing to Pass the test")
        chk_true(True, "Passed the test")

    def tear_down(self):
        user_info("Well done, you wouldn't fail anyway!")


class SimpleTestToFail(TestClass):
    """Simple test case that always fails"""

    test_desc = __qualname__
    attempts = 2
    retry_type = TestClass.RetryMode.RT_PROMPT

    def set_up(self):
        user_info("Setting up to fail")

    def test(self):
        user_info("Testing to Fail the test")
        chk_true(False, "Failed the test")

    def tear_down(self):
        user_info("Well, you wouldn't pass anyway!")


class RetryTestPass(TestClass):
    """Simple test case that always passes but setup to retry if fails to test passing cases."""

    test_desc = __qualname__
    retry_type = TestClass.RetryMode.RT_RETRY
    attempts = 3

    def set_up(self):
        user_info("Setting up to pass")

    def test(self):
        user_info("Testing to Pass the test")
        chk_true(True, "Passed the test")

    def tear_down(self):
        user_info("Well done, you wouldn't fail anyway!")


class RetryTestFail(TestClass):
    """Simple test case that always fails and retries for the number of
    attempts and prompts the user after all the attempts have failed..
    """

    test_desc = __qualname__

    retry_type = TestClass.RetryMode.RT_RETRY
    attempts = 3

    def set_up(self):
        user_info("Setting up to fail")

    def test(self):
        user_info("Testing to Fail the test")
        chk_true(False, "Failed the test")

    def tear_down(self):
        user_info("Well, you wouldn't pass anyway!")


# RT_FAIL = 4  # Automatically fail and move on
class RetryTestPassRTFAIL(TestClass):
    """Simple test case that always passes but setup to retry if fails to test passing cases."""

    test_desc = __qualname__

    retry_type = TestClass.RetryMode.RT_FAIL
    attempts = 3

    def set_up(self):
        user_info("Setting up to pass")

    def test(self):
        user_info("Testing to Pass the test")
        chk_true(True, "Passed the test")

    def tear_down(self):
        user_info("Well done, you wouldn't fail anyway!")


class RetryTestFailRTFAIL(TestClass):
    """Simple test case that always fails and retries for the number of
    attempts. Then automatically failes the test and moves onto the next one."""

    test_desc = __qualname__

    retry_type = TestClass.RetryMode.RT_FAIL
    attempts = 3

    def set_up(self):
        user_info("Setting up to fail")

    def test(self):
        user_info("Testing to Fail the test")
        chk_true(False, "Failed the test")

    def tear_down(self):
        user_info("Well, you wouldn't pass anyway!")


class TestListRTFAIL(TestList):
    """Test list to test the RT_FAIL within the test list"""

    def enter(self):
        user_info("Entering the test list")

    def exit(self):
        user_info("Leaving the test list")


# RT_ABORT = 1  # Abort the whole test sequence
class RetryTestFailRTABORT(TestClass):
    """Simple test case that always fails and retries the number of attempts when final attempt has failed
    It aborts the all the test. It may be useful if there is critical test that may damage Device Under Test if fails.
    """

    test_desc = __qualname__

    retry_type = TestClass.RetryMode.RT_ABORT
    attempts = 3

    def set_up(self):
        user_ok("Setting up to abort, Press Enter to proceed")

    def test(self):
        user_info("Testing to Fail the test")
        chk_true(False, "Failed the test")

    def tear_down(self):
        user_info("ABORTING!")


TEST_SEQUENCE = [
    SimpleTestToPass(),
    SimpleTestToFail(),
    RetryTestPass(),
    RetryTestFail(),
    RetryTestPassRTFAIL(),
    RetryTestFailRTFAIL(),
    TestListRTFAIL(
        [
            RetryTestPassRTFAIL(),
            RetryTestFailRTFAIL(),
        ]
    ),
    RetryTestFailRTABORT(),
]

if __name__ == "__main__":
    import fixate

    argv = ["-p", __file__, "--serial_number", "1234567890"]
    fixate.run(__file__, argv)
