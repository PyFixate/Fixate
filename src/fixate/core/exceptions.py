class FixateError(Exception):
    pass


class SequenceAbort(FixateError):
    pass


class ScriptError(FixateError):
    pass


class TestRetryExceeded(FixateError):
    pass


class TestAbort(FixateError):
    pass


class InstrumentError(FixateError):
    pass


class InstrumentTimeOut(InstrumentError):
    pass


class ParameterError(FixateError):
    pass


class InvalidScalarQuantityError(FixateError):
    pass


class InstrumentFeatureUnavailable(InstrumentError):
    pass


class InstrumentNotConnected(InstrumentError):
    pass


class NotCompatible(FixateError):
    pass


class MissingParameters(ParameterError):
    pass


class UserInputError(FixateError):
    pass


class TestClassError(FixateError):
    pass


class TestError(FixateError):
    pass


class DUTError(FixateError):
    pass


class CheckFail(FixateError):
    pass
