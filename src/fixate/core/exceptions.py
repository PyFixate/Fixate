class SequenceAbort(Exception):
    pass


class ScriptError(Exception):
    pass


class TestRetryExceeded(Exception):
    pass


class TestAbort(Exception):
    pass


class InstrumentError(Exception):
    pass


class InstrumentTimeOut(InstrumentError):
    pass


class ParameterError(Exception):
    pass


class InvalidScalarQuantityError(Exception):
    pass


class InstrumentFeatureUnavailable(InstrumentError):
    pass


class InstrumentNotConnected(InstrumentError):
    pass


class NotCompatible(Exception):
    pass


class MissingParameters(ParameterError):
    pass


class UserInputError(Exception):
    pass


class TestClassError(Exception):
    pass


class TestError(Exception):
    pass


class DUTError(Exception):
    pass


class CheckFail(Exception):
    pass
