"""
This module is used to allow for tests to test values against criteria.
It should implement necessary logging functions and report success or failure.
"""
import fixate.config


class CheckClass:
    status = None
    test_val = None
    comparison = None
    _min = None
    _max = None
    nominal = None
    context = None
    exception = None
    tol = None
    description = ""
    test_index = ""

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


def _message_parse(target, **kwargs):
    chk = CheckClass(**kwargs)
    chk.target = target
    result = target(chk)
    return fixate.config.RESOURCES["SEQUENCER"].check(chk, result)


def _passes(chk):
    return True


def chk_passes(description=""):
    return _message_parse(target=_passes, description=description)


def _fails(chk):
    return False


def chk_fails(description=""):
    return _message_parse(target=_fails, description=description)


def _log_value(chk):
    return True


def chk_log_value(test_val, description=""):
    return _message_parse(test_val=test_val, target=_log_value, description=description)


def _in_range(chk):
    return chk._min < chk.test_val < chk._max


def chk_in_range(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_range,
        _min=_min,
        _max=_max,
        description=description,
    )


def _in_tolerance(chk):
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


def chk_in_tolerance(test_val, nominal, tol, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_tolerance,
        nominal=nominal,
        tol=tol,
        description=description,
    )


def _in_range_equal(chk):
    return chk._min <= chk.test_val <= chk._max


def chk_in_range_equal(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal,
        _min=_min,
        _max=_max,
        description=description,
    )


def _in_range_equal_min(chk):
    return chk._min <= chk.test_val < chk._max


def chk_in_range_equal_min(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal_min,
        _min=_min,
        _max=_max,
        description=description,
    )


def _in_range_equal_max(chk):
    return chk._min < chk.test_val <= chk._max


def chk_in_range_equal_max(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_range_equal_max,
        _min=_min,
        _max=_max,
        description=description,
    )


def _outside_range(chk):
    return chk.test_val < chk._min or chk.test_val > chk._max


def chk_outside_range(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_outside_range,
        _min=_min,
        _max=_max,
        description=description,
    )


def _outside_range_equal(chk):
    return chk.test_val <= chk._min or chk.test_val >= chk._max


def chk_outside_range_equal(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal,
        _min=_min,
        _max=_max,
        description=description,
    )


def _outside_range_equal_min(chk):
    return chk.test_val <= chk._min or chk.test_val > chk._max


def chk_outside_range_equal_min(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal_min,
        _min=_min,
        _max=_max,
        description=description,
    )


def _outside_range_equal_max(chk):
    return chk.test_val < chk._min or chk.test_val >= chk._max


def chk_outside_range_equal_max(test_val, _min, _max, description=""):
    return _message_parse(
        test_val=test_val,
        target=_outside_range_equal_max,
        _min=_min,
        _max=_max,
        description=description,
    )


def _smaller_or_equal(chk):
    return chk.test_val <= chk.nominal


def chk_smaller_or_equal(test_val, nominal, description=""):
    return _message_parse(
        test_val=test_val,
        target=_smaller_or_equal,
        nominal=nominal,
        description=description,
    )


def _greater_or_equal(chk):
    return chk.test_val >= chk.nominal


def chk_greater_or_equal(test_val, nominal, description=""):
    return _message_parse(
        test_val=test_val,
        target=_greater_or_equal,
        nominal=nominal,
        description=description,
    )


def _smaller(chk):
    return chk.test_val < chk.nominal


def chk_smaller(test_val, nominal, description=""):
    return _message_parse(
        test_val=test_val, target=_smaller, nominal=nominal, description=description
    )


def _greater(chk):
    return chk.test_val > chk.nominal


def chk_greater(test_val, nominal, description=""):
    return _message_parse(
        test_val=test_val, target=_greater, nominal=nominal, description=description
    )


def _equal(chk):
    return chk.test_val == chk.nominal


def chk_equal(test_val, nominal, description=""):
    return _message_parse(
        test_val=test_val, target=_equal, nominal=nominal, description=description
    )


def _true(chk):
    return chk.test_val is True


def chk_true(test_val, description=""):
    return _message_parse(test_val=test_val, target=_true, description=description)


def _false(chk):
    return chk.test_val is False


def chk_false(test_val, description=""):
    return _message_parse(test_val=test_val, target=_false, description=description)


def _in_tolerance_equal(chk):
    return (
        chk.nominal * (1 - chk.tol / 100)
        <= chk.test_val
        <= chk.nominal * (1 + chk.tol / 100)
    )


def chk_in_tolerance_equal(test_val, nominal, tol, description=""):
    return _message_parse(
        test_val=test_val,
        target=_in_tolerance_equal,
        nominal=nominal,
        tol=tol,
        description=description,
    )
