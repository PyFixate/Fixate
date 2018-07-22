import time
import unittest
from unittest.mock import MagicMock, call
from pubsub import pub
import fixate
from fixate.core.common import TestList, TestClass


def sleep_100m():
    time.sleep(.1)
    return True


class Lst(TestList):
    """
    Mock Test List
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


class LstSetupFail(Lst):
    def set_up(self):
        super().set_up()
        raise ValueError("Failed Setup")


class Test(TestClass):
    """
    Dummy Test Class
    """
    attempts = 1

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

@unittest.skip("busted. Looks like aysnc stuff might not be working?")
class TestSequencerTests(unittest.TestCase):
    async = False

    def setUp(self):
        self.test_cls = fixate.config.RESOURCES["SEQUENCER"]
        pub.subscribe(self.abort_on_error, "UI_req")

    def abort_on_error(self, msg, q, target=None, attempts=5, kwargs=None):
        q.put("Result", "ABORT")

    def test_single_test_deep_level(self):
        self.mock_master = MagicMock()
        self.test_cls.clear_tests()

        test_lst = \
            Lst([
                Lst([
                    Test(3, self.mock_master)],
                    2, self.mock_master)],
                1, self.mock_master)
        self.test_cls.load(test_lst)
        self.run_test_cls()
        self.mock_master.assert_has_calls([call.list_enter(1),
                                           call.list_enter(2),
                                           call.list_setup(1),
                                           call.list_setup(2),
                                           call.test_setup(3),
                                           call.test_test(3),
                                           call.test_tear_down(3),
                                           call.list_tear_down(2),
                                           call.list_tear_down(1),
                                           call.list_exit(2),
                                           call.list_exit(1),
                                           ])

    def test_async_single_test_deep_level(self):
        self.async = True
        try:
            self.test_single_test_deep_level()
        finally:
            self.async = False

    def test_complex_test_list(self):
        self.mock_master = MagicMock()
        self.test_cls.clear_tests()
        test_lst = Lst([Test(2, self.mock_master),
                        Lst([Test(4, self.mock_master),
                             Test(5, self.mock_master)],
                            3, self.mock_master),
                        Test(6, self.mock_master)],
                       1, self.mock_master)
        self.test_cls.load(test_lst)
        self.run_test_cls()
        self.mock_master.assert_has_calls([call.list_enter(1),
                                           call.list_setup(1),
                                           call.test_setup(2),
                                           call.test_test(2),
                                           call.test_tear_down(2),
                                           call.list_tear_down(1),
                                           call.list_enter(3),
                                           call.list_setup(1),
                                           call.list_setup(3),
                                           call.test_setup(4),
                                           call.test_test(4),
                                           call.test_tear_down(4),
                                           call.list_tear_down(3),
                                           call.list_tear_down(1),
                                           call.list_setup(1),
                                           call.list_setup(3),
                                           call.test_setup(5),
                                           call.test_test(5),
                                           call.test_tear_down(5),
                                           call.list_tear_down(3),
                                           call.list_tear_down(1),
                                           call.list_exit(3),
                                           call.list_setup(1),
                                           call.test_setup(6),
                                           call.test_test(6),
                                           call.test_tear_down(6),
                                           call.list_tear_down(1),
                                           call.list_exit(1),
                                           ])

    def test_async_complex_test_list(self):
        self.async = True
        try:
            self.test_complex_test_list()
        finally:
            self.async = False

    def test_list_setup_fail(self):
        self.mock_master = MagicMock()
        self.test_cls.clear_tests()

        test_lst = \
            Lst(
                [LstSetupFail(
                    [Lst(
                        [Test(4, self.mock_master)],
                        3, self.mock_master)],
                    2, self.mock_master)],
                1, self.mock_master)
        self.test_cls.load(test_lst)
        self.run_test_cls()
        self.mock_master.assert_has_calls([call.list_enter(1),
                                           call.list_enter(2),
                                           call.list_enter(3),
                                           call.list_setup(1),
                                           call.list_setup(2),
                                           call.list_tear_down(2),
                                           call.list_tear_down(1),
                                           call.list_exit(3),
                                           call.list_exit(2),
                                           call.list_exit(1),
                                           ])

    def test_list_retry_enter_exit(self):
        """
        Test for retries
        :return:
        """
        self.mock_master = MagicMock()
        self.test_cls.clear_tests()

        test_lst = \
            Lst(
                [LstSetupFail(
                    [Lst(
                        [Test(4, self.mock_master)],
                        3, self.mock_master)],
                    2, self.mock_master)],
                1, self.mock_master)
        self.test_cls.load(test_lst)
        self.run_test_cls()
        self.mock_master.assert_has_calls([call.list_enter(1),
                                           call.list_enter(2),
                                           call.list_enter(3),
                                           call.list_setup(1),
                                           call.list_setup(2),
                                           call.list_tear_down(2),
                                           call.list_tear_down(1),
                                           call.list_exit(3),
                                           call.list_exit(2),
                                           call.list_exit(1),
                                           ])
    def test_async_list_setup_fail(self):
        self.async = True
        try:
            self.test_list_setup_fail()
        finally:
            self.async = False

    def run_test_cls(self):
        if self.async:
            self.test_cls.loop.run_in_executor(None, self.test_cls.run_sequence)
        else:
            self.test_cls.run_sequence()

    def tearDown(self):
        self.mock_master = None
        pub.unsubscribe(self.abort_on_error, "UI_req")
        self.test_cls.clear_tests()
