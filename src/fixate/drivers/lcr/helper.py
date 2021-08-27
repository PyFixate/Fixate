from abc import ABCMeta, abstractmethod


class TestResult:
    Rs = None
    Cs = None
    Rp = None
    Cp = None
    Ls = None
    Lp = None
    Z = None
    TH = None
    F = None
    D = None
    Q = None

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class LCR(metaclass=ABCMeta):
    REGEX_ID = "LCR"
    frequency = None
    range = None

    def __init__(self, instrument):
        self.instrument = instrument
        self.samples = 1

    @abstractmethod
    def measure(self, func=None, multiple_results=False, **mode_params):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_identity(self):
        pass
