import pytest
import pubsub

from fixate.core.exceptions import UserInputError
from fixate import (
    user_input,
    user_input_float,
    user_serial,
    Validator,
    user_yes_no,
)

# Mock the UI interface
class MockUserInterface:
    def execute_target(self, msg, q):
        q.put(self.test_value)


@pytest.fixture
def mock_user_interface():
    mock = MockUserInterface()
    pubsub.pub.subscribe(mock.execute_target, "UI_req_input")
    return mock


class MockUserInterfaceChoices:
    def execute_target(self, msg, q, choices):
        q.put(self.test_value)


@pytest.fixture
def mock_user_interface_choices():
    mock = MockUserInterfaceChoices()
    pubsub.pub.subscribe(mock.execute_target, "UI_req_choices")
    return mock


def test_user_input(mock_user_interface):
    mock_user_interface.test_value = "Hello"
    resp = user_input("message")
    assert resp == "Hello"


def test_user_input_float(mock_user_interface):
    mock_user_interface.test_value = "1.23"
    resp = user_input_float("message")
    assert resp == 1.23


def test_user_input_float_fails(mock_user_interface):
    mock_user_interface.test_value = "abc"
    with pytest.raises(UserInputError):
        user_input_float("message")


def test_user_serial(mock_user_interface):
    mock_user_interface.test_value = "1234567890"
    resp = user_serial("message")
    assert resp == 1234567890


def test_user_serial_fails(mock_user_interface):
    mock_user_interface.test_value = "abc"
    with pytest.raises(UserInputError):
        user_serial("message")


def test_user_serial_custom_validator(mock_user_interface):
    mock_user_interface.test_value = "240712345"
    serial_validator = Validator(
        lambda x: x.startswith("2407"), "Serial must be from July 2024 - 2407"
    )
    resp = user_serial("message", validator=serial_validator)
    assert resp == 240712345


def test_user_serial_custom_validator_fails(mock_user_interface):
    mock_user_interface.test_value = "240612345"
    serial_validator = Validator(
        lambda x: x.startswith("2407"), "Serial must be from July 2024 - 2407"
    )
    with pytest.raises(UserInputError):
        user_serial("message", validator=serial_validator)


def test_user_serial_str(mock_user_interface):
    mock_user_interface.test_value = "abcdefgh"
    serial_validator = Validator(
        lambda x: x.startswith("abc"), "Serial must start with 'abc'"
    )
    resp = user_serial("message", validator=serial_validator, return_type=str)
    assert resp == "abcdefgh"


# the user_yes_no tests implicitly test the _user_choices function, so no need
# to test the _user_retry_abort_fail function
def test_user_yes_no_yes(mock_user_interface_choices):
    mock_user_interface_choices.test_value = "yes"
    resp = user_yes_no("message")
    assert resp == "YES"


def test_user_yes_no_y(mock_user_interface_choices):
    mock_user_interface_choices.test_value = "y"
    resp = user_yes_no("message")
    assert resp == "YES"


def test_user_yes_no_no(mock_user_interface_choices):
    mock_user_interface_choices.test_value = "no"
    resp = user_yes_no("message")
    assert resp == "NO"


def test_user_yes_no_fails(mock_user_interface_choices):
    mock_user_interface_choices.test_value = "maybe"
    with pytest.raises(UserInputError):
        user_yes_no("message")
