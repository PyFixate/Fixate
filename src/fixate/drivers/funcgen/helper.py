from abc import ABCMeta, abstractmethod
from fixate.core.exceptions import InstrumentFeatureUnavailable
from fixate.core.discover import open_visa_instrument
import inspect

try:
    import typing

    number = typing.Union[float, int]
except ImportError:
    number = float


def open():
    """Open is the public api for the dmm driver for discovering and opening a connection
    to a valid Digital Multimeter
    :param restrictions:
    A dictionary containing the extents of the required equipment
    :return:
    A instantiated class connected to a valid funcgen
    """
    return open_visa_instrument("FUNC_GEN")


class Waveform:
    def sin(self):
        raise InstrumentFeatureUnavailable(
            "Feature {} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def square(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def ramp(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def pulse(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def arb(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def triangle(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def noise(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def dc(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def prbs(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class SyncPolarity:
    def normal(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def inverted(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class SyncMode:
    def normal(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def carrier(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def marker(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def source(self, channel: str):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Sync:
    def __init__(self):
        self.polarity = SyncPolarity()
        self.mode = SyncMode()

    def _call(self, output: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def __call__(self, output: bool):
        """
        :param value:
        Set Sync Output on (True) or off (False)
        :return:
        """
        self._call(output)


# class TriggerSource:
#     def immediate(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))
#
#     def external(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))
#
#     def manual(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))
#
#     def timer(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))


# class TriggerEdge:
#     def rising(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))
#
#     def falling(self):
#         raise InstrumentFeatureUnavailable(
#             "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TriggerOut:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def rising(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def falling(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def off(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Trigger:
    def __init__(self):
        self.out = TriggerOut()
        self.external = External()
        self.manual = Manual()

    def delay(self, seconds: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def immediate(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    # def external(self):  # Turn into class
    #     raise InstrumentFeatureUnavailable(
    #         "{} not available on this device".format(inspect.currentframe().f_code.co_name))
    #
    # def manual(self):  # Turn into class
    #     raise InstrumentFeatureUnavailable(
    #         "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def timer(self, seconds: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class External:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def rising(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def falling(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Manual:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def initiate(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Modulate:
    def __init__(self):
        self.am = ModulateAM()
        self.fm = ModulateFM()
        self.pm = ModulatePM()
        self.fsk = ModulateFSK()
        self.bpsk = ModulateBPSK()
        self.sum = ModulateSum()
        # self.shape = ModulateShape()
        self.source = ModulateSource()

    def __call__(self, value: bool):
        self._call(value)

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateInternal:
    def __init__(self):
        self.shape = ModulateShape()

    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def frequency(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def rate(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateSource:
    def __init__(self):
        self.internal = ModulateInternal()

    def external(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def channel1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def channel2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateAM:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def depth(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def dssc(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateFM:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def freq_dev(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

        # def frequency(self, value: number):
        #     raise InstrumentFeatureUnavailable(
        #         "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class ModulatePM:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def phase_dev(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateFSK:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def hop_freq(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def rate(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateBPSK:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def phase(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def rate(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateSum:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def modulate_percent(self, percent: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ModulateShape:
    def sin(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def square(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def triangle(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def up_ramp(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def down_ramp(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def noise(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def prbs(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def arb(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class ChannelBase:
    def __init__(self):
        self.waveform = Waveform()
        self.modulate = Modulate()
        self.burst = Burst()
        self.load = Load()

    def __call__(self, value: bool):
        self._call(value)

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def frequency(self, value: number):
        """
        Set the frequency on the channel
        :param value: int or float
        :return:
        """
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def vpp(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def vrms(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def dbm(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def offset(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def phase(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def duty(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

        # def output(self, value: bool):
        #     raise InstrumentFeatureUnavailable(
        #         "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Load:
    def __call__(self, ohms: number):
        self._call(ohms)

    def _call(self, ohms: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def infinite(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Burst:
    def __init__(self):
        self.gated = BurstGated()
        self.ncycle = BurstNCycle()

    def __call__(self, value: bool):
        self._call(value)

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def phase(self, degrees: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class BurstNCycle:
    def __init__(self):
        self.cycles = Cycles()

    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def burst_period(self, seconds: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def infinite(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class Cycles:
    def __call__(self, cycles: int):
        self._call(cycles)

    def _call(self, cycles: int):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def infinite(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class BurstGated:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def positive(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )

    def negative(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(
                inspect.currentframe().f_code.co_name
            )
        )


class FuncGen(metaclass=ABCMeta):
    """
    API Requirements

    Mockable
    Individually addressable
    Use the most significant at the front of the function call
    Add Sync, Sweep and Modulate
    Add DTMF

    Channel Selection
    >>>fg.channel1
    >>>fg.channel2

    Waveform Selection
    >>>fg.channel1.waveform.sin()
    >>>fg.channel1.waveform.square()
    >>>fg.channel1.waveform.ramp() # Has Special configurations
    >>>fg.channel1.waveform.pulse()
    >>>fg.channel1.waveform.arb() # Has Special configurations
    >>>fg.channel1.waveform.triangle() # Ramp with 50% symmetry
    >>>fg.channel1.waveform.noise() # Has Special configurations
    >>>fg.channel1.waveform.dc()
    >>>fg.channel1.waveform.prbs() # Has Special configurations

    Channel Configuration
    >>>fg.channel1.frequency(1000)
    >>>fg.channel1.vpp(282.8e-3)  # Configures the amplitude parameter and the units
    >>>fg.channel1.vrms(100e-3)
    >>>fg.channel1.dbm(-6.99)
    >>>fg.channel1.offset(10e-3)  # Volts
    >>>fg.channel1.phase(30) # Degrees
    >>>fg.channel1.duty(50) # Percent

    Channel Activation
    # >>>fg.channel1.output(True)
    # >>>fg.channel1.output(False)
    >>>fg.channel1(True)
    >>>fg.channel1(False)

    Arb Configuration
    To Be Implemented

    Sync Configuration
    >>>fg.sync.polarity.normal()
    >>>fg.sync.polarity.inverted()
    >>>fg.sync.mode.normal()
    >>>fg.sync.mode.carrier()
    >>>fg.sync.mode.marker()
    >>>fg.sync.mode.source("1") # Channel to sync to
    >>>fg.sync(True)
    >>>fg.sync(False)

    Trigger Configuration
    >>>fg.trigger.source.immediate()
    >>>fg.trigger.source.external()
    >>>fg.trigger.source.manual()
    >>>fg.trigger.source.timer()
    >>>fg.trigger.delay(1)  # Seconds
    >>>fg.trigger.edge.rising()
    >>>fg.trigger.edge.falling()
    # Not Available on External
    # >>>fg.trigger.out.off()  # Default on reset
    >>>fg.trigger.out(True)
    >>>fg.trigger.out(False) # Default on reset
    >>>fg.trigger.out.rising()
    >>>fg.trigger.out.falling()

    Modulate
    >>>fg.channel1.modulate.am()
    >>>fg.channel1.modulate.fm()
    >>>fg.channel1.modulate.pm()
    >>>fg.channel1.modulate.fsk()
    >>>fg.channel1.modulate.bpsk()
    >>>fg.channel1.modulate.sum()
    Modulate Sources
    >>>fg.channel1.modulate.source.internal()
    >>>fg.channel1.modulate.source.external()
    >>>fg.channel1.modulate.source.channel2()
    Modulate Activation
    >>>fg.channel1.modulate(True)
    >>>fg.channel1.modulate(False)
    Modulate Options
    >>>fg.channel1.modulate.am.depth(100) # %
    >>>fg.channel1.modulate.am.dssc(True)
    >>>fg.channel1.modulate.am.dssc(False)
    >>>fg.channel1.modulate.fm.freq_dev(100e3) # Hz
    >>>fg.channel1.modulate.fm.frequency(100e3) # Hz
    >>>fg.channel1.modulate.pm.phase_dev(100e3) # Degrees
    >>>fg.channel1.modulate.fsk.hop_freq(100e3) # Hz
    >>>fg.channel1.modulate.fsk.rate(100e3) # Hz
    >>>fg.channel1.modulate.bpsk.phase(100e3) # Hz
    >>>fg.channel1.modulate.bpsk.rate(100e3) # Hz
    >>>fg.channel1.modulate.sum.amplitude(100) # %
    >>>fg.channel1.modulate.sum.freq(100) # Hz

    >>>fg.channel1.modulate.shape.sin()
    >>>fg.channel1.modulate.shape.square()
    >>>fg.channel1.modulate.shape.triange()
    >>>fg.channel1.modulate.shape.up_ramp()
    >>>fg.channel1.modulate.shape.down_ramp()
    >>>fg.channel1.modulate.shape.noise()
    >>>fg.channel1.modulate.shape.prbs()
    >>>fg.channel1.modulate.shape.arb()

    Sweep
    To Be Implemented

    Burst
    >>>fg.channel1.burst(True)
    >>>fg.channel1.burst(False)
    >>>fg.channel1.burst.ncycle()
    >>>fg.channel1.burst.gated()
    >>>fg.channel1.burst.ncycle.cycles(-1) # -1 for Infinite positive integers for cycle number
    >>>fg.channel1.burst.ncycle.burst_period(10e-3) # Seconds
    >>>fg.channel1.burst.gated.positive()
    >>>fg.channel1.burst.gated.negative()
    >>>fg.channel1.burst.phase(0) # Degrees
    """

    REGEX_ID = "FUNCGEN"

    def __init__(self, instrument):
        self.instrument = instrument
        self.channel1 = ChannelBase()
        self.channel2 = ChannelBase()
        self.sync = Sync()
        self.trigger = Trigger()
        self.driver_definition = {}

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def local(self):
        pass

    # Deprecated Functions
    # @abstractmethod
    def function(
        self,
        waveform,
        channel=1,
        frequency=None,
        amplitude=None,
        phase=None,
        delay=None,
        offset=None,
        duty_cycle=None,
        symmetry=None,
    ):
        pass

    # @abstractmethod
    def adv_function(self, *mode, **mode_params):
        pass

    # @abstractmethod
    def am(self, frequency, depth, source=None, waveform=None):
        """
        :param frequency:
         int or float in Hz
        :param depth:
         int or float in %
        :param waveform:
         Defaults to sin
        :return:
        """
        pass

    # @abstractmethod
    def disable_am(self):
        pass

    # @abstractmethod
    def enable_am(self):
        pass

    # @property
    def amplitude_ch1(self):
        raise NotImplemented()

    # @amplitude_ch1.setter
    def amplitude_ch1(self, val):
        raise NotImplemented()

    # @property
    def amplitude_ch2(self):
        raise NotImplemented()

    # @amplitude_ch2.setter
    def amplitude_ch2(self, val):
        raise NotImplemented()

    @property
    def output_ch1(self):
        raise NotImplemented()

    @property
    def output_ch2(self):
        raise NotImplemented()

    @property
    def output_ch3(self):
        raise NotImplemented()

    @property
    def output_ch4(self):
        raise NotImplemented()

    @property
    def output_sync(self):
        raise NotImplemented()

    @output_ch1.setter
    def output_ch1(self, val):
        raise InstrumentFeatureUnavailable(
            "Feature output_ch1 not available on this device"
        )

    @output_ch2.setter
    def output_ch2(self, val):
        raise InstrumentFeatureUnavailable(
            "Feature output_ch2 not available on this device"
        )

    @output_ch3.setter
    def output_ch3(self, val):
        raise InstrumentFeatureUnavailable(
            "Feature output_ch3 not available on this device"
        )

    @output_ch4.setter
    def output_ch4(self, val):
        raise InstrumentFeatureUnavailable(
            "Feature output_ch4 not available on this device"
        )

    @output_sync.setter
    def output_sync(self, val):
        raise InstrumentFeatureUnavailable(
            "Feature output_ch4 not available on this device"
        )


if __name__ == "__main__":

    import types
    from functools import partialmethod, update_wrapper

    class TestClass:
        channel1 = ChannelBase()
        channel2 = ChannelBase()
        trigger = Trigger()
        sync = Sync()
        modulate = Modulate()

        def write(self, base_str, *args, **kwargs):
            kwargs["self"] = self
            print(base_str)
            # print(base_str.format(*args, **kwargs))

        def store(self, kwargs):
            """
            Store a dictionary of values in TestClass
            :param kwargs:
            Dictionary containing the parameters to store
            :return:
            """
            self.__dict__.update(kwargs)

        def __init__(self):
            self.api = [
                # waveform selection
                ("channel1.waveform.sin", self.write, "FUNC SIN"),
                ("channel1.waveform.square", self.write, "FUNC SQU"),
                ("channel1.waveform.ramp", self.write, "FUNC RAMP"),
                ("channel1.waveform.pulse", self.write, "FUNC PULS"),
                ("channel1.waveform.arb", self.write, "FUNC ARB"),
                ("channel1.waveform.triangle", self.write, "FUNC TRI"),
                ("channel1.waveform.noise", self.write, "FUNC NOIS"),
                ("channel1.waveform.dc", self.write, "FUNC DC"),
                # ("channel1.waveform.PRBS", self.write, ""), # Not implemented on Rigol
                ("channel2.waveform.sin", self.write, "FUNC:CH2 SIN"),
                ("channel2.waveform.square", self.write, "FUNC:CH2 SQU"),
                ("channel2.waveform.ramp", self.write, "FUNC:CH2 RAMP"),
                ("channel2.waveform.pulse", self.write, "FUNC:CH2 PULS"),
                ("channel2.waveform.arb", self.write, "FUNC:CH2 ARB"),
                ("channel2.waveform.triangle", self.write, "FUNC:CH2 TRI"),
                ("channel2.waveform.noise", self.write, "FUNC:CH2 NOIS"),
                ("channel2.waveform.dc", self.write, "FUNC:CH2 DC"),
                # ("channel2.waveform.PRBS", self.write, ""), # Not implemented on Rigol
                # Channel Configuration
                ("channel1.vrms", self.write, "VOLT:UNIT VRMS\nVOLT {value}"),
                ("channel1.vpp", self.write, "VOLT:UNIT VPP\nVOLT {value}"),
                ("channel1.dbm", self.write, "VOLT:UNIT VDBM\nVOLT {value}"),
                ("channel1.offset", self.write, "VOLT:OFFS {value}"),
                ("channel1.phase", self.write, "PHAS {value}"),
                ("channel1.duty", self.write, "COUN:DCYC"),
                ("channel1.frequency", self.write, "FREQ {value}"),
                ("channel2.vrms", self.write, "VOLT:UNIT:CH2 VRMS\nVOLT {value}"),
                ("channel2.vpp", self.write, "VOLT:UNIT:CH2 VPP\nVOLT {value}"),
                ("channel2.dbm", self.write, "VOLT:UNIT:CH2 DBM\nVOLT {value}"),
                ("channel2.offset", self.write, "VOLT:OFFS:CH2 {value}"),
                ("channel2.phase", self.write, "PHAS:CH2{value}"),
                ("channel2.duty", self.write, "COUN:DCYC"),
                ("channel2.frequency", self.write, "FREQ:CH2 {value}"),
                # Channel Activation
                (
                    "channel1.__call__",
                    self.write,
                    "OUTP {value}",
                ),  # True won't work here needs to be ON or 1, OFF or 0
                (
                    "channel2.__call__",
                    self.write,
                    "OUTP {value}",
                ),  # True won't work here needs to be ON or 1, OFF or 0
                # Sync Configuration
                ("sync.polarity.normal", self.write, ""),
                ("sync.mode.normal", self.write, ""),
                # Sync Mode source only works on one. Need to manually override so that only channel 1 being passed works
                ("sync.mode.source", self.write, ""),
                ("sync.__call__", self.write, "OUTP {value}"),
                # ("sync.polarity.inverted", self.write, "OUTP:POL }")  # Not supported on Rigol
                # Trigger Configuration
                ("trigger.source.immediate", self.write, "TRIG:SOUR IMM"),
                ("trigger.source.external", self.write, "TRIG:SOUR EXT"),
                ("trigger.source.manual", self.write, "TRIG:SOUR BUS"),
                # ("trigger.source.timer", self.write, "TRIG:SOUR \n TRIG {value}"), # Not implemented
                ("trigger.edge.rising", self.write, "TRIG:SLOP POS"),
                ("trigger.edge.falling", self.write, "TRIG:SLOP NEG"),
                ("trigger.delay", self.write, "TRIG:DEL {seconds}"),
                ("trigger.out.__call__", self.write, "OUTP:TRIG {output}"),
                ("trigger.out.rising", self.write, "OUTP:TRIG:SLOP POS"),
                ("trigger.out.falling", self.write, "OUTP:TRIG:SLOP NEG"),
                # modulate
                ("channel1.modulate.am.__call__", self.write, "AM:STAT ON"),
                ("channel1.modulate.fm.__call__", self.write, "FM:STAT ON"),
                ("channel1.modulate.pm.__call__", self.write, "PM:STAT ON"),
                ("channel1.modulate.fsk.__call__", self.write, "FSK:STAT ON"),
                ("channel2.modulate.am.__call__", self.write, "AM:STAT ON"),
                ("channel2.modulate.fm.__call__", self.write, "FM:STAT ON"),
                ("channel2.modulate.pm.__call__", self.write, "PM:STAT ON"),
                ("channel2.modulate.fsk.__call__", self.write, "FSK:STAT ON"),
                # Needs to be separately implemented because Rigol requires individual set up
                # Eg.
                # >>>fg.modulate.am() # Write Nothing
                # >>>fg.modulate(True) # Write AM:STAT ON
                # >>>fg.modulate.fm() # Write Nothing
                # >>>fg.modulate(True) # Write FM:STAT ON
                # ("channel1.modulate.am.__call__", self.store, {"modulate_state": "AM"}),
                # ("channel1.modulate.fm.__call__", self.store, {"modulate_state": "FM"}),
                # ("channel1.modulate.pm.__call__", self.store, {"modulate_state": "PM"}),
                # ("channel1.modulate.__call__", self.write, "{self.modulate_state}:STAT {value}"),
                # MODULATE SOURCES:
                (
                    "channel1.modulate.source.internal",
                    self.store,
                    {"ch1_modulate_source": "INT"},
                ),
                (
                    "channel1.modulate.source.external",
                    self.store,
                    {"ch1_modulate_source": "EXT"},
                ),
                # MODULATE ACTIVATION:
                ("channel1.modulate", self.store, {"ch1_modulate_source": "ON"}),
                ("channel1.modulate", self.store, {"ch1_modulate_source": "OFF"}),
                ("channel2.modulate", self.store, {"ch1_modulate_source": "ON"}),
                ("channel2.modulate", self.store, {"ch1_modulate_source": "OFF"}),
                # MODULATE OPTIONS:
                ("channel1.modulate.am.depth", self.write, "AM:DEPT"),
                # ("channel1.modulate.am.dssc", self.write, "AM   ")
                ("channel1.modulate.fm.freq_dev", self.write, "FM:DEV"),
                ("channel1.modulate.fm.frequency", self.write, "FM:INT:FREQ"),
                ("channel1.modulate.pm.phase_dev", self.write, "PM:DEV"),
                ("channel1.modulate.fsk.hop_freq", self.write, "FSK:FREQ"),
                ("channel1.modulate.fsk.rate", self.write, "FSK:INT:RATE"),
                ("channel2.modulate.am.depth", self.write, "AM:DEPT"),
                # ("channel2.modulate.am.dssc", self.write, "AM   ")
                ("channel2.modulate.fm.freq_dev", self.write, "FM:DEV"),
                ("channel2.modulate.fm.frequency", self.write, "FM:INT:FREQ"),
                ("channel2.modulate.pm.phase_dev", self.write, "PM:DEV"),
                ("channel2.modulate.fsk.hop_freq", self.write, "FSK:FREQ"),
                ("channel2.modulate.fsk.rate", self.write, "FSK:INT:RATE"),
                (
                    "channel1.modulate.shape.sin",
                    self.store,
                    {"ch1_modulate_source": "SIN"},
                ),
                (
                    "channel1.modulate.shape.square",
                    self.store,
                    {"ch1_modulate_source": "SQU"},
                ),
                (
                    "channel1.modulate.shape.triangle",
                    self.store,
                    {"ch1_modulate_source": "RAMP"},
                ),
                (
                    "channel1.modulate.shape.up_ramp",
                    self.store,
                    {"ch1_modulate_source": "NRAMP"},
                ),
                (
                    "channel1.modulate.shape.down_ramp",
                    self.store,
                    {"ch1_modulate_source": "TRI"},
                ),
                (
                    "channel1.modulate.shape.noise",
                    self.store,
                    {"ch1_modulate_source": "NOIS"},
                ),
                (
                    "channel2.modulate.shape.sin",
                    self.store,
                    {"ch1_modulate_source": "SIN"},
                ),
                (
                    "channel2.modulate.shape.square",
                    self.store,
                    {"ch1_modulate_source": "SQU"},
                ),
                (
                    "channel2.modulate.shape.triangle",
                    self.store,
                    {"ch1_modulate_source": "RAMP"},
                ),
                (
                    "channel2.modulate.shape.up_ramp",
                    self.store,
                    {"ch1_modulate_source": "NRAMP"},
                ),
                (
                    "channel2.modulate.shape.down_ramp",
                    self.store,
                    {"ch1_modulate_source": "TRI"},
                ),
                (
                    "channel2.modulate.shape.noise",
                    self.store,
                    {"ch1_modulate_source": "NOIS"},
                ),
                # BURST
                ("channel1.burst.gated.__call__", self.write, "BURS:MODE GAT"),
                ("channel1.burst.ncycle.__call__", self.write, "BURS:MODE TRIG"),
                ("channel1.burst.ncycle.cycles", self.write, "BURS:NCYC {cycle}"),
                (
                    "channel1.burst.ncycle.burst_period",
                    self.write,
                    "BURS:INT:PER {seconds}",
                ),
                ("channel1.burst.gated.positive", self.write, "BURS:GATE:POL NORM"),
                ("channel1.burst.gated.negative", self.write, "BURS:GATE:POL INV"),
                ("channel1.burst.phase", self.write, "BURS:PHAS {angle}"),
                ("channel2.burst.gated.__call__", self.write, "BURS:MODE GAT"),
                ("channel2.burst.ncycle.__call__", self.write, "BURS:NCYC"),
                ("channel2.burst.ncycle.cycles", self.write, "BURS:NCYC{cycle}"),
                # (channel2.burst.ncycle.burst-period, self.write, "BURS:INT:PER {seconds}"),
                ("channel2.burst.gated.positive", self.write, "BURS:GATE:POL NORM"),
                ("channel2.burst.gated.negative", self.write, "BURS:GATE:POL INV"),
                ("channel2.burst.phase", self.write, "BURS:PHAS {angle}"),
            ]
            self.init_api()

        def init_api(self):
            for func_str, handler, base_str in self.api:
                *parents, func = func_str.split(".")
                parent_obj = self
                for parent in parents:
                    parent_obj = getattr(parent_obj, parent)
                func_obc = getattr(parent_obj, func)
                setattr(
                    parent_obj, func, self.prepare_string(func_obc, handler, base_str)
                )

        def prepare_string(self, func, handler, base_str, *args, **kwargs):
            def temp_func(*nargs, **nkwargs):
                """
                Only formats using **nkwargs
                New Temp
                :param nargs:
                :param nkwargs:
                :return:
                """
                sig = inspect.signature(func)
                keys = [itm[0] for itm in sig.parameters.items()]
                for index, param in enumerate(nargs):
                    nkwargs[keys[index]] = param
                new_str = base_str.format(**nkwargs)
                # handler(self, new_str)
                handler(new_str)

            return update_wrapper(temp_func, func)

    testcls = TestClass()
    # Validated
    # testcls.channel1.waveform.sin()
    # testcls.channel1.waveform.square()
    # testcls.channel1.waveform.ramp()
    # testcls.channel1.waveform.pulse()
    # testcls.channel1.waveform.arb()
    # testcls.channel1.waveform.triangle()
    # testcls.channel1.waveform.noise()
    # testcls.channel1.waveform.dc()
    # testcls.channel1.waveform.prbs() Not implemented

    # testcls.channel2.waveform.sin()
    # testcls.channel2.waveform.square()
    # testcls.channel2.waveform.ramp()
    # testcls.channel2.waveform.pulse()
    # testcls.channel2.waveform.arb()
    # testcls.channel2.waveform.triangle()
    # testcls.channel2.waveform.noise()
    # testcls.channel2.waveform.dc()
    # testcls.channel2.waveform.prbs()

    testcls.channel1.frequency(50)
    testcls.channel2.frequency(50)
    testcls.channel1.vrms(2.1)
    testcls.channel2.vrms(2.1)
    testcls.channel1.vpp(5)
    testcls.channel2.vpp(10)
    testcls.channel1.dbm(10)
    testcls.channel2.dbm(100)
    testcls.channel1.offset(1)
    testcls.channel2.offset(0)
    testcls.channel1.phase(30)
    testcls.channel2.phase(60)
    testcls.channel1.duty(50)
    testcls.channel2.duty(25)

    testcls.trigger.source.immediate()
    testcls.trigger.source.external()
    testcls.trigger.source.manual()
    # testcls.trigger.source.timer() # Not on rigol
    testcls.trigger.delay(1)
    testcls.trigger.edge.rising()
    testcls.trigger.edge.falling()
    # testcls.trigger.out(False) # Off  Fails to override __call__
    # testcls.trigger.out(True) # True Fails to override __call__
    testcls.trigger.out.rising()
    testcls.trigger.out.falling()

    testcls.modulate.am()
    testcls.modulate.fm()
    testcls.modulate.pm()
    testcls.modulate.fsk()

    testcls.channel1.modulate.source.internal()
    testcls.channel1.modulate.source.external()
    testcls.channel2.modulate.source.internal()
    testcls.channel2.modulate.source.external()

    testcls.modulate.am.depth(100)
    # testcls.modulate.am.dssc()
    testcls.modulate.fm.freq_dev(100e3)
    testcls.modulate.fm.frequency(100e3)
    testcls.modulate.pm.phase_dev(100e3)
    testcls.modulate.fsk.hop_freq()
    testcls.modulate.fsk.rate()

    # testcls.channel1.burst.gated() # Failed to override __call__
    testcls.channel1.burst.ncycle()
    testcls.channel1.burst.gated()
    testcls.channel1.burst.ncycle.cycles(-1)
    # testcls.channel1.burst.ncycle.burst_period(10e-3)
    testcls.channel1.burst.gated.positive()
    testcls.channel1.burst.gated.negative()
    testcls.channel1.burst.phase(0)

    testcls.channel2.burst.gated()
    testcls.channel2.burst.ncycle()
    testcls.channel2.burst.gated()
    testcls.channel2.burst.ncycle.cycles(-1)
    # testcls.channel2.burst.ncycle.burst_period(10e-3)
    testcls.channel2.burst.gated.positive()
    testcls.channel2.burst.gated.negative()
    testcls.channel2.burst.phase(0)

    print(inspect.signature(testcls.channel1.frequency))
    print(inspect.signature(testcls.channel1.vrms))
    print(inspect.signature(testcls.channel1.vpp))
    print(inspect.signature(testcls.channel1.dbm))
    print(inspect.signature(testcls.channel1.offset))
    print(inspect.signature(testcls.channel1.phase))
    print(inspect.signature(testcls.channel1.duty))

    print(inspect.signature(testcls.channel2.frequency))
    print(inspect.signature(testcls.channel2.vrms))
    print(inspect.signature(testcls.channel2.vpp))
    print(inspect.signature(testcls.channel2.dbm))
    print(inspect.signature(testcls.channel2.offset))
    print(inspect.signature(testcls.channel2.phase))
    print(inspect.signature(testcls.channel2.duty))

    help(testcls.channel1.frequency)
    help(testcls.channel1.vrms)
    help(testcls.channel1.vpp)
    help(testcls.channel1.dbm)
    help(testcls.channel1.offset)
    help(testcls.channel1.phase)
    help(testcls.channel1.duty)

    help(testcls.channel2.frequency)
    help(testcls.channel2.vrms)
    help(testcls.channel2.vpp)
    help(testcls.channel2.dbm)
    help(testcls.channel2.offset)
    help(testcls.channel2.phase)
    help(testcls.channel2.duty)

    # def __init__(self):
    #     self.channel1 = ChannelBase()
    #     self.channel2 = ChannelBase()
