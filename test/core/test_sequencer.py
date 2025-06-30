import pytest
import fixate
from fixate.core.common import TestList, TestClass
from fixate.core.checks import chk_fails, chk_passes
from pubsub import pub


class TestSetupError(TestClass):
    def set_up(self):
        raise Exception("Something went wrong")


class TestTearDownError(TestClass):
    def tear_down(self):
        raise Exception("Something went wrong")


class TestPass(TestClass):
    def test(self):
        chk_passes("Passed check")


class TestFails(TestClass):
    def test(self):
        chk_fails("This test fails")


class TestError(TestClass):
    def test(self):
        raise Exception("Test error")


class TestListSetupError(TestList):
    def set_up(self):
        raise Exception("Test set up error")


class TestListTearDownError(TestList):
    def tear_down(self):
        raise Exception("Test tear down error")


class TestListEnterError(TestList):
    def enter(self):
        raise Exception("Test enter error")


class TestListExitError(TestList):
    def exit(self):
        raise Exception("Test exit error")


class FakeReportingService:
    """
    Fakes out the normal reporting service, so we dont generate logs
    and I don't care about testing this module in this context.
    """

    def install(self):
        return

    def uninstall(self):
        return

    def ensure_alive(self):
        return True


class PubSubSnooper:
    """
    Hooks into the pubsub module and logs test status updates
    """

    def __init__(self):
        # Subscribe to all the basic stuff that monitor the test execution
        pub.subscribe(self.snoop, pub.ALL_TOPICS)
        self.calls = []  # List to store all calls

    def snoop(self, topicObj=pub.AUTO_TOPIC, **msgData):
        self.calls.append(str(topicObj.getName()))


@pytest.fixture
def pubsub_logs():
    # Return a TestStatusHooks object to check for test sequence updates
    return PubSubSnooper()


@pytest.fixture
def sequencer():
    # Gets a sequencer object
    seq = fixate.sequencer.Sequencer()
    seq.reporting_service = FakeReportingService()
    seq.non_interactive = True
    fixate.config.RESOURCES["SEQUENCER"] = seq
    return fixate.config.RESOURCES["SEQUENCER"]


def test_load_test(sequencer):
    test_seq = TestList(seq=[TestPass(), TestPass()])
    sequencer.load(test_seq)


sequence_run_parameters = [
    [
        TestList(
            seq=[
                TestPass(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Check",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "PASSED",
    ],
    [
        TestList(
            seq=[
                TestFails(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Check",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestList(
            seq=[
                TestError(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Test_Exception",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestList(
            seq=[
                TestSetupError(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Test_Exception",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestList(
            seq=[
                TestTearDownError(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Test_Exception",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestListSetupError(
            seq=[
                TestPass(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Test_Exception",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestListTearDownError(
            seq=[
                TestPass(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Check",
            "Test_Exception",
            "Test_Retry",
            "Test_Complete",
            "TestList_Complete",
            "TestList_Complete",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "FAILED",
    ],
    [
        TestListEnterError(
            seq=[
                TestPass(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Exception",
            "Sequence_Abort",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "ERROR",
    ],
    [
        TestListExitError(
            seq=[
                TestPass(),
            ]
        ),
        [
            "Sequence_Update",
            "Sequence_Start",
            "TestList_Start",
            "Test_Start",
            "Check",
            "Test_Complete",
            "TestList_Complete",
            "Test_Exception",
            "Sequence_Abort",
            "Sequence_Update",
            "Sequence_Complete",
        ],
        "ERROR",
    ],
]


@pytest.mark.parametrize("test_seq,expected_calls, end_status", sequence_run_parameters)
def test_sequence_run(test_seq, expected_calls, end_status, sequencer, pubsub_logs):
    sequencer.load(test_seq)
    sequencer.run_sequence()

    assert expected_calls == pubsub_logs.calls
    assert end_status == sequencer.end_status


def test_reporting_service_error(sequencer, pubsub_logs):
    # Make the reporting service check function raise an error
    sequencer.reporting_service.ensure_alive = lambda: 1 / 0
    sequencer.load(
        TestList(
            seq=[
                TestPass(),
            ]
        )
    )
    sequencer.run_sequence()

    expected_calls = [
        "Sequence_Update",
        "Sequence_Start",
        "Test_Exception",
        "Sequence_Abort",
        "Sequence_Update",
        "Sequence_Complete",
    ]
    assert expected_calls == pubsub_logs.calls
    assert "ERROR" == sequencer.end_status
