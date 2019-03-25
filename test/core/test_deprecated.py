import pytest
from fixate.core.common import deprecated


def mock_function_undeprecated(mock_input):
    return mock_input


mock_function = deprecated(mock_function_undeprecated)


def test_returns_callable():
    """
    Check that the return value of the decorator is callable
    """
    assert callable(deprecated(mock_function_undeprecated))


def test_warning_warn():
    """
    Test that our decorated function calls the warning as expected
    """
    with pytest.warns(DeprecationWarning):
        mock_function(None)


def test_returns_functional(mocker):
    test_input = 123
    with mocker.patch("fixate.core.common.warnings"):
        assert test_input == mock_function(test_input)


class Foo:
    def __init__(self):
        self.called = False

    def foo(self):
        self.called = True


def test_decorated_function_is_called():
    test_class = Foo()
    mocked_func = deprecated(test_class.foo)
    with pytest.warns(DeprecationWarning):
        assert not test_class.called
        mocked_func()
        assert test_class.called
