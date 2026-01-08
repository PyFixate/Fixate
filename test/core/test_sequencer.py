import pytest
import fixate
from fixate.core.common import TestList, TestClass
from fixate.core.checks import chk_fails, chk_passes
from pubsub import pub
from unittest.mock import MagicMock, call, patch


class MockTest(TestClass):
    """
    Test class that allows tracing of function calls
    """

    def __init__(self, num, mock_obj):
        super().__init__()
        self.mock = mock_obj
        self.num = num

    def set_up(self):
        self.mock.test_setup(self.num)

    def tear_down(self):
        self.mock.test_tear_down(self.num)

    def test(self):
        self.mock.test_test(self.num)


class MockTestList(TestList):
    """
    Test list that allows tracing of function calls
    """

    def __init__(self, seq, num, mock_obj):
        super().__init__(seq)
        self.mock = mock_obj
        self.num = num

    def set_up(self):
        self.mock.list_setup(self.num)

    def tear_down(self):
        self.mock.list_tear_down(self.num)

    def enter(self):
        self.mock.list_enter(self.num)

    def exit(self):
        self.mock.list_exit(self.num)


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


def abort_on_prompt(msg, q, choices=None, target=None, attempts=5, kwargs=None):
    q.put(("Result", "ABORT"))


def fail_on_prompt(msg, q, choices=None, target=None, attempts=5, kwargs=None):
    q.put(("Result", "FAIL"))


@pytest.fixture
def sequencer():
    # Gets a sequencer object
    seq = fixate.sequencer.Sequencer()
    seq.reporting_service = FakeReportingService()

    # Make the test fail by default:
    pub.subscribe(fail_on_prompt, "UI_req_choices")

    # Remove any latent subscription to the abort function:
    pub.unsubscribe(abort_on_prompt, "UI_req_choices")

    fixate.config.RESOURCES["SEQUENCER"] = seq
    return fixate.config.RESOURCES["SEQUENCER"]


@pytest.fixture
def mock_obj():
    return MagicMock()


def test_test_error(sequencer, mock_obj):
    with patch.object(MockTest, "test", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                call.test_setup(2),
                # No call.test_test(1) as this now raises an exception
                call.test_tear_down(2),
                call.list_tear_down(1),
                call.list_exit(1),
            ]
        )
    assert "FAILED" == sequencer.end_status


def test_test_setup_error(sequencer, mock_obj):
    with patch.object(MockTest, "set_up", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                # Hit error here in setup()
                # Skip test_test()
                call.test_tear_down(2),
                call.list_tear_down(1),
                call.list_exit(1),
            ]
        )

    assert "FAILED" == sequencer.end_status


def test_test_tear_down_error(sequencer, mock_obj):
    with patch.object(MockTest, "tear_down", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                call.test_setup(2),
                call.test_test(2),
                # Hit error in tear down here
                # No list tear down runs
                call.list_exit(1),
            ]
        )
    assert "FAILED" == sequencer.end_status


def test_list_setup_error(sequencer, mock_obj):
    with patch.object(MockTestList, "set_up", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [call.list_enter(1), call.list_tear_down(1), call.list_exit(1)]
        )

    assert "FAILED" == sequencer.end_status


def test_list_tear_down_error(sequencer, mock_obj):
    with patch.object(MockTestList, "tear_down", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                call.test_setup(2),
                call.test_test(2),
                call.test_tear_down(2),
                # List tear down raises error
                call.list_exit(1),
            ]
        )
    assert "FAILED" == sequencer.end_status


def test_list_enter_error(sequencer, mock_obj):
    with patch.object(MockTestList, "enter", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls([call.list_exit(1)])
    assert "ERROR" == sequencer.end_status


def test_list_exit_error(sequencer, mock_obj):
    with patch.object(MockTestList, "exit", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                call.test_setup(2),
                call.test_test(2),
                call.test_tear_down(2),
                call.list_tear_down(1),
            ]
        )
    assert "ERROR" == sequencer.end_status


def test_sequence_pass(sequencer, mock_obj):
    test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

    sequencer.load(test_seq)
    sequencer.run_sequence()

    mock_obj.assert_has_calls(
        [
            call.list_enter(1),
            call.list_setup(1),
            call.test_setup(2),
            call.test_test(2),
            call.test_tear_down(2),
            call.list_tear_down(1),
            call.list_exit(1),
        ]
    )
    assert "PASSED" == sequencer.end_status


def test_nested_sequence(sequencer, mock_obj):
    test_seq = MockTestList(
        [
            MockTest(2, mock_obj),
            MockTestList([MockTest(3, mock_obj), MockTest(4, mock_obj)], 5, mock_obj),
        ],
        1,
        mock_obj,
    )

    sequencer.load(test_seq)
    sequencer.run_sequence()

    mock_obj.assert_has_calls(
        [
            call.list_enter(1),
            call.list_setup(1),
            call.test_setup(2),
            call.test_test(2),
            call.test_tear_down(2),
            call.list_tear_down(1),
            call.list_enter(5),
            call.list_setup(1),
            call.list_setup(5),
            call.test_setup(3),
            call.test_test(3),
            call.test_tear_down(3),
            call.list_tear_down(5),
            call.list_tear_down(1),
            call.list_setup(1),
            call.list_setup(5),
            call.test_setup(4),
            call.test_test(4),
            call.test_tear_down(4),
            call.list_tear_down(5),
            call.list_tear_down(1),
            call.list_exit(5),
            call.list_exit(1),
        ]
    )
    assert "PASSED" == sequencer.end_status


def test_abort_sequence(sequencer, mock_obj):
    # Un-subscribe the other function as this was causing conflicts in tests
    pub.unsubscribe(fail_on_prompt, "UI_req_choices")

    # Make the test abort by default:
    pub.subscribe(abort_on_prompt, "UI_req_choices")

    with patch.object(MockTest, "test", side_effect=Exception("Test error")):
        test_seq = MockTestList([MockTest(2, mock_obj)], 1, mock_obj)

        sequencer.load(test_seq)
        sequencer.run_sequence()

        mock_obj.assert_has_calls(
            [
                call.list_enter(1),
                call.list_setup(1),
                call.test_setup(2),
                # No call.test_test(1) as this now raises an exception
                call.test_tear_down(2),
                call.list_tear_down(1),
                call.list_exit(1),
            ]
        )
    assert "ERROR" == sequencer.end_status


def test_load_test(sequencer):
    test_seq = TestList(seq=[TestPass(), TestPass()])
    sequencer.load(test_seq)

    # Check sequence object loaded
    assert sequencer.tests.tests[-1] == test_seq
    # Check status is "N/A"
    assert sequencer.end_status == "N/A"


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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
            "UI_block_start",
            "UI_req_choices",
            "UI_block_end",
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
