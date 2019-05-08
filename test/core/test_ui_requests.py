import unittest
from unittest.mock import MagicMock
from pubsub import pub
from fixate.core.ui import _user_req_input


class MockUserDriver(MagicMock):
    def execute_target(self, msg, q, target=None, attempts=5, kwargs=None):
        if target:
            try:
                ret_val = target(**kwargs)
                q.put(("Result", ret_val))
            except Exception as e:
                q.put(("Exception", e))
        else:
            q.put(("Result", self.return_value))


@unittest.skip("process hangs. Probably waiting for a message to get sent?")
class TestUserRequest(unittest.TestCase):
    def setUp(self):
        self.test_method = _user_req_input
        self.mock = MockUserDriver()
        pub.subscribe(self.mock.execute_target, "UI_req")

    def test_read_from_queue(self):
        self.mock.return_value = "World"
        self.assertEqual(self.test_method("HI"), ("Result", "World"))

    def test_target_check(self):
        self.mock.test.return_value = "World"
        self.assertEqual(
            self.test_method("HI", target=self.mock.test), ("Result", "World")
        )
