import unittest
from unittest.mock import MagicMock
from pubsub import pub
from fixate.core.ui import (
    _user_req_input,
    _float_validate,
    user_serial,
    user_input_float,
    _ten_digit_serial,
)
from fixate.core.exceptions import UserInputError


class MockUserDriver(MagicMock):
    def execute_target(self, msg, q):
        q.put(self.test_value)


class TestUserRequest(unittest.TestCase):
    def setUp(self):
        self.test_method = _user_req_input
        self.mock = MockUserDriver()
        pub.subscribe(self.mock.execute_target, "UI_req_input")

    def tearDown(self):
        pub.unsubscribe(self.mock.execute_target, "UI_req_input")

    def test_read_from_queue(self):
        self.mock.test_value = "World"
        self.assertEqual(self.test_method("message"), ("Result", "World"))

    def test_target_check(self):
        self.mock.return_value = "World"
        self.assertEqual(self.test_method("HI", target=self.mock), ("Result", "World"))

    def test_float_validate_fails(self):
        # _float_validate is tested implicitly by user_input_float, but because of how the
        # failures are done at that level, we should check the failure case here
        self.assertFalse(_float_validate("abc"))

    def test_target_float(self):
        self.mock.test_value = "1.23"
        self.test_method = user_input_float
        resp = self.test_method("message")
        self.assertAlmostEqual(resp[1], float(self.mock.test_value))

    def test_target_float_fails(self):
        self.mock.test_value = "abc"
        self.test_method = user_input_float
        resp = self.test_method("message")
        self.assertTrue(isinstance(resp[1], UserInputError))

    def test_user_serial(self):
        self.mock.test_value = "1234567890"
        resp = user_serial("message")
        self.assertEqual(resp[1], int(self.mock.test_value))

    def test_ten_digit_serial_fails(self):
        # _ten_digit_serial is tested implicitly by user_serial since it's the default, but because of how the
        # failures are done at that level, we should check the failure case here
        self.assertEqual(_ten_digit_serial("123456789"), False)

    def test_user_serial_fail(self):
        self.mock.test_value = "123456789"  # < 10 digits
        resp = user_serial("message")
        self.assertTrue(isinstance(resp[1], UserInputError))
