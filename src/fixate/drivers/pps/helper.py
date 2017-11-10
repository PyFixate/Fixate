from abc import ABCMeta, abstractmethod
import fixate.config
from fixate.core.discover import discover_serial, filter_connected
from fixate.core.exceptions import InstrumentNotConnected


def open(restrictions=None):
    """
    Currently only searches for Serial Devices
    :param restrictions:
    :return:
    """
    # All config values for implemented instruments should be called
    if restrictions is None:
        restrictions = {}
    com_ports = restrictions.get('com_ports', None)
    baud_rates = restrictions.get('baud_rates', None)
    instruments = fixate.config.INSTRUMENTS.get("serial")
    classes = fixate.config.DRIVERS.get("PPS", {})
    instruments = filter_connected(instruments or {}, classes)
    if not instruments:
        # All discovery methods for implemented instruments should be called
        instruments = discover_serial(classes, com_ports=com_ports, baud_rates=baud_rates)
        instruments = filter_connected(instruments or {}, classes)
    # This is where the restrictions would come in
    if instruments:
        for instr in instruments:
            return instruments[instr]
    raise InstrumentNotConnected("No valid {} found".format("PPS"))


class PPS(metaclass=ABCMeta):
    _baud_rates = []
    REGEX_ID = "PPS"
    INSTR_TYPE = ""

    @abstractmethod
    def identify(self):
        pass
