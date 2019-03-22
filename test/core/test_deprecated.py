import pytest
import unittest.mock as mocker
from fixate.core.common import deprecated
import warnings


@deprecated
def mock_function(mock_input):
    return mock_input


def mock_function_undeprecated(mock_input):
    return mock_input


def test_warning_warn(mocker):
    with pytest.warns(DeprecationWarning):
        test_input = 123
        mock_function(test_input)


@mocker.patch('warnings.warn')
def test_returns_callable(mocker):
    test_input = 123
    assert callable(deprecated(mock_function(test_input)))


@mocker.patch('warnings.warn')
def test_returns_functional(mocker):
    test_input = 123
    sent = mock_function_undeprecated(test_input)
    returned = deprecated(mock_function_undeprecated)
    assert sent == returned(test_input)


@mocker.patch('warnings.warn')
def test_warnings_warn_called(mocker):
    test_input = 123
    mock_function(test_input)
    warnings.warn.assert_called_once_with('Function mock_function is deprecated. Please consider updating api calls', DeprecationWarning)
