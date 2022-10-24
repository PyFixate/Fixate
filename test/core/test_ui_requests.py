import unittest
from unittest.mock import MagicMock
from pubsub import pub
from fixate.core.ui import _user_req_input, _float_validate, user_serial


class MockUserDriver(MagicMock):
    def execute_target(self, msg, q, target=None, attempts=5, kwargs=None):
        if target:
            try:
                if self.test_value is None:
                    ret_val = target(**kwargs)
                else:
                    ret_val = target(self.test_value, **kwargs)
                q.put(("Result", ret_val))
            except Exception as e:
                q.put(("Exception", e))
        else:
            q.put(("Result", self.test_value))


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

    def test_target_float(self):
        self.mock.test_value = "1.23"
        resp = self.test_method("message", target=_float_validate)
        self.assertAlmostEqual(resp[1], float(self.mock.test_value))

    def test_target_float_fails(self):
        self.mock.test_value = "abc"
        resp = self.test_method("message", target=_float_validate)
        self.assertFalse(resp[1])

    def test_user_serial(self):
        self.mock.test_value = "1234567890"
        resp = user_serial("message")
        self.assertEqual(resp[1], int(self.mock.test_value))

    def test_user_serial_fail(self):
        self.mock.test_value = "123456789"  # < 10 digits
        resp = user_serial("message")
        self.assertFalse(resp[1])

    def test_user_serial_no_target(self):
        # Not really meaningful test?
        self.mock.test_value = 123
        resp = user_serial("message", None)
        self.assertEqual(resp[1], self.mock.test_value)
