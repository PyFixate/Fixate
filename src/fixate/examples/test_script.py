"""
This is a test script that shows basic use case for the fixate library
"""
from fixate.core.common import TestClass, TestList
from fixate.core.checks import *
from fixate.core.ui import *

__version__ = "3"


class RedButton(TestClass):
    """
    Asks the user to push the red button
    """

    test_desc = "Red Button"

    def test(self):
        user_ok("Please Push the Red Button\n")
        chk_passes("Red Button Pushed")


class ReturnTrue(TestClass):
    """
    Just passes and returns True
    """

    test_desc = "Return True"

    def test(self):
        chk_equal(True, True)


class ReturnFalse(TestClass):
    """
    Just fails and returns False
    """

    test_desc = "Fail False"
    skip_on_fail = True

    def test(self):
        chk_equal(False, True)


class RaiseValueError(TestClass):
    """
    Raises a value error before making a comparison
    """

    test_desc = "Raise Value Error"
    skip_exceptions = [ValueError]

    def test(self):
        raise ValueError("Things be broken")


class RaiseValueErrorInComparison(TestClass):
    """
    Comparison Value Error <- If test_desc not present than this is the test_desc
    Raises a value error during a comparison <- If test_desc not present than this is the test_desc_long
    """

    skip_exceptions = [TypeError]

    def test(self):
        chk_in_range("HI", 5, 10)


class GetUserInput(TestClass):
    """
    Raises a value error
    """

    test_desc = "Get Input from User"

    def enter(self):
        self.retry_type = self.RT_PROMPT

    def test(self):
        get_input = user_input("What is 1 + 1?\n")
        chk_equal(int(get_input), 2)


class MultiplePassedTestResults(TestClass):
    """
    This class has multiple test results
    """

    test_desc = "Multiple passed results"

    def test(self):
        chk_log_value("Result 1")
        chk_log_value("Result 2")

    def tear_down(self):
        user_info("Tearing down this function")


class MultipleTestResults(TestClass):
    """
    This class has multiple test results including passed, and failed in comparisons
    """

    test_desc = "Multiple testresults"
    skip_on_fail = True

    def test(self):
        chk_in_range(1, 0, 2)
        chk_in_range(1, 2, 3)
        chk_equal(1, 1)
        chk_equal(1, 2)
        chk_in_range(5, 0, 10)


class MultipleTestResultsTestException(TestClass):
    """
    This class has multiple test results including passed, failed and exceptions in comparisons
    """

    test_desc = "Multiple exception in main line test"
    skip_exceptions = [ZeroDivisionError, TypeError]

    def test(self):
        chk_in_range(1, 0, 2)
        chk_in_range(1, 2, 3)
        chk_equal(1, 1)
        chk_equal(1, 2)
        chk_in_range("hi", 0, 10)
        x = 1 / 0
        chk_in_range(5, 0, 10)


class ParameterisedTest(TestClass):
    """
    This class uses the init function to build a set of parameters used in the test function
    """

    test_desc = "Parameterised Test Function"
    class_param = "Class Param"
    class_param_override = "Override Me"

    def __init__(self, frequency, time, **kwargs):
        super().__init__(**kwargs)
        self.frequency = frequency
        self.time = time
        self.class_param_override = "Overridden"

    def test(self):
        chk_equal(
            self.class_param_override,
            "Overridden",
            description="Checking that parameter is overridden",
        )
        chk_equal(self.class_param, "Class Param")
        chk_log_value(
            "Frequency {}".format(self.frequency),
            description="Just outputting the frequency",
        )
        chk_log_value("Time {}".format(self.time))
        user_info("This won't be in the report")
        chk_passes("This will be in the report")


class MultipleLeveled(TestClass):
    """
    This class also execute tests in the self.sub_tests
    """

    test_desc = "Multi Levelled Test Function"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sub_tests = [ReturnTrue(), ReturnFalse()]

    def test(self):
        user_info("Test")


SHOULD_I_PASS = False


class PassEverySecondAttempt(TestClass):
    """
    Only passes if the global is True
    """

    retry_on_fail = True
    attempts = 5

    def test(self):
        chk_equal(SHOULD_I_PASS, True, description="Checking state of SHOULD_I_PASS")

    def tear_down(self):
        global SHOULD_I_PASS
        SHOULD_I_PASS = not SHOULD_I_PASS


class PassEverySecondAttemptThrowOthers(PassEverySecondAttempt):
    """
    Only passes if the global is True
    Throws Exceptions other times
    """

    retry_exceptions = [Exception]

    def test(self):
        chk_equal(SHOULD_I_PASS, True, description="Checking state of SHOULD_I_PASS")
        if not SHOULD_I_PASS:
            raise Exception("This should throw exception if SHOULD_I_PASS is False")


class MultipleLeveledSubTestFails(TestClass):
    """
    This class also execute tests in the self.sub_tests
    """

    test_desc = "Multi Levelled Test Function with fail retries"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sub_tests = [PassEverySecondAttempt(), PassEverySecondAttemptThrowOthers()]

    def test(self):
        chk_passes()


class MultipleLeveledSubTestFailsRetryOnTopLevel(TestClass):
    """
    This class also execute tests in the self.sub_tests
    """

    test_desc = "Multi Levelled Test Function with fail retries"
    attempts = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        mod = PassEverySecondAttemptThrowOthers()
        self.retry_exceptions = mod.retry_exceptions
        mod.retry_exceptions = []
        self.sub_tests = [PassEverySecondAttempt(), mod]

    def test(self):
        chk_passes()


class MultipleLineInstruction(TestClass):
    """
    Multiple line instruction
    """

    def test(self):
        user_info("Line 1")
        user_info("Line 2")
        user_info("Line 3")
        user_info("Line 4")
        user_ok("Line 5")


class PostSequenceInfo(TestClass):
    def test(self):
        user_post_sequence_info("Post sequence info is here and should always be here")
        user_post_sequence_info_pass(
            "Post sequence info that should only show if sequence passes"
        )
        user_post_sequence_info_fail(
            "Post sequence info that should only show if sequence fails"
        )


class CheckPostSequenceInfo(TestClass):
    def test(self):
        user_info(
            "When the sequence finishes, check the following in the active and history window:"
        )
        user_info("Post sequence info is here and should always be here")
        user_ok(
            "Post sequence info that should only show if sequence x where x is passes or fails"
        )


PASSES = [
    PostSequenceInfo(),
    CheckPostSequenceInfo(),
    ReturnTrue(),
    ReturnFalse(skip=True),
    RaiseValueError(skip=True),
    RaiseValueErrorInComparison(skip=True),
    RedButton(),
    GetUserInput(),
    MultiplePassedTestResults(),
    MultipleTestResults(skip=True),
    MultipleTestResultsTestException(skip=True),
    ReturnTrue(),
    ParameterisedTest(50, 500),
    ReturnTrue(),
    ParameterisedTest(10, 5),
    MultipleLineInstruction(),
    CheckPostSequenceInfo(),
]
FAILS = [
    PostSequenceInfo(),
    CheckPostSequenceInfo(),
    ReturnTrue(),
    ReturnFalse(),
    RaiseValueError(skip=True),
    RaiseValueErrorInComparison(skip=True),
    RedButton(),
    GetUserInput(),
    MultiplePassedTestResults(),
    MultipleTestResults(),
    MultipleTestResultsTestException(skip=True),
    ReturnTrue(),
    ParameterisedTest(50, 500),
    ReturnTrue(),
    ParameterisedTest(10, 5),
    MultipleLineInstruction(),
    CheckPostSequenceInfo(),
]
ERRORS = [
    PostSequenceInfo(),
    CheckPostSequenceInfo(),
    ReturnTrue(),
    ReturnFalse(),
    RaiseValueError(),
    RaiseValueErrorInComparison(),
    RedButton(),
    GetUserInput(),
    MultiplePassedTestResults(),
    MultipleTestResults(),
    MultipleTestResultsTestException(),
    ReturnTrue(),
    ParameterisedTest(50, 500),
    ReturnTrue(),
    ParameterisedTest(10, 5),
    MultipleLineInstruction(),
    CheckPostSequenceInfo(),
]

TEST_SEQUENCE = PASSES

test_data = {"default": PASSES, "passes": PASSES, "fails": FAILS, "ERRORS": ERRORS}
