import inspect
from abc import ABCMeta, abstractmethod
from functools import update_wrapper
from fixate.core.discover import discover_sub_classes, open_visa_instrument
from fixate.core.exceptions import InstrumentFeatureUnavailable

try:
    import typing

    number = typing.Union[float, int]
except ImportError:
    number = float


def open(restrictions=None):
    """Open is the public api for the dmm driver for discovering and opening a connection
    to a valid Digital Multimeter.
    At the moment opens the first dmm connected
    :param restrictions:
    A dictionary containing the technical specifications of the required equipment
    :return:
    A instantiated class connected to a valid dmm
    """
    return open_visa_instrument("DSO", restrictions)


def discover():
    """Discovers the dmm classes implemented
    :return:
    """
    return set(discover_sub_classes(DSO))


def validate_specifications(_class, specifications):
    """Validates the implemented dmm class against the specifications provided
    :return:
    True if all specifications are met
    False if one or more specifications are not met by the class
    """
    raise NotImplementedError()


class CallableNoArgs:
    def __call__(self):
        self._call()

    def _call(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class CallableBool:
    def __call__(self, value: bool):
        self._call(value)

    def _call(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class SourcesCh:
    def ch1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def ch2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def ch3(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def ch4(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class SourcesSpecial:
    def function(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def math(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class SourcesWMem:
    def wmemory1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def wmemory2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class SourcesExt:
    def external(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class SourcesDig:
    def d0(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d1(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d2(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d3(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d4(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d5(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d6(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d7(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d8(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d9(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d10(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d11(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d12(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d13(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d14(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def d15(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class MeasureAllSources(SourcesCh, SourcesSpecial, SourcesWMem, SourcesDig, CallableNoArgs):
    pass


class TrigSources(SourcesCh, SourcesExt, SourcesDig):
    pass


class MultiMeasureSources(MeasureAllSources):
    def __init__(self):
        self.ch1 = MeasureAllSources()
        self.ch1 = MeasureAllSources()
        self.ch2 = MeasureAllSources()
        self.ch3 = MeasureAllSources()
        self.ch4 = MeasureAllSources()
        self.function = MeasureAllSources()
        self.math = MeasureAllSources()
        self.wmemory1 = MeasureAllSources()
        self.wmemory2 = MeasureAllSources()
        self.external = MeasureAllSources()
        self.d0 = MeasureAllSources()
        self.d1 = MeasureAllSources()
        self.d2 = MeasureAllSources()
        self.d3 = MeasureAllSources()
        self.d4 = MeasureAllSources()
        self.d5 = MeasureAllSources()
        self.d6 = MeasureAllSources()
        self.d7 = MeasureAllSources()
        self.d8 = MeasureAllSources()
        self.d9 = MeasureAllSources()
        self.d10 = MeasureAllSources()
        self.d11 = MeasureAllSources()
        self.d12 = MeasureAllSources()
        self.d13 = MeasureAllSources()
        self.d14 = MeasureAllSources()
        self.d15 = MeasureAllSources()


class Coupling:
    def ac(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def dc(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def lf_reject(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def tv(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Probe:
    def attenuation(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class VerticalUnits:
    def volts(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def amps(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class ChannelBase(CallableBool):
    def __init__(self, channel_name: str):
        self._ch_name = channel_name
        # self.waveform = Waveform()
        # self.modulate = Modulate()
        # self.burst = Burst()
        # self.load = Load()
        self.coupling = Coupling()
        self.probe = Probe()
        self.units = VerticalUnits()

    def bandwidth(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def bandwidth_limit(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def impedance(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def invert(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def offset(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def scale(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Trigger:
    def __init__(self):
        self.mode = TrigMode()
        self.delay = None
        self.eburst = None
        self.coupling = Coupling()
        self.sweep = TrigSweep()

    def force(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def hf_reject(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def hold_off(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def n_reject(self, value: bool):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TrigSweep:
    def auto(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def normal(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TrigLevel:
    def high(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def low(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TrigMode:
    def __init__(self):
        self.edge = TrigEdge()


class TrigEdge(CallableNoArgs):
    def __init__(self):
        self.source = TrigSources()
        self.slope = Slopes()

    def level(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TrigReject:
    def off(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def lf(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def hf(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Slopes:
    def rising(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def falling(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def alternating(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def either(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Acquire:
    def __init__(self):
        self.mode = AcquireMode()

    def normal(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def peak_detect(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def averaging(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def high_resolution(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class AcquireMode:
    def rtim(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def segm(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Timebase:
    def __init__(self):
        self.mode = TimebaseMode()

    def position(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def scale(self, value: number):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class TimebaseMode:
    def main(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def window(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def xy(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def roll(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class Events:
    def trigger(self):
        """
        Indicates if a trigger event has occurred.
        Calls to this will clear the existing trigger events
        :return:
        """
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))


class MeasureInterval:
    def __init__(self):
        self.cycle = MeasureAllSources()
        self.display = MeasureAllSources()


class MeasureIntervalMultipleSources:
    def __init__(self):
        self.cycle = MultiMeasureSources()
        self.display = MultiMeasureSources()


class MeasureRMS:
    def __init__(self):
        self.dc = MeasureInterval()
        self.ac = MeasureInterval()


class Measure:
    def __init__(self):
        self.counter = MeasureAllSources()
        self.delay = MultiMeasureSources()
        self.duty = MeasureAllSources()
        self.fall_time = MeasureAllSources()
        self.frequency = MeasureAllSources()
        self.cnt_edge_rising = MeasureAllSources()
        self.cnt_edge_falling = MeasureAllSources()
        self.cnt_pulse_positive = MeasureAllSources()
        self.cnt_pulse_negative = MeasureAllSources()
        self.period = MeasureAllSources()
        self.phase = MultiMeasureSources()
        self.pulse_width = MeasureAllSources()
        self.vamplitude = MeasureAllSources()
        self.vaverage = MeasureInterval()
        self.vbase = MeasureAllSources()
        self.vmax = MeasureAllSources()
        self.vmin = MeasureAllSources()
        self.vpp = MeasureAllSources()
        self.vratio = MeasureIntervalMultipleSources()
        self.vrms = MeasureRMS()
        self.xmax = MeasureAllSources()
        self.xmin = MeasureAllSources()



class DSO(metaclass=ABCMeta):
    REGEX_ID = "DSO"

    def __init__(self, instrument):
        self.instrument = instrument
        self.samples = 1
        self.api = []
        self.ch1 = ChannelBase("1")
        self.ch2 = ChannelBase("2")
        self.ch3 = ChannelBase("3")
        self.ch4 = ChannelBase("4")
        self.chmath = ChannelBase("math")
        self.chfunc = ChannelBase("func")
        self.trigger = Trigger()
        self.time_base = Timebase()
        self.acquire = Acquire()
        self.measure = Measure()
        self.events = Events()

    @abstractmethod
    def acquire(self, acquire_type, averaging_samples):
        pass

    @abstractmethod
    def waveform_values(self, source, filename):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def auto_scale(self):
        pass

    @abstractmethod
    def save_setup(self, file_name):
        pass

    @abstractmethod
    def load_setup(self, file_name):
        pass

    def run(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def single(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def stop(self):
        raise InstrumentFeatureUnavailable(
            "{} not available on this device".format(inspect.currentframe().f_code.co_name))

    def init_api(self):
        for func_str, handler, base_str in self.api:
            *parents, func = func_str.split(".")
            parent_obj = self
            for parent in parents:
                parent_obj = getattr(parent_obj, parent)
            func_obc = getattr(parent_obj, func)
            setattr(parent_obj, func, self.prepare_string(func_obc, handler, base_str))

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
            return handler(new_str)

        return update_wrapper(temp_func, func)
