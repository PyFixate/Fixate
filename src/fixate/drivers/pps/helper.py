from abc import ABCMeta, abstractmethod
import inspect
import fixate.config
from fixate.core.discover import filter_connected, open_visa_instrument, discover_visa
from fixate.core.exceptions import InstrumentNotConnected, InstrumentFeatureUnavailable

try:
    import typing

    number = typing.Union[float, int]
except ImportError:
    number = float


def open(restrictions=None):
    """
    Currently only searches for Serial Devices
    :param restrictions:
    :return:
    """
    # All config values for implemented instruments should be called
    if restrictions is None:
        restrictions = {}

    classes = fixate.config.DRIVERS.get("PPS", {})

    instruments = filter_connected(fixate.config.INSTRUMENTS or {}, classes)
    if not instruments:
        # All discovery methods for implemented instruments should be called
        discover_visa()
        instruments = filter_connected(fixate.config.INSTRUMENTS or {}, classes)
    # This is where the restrictions would come in
    if instruments:
        for instr in instruments:
            return instruments[instr]
    raise InstrumentNotConnected("No valid {} found".format("PPS"))


class Groups:
    def group1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def group2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def group3(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def group4(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def group5(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Measure:
    def voltage(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def current(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def power(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Timer:

    def set_waveform(self, waveform: list):
        """
        :param pattern: A list of tuples of pattern
        [ (voltage: number in volts, current: number in amps, duration: number in seconds)
        ]
        eg. [(12,0.5,2), (24, 0.5, 3)]
        will be set at 12V 0.5Amps for 2 seconds followed by 24V 0.5 Amps for 3 seconds
        Takes a maximum of 5 points
        Must call timer(True) to start the waveform
        :return:
        """

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def __call__(self, value: bool):
        self._call(value)


class Channel:
    def __init__(self):
        self.measure = Measure()
        self.timer = Timer()

    def voltage(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def current(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def wave(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def __call__(self, value: bool):
        self._call(value)


class Address:
    def ip(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def mask(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def gate(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def dhcp(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class PPS(metaclass=ABCMeta):
    _baud_rates = []
    REGEX_ID = "PPS"
    INSTR_TYPE = ""

    def __init__(self, instrument):
        self.instrument = instrument
        self.save = Groups()
        self.recall = Groups()
        self.channel1 = Channel()
        self.channel2 = Channel()
        self.address = Address()
        self.series = Channel()
        self.parallel = Channel()

    def series(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def idn(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))
