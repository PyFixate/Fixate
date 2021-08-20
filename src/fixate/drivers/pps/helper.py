import inspect
from abc import ABCMeta

from fixate.core.exceptions import InstrumentFeatureUnavailable

import typing

number = typing.Union[float, int]


class Groups:
    def group1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def group2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def group3(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def group4(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def group5(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Measure:
    def voltage(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def current(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def power(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


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
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def __call__(self, value: bool):
        self._call(value)


class Channel:
    def __init__(self):
        self.measure = Measure()
        self.timer = Timer()

    def voltage(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def current(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def wave(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def __call__(self, value: bool):
        self._call(value)


class Address:
    def ip(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def mask(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def gate(self, value: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def dhcp(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


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
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def idn(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def get_identity(self):
        """
        same function as idn, but discover.py expects this function
        I don't know if any test scripts reference idn so I won't refactor it
        """
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )
