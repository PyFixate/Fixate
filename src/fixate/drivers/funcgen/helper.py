from abc import ABCMeta, abstractmethod
from fixate.core.exceptions import InstrumentFeatureUnavailable
import inspect

import typing

number = typing.Union[float, int]


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
        raise NotImplementedError

    # @amplitude_ch1.setter
    def amplitude_ch1(self, val):
        raise NotImplementedError

    # @property
    def amplitude_ch2(self):
        raise NotImplementedError

    # @amplitude_ch2.setter
    def amplitude_ch2(self, val):
        raise NotImplementedError

    @property
    def output_ch1(self):
        raise NotImplementedError

    @property
    def output_ch2(self):
        raise NotImplementedError

    @property
    def output_ch3(self):
        raise NotImplementedError

    @property
    def output_ch4(self):
        raise NotImplementedError

    @property
    def output_sync(self):
        raise NotImplementedError

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

    @abstractmethod
    def get_identity(self):
        pass
