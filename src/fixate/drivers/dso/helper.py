from abc import ABCMeta, abstractmethod
from fixate.core.discover import discover_sub_classes, open_visa_instrument


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


class DSO(metaclass=ABCMeta):
    REGEX_ID = "DSO"

    def __init__(self, instrument):
        self.instrument = instrument
        self.samples = 1

    @abstractmethod
    def acquire(self, acquire_type, averaging_samples):
        pass

    @abstractmethod
    def waveform_values(self, source, filename):
        pass

    @abstractmethod
    def measure_frequency(self, signal):
        pass

    @abstractmethod
    def measure_phase(self, signal, reference):
        pass

    @abstractmethod
    def measure_v_pp(self, source):
        pass

    @abstractmethod
    def measure_v_rms(self, source):
        pass

    @abstractmethod
    def measure_v_max(self, source):
        pass

    @abstractmethod
    def measure_v_min(self, source):
        pass

    @abstractmethod
    def measure_x_min(self, source):
        pass

    @abstractmethod
    def measure_x_max(self, source):
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
