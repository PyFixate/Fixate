class SequenceAbort(BaseException):
    pass


class ScriptError(BaseException):
    pass


class TestRetryExceeded(BaseException):
    pass


class TestAbort(BaseException):
    pass


class InstrumentError(BaseException):
    pass


class InstrumentTimeOut(InstrumentError):
    pass


class ParameterError(BaseException):
    pass


class InvalidScalarQuantityError(BaseException):
    pass


class InstrumentFeatureUnavailable(InstrumentError):
    pass


class InstrumentNotConnected(InstrumentError):
    pass


class NotCompatible(BaseException):
    pass


class MissingParameters(ParameterError):
    pass


class UserInputError(BaseException):
    pass


class TestClassError(BaseException):
    pass


class TestError(BaseException):
    pass


class DUTError(BaseException):
    pass


class CheckFail(BaseException):
    pass
