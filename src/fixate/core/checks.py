"""
This module is used to allow for tests to test values against criteria.
It should implement necessary logging functions and report success or failure.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional
import logging

import fixate.config

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    """Check Class Results to publish to subscribers
    Is a subset of CheckClass attrs
    """

    result: bool  # Result of check
    status: str  # Status string PASS/FAIL
    description: str  # Description of check
    test_val: Any = None
    target_name: str = None  # Name of check type
    check_string: str = None  # formatted string for UI display
    check_params: Iterable = None  # Store for csv logging


@dataclass
class _CheckClass:
    """Loads check parameters and evaluates check"""

    target: Callable
    test_val: Any = field(default=None)
    target_name: str = field(default=None)
    _min: Optional[Any] = field(default=None)
    _max: Optional[Any] = field(default=None)
    nominal: Optional[Any] = field(default=None)
    tol: Optional[Any] = field(default=None)
    deviation: Optional[Any] = field(default=None)
    description: str = field(default="")
    fmt: Optional[str] = field(default=None)
    formatter: Optional[Callable] = field(default=None)
    status: str = field(default=None)

    def _generate_check_string(self) -> str:
        self.target_name = self.target.__name__[1:].replace("_", " ")
        if self.formatter is None:
            self.formatter = _format_novalue
        try:
            check_string = self.formatter(self)
        except (ValueError, TypeError):
            # Catch bad formatter choice
            _logger.exception("Failed to format check string - ignoring format...")
            # Fall back to no formatting - to be consistent with previous implementation
            self.fmt = ""
            check_string = self.formatter(self)
        return check_string

    def get_result(self) -> CheckResult:
        """Return check result as a dataclass

        With necessary information to log and display on UI
        """
        result = self.target(self)
        self.status = "PASS" if result else "FAIL"
        check_string = self._generate_check_string()
        # NOTE: stash used params for csv reporting (probably a better way)
        check_params = [
            x
            for x in [self.nominal, self._min, self._max, self.tol, self.deviation]
            if x is not None
        ]
        return CheckResult(
            result,
            self.status,
            self.description,
            self.test_val,
            self.target_name,
            check_string,
            check_params,
        )


def _message_parse(target: Callable[[_CheckClass], bool], **kwargs) -> bool:
    chk = _CheckClass(target=target, **kwargs)
    chkresult = chk.get_result()
    return fixate.config.RESOURCES["SEQUENCER"].check(chkresult)


def _format_range(chk: _CheckClass) -> str:
    fmt = chk.fmt if chk.fmt is not None else ".3g"  # Default
    return (
        f"{chk.status} when comparing {chk.test_val:{fmt}} {chk.target_name} "
        f"{chk._min:{fmt}} - {chk._max:{fmt}} : {chk.description}"
    )


def _format_tolerance(chk: _CheckClass) -> str:
    fmt = chk.fmt if chk.fmt is not None else ".3g"  # Default
    return (
        f"{chk.status} when comparing {chk.test_val:{fmt}} {chk.target_name} "
        f"{chk.nominal:{fmt}} +- {chk.tol:{fmt}}% : {chk.description}"
    )


def _format_deviation(chk: _CheckClass) -> str:
    fmt = chk.fmt if chk.fmt is not None else ".3g"  # Default
    return (
        f"{chk.status} when comparing {chk.test_val:{fmt}} {chk.target_name} "
        f"{chk.nominal:{fmt}} +- {chk.deviation:{fmt}} : {chk.description}"
    )


def _format_onesided(chk: _CheckClass) -> str:
    fmt = chk.fmt if chk.fmt is not None else ".3g"  # Default
    return (
        f"{chk.status} when comparing {chk.test_val:{fmt}} {chk.target_name} "
        f"{chk.nominal:{fmt}} : {chk.description}"
    )


def _format_testvalue(chk: _CheckClass) -> str:
    fmt = chk.fmt if chk.fmt is not None else ".3g"  # Default
    return f"{chk.status}: {chk.test_val:{fmt}} : {chk.description}"


def _format_novalue(chk: _CheckClass) -> str:
    return f"{chk.status}: {chk.description}"


def _passes(chk: _CheckClass) -> bool:
    return True


def chk_passes(description="") -> bool:
    """Pass Test"""
    return _message_parse(target=_passes, description=description)
    # _format_novalue


def _fails(chk: _CheckClass) -> bool:
    return False


def chk_fails(description="") -> bool:
    """Fail Test"""
    return _message_parse(target=_fails, description=description)
    # _format_novalue


def _log_value(chk: _CheckClass) -> bool:
    return True


def chk_log_value(test_val, description="", fmt=None) -> bool:
    """Log test_val"""
    return _message_parse(
        test_val=test_val,
        target=_log_value,
        description=description,
        formatter=_format_testvalue,
        fmt=fmt,
    )


def _in_range(chk: _CheckClass) -> bool:
    return chk._min < chk.test_val < chk._max


def chk_in_range(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: _min < test_val < _max"""
    return _message_parse(
        test_val=test_val,
        target=_in_range,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _in_tolerance(chk: _CheckClass) -> bool:
    if chk.nominal >= 0:
        return (
            chk.nominal * (1 - chk.tol / 100)
            <= chk.test_val
            <= chk.nominal * (1 + chk.tol / 100)
        )
    else:
        return (
            chk.nominal * (1 + chk.tol / 100)
            <= chk.test_val
            <= chk.nominal * (1 - chk.tol / 100)
        )


def chk_in_tolerance(test_val, nominal, tol, description="", fmt=None) -> bool:
    """Check: nominal - tol% < test_val < nominal + tol%"""
    return _message_parse(
        test_val=test_val,
        target=_in_tolerance,
        nominal=nominal,
        tol=tol,
        description=description,
        formatter=_format_tolerance,
        fmt=fmt,
    )


def _in_range_equal(chk: _CheckClass) -> bool:
    return chk._min <= chk.test_val <= chk._max


def chk_in_range_equal(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: _min <= test_val <= _max"""
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _in_range_equal_min(chk: _CheckClass) -> bool:
    return chk._min <= chk.test_val < chk._max


def chk_in_range_equal_min(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: _min <= test_val < _max"""
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal_min,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _in_range_equal_max(chk: _CheckClass) -> bool:
    return chk._min < chk.test_val <= chk._max


def chk_in_range_equal_max(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: _min < test_val <= _max"""
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal_max,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _outside_range(chk: _CheckClass) -> bool:
    return chk.test_val < chk._min or chk.test_val > chk._max


def chk_outside_range(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: test_val > _max or < _min"""
    return _message_parse(
        test_val=test_val,
        target=_outside_range,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _outside_range_equal(chk: _CheckClass) -> bool:
    return chk.test_val <= chk._min or chk.test_val >= chk._max


def chk_outside_range_equal(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: test_val >= _max or <= _min"""
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _outside_range_equal_min(chk: _CheckClass) -> bool:
    return chk.test_val <= chk._min or chk.test_val > chk._max


def chk_outside_range_equal_min(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: test_val > _max or <= _min"""
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal_min,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _outside_range_equal_max(chk: _CheckClass) -> bool:
    return chk.test_val < chk._min or chk.test_val >= chk._max


def chk_outside_range_equal_max(test_val, _min, _max, description="", fmt=None) -> bool:
    """Check: test_val >= _max or < _min"""
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal_max,
        _min=_min,
        _max=_max,
        description=description,
        formatter=_format_range,
        fmt=fmt,
    )


def _smaller_or_equal(chk: _CheckClass) -> bool:
    return chk.test_val <= chk.nominal


def chk_smaller_or_equal(test_val, nominal, description="", fmt=None) -> bool:
    """Check: test_val <= nominal"""
    return _message_parse(
        test_val=test_val,
        target=_smaller_or_equal,
        nominal=nominal,
        description=description,
        formatter=_format_onesided,
        fmt=fmt,
    )


def _greater_or_equal(chk: _CheckClass) -> bool:
    return chk.test_val >= chk.nominal


def chk_greater_or_equal(test_val, nominal, description="", fmt=None) -> bool:
    """Check: test_val >= nominal"""
    return _message_parse(
        test_val=test_val,
        target=_greater_or_equal,
        nominal=nominal,
        description=description,
        formatter=_format_onesided,
        fmt=fmt,
    )


def _smaller(chk: _CheckClass) -> bool:
    return chk.test_val < chk.nominal


def chk_smaller(test_val, nominal, description="", fmt=None) -> bool:
    """Check: test_val < nominal"""
    return _message_parse(
        test_val=test_val,
        target=_smaller,
        nominal=nominal,
        description=description,
        formatter=_format_onesided,
        fmt=fmt,
    )


def _greater(chk: _CheckClass) -> bool:
    return chk.test_val > chk.nominal


def chk_greater(test_val, nominal, description="", fmt=None) -> bool:
    """Check: test_val > nominal"""
    return _message_parse(
        test_val=test_val,
        target=_greater,
        nominal=nominal,
        description=description,
        formatter=_format_onesided,
        fmt=fmt,
    )


def _equal(chk: _CheckClass) -> bool:
    return chk.test_val == chk.nominal


def chk_equal(test_val, nominal, description="", fmt=None) -> bool:
    """Check: test_val == nominal"""
    return _message_parse(
        test_val=test_val,
        target=_equal,
        nominal=nominal,
        description=description,
        formatter=_format_onesided,
        fmt=fmt,
    )


def _true(chk: _CheckClass) -> bool:
    return chk.test_val is True


def chk_true(test_val, description="", fmt="") -> bool:
    """Check: test_val is True"""
    return _message_parse(
        test_val=test_val,
        target=_true,
        description=description,
        formatter=_format_testvalue,
        fmt=fmt,
    )


def _false(chk: _CheckClass) -> bool:
    return chk.test_val is False


def chk_false(test_val, description="", fmt="") -> bool:
    """Check: test_val is False"""
    return _message_parse(
        test_val=test_val,
        target=_false,
        description=description,
        formatter=_format_testvalue,
        fmt=fmt,
    )


def _in_tolerance_equal(chk: _CheckClass) -> bool:
    return (
        chk.nominal * (1 - chk.tol / 100)
        <= chk.test_val
        <= chk.nominal * (1 + chk.tol / 100)
    )


def chk_in_tolerance_equal(test_val, nominal, tol, description="", fmt=None) -> bool:
    """Check: nominal - tol% <= test_val <= nominal + tol%"""
    return _message_parse(
        test_val=test_val,
        target=_in_tolerance_equal,
        nominal=nominal,
        tol=tol,
        description=description,
        formatter=_format_tolerance,
        fmt=fmt,
    )


def _in_deviation_equal(chk: _CheckClass) -> bool:
    return chk.nominal - chk.deviation <= chk.test_val <= chk.nominal + chk.deviation


def chk_in_deviation_equal(
    test_val, nominal, deviation, description="", fmt=None
) -> bool:
    """Check: nominal - deviation <= test_val <= nominal + deviation"""
    return _message_parse(
        test_val=test_val,
        target=_in_deviation_equal,
        nominal=nominal,
        deviation=deviation,
        description=description,
        formatter=_format_deviation,
        fmt=fmt,
    )
